# GPU memory and model switching

## Question

With two chat models loaded on one 12 GB GPU, why did some split turns (chat on one model, tools on the other) take 15–43 s, when the same lines took 3–6 s on one model? And how much memory do K/V cache quantization and a shorter context free?

The same data is in CetiMind #79 as experiments 16 and 17.

## Setup

- **Date:** Nov 16 2026.
- **Machine:** one Windows 11 PC with an NVIDIA GeForce RTX 4070 (12 GB). Discord, Steam and Edge were also running and using the GPU.
- **Server:** LM Studio on the same machine, which runs one `llama-server` process per loaded model.
- **Models:**
  - `qwen3.5-4b` (`Q4_K_S`).
  - `nvidia/nemotron-3-nano-4b` (`Q4_K_M`).
  - `text-embedding-nomic-embed-text-v1.5` (`Q4_K_M`, context 2048).
- **Three conditions:**
  1. **Card nearly full:** context 8192, flash attention on, no K/V quantization.
  2. **After freeing GPU memory:** other apps closed, same settings.
  3. **After K/V q8_0 and context 6144:** one reload of both chat models changed both settings at once.
- **CetiMind:** branch `feat/tool-model-77` (merged as `75f69b3`).

## Method

- **Intent check timing,** `bench.py switch` from [tool-model-split-2026-11-16](../../tool-model-split-2026-11-16/README.md):
  - CetiMind's intent check (`IntentRouter.decide`) on nemotron, for "Remind me to drink water in 20 minutes." with 6 tools, n = 10.
  - **after_nemotron:** run right after a short nemotron chat call ("Say one short friendly sentence.", thinking off).
  - **after_qwen:** run right after the same call on qwen.
- **Model after model:** each model's chat call right after a call to itself and right after a call to the other model, n = 8, `max_tokens` 64. This was a one-off inline script, condition 2 only.
- **GPU memory:**
  - `nvidia-smi` for the card's dedicated memory in use.
  - Task Manager for the card's shared GPU memory.
  - The Windows performance counters `\GPU Process Memory(pid_*)\Dedicated Usage` and `\GPU Process Memory(pid_*)\Shared Usage` for each `llama-server` process, read with PowerShell `Get-Counter`.

## Results

### Intent check after each model (median)

| Condition | GPU memory | After nemotron | After qwen |
| --- | --- | --- | --- |
| 1. Card nearly full | 10.8 / 12.3 GB used. Task Manager: 11.0 / 12.0 GB dedicated, 0.8 GB shared | 326 ms | 1,322 ms |
| 2. After freeing GPU memory | 9.9 GB used | 305 ms | 232 ms |
| 3. After K/V q8_0 and context 6144 | 9.8 GB used | 327 ms | 251 ms |

Rows 1 and 3 are in `switch-timing.jsonl`, with all ten times each. Row 2's times were not saved to a file.

### Model after model (condition 2, median)

| Call | Median |
| --- | --- |
| qwen after qwen | 590 ms |
| qwen after nemotron | 381 ms |
| nemotron after nemotron | 188 ms |
| nemotron after qwen | 182 ms |

### Per-process memory (conditions 2 and 3)

| Process | Dedicated before | Dedicated after | Shared before | Shared after |
| --- | --- | --- | --- | --- |
| nemotron (smaller process) | 3,239 MB | 3,103 MB | 112 MB | 110 MB |
| qwen (larger process) | 4,623 MB | 4,523 MB | 174 MB | 108 MB |

Which process is which model was inferred from their sizes.

### Split turns (from the tool-model runs)

| Condition | Split median turn | Notes |
| --- | --- | --- |
| 1. Card nearly full | 4.7 s, p90 21 s | Third repeat: simple turns took 15–43 s, while the one-model setups stayed normal in the same stretch |
| 2. After freeing | 4.7 s | Slowest turn 11.8 s |
| 3. After K/V and context 6144 | 3.1–3.2 s | Two sessions |

## What it means

- **CetiMind never swaps the models.** Both stay loaded, and the requests never overlap, except the embedding call during the intent check. The ~1 s cost came from moving between models while the card was nearly full.
- **Windows spills instead of failing.** With the card full, the driver quietly moves part of a model into system RAM ("shared GPU memory") and pulls it back on that model's next request.
  - That fits a cost that shows up only when moving between models, never on back-to-back calls to one model.
  - It also fits one repeat where simple split turns took 15–43 s.
- **Headroom fixed it.** Freeing about 1–2 GB removed the extra cost in both directions.
- **Spill can be watched per model.** With headroom, each `llama-server` process showed about 110–175 MB shared, as a baseline. A slow intent check is a cheaper signal, and it also works when the server is on another machine.
- **K/V q8_0 plus context 6144 freed about 240 MB.** That's small: these models use attention layers, which the K/V cache serves, in only part of the network.
- **The speed-up after the reload is not isolated.** The split's median fell from 4.7 s to 3.1–3.2 s, but other GPU apps and the time of day changed too, and timings on this machine swing between sessions.
- **Context length vs. max tokens:**
  - LM Studio's context length reserves GPU memory at load, sized for the full window.
  - CetiMind's `max_tokens` only caps output, thinking included.
  - The context has to fit the largest prompt plus `max_tokens`.
  - The tool model's rounds carry the full chat prompt, so it needs as much context as the chat model.

## Limits

- **The spill cause is partly inferred.** The per-process counter was not read during the slow repeat. The card-wide 0.8 GB shared reading was taken near it.
- **K/V quantization and context length are not separated:** they changed in one reload.
- **Small samples:** n = 10 and n = 8.
- **One machine,** and other GPU apps were not controlled for.

## Files

- `switch-timing.jsonl`: the intent check times for conditions 1 and 3, with the condition, the model called before it, and all ten times.
