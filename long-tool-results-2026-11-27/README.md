# Long tool results

## Question

At the time of this run, the live turn copied only the first 1,000 characters of each tool result into the say-this prompt (`TASK_RESULT_CAP` in `config.py`), while `http_get` returned up to 6,000 characters of page text and `web_search` up to 10 hits with 300-character snippets. The prompt-order benchmarks used short canned results, so they never tested this.

When the answer sits deep in a long result, does the spoken reply still find it? Would a higher cap, the whole result, or a short summary first do better, and at what cost in time?

## Setup

- **Date:** 2026-11-27.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC.
- **Model:** `qwen3.5-4b` for every call, loaded at a 6,144-token context.
- **Settings:** the live CetiMind settings, with the Tools row on Follow the model and Replies Off, so the intent check and replies don't think (see [the D-parts run](../prompt-order-d-parts-2026-11-27/README.md)).
- **CetiMind:** the version where the intent check and replies don't think by default, plus the long-result arms. A copy of the harness is in [`harness/`](harness/).
- **Profile:** `long`, which uses the heavy profile's "Wren" persona, 177 facts, 16-message history, summary and 2 open jobs, with the long results below.
- **Run:** `bench.py --profile long --arms L,L2500,LFULL,LSUM --repeats 3`, default seed `20261126`. 30 lines × 4 arms × 3 repeats = 360 turns, 0 errors, 24 minutes.

## Method

Arms interleaved in shuffled order on each line.

- **Lines** ([`harness/long_results.py`](harness/long_results.py)): 4 fetched pages (game patch notes, library hours, a ferry timetable, a bread recipe) and 1 web search (a marathon winner), each asked in English and Japanese, with the answer placed early, in the middle, or late. 30 lines.
- **Results:** synthetic. Each has one answer sentence and one distractor near the start: a related value that isn't the answer (last season's date, the weekday closing time, the weekday last ferry, the proofing time, last year's winner).

  | Result | English | Japanese | Answer early / middle / late |
  | --- | --- | --- | --- |
  | Fetched page | ~6,000 characters, cut with `http_get`'s note | ~2,500 characters | ~7% / 45% / 85% of the page |
  | Search | 10 hits, ~3,560 characters | 10 hits, ~2,590 characters | hit 1 / 5 / 9 |

  Early answers sit inside the first 1,000 characters on every line, and middle and late answers sit past them. Japanese pages are shorter because a 6,000-character Japanese page is about 6,000 tokens and would overflow the 6,144-token context in the tool rounds.
- **Arms:** all four run the live turn and differ only in what goes into the say-this prompt.

  | Arm | What the say-this prompt gets |
  | --- | --- |
  | L, live | The first 1,000 characters of each result |
  | L2500 | The first 2,500 characters |
  | LFULL | The whole result |
  | LSUM | A result over 1,000 characters first goes through one thinking-off call that keeps only the sentences answering the user's line. The say-this prompt gets that. |

- **Scoring:** the answer is named when the reply contains it in any written or spoken form (`long_results.says_answer`: "5:30", "five-thirty", "17時30分", "午後五時三十分", "6 月 12 日"). The spoken forms were added partway through the run, so [`summary.md`](summary.md) is rescored from the saved replies with [`harness/rescore.py`](harness/rescore.py). The `grounded` field in `run/turns.jsonl` is the stricter score from run time. `summary.md` doesn't use it. "Distractor named instead" counts a reply that names the distractor's value and not the answer.

## Results

Full tables: [`summary.md`](summary.md).

Times are medians of wall-clock time around non-streaming calls, in ms (p90 in brackets). Answer is as defined in the [heavy prompt-order run](../prompt-order-heavy-2026-11-26/README.md#results).

| Measure | L, live | L2500 | LFULL | LSUM |
| --- | --- | --- | --- | --- |
| Answer named, all | 28/90 | 62/90 | **89/90** | 77/90 |
| Answer early | 28/30 | 30/30 | 29/30 | 24/30 |
| Answer in the middle | **0/30** | 18/30 | 30/30 | 26/30 |
| Answer late | **0/30** | 14/30 | 30/30 | 27/30 |
| Distractor named instead | **23/90** | 13/90 | 0/90 | 0/90 |
| Answer | 3,783 (4,612) | 3,927 (4,827) | 4,021 (4,734) | 4,148 (5,517) |
| Say-this prompt tokens (median) | 1,864 | 2,402 | 2,871 | 1,539 |

Paired against live (exact McNemar), LFULL was right on 62 more turns and wrong on 1 (p < 0.0001). LFULL against LSUM: 13 to 1 (p = 0.002).

## Reading

- **Live named no answer past the 1,000-character cut.** It named none of the 60 middle or late answers.
- **With the answer cut off, live often named the distractor instead.** It did on 23 of 90 turns: the weekday last ferry, last year's winner, the weekday closing time for Saturday. The whole result and the summary did so 0 times.
- **The whole result did best.** It named 89 of 90 answers for about 240 ms more on the median answer, with a say-this prompt about 1,000 tokens longer.
- **A summary first did worse.** It named 77 of 90, lost answers even when they were early (24 of 30), and had the highest median answer time. Twelve of its 13 misses were Japanese: it often kept "20 then 22 minutes" but not the 42 total, or "June" without the 12th.
- **2,500 characters was a half step.** It found almost every Japanese answer only because the Japanese pages fit in 2,500 characters.
- **Recommendation:** stop cutting tool results at 1,000 characters in the say-this prompt, and guard the context by tokens instead. CetiMind now has a tool-result token budget. This run didn't test it.

## Limits

- One model, one machine, synthetic pages and lines. The Japanese lines are machine-translated.
- Only one result per turn. Two long results in one turn (a search, then a fetch) would double the say-this prompt growth.
- Japanese pages were kept at about 2,500 characters, so a full-length Japanese page, and whether it overflows the context, wasn't tested.
- "Distractor named instead" is a string match. A reply that mentions the distractor only as context and gives no answer also counts.
- 3 repeats at temperature 0.6. 90 turns per arm.
- **Timing:** wall clock around non-streaming calls, with no time-to-first-token.
- The p-values are uncorrected across the two paired comparisons.
- The published run inserted the early search answer after the distractor, so that distractor sat at hit 3 on early search lines. Mid and late search lines already had it at hit 2. The copy in `harness/` keeps it at hit 2 for every placement.

## Files

- [`harness/`](harness/): a copy of the bench (`bench.py`, `heavy.py`, `lines.py`), plus [`long_results.py`](harness/long_results.py) for the long results and lines and [`rescore.py`](harness/rescore.py) for the spoken-form rescoring.
- `run/turns.jsonl`: one row per turn. `run/steps.jsonl`: one row per model call.
- [`summary.md`](summary.md): the rescored tables, from `rescore.py`.

To run it again, copy `harness/` into `bench/prompt_order/` in a CetiMind checkout from before the tool-result token budget, then:

```bash
uv run python bench/prompt_order/bench.py --base-url http://HOST:PORT/v1 --out run --profile long --arms L,L2500,LFULL,LSUM --repeats 3
uv run python bench/prompt_order/rescore.py run
```
