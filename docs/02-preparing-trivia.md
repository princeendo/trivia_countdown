# Preparing Trivia Questions

Trivia Countdown reads questions from a CSV file. Mac app users choose this file on the **Main** tab; source users can pass it to the GUI or command line. You can create the file in a spreadsheet application or edit it as plain text.

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

If the file is invalid, the command or GUI reports the affected row and the value that needs attention. In the GUI, choose the CSV on the Main tab; its rows appear in the Questions tab after validation.

## Using a Spreadsheet

You can prepare questions in Numbers, Excel, Google Sheets, or another spreadsheet application:

1. Put the required column names in the first row.
2. Enter one question per row.
3. Export or download the sheet as a UTF-8 CSV file.
4. Open the exported file once to confirm that the header and questions are present.

Spreadsheet applications handle commas and quotation marks in cells when exporting. If you edit the CSV by hand, follow standard CSV quoting rules for values that contain commas, quotation marks, or line breaks.

## Writing Readable Questions

Question and answer text wraps and shrinks automatically. Short, direct wording will remain easier to read, especially in answer choices. Render a small test before processing a long video when your questions contain lengthy text.

The GUI Main tab displays a static source-video frame with the selected question overlay. Select a row in the Questions tab to inspect that question. **Show answer reveal in preview** is enabled by default; turn it off to inspect the question-only panel. The Questions tab displays every validated row, but only the first rows that fit within the video's available time are rendered. Previewing a later row does not guarantee that it will appear in the final video.

If **Randomize question order** is enabled, provide a random seed when you need the Questions tab, preview, and final render to use the same order. Without a seed, the order can be regenerated separately and may differ between the preview and the completed video. Use `--overlay-dir preview_overlays` to keep full-resolution PNG files when you need to inspect command-line renders. See [Usage and Command Reference](03-usage-and-reference.md#output-and-question-order) for details.

## Sample File

A complete five-question example is included at the top level of the mounted DMG as **Sample Trivia Questions.csv**. Source users can find the same file at [`sample_objects/sample_of_5_trivia_questions.csv`](../sample_objects/sample_of_5_trivia_questions.csv).

---

[Previous: Installation](01-installation.md) | [Back to README](../README.md) | [Next: Usage and Command Reference](03-usage-and-reference.md)
