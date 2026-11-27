# Arm D's three changes, one at a time

## Question

In run 2 of the [heavy prompt-order run](../prompt-order-heavy-2026-11-26/README.md), arm D spoke first at 0.84 s on tool lines and answered 2.9 s sooner than the tiered order (A). D changed three things at once:

1. The intent check runs with thinking off.
2. The say-this reply and the persona reply run with thinking off. A persona reply after tool rounds that called no tool still follows the chat model, as in run 2.
3. The say-this prompt lists the tool results before quoting the hold line, and tells the reply not to repeat it. The hold line is still spoken first.

Which change buys the speed, and does any of them cost accuracy?

## Setup

- **Date:** 2026-11-27.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC.
- **Model and settings:** `qwen3.5-4b` for every call, with the live CetiMind settings of 2026-11-26 pinned (see the [first run](../prompt-order-vs-full-2026-11-26/README.md)).
- **CetiMind:** the version with per-tool intent examples (see the [intent-check follow-up](../intent-cancel-example-2026-11-26/README.md#follow-up-examples-on-the-tool-spec)), plus the D1–D3 arms. Every arm's intent check carries the `schedule_cancel` example. A copy of the harness is in [`harness/`](harness/).
- **Profile:** the heavy profile from the earlier run (`--profile heavy`): the "Wren" persona, 177 facts with 12 traps, a 16-message history, a summary and 2 open jobs.
- **Run:** `bench.py --profile heavy --arms A,D1,D2,D3,D --repeats 3`, default seed `20261126`. 58 lines (29 EN, 29 JA) × 5 arms × 3 repeats = 870 turns, 0 errors, 87 minutes.

## Method

Arms interleaved in shuffled order on each line.

| Arm | Intent check thinks | Replies think | Results first in the say-this prompt |
| --- | --- | --- | --- |
| A, tiered | yes | yes | no |
| D1 | **no** | yes | no |
| D2 | yes | **no** | no |
| D3 | yes | yes | **yes** |
| D, all three | no | no | yes |

A and D are rerun here rather than reused, because the intent check has changed since the earlier runs.

In this run, the Tools and Replies rows follow the chat model, which thinks, so A's intent check and replies think. Current CetiMind keeps the intent check from thinking unless the Tools row is On, and new settings start with Replies Off.

## Results

Full tables: [`summary.md`](summary.md).

Times are medians of wall-clock time around non-streaming calls, in ms (p90 in brackets). First word, answer, tool lines and chit-chat are as defined in the [heavy prompt-order run](../prompt-order-heavy-2026-11-26/README.md#results). First word isn't time to first token.

| Measure | A | D1 | D2 | D3 | D |
| --- | --- | --- | --- | --- | --- |
| Right tools, in the turn | 161/174 (93%) | 165/174 (95%) | 163/174 (94%) | 160/174 (92%) | 167/174 (96%) |
| Paired vs A, exact McNemar (A-only / arm-only, p) | | 3 / 7, 0.34 | 3 / 5, 0.73 | 5 / 4, 1.00 | 1 / 7, 0.07 |
| False claims (108 tool turns) | 0 | 0 | 0 | 0 | 0 |
| Grounded in the tool result | 79% | 76% | 85% | 83% | 87% |
| Partial claim (of 12 two-tool turns) | 1 | 2 | 2 | **6** | 4 |
| Reply repeats the hold | 2% | 5% | 0% | **9%** | 1% |
| First word, tool lines | 1,873 (2,156) | **662 (847)** | 1,899 (2,126) | 1,894 (2,136) | 676 (839) |
| Answer, tool lines | 6,308 (8,602) | 5,060 (6,726) | **5,099 (7,313)** | 6,135 (9,052) | 3,823 (5,769) |
| First word, chit-chat | 3,093 (3,450) | 2,236 (2,766) | **1,806 (2,154)** | 3,131 (3,417) | 1,072 (1,430) |
| Reasoning tokens per turn (mean) | 515 | 376 | 374 | 511 | 252 |

By language, right tools in the turn: A 95% in English and 90% in Japanese, D 97% and 95%.

## Reading

- **No change cost tool accuracy significantly.** No arm differed from A at p < 0.05. D got 7 turns right that A missed, and A got 1 that D missed (p = 0.07, not significant). The run is too small to show the arms are the same.
- **D1 (intent thinking off) gave the fast first word on tool lines.** The intent check dropped from 1,487 ms to 307 ms, and the hold line is ready right after it. The tool-line answer also dropped to 5,060 ms, about the same as D2, because the intent check is on the critical path.
- **D2 (reply thinking off) gave the fast answer and chit-chat.** The say-this reply dropped from 1,796 ms to 537 ms and the persona reply from 1,737 ms to 465 ms.
- **D, with D1 and D2 together, was fastest on every time row.** D3 alone was no faster than A.
- **D3 (results first) had the most reply problems.** It repeated the hold line on 9% of replies and claimed a second tool that never ran on 6 of 12 two-tool turns. D, which includes D3, had 4 of 12 partial claims against A's 1.
- **Recommendation:** keep D1 and D2, which are now CetiMind's defaults, and drop D3. The partial-claim counts are small (12 turns per arm), so this isn't a settled result.

## Limits

- One model, one machine, synthetic lines and context. The Japanese lines are machine-translated.
- 3 repeats at temperature 0.6. 174 turns per arm can't separate arms closer than about 5 points.
- The p-values are uncorrected across the four comparisons against A.
- Partial claims and hold repeats are regex-scored (`heavy.partial_claim`, the hold overlap check in `bench.py`), not hand-checked.
- **Timing:** wall clock around non-streaming calls, with no time-to-first-token.

## Files

- [`harness/`](harness/): a copy of the bench (`bench.py`, `heavy.py`, `lines.py`, `summarize.py`), with the D1–D3 arms.
- `run/turns.jsonl`: one row per turn. `run/steps.jsonl`: one row per model call.
- [`summary.md`](summary.md): the output of `summarize.py run`.

To run it again, copy `harness/` into `bench/prompt_order/` in a CetiMind checkout with per-tool intent examples. To repeat this run's A arm, use a checkout from before the intent check started thinking only when the Tools row is On. On current CetiMind, that A arm would run with thinking off on the intent check.

```bash
uv run python bench/prompt_order/bench.py --base-url http://HOST:PORT/v1 --out run --profile heavy --arms A,D1,D2,D3,D --repeats 3
uv run python bench/prompt_order/summarize.py run
```
