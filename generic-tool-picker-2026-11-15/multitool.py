"""Experiment 8: stub tools next to the schedule tools.

A. A generic intent check that picks tools by name from the tool list, with and without per-tool examples.
B. Whether thinking off also stops calls to the stub tools.

Stubs are never run: only the first reply's tool_calls are read. Writes multitool-A.jsonl and multitool-B.jsonl.
"""
import json, pathlib, sys, time
from datetime import datetime
import httpx2
from cetimind.app.persona import load_persona
from cetimind.app.settings import Settings
from cetimind.app.tools.schedule import user_tools
from cetimind.core.prompt import PromptContext, build_prompt
from cetimind.core.tools import ToolSpec
from cetimind.llm.client import _function_tool

URL = "http://localhost:1234/v1/chat/completions"
HERE = pathlib.Path(__file__).parent
s = Settings.load(); persona = load_persona(saved=s.persona)
http = httpx2.Client(timeout=300)

STUBS = (
    ToolSpec("web_search", "Search the web for current or outside information. Returns titles, links, and snippets.",
             {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False}),
    ToolSpec("http_get", "Fetch one web page by URL and return its text.",
             {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"], "additionalProperties": False}),
    ToolSpec("list_add", "Add an item to one of the user's lists, such as shopping or todo.",
             {"type": "object", "properties": {"list": {"type": "string"}, "item": {"type": "string"}},
              "required": ["list", "item"], "additionalProperties": False}, writes=True),
    ToolSpec("list_show", "Show the items on one of the user's lists.",
             {"type": "object", "properties": {"list": {"type": "string"}}, "required": ["list"], "additionalProperties": False}),
)
TOOLS = (*user_tools(), *STUBS)
NAMES = [t.name for t in TOOLS]
EXAMPLES = {  # per-tool example lines for variant json_ex. None is a test line.
    "current_time": ["what's the time in my timezone right now"],
    "schedule_create": ["remind me to take my pills in 15 minutes", "every night at 11 tell me to sleep"],
    "schedule_list": ["which reminders are coming up"],
    "schedule_cancel": ["cancel the pills reminder"],
    "web_search": ["look up the newest pokemon game", "who won the match last night"],
    "http_get": ["read https://example.org/post and tell me what it says"],
    "list_add": ["put eggs on my shopping list", "add 'call bank' to my todo"],
    "list_show": ["what's on my todo list"],
}
S = ["schedule_create", "schedule_list", "schedule_cancel"]

# (needed tools, line, last assistant reply). An empty set means a normal reply is enough.
# current_time is never required, because the prompt has a clock line, and choosing it is not counted as wrong.
CASES = [
    ({"schedule_create"}, "remind me to drink water in 20 minutes", None),
    ({"schedule_create"}, "every day at 8am tell me to stretch", None),
    ({"schedule_create"}, "don't let me forget to submit the form by 5pm", None),
    ({"schedule_create"}, "in 45 minutes ask me if I finished the essay", None),
    ({"schedule_create"}, "remind me to buy milk when I leave work at 6", None),
    ({"schedule_list"}, "what reminders do I have?", None),
    ({"schedule_cancel"}, "cancel the laundry reminder", None),
    ({"schedule_create"}, "yes please", "Want me to remind you before your exam?"),
    ({"web_search"}, "what's the latest news about the nintendo switch 2?", None),
    ({"web_search"}, "search for the best ramen places in osaka", None),
    ({"web_search"}, "what's the weather in tokyo today?", None),
    ({"web_search"}, "look up when the next elden ring dlc comes out", None),
    ({"web_search"}, "find me a good recipe for chicken curry", None),
    ({"web_search"}, "who is the current prime minister of japan?", None),
    ({"web_search"}, "is the steam summer sale on right now?", None),
    ({"web_search"}, "google how to fix error 0x80070005 on windows", None),
    ({"http_get"}, "what does https://example.com say?", None),
    ({"http_get"}, "summarize this page for me https://example.org/blog/post-12", None),
    ({"http_get"}, "can you read https://news.example.net/today and tell me the headlines", None),
    ({"http_get"}, "open this link https://example.com/recipe", None),
    ({"http_get"}, "check what's on https://docs.example.dev/install", None),
    ({"list_add"}, "add milk to my shopping list", None),
    ({"list_add"}, "put 'finish the slides' on my todo list", None),
    ({"list_add"}, "we're out of rice, add it to the groceries", None),
    ({"list_add"}, "can you note down 'buy a birthday gift' in my todos", None),
    ({"list_show"}, "what's on my shopping list?", None),
    ({"list_show"}, "show me my todo list", None),
    ({"list_show"}, "what did I need to buy again?", None),
    ({"schedule_create", "list_add"}, "add dentist to my todo and remind me about it tomorrow at 9", None),
    ({"web_search", "schedule_create"}, "check when the store closes today and remind me an hour before", None),
    (set(), "what time is it?", None),
    (set(), "i remember you said you like tea", None),
    (set(), "tell me about your day", None),
    (set(), "can you remind me what we talked about?", None),
    (set(), "hi ceti!", None),
    (set(), "what's 17*23?", None),
    (set(), "i have a dentist appointment tomorrow at 3", None),
    (set(), "every day at 8am I go for a run", None),
    (set(), "i already searched for it, no luck", None),
    (set(), "i googled you lol", None),
    (set(), "my shopping list is so long this week", None),
    (set(), "that website was so slow yesterday", None),
    (set(), "tell me about osaka", None),
    (set(), "what's your favorite food?", None),
    (set(), "i added you to my list of favorite people", None),
    (set(), "how do I make rice in a pot?", None),
    (set(), "i'll check the news later", None),
    (set(), "what's the capital of france?", None),
    (set(), "no thanks", "Want me to remind you before your exam?"),
    (set(), "thanks!", "Done, I added milk to your shopping list."),
]
OPTIONAL = {"current_time"}


def tool_lines(with_examples):
    lines = []
    for t in TOOLS:
        line = f"- {t.name}: {t.description}"
        if with_examples and t.name in EXAMPLES:
            line += " Examples: " + "; ".join(f'"{e}"' for e in EXAMPLES[t.name])
        lines.append(line)
    return "\n".join(lines)


def conversation(line, reply):
    return f"Assistant: {reply}\nUser: {line}" if reply else f"User: {line}"


SCHEMA = {"type": "object", "properties": {"tools": {"type": "array", "items": {"type": "string", "enum": NAMES}}},
          "required": ["tools"], "additionalProperties": False}


def pick(line, reply, with_examples):
    prompt = ("Which tools does the user's last message need? Choose an empty list when a normal reply is enough. "
              "A tool is needed only when the user asks for something the tool does, not when they just mention the topic. "
              "The current time is already known.\n"
              f"Tools:\n{tool_lines(with_examples)}\n\nConversation:\n{conversation(line, reply)}")
    body = {"model": s.chat_model, "temperature": 0, "max_tokens": 200, "reasoning_effort": "none",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "result", "schema": SCHEMA, "strict": True}}}
    started = time.perf_counter()
    content = http.post(URL, json=body).json()["choices"][0]["message"]["content"]
    return set(json.loads(content)["tools"]), round((time.perf_counter() - started) * 1000)


def part_a():
    out = (HERE / "multitool-A.jsonl").open("w", encoding="utf-8")
    for variant, with_examples in (("json_desc", False), ("json_ex", True)):
        miss = false = wrong = extra = 0
        times = []
        for need, line, reply in CASES:
            chosen, ms = pick(line, reply, with_examples)
            times.append(ms)
            real = chosen - OPTIONAL
            is_miss = bool(need) and not real                 # a tool turn routed to no tools
            is_false = not need and bool(real)                # a normal line routed to tools
            is_wrong = bool(need) and bool(real) and not need <= real  # tool turn, but a needed tool is missing
            is_extra = bool(need) and need <= real and real != need    # all needed tools, plus others
            miss += is_miss; false += is_false; wrong += is_wrong; extra += is_extra
            out.write(json.dumps({"variant": variant, "need": sorted(need), "chosen": sorted(chosen), "line": line,
                                  "reply": reply, "ms": ms}) + "\n")
            flag = "MISS" if is_miss else "FALSE" if is_false else "WRONG" if is_wrong else "extra" if is_extra else "ok"
            if flag != "ok":
                print(f"   {flag:5} need={sorted(need)} chose={sorted(chosen)}  {line}", flush=True)
        tool_turns = sum(1 for n, _, _ in CASES if n)
        print(f"{variant}: tool turns {tool_turns}, misses {miss}, missing a needed tool {wrong}, extra tools {extra}; "
              f"normal lines {len(CASES) - tool_turns}, false alarms {false}; median {sorted(times)[len(times) // 2]} ms\n",
              flush=True)


B_LINES = [("web_search", "what's the latest news about the nintendo switch 2?"),
           ("web_search", "search for the best ramen places in osaka"),
           ("http_get", "what does https://example.com say?"),
           ("http_get", "summarize this page for me https://example.org/blog/post-12"),
           ("list_add", "add milk to my shopping list"),
           ("list_show", "show me my todo list")]


def part_b(reps):
    wire = [_function_tool(t) for t in TOOLS]
    out = (HERE / "multitool-B.jsonl").open("w", encoding="utf-8")
    for effort in ("none", "low"):
        hits = runs = 0
        times = []
        for want, line in B_LINES:
            for rep in range(reps):
                built = build_prompt(persona, line, PromptContext(user_name=s.user_name or "User", now=datetime.now().astimezone()))
                body = {"model": s.chat_model, "messages": [{"role": m.role, "content": m.content} for m in built],
                        "temperature": s.chat_temperature, "max_tokens": s.chat_max_tokens, "tools": wire,
                        "reasoning_effort": effort}
                started = time.perf_counter()
                data = http.post(URL, json=body).json()
                ms = round((time.perf_counter() - started) * 1000)
                message = data["choices"][0]["message"]
                called = [c["function"]["name"] for c in message.get("tool_calls") or []]
                args = [c["function"]["arguments"] for c in message.get("tool_calls") or []]
                reasoning = ((data.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens")
                ok = want in called
                hits += ok; runs += 1; times.append(ms)
                out.write(json.dumps({"effort": effort, "want": want, "line": line, "rep": rep, "called": called, "args": args,
                                      "reasoning_tokens": reasoning, "ms": ms,
                                      "content": (message.get("content") or "")[:200]}) + "\n")
                detail = args if called else repr((message.get("content") or "")[:70])
                print(f"   {'ok  ' if ok else 'MISS'} {effort:4} {ms:6}ms r={reasoning} {line!r} -> {called} {detail}", flush=True)
        print(f"thinking {effort}: {hits}/{runs} called the right tool, avg {sum(times) / len(times):.0f} ms\n", flush=True)


if "a" in sys.argv[1:] or len(sys.argv) == 1:
    part_a()
if "b" in sys.argv[1:] or len(sys.argv) == 1:
    part_b(2)
