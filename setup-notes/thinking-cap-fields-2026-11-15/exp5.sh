U=http://localhost:1234/v1/chat/completions
M='"model":"qwen/qwen3.5-9b","messages":[{"role":"user","content":"How many weekdays are there between nov 3 and dec 1 2026?"}],"max_tokens":3000,"reasoning_effort":"low"'
for extra in '' ',"reasoning_budget":150' ',"thinking_budget":150' ',"reasoning":{"max_tokens":150}' ',"max_reasoning_tokens":150' ',"max_thinking_tokens":150'; do
  s=$(date +%s.%N); r=$(curl -s $U -H 'Content-Type: application/json' -d "{$M$extra}"); e=$(date +%s.%N)
  echo "$extra -> $(echo "$r" | python -c "import sys,json;d=json.load(sys.stdin);print(d.get('error') or d['usage']['completion_tokens_details'], '| content:', (d['choices'][0]['message'].get('content') or '')[:50].replace(chr(10),' '))" 2>&1) | $(python -c "print(round($e-$s,1))")s"
done
