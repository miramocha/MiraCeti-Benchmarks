"""Tool keyword bench (#154): does narrowing the tool list by keywords keep the line's tool, how much does it save,
and does the intent check still pick right on the smaller list?

Lines are intent_bench.all_lines(): the prompt-order cases plus the held-out cancel lines and near misses. Tools
are intent_bench.LIVE_TOOLS (the four Timer tools plus web_search and http_get). Four tool sets per line:
  full    every tool, as today
  narrow  cetimind.core.tool_filter.narrow: core tools plus keyword matches, full list when nothing matches
  strict  core tools plus keyword matches, never the full list
  expand  strict plus a model-visible more_tools option. When the check picks it, the check runs again on the
          full list, and that answer stands (the issue's expand step before the full list)

Offline pass (no model): recall (every expected tool is in the set), fallback rate (the full list is offered),
extra-tool rate (offered non-core tools the line does not need), list size, and estimated tokens of the intent tool
lines and the tool-round tools block. With --base-url it also counts real prompt tokens on the server and runs the
intent check, interleaved per line, on full, narrow, strict and expand with the live examples, and on full and
narrow with the examples stripped (bare). Expand's fallback rate is how often the check picked more_tools.

    uv run python bench/prompt_order/tool_keyword_bench.py --out DIR [--base-url http://HOST:PORT/v1] [--repeats 5]
Writes DIR/offline.jsonl, DIR/tokens.json, DIR/calls.jsonl (live only) and DIR/summary.json.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import os
import random
import statistics
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

if not os.environ.get("CETIMIND_DATA_DIR"):
    os.environ["CETIMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="cetimind-keywords-")
sys.path.insert(0, str(Path(__file__).parent))

import fake_tools  # noqa: E402
import heavy  # noqa: E402
import intent_bench  # noqa: E402
from intent_bench import CAPS, GROUPS, LIVE_TOOLS, MODEL, Line, all_lines, right  # noqa: E402

from cetimind.app.intent import _intent_data  # noqa: E402
from cetimind.app.router import FailedRoute, RouteTurn  # noqa: E402
from cetimind.core.calls import task_messages, text_tokens, wire_messages  # noqa: E402
from tool_filter import MORE_TOOLS, matched, narrow, norm  # noqa: E402
from tool_keywords import CORE_TOOLS, TOOL_KEYWORDS  # noqa: E402

from cetimind.core.instructions import INTENT_INSTRUCTION  # noqa: E402
from cetimind.core.tools import ToolSpec  # noqa: E402
from cetimind.llm.client import _function_tool  # noqa: E402

SETS = ("full", "narrow", "strict")
# The offered list and keywords. main() adds fake tools here for a scaling run (--fakes).
OFFERED: tuple[ToolSpec, ...] = LIVE_TOOLS
KEYWORDS: dict[str, tuple[str, ...]] = dict(TOOL_KEYWORDS)
LIVE_VARIANTS = ("full_live", "narrow_live", "strict_live", "expand_live", "full_bare", "narrow_bare")


class KeywordReuseError(Exception):
    """A keyword is a whole bench line, so the bench would measure copying."""


def check_keywords(lines: list[Line]) -> None:
    """Raise when a keyword is a whole bench line. Keywords are short, so this only catches a pasted line."""
    texts = {norm(" ".join(line.text.split())) for line in lines}
    for name, words in TOOL_KEYWORDS.items():
        for word in words:
            if norm(word) in texts:
                raise KeywordReuseError(f"{name} keyword is a bench line: {word!r}")


def _offered_matches(line: str, offered: tuple[ToolSpec, ...]) -> frozenset[str]:
    """Keyword matches that name a tool in offered."""
    return matched(line, KEYWORDS) & {spec.name for spec in offered}


def strict(line: str, offered: tuple[ToolSpec, ...]) -> tuple[ToolSpec, ...]:
    """Core tools plus keyword matches, with no fallback to the full list: CetiMind's narrow()."""
    return narrow(line, offered, keywords=KEYWORDS)


def fallback_narrow(line: str, offered: tuple[ToolSpec, ...]) -> tuple[ToolSpec, ...]:
    """The issue's first sketch: strict, but the full list when nothing beyond the core tools matches."""
    if not (_offered_matches(line, offered) - set(CORE_TOOLS)):
        return offered
    return strict(line, offered)


def tool_set(kind: str, line: str, offered: tuple[ToolSpec, ...]) -> tuple[ToolSpec, ...]:
    if kind == "full":
        return offered
    if kind == "narrow":
        return fallback_narrow(line, offered)
    return strict(line, offered)


def _bare(specs: tuple[ToolSpec, ...]) -> tuple[ToolSpec, ...]:
    return tuple(dataclasses.replace(spec, intent_examples=()) for spec in specs)


def _intent_tool_text(specs: tuple[ToolSpec, ...]) -> str:
    """The tool lines the intent prompt carries for specs."""
    return _intent_data(RouteTurn("", "", specs, False, None)).split("\n\n", 1)[0]


def _tools_json(specs: tuple[ToolSpec, ...]) -> str:
    return json.dumps([_function_tool(spec) for spec in specs], ensure_ascii=False)


def _extra(line: Line, names: set[str]) -> int:
    """Offered non-core tools the line does not need."""
    return len(names - set(CORE_TOOLS) - line.expect)


def offline_rows(lines: list[Line]) -> list[dict]:
    rows = []
    for line in lines:
        hits = _offered_matches(line.text, OFFERED)
        row = {
            "id": line.id,
            "lang": line.lang,
            "group": line.group,
            "need": line.need,
            "line": line.text,
            "expect": sorted(line.expect),
            "matched": sorted(hits),
        }
        for kind in SETS:
            specs = tool_set(kind, line.text, OFFERED)
            names = {spec.name for spec in specs}
            row[kind] = {
                "tools": [spec.name for spec in specs],
                "size": len(specs),
                "recall": line.expect <= names,
                "fallback": kind == "narrow" and not (hits - set(CORE_TOOLS)),
                "extra": _extra(line, names),
                "intent_est": text_tokens(_intent_tool_text(specs)),
                "block_est": text_tokens(_tools_json(specs)),
            }
        rows.append(row)
    return rows


def wilson(hits: int, total: int) -> dict:
    if total == 0:
        return {"hits": 0, "total": 0}
    z = 1.96
    p = hits / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return {
        "hits": hits,
        "total": total,
        "rate": round(p, 4),
        "lo": round(max(0.0, centre - half), 4),
        "hi": round(min(1.0, centre + half), 4),
    }


def offline_summary(rows: list[dict]) -> dict:
    out: dict = {}
    for kind in SETS:
        need_tool = [r for r in rows if r["expect"] and r["need"] != "either"]
        out[kind] = {
            "recall_tool_lines": wilson(sum(r[kind]["recall"] for r in need_tool), len(need_tool)),
            "recall_by_group": {
                g: wilson(
                    sum(r[kind]["recall"] for r in rows if r["group"] == g), sum(1 for r in rows if r["group"] == g)
                )
                for g in GROUPS
            },
            "mean_size": round(statistics.mean(r[kind]["size"] for r in rows), 3),
            "mean_intent_est": round(statistics.mean(r[kind]["intent_est"] for r in rows), 1),
            "mean_block_est": round(statistics.mean(r[kind]["block_est"] for r in rows), 1),
            "narrowed_lines": sum(1 for r in rows if r[kind]["size"] < len(OFFERED)),
            "fallback": wilson(sum(r[kind]["fallback"] for r in rows), len(rows)),
            "extra_per_line": round(statistics.mean(r[kind]["extra"] for r in rows), 3),
            "lines_with_extra": sum(1 for r in rows if r[kind]["extra"]),
            "misses": [r["id"] for r in need_tool if not r[kind]["recall"]],
        }
    out["lines"] = len(rows)
    out["matched_lines"] = sum(1 for r in rows if set(r["matched"]) - set(CORE_TOOLS))
    out["matched_on_no_tool_lines"] = [r["id"] for r in rows if not r["expect"] and r["matched"]]
    return out


def _real_tokens(client, messages: list[dict], tools: list[dict] | None = None) -> int:
    body: dict = {"model": MODEL, "messages": messages, "max_tokens": 1, "temperature": 0}
    if tools:
        body["tools"] = tools
    return client._post(f"{client._base}/chat/completions", body, 60.0, "count")["usage"]["prompt_tokens"]


def _count(client, messages: list[dict], tools: list[dict] | None = None) -> int | None:
    """Prompt tokens, or None when the server refuses the prompt (for example, past the context length)."""
    from cetimind.llm.client import LlmError

    try:
        return _real_tokens(client, messages, tools)
    except LlmError as error:
        print(json.dumps({"count_failed": str(error)[:200], "tools": len(tools or ())}), flush=True)
        return None


def _minus(value: int | None, base: int) -> int | None:
    return None if value is None else value - base


def _mean(values: list) -> float | None:
    """The mean, or None when any value is missing, so a refused prompt is never averaged away."""
    return None if any(v is None for v in values) else round(statistics.mean(values), 1)


def real_tokens(client, rows: list[dict]) -> dict:
    """Server prompt tokens per distinct tool set: the intent prompt with an empty line, and the tools block on a
    one-word chat, less the same chat with no tools."""
    sets = {tuple(r[kind]["tools"]) for r in rows for kind in SETS}
    by_name = {spec.name: spec for spec in OFFERED}
    base_msgs = [{"role": "user", "content": "hi"}]
    base = _real_tokens(client, base_msgs)
    table = {}
    for names in sorted(sets, key=len):
        specs = tuple(by_name[n] for n in names)
        intent_msgs = wire_messages(
            task_messages(INTENT_INSTRUCTION, _intent_data(RouteTurn("hi", "", specs, False, None)))
        )
        table[",".join(names)] = {
            "size": len(names),
            "intent_prompt": _count(client, list(intent_msgs)),
            "tools_block": _minus(_count(client, base_msgs, [_function_tool(s) for s in specs]), base),
        }
    per_line = {
        kind: {
            "intent_prompt": _mean([table[",".join(r[kind]["tools"])]["intent_prompt"] for r in rows]),
            "tools_block": _mean([table[",".join(r[kind]["tools"])]["tools_block"] for r in rows]),
        }
        for kind in SETS
    }
    return {"by_set": table, "mean_per_line": per_line}


def mcnemar(rows: list[dict], a: str, b: str, group: str | None = None) -> dict:
    """Exact two-sided McNemar on paired (line, repeat) right results, a against b."""
    by: dict = defaultdict(dict)
    for r in rows:
        if r["failed"] or (group and r["group"] != group):
            continue
        by[(r["id"], r["repeat"])][r["variant"]] = r["right"]
    a_only = sum(1 for v in by.values() if v.get(a) is True and v.get(b) is False)
    b_only = sum(1 for v in by.values() if v.get(a) is False and v.get(b) is True)
    n = a_only + b_only
    k = min(a_only, b_only)
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)
    return {f"{a}_only": a_only, f"{b}_only": b_only, "p": round(p, 4)}


def live_summary(rows: list[dict]) -> dict:
    table = {
        v: {
            g: wilson(
                sum(r["right"] for r in rows if r["variant"] == v and r["group"] == g and not r["failed"]),
                sum(1 for r in rows if r["variant"] == v and r["group"] == g and not r["failed"]),
            )
            for g in (*GROUPS, "all")
        }
        for v in LIVE_VARIANTS
    }
    for v in LIVE_VARIANTS:
        ok = [r for r in rows if r["variant"] == v and not r["failed"]]
        table[v]["all"] = wilson(sum(r["right"] for r in ok), len(ok))
    medians = {v: round(statistics.median(r["ms"] for r in rows if r["variant"] == v), 1) for v in LIVE_VARIANTS}
    failures = {v: sum(1 for r in rows if r["variant"] == v and r["failed"]) for v in LIVE_VARIANTS}
    alarms = {
        v: sum(1 for r in rows if r["variant"] == v and r["group"] == "near_miss" and not r["failed"] and r["picked"])
        for v in LIVE_VARIANTS
    }
    strays = {v: sum(1 for r in rows if r["variant"] == v and intent_bench._stray(r)) for v in LIVE_VARIANTS}
    expand = [r for r in rows if r["variant"] == "expand_live"]
    expanded = {
        "rate": wilson(sum(r["expanded"] for r in expand), len(expand)),
        "by_group": {
            g: wilson(sum(r["expanded"] for r in expand if r["group"] == g), sum(1 for r in expand if r["group"] == g))
            for g in GROUPS
        },
    }
    cat = [r for r in rows if r["variant"] == "cat_live"]
    cat_summary = {
        "rate": wilson(sum(r["expanded"] for r in cat), len(cat)),
        "picked": dict(Counter(g for r in cat for g in r.get("categories", ()))),
        "by_group": {
            g: wilson(sum(r["expanded"] for r in cat if r["group"] == g), sum(1 for r in cat if r["group"] == g))
            for g in GROUPS
        },
    }
    intent_est = {
        v: round(statistics.mean(r["intent_est"] for r in rows if r["variant"] == v), 1)
        for v in LIVE_VARIANTS
        if any("intent_est" in r for r in rows if r["variant"] == v)
    }
    pairs = {
        f"{a}_vs_{b}": {g: mcnemar(rows, a, b, None if g == "all" else g) for g in (*GROUPS, "all")}
        for a, b in (
            ("narrow_live", "full_live"),
            ("strict_live", "full_live"),
            ("expand_live", "full_live"),
            ("cat_live", "full_live"),
            ("cat_live", "strict_live"),
            ("cat_live", "expand_live"),
            ("narrow_bare", "full_bare"),
        )
        if a in LIVE_VARIANTS and b in LIVE_VARIANTS
    }
    return {
        "groups": table,
        "median_ms": medians,
        "failures": failures,
        "near_miss_alarms": alarms,
        "stray_lines": strays,
        "expand_fallback": expanded,
        "category_picks": cat_summary,
        "first_pass_intent_tokens_est": intent_est,
        "mcnemar": pairs,
    }


# The cat variant: strict narrowing plus one line per category whose tools narrowing dropped. Picking a category
# reruns the check with that category's tools added. The Timer tools are core, so they never form a category.
REAL_CATEGORIES: dict[str, str] = {
    "web": "Search the web and read web pages: news, prices, weather, scores, and anything live or at a URL.",
}
CATEGORY_PREFIX = "category_"


def _group_of(spec: ToolSpec) -> str:
    return fake_tools.FAKE_GROUP.get(spec.name, spec.group)


def _category_spec(group: str) -> ToolSpec:
    text = REAL_CATEGORIES.get(group) or fake_tools.FAKE_CATEGORIES[group][0]
    return ToolSpec(
        name=f"{CATEGORY_PREFIX}{group}",
        description=f"A category of more tools: {text} Pick it to see them.",
        parameters={"type": "object", "properties": {}},
    )


def category_set(line: str, offered: tuple[ToolSpec, ...]) -> tuple[ToolSpec, ...]:
    """Strict narrowing, then one category line for each group with a dropped tool, in first-seen order."""
    kept = strict(line, offered)
    names = {spec.name for spec in kept}
    groups: list[str] = []
    for spec in offered:
        group = _group_of(spec)
        if spec.name not in names and group not in groups:
            groups.append(group)
    return (*kept, *(_category_spec(group) for group in groups))


def _expand_categories(listed: tuple[ToolSpec, ...], picked: set[str]) -> tuple[ToolSpec, ...]:
    """The listed real tools plus every offered tool in a picked category, in offered order."""
    groups = {name[len(CATEGORY_PREFIX) :] for name in picked if name.startswith(CATEGORY_PREFIX)}
    keep = {spec.name for spec in listed if not spec.name.startswith(CATEGORY_PREFIX)}
    return tuple(spec for spec in OFFERED if spec.name in keep or _group_of(spec) in groups)


def run_live(client, lines: list[Line], out: Path, repeats: int, seed: int) -> list[dict]:
    from cetimind.app.intent import IntentRouter

    router = IntentRouter(client)
    last = {lang: heavy.HISTORY[lang][-1][1] for lang in ("en", "ja")}
    client.chat([{"role": "user", "content": "hi"}], think=False)
    started = time.perf_counter()
    rows: list[dict] = []
    with (out / "calls.jsonl").open("w", encoding="utf-8") as handle:
        for repeat in range(repeats):
            rng = random.Random(seed + repeat)
            for line in lines:
                order = list(LIVE_VARIANTS)
                rng.shuffle(order)
                for name in order:
                    kind, examples = name.split("_")
                    if kind == "cat":
                        specs = category_set(line.text, OFFERED)
                    else:
                        specs = tool_set("strict" if kind == "expand" else kind, line.text, OFFERED)
                    if kind == "expand":
                        specs = (*specs, MORE_TOOLS)
                    if examples == "bare":
                        specs = _bare(specs)
                    turn = RouteTurn(line.text, last[line.lang], specs, False, None)
                    t0 = time.perf_counter()
                    chosen = router.decide(turn)
                    first = set() if isinstance(chosen, FailedRoute) else {spec.name for spec in chosen}
                    categories = sorted(n[len(CATEGORY_PREFIX) :] for n in first if n.startswith(CATEGORY_PREFIX))
                    expanded = (kind == "expand" and MORE_TOOLS.name in first) or (kind == "cat" and bool(categories))
                    second: tuple[ToolSpec, ...] = ()
                    if expanded and kind == "expand":
                        second = OFFERED
                    elif expanded:
                        second = _expand_categories(specs, first)
                    if expanded:
                        chosen = router.decide(dataclasses.replace(turn, tools=second))
                    ms = (time.perf_counter() - t0) * 1000
                    failed = isinstance(chosen, FailedRoute)
                    picked = None if failed else {spec.name for spec in chosen}
                    row = {
                        "variant": name,
                        "repeat": repeat,
                        "id": line.id,
                        "lang": line.lang,
                        "line": line.text,
                        "group": line.group,
                        "need": line.need,
                        "expect": sorted(line.expect),
                        "offered": [s.name for s in specs],
                        "picked": None if picked is None else sorted(picked),
                        "expanded": expanded,
                        "categories": categories,
                        "second_offered": [s.name for s in second],
                        "intent_est": text_tokens(_intent_tool_text(specs)),
                        "failed": failed,
                        "right": right(line, picked),
                        "ms": round(ms, 1),
                    }
                    rows.append(row)
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    handle.flush()
            print(json.dumps({"repeat": repeat, "elapsed_s": round(time.perf_counter() - started)}), flush=True)
    return rows


def main() -> None:
    global OFFERED, LIVE_VARIANTS
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261126)
    parser.add_argument("--fakes", type=int, default=0, help="fake tools added after the real ones")
    parser.add_argument("--variants", default=",".join(LIVE_VARIANTS), help="comma-separated live variants")
    args = parser.parse_args()
    if args.fakes:
        OFFERED = (*LIVE_TOOLS, *fake_tools.fake_tools(args.fakes))
        KEYWORDS.update({spec.name: fake_tools.FAKE_KEYWORDS[spec.name] for spec in OFFERED[len(LIVE_TOOLS) :]})
    LIVE_VARIANTS = tuple(name for name in args.variants.split(",") if name)
    sys.stdout.reconfigure(encoding="utf-8")
    lines = all_lines()
    try:
        intent_bench.check_wording(lines)
        check_keywords(lines)
    except (intent_bench.ExampleReuseError, KeywordReuseError) as error:
        sys.exit(str(error))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = offline_rows(lines)
    with (out / "offline.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary: dict = {"tools": len(OFFERED), "fakes": args.fakes, "offline": offline_summary(rows)}
    if args.base_url:
        from cetimind.llm.client import LlmClient

        client = LlmClient(args.base_url, MODEL, "unused", max_tokens=2048, capabilities=CAPS)
        try:
            tokens = real_tokens(client, rows)
            (out / "tokens.json").write_text(json.dumps(tokens, indent=2), encoding="utf-8")
            summary["tokens"] = tokens
            summary["live"] = live_summary(run_live(client, lines, out, args.repeats, args.seed))
        finally:
            client.close()
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
