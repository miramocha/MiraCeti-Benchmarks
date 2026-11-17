import json, time, sys, urllib.request
URL = "http://127.0.0.1:8009/v1/systemone"
Q = "Does answering the user's last message need careful step-by-step reasoning (math, logic, code, planning, multi-step analysis), rather than a quick conversational reply?"
lines = [
 ("easy","hi ceti!"), ("easy","lol that's funny"), ("easy","good morning, how are you?"),
 ("easy","i'm going to bed now, night"), ("easy","what's your favorite color?"),
 ("easy","thanks, that helps"), ("easy","remind me to drink water in 20 minutes"),
 ("hard","what is 17*23 minus 48?"), ("hard","why does my python loop skip every other item when I remove from the list?"),
 ("hard","plan a 3-day study schedule for my exam covering 5 chapters"),
 ("hard","compare renting vs buying a car for 2 years, pros and cons"),
 ("hard","if A is taller than B and B is taller than C, who is shortest?"),
 ("hard","how many weekdays are there between nov 3 and dec 1?"),
]
for want, text in lines:
    body = {"state": f"User: {text}", "model": "kev-latest", "questions": {"think": {"type": "noul", "instructions": Q}}}
    t = time.perf_counter()
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    out = json.load(urllib.request.urlopen(req, timeout=30))
    ms = (time.perf_counter() - t) * 1000
    print(f"{want:4} {float(out['answers']['think']['noul']):.2f} {ms:6.0f}ms  {text}")
