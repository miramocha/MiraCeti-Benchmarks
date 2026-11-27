"""Line sets for the intent bench (#137), beside the prompt-order test lines in lines.py and heavy.py.

The held-out cancel lines and the near misses were written for the 2026-11-26 intent-cancel-example run. No
ToolSpec.intent_examples line may reuse this wording, so the bench measures generalizing, not copying.
"""

from __future__ import annotations

# Prompt-order case ids that are cancel lines. They join the cancel_test group.
CANCEL_TEST = ("cancel-", "forget-")

# Cancel lines no prompt or example has seen. Right when schedule_cancel is picked.
CANCEL_NEW = {
    "en": [
        "Drop the water reminder, I just had a glass.",
        "I don't need the stretch alarm anymore.",
        "Scrap my oven timer, the bread is out.",
        "Turn off the reminder about the oven.",
        "No need to remind me about water today.",
        "Can you clear my reminders?",
    ],
    "ja": [
        "水のリマインダーはいらない、今飲んだから。",
        "ストレッチのアラームはもういらない。",
        "オーブンのタイマーは消して、パンはもう出した。",
        "オーブンのリマインダーをオフにして。",
        "今日は水のことリマインドしなくていいよ。",
        "リマインダーを全部消してくれる？",
    ],
}

# Lines that mention reminders or cancelling but ask for nothing. Right when no tool is picked.
NEAR_MISS = {
    "en": [
        "I cancelled my gym membership today.",
        "I already checked the oven, the bread looks great.",
        "My reminders app at work is so annoying.",
        "I forgot to drink water again, oops.",
    ],
    "ja": [
        "今日ジムの会員を解約したよ。",
        "もうオーブンは確認した、パンいい感じ。",
        "職場のリマインダーアプリ、ほんと面倒。",
        "また水飲むの忘れてた、あはは。",
    ],
}

# The bar the live prompt must meet on qwen3.5-4b whenever INTENT_INSTRUCTION or an example changes.
MIN_CANCEL_NEW = 0.80
MAX_NEAR_MISS_ALARMS = 0
# Groups where the live prompt may not score below the bare prompt (no examples).
NO_DROP_GROUPS = ("tool", "none", "either", "cancel_test")
