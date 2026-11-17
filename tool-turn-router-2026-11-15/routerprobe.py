"""Experiment 7: which router finds tool turns. Rules, embedding similarity, a JSON intent check, and Kev.

Positive = the turn needs schedule_create, schedule_list, or schedule_cancel. current_time does not count,
because the prompt already carries a clock line. Writes routerprobe.jsonl beside this script, then prints
a threshold sweep and a split-half check per method.
"""
import json, math, pathlib, re, sys, time
import httpx2
from cetimind.app.settings import Settings
from cetimind.app.tools.schedule import SCHEDULE_CANCEL, SCHEDULE_CREATE, SCHEDULE_LIST
from cetimind.config import SHORT_LINE_WORDS, llm_base_url
from cetimind.llm.client import LlmClient

KEV = "http://127.0.0.1:8009/v1/systemone"
s = Settings.load()
llm = LlmClient(llm_base_url(s.llm_base_url), s.chat_model, s.embed_model, max_tokens=50)
http = httpx2.Client(timeout=120)
HERE = pathlib.Path(__file__).parent

# (label, line, last assistant reply or None). 1 = needs a schedule tool.
CASES = [
    (1, "remind me to drink water in 20 minutes", None),
    (1, "can you remind me at 9pm to call mom", None),
    (1, "every day at 8am tell me to stretch", None),
    (1, "ping me in an hour about the laundry", None),
    (1, "set a reminder for tomorrow 3pm, dentist", None),
    (1, "hey in 10 min tell me to check the oven", None),
    (1, "wake me up at 7 tomorrow", None),
    (1, "don't let me forget to submit the form by 5pm", None),
    (1, "nudge me every 30 minutes to fix my posture", None),
    (1, "tell me to go to bed at midnight", None),
    (1, "in 45 minutes ask me if I finished the essay", None),
    (1, "every monday at 10 remind me about standup", None),
    (1, "could you check in on me in 2 hours", None),
    (1, "remind me to stream tonight at 8", None),
    (1, "set a timer for 25 minutes", None),
    (1, "at noon tell me to eat lunch", None),
    (1, "i need a reminder on friday morning to pay rent", None),
    (1, "yell at me in 15 min if I'm still gaming lol", None),
    (1, "schedule a message for 6pm saying good luck on the exam", None),
    (1, "every weekday at 5 tell me to log off", None),
    (1, "what reminders do I have?", None),
    (1, "did you set anything for tonight?", None),
    (1, "show me my scheduled stuff", None),
    (1, "what's on my schedule from you?", None),
    (1, "cancel the laundry reminder", None),
    (1, "never mind, don't remind me about the oven", None),
    (1, "stop the posture nudges", None),
    (1, "delete all my reminders", None),
    (1, "yes please", "Want me to remind you before your exam?"),
    (1, "make it 2pm instead", "Okay, I'll remind you about the dentist at 3pm tomorrow."),
    (0, "what time is it?", None),
    (0, "i remember you said you like tea", None),
    (0, "tell me about your day", None),
    (0, "i forgot to call my mom yesterday lol", None),
    (0, "what's the weather like where you are?", None),
    (0, "can you remind me what we talked about?", None),
    (0, "hi ceti!", None),
    (0, "good night", None),
    (0, "what's 17*23?", None),
    (0, "i have a dentist appointment tomorrow at 3", None),
    (0, "my mom's birthday is on december 5", None),
    (0, "i usually wake up at 7", None),
    (0, "every day at 8am I go for a run", None),
    (0, "the laundry has been sitting there for an hour", None),
    (0, "do you remember my favorite color?", None),
    (0, "remind me, what's your name again?", None),
    (0, "i'm so tired, I worked 10 hours today", None),
    (0, "what day is it tomorrow?", None),
    (0, "lol you never remember anything", None),
    (0, "how long does it take to boil an egg?", None),
    (0, "i set an alarm on my phone already", None),
    (0, "what should I eat for lunch?", None),
    (0, "tell me a joke", None),
    (0, "i'll be back in 20 minutes", None),
    (0, "explain how reminders work in your app", None),
    (0, "i hate mondays", None),
    (0, "can you help me plan my study schedule?", None),
    (0, "my schedule is so packed this week ugh", None),
    (0, "no thanks", "Want me to remind you before your exam?"),
    (0, "thanks!", "Done, I'll ping you at 9."),
]

# Anchors for the embedding methods. None of these wordings is a test line.
POS_ANCHORS = ["remind me to take out the trash in thirty minutes", "set a reminder for next tuesday at 4pm",
               "every night at 11 tell me to sleep", "list my reminders", "cancel that reminder"]
NEG_ANCHORS = ["I remember when we first met", "what time is it right now", "tell me about yourself",
               "I have a meeting at 3", "good morning"]
LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
LOCAL_POS, LOCAL_NEG = POS_ANCHORS, NEG_ANCHORS
if LANG != "en":
    pack = json.loads((HERE / "multilang.json").read_text(encoding="utf-8"))[LANG]
    CASES = [tuple(c) for c in pack["cases"]]
    LOCAL_POS, LOCAL_NEG = pack["pos_anchors"], pack["neg_anchors"]
DESCRIPTIONS = [SCHEDULE_CREATE.description, SCHEDULE_LIST.description, SCHEDULE_CANCEL.description]

RULES = re.compile(
    r"(?i)\b(remind(er|ers)?|ping me|nudge|wake me|alarm|timer|schedul(e|ed)|check in on me|"
    r"tell me to|ask me (if|to)|don'?t let me forget|cancel|never mind|"
    r"in \d+ ?(min|mins|minutes|hours?|hrs?)|every (day|morning|night|week|weekday|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d+ ?(min|minutes|hours?)))\b"
)
INTENT_Q = ("Is the user asking to set, change, list, or cancel a reminder or scheduled message, "
            "or agreeing to one that was just offered?")
INTENT = {"type": "object", "properties": {"tool": {"type": "boolean"}}, "required": ["tool"], "additionalProperties": False}


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def context_query(line, reply):
    """CetiMind's _context_query: a short line follows the last reply."""
    if reply and len(line.split()) < SHORT_LINE_WORDS:
        return f"{reply}\n{line}"
    return line


def state(line, reply):
    return f"Assistant: {reply}\nUser: {line}" if reply else f"User: {line}"


def kev(line, reply):
    body = {"state": state(line, reply), "model": "kev-latest", "questions": {"q": {"type": "noul", "instructions": INTENT_Q}}}
    return float(http.post(KEV, json=body).json()["answers"]["q"]["noul"])


def json_intent(line, reply):
    prompt = (f"{INTENT_Q} Answer tool=true or false.\n"
              "Examples: \"remind me to eat in 5 min\" -> true; \"what reminders are set?\" -> true; "
              "\"remind me what you said\" -> false; \"I forgot to call mom\" -> false; \"I have a meeting at 4\" -> false.\n"
              f"Conversation:\n{state(line, reply)}")
    saved = llm._reasoning_effort
    llm.set_reasoning("none")
    try:
        return bool(llm.chat_json([{"role": "user", "content": prompt}], INTENT, name="result")["tool"])
    finally:
        llm.set_reasoning(saved)


def timed(fn, *args):
    started = time.perf_counter()
    value = fn(*args)
    return value, (time.perf_counter() - started) * 1000


pos_vecs = [llm.embed_document(t) for t in POS_ANCHORS]
neg_vecs = [llm.embed_document(t) for t in NEG_ANCHORS]
desc_vecs = [llm.embed_document(t) for t in DESCRIPTIONS]
lpos_vecs = [llm.embed_document(t) for t in LOCAL_POS]
lneg_vecs = [llm.embed_document(t) for t in LOCAL_NEG]
kev("warm up", None)

rows = []
log = (HERE / f"routerprobe-{LANG}.jsonl").open("w", encoding="utf-8")
for index, (label, line, reply) in enumerate(CASES):
    vec, embed_ms = timed(llm.embed_query, context_query(line, reply))
    pos = max(cosine(vec, v) for v in pos_vecs)
    neg = max(cosine(vec, v) for v in neg_vecs)
    row = {
        "i": index, "label": label, "line": line, "reply": reply,
        "rules": 1 if RULES.search(line) else 0,
        "embed_desc": round(max(cosine(vec, v) for v in desc_vecs), 4),
        "embed_pos": round(pos, 4),
        "embed_margin": round(pos - neg, 4),
        "embed_local": round(max(cosine(vec, v) for v in lpos_vecs) - max(cosine(vec, v) for v in lneg_vecs), 4),
        "embed_ms": round(embed_ms),
    }
    row["kev"], kev_ms = timed(kev, line, reply)
    row["kev"] = round(row["kev"], 4); row["kev_ms"] = round(kev_ms)
    answer, json_ms = timed(json_intent, line, reply)
    row["json"] = 1 if answer else 0; row["json_ms"] = round(json_ms)
    rows.append(row)
    log.write(json.dumps(row) + "\n"); log.flush()
    print(f"{label} rules={row['rules']} desc={row['embed_desc']:.3f} pos={row['embed_pos']:.3f} "
          f"margin={row['embed_margin']:+.3f} kev={row['kev']:.2f} json={row['json']} "
          f"({embed_ms:.0f}/{kev_ms:.0f}/{json_ms:.0f} ms)  {line}", flush=True)


def counts(scores, labels, cut):
    fn = sum(1 for x, y in zip(scores, labels) if y == 1 and x < cut)
    fp = sum(1 for x, y in zip(scores, labels) if y == 0 and x >= cut)
    return fn, fp


def best_cut(scores, labels):
    """The cut with the fewest errors. Ties go to fewer misses, because a miss is a false 'it's set'."""
    options = sorted(set(scores))
    return min(options, key=lambda c: (sum(counts(scores, labels, c)), counts(scores, labels, c)[0]))


def median(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


labels = [r["label"] for r in rows]
print(f"\n{sum(labels)} positive, {len(labels) - sum(labels)} negative")
print("method        | misses | false alarms | cut | split-half misses/false alarms | median ms")
for name, ms_key in (("rules", None), ("json", "json_ms"), ("kev", "kev_ms"),
                     ("embed_desc", "embed_ms"), ("embed_pos", "embed_ms"), ("embed_margin", "embed_ms"), ("embed_local", "embed_ms")):
    scores = [r[name] for r in rows]
    if name in ("rules", "json"):
        cut, split = 1, ""
    else:
        cut = best_cut(scores, labels)
        even = [i for i in range(len(rows)) if i % 2 == 0]
        odd = [i for i in range(len(rows)) if i % 2 == 1]
        split_errors = [0, 0]
        for train, test in ((even, odd), (odd, even)):
            c = best_cut([scores[i] for i in train], [labels[i] for i in train])
            fn, fp = counts([scores[i] for i in test], [labels[i] for i in test], c)
            split_errors[0] += fn; split_errors[1] += fp
        split = f"{split_errors[0]}/{split_errors[1]}"
    fn, fp = counts(scores, labels, cut)
    ms = median([r[ms_key] for r in rows]) if ms_key else 0
    print(f"{name:13} | {fn:6} | {fp:12} | {cut:.3f} | {split:30} | {ms}")

# Two-stage idea: rules say no -> no tool; rules say yes -> ask the second method.
print("\nrules first, then a second check on rule hits only:")
for name in ("json", "kev", "embed_margin", "embed_local"):
    scores = [r[name] for r in rows]
    cut = 1 if name == "json" else best_cut([s for s, r in zip(scores, rows) if r["rules"]],
                                             [r["label"] for r in rows if r["rules"]])
    decided = [1 if r["rules"] and sc >= cut else 0 for sc, r in zip(scores, rows)]
    fn = sum(1 for d, y in zip(decided, labels) if y == 1 and d == 0)
    fp = sum(1 for d, y in zip(decided, labels) if y == 0 and d == 1)
    calls = sum(r["rules"] for r in rows)
    print(f"  rules -> {name}: misses {fn}, false alarms {fp}, second check ran on {calls}/{len(rows)} lines (cut {cut})")
print("\nmisses and false alarms per method are in routerprobe.jsonl")
