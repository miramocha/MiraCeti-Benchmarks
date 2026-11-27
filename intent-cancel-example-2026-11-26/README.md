# Intent check: one cancel example

## Question

In the heavy prompt-order runs (`prompt-order-heavy-2026-11-26`), "Forget the oven reminder, I already checked it" was missed on every turn by both intent checks: A's, which thinks, and D's, which doesn't. The 2026-11-16 [tool-model-split](../tool-model-split-2026-11-16/README.md) run found that every intent check usually sent that line to no tool.

Does one cancel example in the intent check's instruction fix cancel lines? Does it add false alarms on lines that only mention reminders? And does thinking help?

## Setup

- **Date:** 2026-11-26.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC.
- **Model:** `qwen3.5-4b`, loaded with context 6144, `parallel` 4, flash attention, f16 K/V, and a server reasoning budget of 256. `on128` sends a Token cap of 128 per call. The log has no reasoning-token counts, so which limit applied isn't recorded. `nvidia/nemotron-3-nano-4b` was also loaded but not called. VRAM use and the LM Studio version weren't recorded.
- **CetiMind:** `main` at `c4cd140` for the code under test. The harness later landed in CetiMind as `bench/prompt_order/intent_bench.py`. [`harness/`](harness/) holds the copy that ran. Default seed `20261126`.

## Method

- **The call:** CetiMind's `IntentRouter.decide` on its own, with no turn after it. That's temperature 0 and strict JSON (`{"tools": [...]}`). Each check sees the 6 tools (`current_time`, `schedule_create`, `schedule_list`, `schedule_cancel`, `web_search`, `http_get`), the line, and the last assistant line of the heavy profile's history.
- **Variants:** the three run in shuffled order on each line, for 5 repeats.

  | Variant | Thinking | Instruction |
  | --- | --- | --- |
  | `off` | off | Today's `INTENT_INSTRUCTION` (arm D's intent check) |
  | `off_example` | off | Today's instruction, plus the cancel example below |
  | `on128` | on, Token cap 128 | Today's instruction (arm A's intent check under the live settings) |

  The example added to the instruction:

  > Example: "Never mind the laundry alarm, I already emptied it." needs schedule_list and schedule_cancel, because the user wants an existing reminder removed.

  No cancel line names its reminder (laundry). It has the same shape as "Forget the oven reminder, I already checked it." (a dismissal, then "I already ___ it"), and it was written after the heavy runs missed that line, so the held-out lines are the fair test. The example is in English, for both languages.
- **Time:** wall clock around one non-streaming `IntentRouter.decide` call, median and p90 per variant.
- **Lines:** 78 per repeat (1,170 checks in all). All are synthetic, and the Japanese lines are machine-translated.

  | Group | Lines | Right when |
  | --- | --- | --- |
  | Cancel lines from the prompt-order set (not held out) | 2 × 2 languages ("Cancel my water reminder.", "Forget the oven reminder, I already checked it.") | `schedule_cancel` is picked |
  | New cancel lines (held out) | 6 × 2 languages, written for this run ("Drop the water reminder, I just had a glass.", "Scrap my oven timer, the bread is out.", "Can you clear my reminders?"…) | `schedule_cancel` is picked |
  | Near misses | 4 × 2 languages that mention reminders but ask for nothing ("I already checked the oven, the bread looks great.", "I cancelled my gym membership today."…) | nothing is picked |
  | Other tool lines | 16 × 2 languages from the prompt-order set | an expected tool is picked (both on the two-tool lines) |
  | Chit-chat | 7 × 2 languages | nothing is picked |
  | Either way | 4 × 2 languages (the list lines, which the jobs list answers, and "What day is it today?") | nothing outside the expected set |

## Results

1,170 checks. None failed.

| Group | `off` | `off_example` | `on128` |
| --- | --- | --- | --- |
| Cancel lines from the prompt-order set (not held out) | 13/20 (65%) | **20/20 (100%)** | 10/20 (50%) |
| New cancel lines (held out) | 28/60 (47%) | **50/60 (83%)** | 17/60 (28%) |
| Near misses (need no tool) | 35/40 (88%) | **40/40** | **40/40** |
| Other tool lines | 155/160 (97%) | **160/160** | **160/160** |
| Chit-chat | 70/70 | 70/70 | 70/70 |
| Either way | 40/40 | 40/40 | 40/40 |
| Median time (p90) | 335 ms (878) | 356 ms (470) | 1,637 ms (1,833) |

By language, on the held-out cancel lines: `off` 13/30 in English and 15/30 in Japanese; `off_example` 25/30 in both; `on128` 2/30 in English and 15/30 in Japanese.

At temperature 0, the 5 repeats gave the same result on 231 of 234 line-and-variant pairs, so the comparisons count lines, not checks. Over the 24 cancel and near-miss lines (exact sign test):

- **`off_example` vs `off`:** better on 8 lines, worse on none. p = 0.008. On the 12 held-out cancel lines alone, better on 5, worse on none, p = 0.063.
- **`off_example` vs `on128`:** better on 9 lines, worse on none. p = 0.004.

Both stay under 0.05 after a Holm correction for the two tests (both 0.008).

All 10 of `off_example`'s misses were one line, in both languages: "No need to remind me about water today." It picked nothing every time. That line asks to skip a reminder without naming one to cancel, which is the vaguest of the six.

## Reading

- **One example fixed most cancel lines, including new ones.** On the 12 held-out cancel lines, the check was right on every repeat for 10 lines with the example, against 5 without it. Only one shares a word with the example ("alarm"), and it was right without the example too.
- **It added no false alarms.** The near misses went from 35/40 to 40/40. All 5 false alarms without the example were one line, "My reminders app at work is so annoying." The other tool lines went from 155/160 to 160/160, also one line (the Japanese time-and-stretch line). Chit-chat didn't change.
- **It added no measurable time.** The median was 356 ms against 335 ms, and the p90 was 470 ms against 878 ms.
- **Thinking didn't help.** The thinking-on check (arm A's) got the fewest cancel checks right (28% held out). On the held-out lines, the whole gap to thinking off was in English. By line, thinking off did better on 4 cancel lines in both languages and worse on none, which isn't significant (p = 0.125). Three are English held-out lines, and the fourth is the Japanese "Forget the oven reminder…" line (3/5 against 0/5). Thinking on made no false alarms on near misses, and its median time was 1,637 ms against 335 ms. Turning thinking off in arm D wasn't what cost the cancel lines.
- **For CetiMind:** a cancel example in `INTENT_INSTRUCTION` is the candidate fix for cancel lines. It doesn't address D's gap to A in the heavy runs, which came from two-tool lines and stray calls, not cancels. Run 3 of the heavy prompt-order run tests it in a full turn (see the follow-up's last bullet).

## Follow-up: examples on the tool spec

The follow-up moved the example out of `INTENT_INSTRUCTION` and onto the tool. `ToolSpec` gained an optional `intent_examples` field, and `IntentRouter` lists each example on its own indented line under its tool's line. The tool lines don't change from turn to turn, so the prompt cache still holds. `schedule_cancel` brings the one example. The bench was rewritten as a regression check that runs whenever the instruction or an example changes.

### Setup

- **Date:** 2026-11-26, the same evening and PC as the first run.
- **Model:** `qwen3.5-4b` on LM Studio, with `text-embedding-nomic-embed-text-v1.5` also loaded and not called. The load settings weren't recorded again.
- **CetiMind:** CetiMind with per-tool intent examples. Spec run 1 used the example line without the reason clause. Spec runs 2 and 3 added the reason clause, and spec run 3 also added the complaint sentence, which is the prompt the later runs used. The harness is in [`harness-spec/`](harness-spec/), and the history and test lines are the same as in [`harness/`](harness/).

### Method

- **The call:** the same as the first run. `IntentRouter.decide` alone, thinking off, temperature 0, strict JSON, 6 tools.
- **Variants:** two, in shuffled order on each line, for 5 repeats.

  | Variant | Instruction | Tool lines |
  | --- | --- | --- |
  | `live` | Today's `INTENT_INSTRUCTION` | With every `intent_examples` line |
  | `bare` | Today's `INTENT_INSTRUCTION` | With the examples stripped |

  Both use the same instruction, so in spec run 3 `bare` also has the new instruction sentence.
- **Lines:** the same 78 lines per repeat as the first run, in the same groups (780 checks per run). The held-out cancel lines and near misses now live in [`harness-spec/intent_lines.py`](harness-spec/intent_lines.py). The bench stops if an example is a copy of a bench line.
- **The bar for `live`:**
  - At least 80% of held-out cancel lines right.
  - No false alarms on the near misses.
  - No group among other tool lines, chit-chat, either way, and cancel lines from the prompt-order set below `bare`.
- **What changed between runs:**

  | Run | `schedule_cancel` example | Instruction |
  | --- | --- | --- |
  | Spec 1 | `Example: "Never mind the laundry alarm, I already emptied it." needs schedule_cancel.` | Unchanged from the first bench |
  | Spec 2 | Adds `, because the user wants an existing reminder removed` | Unchanged |
  | Spec 3 | As spec run 2 | Adds "A tool is needed only when the user asks for something the tool does, not when they just mention or complain about the topic." |

  Unlike the first run's example, these name only `schedule_cancel`, not `schedule_list` as well.

### Results

780 checks per run. None failed.

| Group | Spec 1 `live` | Spec 2 `live` | Spec 3 `live` | Spec 3 `bare` |
| --- | --- | --- | --- | --- |
| Cancel lines from the prompt-order set (not held out) | 20/20 | 20/20 | **20/20** | 10/20 (50%) |
| New cancel lines (held out) | 45/60 (75%) | 60/60 | **60/60** | 30/60 (50%) |
| Near misses (need no tool) | 30/40 (75%) | 30/40 (75%) | **40/40** | 40/40 |
| Other tool lines | 160/160 | 155/160 (97%) | 155/160 (97%) | 155/160 (97%) |
| Chit-chat | 70/70 | 70/70 | 70/70 | 70/70 |
| Either way | 40/40 | 40/40 | 40/40 | 40/40 |
| Median time (p90) | 337 ms (584) | 334 ms (879) | 327 ms (916) | 330 ms (936) |
| Meets the bar | No | No | **Yes** | – |

`bare` in spec runs 1 and 2 matched spec run 3's `bare`, except on the near misses: 35/40 in both.

Every miss repeated on all 5 repeats:

- **Spec run 1:**
  - "No need to remind me about water today", in both languages, picked nothing.
  - "Can you clear my reminders?", in English, picked only `schedule_list`.
  - "My reminders app at work is so annoying", in English, picked `schedule_cancel`.
  - The Japanese "I cancelled my gym membership today" picked `web_search`.
- **Spec run 2:** the cancels were all right, but "My reminders app at work is so annoying" picked `schedule_cancel` in both languages. The Japanese two-tool line picked only `schedule_create`.
- **Spec run 3:** only that two-tool line, the same as `bare` in every run.

### Reading the follow-up

- **With the reason clause, the held-out cancels went from 75% to all 60.** That includes the soft "No need to remind me…" that the first bench never got.
- **The example made the check trigger on complaints.** "My reminders app at work is so annoying" picked `schedule_cancel` in spec runs 1 and 2. That was one line, on every repeat, and both languages in spec run 2.
- **One instruction sentence fixed the complaints without losing cancels.** Spec run 3 kept all the cancels and had no false alarms. It also fixed `bare` on that line (35/40 to 40/40).
- **The two-tool line isn't an example problem.** The Japanese time-plus-reminder line missed `current_time` in `bare` in every run, and in `live` from spec run 2 on. In spec run 1 it got that line right, so the example can change it, but this bench doesn't test a fix.
- **No speed cost.** `live` and `bare` medians are within 6 ms of each other in every run.
- **End to end:** arm D, rerun with spec run 3's prompt on the heavy profile, got the cancel lines right on 10 of 12 turns, against 6 of 12 in heavy run 2. See [run 3 of the heavy prompt-order run](../prompt-order-heavy-2026-11-26/README.md#run-3-arm-d-after-the-intent-fix).

## Limits

- **Scope:** one model, one example, 6 tools, single-turn lines. The intent check alone, not a full turn.
- **Sample:** the held-out cancel lines are only 6 per language. In the first bench and spec run 1, "No need to remind me…" still slipped through.
- **Language:** Japanese improved about as much as English, but a Japanese example wasn't tested.
- **Unseen tools:** in the first run, the instruction names two tools. A future tool set without `schedule_cancel` would need the example adjusted. In the follow-up, the example lives on its tool, so it's left out when the tool is.
- **Follow-up runs:** the bar was tuned on the same line sets it's scored on. Spec run 3 is the third try, so its held-out cancels aren't fully held out anymore. The near misses are only 4 per language.
- **Repeats:** at temperature 0 the 5 repeats gave the same result on 231 of 234 line-and-variant pairs, so the run has 78 distinct lines, not 1,170 independent checks.

## Files

- **First run:**
  - [`harness/intent_bench.py`](harness/intent_bench.py), with [`harness/heavy.py`](harness/heavy.py) and [`harness/lines.py`](harness/lines.py) for the test lines and history.
  - `run/calls.jsonl`: one row per intent check (variant, line, group, pick, right or wrong, time).
  - `run/raw-output.txt`: the console log.
- **Follow-up:**
  - [`harness-spec/intent_bench.py`](harness-spec/intent_bench.py) and [`harness-spec/intent_lines.py`](harness-spec/intent_lines.py). They also need `harness/heavy.py` and `harness/lines.py`.
  - `run-spec1/`, `run-spec2/` and `run-spec3/`: `calls.jsonl`, `summary.json` (the groups and the bar checks) and `raw-output.txt` for each run.

To run the follow-up again, copy `harness/` and `harness-spec/` into `bench/prompt_order/` in a CetiMind checkout with per-tool intent examples. It exits 1 when `live` misses the bar.

```bash
uv run python bench/prompt_order/intent_bench.py --base-url http://HOST:PORT/v1 --out DIR --repeats 5
```

CetiMind's `intent_bench.py` is now the follow-up version, with `live` and `bare`. To repeat the first run (`off`, `off_example`, `on128`), use the copy in [`harness/intent_bench.py`](harness/intent_bench.py), when `INTENT_INSTRUCTION` and the tools are as they were, and run the same command.
