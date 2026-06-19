#!/usr/bin/env python3
"""Unit tests for csv_to_cues.py — the cue-list CSV → grandMA2 command transform.

Run: python3 -m unittest test_csv_to_cues  (from the scripts/ directory)
Pure stdlib (unittest + tempfile); no install step, mirrors the skill's
"never reach for a dependency" stance.
"""

import os
import tempfile
import unittest

import csv_to_cues as mod


def _write(tmp: str, name: str, text: str) -> str:
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class ParseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_canonical_header_parses_in_order(self):
        path = _write(self.tmp, "s.csv",
                      "number,name,time,fadeIn,fadeOut,type,notes\n"
                      "1,PGM IN,0.0,0,0,General,\n"
                      "2,INTRO,8.2,0,0,General,\n")
        cues, warnings = mod.parse(path)
        self.assertEqual([c.number for c in cues], ["1", "2"])
        self.assertEqual([c.name for c in cues], ["PGM IN", "INTRO"])
        self.assertEqual(cues[1].time, 8.2)
        self.assertEqual(warnings, [])

    def test_variant_headers_resolve(self):
        # Cue / Section / Timecode are accepted as number / name / time.
        path = _write(self.tmp, "s.csv",
                      "Cue,Section,Timecode\n1,Intro,0\n2,Verse,12.5\n")
        cues, _ = mod.parse(path)
        self.assertEqual([c.name for c in cues], ["Intro", "Verse"])
        self.assertEqual(cues[1].time, 12.5)

    def test_missing_number_falls_back_to_row_order(self):
        path = _write(self.tmp, "s.csv", "label,time\nHit,0\nDrop,8\n")
        cues, _ = mod.parse(path)
        self.assertEqual([c.number for c in cues], ["1", "2"])
        self.assertEqual([c.name for c in cues], ["Hit", "Drop"])

    def test_notes_column_is_not_misread_as_number(self):
        # "no" must not greedily match the "notes" header — the row-order
        # fallback should supply numbers, and notes stays out of `number`.
        path = _write(self.tmp, "s.csv",
                      "name,notes\nPGM IN,top of show\nINTRO,band enters\n")
        cues, _ = mod.parse(path)
        self.assertEqual([c.number for c in cues], ["1", "2"])
        self.assertEqual([c.name for c in cues], ["PGM IN", "INTRO"])

    def test_integer_numbers_stay_integers(self):
        path = _write(self.tmp, "s.csv", "number,name\n1.0,A\n2,B\n")
        cues, _ = mod.parse(path)
        self.assertEqual([c.number for c in cues], ["1", "2"])

    def test_utf8_bom_and_chinese_names(self):
        path = os.path.join(self.tmp, "s.csv")
        with open(path, "w", encoding="utf-8-sig") as fh:
            fh.write("number,name,time\n1,前奏,0\n2,主歌,10\n")
        cues, _ = mod.parse(path)
        self.assertEqual([c.name for c in cues], ["前奏", "主歌"])

    def test_blank_rows_skipped(self):
        path = _write(self.tmp, "s.csv", "number,name\n1,A\n\n2,B\n")
        cues, _ = mod.parse(path)
        self.assertEqual(len(cues), 2)

    def test_missing_name_column_is_fatal(self):
        path = _write(self.tmp, "s.csv", "number,time\n1,0\n")
        with self.assertRaises(SystemExit):
            mod.parse(path)


class WarningTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _parse(self, text):
        path = os.path.join(self.tmp, "s.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return mod.parse(path)

    def test_duplicate_name_warns(self):
        _, warnings = self._parse("number,name\n5,CHOR 1\n11,CHOR 1\n")
        self.assertTrue(any("duplicate" in w.lower() for w in warnings))

    def test_non_increasing_numbers_warn(self):
        _, warnings = self._parse("number,name\n2,A\n1,B\n")
        self.assertTrue(any("increasing" in w.lower() for w in warnings))

    def test_blank_name_warns(self):
        _, warnings = self._parse("number,name\n1,\n2,B\n")
        self.assertTrue(any("blank" in w.lower() for w in warnings))


class CommandTests(unittest.TestCase):
    def test_clearall_brackets_and_store_lines(self):
        cues = [mod.Cue("1", "PGM IN", 0.0), mod.Cue("2", "INTRO", 8.2)]
        lines = mod.cmd_lines(cues, "101", note_col=None)
        self.assertEqual(lines[0], "ClearAll")
        self.assertEqual(lines[-1], "ClearAll")
        self.assertIn('Store Sequence 101 Cue 1 "PGM IN" /nc', lines)
        self.assertIn('Store Sequence 101 Cue 2 "INTRO" /nc', lines)

    def test_note_col_time_emits_assign_lines(self):
        cues = [mod.Cue("1", "PGM IN", 0.0), mod.Cue("2", "INTRO", 8.2)]
        lines = mod.cmd_lines(cues, "101", note_col="time")
        self.assertIn('Assign Cue 1 Sequence 101 /note="@0.0s"', lines)
        self.assertIn('Assign Cue 2 Sequence 101 /note="@8.2s"', lines)

    def test_note_col_skips_rows_without_time(self):
        cues = [mod.Cue("1", "PGM IN", None)]
        lines = mod.cmd_lines(cues, "101", note_col="time")
        self.assertFalse(any("/note" in ln for ln in lines))

    def test_double_quotes_in_name_downgraded(self):
        # MA command quoting uses double-quotes; a name containing one would
        # break the Store, so it is downgraded to a single quote.
        cues = [mod.Cue("1", 'THE "BIG" HIT', None)]
        lines = mod.cmd_lines(cues, "101", note_col=None)
        self.assertIn("Store Sequence 101 Cue 1 \"THE 'BIG' HIT\" /nc", lines)


if __name__ == "__main__":
    unittest.main()
