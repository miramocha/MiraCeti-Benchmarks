# Memory classifier: Kev vs the judge model

Is Kev worth running in CetiMind's memory pipeline? This experiment tests the two places [CetiMind#53](https://github.com/miramocha/CetiMind/issues/53) proposed for a small classifier:

- **Item 1, learn gate:** before the extract call, ask "does this line state something about the user worth remembering?" Skip `learn()` when the answer is no.
- **Item 3, dedupe:** for a new fact next to a stored one, decide whether it is the same fact, an update, or a different fact.

**Verdict: don't add Kev for now.**

- Kev fails as a learn gate.
- Kev wins dedupe by 2 pairs out of 30 over a JSON check on the judge model. That is within noise, and it doesn't justify a new dependency.
- On CUDA, Kev slows the next reply's first token about 8×. On CPU it does not.

Run on Nov 16 2026. One run per case, hand-written cases, so treat the results as directional.

## Setup

- **Machine:** Windows 11, one RTX 4070 (12 GB). Other apps (OBS, Discord, Steam) also used the GPU.
- **LLM server:** LM Studio, OpenAI-compatible API, on the same machine.
  - `qwen3.5-4b` (GGUF `Q4_K_S`): the chat model and the judge.
  - `nvidia/nemotron-3-nano-4b` (GGUF `Q4_K_M`): the tool model.
  - `text-embedding-nomic-embed-text-v1.5`: the embedding model.
  - Both chat models: context 6144, `parallel` 4, flash attention on, K/V cache `q8_0`.
- **Kev:** `jaredpalmer/kev-0.8b@bf75a6a8848ea6960ff2ed108d9ed44c2941174f` (a pointer head on `Qwen/Qwen3.5-0.8B-Base`), served by `kev.serve`, torch float32.
  - **CUDA:** the usual instance on port 8009, about 4.0 GB of dedicated GPU memory. With it loaded, the GPU used 11.2–11.4 GB of 12.3 GB.
  - **CPU:** a second instance started for this test on port 8019 (`--device cpu`).
- **CetiMind:** `main` at `a0771d4`.
- **JSON candidates:** `JudgeAdapter.complete_json`, the path the app's judge uses. `judge_thinking` was `auto`, which means thinking off for judge calls. Temperature 0, `judge_max_tokens` 1024. The capability probe found that `reasoning_effort` switches thinking for both models.
- **Load:**
  - **Accuracy run:** the CetiMind app and CetiAct (which also calls Kev) were running. Its latencies are rough.
  - **Time-to-first-token runs:** both apps were paused.

## Method

The cases are in [`scripts/cases.py`](scripts/cases.py). All are synthetic.

- **Gate:** 30 English and 30 Japanese lines. In each language, 15 are worth remembering (a lasting fact, preference, person, pet, plan, or a past event) and 15 are not (greetings, small talk, questions, requests).
- **Dedupe:** 15 English and 15 Japanese pairs of a stored fact and a new fact. Each language has 5 pairs labeled `same`, 5 `update` and 5 `different`.

### Candidates

| Candidate | Gate (item 1) | Dedupe (item 3) |
| --- | --- | --- |
| Kev | `noul` question. A score of 0.5 or more counts as yes. | `choice` over `same`, `update`, `different` |
| nemotron JSON | `{"remember": bool}` | `{"relation": enum}` |
| qwen JSON | the same | the same |
| Baseline | Today's extract: the real `learn()` on qwen in a temp store. "Yes" means it stored something. | Today's path: the real `place()` on a store seeded with the stored fact. It uses the nomic thresholds (`LEARN_ADD_BELOW` 0.80, `LEARN_REPLACE_AT` 0.92, `LEARN_SKIP_AT` 0.97), then the qwen decide call. The action maps to a label: `add` is different, `merge` and `replace` are update, `skip` is same. |

### Prompts

The gate question was sent as the Kev `noul` instructions, with `User: <line>` as the state. The JSON candidates got the same question with `\nUser: <line>` after it:

> Does the user's line state something about the user worth remembering later: a lasting fact, preference, person, pet, plan, or something that happened to them? Greetings, small talk, passing moods, questions and requests are not.

The dedupe question was "How does the new fact relate to the stored fact?", with these criteria:

- `same`: The same fact, nothing new.
- `update`: The same subject with a changed, corrected or added detail.
- `different`: A different fact about something else.

The state was `Stored fact: … \nNew fact: …`.

### Time to first token

This measures how much a background check slows the next reply. A background call starts, and 20 ms later a streamed `qwen3.5-4b` reply begins:

- System prompt: "You are Ceti, a cheerful companion. Be brief."
- User line: "Tell me something nice about autumn."
- 48 tokens, thinking off.

The time is from the request to the first content token. There are 10 rounds per condition.

## Results

### Item 1: learn gate

| Candidate | EN recall / precision | JA recall / precision | Median |
| --- | --- | --- | --- |
| Kev `noul` | 0.07 / 0.50 | 0.20 / 0.75 | ~550 ms (CUDA), ~1.15 s (CPU) |
| nemotron JSON | 0.80 / 0.86 | 1.00 / 0.88 | ~800 ms |
| **qwen JSON** | **0.93 / 1.00** | **0.87 / 0.93** | ~0.7–1.3 s |
| Today's extract on qwen (no gate) | 0.93 / 1.00 | 0.80 / 0.86 | ~2.2 s |

Counts (true positives / misses / false positives / true negatives, out of 15 + 15 per language):

| Candidate | EN | JA |
| --- | --- | --- |
| Kev | 1 / 14 / 1 / 14 | 3 / 12 / 1 / 14 |
| nemotron | 12 / 3 / 2 / 13 | 15 / 0 / 2 / 13 |
| qwen | 14 / 1 / 0 / 15 | 13 / 2 / 1 / 14 |
| Today's extract | 14 / 1 / 0 / 15 | 12 / 3 / 2 / 13 |

- **Kev says "no" to almost everything.** Its average score was 0.34 on lines worth remembering and 0.28 on the rest (AUC 0.69). The best threshold, tuned on these same lines, still got 23 of 60 wrong. Scores were identical across 2 repeats.
- **Effect against today's extract:**
  - qwen as a gate would skip 32 of 60 extract calls and lose 3 lines. Two of the 3 are lines extract stores by mistake ("User expressed gratitude.").
  - nemotron would skip 29 and lose 5.
  - Kev would skip 54 and lose 22.
- **Extract's own misses:** a dentist visit (in both languages), "猫の名前はモチ", and "Neovim派".

### Item 3: dedupe

| Candidate | EN | JA | Median |
| --- | --- | --- | --- |
| **Kev `choice`** | **14/15** | **14/15** | ~500 ms (CUDA), ~1.2 s (CPU) |
| nemotron JSON | 13/15 | 13/15 | ~700 ms |
| qwen JSON | 13/15 | 13/15 | ~1.4 s |
| Today's path (thresholds, then judge) | 12/15 | 11/15 | 1.3–2.9 s |

Right per label (same / update / different, out of 5 each):

| Candidate | EN | JA |
| --- | --- | --- |
| Kev | 5 / 4 / 5 | 5 / 5 / 4 |
| nemotron | 4 / 5 / 4 | 4 / 4 / 5 |
| qwen | 3 / 5 / 5 | 3 / 5 / 5 |
| Today's path | 4 / 3 / 5 | 4 / 2 / 5 |

- **Kev has no answer bias:** it predicted each label 10 times out of 30. Both of its misses were close calls (0.51 against 0.39, and 0.42 against 0.41).
- **Today's path loses updates because it never asks.**
  - In English, Tokyo to Kyoto had cosine 0.825 and VS Code to Neovim had 0.826. In Japanese the same pairs had 0.863 and 0.826.
  - Each is just over `LEARN_ADD_BELOW` 0.80, so the new fact is added and the old one stays.
  - "猫モチは3歳 / 4歳になった" scored 0.907, so the judge was asked, and it still added a new fact.
  - A Japanese "same" pair at 0.793 fell below the band and was added.

### Time to first token while a check runs

| Running at the same time | Median TTFT | Max |
| --- | --- | --- |
| Nothing | 94 ms | 107 ms |
| **Kev `noul`, CUDA** | **776 ms** | 1064 ms |
| nemotron gate JSON | 110 ms | 1015 ms |
| qwen gate JSON | 219 ms | 295 ms |
| Today's extract on qwen | 154 ms | 222 ms |
| Nothing (CPU run) | 79 ms | 102 ms |
| **Kev `noul`, CPU** | **106 ms** | 117 ms |

- **Kev on CUDA slows the next reply's first token about 8×.** Its unfused float32 PyTorch path seems to compete with llama.cpp for GPU compute, not just memory.
- **A stall during the accuracy run:** one qwen request timed out after 60 s while Kev's shared GPU memory was 386 MB. That is the spill zone, with the GPU above about 11 GB used.
- **Kev on CPU gives the same answers as on CUDA:** none of 90 predictions differed, and gate scores stayed within 0.011. It adds about 27 ms to the next reply's first token.

## What it means

- **Learn gate:** use a thinking-off JSON call on the judge model. Kev can't do this job.
- **Dedupe:** most of the gain comes from asking a classifier when a pair falls in the 0.80–0.92 zone, not from which classifier is asked. Widen the band so updates in that zone are asked, and use a JSON check on the judge model. Kev's 2-pair lead is within noise.
- **If Kev is used later, run it on CPU only.** That costs about 1.2 s per question in the background, about 3.8 GB of RAM, and a CetiModel service that must be running.

## Not measured

- Kev `bf16` on CUDA.
- Real pairs from a memory store (these are clean, hand-written pairs).
- More than one run per case.
- Persona extract.
- Summary, profile and reflection with each model.

## Files

- `scripts/cases.py`: the labeled cases.
- `scripts/bench.py`: gate, dedupe and TTFT for every candidate. Run it as `bench.py <settings.toml> <out.jsonl> [gate|dedupe|ttft ...]` with the CetiMind checkout. It opens a temp data dir only.
- `scripts/kev_only.py`: the Kev rows only, against `KEV_URL`. Used for the CPU run.
- `scripts/summarize.py`: the tables above, from the JSONL files.
- `data/run1.jsonl`: the accuracy run, with Kev on CUDA.
- `data/ttft1.jsonl`: the TTFT run.
- `data/kevcpu.jsonl`: Kev on CPU, covering accuracy and TTFT. The run-metadata rows were removed.
