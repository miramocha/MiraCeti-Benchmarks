# Arm D's three changes, one at a time

## Question

In the [heavy prompt-order run](../prompt-order-heavy-2026-11-26/README.md), arm D spoke first in 0.84 s on tool lines and answered about 3 s sooner than the tiered order (A). D changed three things at once:

1. The intent check runs with thinking off.
2. The replies (say-this and the plain persona reply) run with thinking off.
3. The say-this message puts the tool results before the hold line and says not to repeat the hold.

Which change buys the speed, and does any of them cost accuracy? This is CetiMind issue #139.

## Setup

- **Date:** 2026-11-27.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC.
- **Model and settings:** `qwen3.5-4b` for every call, with the live CetiMind settings of 2026-11-26 pinned (see the [first run](../prompt-order-vs-full-2026-11-26/README.md)).
- **CetiMind:** `main` at `b63c957` plus the D1–D3 arms (`fba5ae5`). `main` includes #137, so every arm's intent check carries the `schedule_cancel` example. A copy of the harness is in [`harness/`](harness/).
- **Profile:** the heavy profile from the earlier run (`--profile heavy`): the "Wren" persona, 177 facts with 12 traps, a 16-message history, a summary and 2 open jobs.
- **Run:** `bench.py --profile heavy --arms A,D1,D2,D3,D --repeats 3`, default seed `20261126`. Arms interleaved in shuffled order on each line. 58 lines (29 EN, 29 JA) × 5 arms × 3 repeats = 870 turns, 0 errors, 87 minutes.

## Arms

| Arm | Intent check thinks | Replies think | Results before the hold |
| --- | --- | --- | --- |
| A, tiered | yes | yes | no |
| D1 | **no** | yes | no |
| D2 | yes | **no** | no |
| D3 | yes | yes | **yes** |
| D, all three | no | no | yes |

A and D are rerun here rather than reused, because the intent check changed (#137) since the earlier runs.

## Results

Full tables: [`summary.md`](summary.md). Raw rows: [`run/turns.jsonl`](run/turns.jsonl) (one per turn) and [`run/steps.jsonl`](run/steps.jsonl) (one per model call).

| Measure | A | D1 | D2 | D3 | D |
| --- | --- | --- | --- | --- | --- |
| Right tools, in the turn | 93% | 95% | 94% | 92% | 96% |
| Paired vs A (A-only / arm-only, p) | | 3 / 7, 0.34 | 3 / 5, 0.73 | 5 / 4, 1.00 | 1 / 7, 0.07 |
| False claims (108 tool turns) | 0 | 0 | 0 | 0 | 0 |
| Grounded in the tool result | 79% | 76% | 85% | 83% | 87% |
| Partial claim (of 12 two-tool turns) | 1 | 2 | 2 | **6** | 4 |
| Reply repeats the hold | 2% | 5% | 0% | **9%** | 1% |
| First word, tool lines (median) | 1.87 s | **0.66 s** | 1.90 s | 1.89 s | 0.68 s |
| Answer, tool lines | 6.31 s | 5.06 s | **5.10 s** | 6.14 s | 3.82 s |
| First word, chit-chat | 3.09 s | 2.24 s | **1.81 s** | 3.13 s | 1.07 s |
| Reasoning tokens per turn (mean) | 515 | 376 | 374 | 511 | 252 |

Right tools by language: A 95% EN / 90% JA, D 97% / 95%.

## Reading

- **No change costs tool accuracy.** No arm differs from A at p < 0.05. D leans better (7 turns only D got right, 1 only A got right, p = 0.07). The earlier gap (D 89% vs A 92%) is gone now that the intent check has the cancel example.
- **D1 (intent thinking off) gives the fast first word on tool lines.** The intent check drops from 1.49 s to 0.31 s, and the hold plays right after it.
- **D2 (reply thinking off) gives the fast answer and chit-chat.** The say-this call drops from 1.80 s to 0.54 s and the persona reply from 1.74 s to 0.47 s.
- **D1 and D2 add up to D's times.** D3 adds no speed.
- **D3 (results first) makes replies worse.** It repeated the hold on 9% of replies and claimed a second tool that never ran on 6 of 12 two-tool turns. D, which includes D3, had 4 of 12 partial claims against A's 1.
- **Recommendation:** keep D1 and D2 in the live order and drop D3. The partial-claim counts are small (12 turns per arm), so D3's harm is likely, not settled.

## Limits

- One model, one machine, synthetic lines and context; the Japanese lines are machine-translated.
- 3 repeats at temperature 0.6. 174 turns per arm can't separate arms closer than about 5 points.
- The p-values are uncorrected across the four comparisons against A.
- Partial claims and hold repeats are regex-scored (`heavy.partial_claim`, the hold overlap check in `bench.py`), not hand-checked.
