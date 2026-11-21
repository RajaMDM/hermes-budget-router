"""Unit tests for bin/h. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import datetime as dt
import importlib.machinery
import importlib.util
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("h", str(ROOT / "bin" / "h"))
spec = importlib.util.spec_from_loader("h", loader)
h = importlib.util.module_from_spec(spec)
sys.modules["h"] = h
loader.exec_module(h)

CFG = h.parse_config(h.DEFAULT_CONFIG)


def tmpdir() -> Path:
    return Path(tempfile.mkdtemp())


class TestConfig(unittest.TestCase):
    def test_default_is_claude(self):
        self.assertEqual(CFG.tiers["o"].provider, "anthropic")

    def test_all_presets_are_valid_json_with_three_tiers(self):
        for p in (ROOT / "presets").glob("*.json"):
            raw = json.loads(p.read_text())
            self.assertEqual(set(raw["tiers"]), {"q", "s", "o"}, p.name)
            self.assertIn("description", raw, p.name)

    def test_presets_without_placeholders_parse(self):
        for p in (ROOT / "presets").glob("*.json"):
            if "REPLACE" not in p.read_text():
                h.parse_config(json.loads(p.read_text()))

    def test_placeholder_rejected(self):
        raw = json.loads((ROOT / "presets" / "openrouter.json").read_text())
        with self.assertRaises(ValueError):
            h.parse_config(raw)

    def test_missing_tier_rejected(self):
        with self.assertRaises(ValueError):
            h.parse_config({"tiers": {"q": {"provider": "x", "model": "y"}}})

    def test_null_budget(self):
        raw = json.loads((ROOT / "presets" / "gemini-free.json").read_text())
        self.assertIsNone(h.parse_config(raw).budget_usd)

    def test_user_endpoint_overrides_builtin(self):
        raw = dict(h.DEFAULT_CONFIG, endpoints={"anthropic": {"api": "openai", "base_url": "http://x", "key_env": []}})
        self.assertEqual(h.parse_config(raw).endpoint("anthropic")["base_url"], "http://x")


class TestKeys(unittest.TestCase):
    def test_env_file_parsing_skips_comments_and_empty(self):
        p = tmpdir() / ".env"
        p.write_text("# ANTHROPIC_TOKEN=old\nANTHROPIC_API_KEY=\nANTHROPIC_API_KEY=sk-new\nX='q'\n")
        self.assertEqual(h.read_env_file(p), {"ANTHROPIC_API_KEY": "sk-new", "X": "q"})

    def test_get_key_fallback_names(self):
        ep = h.ENDPOINTS["gemini"]
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(h.get_key(ep, {"GOOGLE_API_KEY": "g"}), "g")
            self.assertIsNone(h.get_key(ep, {}))

    def test_local_needs_no_key(self):
        self.assertEqual(h.get_key(h.ENDPOINTS["custom"], {}), "")


class TestRubric(unittest.TestCase):
    def test_general_knowledge_plans_go_to_standard(self):
        sp = h.SYSTEM_PROMPT
        s_line = next(l for l in sp.splitlines() if l.startswith("s = "))
        o_line = next(l for l in sp.splitlines() if l.startswith("o = "))
        self.assertIn("plans or advice drawn from general knowledge", s_line)
        self.assertIn("real stakes", o_line)
        self.assertIn("{budget_hint}", sp)


class TestHeuristicAndParse(unittest.TestCase):
    def test_heuristic_plans_go_standard(self):
        self.assertEqual(h.heuristic("my team keeps missing deadlines. diagnose causes and give me a 30-day fix plan")[0], "s")
        self.assertEqual(h.heuristic("draft an email to finance")[0], "s")

    def test_heuristic(self):
        self.assertEqual(h.heuristic("what is survivorship")[0], "q")
        self.assertEqual(h.heuristic("design the target-state architecture")[0], "o")
        self.assertEqual(h.heuristic(" ".join(["word"] * 40))[0], "s")

    def test_parse_reply(self):
        self.assertEqual(h.parse_reply('{"tier":"s","reason":"draft"}'), ("s", "draft"))
        self.assertEqual(h.parse_reply('ok {"tier":"O","reason":"hard"}')[0], "o")
        self.assertIsNone(h.parse_reply('{"tier":"x"}'))
        self.assertIsNone(h.parse_reply("nope"))


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestAdapters(unittest.TestCase):
    def test_openai_compatible_chat(self):
        body = json.dumps({"choices": [{"message": {"content": '{"tier":"q","reason":"r"}'}}]}).encode()
        with mock.patch("urllib.request.urlopen", return_value=FakeResp(body)) as u:
            out = h.chat(h.ENDPOINTS["xai"], "k", "grok", "sys", "hi")
        self.assertIn('"tier":"q"', out)
        req = u.call_args[0][0]
        self.assertTrue(req.full_url.endswith("/chat/completions"))
        self.assertEqual(req.get_header("Authorization"), "Bearer k")

    def test_anthropic_chat_retries_bearer_on_401(self):
        import urllib.error
        ok = json.dumps({"content": [{"type": "text", "text": '{"tier":"o","reason":"r"}'}]}).encode()
        err = urllib.error.HTTPError("u", 401, "no", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=[err, FakeResp(ok)]) as u:
            out = h.chat(h.ENDPOINTS["anthropic"], "k", "m", "sys", "hi")
        self.assertIn('"o"', out)
        self.assertEqual(u.call_args[0][0].get_header("Authorization"), "Bearer k")

    def test_classifier_budget_is_not_tiny(self):
        import inspect
        self.assertGreaterEqual(inspect.signature(h.chat).parameters["max_tokens"].default, 300)

    def test_list_models_strips_prefix(self):
        body = json.dumps({"data": [{"id": "models/gemini-3.5-flash"}]}).encode()
        with mock.patch("urllib.request.urlopen", return_value=FakeResp(body)):
            self.assertIn("gemini-3.5-flash", h.list_models(h.ENDPOINTS["gemini"], "k"))


class TestRouting(unittest.TestCase):
    def test_forced(self):
        self.assertEqual(h.route("x", CFG, forced="o").source, "forced")

    def test_heuristic_when_no_classifier(self):
        with mock.patch.object(h, "classifier_target", return_value=None):
            d = h.route("what is MDM", CFG)
        self.assertEqual((d.tier, d.source), ("q", "heuristic"))

    def test_classifier_with_budget_hint(self):
        b = h.Budget(150, 200, dt.date(2026, 11, 10), dt.date(2026, 12, 10), dt.date(2026, 11, 20))
        target = (CFG.tiers["q"], h.ENDPOINTS["anthropic"], "k")
        with mock.patch.object(h, "classifier_target", return_value=target), \
             mock.patch.object(h, "chat", return_value='{"tier":"s","reason":"routine"}') as c:
            d = h.route("draft an email", CFG, budget=b)
        self.assertEqual((d.tier, d.source), ("s", "classifier"))
        self.assertIn("run out early", c.call_args[0][3])

    def test_classifier_skips_launch_only_provider(self):
        raw = json.loads((ROOT / "presets" / "chatgpt-plan.json").read_text())
        for t in raw["tiers"].values():
            t["model"] = "m"
        cfg = h.parse_config(raw)
        with mock.patch.object(h, "read_env_file", return_value={}):
            self.assertIsNone(h.classifier_target(cfg))

    def test_mixed_config_falls_through_to_tier_with_key(self):
        raw = json.loads((ROOT / "presets" / "mixed-budget.json").read_text())
        raw["tiers"]["q"]["model"] = "llama"
        cfg = h.parse_config(raw)
        with mock.patch.object(h, "read_env_file", return_value={}), mock.patch.dict("os.environ", {}, clear=True):
            tier, ep, key = h.classifier_target(cfg)
        self.assertEqual(tier.provider, "custom")  # gemini (s) has no key; local needs none


class TestBudget(unittest.TestCase):
    def test_cycle_bounds(self):
        self.assertEqual(h.cycle_bounds(dt.date(2026, 11, 21), 10), (dt.date(2026, 11, 10), dt.date(2026, 12, 10)))
        self.assertEqual(h.cycle_bounds(dt.date(2027, 1, 5), 10), (dt.date(2026, 12, 10), dt.date(2027, 1, 10)))
        self.assertEqual(h.cycle_bounds(dt.date(2027, 2, 15), 31), (dt.date(2027, 1, 31), dt.date(2027, 2, 28)))

    def test_sum_current_cycle(self):
        db = tmpdir() / "state.db"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE sessions (id TEXT, started_at, estimated_cost_usd REAL)")
        ts = dt.datetime(2026, 11, 20, 12).timestamp()
        con.executemany("INSERT INTO sessions VALUES (?,?,?)",
                        [("a", ts, 1.5), ("b", "2026-11-12T09:00:00", 0.5), ("c", "2026-11-01", 99), ("d", ts * 1000, 0.25)])
        con.commit()
        con.close()
        self.assertAlmostEqual(h.read_budget(CFG, db, dt.date(2026, 11, 21)).spent, 2.25)

    def test_no_budget_configured(self):
        raw = json.loads((ROOT / "presets" / "gemini-free.json").read_text())
        self.assertIsNone(h.read_budget(h.parse_config(raw)))

    def test_status(self):
        mk = lambda spent, today: h.Budget(spent, 200, dt.date(2026, 11, 10), dt.date(2026, 12, 10), today)
        self.assertEqual(mk(150, dt.date(2026, 11, 20)).status, "tight")
        self.assertEqual(mk(20, dt.date(2026, 12, 7)).status, "underuse")
        self.assertEqual(mk(20, dt.date(2026, 11, 20)).status, "normal")


class TestCheck(unittest.TestCase):
    def test_reports_missing_key_and_bad_model(self):
        with mock.patch.object(h, "read_env_file", return_value={}), mock.patch.dict("os.environ", {}, clear=True):
            out = "\n".join(h.check(CFG))
        self.assertIn("no key", out)
        with mock.patch.object(h, "read_env_file", return_value={"ANTHROPIC_API_KEY": "k"}), \
             mock.patch.object(h, "list_models", return_value={"claude-haiku-5-5", "claude-opus-5-5"}):
            out = "\n".join(h.check(CFG))
        self.assertIn("✓", out)
        self.assertIn("not offered", out)  # sonnet missing from fake list


class TestLaunchArgs(unittest.TestCase):
    def test_query_flag_by_default(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            args = h.build_args("what is MDM", CFG.tiers["q"])
        self.assertEqual(args[-2:], ["-q", "what is MDM"])
        self.assertNotIn("--reasoning", args)

    def test_clipboard_mode(self):
        with mock.patch.dict("os.environ", {"H_FIRST_MESSAGE_FLAG": "clipboard"}):
            self.assertNotIn("what is MDM", h.build_args("what is MDM", CFG.tiers["q"]))

    def test_reasoning_passed(self):
        raw = json.loads(json.dumps(h.DEFAULT_CONFIG))
        raw["tiers"]["o"]["reasoning"] = "high"
        args = h.build_args("x", h.parse_config(raw).tiers["o"])
        self.assertEqual(args[args.index("--reasoning") + 1], "high")

    def test_bad_reasoning_rejected(self):
        raw = json.loads(json.dumps(h.DEFAULT_CONFIG))
        raw["tiers"]["o"]["reasoning"] = "turbo"
        with self.assertRaises(ValueError):
            h.parse_config(raw)


class TestSessions(unittest.TestCase):
    def _db(self):
        db = tmpdir() / "state.db"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE sessions (id TEXT, user_id TEXT, title TEXT, model TEXT, model_config TEXT, "
                    "started_at REAL, message_count INT, api_call_count INT, tool_call_count INT, "
                    "input_tokens INT, output_tokens INT, cache_read_tokens INT, cache_write_tokens INT, "
                    "reasoning_tokens INT, estimated_cost_usd REAL, actual_cost_usd REAL, cost_status TEXT, "
                    "cost_source TEXT, hidden INT, chat_id TEXT, prompt_cache_clock TEXT)")
        rows = [
            ("local-aaaaaaaaaaaaaaaa", "uid:501", "private topic", "claude-opus-5-5", "{}",
             dt.datetime(2026, 11, 21, 12, 5).timestamp(), 24, 21, 20, 1000, 3000, 200000, 30000, 0,
             0.38, None, "estimated", "provider_models_api", 0, "c", "{}"),
            ("local-bbbbbbbbbbbbbbbb", "uid:501", "survivorship", "claude-haiku-5-5", "{}",
             dt.datetime(2026, 11, 21, 14, 50).timestamp(), 2, 1, 0, 4, 131, 0, 21693, 0,
             0.0028, None, "estimated", "provider_models_api", 0, "c", "{}"),
        ]
        con.executemany(f"INSERT INTO sessions VALUES ({','.join('?' * 21)})", rows)
        con.commit()
        con.close()
        return db

    def test_whitelist_only(self):
        cols, rows = h.read_sessions(self._db(), limit=5)
        for bad in ("title", "user_id", "model_config", "hidden", "chat_id", "prompt_cache_clock", "cost_source"):
            self.assertNotIn(bad, cols)
        self.assertIn("tools", cols)
        self.assertEqual(rows[0][0], "bbbbbbbbbb")  # newest first, short id

    def test_recompute_matches_real_haiku_session(self):
        # Real row from a Hermes v0.23 session: 4 in, 131 out, 21,693 cache-write tokens, Hermes said $0.0028.
        rc = h.recompute_cost("claude-haiku-5-5", {"input_tokens": 4, "output_tokens": 131, "cache_write_tokens": 21693})
        self.assertAlmostEqual(rc, 0.0028, places=4)

    def test_unknown_model_not_recomputed(self):
        self.assertIsNone(h.recompute_cost("some-other-model", {"input_tokens": 10}))

    def test_titles_opt_in_and_csv(self):
        cols, rows = h.read_sessions(self._db(), limit=5, titles=True)
        out = h.format_sessions(cols, rows, as_csv=True)
        self.assertIn("private topic", out)
        self.assertIn("2026-11-21 12:05", out)
        self.assertIn("recomputed_usd", out.splitlines()[0])

    def test_text_table_totals(self):
        cols, rows = h.read_sessions(self._db(), limit=5)
        out = h.format_sessions(cols, rows)
        self.assertIn("Hermes estimate $0.3828", out)
        self.assertIn("recomputed from published prices", out)
        self.assertNotIn("uid:501", out)


class TestInit(unittest.TestCase):
    def test_init_names_config_and_flags_placeholders(self):
        target = tmpdir() / "h.json"
        buf = io.StringIO()
        with mock.patch.object(h, "CONFIG_FILE", target), mock.patch("sys.stdout", buf):
            h.init("claude-credits")
            self.assertEqual(json.loads(target.read_text())["name"], "claude-credits")
            self.assertIn("Next: run h --check", buf.getvalue())
            h.init("openrouter")
        self.assertIn("placeholder model for tier(s) q, s, o", buf.getvalue())
        self.assertTrue(target.with_suffix(".json.bak").exists())


class TestLogStatsEval(unittest.TestCase):
    def test_log_stats(self):
        p = tmpdir() / "log.jsonl"
        for t in ("q", "q", "o"):
            h.log_decision("task", h.Decision(t, "r", "classifier"), CFG, None, p)
        out = h.stats(p)
        self.assertIn("3 sessions", out)
        self.assertIn("anthropic/claude-haiku-5-5 2", out)

    def test_log_tasks_off(self):
        p = tmpdir() / "log.jsonl"
        with mock.patch.dict("os.environ", {"H_LOG_TASKS": "0"}):
            h.log_decision("secret", h.Decision("q", "r", "classifier"), CFG, None, p)
        self.assertNotIn("task", json.loads(p.read_text()))

    def test_eval_score(self):
        d = tmpdir()
        (d / "t.txt").write_text("# c\nwhat is MDM\ndesign the architecture\n")
        buf = io.StringIO()
        with mock.patch.object(h, "classifier_target", return_value=None), \
             mock.patch.object(h, "read_budget", return_value=None):
            h.run_eval(CFG, d / "t.txt", out=buf)
        self.assertEqual(len(buf.getvalue().strip().splitlines()), 3)
        (d / "l.csv").write_text("task,tier,reason,source,expected\na,q,r,h,q\nb,q,r,h,o\nc,o,r,h,s\n")
        s = h.score(d / "l.csv")
        self.assertIn("1 exact", s)
        self.assertIn("1 under-routed", s)
        self.assertIn("1 over-routed", s)


if __name__ == "__main__":
    unittest.main()
