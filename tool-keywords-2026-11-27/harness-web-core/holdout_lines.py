"""Held-out lines for the catkw run, written before it and never used to write a keyword.

web: lines that need web_search but avoid the web tool keywords (no "latest", "news", "price", "weather",
"score", "search", "who won" and the like), so only a fallback can reach the tool.
small_talk: lines near a category's topic that ask for nothing, so a category line could pull a wrong pick.
"""

from __future__ import annotations

WEB = {
    "en": [
        "Did Japan beat Germany in last night's match?",
        "What did the central bank decide this week?",
        "Is the new Zelda game out yet?",
        "Has the typhoon reached Okinawa?",
        "Which phone did Apple announce yesterday?",
        "Is the Shibuya station line running normally right now?",
    ],
    "ja": [
        "昨夜の試合で日本はドイツに勝った？",
        "今週、中央銀行は何を決めた？",
        "新しいゼルダのゲームはもう出た？",
        "台風はもう沖縄に来た？",
        "アップルは昨日どのスマホを発表した？",
        "渋谷駅の路線は今ちゃんと動いてる？",
    ],
}

SMALL_TALK = {
    "en": [
        "I slept so badly last night.",
        "My cat knocked over a plant again.",
        "I love that song you mentioned.",
        "I should really call my mom more.",
    ],
    "ja": [
        "昨夜は全然眠れなかった。",
        "また猫が植木鉢を倒したよ。",
        "前に話してたあの曲、大好き。",
        "もっと母に電話しなきゃな。",
    ],
}
