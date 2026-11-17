"""Experiment 10: can a check on the reply catch tool turns that were answered without a tool?

1. Make replies with thinking off and all 8 tools offered (real schedule tools plus the stubs from experiment 8),
   in English and Japanese. A reply to a tool request with no tool call is positive: the net should fire.
   A reply to a normal line is negative: the net should stay quiet. Replies that called a tool are dropped.
2. Score three checks on those replies:
   regex       English completion phrases, in the style of the gist in the research notes.
   json_reply  thinking-off JSON check on the reply alone.
   json_pair   thinking-off JSON check on the user line and the reply together.
Writes safetynet-replies.jsonl and safetynet-checks.jsonl.
"""
import json, pathlib, re, sys, time
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
WIRE = [_function_tool(t) for t in TOOLS]

TOOL_LINES = {
    "en": ["remind me to drink water in 20 minutes", "can you remind me at 9pm to call mom",
           "every day at 8am tell me to stretch", "ping me in an hour about the laundry",
           "set a reminder for tomorrow 3pm, dentist", "cancel the laundry reminder",
           "add milk to my shopping list", "put 'finish the slides' on my todo list",
           "what's the latest news about the nintendo switch 2?", "search for the best ramen places in osaka",
           "what does https://example.com say?", "summarize this page for me https://example.org/blog/post-12"],
    "ja": ["20分後に水を飲むようにリマインドして", "夜9時にお母さんに電話するようリマインドしてくれる？",
           "毎朝8時にストレッチするように言って", "1時間後に洗濯物のこと教えて",
           "明日の午後3時に歯医者のリマインダーを設定して", "洗濯物のリマインダーをキャンセルして",
           "買い物リストに牛乳を追加して", "ToDoに「スライドを仕上げる」を入れて",
           "Switch 2の最新ニュースは？", "大阪のおいしいラーメン屋を検索して",
           "https://example.com には何が書いてある？", "このページを要約して https://example.org/blog/post-12"],
}
NORMAL_LINES = {
    "en": ["what time is it?", "i remember you said you like tea", "tell me about your day",
           "i forgot to call my mom yesterday lol", "can you remind me what we talked about?", "hi ceti!",
           "good night", "what's 17*23?", "i have a dentist appointment tomorrow at 3", "every day at 8am I go for a run",
           "i already searched for it, no luck", "my shopping list is so long this week", "i set an alarm on my phone already",
           "i'll be back in 20 minutes", "what should I eat for lunch?", "tell me a joke",
           "i'm so tired, I worked 10 hours today", "how do I make rice in a pot?", "i hate mondays", "what's your favorite food?"],
    "ja": ["今何時？", "紅茶が好きって言ってたの覚えてるよ", "今日はどんな一日だった？", "昨日お母さんに電話するの忘れたw",
           "前に何を話したか思い出させてくれる？", "やっほー、セティ！", "おやすみ", "17×23は？",
           "明日の3時に歯医者の予約があるんだ", "毎朝8時にランニングしてる", "もう検索したけど見つからなかった",
           "今週は買い物リストが長すぎる", "スマホでもうアラームセットしたよ", "20分で戻るね", "お昼何食べようかな？",
           "何か面白い話して", "疲れた、今日10時間働いたよ", "鍋でご飯ってどう炊くの？", "月曜日きらい", "好きな食べ物は何？"],
}
TOOL_REPS = 2

REGEX = re.compile(
    r"(?i)\b(i'?ve (set|added|scheduled|created|searched|looked|checked|put|noted)|i (set|added|scheduled|searched|looked up|checked|noted)|"
    r"i'?ll (remind|ping|nudge|set|add|search|look|check|fetch|let you know|tell you)|"
    r"(reminder|timer|alarm) (is )?(set|scheduled)|(is|it'?s) (on|added to) (your|the) list|"
    r"done[.!,]|got it[.!,]|all set|set up for you)"
)
CLAIM_Q = ("Does this assistant reply say that the assistant has done, is doing, or will do an action for the user, "
           "such as setting, changing or cancelling a reminder, adding to or reading a list, searching the web, or opening a page? "
           "Offers, questions, refusals, and plain chat are not actions.")
PAIR_Q = ("The assistant has tools for reminders, lists, web search, and opening web pages. "
          "Did the user ask for something one of those tools does, while the assistant replied without using one "
          "(for example by claiming it is done, promising to do it, guessing, or saying it cannot)?")
SCHEMA = {"type": "object", "properties": {"yes": {"type": "boolean"}}, "required": ["yes"], "additionalProperties": False}


def chat_reply(line):
    built = build_prompt(persona, line, PromptContext(user_name=s.user_name or "User", now=datetime.now().astimezone()))
    body = {"model": s.chat_model, "messages": [{"role": m.role, "content": m.content} for m in built],
            "temperature": s.chat_temperature, "max_tokens": s.chat_max_tokens, "tools": WIRE, "reasoning_effort": "none"}
    message = http.post(URL, json=body).json()["choices"][0]["message"]
    return message.get("content") or "", [c["function"]["name"] for c in message.get("tool_calls") or []]


def ask(prompt):
    body = {"model": s.chat_model, "temperature": 0, "max_tokens": 50, "reasoning_effort": "none",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "result", "schema": SCHEMA, "strict": True}}}
    started = time.perf_counter()
    content = http.post(URL, json=body).json()["choices"][0]["message"]["content"]
    return bool(json.loads(content)["yes"]), round((time.perf_counter() - started) * 1000)


replies_path = HERE / "safetynet-replies.jsonl"
if "reuse" in sys.argv[1:] and replies_path.exists():
    replies = [json.loads(l) for l in replies_path.read_text(encoding="utf-8").splitlines()]
else:
    replies = []
    with replies_path.open("w", encoding="utf-8") as out:
        for lang in ("en", "ja"):
            for label, lines, reps in ((1, TOOL_LINES[lang], TOOL_REPS), (0, NORMAL_LINES[lang], 1)):
                for line in lines:
                    for rep in range(reps):
                        content, called = chat_reply(line)
                        row = {"lang": lang, "label": label, "line": line, "rep": rep, "called": called, "reply": content}
                        out.write(json.dumps(row, ensure_ascii=False) + "\n"); out.flush()
                        if not called and content:
                            replies.append(row)
                        print(f"   gen {lang} {label} called={called} {line!r} -> {content[:70]!r}", flush=True)
    replies = [r for r in (json.loads(l) for l in replies_path.read_text(encoding="utf-8").splitlines()) if not r["called"] and r["reply"]]

print(f"\nreplies kept: {len(replies)} "
      f"(en +{sum(1 for r in replies if r['lang']=='en' and r['label'])} -{sum(1 for r in replies if r['lang']=='en' and not r['label'])}, "
      f"ja +{sum(1 for r in replies if r['lang']=='ja' and r['label'])} -{sum(1 for r in replies if r['lang']=='ja' and not r['label'])})", flush=True)

results = {"regex": [], "json_reply": [], "json_pair": []}
times = {"json_reply": [], "json_pair": []}
with (HERE / "safetynet-checks.jsonl").open("w", encoding="utf-8") as out:
    for r in replies:
        regex = bool(REGEX.search(r["reply"]))
        reply_yes, reply_ms = ask(f"{CLAIM_Q}\nReply: {json.dumps(r['reply'], ensure_ascii=False)}")
        pair_yes, pair_ms = ask(f"{PAIR_Q}\nUser: {json.dumps(r['line'], ensure_ascii=False)}\n"
                                f"Assistant: {json.dumps(r['reply'], ensure_ascii=False)}")
        results["regex"].append(regex); results["json_reply"].append(reply_yes); results["json_pair"].append(pair_yes)
        times["json_reply"].append(reply_ms); times["json_pair"].append(pair_ms)
        out.write(json.dumps({**r, "regex": regex, "json_reply": reply_yes, "json_pair": pair_yes,
                              "json_reply_ms": reply_ms, "json_pair_ms": pair_ms}, ensure_ascii=False) + "\n")

print("\ncheck       | lang | caught (of positives) | false fires (of negatives) | median ms")
for name in ("regex", "json_reply", "json_pair"):
    for lang in ("en", "ja"):
        idx = [i for i, r in enumerate(replies) if r["lang"] == lang]
        pos = [i for i in idx if replies[i]["label"]]; neg = [i for i in idx if not replies[i]["label"]]
        caught = sum(results[name][i] for i in pos); fired = sum(results[name][i] for i in neg)
        ms = sorted(times[name])[len(times[name]) // 2] if name in times else 0
        print(f"{name:11} | {lang}   | {caught}/{len(pos)} | {fired}/{len(neg)} | {ms}", flush=True)

print("\nmissed positives and false fires per check:")
for name in ("regex", "json_reply", "json_pair"):
    for i, r in enumerate(replies):
        if r["label"] and not results[name][i]:
            print(f"   {name} MISSED {r['lang']} {r['line']!r} -> {r['reply'][:90]!r}")
        if not r["label"] and results[name][i]:
            print(f"   {name} FIRED  {r['lang']} {r['line']!r} -> {r['reply'][:90]!r}")
