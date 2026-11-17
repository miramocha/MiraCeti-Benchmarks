import json, sys, time
from datetime import datetime
import httpx2
from cetimind.app.settings import Settings
from cetimind.app.persona import load_persona
from cetimind.app.tools.schedule import user_tools, SCHEDULE_CREATE, CURRENT_TIME
from cetimind.core.prompt import PromptContext, build_prompt
from cetimind.llm.client import _function_tool

URL = "http://localhost:1234/v1/chat/completions"
s = Settings.load(); persona = load_persona(saved=s.persona)
tools = [_function_tool(t) for t in user_tools()]
RULE = ("Tools: when the user asks to be reminded, pinged, or told something later, or to schedule anything, "
        "call schedule_create in this reply. Never say a reminder is set unless you called schedule_create.")
LINES = ["remind me to drink water in 20 minutes", "can you remind me at 9pm to call mom",
         "every day at 8am tell me to stretch", "ping me in an hour about the laundry",
         "set a reminder for tomorrow 3pm, dentist", "hey in 10 min tell me to check the oven"]
PLAIN = ["what time is it?", "i remember you said you like tea", "tell me about your day"]
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
http = httpx2.Client(timeout=180)

def msgs(line, rule):
    m = build_prompt(persona, line, PromptContext(user_name=s.user_name or "User", now=datetime.now().astimezone()))
    out = [{"role": x.role, "content": x.content} for x in m]
    if rule: out[0]["content"] += "\n\n" + RULE
    return out

def call(line, effort, rule=False, extra=None):
    body = {"model": s.chat_model, "messages": msgs(line, rule), "temperature": s.chat_temperature,
            "max_tokens": s.chat_max_tokens, "tools": tools, "reasoning_effort": effort}
    body.update(extra or {})
    t = time.perf_counter(); r = http.post(URL, json=body); ms = (time.perf_counter()-t)*1000
    if r.status_code >= 400: return None, ms, r.text[:120]
    m = r.json()["choices"][0]["message"]
    names = [c["function"]["name"] for c in (m.get("tool_calls") or [])]
    return "schedule_create" in names, ms, ",".join(names) or (m.get("content") or "")[:60]


INTENT = {"type":"object","properties":{"schedule":{"type":"boolean"}},"required":["schedule"],"additionalProperties":False}
def intent(line):
    body={"model":s.chat_model,"temperature":0,"max_tokens":50,"reasoning_effort":"none",
      "messages":[{"role":"user","content":"Does this message ask to be reminded, pinged, or told something later, or to schedule, list, or cancel a scheduled job? Message: "+json.dumps(line)}],
      "response_format":{"type":"json_schema","json_schema":{"name":"result","schema":INTENT,"strict":True}}}
    return json.loads(http.post(URL,json=body).json()["choices"][0]["message"]["content"])["schedule"]
def two_step(line):
    t=time.perf_counter(); want=intent(line); ims=(time.perf_counter()-t)*1000
    if not want: return False, ims, "intent=no"
    ok, ms, info = call(line, "none", rule=True)
    return ok, ims+ms, info
variants = {
  "A off": lambda l: call(l, "none"),
  "B think": lambda l: call(l, "low"),
  "C off+rule": lambda l: call(l, "none", rule=True),
  "E intent->off+rule": two_step,
}
print("persona:", persona.name, "| tools:", [t["function"]["name"] for t in tools], flush=True)
for name, fn in variants.items():
    hits=n=0; tot=0.0; misses=[]; fp=0
    for line in LINES:
        for _ in range(REPS):
            ok, ms, info = fn(line); n+=1; tot+=ms
            if ok: hits+=1
            else: misses.append(f"{line!r} -> {info!r}")
    for line in PLAIN:
        ok, ms, info = fn(line)
        if ok: fp+=1
    print(f"\n{name}: {hits}/{n} scheduled, avg {tot/n:.0f} ms, false schedule on plain {fp}/{len(PLAIN)}", flush=True)
    for x in misses[:4]: print("   miss", x, flush=True)
