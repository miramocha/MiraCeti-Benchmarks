# MiraCeti benchmarks

Benchmarks and experiments for the MiraCeti apps. One directory per experiment, each with its own `README.md` for the question, the method, and the results. A benchmark that is run more than once keeps each run as a directory inside its own directory. The code that produces a run stays in the app repo.

## Experiments

### Benchmarks

| Benchmark | App | What it measures |
| --- | --- | --- |
| [Reminder accuracy](reminder-accuracy/README.md) | CetiMind | Whether a reply matches the real schedule, and whether a reminder request is stored as memory. Includes the ad-hoc before/after check from the fix. |

### One-off experiments, by date

| Date | Experiment | App | What it checks |
| --- | --- | --- | --- |
| 2026-11-15 | [Thinking switch](thinking-switch-2026-11-15/README.md) | CetiMind | Which request field turns Qwen3.5-9B thinking on in LM Studio. Only `reasoning_effort`; the level barely matters. |
| 2026-11-15 | [Kev reasoning check](kev-reasoning-check-2026-11-15/README.md) | CetiMind | Whether Kev 0.8B can tell lines that need reasoning from small talk. The margin is thin. |
| 2026-11-15 | [Schedule tool calls](schedule-tool-calls-2026-11-15/README.md) | CetiMind | How often a reminder request gets a `schedule_create` call with thinking off, on, and with a prompt rule (0/18, 15/18, 0/18). |
| 2026-11-15 | [Thinking-off steps](thinking-off-steps-2026-11-15/README.md) | CetiMind | Whether a thinking-off intent check plus JSON argument extraction can replace thinking (intent 12/12, extraction 3/6). |
| 2026-11-15 | [Thinking cap fields](thinking-cap-fields-2026-11-15/README.md) | CetiMind | Whether any request field caps thinking length in LM Studio. None of six did. |
| 2026-11-15 | [Tool call examples](tool-call-examples-2026-11-15/README.md) | CetiMind | Whether example tool calls or "think briefly" fix tool calls (examples 0/18; brief thinking made reasoning 10–25× longer). |
| 2026-11-15 | [Tool turn router](tool-turn-router-2026-11-15/README.md) | CetiMind | Which router finds tool turns in English and Japanese: rules, Kev, embeddings, or a JSON check. The JSON check wins. |
| 2026-11-15 | [Generic tool picker](generic-tool-picker-2026-11-15/README.md) | CetiMind | A tool-name picker over 8 tools (1/30 misses), and thinking off vs on with stub tools (2/12 vs 12/12). |
| 2026-11-15 | [Hidden tool calls](hidden-tool-calls-2026-11-15/README.md) | CetiMind | Whether thinking-on misses are tool calls hidden in the reasoning. No: 27/30 called, and the 3 misses had no markup. |
| 2026-11-15 | [Missed tool check](missed-tool-check-2026-11-15/README.md) | CetiMind | Which check catches a reply that skipped a tool: regex, reply-only JSON, or request-plus-reply JSON (the pair caught 19/21 EN, 22/23 JA). |
| 2026-11-15 | [Prompt cache layout](prompt-cache-layout-2026-11-15/README.md) | CetiMind | How prompt layout and a changing tool set affect LM Studio's prompt cache. A stable start halves time to first token. |
| 2026-11-15 | [Forced tool choice](forced-tool-choice-2026-11-15/README.md) | CetiMind | Whether `tool_choice` can force the chosen tool with thinking off (named: HTTP 400; required: 3/12 with about 65 s stalls). |
| 2026-11-15 | [Max tokens and tool calls](max-tokens-tool-calls-2026-11-15/README.md) | CetiMind | On a real-history turn, chat `max_tokens` 4096 vs 1024 and `schedule_create` calls (1/6 vs 7/7). Run on real data; counts only. |
| 2026-11-15 | [Endpoint capabilities](endpoint-capabilities-2026-11-15/README.md) | CetiMind | Which thinking switch, tool support, and named `tool_choice` behaviour a short probe finds on LM Studio with `qwen/qwen3.5-9b`. |
| 2026-11-16 | [Memory classifier: Kev vs JSON checks](memory-classifier-kev-2026-11-16/README.md) | CetiMind | Kev against JSON checks on the qwen and nemotron 4B models for the learn gate and fact dedupe (EN and JA), plus the slowdown on the next reply's first token. |
| 2026-11-16 | [Tool model split](tool-model-split-2026-11-16/README.md) | CetiMind | One model vs a separate tool model (`qwen3.5-4b` chat, `nemotron-3-nano-4b` tools), and tool calls with thinking off: needed tools called, stray calls, and turn time over 23 lines. |
| 2026-11-16 | [Judge model](judge-model-2026-11-16/README.md) | CetiMind | `qwen3.5-4b` vs `nemotron-3-nano-4b` as the learn-step judge: fact extraction and fact updates on hand-written lines. |
| 2026-11-16 | [GPU memory and model switching](gpu-memory-model-switch-2026-11-16/README.md) | CetiMind | Why alternating two models on a 12 GB GPU cost about 1 s per switch (memory spill), and what K/V `q8_0` plus context 6144 freed. |
| 2026-11-17 | [Turn latency](turn-latency-2026-11-17/README.md) | CetiMind | Where reply time goes, from the app log: thinking turns, the router, and tool-call retries. |

## Adding an experiment

- Name the directory `<topic>-<yyyy-mm-dd>`. A repeatable benchmark has no date; its runs inside it do.
- Put the question, setup (models, load settings, code version), method, and results in its `README.md`. Add data files beside it.
- This repo is public. Do not add real user chat text, memory, or app settings. For a run on real data, publish the method and counts only.
- Add one row to the table above.
