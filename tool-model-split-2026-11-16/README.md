# Tool model split

## Question

CetiMind can run its tool calls on a separate model from the one that writes replies (CetiMind #77, #78). The tool model runs the intent check, the tool-call rounds and the miss check, and the chat model writes the reply from the tool results with no tools offered. This experiment asks two things:

1. Does a separate tool model call the needed tool more often than one model doing everything, and what does it cost in time?
2. Can the model that makes the tool calls skip thinking, if the intent check still runs and picks the tool?

The same data is in CetiMind #79 as experiments 13 and 14.

## Setup

- **Date:** Nov 16 2026.
- **Machine:** one Windows 11 PC with an NVIDIA GeForce RTX 4070 (12 GB). Discord, Steam and Edge were also running.
- **Server:** LM Studio on the same machine, one `llama-server` process per loaded model.
- **Models:**
  - `qwen3.5-4b`, GGUF `Q4_K_S`.
  - `nvidia/nemotron-3-nano-4b`, GGUF `Q4_K_M`.
  - `text-embedding-nomic-embed-text-v1.5`, `Q4_K_M`.
- **LM Studio load settings,** for both chat models:
  - Context 6144, flash attention on, K and V cache quantization `q8_0`, `parallel` 4.
  - Each model's capability probe: thinking switch `reasoning_effort`, tools yes, named `tool_choice` not enforced.
- **CetiMind:** branch `feat/tool-model-77`, `551a62c` to `569ff09` (merged as `75f69b3`). Question 2's rows need `569ff09`, where the intent check runs in every thinking mode.
- **Turn settings:**
  - Chat temperature 0.7. A separate tool model's rounds run at 0.
  - `max_tokens` 1024 per call.
  - A test persona: "Ceti", tone "Warm, playful", one boundary "Be brief.", prompt "You are Ceti, a cheerful companion."

## Method

`bench.py` in this directory, run from a CetiMind checkout.

- **Turn:** each line runs CetiMind's own `reply_turn`, then `finish_turn`, then `run_net` when the turn hands back a safety-net candidate.
  - The intent check (`IntentRouter`) and the miss check (`JsonMissCheck`) run on the tool client.
  - Each line gets a fresh temporary store, with the real embedder and no memories, so the memory search's embedding call overlaps the intent check as in the app.
  - The learn step's judge is a stub. The real data directory is never opened.
- **Tools:** six fakes that record their name and return a canned result:

  | Tool | Canned result |
  | --- | --- |
  | `current_time` | `2026-11-16 14:05 (Monday), local time.` |
  | `schedule_create` | `Scheduled job 7.` |
  | `schedule_list` | `Jobs: 7 'Drink water' in 18 minutes. 8 'Check the oven' in 1 hour 40 minutes.` |
  | `schedule_cancel` | `Cancelled job 7.` |
  | `web_search` | `1. Godot 4.6 released (godotengine.org) 2. F1: Verstappen won the Las Vegas GP.` |
  | `http_get` | `Example Domain. This domain is for use in illustrative examples in documents.` |

- **Lines:** 23 English lines, all hand-written test lines (no real chat).
  - 14 need a tool.
  - 8 need none.
  - "What day is it today?" is right with or without `current_time`, because the prompt carries the date.
- **Scoring:**
  - A tool line is right when an expected tool ran and nothing outside the expected set (plus `current_time`) ran.
  - A no-tool line is right when no tool ran.
  - "Needed tool called" counts tool lines where any tool ran.
- **Timing:** wall clock around one `reply_turn`. It includes the intent check, the embedding call, the prompt build, the tool rounds and the reply, but not learning or the safety net.
- **Order:** the setups take turns within each repeat. Each setup starts with one warm-up call per model. The tables use repeats 0 and 1 of each setup (46 turns).

| Setup | Chat model | Tool model | Chat thinking | Tool thinking |
| --- | --- | --- | --- | --- |
| split | qwen3.5-4b | nemotron-3-nano-4b | auto | auto |
| qwen | qwen3.5-4b | (same) | auto | — |
| nemotron | nemotron-3-nano-4b | (same) | auto | — |
| qwen_off | qwen3.5-4b | (same) | off | — |
| split_tooloff | qwen3.5-4b | nemotron-3-nano-4b | auto | off |

The `qwen` and `nemotron` rows come from `session-1.jsonl`. The `split`, `qwen_off` and `split_tooloff` rows come from `session-2.jsonl`. A split run in session 1 gave the same picture: a 3.1 s median, 3.7 s on tool turns, 0.9 s on plain chat, and every needed tool called. Session 1 stopped at its third repeat, when LM Studio returned HTTP 500 on a warm-up call.

## Results

| Setup | Turns | Scored right | Needed tool called | Stray tool calls | Errors | Median turn | Tool turns | Plain chat | p90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| split | 46 | 43/46 | 29/30 | 0 | 0 | 3.2 s | 3.8 s | 0.9 s | 5.6 s |
| qwen | 46 | 41/46 | 28/30 | 1 | 0 | 3.8 s | 4.7 s | 0.9 s | 6.3 s |
| nemotron | 46 | 41/46 | 27/30 | 1 | 1 | 3.3 s | 4.3 s | 0.9 s | 6.9 s |
| qwen_off | 46 | 25/46 | 11/30 | 0 | 0 | 1.4 s | 1.6 s | 1.0 s | 2.0 s |
| split_tooloff | 46 | 21/46 | 5/30 | 0 | 0 | 1.4 s | 1.8 s | 0.9 s | 2.6 s |

With all 3 repeats of session 2 (69 turns per setup), the tool lines with a tool called were: split 43/45, qwen_off 18/45, split_tooloff 7/45.

### Per line (right out of 2)

| Line | Expected | split | qwen | nemotron | qwen_off | split_tooloff |
| --- | --- | --- | --- | --- | --- | --- |
| What time is it right now? | `current_time` | 2/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| Remind me to drink water in 20 minutes. | `schedule_create` | 2/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| What reminders do I have? | `schedule_list` | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| Cancel my water reminder. | `schedule_cancel, schedule_list` | 1/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| Every morning at 8, remind me to stretch. | `schedule_create` | 2/2 | 2/2 | 1/2 | 0/2 | 0/2 |
| In 2 hours tell me to check the oven. | `schedule_create` | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 |
| Search the web for the latest Godot engine release. | `web_search` | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| Who won the most recent Formula 1 race? | `web_search` | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| What does https://example.com say? | `http_get` | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Tell me about your day! | none | 2/2 | 1/2 | 2/2 | 2/2 | 2/2 |
| I love ramen, especially tonkotsu. | none | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| How are you feeling today? | none | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Wake me up at 7 tomorrow. | `schedule_create` | 2/2 | 1/2 | 2/2 | 0/2 | 0/2 |
| Set a timer for 5 minutes. | `schedule_create` | 2/2 | 1/2 | 2/2 | 0/2 | 0/2 |
| Are my reminders still on? | `schedule_list` | 2/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| Forget the oven reminder, I already checked it. | `schedule_cancel, schedule_list` | 1/2 | 1/2 | 0/2 | 0/2 | 0/2 |
| What day is it today? | `current_time` or none | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| What's the weather in Tokyo right now? | `web_search` | 1/2 | 2/2 | 1/2 | 1/2 | 0/2 |
| Read https://godotengine.org for me. | `http_get` | 2/2 | 1/2 | 2/2 | 0/2 | 1/2 |
| lol that's so funny | none | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| I'm going to drink some water now. | none | 2/2 | 2/2 | 1/2 | 2/2 | 2/2 |
| My favorite color is blue. | none | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Do you remember what we talked about yesterday? | none | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |

## What it means

- **The split missed the fewest tool calls,** and keeps the chat model's voice: qwen's replies are warm, and nemotron alone is terse ("Godot 4.6 was recently released.").
- **The split's one real miss** was a cancel that listed the jobs and then searched the web.
- **The split costs about 1 s more on tool turns** than qwen alone, and nothing on plain chat. That holds only with GPU memory headroom; see [gpu-memory-model-switch-2026-11-16](../gpu-memory-model-switch-2026-11-16/README.md).
- **qwen alone claims tool calls it never made.** On "Set a timer for 5 minutes" it replied that the timer was set, with no `schedule_create` call. It also answered "Wake me up at 7 tomorrow." with a web search.
- **nemotron alone** once returned an empty reply (`EmptyReplyError`) on a turn with no tool call. At the time, nothing retried that case on one model.
- **Tool calls need thinking.** With thinking off, the intent check still named the right tool every time, but the model replied in text instead of calling it.
  - The retry also ran without thinking, and failed the same way.
  - LM Studio does not enforce a named `tool_choice` here, so the pick cannot be forced.
  - The safety net checks only turns the intent check sent to "no tool", so it does not catch these.
  - Thinking off is about twice as fast, at the cost of most tool calls.
  - nemotron needs thinking even more than qwen.
- **Tool-call messages worked across models.** qwen accepted nemotron's assistant `tool_calls` and the `tool` results, with no `tools` field in the request, on every split tool turn.
- **Strict scoring:** most weather "misses" are extra lookups (`http_get`, more searches) after a correct `web_search`.
- **A miss nothing caught:** "Forget the oven reminder, I already checked it." was usually sent to "no tool" by every intent check.
- **The miss check's false alarms:** it flagged about 40% of plain chat lines in every setup. Its retry never made a call on those lines, so they cost only background time (1–4 s each).

## Limits

- **Small samples:** n = 2 per line in the tables.
- **One machine, one server, one test persona, English only.**
- **Fake tools and an empty memory store:** nothing was scheduled, and turns had no history.
- **Tool arguments were not scored.**
- **Other GPU apps were not controlled for,** and timings swing between sessions.

## Files

- `bench.py`: the runner. Run it from a CetiMind checkout at `569ff09` or later: `python bench.py <settings.toml> qwen,nemotron,split,qwen_off,split_tooloff 3`. It reads only the base URL and capability records from that file, and points `CETIMIND_DATA_DIR` at a temporary folder.
- `session-1.jsonl`, `session-2.jsonl`: one row per turn, with the setup, repeat, line, expected tools, routed tools, tools run, timing, a reply excerpt and the score. Endpoint URLs in error strings are replaced with `<endpoint>`.
