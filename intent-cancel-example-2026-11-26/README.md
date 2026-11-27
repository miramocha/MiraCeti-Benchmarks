# Intent check: one cancel example

## Question

In the heavy prompt-order runs (`prompt-order-heavy-2026-11-26`, run 2), the fast intent check with thinking off (arm D) missed "Forget the oven reminder, I already checked it" in both languages, so no tool ran. The 2026-11-16 [tool-model-split](../tool-model-split-2026-11-16/README.md) run had found the same line missed by every intent check.

Does one cancel example in the intent check's instruction fix cancel lines? Does it add false alarms on lines that only mention reminders? And does thinking help?

## Setup

- **Date:** 2026-11-26.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC.
- **Model:** `qwen3.5-4b`, loaded with context 6144, `parallel` 4, flash attention, f16 K/V, and a server reasoning budget of 256. `nvidia/nemotron-3-nano-4b` was also loaded but not called.
- **CetiMind:** `main` at `c4cd140` for the code under test. The harness, `bench/prompt_order/intent_bench.py`, was committed afterward as `8750404` on branch `local/batch` (copied to [`harness/`](harness/)).

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

## Follow-up: examples on the tool spec

CetiMind issue #137 moved the example out of `INTENT_INSTRUCTION` and onto the tool. `ToolSpec` gained an optional `intent_examples` field, and `IntentRouter` lists each example on its own indented line under its tool's line. The tool lines don't change from turn to turn, so the prompt cache still holds. `schedule_cancel` brings the one example. The bench was rewritten as a regression check that runs whenever the instruction or an example changes.

### Setup

- **Date:** 2026-11-26, the same evening and PC as the first run.
- **Model:** `qwen3.5-4b` on LM Studio, with `text-embedding-nomic-embed-text-v1.5` also loaded and not called. The load settings weren't recorded again.
- **CetiMind:** branch `local/batch`. Run 1 at `f202b32`. Runs 2 and 3 on uncommitted changes, and run 3's changes are what `45d28ad` committed. The harness is in [`harness-spec/`](harness-spec/), and the history and test lines are the same as in [`harness/`](harness/).

### Method

- **The call:** the same as the first run. `IntentRouter.decide` alone, thinking off, temperature 0, strict JSON, 6 tools.
- **Variants:** two, in shuffled order on each line, for 5 repeats.

  | Variant | Instruction | Tool lines |
  | --- | --- | --- |
  | `live` | Today's `INTENT_INSTRUCTION` | With every `intent_examples` line |
  | `bare` | Today's `INTENT_INSTRUCTION` | With the examples stripped |

  Both use the same instruction, so in run 3 `bare` also has the new instruction sentence.
- **Lines:** the same 78 lines per repeat as the first run, in the same groups (780 checks per run). The held-out cancel lines and near misses now live in [`harness-spec/intent_lines.py`](harness-spec/intent_lines.py). The bench stops if an example reuses the wording of any bench line.
- **The bar for `live`:**
  - At least 80% of held-out cancel lines right.
  - No false alarms on the near misses.
  - No group among other tool lines, chit-chat, either way and test-set cancels below `bare`.
- **What changed between runs:**

  | Run | `schedule_cancel` example | Instruction |
  | --- | --- | --- |
  | 1 | `Example: "Never mind the laundry alarm, I already emptied it." needs schedule_cancel.` | Unchanged from the first run |
  | 2 | Adds `, because the user wants an existing reminder removed` | Unchanged |
  | 3 | As run 2 | Adds "A tool is needed only when the user asks for something the tool does, not when they just mention or complain about the topic." |

  Unlike the first run's example, these name only `schedule_cancel`, not `schedule_list` as well.

### Results

780 checks per run. None failed.

| Group | Run 1 `live` | Run 2 `live` | Run 3 `live` | Run 3 `bare` |
| --- | --- | --- | --- | --- |
| Cancel lines in the test set | 20/20 | 20/20 | **20/20** | 10/20 (50%) |
| New cancel lines (held out) | 45/60 (75%) | 60/60 | **60/60** | 30/60 (50%) |
| Near misses (need no tool) | 30/40 (75%) | 30/40 (75%) | **40/40** | 40/40 |
| Other tool lines | 160/160 | 155/160 (97%) | 155/160 (97%) | 155/160 (97%) |
| Chit-chat | 70/70 | 70/70 | 70/70 | 70/70 |
| Either way | 40/40 | 40/40 | 40/40 | 40/40 |
| Median time (p90) | 337 ms (584) | 334 ms (879) | 327 ms (916) | 330 ms (936) |
| Meets the bar | No | No | **Yes** | – |

`bare` in runs 1 and 2 matched run 3's `bare`, except on the near misses: 35/40 in both.

Every miss repeated on all 5 repeats:

- **Run 1:**
  - "No need to remind me about water today", in both languages, picked nothing.
  - "Can you clear my reminders?" picked only `schedule_list`.
  - "My reminders app at work is so annoying" picked `schedule_cancel`.
  - The Japanese "I cancelled my gym membership today" picked `web_search`.
- **Run 2:** the cancels were all right, but "My reminders app at work is so annoying" picked `schedule_cancel` in both languages. The Japanese two-tool line "What time is it? And remind me to stretch in 10 minutes" picked only `schedule_create`.
- **Run 3:** only that two-tool line, the same as `bare` in every run.

### Reading the follow-up

- **The reason clause carried the held-out cancels.** With only the line, the example got 75% of them, below the bar and below the first run's 83%. With "because the user wants an existing reminder removed", it got all 60, including the soft "No need to remind me…" that the first run never got.
- **The example made the check trigger on complaints.** "My reminders app at work is so annoying" picked `schedule_cancel` in runs 1 and 2. A cancel example alone teaches "reminders, said with annoyance, means cancel".
- **One instruction sentence fixed the complaints without losing cancels.** Run 3 kept all the cancels and had no false alarms. It fixed `bare` too (35/40 to 40/40), so the sentence helps with or without examples.
- **The two-tool line isn't an example problem.** The Japanese time-plus-reminder line missed `current_time` in `bare` in every run, and in `live` from run 2 on. Run 1's 160/160 says the example line can move it. This bench doesn't test a fix for it.
- **No speed cost.** `live` and `bare` medians are within 6 ms of each other in every run.
- **End to end:** arm D, rerun with run 3's prompt on the heavy profile, got the cancel lines right on 10 of 12 turns, up from 6 of 12. See [run 3 of the heavy prompt-order run](../prompt-order-heavy-2026-11-26/README.md#run-3-arm-d-after-the-intent-fix).

## Limits

- **Scope:** one model, one example, 6 tools, single-turn lines. The intent check alone, not a full turn.
- **Sample:** the held-out cancel lines are only 6 per language. "No need to remind me…" shows that softer phrasings still slip through.
- **Language:** the example is in English. Japanese improved just as much, but a Japanese example wasn't tested.
- **Unseen tools:** in the first run, the instruction names two tools. A future tool set without `schedule_cancel` would need the example adjusted. The follow-up fixes this: the example travels with its tool.
- **Follow-up runs:** the bar was tuned on the same line sets it's scored on. Run 3 is the third try, so its held-out cancels aren't fully held out any more. The near misses are only 4 per language.

## Files

- **First run:**
  - [`harness/intent_bench.py`](harness/intent_bench.py), with [`harness/heavy.py`](harness/heavy.py) and [`harness/lines.py`](harness/lines.py) for the test lines and history.
  - `run/calls.jsonl`: one row per intent check (variant, line, group, pick, right or wrong, time).
  - `run/raw-output.txt`: the console log.
- **Follow-up:**
  - [`harness-spec/intent_bench.py`](harness-spec/intent_bench.py) and [`harness-spec/intent_lines.py`](harness-spec/intent_lines.py). They also need `harness/heavy.py` and `harness/lines.py`.
  - `run-spec1/`, `run-spec2/` and `run-spec3/`: `calls.jsonl`, `summary.json` (the groups and the bar checks) and `raw-output.txt` for each run.

To run the follow-up again from a CetiMind checkout (it exits 1 when `live` misses the bar):

```bash
uv run python bench/prompt_order/intent_bench.py --base-url http://HOST:PORT/v1 --out DIR --repeats 5
```

CetiMind's `intent_bench.py` is now the follow-up version, with `live` and `bare`. To repeat the first run (`off`, `off_example`, `on128`), check out CetiMind at `8750404`, where the bench file matches [`harness/intent_bench.py`](harness/intent_bench.py) and `INTENT_INSTRUCTION` and the tools are as they were, and run the same command there.
