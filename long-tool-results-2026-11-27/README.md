# Long tool results

## Question

The live turn copies only the first 1,000 characters of each tool result into the say-this line (`TASK_RESULT_CAP` in `config.py`), while `http_get` returns up to 6,000 characters of page text and `web_search` up to 10 hits with 300-character snippets. The prompt-order benchmarks used short canned results, so they never tested this.

When the answer sits deep in a long result, does the spoken reply still find it? Would a higher cap, the whole result, or a short summary first do better, and at what cost in time? This is CetiMind issue #143.

## Setup

- **Date:** 2026-11-27.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC, with `qwen3.5-4b` loaded at a 6,144-token context.
- **Model and settings:** `qwen3.5-4b` for every call, with the live CetiMind settings: the intent check and replies without thinking (from [the D-parts run](../prompt-order-d-parts-2026-11-27/README.md)).
- **CetiMind:** `main` at `52d8137` plus the long-result harness (`34658fc`, `7ec2497`). A copy is in [`harness/`](harness/).
- **Profile:** the heavy profile from the earlier runs: the "Wren" persona, 177 facts, a 16-message history, a summary and 2 open jobs.
- **Run:** `bench.py --profile long --arms L,L2500,LFULL,LSUM --repeats 3`, default seed `20261126`, arms in shuffled order per line. 30 lines × 4 arms × 3 repeats = 360 turns, 0 errors, 24 minutes.

## Method

- **Lines** ([`harness/long_results.py`](harness/long_results.py)): 4 fetched pages (game patch notes, library hours, a ferry timetable, a bread recipe) and 1 web search (a marathon winner), each asked in English and Japanese, with the answer placed early, in the middle, or late. 30 lines.
- **Results:** synthetic. Each has one answer sentence and one distractor near the start: a related value that isn't the answer (last season's date, the weekday closing time, the weekday last ferry, the proofing time, last year's winner).

  | Result | English | Japanese | Answer early / middle / late |
  | --- | --- | --- | --- |
  | Fetched page | ~6,000 characters, cut with `http_get`'s note | ~2,500 characters | ~7% / 45% / 85% of the page |
  | Search | 10 hits, ~3,560 characters | 10 hits, ~2,590 characters | hit 1 / 5 / 9 |

  Early answers sit inside the first 1,000 characters on every line, and middle and late answers sit past them. Japanese pages are shorter because a 6,000-character Japanese page is about 6,000 tokens and would overflow the 6,144-token context in the tool rounds.
- **Arms:** all four run the live turn and differ only in what the say-this line gets.

  | Arm | What the reply sees |
  | --- | --- |
  | L, live | The first 1,000 characters of each result |
  | L2500 | The first 2,500 characters |
  | LFULL | The whole result |
  | LSUM | A result over 1,000 characters first goes through one thinking-off call that copies only the sentences answering the line. The reply sees that. |

- **Scoring:** the answer is named when the reply contains it in any written or spoken form (`long_results.says_answer`: "5:30", "five-thirty", "17時30分", "午後五時三十分", "6 月 12 日"). The spoken forms were added partway through the run, so [`summary.md`](summary.md) is rescored from the saved replies with [`harness/rescore.py`](harness/rescore.py). The `grounded` field in `run/turns.jsonl` is the stricter score from run time. "Distractor named instead" counts a reply that names the distractor's value and not the answer.

## Results

Full tables: [`summary.md`](summary.md). Raw rows: [`run/turns.jsonl`](run/turns.jsonl) and [`run/steps.jsonl`](run/steps.jsonl).

| Measure | L, live | L2500 | LFULL | LSUM |
| --- | --- | --- | --- | --- |
| Answer named, all | 28/90 | 62/90 | **89/90** | 77/90 |
| Answer early | 28/30 | 30/30 | 29/30 | 24/30 |
| Answer in the middle | **0/30** | 18/30 | 30/30 | 26/30 |
| Answer late | **0/30** | 14/30 | 30/30 | 27/30 |
| Distractor named instead | **23/90** | 13/90 | 0/90 | 0/90 |
| Answer time (median) | 3.78 s | 3.93 s | 4.02 s | 4.15 s |
| Say-this prompt tokens (median) | 1,864 | 2,402 | 2,871 | 1,539 |

Paired against live, LFULL was right on 62 more turns and wrong on 1 (p < 0.0001). LFULL against LSUM: 13 to 1 (p = 0.002).

## Reading

- **The 1,000-character cut hides every answer past it.** Live named none of the 60 middle or late answers.
- **The cut also makes the reply state wrong facts.** With the answer cut off, live named the distractor on 23 of 90 turns: the weekday closing time for Saturday, last year's winner, last season's date. The whole result and the summary did so 0 times.
- **The whole result is the best fix.** It named 89 of 90 answers for about 0.24 s more to the answer, with a say-this prompt about 1,000 tokens longer.
- **A summary first is worse and slower.** It named 77 of 90, and lost answers even when they were early (24 of 30). Its misses are all Japanese: it kept "20 then 22 minutes" but not the 42 total, or "June" without the 12th.
- **2,500 characters is a half step.** It found almost every Japanese answer only because the Japanese pages fit in 2,500 characters.
- **Recommendation:** stop cutting tool results at 1,000 characters in the say-this line. Guard the context by tokens instead of characters, since a long Japanese page could overflow the 6,144-token context.

## Limits

- One model, one machine, synthetic pages and lines; the Japanese lines are machine-translated.
- Only one result per turn. Two long results in one turn (a search, then a fetch) would double the say-this prompt growth.
- Japanese pages were kept at about 2,500 characters, so a full-length Japanese page, and whether it overflows the context, wasn't tested.
- "Distractor named instead" is a string match. A reply that mentions the distractor only as context and gives no answer also counts.
- 3 repeats at temperature 0.6. 90 turns per arm.
