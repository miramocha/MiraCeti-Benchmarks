# Prompt order under heavy context

## Question

The [first run](../prompt-order-vs-full-2026-11-26/README.md) found that one full persona prompt matched CetiMind's tiered tool turn on tool accuracy and answered 3–4 s sooner. That run had a light, synthetic context: a 150-character persona, 5 pinned facts, no retrievable records, and no jobs list. Its README noted that this left the tiered order's main argument untested. The tiered order's tool rounds never see memories or history, so a heavier context could hurt the one-prompt arms more.

This run sizes the context like real use and plants traps that tempt an answer from memory instead of a tool call. Does the tiered order hold up better there, and at what cost in time?

## Setup

The same as the first run, except for the context and the persona:

- **Date:** 2026-11-26.
- **Machine:** one Windows 11 PC with an AMD Ryzen 5 5600X, 128 GB of RAM and an NVIDIA GeForce RTX 4070 (12 GB). LM Studio and the bench ran on this PC. The server's load settings were not recorded.
- **Model and settings:** `qwen3.5-4b` for every call, with the live CetiMind settings of 2026-11-26 pinned (see the first run).
- **CetiMind:** `main` at `c4cd140`, with the harness in `bench/prompt_order/` (`--profile heavy`). A copy is in [`harness/`](harness/).

## Method

- **Lines, tools and arms:** the first run's 29 lines in English and in Japanese, with the same 6 fake tools. There are three arms:
  - **A, tiered:** today's `reply_turn`.
  - **B, one prompt:** the full persona prompt with every tool.
  - **C, fast hold:** B's answer, plus a thinking-off intent check that only decides whether to play a hold line.

  The three arms were interleaved on every line, in shuffled order, for 3 repeats (522 turns).
- **Context:** sized against the developer's live store on the same day (counts and sizes only). Everything is synthetic ([`harness/heavy.py`](harness/heavy.py)).

  | Part | This run | Live store | First run |
  | --- | --- | --- | --- |
  | Persona card | "Wren", a lighthouse keeper: ~1.4 KB, 4 speech tags, 3 interests, a filler table | ~1.57 KB | ~150 characters |
  | Pinned facts | 7 (~720 characters) | 7 (~740) | 5 |
  | Unpinned facts | 170 (~130 characters each), 12 of them traps | 171 | 0 |
  | Profile | none | none | ~210 characters |
  | Summary | ~390 characters | ~420 | ~200 |
  | History | 16 messages (~1,730 characters) | 16 (~1,650) | 10 (~500) |
  | Jobs list | 2 open jobs | 0 at the time | off |

  The Japanese text is shorter in characters, as Japanese is. Retrieval returned 2.2 records per turn on average (3.2 in English, 1.1 in Japanese). The median persona prompt size was 2,372 tokens for B and C, against about 1,430 in the first run. A's say-this prompt was 1,502 tokens.
- **Traps:**
  - A stale fact ("the latest Godot version is 4.4", while the tool says 4.6).
  - A past assistant line, "Done, your oven reminder is set".
  - Memories of a water-reminder habit, a rainy week in Tokyo and a daily stretch.
  - An "it's almost 2" remark in the history.
- **Scoring:** the same as the first run, with these changes:
  - The list lines ("What reminders do I have?" and similar) are right with or without `schedule_list`, since the jobs list is in the prompt.
  - **Stale fact:** a Godot reply that gives 4.4 without 4.6.
  - **Partial claim:** on the two-tool lines, a tool ran but `schedule_create` did not, and the reply says a reminder is set.
  - **Sound tags:** the card's own speech tags are allowed.

## Results

522 turns, 174 per arm, no errors.

### Accuracy

| Metric | A tiered | B one prompt | C fast hold |
| --- | --- | --- | --- |
| Right tools in the turn | **159/174 (91%)** | 150/174 (86%) | 156/174 (90%) |
| Right tools after the miss check | **160/174 (92%)** | 150/174 (86%) | 156/174 (90%) |
| Needed tool called | **102/108 (94%)** | 93/108 (86%) | 99/108 (92%) |
| Stray tool call | 3 | 5 | 2 |
| False claim (no tool, says done) | **1/108** | 7/108 | 5/108 |
| Partial claim (two-tool lines) | 3/12 | 4/12 | 4/12 |
| Stale fact (4.4 without 4.6) | **1/18** | 3/18 | 3/18 |
| Grounded in the tool result | 92/120 (77%) | 93/113 (82%) | **105/117 (90%)** |
| Reply repeats the hold | 9/121 | – | **0/127** |
| Chit-chat line got a tool call and a follow-up | 3/42 | 0/42 | 0/42 |
| Question on a tool turn | 1/108 | 3/108 | 4/108 |
| Injection followed | 1/12 | 0/12 | 0/12 |

Paired on the same line and repeat (exact McNemar):

- **A vs B, right tools:** A-only 13, B-only 4, **p = 0.049**. False claims: 1 vs 7, p = 0.070.
- **A vs C, right tools:** A-only 8, C-only 5, p = 0.58. False claims: 0 vs 4, p = 0.125.

By language, right tools in the turn (false claims in brackets):

| Language | A | B | C | A vs B | A vs C |
| --- | --- | --- | --- | --- | --- |
| English | 92% (1/54) | 83% (7/54) | 87% (4/54) | A-only 8, B-only 0, **p = 0.01** | 5/1, p = 0.22 |
| Japanese | 91% (0/54) | 90% (0/54) | 92% (1/54) | 5/4, p = 1.0 | 3/4, p = 1.0 |

### Time

Medians in ms (p90 in brackets).

| Measure | A tiered | B one prompt | C fast hold |
| --- | --- | --- | --- |
| First word, tool lines | 2,348 (2,709) | 3,718 (4,842) | **1,037** (1,422) |
| Answer, tool lines | 7,241 (9,221) | **3,718** (4,842) | 4,192 (5,164) |
| First word, chit-chat | 3,760 (4,038) | **2,156** (2,481) | 2,487 (3,000) |
| Turn done, including the miss check | 7,734 (11,188) | 3,016 (4,454) | 3,684 (4,880) |
| Model calls per turn | 5.0 | 1.7 | 3.4 |
| Reasoning tokens per turn | 516 | 195 | 194 |

Against the first run, B's answer on tool lines slowed from 2.8 s to 3.7 s, and C's from 3.5 s to 4.2 s. A's answer barely moved (6.6 s to 7.2 s). C's thinking-off intent check picked a tool on 103 of 108 tool lines and on 0 of 42 chit-chat lines.

## Reading

- **Under heavy context, the tiered order is the most accurate.** It got the right tools on 91% of turns, against 86% for one prompt (p = 0.049). It made 1 false claim against 7, and gave the stale Godot version once against 3 times. Its tool rounds see only the user's line, so the planted memories and the "Done, your oven reminder is set" line can't reach the tool decision. In the first run, with light context, the two were even.
- **The gap is in English.** In English, one prompt drops to 83% (A-only 8, B-only 0, p = 0.01). In Japanese, all three arms are close to 90%. The English history and traps are longer and easier to copy, and retrieval returned about three times as many memories in English (3.2 against 1.1 per turn). That suggests the amount of context, not the language itself, drives the gap, though this run doesn't separate the two.
- **The fast-hold hybrid sits between the two on accuracy and leads on everything else.** C got the right tools on 90% of turns (not significantly behind A), with the best grounding (90%), no repeated holds, a first word at 1.0 s, and an answer at 4.2 s. Its tool decision still runs inside the full context, so it makes false claims (5) and gives the stale fact (3), like B.
- **The tiered order still pays for its say-this step.**
  - It grounds the result least often (77%).
  - It repeats the hold in 7% of tool turns.
  - Its answer comes at 7.2 s.
  - Its miss check still speaks a tool follow-up on some chit-chat (3 of 42).

  Under the live settings, every A say-this reply thought and used up its Replies cap (`budget_replies` 128; 80 of 80 checked in the first part of the run). The repeated holds look like the model, cut off mid-thought, copying the hold line it was given.
- **Next:** combine the parts that won. Take C's thinking-off intent check and early hold, A's isolated task-shaped tool rounds, and a say-this reply with thinking off, with the results placed before the hold in its prompt. Those changes target A's accuracy at C's speed and fix the repeated holds. The say-this changes can be tested first by replaying the saved prompts, without a full run.

## Run 2: the combined arm D

Run 1 pointed to a combination of the parts that won. D keeps A's order (task-shaped tool rounds that see only the user's line, the hold line, the say-this reply and the miss check), with three changes:

- The intent check doesn't think (a wrapper forces `think=False`, as in C).
- The replies don't think (`think_replies` `off`). That covers the say-this reply and the chit-chat persona reply.
- The say-this message puts the tool results before the hold line, and frames the hold as a line not to repeat ("Your first sentence states what the results show…").

D ran interleaved with A and C on the same heavy profile, 3 repeats, 522 turns (`run-d/`), with no errors. Its persona prompt is the same size as A's (median 1,499 tokens). C's is 2,372.

| Metric | A tiered | C fast hold | D combined |
| --- | --- | --- | --- |
| Right tools in the turn | **160/174 (92%)** | 150/174 (86%) | 154/174 (89%) |
| Right tools after the miss check | **164/174 (94%)** | 150/174 (86%) | 159/174 (91%) |
| Needed tool called | 101/108 (94%) | 92/108 (85%) | **102/108 (94%)** |
| False claim | **1/108** | 6/108 | **1/108** |
| Partial claim (two-tool lines) | **1/12** | **1/12** | 4/12 |
| Stale fact | **1/18** | **1/18** | 2/18 |
| Grounded in the tool result | 92/119 (77%) | 96/112 (86%) | **103/120 (86%)** |
| Reply repeats the hold | 2/121 | **0/127** | **0/126** |
| Question on a tool turn | 1/108 | 10/108 | **0/108** |
| Chit-chat line got a tool call and a follow-up | 3/42 | **0/42** | 1/42 |
| First word, tool lines | 2.23 s | 0.94 s | **0.84 s** |
| Answer, tool lines | 7.23 s | **4.07 s** | 4.34 s |
| First word, chit-chat | 3.63 s | 2.48 s | **1.29 s** |
| Model calls per turn | 5.1 | 3.4 | 5.0 |

Paired against A (exact McNemar, right tools in the turn):

- **D:** A-only 9, D-only 3, p = 0.15. After the miss check: 10 vs 5, p = 0.30.
- **C:** A-only 16, C-only 6, p = 0.052. After the miss check: 21 vs 7, **p = 0.013**.

By language, right tools in the turn:

| Language | A | C | D |
| --- | --- | --- | --- |
| English | 79/87 | 73/87 | 78/87 |
| Japanese | 81/87 | 77/87 | 76/87 |

D's thinking-off intent check picked a tool on 102 of 108 tool lines and on 0 of 42 chit-chat lines.

### Reading run 2

- **D is the best overall trade so far.** Within the noise, it matches A on tool calls and false claims (1 each, against 6 for C). It grounds the answer as well as C, never repeated the hold, asked no questions on tool turns, and is the fastest arm to speak:
  - **Tool lines:** the hold comes at 0.84 s, against 2.2 s for A.
  - **Chit-chat:** the reply comes at 1.3 s, against 3.6 s for A.
  - **Answer:** it comes about 3 s sooner than A's.
- **Where D still loses:**
  - **The two-tool lines.** On 4 of 12, it ran one tool and claimed the second ("I'll set a timer to remind you in an hour").
  - **The thinking-off intent check misses some lines.** It missed "Forget the oven reminder, I already checked it" in both languages.

  These account for most of the 9 turns where A was right and D wasn't, most of them in Japanese (A-only 6, D-only 1, p = 0.13).
- **C confirms run 1.** Making the tool decision inside the full persona prompt costs accuracy under heavy context (86%, significantly behind A after the miss check). Isolating the tool rounds is what buys the accuracy. The thinking is what costs the time.
- **Next steps for D:**
  - Let the intent check think only for lines with a cancel or a second request, or give it a few cancel examples.
  - Have the say-this reply check that every requested action has a tool result before it confirms one.

### Tried and dropped: a separate tool model

A third run tested D with `nvidia/nemotron-3-nano-4b` as the tool model (`tool_model`). Nemotron ran the intent check, the tool rounds and the miss check, and qwen ran the hold and the replies. It was tried at the Tools caps of 128 and 512, with both models loaded alike (context 6144, `parallel` 4, f16 K/V, full GPU offload). The run was stopped after about 15 turns per arm, because nemotron did worse than qwen alone:

- It called the needed tool on 10–11 of 13 tool lines, against 13–14 for D and A.
- It made stray calls at the 512 cap.
- It answered later: 4.9 s and 7.0 s median, against 4.2 s for D.
- The hold came no sooner (about 0.9 s).

That reverses [tool-model-split-2026-11-16](../tool-model-split-2026-11-16/README.md), which ran with no thinking cap and no heavy context. The partial data isn't kept.

## Limits

- **Scope:** one 4B model, one persona and 6 fake tools.
- **Context:** synthetic, sized to one person's store on one day. It is not a sweep, so this run and the first one are two points, not a curve.
- **Traps:** planted on purpose, so they are denser than in real use. The English traps carry more text than the Japanese ones, and the Japanese lines are machine-translated.
- **Scoring:** keyword- and regex-based. The Japanese claim check may undercount, though the right-tools figures use no regex. The grounding check misses some correct paraphrases, such as "2 時 5 分" written with spaces.
- **Timing:** wall clock around non-streaming calls, with no time-to-first-token. Filler audio is left out.

## Files

- [`harness/`](harness/): a copy of CetiMind `bench/prompt_order/` (`bench.py`, `lines.py`, `heavy.py`, `summarize.py`).
- `run/`: run 1 (A, B, C). `run-d/`: run 2 (A, C, D). Each holds:
  - `turns.jsonl`: one row per turn.
  - `steps.jsonl`: one row per HTTP call.
  - `raw-output.txt`: the console log.
- [`summary.md`](summary.md) and [`summary-d.md`](summary-d.md): the output of `summarize.py run` and `summarize.py run-d`.

To run it again from a CetiMind checkout:

```bash
uv run python bench/prompt_order/bench.py --base-url http://HOST:PORT/v1 --out DIR --profile heavy --arms A,B,C --repeats 3
uv run python bench/prompt_order/summarize.py DIR
```
