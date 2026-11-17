"""#53 bench: Kev vs nemotron vs qwen for the learn gate (item 1) and dedupe (item 3), plus next-turn TTFT.

Usage: uv run --project <CetiMind> python bench.py <settings.toml> <out.jsonl> [gate|dedupe|ttft ...]
Temp store only; the real data folder is never opened.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

os.environ["CETIMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="cetimind-kev53-")
sys.path.insert(0, str(Path(__file__).parent))

import httpx2 as httpx  # noqa: E402

from cases import GATE_EN, GATE_JA, PAIRS_EN, PAIRS_JA  # noqa: E402
from cetimind.app.judge import JudgeAdapter  # noqa: E402
from cetimind.app.settings import Settings  # noqa: E402
from cetimind.config import llm_base_url  # noqa: E402
from cetimind.llm.client import LlmClient  # noqa: E402
from cetimind.memory.learn import Candidate, learn, place  # noqa: E402
from cetimind.memory.store import ListQuery, Store  # noqa: E402

EMBED = "text-embedding-nomic-embed-text-v1.5"
QWEN = "qwen3.5-4b"
NEMO = "nvidia/nemotron-3-nano-4b"
KEV = os.environ.get("KEV_URL", "http://127.0.0.1:8009/v1/systemone")

GATE_Q = (
    "Does the user's line state something about the user worth remembering later: a lasting fact, "
    "preference, person, pet, plan, or something that happened to them? Greetings, small talk, passing "
    "moods, questions and requests are not."
)
GATE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["remember"],
    "properties": {"remember": {"type": "boolean"}},
}
REL_Q = "How does the new fact relate to the stored fact?"
REL_CRITERIA = {
    "same": "The same fact, nothing new.",
    "update": "The same subject with a changed, corrected or added detail.",
    "different": "A different fact about something else.",
}
REL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["relation"],
    "properties": {"relation": {"type": "string", "enum": list(REL_CRITERIA)}},
}
ACTION_TO_REL = {"add": "different", "merge": "update", "replace": "update", "skip": "same"}

OUT = None
LOCK = threading.Lock()


def emit(row: dict) -> None:
    line = json.dumps(row, ensure_ascii=False)
    with LOCK:
        OUT.write(line + "\n")
        OUT.flush()
    print(line, flush=True)


def ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def client(settings: Settings, base: str, model: str) -> LlmClient:
    return LlmClient(
        base, model, EMBED, max_tokens=settings.judge_max_tokens, thinking="auto",
        capabilities=settings.capabilities_for(base, model), judge_max_tokens=settings.judge_max_tokens,
    )


def open_store(embedder: LlmClient) -> Store:
    folder = Path(tempfile.mkdtemp())
    return Store.open(folder / "m.db", embedder=embedder, embed_model=EMBED, embed_dim=768,
                      clock=lambda: datetime.now(UTC))


def kev(state: str, question: dict, http: httpx.Client) -> dict:
    body = {"state": state, "model": "kev-latest", "questions": {"q": question}}
    response = http.post(KEV, json=body, headers={"X-S1-App": "cetimind", "X-S1-Run": "kev53"})
    response.raise_for_status()
    return response.json()["answers"]["q"]


# ---------- item 1: gate ----------

def gate(settings: Settings, base: str) -> None:
    qwen, nemo = client(settings, base, QWEN), client(settings, base, NEMO)
    judges = {"qwen": JudgeAdapter(qwen), "nemotron": JudgeAdapter(nemo)}
    http = httpx.Client(timeout=30)
    try:
        for lang, cases in (("en", GATE_EN), ("ja", GATE_JA)):
            for index, (line, label) in enumerate(cases):
                base_row = {"part": "gate", "lang": lang, "case": index, "line": line, "label": label}
                # Kev noul, twice to check it is deterministic.
                for repeat in range(2):
                    started = time.perf_counter()
                    try:
                        answer = kev(f"User: {line}", {"type": "noul", "instructions": GATE_Q}, http)
                        p = answer["noul"]
                        emit({**base_row, "cand": "kev", "repeat": repeat, "p": p, "pred": p >= 0.5, "ms": ms(started)})
                    except Exception as error:  # noqa: BLE001
                        emit({**base_row, "cand": "kev", "repeat": repeat, "error": str(error)[:200], "ms": ms(started)})
                for name, judge in judges.items():
                    started = time.perf_counter()
                    try:
                        payload = judge.complete_json(f"{GATE_Q}\nUser: {line}", GATE_SCHEMA)
                        emit({**base_row, "cand": name, "pred": bool(payload.get("remember")), "ms": ms(started)})
                    except Exception as error:  # noqa: BLE001
                        emit({**base_row, "cand": name, "error": str(error)[:200], "ms": ms(started)})
                # No-gate baseline: the real extract on qwen (today's judge). pred = it stored something.
                store = open_store(qwen)
                started = time.perf_counter()
                try:
                    learn(store, judges["qwen"], qwen, line, name="User", assistant="Ceti")
                    stored = [r.text for r in (*store.list_records(ListQuery(kind="fact")),
                                               *store.list_records(ListQuery(kind="event")))]
                    emit({**base_row, "cand": "extract_qwen", "pred": bool(stored), "stored": stored, "ms": ms(started)})
                except Exception as error:  # noqa: BLE001
                    emit({**base_row, "cand": "extract_qwen", "error": str(error)[:200], "ms": ms(started)})
                finally:
                    store.close()
    finally:
        qwen.close()
        nemo.close()
        http.close()


# ---------- item 3: dedupe ----------

def rel_prompt(stored: str, new: str) -> str:
    options = " ".join(f"{key}: {text}" for key, text in REL_CRITERIA.items())
    return f"{REL_Q} {options}\nStored fact: {stored}\nNew fact: {new}"


def dedupe(settings: Settings, base: str) -> None:
    qwen, nemo = client(settings, base, QWEN), client(settings, base, NEMO)
    judges = {"qwen": JudgeAdapter(qwen), "nemotron": JudgeAdapter(nemo)}
    http = httpx.Client(timeout=30)
    try:
        for lang, cases in (("en", PAIRS_EN), ("ja", PAIRS_JA)):
            for index, (stored, new, label) in enumerate(cases):
                base_row = {"part": "dedupe", "lang": lang, "case": index, "stored": stored, "new": new, "label": label}
                started = time.perf_counter()
                try:
                    answer = kev(f"Stored fact: {stored}\nNew fact: {new}",
                                 {"type": "choice", "instructions": REL_Q, "criteria": REL_CRITERIA}, http)
                    emit({**base_row, "cand": "kev", "pred": answer.get("choice"), "raw": answer, "ms": ms(started)})
                except Exception as error:  # noqa: BLE001
                    emit({**base_row, "cand": "kev", "error": str(error)[:200], "ms": ms(started)})
                for name, judge in judges.items():
                    started = time.perf_counter()
                    try:
                        payload = judge.complete_json(rel_prompt(stored, new), REL_SCHEMA)
                        emit({**base_row, "cand": name, "pred": payload.get("relation"), "ms": ms(started)})
                    except Exception as error:  # noqa: BLE001
                        emit({**base_row, "cand": name, "error": str(error)[:200], "ms": ms(started)})
                # Today's path: nomic thresholds, then the qwen judge's decide call.
                store = open_store(qwen)
                try:
                    seeded = store.add_fact(stored, source="user")
                    similarity = None
                    started = time.perf_counter()
                    event = place(store, judges["qwen"], qwen, Candidate(new, 5, False, (), "user"), source="user")
                    elapsed = ms(started)
                    a = qwen.embed_document(stored)
                    b = qwen.embed_document(new)
                    similarity = round(sum(x * y for x, y in zip(a, b, strict=True))
                                       / ((sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)), 3)
                    texts = [r.text for r in store.list_records(ListQuery(kind="fact"))]
                    emit({**base_row, "cand": "current_path", "pred": ACTION_TO_REL.get(event.action, event.action),
                          "action": event.action, "cos": similarity, "after": texts, "seed_id": seeded.id, "ms": elapsed})
                except Exception as error:  # noqa: BLE001
                    emit({**base_row, "cand": "current_path", "error": f"{type(error).__name__}: {error}"[:200]})
                finally:
                    store.close()
    finally:
        qwen.close()
        nemo.close()
        http.close()


# ---------- next-turn TTFT while a gate call runs ----------

REPLY = [{"role": "system", "content": "You are Ceti, a cheerful companion. Be brief."},
         {"role": "user", "content": "Tell me something nice about autumn."}]


def ttft(http: httpx.Client, base: str, model: str) -> int:
    body = {"model": model, "messages": REPLY, "temperature": 0.7, "max_tokens": 48, "stream": True,
            "reasoning_effort": "none"}
    started = time.perf_counter()
    with http.stream("POST", f"{base}/chat/completions", json=body) as response:
        first = -1
        for line in response.iter_lines():
            if first < 0 and line.startswith("data: ") and '"content":"' in line and '"content":""' not in line:
                first = ms(started)
    return first


def ttft_run(settings: Settings, base: str, rounds: int = 10) -> None:
    qwen, nemo = client(settings, base, QWEN), client(settings, base, NEMO)
    judges = {"qwen": JudgeAdapter(qwen), "nemotron": JudgeAdapter(nemo)}
    http = httpx.Client(timeout=60)
    kev_http = httpx.Client(timeout=30)
    line = "I just finished my first marathon yesterday!"

    def background(kind: str) -> None:
        if kind == "kev":
            kev(f"User: {line}", {"type": "noul", "instructions": GATE_Q}, kev_http)
        elif kind == "extract_qwen":
            store = open_store(qwen)
            try:
                learn(store, judges["qwen"], qwen, line, name="User", assistant="Ceti")
            finally:
                store.close()
        else:
            judges[kind].complete_json(f"{GATE_Q}\nUser: {line}", GATE_SCHEMA)

    try:
        ttft(http, base, QWEN)  # warm
        for kind in ("idle", "kev", "nemotron", "qwen", "extract_qwen"):
            for repeat in range(rounds):
                worker = None
                if kind != "idle":
                    worker = threading.Thread(target=background, args=(kind,))
                    worker.start()
                    time.sleep(0.02)
                first = ttft(http, base, QWEN)
                if worker:
                    worker.join()
                emit({"part": "ttft", "during": kind, "repeat": repeat, "ttft_ms": first})
                time.sleep(0.3)
    finally:
        qwen.close()
        nemo.close()
        http.close()
        kev_http.close()


def main() -> None:
    global OUT
    settings = Settings.load(Path(sys.argv[1]))
    base = llm_base_url(settings.llm_base_url)
    parts = sys.argv[3:] or ["gate", "dedupe", "ttft"]
    with open(sys.argv[2], "a", encoding="utf-8") as OUT:
        emit({"part": "meta", "ts": datetime.now().isoformat(), "base": base, "parts": parts,
              "judge_max_tokens": settings.judge_max_tokens})
        if "gate" in parts:
            gate(settings, base)
        if "dedupe" in parts:
            dedupe(settings, base)
        if "ttft" in parts:
            ttft_run(settings, base)


if __name__ == "__main__":
    main()
