import json, time, httpx2
URL = "http://localhost:1234/v1/chat/completions"
long = " ".join(f"Fact {i}: the user likes item number {i} and visits place {i*7} on weekends." for i in range(250))
def run(tag, user):
    body = {"model": "qwen/qwen3.5-9b", "stream": True, "stream_options": {"include_usage": True}, "max_tokens": 8,
            "reasoning_effort": "none", "temperature": 0,
            "messages": [{"role": "system", "content": "You are terse.\n" + long}, {"role": "user", "content": user}]}
    t = time.perf_counter(); first = None; usage = None
    with httpx2.Client(timeout=120) as c, c.stream("POST", URL, json=body) as r:
        for line in r.iter_lines():
            if not line.startswith("data: ") or line == "data: [DONE]": continue
            d = json.loads(line[6:])
            if d.get("usage"): usage = d["usage"]
            ch = d.get("choices") or []
            if first is None and ch and (ch[0].get("delta") or {}).get("content"): first = time.perf_counter() - t
    print(tag, "ttft", round(first or -1, 3), "total", round(time.perf_counter() - t, 3), "usage", usage)
run("cold", "Say hi.")
run("same prompt again", "Say hi.")
run("new last message", "Say bye.")
