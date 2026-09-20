# Sample Trivia Collection

The active collection contains **895 Bible and church-related questions**: 795 retained from the original CSVs and 100 new additions (80 Bible questions and 20 church-history or hymn questions).

## Choose a File

| Path | Contents |
| --- | --- |
| [`master_trivia.csv`](master_trivia.csv) | All 895 questions, with repeated prompts and same-fact paraphrases consolidated. |
| [`sets/trivia_set_001.csv`](sets/trivia_set_001.csv) through [`sets/trivia_set_038.csv`](sets/trivia_set_038.csv) | 38 numbered files, each containing exactly 23 questions plus a header. |
| [`sets/trivia_remainder.csv`](sets/trivia_remainder.csv) | The remaining 21 questions plus a header. |
| [`sample_of_5_trivia_questions.csv`](sample_of_5_trivia_questions.csv) | The separate general-trivia demo used by the Mac DMG and quick-start documentation. |
| [`archive/`](archive/) | The 42 original batch CSVs, preserved byte-for-byte for reference. |
| [`audit/`](audit/) | Source mappings, clarification records, and references for all 100 additions. These are review tables, not playable trivia files. |

Each active trivia CSV uses this header:

```csv
question,answer_1,answer_2,answer_3,answer_4,correct_answer,difficulty
```

`correct_answer` is the 1-based answer position. `difficulty` retains the collection's editorial 1–8 scale, with lower numbers easier; the application ignores this extra column. The new questions have 25 correct answers in each of the four positions.

The numbered sets mix Bible content with church history, theology, and hymns. Each full set includes six or seven church-related questions, and questions progress from lower to higher difficulty within each set. The set order is fixed. Concatenating the numbered sets in order and then the remainder, without their headers, exactly reproduces the master. No question is repeated between sets.

## Use a Set

Choose a numbered CSV in the GUI, or run this from the repository root:

```sh
uv run python make_trivia_countdown.py input.mp4 sample_objects/sets/trivia_set_001.csv
```

With the default timing settings, all 23 questions require a video at least **312.5 seconds (5 minutes 12.5 seconds)** long. See [Timing and Video Capacity](../docs/03-usage-and-reference.md#timing-and-video-capacity) for the calculation and timing options.

## Collection Review

The original 43 CSVs contained 1,279 data rows, including full-batch/split-file copies and the five-question demo. Their disposition is:

| Disposition | Original rows |
| --- | ---: |
| Retained as distinct questions | 795 |
| Repeated prompts or equivalent tested facts | 438 |
| Non-Bible/non-church topics | 38 |
| Unsupported or ambiguous premises | 8 |
| **Total** | **1,279** |

Of the 795 retained questions, 51 received wording or answer-choice clarifications. For example, Philip in Acts 8 is identified as an evangelist, traditional authorship is qualified, and Reuel is no longer offered as a wrong alternative to Jethro. The eight excluded ambiguous rows represent six distinct questions, some of which had split-file copies; see the [audit notes](audit/README.md).

The review compared the fact being tested, not just matching strings. Different wording, reversed question/answer direction, and reordered choices did not make a repeated fact new. Distinct details about the same person or event remain separate questions. The 100 additions were compared against the entire original collection and each other, with supporting biblical passages or historical references recorded in [`audit/new_question_sources.csv`](audit/new_question_sources.csv).

## Editing and Splitting

Treat `master_trivia.csv` as the active source of truth. The files in `sets/` are snapshots, so edits to the master do not automatically update them. The audit tables document this consolidation; their row references must be updated if questions are reordered or removed.

For other CSVs, the repository's splitter can create parts beside its input:

```sh
uv run python csv_splitter.py /path/to/questions.csv 23
```

It writes `questions_part_001.csv`, `questions_part_002.csv`, and so on. Every part repeats the header and contains at most 23 data records; the last part contains any smaller remainder. A header is not counted as a question. This replaces the previous behavior that appended leftovers to an oversized last part. Existing matching part filenames are overwritten, but obsolete parts from earlier runs are not removed; use a clean working folder when re-splitting. This generic command does not recreate the curated `sets/` filenames or mix questions by topic and difficulty.
