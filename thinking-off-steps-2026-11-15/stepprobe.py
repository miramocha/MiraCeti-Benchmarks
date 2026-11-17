import json, time
from datetime import datetime
import httpx2
from cetimind.app.settings import Settings
from cetimind.app.tools.schedule import SCHEDULE_CREATE
from cetimind.core.prompt import format_now

URL = "http://localhost:1234/v1/chat/completions"; KEV = "http://127.0.0.1:8009/v1/systemone"
s = Settings.load(); http = httpx2.Client(timeout=120)
now = format_now(datetime.now().astimezone()) if callable(format_now) else str(datetime.now())
SCHED = ["remind me to drink water in 20 minutes", "can you remind me at 9pm to call mom",
         "every day at 8am tell me to stretch", "ping me in an hour about the laundry",
         "set a reminder for tomorrow 3pm, dentist", "hey in 10 min tell me to check the oven"]
PLAIN = ["what time is it?", "i remember you said you like tea", "tell me about your day",
         "i forgot to call my mom yesterday lol", "what's the weather like where you are?", "can you remind me what we talked about?"]
INTENT_Q = "Is the user asking to be reminded, pinged, or told something at a later time (a reminder or scheduled message)?"
def kev(line):
    t=time.perf_counter()
    r=http.post(KEV,json={"state":f"User: {line}","model":"kev-latest","questions":{"q":{"type":"noul","instructions":INTENT_Q}}}).json()
    return float(r["answers"]["q"]["noul"]), (time.perf_counter()-t)*1000
def js(prompt, schema):
    t=time.perf_counter()
    b={"model":s.chat_model,"temperature":0,"max_tokens":300,"reasoning_effort":"none","messages":[{"role":"user","content":prompt}],
       "response_format":{"type":"json_schema","json_schema":{"name":"result","schema":schema,"strict":True}}}
    return json.loads(http.post(URL,json=b).json()["choices"][0]["message"]["content"]), (time.perf_counter()-t)*1000
INTENT = {"type":"object","properties":{"reminder":{"type":"boolean"}},"required":["reminder"],"additionalProperties":False}
def intent_json(line):
    p=(f"{INTENT_Q} Answer reminder=true or false.\nExamples: \"remind me to eat in 5 min\" -> true; \"remind me what you said\" -> false; "
       f"\"I forgot to call mom\" -> false.\nUser: {json.dumps(line)}")
    return js(p, INTENT)
def extract(line):
    params = dict(SCHEDULE_CREATE.parameters)
    p=(f"Now: {now}.\nFill the arguments for schedule_create from the user's message. {SCHEDULE_CREATE.description}\n"
       f"Use exactly one time field. User: {json.dumps(line)}")
    return js(p, params)
print("now:", now, flush=True)
for label, lines in (("SCHED", SCHED), ("PLAIN", PLAIN)):
    for line in lines:
        k, kms = kev(line); (ij, ims) = intent_json(line)
        out = f"{label} kev={k:.2f} ({kms:.0f}ms) json={ij['reminder']} ({ims:.0f}ms)  {line}"
        if label == "SCHED":
            a, ams = extract(line); out += f"\n      extract ({ams:.0f}ms): {json.dumps(a)}"
        print(out, flush=True)
