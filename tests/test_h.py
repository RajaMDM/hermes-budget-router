"""Unit tests for bin/h. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import datetime as dt
import importlib.machinery
import importlib.util
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("h", str(ROOT / "bin" / "h"))
spec = importlib.util.spec_from_loader("h", loader)
h = importlib.util.module_from_spec(spec)
import sys; sys.modules["h"] = h
loader.exec_module(h)


class TestHeuristic(unittest.TestCase):
    def test_short_question_is_haiku(self):
        self.assertEqual(h.heuristic("what is survivorship")[0], "q")

    def test_heavy_keyword_is_opus(self):
        self.assertEqual(h.heuristic("design the target-state architecture")[0], "o")

    def test_long_plain_task_is_sonnet(self):
        self.assertEqual(h.heuristic(" ".join(["word"] * 40))[0], "s")


class TestParseReply(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(h.parse_reply('{"tier":"s","reason":"draft"}'), ("s", "draft"))

    def test_wrapped_in_text(self):
        self.assertEqual(h.parse_reply('Sure: {"tier":"O","reason":"hard"} done')[0], "o")

    def test_invalid_tier(self):
        self.assertIsNone(h.parse_reply('{"tier":"x"}'))

    def test_garbage(self):
        self.assertIsNone(h.parse_reply("no json here"))


class TestCycle(unittest.TestCase):
    def test_after_cycle_day(self):
        self.assertEqual(h.cycle_bounds(dt.date(2026, 11, 21), 10),
                         (dt.date(2026, 11, 10), dt.date(2026, 12, 10)))

    def test_before_cycle_day_wraps_year(self):
        self.assertEqual(h.cycle_bounds(dt.date(2027, 1, 5), 10),
                         (dt.date(2026, 12, 10), dt.date(2027, 1, 10)))

    def test_day_31_clamps(self):
        start, end = h.cycle_bounds(dt.date(2027, 2, 15), 31)
        self.assertEqual(start, dt.date(2027, 1, 31))
        self.assertEqual(end, dt.date(2027, 2, 28))


class TestBudget(unittest.TestCase):
    def _db(self, rows, time_col="started_at"):
        tmp = Path(tempfile.mkdtemp()) / "state.db"
        con = sqlite3.connect(tmp)
        con.execute(f"CREATE TABLE sessions (id TEXT, {time_col}, estimated_cost_usd REAL)")
        con.executemany("INSERT INTO sessions VALUES (?,?,?)", rows)
        con.commit()
        con.close()
        return tmp

    def test_sums_only_current_cycle_epoch_and_iso(self):
        in_cycle = dt.datetime(2026, 11, 20, 12).timestamp()
        db = self._db([("a", in_cycle, 1.5), ("b", "2026-11-12T09:00:00", 0.5),
                       ("c", "2026-11-01T09:00:00", 99.0), ("d", in_cycle * 1000, 0.25)])
        b = h.read_budget(db, today=dt.date(2026, 11, 21))
        self.assertAlmostEqual(b.spent, 2.25)

    def test_status_tight(self):
        b = h.Budget(150, 200, dt.date(2026, 11, 10), dt.date(2026, 12, 10), dt.date(2026, 11, 20))
        self.assertEqual(b.status, "tight")

    def test_status_underuse(self):
        b = h.Budget(20, 200, dt.date(2026, 11, 10), dt.date(2026, 12, 10), dt.date(2026, 12, 7))
        self.assertEqual(b.status, "underuse")

    def test_missing_cost_column_returns_none(self):
        tmp = Path(tempfile.mkdtemp()) / "state.db"
        con = sqlite3.connect(tmp)
        con.execute("CREATE TABLE sessions (id TEXT, started_at TEXT)")
        con.close()
        self.assertIsNone(h.read_budget(tmp))


class TestRouting(unittest.TestCase):
    def test_forced(self):
        self.assertEqual(h.route("anything", forced="o").source, "forced")

    def test_falls_back_to_heuristic_without_key(self):
        with mock.patch.object(h, "load_api_key", return_value=None):
            d = h.route("what is MDM")
        self.assertEqual((d.tier, d.source), ("q", "heuristic"))

    def test_uses_classifier_and_passes_budget_hint(self):
        with mock.patch.object(h, "load_api_key", return_value="k"), \
             mock.patch.object(h, "classify", return_value=("s", "routine")) as c:
            b = h.Budget(150, 200, dt.date(2026, 11, 10), dt.date(2026, 12, 10), dt.date(2026, 11, 20))
            d = h.route("draft an email", budget=b)
        self.assertEqual((d.tier, d.source), ("s", "classifier"))
        self.assertEqual(c.call_args[0][2], "tight")


class TestLogAndStats(unittest.TestCase):
    def test_log_then_stats(self):
        path = Path(tempfile.mkdtemp()) / "log.jsonl"
        for tier in ("q", "q", "o"):
            h.log_decision("task", h.Decision(tier, "r", "classifier"), None, path)
        out = h.stats(path)
        self.assertIn("3 sessions", out)
        self.assertIn("Haiku", out)
        self.assertEqual(json.loads(path.read_text().splitlines()[0])["task"], "task")

    def test_log_tasks_off(self):
        path = Path(tempfile.mkdtemp()) / "log.jsonl"
        with mock.patch.dict("os.environ", {"H_LOG_TASKS": "0"}):
            h.log_decision("secret", h.Decision("q", "r", "classifier"), None, path)
        self.assertNotIn("task", json.loads(path.read_text()))


class TestEvalScore(unittest.TestCase):
    def test_eval_and_score(self):
        d = Path(tempfile.mkdtemp())
        tasks = d / "tasks.txt"
        tasks.write_text("# comment\nwhat is MDM\ndesign the architecture\n")
        buf = io.StringIO()
        with mock.patch.object(h, "load_api_key", return_value=None), \
             mock.patch.object(h, "read_budget", return_value=None):
            h.run_eval(tasks, out=buf)
        rows = buf.getvalue().strip().splitlines()
        self.assertEqual(len(rows), 3)
        labelled = d / "labelled.csv"
        labelled.write_text("task,tier,reason,source,expected\n"
                            "a,q,r,heuristic,q\nb,q,r,heuristic,o\nc,o,r,heuristic,s\n")
        self.assertIn("1 exact", h.score(labelled))
        self.assertIn("1 under-routed", h.score(labelled))
        self.assertIn("1 over-routed", h.score(labelled))


if __name__ == "__main__":
    unittest.main()
