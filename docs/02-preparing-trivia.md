# Preparing Trivia Questions

Trivia Countdown reads questions from a CSV file. You can create the file in a spreadsheet application or edit it as plain text.

## Required Columns

The first row must contain these column names exactly:

```csv
question,answer_1,answer_2,answer_3,answer_4,correct_answer
What planet is known as the Red Planet?,Venus,Mars,Jupiter,Saturn,2
Which element has the chemical symbol O?,Gold,Oxygen,Silver,Iron,2
```

| Column | Description |
| --- | --- |
| `question` | The question shown above the four answers. |
| `answer_1` | The first answer choice. |
| `answer_2` | The second answer choice. |
| `answer_3` | The third answer choice. |
| `answer_4` | The fourth answer choice. |
| `correct_answer` | The number `1`, `2`, `3`, or `4` identifying the correct answer choice. |

`correct_answer` contains the answer number, not the answer text. In the first example row, `2` means that `answer_2` (`Mars`) is highlighted.

## Validation Rules

- Every required value must be present.
- `correct_answer` must be an integer from `1` through `4`.
- Empty rows are ignored.
- Additional columns are allowed and ignored.
- Files may use UTF-8 with or without a byte order mark.

If the file is invalid, the command reports the affected row and the value that needs attention.

## Using a Spreadsheet

You can prepare questions in Numbers, Excel, Google Sheets, or another spreadsheet application:

1. Put the required column names in the first row.
2. Enter one question per row.
3. Export or download the sheet as a UTF-8 CSV file.
4. Open the exported file once to confirm that the header and questions are present.

Spreadsheet applications handle commas and quotation marks in cells when exporting. If you edit the CSV by hand, follow standard CSV quoting rules for values that contain commas, quotation marks, or line breaks.

## Writing Readable Questions

Question and answer text wraps and shrinks automatically. Short, direct wording will remain easier to read, especially in answer choices. Render a small test before processing a long video when your questions contain lengthy text.

Use `--overlay-dir preview_overlays` to keep the generated PNG files when you want to inspect the panel layout. See [Usage and Command Reference](03-usage-and-reference.md#output-and-question-order) for details.

## Sample File

A complete five-question example is available at [`sample_objects/sample_of_5_trivia_questions.csv`](../sample_objects/sample_of_5_trivia_questions.csv).

---

[Previous: Installation](01-installation.md) | [Back to README](../README.md) | [Next: Usage and Command Reference](03-usage-and-reference.md)
