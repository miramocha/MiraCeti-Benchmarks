# Memories per turn by language

## Question

In the [heavy prompt-order run](../prompt-order-heavy-2026-11-26/README.md), the one-prompt order (B) lost accuracy against the tiered order (A) in English only, and English turns carried 3.24 memories against Japanese's 1.07. One guess was that the prompt budget, counted in characters, lets English carry more memories and bury the right fact deeper.

Why do the two languages get different memory counts? If both get the same count, does the English gap between A and B close?

## Setup

- **Date:** 2026-11-27.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC.
- **Model:** `qwen3.5-4b` for every call, loaded at a 6,144-token context. Embeddings from `nomic-embed-text-v1.5`.
- **Settings:** the 2026-11-26 settings pinned in the harness, matching the original heavy A and B arms: chat thinking on, and Replies set to follow, so the intent check and say-this reply think. These are not the later live settings, where the intent check and replies don't think.
- **CetiMind:** the version with the fix below. A copy of the harness is in [`harness/`](harness/).
- **Profile:** `heavy`: the "Wren" persona, 177 facts with 12 traps, a 16-message history, a summary and 2 open jobs.
- **Run:** `bench.py --profile heavy --arms A,B,A1,B1 --repeats 3`, default seed `20261126`. 58 lines × 4 arms × 3 repeats = 696 turns, 1 error, about 60 minutes.

## Step 1: memory counts

[`harness/memory_count.py`](harness/memory_count.py) builds each heavy line's prompt with CetiMind's own `_load`, with no chat model. It logs how many memories the lookup returned and how many reached the prompt. It also records the real token count of the memory lines, and reruns the search with no relevance floor.

| | Lines | Memories in the prompt | Real tokens | Prompt estimate |
| --- | --- | --- | --- | --- |
| Before the fix | English | 3.24 | 80 | 1,531 |
| Before the fix | Japanese | 1.07 | 27 | 1,879 |
| After the fix | English | 3.24 | 80 | 1,531 |
| After the fix | Japanese | 4.00 | 125 | 2,054 |

Means over the 29 lines per language. Rows are in [`counts/`](counts/).

- **The prompt budget never cut a memory.** In every line, every memory the lookup kept reached the prompt. The estimate stays under the 3,000-token budget in both languages.
- **Japanese lost its memories to the already-shown filter.** Every Japanese line had 20 candidates over the relevance floor, but one usually survived. `_already_shown` drops a memory when 85% of its words are already in one sentence of the profile, summary or recent chat. It counted only Latin words (`[0-9a-z']+`), so `Alexは毎朝8時にストレッチをしている。` became `{alex, 8}`. Any summary sentence with "Alex" then hid it. That dropped 165 of the 170 Japanese facts. The survivors had another Latin word or number the summary didn't share, such as `f1` or `godot` plus `4`.
- **The fix:** kana, CJK and hangul runs count as pairs of neighboring characters, and `。！？` end a sentence. Japanese then reaches the live limit of 4 memories per turn.

## Step 2: method

Arms interleaved in shuffled order on each line. Lines and scoring as in the heavy run. All four arms run with the fix.

| Arm | Order | Memories kept (`SCORING.keep`) |
| --- | --- | --- |
| A | Tiered: intent check, hold line, tool rounds, say-this reply, miss check | 4 (live) |
| B | One prompt with every tool | 4 (live) |
| A1 | Tiered | 1 |
| B1 | One prompt | 1 |

With one memory kept, both languages carry the same count: 1.0 per scored turn.

## Results

Full tables, with Wilson 95% intervals: [`summary.md`](summary.md).

| Right tools in the turn | A | B | A1 | B1 |
| --- | --- | --- | --- | --- |
| English | 82/87 (94%) | 77/87 (89%) | 83/87 (95%) | 75/87 (86%) |
| Japanese | 80/87 (92%) | 75/87 (86%) | 80/87 (92%) | 74/86 (86%) |
| Both | 162/174 (93%) | 152/174 (87%) | 163/174 (94%) | 149/173 (86%) |

Paired on the same line and repeat (exact McNemar; first number = only the first arm right):

| Pair | English | Japanese | Both |
| --- | --- | --- | --- |
| A vs B, 4 memories | 8 / 3, p 0.23 | 9 / 4, p 0.27 | 17 / 7, p 0.064 |
| A1 vs B1, 1 memory | 9 / 1, p 0.021 | 9 / 4, p 0.27 | 18 / 5, p 0.011 |
| A vs A1 | 1 / 2, p 1 | 2 / 2, p 1 | 3 / 4, p 1 |
| B vs B1 | 9 / 7, p 0.80 | 7 / 7, p 1 | 16 / 14, p 0.86 |

The A − B gap in right tools, in points:

| Lines | 11-26 run (EN 3.24, JA 1.07 memories) | This run, 4 memories | This run, 1 memory |
| --- | --- | --- | --- |
| English | +9 | +6 | +9 |
| Japanese | +1 | +6 | +6 |

Times are medians of wall-clock time around non-streaming calls, in ms (p90 in brackets). Answer is as defined in the [heavy prompt-order run](../prompt-order-heavy-2026-11-26/README.md#results).

Cutting to one memory shrank the first persona-prompt call by about 70–90 tokens on the median (A 1,551 to 1,480, B 2,452 to 2,360). Cutting to one memory changed no median answer by more than 230 ms (B 2,731 (4,052) to 2,498 (3,942); A 4,741 (6,603) to 4,702 (6,345)).

## Reading

- **Memory count doesn't explain the English A vs B gap on this run.** With one memory in both languages, on this model and the heavy profile, A1 beat B1 in English by 9 points (p = 0.021), as wide as in the 11-26 run. Cutting to one memory changed neither order: A vs A1 and B vs B1 split almost evenly.
- **The one-prompt order's loss is not English only.** With Japanese at 4 memories, B trailed A by 6 points in both languages. In the 11-26 run Japanese had about 1 memory and the gap there was 1 point. That comparison is across runs, so it isn't paired.
- **The live tiered order holds its accuracy with the extra Japanese memories:** 92% here against 91% in the 11-26 run.
- **Recommendation:** keep the already-shown fix, so Japanese turns get the memories the lookup finds. No change to the memory limit. B's loss on this run stays when the memory count is the same, so it isn't the extra English memories. The one-prompt order isn't live.

## Limits

- One model, one machine, synthetic memories and lines. The Japanese lines are machine-translated.
- The Japanese candidates barely separate on relevance: the top 8 sit at about 0.30–0.47 and all 20 clear the 0.27 floor. The embedder ranks Japanese poorly, so the 4 Japanese memories are close to a random pick from the haystack. This run doesn't test better Japanese ranking.
- FTS keyword matching (`_TOKEN` in `retrieve.py`) finds only Latin words, so Japanese lines get no keyword boost.
- The heavy profile's summary names Alex, which is what made the filter bug so wide here. A real summary may hide fewer memories.
- 3 repeats at temperature 0.6. 87 turns per arm and language.
- One turn (B1, a Japanese line) ended with an empty reply from the server and is left out.
- **Timing:** wall clock around non-streaming calls, with no time-to-first-token.
- The p-values are uncorrected across the four paired comparisons.

## Files

- [`harness/`](harness/): a copy of the bench (`bench.py`, `heavy.py`, `lines.py`, `long_results.py`, `summarize.py`), plus [`memory_count.py`](harness/memory_count.py) for step 1. Arms A1 and B1 are `kept(arm, 1)` in `bench.py`.
- [`counts/`](counts/): `before-fix.jsonl` and `after-fix.jsonl`, one row per line from `memory_count.py`.
- `run/turns.jsonl`: one row per turn. `run/steps.jsonl`: one row per model call. `run/raw-output.txt`: the console log.
- [`summary.md`](summary.md): the tables from `summarize.py`.

To run it again, copy `harness/` into `bench/prompt_order/` in a CetiMind checkout with the fix, then:

```bash
uv run python bench/prompt_order/memory_count.py --base-url http://HOST:PORT/v1 --out counts
uv run python bench/prompt_order/bench.py --base-url http://HOST:PORT/v1 --out run --profile heavy --arms A,B,A1,B1 --repeats 3
uv run python bench/prompt_order/summarize.py run
```

`counts/before-fix.jsonl` needs a checkout from before the fix.
