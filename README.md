# MiraCeti benchmarks

Performance and accuracy experiments for the MiraCeti apps. One directory per experiment, each with its own `README.md` for the question, the method, and the results. A benchmark that is run more than once keeps each run as a directory inside its own directory. The code that produces a run stays in the app repo.

## Benchmarks

| Benchmark | App | What it measures |
| --- | --- | --- |
| [Reminder accuracy](reminder-accuracy/README.md) | CetiMind | Whether a reply matches the real schedule, and whether a reminder request is stored as memory. Includes the ad-hoc before/after check from the fix. |

## Experiments, by date

| Date | Experiment | App | Measures | What it checks |
| --- | --- | --- | --- | --- |
| 2026-11-15 | [Kev reasoning check](kev-reasoning-check-2026-11-15/README.md) | CetiMind | Accuracy | Whether Kev 0.8B can tell lines that need reasoning from small talk. The margin is thin. |
| 2026-11-15 | [Schedule tool calls](schedule-tool-calls-2026-11-15/README.md) | CetiMind | Accuracy | How often a reminder request gets a `schedule_create` call with thinking off, on, and with a prompt rule (0/18, 15/18, 0/18). |
| 2026-11-15 | [Thinking-off steps](thinking-off-steps-2026-11-15/README.md) | CetiMind | Accuracy | Whether a thinking-off intent check plus JSON argument extraction can replace thinking (intent 12/12, extraction 3/6). |
| 2026-11-15 | [Tool call examples](tool-call-examples-2026-11-15/README.md) | CetiMind | Accuracy, speed | Whether example tool calls or "think briefly" fix tool calls (examples 0/18; brief thinking made reasoning 10–25× longer). |
| 2026-11-15 | [Tool turn router](tool-turn-router-2026-11-15/README.md) | CetiMind | Accuracy, speed | Which router finds tool turns in English and Japanese: rules, Kev, embeddings, or a JSON check. The JSON check wins. |
| 2026-11-15 | [Generic tool picker](generic-tool-picker-2026-11-15/README.md) | CetiMind | Accuracy | A tool-name picker over 8 tools (1/30 misses), and thinking off vs on with stub tools (2/12 vs 12/12). |
| 2026-11-15 | [Hidden tool calls](hidden-tool-calls-2026-11-15/README.md) | CetiMind | Accuracy | Whether thinking-on misses are tool calls hidden in the reasoning. No: 27/30 called, and the 3 misses had no markup. |
| 2026-11-15 | [Missed tool check](missed-tool-check-2026-11-15/README.md) | CetiMind | Accuracy | Which check catches a reply that skipped a tool: regex, reply-only JSON, or request-plus-reply JSON (the pair caught 19/21 EN, 22/23 JA). |
| 2026-11-15 | [Prompt cache layout](prompt-cache-layout-2026-11-15/README.md) | CetiMind | Speed | How prompt layout and a changing tool set affect the prompt cache. A stable start halves time to first token. |
| 2026-11-15 | [Forced tool choice](forced-tool-choice-2026-11-15/README.md) | CetiMind | Accuracy, speed | Whether forcing the chosen tool with thinking off makes tool turns faster (named: HTTP 400; required: 3/12 with about 65 s stalls). |
| 2026-11-15 | [Max tokens and tool calls](max-tokens-tool-calls-2026-11-15/README.md) | CetiMind | Accuracy | On a real-history turn, chat `max_tokens` 4096 vs 1024 and `schedule_create` calls (1/6 vs 7/7). Run on real data; counts only. |
| 2026-11-16 | [Memory classifier: Kev vs JSON checks](memory-classifier-kev-2026-11-16/README.md) | CetiMind | Accuracy, speed | Kev against JSON checks on the qwen and nemotron 4B models for the learn gate and fact dedupe (EN and JA), plus the slowdown on the next reply's first token. |
| 2026-11-16 | [Tool model split](tool-model-split-2026-11-16/README.md) | CetiMind | Accuracy, speed | One model vs a separate tool model (`qwen3.5-4b` chat, `nemotron-3-nano-4b` tools), and tool calls with thinking off: needed tools called, stray calls, and turn time over 23 lines. |
| 2026-11-16 | [Judge model](judge-model-2026-11-16/README.md) | CetiMind | Accuracy | `qwen3.5-4b` vs `nemotron-3-nano-4b` as the learn-step judge: fact extraction and fact updates on hand-written lines. |
| 2026-11-17 | [Turn latency](turn-latency-2026-11-17/README.md) | CetiMind | Speed | Where reply time goes, from the app log: thinking turns, the intent check, and tool-call retries. |
| 2026-11-26 | [Tiered prompts vs. one prompt](prompt-order-vs-full-2026-11-26/README.md) | CetiMind | Accuracy, speed | CetiMind's tiered tool turn against one full persona prompt, plus a 512-token Tools cap and a fast-hold hybrid. One prompt matched it on tools (91% vs 89%) and answered at 2.8 s vs 6.6 s. The hybrid spoke a hold at 0.95 s. |
| 2026-11-26 | [Prompt order under heavy context](prompt-order-heavy-2026-11-26/README.md) | CetiMind | Accuracy, speed | The same three arms with context sized like real use and planted traps. The tiered order led on tools (91% vs 86%, p = 0.049 uncorrected) with 1 false claim against 7. The gap was in English. A follow-up arm D, with isolated tool rounds, a thinking-off intent check and thinking-off replies, came close to A on tools (89% vs 92%, p = 0.15), spoke first at 0.84 s, and answered 2.9 s sooner (4.3 s against 7.2 s). Run 3, after the intent-check follow-up: D at 93% against A at 95% (p = 0.58, not significant), with no false claims from either. |
| 2026-11-26 | [Intent check: one cancel example](intent-cancel-example-2026-11-26/README.md) | CetiMind | Accuracy, speed | One cancel example in the thinking-off intent check: held-out cancel lines 47% to 83% (5 to 10 of 12 lines right every time), near-miss false alarms 5 to 0 (one line), with no measurable time cost. Thinking on didn't help (28% held out, with that gap in English) and took about 5 times as long. A follow-up moved the example onto the tool: with a reason clause and one instruction sentence, the third spec run got every held-out cancel and no false alarms, on lines tuned over three tries. |
| 2026-11-27 | [Arm D's three changes, one at a time](prompt-order-d-parts-2026-11-27/README.md) | CetiMind | Accuracy, speed | D's thinking-off intent check, thinking-off replies and results-first say-this prompt, each alone on the heavy profile. No arm differed significantly from A on tools (92–96%). The intent change gave the 0.66 s first word and the reply change the faster answer. Results first added no speed and had the most partial claims (6 of 12 against A's 1) and hold repeats. |
| 2026-11-27 | [Long tool results](long-tool-results-2026-11-27/README.md) | CetiMind | Accuracy, speed | Answers planted early, in the middle or late in long fetched pages and search results. With the say-this prompt cut at 1,000 characters, CetiMind named 0 of 60 middle or late answers and named the distractor instead on 23 of 90 turns. Passing the whole result named 89 of 90, for about 240 ms more on the median answer. A summary step first named 77 of 90. |

## Setup notes

How the local model server behaves. These do not measure the apps; they explain settings the experiments above depend on.

| Date | Note | What it found |
| --- | --- | --- |
| 2026-11-15 | [Thinking switch](setup-notes/thinking-switch-2026-11-15/README.md) | Which request field turns Qwen3.5-9B thinking on in LM Studio. Only `reasoning_effort`; the level barely matters. |
| 2026-11-15 | [Thinking cap fields](setup-notes/thinking-cap-fields-2026-11-15/README.md) | Whether any request field caps thinking length in LM Studio. None of six did. |
| 2026-11-15 | [Endpoint capabilities](setup-notes/endpoint-capabilities-2026-11-15/README.md) | Whether CetiMind's startup probe finds the thinking switch, tool support, and named `tool_choice` behavior on LM Studio with `qwen/qwen3.5-9b`. |
| 2026-11-16 | [GPU memory and model switching](setup-notes/gpu-memory-model-switch-2026-11-16/README.md) | Why alternating two models on a 12 GB GPU cost about 1 s per switch (memory spill), and what K/V `q8_0` plus context 6144 freed. |

## Adding an experiment

- Name the directory `<topic>-<yyyy-mm-dd>`. A repeatable benchmark has no date; its runs inside it do. A note on server or model settings goes in `setup-notes/`.
- Put the question, setup (models, load settings, code version), method, and results in its `README.md`. Add data files beside it.
- Add a chart where a comparison is easier to see than to read: add it to `tools/make_charts.py` and embed it next to the results table. [tools/README.md](tools/README.md) has the steps.
- This repo is public. Do not add real user chat text, memory, or app settings. For a run on real data, publish the method and counts only.
- Add one row to the matching table above.
