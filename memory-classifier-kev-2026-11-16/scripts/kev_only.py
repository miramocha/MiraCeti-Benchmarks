"""Kev-only rerun (e.g. Kev on CPU via KEV_URL): gate + dedupe accuracy and latency, then qwen TTFT idle vs during Kev."""

import json
import sys
import threading
import time
from pathlib import Path

import bench
from bench import GATE_Q, REL_CRITERIA, REL_Q, httpx, kev, ms, ttft
from cases import GATE_EN, GATE_JA, PAIRS_EN, PAIRS_JA
from cetimind.app.settings import Settings
from cetimind.config import llm_base_url

label = sys.argv[3]
settings = Settings.load(Path(sys.argv[1]))
base = llm_base_url(settings.llm_base_url)
http = httpx.Client(timeout=60)
with open(sys.argv[2], "a", encoding="utf-8") as bench.OUT:
    emit = bench.emit
    emit({"part": "meta", "kev_url": bench.KEV, "label": label})
    kev(f"User: hi", {"type": "noul", "instructions": GATE_Q}, http)  # warm
    for lang, cases in (("en", GATE_EN), ("ja", GATE_JA)):
        for index, (line, lab) in enumerate(cases):
            started = time.perf_counter()
            p = kev(f"User: {line}", {"type": "noul", "instructions": GATE_Q}, http)["noul"]
            emit({"part": "gate", "lang": lang, "case": index, "line": line, "label": lab, "cand": "kev",
                  "repeat": 0, "p": p, "pred": p >= 0.5, "ms": ms(started)})
    for lang, cases in (("en", PAIRS_EN), ("ja", PAIRS_JA)):
        for index, (stored, new, lab) in enumerate(cases):
            started = time.perf_counter()
            answer = kev(f"Stored fact: {stored}\nNew fact: {new}",
                         {"type": "choice", "instructions": REL_Q, "criteria": REL_CRITERIA}, http)
            emit({"part": "dedupe", "lang": lang, "case": index, "stored": stored, "new": new, "label": lab,
                  "cand": "kev", "pred": answer.get("choice"), "raw": answer, "ms": ms(started)})
    llm = httpx.Client(timeout=60)
    ttft(llm, base, bench.QWEN)
    for kind in ("idle", "kev"):
        for repeat in range(10):
            worker = None
            if kind == "kev":
                worker = threading.Thread(
                    target=kev, args=("User: I just finished my first marathon yesterday!",
                                      {"type": "noul", "instructions": GATE_Q}, http))
                worker.start()
                time.sleep(0.02)
            first = ttft(llm, base, bench.QWEN)
            if worker:
                worker.join()
            emit({"part": "ttft", "during": kind, "repeat": repeat, "ttft_ms": first})
            time.sleep(0.3)
