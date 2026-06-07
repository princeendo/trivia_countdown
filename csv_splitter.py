#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


def split_csv(input_file: Path, row_count: int) -> None:
    if row_count <= 0:
        raise ValueError("row_count must be positive")

    with input_file.open("r", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    if not reader:
        raise ValueError("CSV file is empty")

    header = reader[0]
    rows = reader[1:]
    total_rows = len(rows)

    if total_rows == 0:
        raise ValueError("CSV file contains only a header row")

    file_count = max(1, total_rows // row_count)

    output_dir = input_file.parent
    stem = input_file.stem
    suffix = input_file.suffix

    for i in range(file_count):
        start = i * row_count

        if i == file_count - 1:
            chunk = rows[start:]
        else:
            chunk = rows[start:start + row_count]

        output_file = output_dir / f"{stem}_part_{i + 1:03d}{suffix}"

        with output_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(chunk)

        print(f"Wrote {output_file} ({len(chunk)} data rows)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a CSV into multiple files by row count, preserving the header."
    )
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("row_count", type=int)

    args = parser.parse_args()
    split_csv(args.csv_file, args.row_count)


if __name__ == "__main__":
    main()
