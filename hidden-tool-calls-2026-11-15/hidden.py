"""Experiment 9: are thinking-on misses tool calls written inside the reasoning (llama.cpp #20837)?

Runs the six schedule lines with thinking on, 5 times each, and logs the full reasoning and content.
A miss is 'hidden' when its reasoning or content holds tool-call markup. Writes hidden.jsonl.
"""
import json, pathlib, re, time
from datetime import datetime
import httpx2
from cetimind.app.persona import load_persona
from cetimind.app.settings import Settings
from cetimind.app.tools.schedule import user_tools
from cetimind.core.prompt import PromptContext, build_prompt
from cetimind.llm.client import _function_tool

URL = "http://localhost:1234/v1/chat/completions"
HERE = pathlib.Path(__file__).parent
s = Settings.load(); persona = load_persona(saved=s.persona)
http = httpx2.Client(timeout=300)
tools = [_function_tool(t) for t in user_tools()]
LINES = ["remind me to drink water in 20 minutes", "can you remind me at 9pm to call mom",
         "every day at 8am tell me to stretch", "ping me in an hour about the laundry",
         "set a reminder for tomorrow 3pm, dentist", "hey in 10 min tell me to check the oven"]
MARKUP = re.compile(r"<tool_call>|<function=|\"name\"\s*:\s*\"schedule_|schedule_create\s*\(", re.IGNORECASE)
REPS = 5

out = (HERE / "hidden.jsonl").open("w", encoding="utf-8")
hits = misses = hidden = 0
for line in LINES:
    for rep in range(REPS):
        built = build_prompt(persona, line, PromptContext(user_name=s.user_name or "User", now=datetime.now().astimezone()))
        body = {"model": s.chat_model, "messages": [{"role": m.role, "content": m.content} for m in built],
                "temperature": s.chat_temperature, "max_tokens": s.chat_max_tokens, "tools": tools, "reasoning_effort": "low"}
        started = time.perf_counter()
        data = http.post(URL, json=body).json()
        ms = round((time.perf_counter() - started) * 1000)
        message = data["choices"][0]["message"]
        reasoning = message.get("reasoning_content") or message.get("reasoning") or ""
        content = message.get("content") or ""
        called = [c["function"]["name"] for c in message.get("tool_calls") or []]
        ok = "schedule_create" in called
        markup = bool(MARKUP.search(reasoning) or MARKUP.search(content))
        hits += ok; misses += not ok; hidden += (not ok) and markup
        out.write(json.dumps({"line": line, "rep": rep, "ms": ms, "called": called, "markup": markup,
                              "finish_reason": data["choices"][0].get("finish_reason"),
                              "reasoning_tokens": ((data.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens"),
                              "reasoning": reasoning, "content": content}, ensure_ascii=False) + "\n")
        out.flush()
        tail = reasoning[-160:].replace("\n", " ")
        print(f"   {'ok  ' if ok else 'MISS'} markup={markup} {ms:6}ms {line!r}" + ("" if ok else f"\n        content: {content[:100]!r}\n        reasoning end: {tail!r}"), flush=True)
print(f"\nthinking on: {hits}/{hits + misses} called schedule_create; misses {misses}, of which {hidden} had tool-call markup in reasoning or content", flush=True)
