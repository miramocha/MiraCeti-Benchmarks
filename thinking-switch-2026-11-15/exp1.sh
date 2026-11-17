U=http://localhost:1234/v1/chat/completions
run(){ echo "== $1"; s=$(date +%s.%N); curl -s $U -H 'Content-Type: application/json' -d "$2" | python -c "import sys,json;d=json.load(sys.stdin);m=d['choices'][0]['message'];print('reasoning chars:',len(m.get('reasoning_content') or m.get('reasoning') or ''),'| usage:',d.get('usage',{}).get('completion_tokens_details'))"; e=$(date +%s.%N); echo "secs: $(python -c "print(round($e-$s,2))")"; }
M='"model":"qwen/qwen3.5-9b","messages":[{"role":"user","content":"What is 17*23? Answer briefly."}],"max_tokens":3000'
run default "{$M}"
run effort_none "{$M,\"reasoning_effort\":\"none\"}"
run kwargs_off "{$M,\"chat_template_kwargs\":{\"enable_thinking\":false}}"
run reasoning_off "{$M,\"reasoning\":\"off\"}"
run reasoning_obj "{$M,\"reasoning\":{\"effort\":\"none\"}}"
run effort_low "{$M,\"reasoning_effort\":\"low\"}"
run effort_high "{$M,\"reasoning_effort\":\"high\"}"
run reasoning_on "{$M,\"reasoning\":\"on\"}"
run kwargs_on "{$M,\"chat_template_kwargs\":{\"enable_thinking\":true}}"
