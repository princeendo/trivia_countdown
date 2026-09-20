"""Regression checks for complete sets and leftover question records."""

import contextlib
import csv
import io
from pathlib import Path
import tempfile
import unittest

from csv_splitter import split_csv


class CsvSplitterTests(unittest.TestCase):
    def test_question_sets_preserve_records_without_oversized_last_part(self):
        cases = (
            (1, [1]),
            (22, [22]),
            (23, [23]),
            (24, [23, 1]),
            (45, [23, 22]),
            (46, [23, 23]),
            (47, [23, 23, 1]),
            (69, [23, 23, 23]),
        )
        for count, expected_sizes in cases:
            with self.subTest(count=count), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "questions.csv"
                header = ["question", "answer"]
                rows = [[f'Question {i}, with "quotes"\nand a newline', str(i)] for i in range(count)]
                with source.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(rows)
                original = source.read_bytes()

                with contextlib.redirect_stdout(io.StringIO()):
                    split_csv(source, 23)

                parts = sorted(source.parent.glob("questions_part_*.csv"))
                sizes = []
                combined = []
                for part in parts:
                    with part.open(newline="", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        self.assertEqual(next(reader), header)
                        records = list(reader)
                    sizes.append(len(records))
                    combined.extend(records)
                self.assertEqual(sizes, expected_sizes)
                self.assertEqual(combined, rows)
                self.assertEqual(source.read_bytes(), original)

    def test_invalid_row_count_does_not_create_parts(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "questions.csv"
            source.write_text("question\nExample\n", encoding="utf-8")
            for size in (0, -1):
                with self.subTest(size=size), self.assertRaisesRegex(ValueError, "positive"):
                    split_csv(source, size)
            self.assertEqual(list(source.parent.glob("questions_part_*.csv")), [])


if __name__ == "__main__":
    unittest.main()
