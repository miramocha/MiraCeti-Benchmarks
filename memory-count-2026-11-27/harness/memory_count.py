"""Memories per turn by language on the heavy profile, with no chat model (#141 step 1).

For each heavy case this builds the same prompt arm B builds, with CetiMind's own _load, and logs how many memories
the lookup returned, how many reached the prompt, and the real token count of the memory lines. It also reruns the
search with no relevance floor, so the log shows where the other candidates fell, and records which words of the
line FTS can match.

Run from a CetiMind checkout:
    uv run python bench/prompt_order/memory_count.py --base-url http://HOST:PORT/v1 --out DIR
Writes DIR/memory-count.jsonl (one row per case).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import bench
from bench import NOW, USER_NAME, _open, _options, seed_templates

from cetimind.app.turn import _context_query, _history, _load, _safe, _schedule_lines
from cetimind.config import SCORING
from cetimind.core.calls import text_tokens
from cetimind.core.persona import Persona
from cetimind.core.prompt import MEMORIES_TITLE
from cetimind.memory.guard import strip_placeholders
from cetimind.memory.retrieve import RECALL_KINDS, fts_query, search


def _memory_lines(content: str) -> list[str]:
    """The memory lines in the new message, after the Memories title and before the next blank line."""
    head = f"{MEMORIES_TITLE}\n"
    if head not in content:
        return []
    block = content.split(head, 1)[1].split("\n\n", 1)[0]
    return [line[2:] for line in block.split("\n") if line.startswith("- ")]


def _real_tokens(chat, text: str, empty: int) -> int:
    """Prompt tokens the model counts for text, less the chat template's own tokens."""
    if not text:
        return 0
    body = {"model": bench.MODEL, "messages": [{"role": "user", "content": text}], "max_tokens": 1,
            "temperature": 0}
    return chat._post(f"{chat._base}/chat/completions", body, 60.0, "count")["usage"]["prompt_tokens"] - empty


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    bench.PROFILE = bench.PROFILES["heavy"]
    persona = Persona.from_mapping(bench.PROFILE["persona"])
    chat = bench._client(args.base_url)
    work = Path(tempfile.mkdtemp(prefix="memory-count-"))
    templates = seed_templates(work, chat)
    empty = _real_tokens(chat, ".", 0) - 1
    open_floor = replace(SCORING, relevance_floor=0.0)
    with (out / "memory-count.jsonl").open("w", encoding="utf-8") as rows:
        for case in bench.PROFILE["cases"]():
            path = work / f"count-{case.id}.db"
            shutil.copy(templates[case.lang], path)
            store = _open(path, chat)
            try:
                ran: list[str] = []
                options = _options(store, chat, case, ran, chat, routed=False)
                safe, removed = _safe(case.line)
                history = _history(store)
                messages, retrieved, _ = _load(
                    store, persona, safe, removed=removed != "", user_name=USER_NAME, now=NOW, history=history,
                    tool_notes=options.tool_notes, network=any(spec.network for spec in options.tools),
                    schedule=_schedule_lines(options), interests=persona.interests,
                )
                query = strip_placeholders(safe).strip()
                every = search(store, _context_query(query, history), exclude_pinned=True, keywords=query,
                               kinds=RECALL_KINDS, limit=SCORING.vector_k + SCORING.fts_k, scoring=open_floor)
                shown = _memory_lines(messages[-1].content)
                row = {
                    "case": case.id,
                    "lang": case.lang,
                    "line": case.line,
                    "fts_words": fts_query(query),
                    "retrieved": len(retrieved),
                    "in_prompt": len(shown),
                    "memory_chars": sum(len(line) for line in shown),
                    "memory_estimate": sum(text_tokens(line) for line in shown),
                    "memory_tokens": _real_tokens(chat, "\n".join(f"- {line}" for line in shown), empty),
                    "top_relevance": [round(item.relevance, 3) for item in every[:8]],
                    "over_floor": sum(item.relevance >= SCORING.relevance_floor for item in every),
                    "prompt_estimate": sum(text_tokens(message.content) for message in messages),
                }
            finally:
                store.close()
            rows.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows.flush()
            print(json.dumps({k: row[k] for k in ("case", "retrieved", "in_prompt", "memory_tokens", "over_floor",
                                                 "top_relevance")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
