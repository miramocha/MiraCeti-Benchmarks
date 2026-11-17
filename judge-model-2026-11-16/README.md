# Judge model

## Question

CetiMind's judge model runs the learn step: it pulls facts and events out of a user line, then decides whether each one is added, merged, replaces an old fact, or is skipped. Which of the two loaded 4B models is the better judge? The saved setting used `nvidia/nemotron-3-nano-4b`, on the guess that it was the stronger structured-output model.

The same data is in CetiMind #79 as experiment 15.

## Setup

- **Date:** Nov 16 2026.
- **Machine, server and LM Studio load settings:** as in [tool-model-split-2026-11-16](../tool-model-split-2026-11-16/README.md). That is an RTX 4070 12 GB, LM Studio, context 6144, flash attention on, K/V cache `q8_0`.
- **Models:**
  - `qwen3.5-4b` (`Q4_K_S`).
  - `nvidia/nemotron-3-nano-4b` (`Q4_K_M`).
  - `text-embedding-nomic-embed-text-v1.5` for the store's embeddings.
- **CetiMind:** branch `feat/tool-model-77` at `569ff09` (merged as `75f69b3`).
- **Judge client:** `LlmClient` with `thinking="auto"` (judge calls don't think in auto), `max_tokens` 1024, through CetiMind's `JudgeAdapter`. Judge calls run at temperature 0.

## Method

`judge_bench.py` in this directory, run from a CetiMind checkout.

- **Learn step:** each case runs CetiMind's own `learn(store, judge, embedder, line, name="User", assistant="Ceti")` on a fresh temporary store, with the real embedder. The real data directory is never opened.
- **Repeats:** n = 3 per line and model, with the models alternating per repeat.
- **Extraction:** 12 hand-written lines.
  - A line that should store something is right when every expected keyword appears in a stored fact or event.
  - A line that should store nothing is right when nothing is stored.

  | Line | Expected |
  | --- | --- |
  | I love ramen, especially tonkotsu. | a fact with "ramen" |
  | My sister Aiko lives in Osaka. | a fact with "aiko" |
  | I work as a game developer at a small indie studio. | a fact with "game" |
  | I'm allergic to peanuts. | a fact with "peanut" |
  | My cat's name is Mochi and she's 3 years old. | a fact with "mochi" |
  | I don't like horror movies. | a fact with "horror" |
  | My favorite color is blue. | a fact with "blue" |
  | I just finished my first marathon yesterday! | a fact or event with "marathon" |
  | lol that's so funny | nothing |
  | What time is it? | nothing |
  | Can you remind me to drink water in 20 minutes? | nothing |
  | How are you feeling today? | nothing |

- **Updates:** 3 cases. Each seeds one fact, then learns a line.

  | Seeded fact | Line | Right when |
  | --- | --- | --- |
  | User's favorite color is blue. | Actually my favorite color is green now. | "green" is stored and "blue" is gone |
  | User lives in Tokyo. | I moved to Kyoto last month. | "kyoto" is stored and "tokyo" is gone |
  | User loves ramen. | I really love ramen. | exactly one ramen fact remains |

- **Timing:** wall clock around one `learn` call. That's the extract call, plus the placement calls and the embedding calls.

## Results

| Judge | Extraction right | Updates right | Median extract | Median update |
| --- | --- | --- | --- | --- |
| qwen3.5-4b | 36/36 | 6/9 | 1.0 s | 1.9 s |
| nvidia/nemotron-3-nano-4b | 30/36 | 0/9 | 1.0 s | 2.4 s |

| Case | qwen3.5-4b | nemotron |
| --- | --- | --- |
| extract: I love ramen, especially tonkotsu. | 3/3 | 3/3 |
| extract: My sister Aiko lives in Osaka. | 3/3 | 3/3 |
| extract: I work as a game developer at a small indie studio. | 3/3 | 0/3 |
| extract: I'm allergic to peanuts. | 3/3 | 3/3 |
| extract: My cat's name is Mochi and she's 3 years old. | 3/3 | 3/3 |
| extract: I don't like horror movies. | 3/3 | 0/3 |
| extract: My favorite color is blue. | 3/3 | 3/3 |
| extract: I just finished my first marathon yesterday! | 3/3 | 3/3 |
| extract: lol that's so funny (nothing) | 3/3 | 3/3 |
| extract: What time is it? (nothing) | 3/3 | 3/3 |
| extract: Can you remind me to drink water in 20 minutes? (nothing) | 3/3 | 3/3 |
| extract: How are you feeling today? (nothing) | 3/3 | 3/3 |
| update: favorite color blue → green | 3/3 | 0/3 |
| update: lives in Tokyo → moved to Kyoto | 0/3 | 0/3 |
| update: loves ramen + "I really love ramen" | 3/3 | 0/3 |

What each judge stored on the failed update cases (repeat 0):

| Case | qwen3.5-4b | nemotron |
| --- | --- | --- |
| blue → green | `User's favorite color is green.` (right) | `User's favorite color is blue.` (no change) |
| Tokyo → Kyoto | `User moved to Kyoto.`, `User lives in Tokyo.` | `User moved to Kyoto last month.`, `User lives in Tokyo.`, `User moved to Kyoto.` |
| ramen | `User loves ramen.` (right) | `User likes ramen.`, `User loves ramen.` |

## What it means

- **qwen3.5-4b is the better judge, at the same speed.**
- **nemotron skipped two kinds of facts every time:** a job and a dislike.
- **nemotron never changed a stored fact.** It kept the old color, added a near-duplicate for ramen, and stored Kyoto twice.
- **qwen's only miss was the move:** it stored the new city but kept the old one.
- **nemotron is still a good tool model.** It picked the right tool reliably in [tool-model-split-2026-11-16](../tool-model-split-2026-11-16/README.md). Choosing a tool and judging memory are different skills.
- **A catch in CetiMind at this commit:** setting the judge to the chat model turns reflection off, because reflection runs only with a separate judge model.

## Limits

- **The learn step only.** Summaries, the user profile and reflection were not tested.
- **Small and hand-written:** 15 cases, 3 repeats, English only, scored by keywords.
- **No thinking:** judge calls ran without thinking (`auto`), and `on` was not tried.

## Files

- `judge_bench.py`: the runner. Run it from a CetiMind checkout: `python judge_bench.py <settings.toml> 3`. It reads only the base URL and capability records from that file, and points `CETIMIND_DATA_DIR` at a temporary folder.
- `judge.jsonl`: one row per learn call, with the model, kind, repeat, case, line, score, time and what was stored.
