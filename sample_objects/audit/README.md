# Collection Audit

These tables document the consolidation of the original sample collection and the 100 new additions. They are metadata, not trivia inputs for the app.

## Tables

- [`source_index.csv`](source_index.csv): one entry for every original data row (1,279 entries). `source_file` is relative to `sample_objects/`; `source_row` identifies the original CSV record. Included and duplicate rows point to their canonical `master_row`. Excluded rows have an empty `master_row` and an explanation.
- [`clarifications.csv`](clarifications.csv): original and final question wording, all four answer choices, and correct answer text for the 51 retained questions clarified during review. Choices are listed in their original position order, separated by ` | `.
- [`new_question_sources.csv`](new_question_sources.csv): the 100 additions, numbered 1–100, with their master location, correct answer text, and a biblical passage or historical source URL. Questions 1–80 are biblical; 81–100 concern church history or hymns.

All row numbers count the header as record **1**, so the first question is record **2**. Use question text to identify records if the master is subsequently edited or reordered.

## Source Dispositions

| Status | Meaning | Rows |
| --- | --- | ---: |
| `retained` | Canonical source row retained as written. | 744 |
| `retained_clarified` | Canonical source row retained with a wording or choice correction. | 51 |
| `duplicate_prompt` | Another occurrence of the same normalized question text; choices or difficulty may differ. | 263 |
| `duplicate_fact` | A differently worded question testing an already retained fact, including any copies of that wording. | 175 |
| `excluded_topic` | Astronomy, general science, geography, or literature outside this collection's scope. | 38 |
| `excluded_ambiguous` | An unsupported or insufficiently specific premise. | 8 |

Semantic duplicate decisions were reviewed manually after normalizing question text and examining similarity candidates. Questions about genuinely different details of the same narrative or historical figure were retained. The master and sets contain 795 retained questions plus 100 new questions, for 895 total.

## Excluded Ambiguous Premises

The eight affected source rows represent these six questions:

1. **Who accompanied Paul and Silas out of Philippi after the jail miracle?** Acts 16:40 does not identify an additional traveling companion; the original question depends on an unsupported inference.
2. **Which church father taught Gregory Nazianzen and Basil?** The intended teacher and context were not specified, and the correct choice was “None of these.”
3. **Who was the first person baptized by Philip in Acts 8?** The original answer was the Ethiopian official, but Acts 8:12–13 already describes earlier baptisms.
4. **What was the name of Abraham's servant who sought a wife for Isaac?** Genesis 24 does not name the servant. Identifying him with Eliezer from Genesis 15 is an inference.
5. **Which king of Assyria captured Samaria?** The unqualified attribution is disputed across the Shalmaneser V/Sargon II transition.
6. **Who was Jesus placed in a manger beside after He was born?** Luke 2:7 describes the manger but does not identify a person beside whom he was placed.

The original versions remain available in the archive. The master includes clearer existing questions about Philip's encounter with the Ethiopian official and other related subjects where appropriate.

## New-Question References

Biblical answers were checked against the cited passages, using the public-domain KJV transcription at [thiagobodruk/bible](https://github.com/thiagobodruk/bible/blob/master/json/en_kjv.json) and selected [World English Bible passages](https://bible-api.com/). Question wording modernizes terms such as *kine*, *pulse*, and *pence*. The reference table links to the passages on Bible Gateway; English translations vary in spelling and wording.

Historical answers were checked using the linked Hymnary entries, New Advent texts and encyclopedia articles, Library of Congress exhibit, Lausanne Movement account, and encyclopedia articles. Each question asks for the specific person, work, event, or detail supported by its reference. The additions also underwent a separate comparison with all original prompts and with one another for equivalent facts; textual similarity was a review aid rather than the definition of novelty.
