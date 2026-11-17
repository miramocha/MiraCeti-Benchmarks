"""Experiment 11: how much of the prompt LM Studio re-reads per turn, by prompt layout and tool set.

Simulates 8 consecutive turns of one conversation per variant, with realistic context: pinned facts, a profile,
a summary, 6 memories that change every turn, a clock that moves 2 minutes per turn, and a history that grows
by one exchange per turn. Each request streams with max_tokens 1 and thinking off, so time to first token is
mostly prompt reading. LM Studio reports no cached-token count, so time to first token is the signal.

Variants:
  A  today's layout: build_prompt (clock and memories in the system message), all 8 tools every turn
  B  stable layout: system = persona, pinned, profile, summary; clock and memories go in front of the user line
  C  B, with the tool set changing per turn as CetiMind #50 would (none, all, schedule only, none, web only, ...)
  D  B, no tools at all
  E  B with all tools, plus a different thinking-off intent-check request before every turn
Writes cacheprobe.jsonl.
"""
import json, pathlib, random, sys, time
from datetime import datetime, timedelta
import httpx2
from cetimind.app.persona import load_persona
from cetimind.app.settings import Settings
from cetimind.app.tools.schedule import user_tools
from cetimind.core.model import ChatMessage
from cetimind.core.prompt import PromptContext, build_prompt, format_now
from cetimind.core.tools import ToolSpec
from cetimind.llm.client import _function_tool

URL = "http://localhost:1234/v1/chat/completions"
HERE = pathlib.Path(__file__).parent
s = Settings.load(); persona = load_persona(saved=s.persona)
http = httpx2.Client(timeout=300)
random.seed(7)

STUBS = (
    ToolSpec("web_search", "Search the web for current or outside information. Returns titles, links, and snippets.",
             {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False}),
    ToolSpec("http_get", "Fetch one web page by URL and return its text.",
             {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"], "additionalProperties": False}),
    ToolSpec("list_add", "Add an item to one of the user's lists, such as shopping or todo.",
             {"type": "object", "properties": {"list": {"type": "string"}, "item": {"type": "string"}},
              "required": ["list", "item"], "additionalProperties": False}),
    ToolSpec("list_show", "Show the items on one of the user's lists.",
             {"type": "object", "properties": {"list": {"type": "string"}}, "required": ["list"], "additionalProperties": False}),
)
ALL = (*user_tools(), *STUBS)
BY_NAME = {t.name: t for t in ALL}
TOOLSETS_C = [[], [t.name for t in ALL], ["schedule_create", "schedule_list", "schedule_cancel"], [],
              ["web_search"], [t.name for t in ALL], ["list_add"], []]

# The invented context (pinned facts, profile, summary, a pool of 24 memories, 8 user lines) is left out of
# the published copy because it mentions the user by name. Sizes: 5 pinned facts, a profile of about 60 words,
# a summary of about 60 words, 24 one-sentence memories, and 8 short chat lines (2 of them ask for a tool).
PINNED = [...]
PROFILE = "..."
SUMMARY = "..."
MEMORY_POOL = [...]
LINES = [...]
REPLY = "Got it, senpai. " + "I'm here, so keep going and tell me how it goes. " * 3
HISTORY0 = []
for i in range(4):
    HISTORY0 += [ChatMessage("user", f"earlier message {i}: I was working on the stream overlay and it kept flickering."),
                 ChatMessage("assistant", f"Earlier reply {i}: try turning off vsync on the browser source, senpai.")]
INTENT_PROMPT = ("Which tools does the user's last message need? Choose an empty list when a normal reply is enough.\n"
                 "Tools:\n" + "\n".join(f"- {t.name}: {t.description}" for t in ALL))


def layout_a(line, history, memories, now):
    built = build_prompt(persona, line, PromptContext(pinned=tuple(PINNED), profile=PROFILE, memories=tuple(memories),
                                                       summary=SUMMARY, history=tuple(history), user_name="User", now=now))
    return [{"role": m.role, "content": m.content} for m in built]


def layout_b(line, history, memories, now):
    """The system message holds only what rarely changes. The clock and memories ride on the newest user line."""
    built = build_prompt(persona, line, PromptContext(pinned=tuple(PINNED), profile=PROFILE, memories=(),
                                                       summary=SUMMARY, history=tuple(history), user_name="User", now=None))
    out = [{"role": m.role, "content": m.content} for m in built]
    context = f"[Now: {format_now(now)}]\n[Memories:\n" + "\n".join(f"- {m}" for m in memories) + "]\n\n"
    out[-1]["content"] = context + out[-1]["content"]
    return out


def first_token(messages, tools):
    body = {"model": s.chat_model, "messages": messages, "temperature": 0, "max_tokens": 1, "reasoning_effort": "none",
            "stream": True, "stream_options": {"include_usage": True}}
    if tools:
        body["tools"] = [_function_tool(BY_NAME[n]) for n in tools]
    started = time.perf_counter(); first = None; usage = {}
    with http.stream("POST", URL, json=body) as response:
        for raw in response.iter_lines():
            if not raw.startswith("data: ") or raw == "data: [DONE]":
                continue
            data = json.loads(raw[6:])
            usage = data.get("usage") or usage
            choices = data.get("choices") or []
            if first is None and choices:
                delta = choices[0].get("delta") or {}
                if delta.get("content") or delta.get("reasoning_content") or delta.get("tool_calls"):
                    first = time.perf_counter() - started
    total = time.perf_counter() - started
    return round((first if first is not None else total) * 1000), usage.get("prompt_tokens")


def intent_check(line):
    body = {"model": s.chat_model, "temperature": 0, "max_tokens": 30, "reasoning_effort": "none",
            "messages": [{"role": "user", "content": f"{INTENT_PROMPT}\n\nConversation:\nUser: {line}"}]}
    started = time.perf_counter()
    http.post(URL, json=body)
    return round((time.perf_counter() - started) * 1000)


VARIANTS = {
    "A_today": (layout_a, lambda i: [t.name for t in ALL], False),
    "B_stable": (layout_b, lambda i: [t.name for t in ALL], False),
    "C_stable_toolsets": (layout_b, lambda i: TOOLSETS_C[i], False),
    "D_stable_no_tools": (layout_b, lambda i: [], False),
    "E_stable_with_intent_call": (layout_b, lambda i: [t.name for t in ALL], True),
}
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
out = (HERE / "cacheprobe.jsonl").open("w", encoding="utf-8")
start = datetime.now().astimezone()
summary: dict[str, list[int]] = {}
for round_no in range(ROUNDS):
    order = list(VARIANTS)
    random.shuffle(order)
    for name in order:
        build, toolset, with_intent = VARIANTS[name]
        # A fresh opening per variant and round, so no earlier run's cache matches the start.
        tag = f"[conversation {name} {round_no}]"
        history = [ChatMessage("user", f"{tag} hi"), ChatMessage("assistant", "Hi senpai.")] + list(HISTORY0)
        for i, line in enumerate(LINES):
            now = start + timedelta(minutes=2 * i + 30 * round_no)
            memories = random.sample(MEMORY_POOL, 6)
            intent_ms = intent_check(line) if with_intent else None
            ms, prompt_tokens = first_token(build(line, history, memories, now), toolset(i))
            out.write(json.dumps({"variant": name, "round": round_no, "turn": i, "ttft_ms": ms, "prompt_tokens": prompt_tokens,
                                  "tools": toolset(i), "intent_ms": intent_ms}) + "\n"); out.flush()
            print(f"{name:26} r{round_no} t{i} ttft {ms:5} ms  prompt {prompt_tokens}  tools {len(toolset(i))}"
                  + (f"  intent {intent_ms} ms" if intent_ms else ""), flush=True)
            if i > 0:
                summary.setdefault(name, []).append(ms)
            history += [ChatMessage("user", line), ChatMessage("assistant", REPLY)]

print("\nvariant                    | median ttft, turns 2-8 | mean")
for name, values in summary.items():
    ordered = sorted(values)
    print(f"{name:26} | {ordered[len(ordered) // 2]:5} ms | {sum(values) / len(values):.0f} ms")
