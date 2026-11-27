# Intent check: one cancel example

## Question

In the heavy prompt-order runs (`prompt-order-heavy-2026-11-26`, run 2), the fast intent check with thinking off (arm D) missed "Forget the oven reminder, I already checked it" in both languages, so no tool ran. The 2026-11-16 [tool-model-split](../tool-model-split-2026-11-16/README.md) run had found the same line missed by every intent check.

Does one cancel example in the intent check's instruction fix cancel lines? Does it add false alarms on lines that only mention reminders? And does thinking help?

## Setup

- **Date:** 2026-11-26.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC.
- **Model:** `qwen3.5-4b`, loaded with context 6144, `parallel` 4, flash attention, f16 K/V, and a server reasoning budget of 256. `nvidia/nemotron-3-nano-4b` was also loaded but not called.
- **CetiMind:** `main` at `c4cd140`, with the harness in `bench/prompt_order/intent_bench.py` (copied to [`harness/`](harness/)).

## Method

- **The call:** CetiMind's `IntentRouter.decide` on its own, with no turn after it. That's temperature 0 and strict JSON (`{"tools": [...]}`). Each check sees the 6 tools (`current_time`, `schedule_create`, `schedule_list`, `schedule_cancel`, `web_search`, `http_get`), the line, and the last assistant line of the heavy profile's history.
- **Variants:** the three run in shuffled order on each line, for 5 repeats.

  | Variant | Thinking | Instruction |
  | --- | --- | --- |
  | `off` | off | Today's `INTENT_INSTRUCTION` (arm D's intent check) |
  | `off_example` | off | Today's instruction, plus the cancel example below |
  | `on128` | on, Tools cap 128 | Today's instruction (arm A's intent check under the live settings) |

  The example added to the instruction:

  > Example: "Never mind the laundry alarm, I already emptied it." needs schedule_list and schedule_cancel, because the user wants an existing reminder removed.

  It's worded unlike every test line, so a hit on the test lines doesn't come from copying the example. The example is in English only, for both languages.
- **Lines:** 78 per repeat (1,170 checks in all). All are synthetic, and the Japanese lines are machine-translated.

  | Group | Lines | Right when |
  | --- | --- | --- |
  | Cancel lines in the test set | 2 × 2 languages ("Cancel my water reminder.", "Forget the oven reminder, I already checked it.") | `schedule_cancel` is picked |
  | New cancel lines (held out) | 6 × 2 languages, written for this run ("Drop the water reminder, I just had a glass.", "Scrap my oven timer, the bread is out.", "Can you clear my reminders?"…) | `schedule_cancel` is picked |
  | Near misses | 4 × 2 languages that mention reminders but ask for nothing ("I already checked the oven, the bread looks great.", "I cancelled my gym membership today."…) | nothing is picked |
  | Other tool lines | 16 × 2 languages from the prompt-order set | an expected tool is picked (both on the two-tool lines) |
  | Chit-chat | 7 × 2 languages | nothing is picked |
  | Either way | 4 × 2 languages (the list lines, which the jobs list answers, and "What day is it today?") | nothing outside the expected set |

## Results

1,170 checks. None failed.

| Group | `off` | `off_example` | `on128` |
| --- | --- | --- | --- |
| Cancel lines in the test set | 13/20 (65%) | **20/20 (100%)** | 10/20 (50%) |
| New cancel lines (held out) | 28/60 (47%) | **50/60 (83%)** | 17/60 (28%) |
| Near misses (need no tool) | 35/40 (88%) | **40/40** | **40/40** |
| Other tool lines | 155/160 (97%) | **160/160** | **160/160** |
| Chit-chat | 70/70 | 70/70 | 70/70 |
| Either way | 40/40 | 40/40 | 40/40 |
| Median time (p90) | 335 ms (878) | 356 ms (470) | 1,637 ms (1,833) |

By language, on the held-out cancel lines: `off` 13/30 in English and 15/30 in Japanese; `off_example` 25/30 in both; `on128` 2/30 in English and 15/30 in Japanese.

Paired on the same line and repeat, over the cancel and near-miss lines (exact McNemar):

- **`off_example` vs `off`:** example right and `off` wrong on 34 checks; the reverse on 0. p < 0.0001.
- **`off_example` vs `on128`:** 43 vs 0. p < 0.0001.

All 10 of `off_example`'s misses were one line, in both languages: "No need to remind me about water today." It picked nothing every time. That line asks to skip a reminder without naming one to cancel, which is the vaguest of the six.

## Reading

- **One example fixes most cancels, and it generalizes.** Held-out cancel lines went from 47% to 83% right, though none of them share wording with the example. Both test-set cancel lines went to 20/20.
- **It adds no false alarms.** The near misses went from 35/40 to 40/40, so the example made the check stricter about "mentions a reminder" vs. "asks to remove one", not looser. The other tool lines and chit-chat didn't change, or improved slightly.
- **It costs about 20 ms per check.**
- **Thinking doesn't help here, and it hurts.** The thinking-on check (arm A's) got the fewest cancels right (28% held out, 2/30 in English) and took about 5 times longer. Turning thinking off in arm D wasn't what cost the cancel lines. The intent check didn't know what a cancel looks like.
- **Implication for CetiMind:** add a cancel example to `INTENT_INSTRUCTION`. With it, arm D's main accuracy gap to A (the missed cancel lines) should close at no speed cost. A rerun of D with the example on the heavy profile would confirm it end to end.

## Limits

- **Scope:** one model, one example, 6 tools, single-turn lines. The intent check alone, not a full turn.
- **Sample:** the held-out cancel lines are only 6 per language. "No need to remind me…" shows that softer phrasings still slip through.
- **Language:** the example is in English. Japanese improved just as much, but a Japanese example wasn't tested.
- **Unseen tools:** the instruction now names two tools. A future tool set without `schedule_cancel` would need the example adjusted.

## Files

- [`harness/intent_bench.py`](harness/intent_bench.py), with [`harness/heavy.py`](harness/heavy.py) and [`harness/lines.py`](harness/lines.py) for the test lines and history.
- `run/calls.jsonl`: one row per intent check (variant, line, group, pick, right or wrong, time).
- `run/raw-output.txt`: the console log.

To run it again from a CetiMind checkout:

```bash
uv run python bench/prompt_order/intent_bench.py --base-url http://HOST:PORT/v1 --out DIR --repeats 5
```
