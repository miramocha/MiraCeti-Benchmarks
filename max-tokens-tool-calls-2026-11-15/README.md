# Tool calls and `max_tokens` on a real-history turn

A one-off check, run while CetiMind's chat was not calling the scheduler. A reminder request got a "the reminder is set" reply with no `schedule_create` call. Lowering the chat `max_tokens` from 4096 to 1024 made the calls come back.

The runs used a copy of real CetiMind memory, so only the method and the counts are published here. No user line, reply text or memory is.

## Question

On a real turn, with conversation history and memories in the prompt, does the chat's `max_tokens` setting change whether Qwen3.5-9B calls `schedule_create`?

## Setup

- **Date:** 2026-11-15, late evening local time.
- **Machine and server:** the same PC and LM Studio setup as the [thinking and tool-call series](../setup-notes/thinking-switch-2026-11-15/README.md): one RTX 4070 (12 GB), LM Studio with `qwen/qwen3.5-9b` (GGUF `Q4_K_M`, 8192 context loaded), and `nomic-embed-text-v1.5` for embeddings. Load settings beyond the context length were not recorded for this run.
- **CetiMind:** branch `feat/59-safety-net` at `7c96523` (the CetiMind #59 background safety net, on top of the CetiMind #58 known-miss retry). Thinking is `auto`: a turn thinks when the intent router picks a tool, and `reasoning_effort` `"low"` switches it on.
- **Turn path:** CetiMind's own `reply_turn` with the `IntentRouter`, the four schedule tools (`current_time`, `schedule_create`, `schedule_list`, `schedule_cancel`), memory recall, and the #58 retry. The background check from CetiMind #59 then ran on turns the router sent to "no tool".
- **Client:** `LlmClient` built in the script, with `max_tokens` set from an environment variable. Everything else in the turn is the app's code.

## Method

- **Store:** each run copied the real `memory.db` into a fresh temporary directory with SQLite's backup API. The copy then dropped the messages from the exchange being reproduced, so the request was not already in the history. Each run also got its own empty `jobs.db`. The real data directory was never written.
- **Line:** one English reminder request of the form "remind me in N minutes to do X", taken from the failing exchange. The same line every run.
- **Variants:**
  - `max_tokens` 1024, real history
  - `max_tokens` 4096, real history
  - `max_tokens` 4096, empty store (no history or memories)
- **Scored:** whether the turn ended with a `schedule_create` call and a job in `jobs.db`, counting a call made by the #58 retry as a success. Also logged: what the router picked, whether the turn thought, and whether the retry ran.
- **Runs:** two batches per real-history variant on the same evening, 3 or 4 runs each.

## Results

| Variant | Runs | `schedule_create` called | Needed the #58 retry | Retry made the call |
| --- | --- | --- | --- | --- |
| `max_tokens` 1024, real history | 7 | **7/7** | 1 | 1/1 |
| `max_tokens` 4096, real history | 6 | **1/6** | 5 | 0/5 |
| `max_tokens` 4096, empty store | 1 | 1/1 | 0 | n/a |

- **The router was right every time.** On real history it picked `schedule_create` in all 13 runs, and every turn thought. On the empty store it picked all four schedule tools.
- **At 4096, every miss was the same false claim:** the reply says the reminder is set, and no tool was called. The #58 retry ran on all 5 misses and called nothing.
- **The replies copy the history.** On real history the replies repeated an earlier false "it's set" reply from the conversation nearly word for word, at both settings. At 1024 the call was made anyway.
- The script exited with an error after the empty-store run. The cause was not checked, so that variant has one run.

## What it means

- `max_tokens` 4096 on this LM Studio setup stopped the model from making tool calls on real-history turns, and the thinking retry did not help. The cause inside LM Studio or the chat template is unknown.
- The app setting was lowered to 1024 after this run. Later live use at 1024 created jobs, but still had some false claims on other reminder lines, so 1024 is not a full fix.
- A false claim already in the history makes the next one more likely. Removing those exchanges from memory is part of the fix.

## Limits

- **Small:** 14 runs, one line, one model, one conversation history.
- **Not isolated:** `max_tokens` was the only setting changed between variants, but the cause was not traced. Other values (such as 2048) were not tried.
- **Real data:** the history cannot be published, so this run cannot be repeated from this directory. The empty-store variant can be repeated with any reminder line.
