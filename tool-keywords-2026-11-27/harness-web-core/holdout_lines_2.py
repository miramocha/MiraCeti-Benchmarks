"""A second held-out set, written on 2026-11-28 after web_search was made a core tool, to test that choice.

The first set (holdout_lines.py) was used to pick web core, so it is a dev set now. These lines follow the same
rules and were never used to write a keyword or to pick a variant. They were written by the same author as the
keyword lists, so the author knew the web keywords while writing them.

web: lines that need web_search but avoid the web tool keywords, so only web core or more_tools can reach the tool.
small_talk: lines near a web or category topic that ask for nothing, to catch stray web_search picks.
"""

from __future__ import annotations

WEB = {
    "en": [
        "Did the Lakers win last night?",
        "Is the Tokaido Shinkansen delayed right now?",
        "What time does the sun set in Sapporo today?",
        "Has the election result in France come out?",
        "Is there a tsunami warning for the coast right now?",
        "What's the top movie at the box office this weekend?",
        "Did the Nintendo Direct announce anything big?",
        "Is the Tokyo Marathon still on this Sunday after the storm?",
        "Who is the new prime minister of the UK?",
        "Are the cherry blossoms out in Kyoto yet?",
        "Did SpaceX launch the rocket today?",
        "Is Steam down for everyone or just me?",
    ],
    "ja": [
        "昨日の夜、レイカーズは勝った？",
        "東海道新幹線、今遅れてる？",
        "札幌は今日何時に日が沈む？",
        "フランスの選挙結果はもう出た？",
        "今、沿岸に津波警報出てる？",
        "今週末の興行収入トップの映画は何？",
        "ニンテンドーダイレクトで何か大きな発表あった？",
        "嵐のあと、日曜の東京マラソンはまだやるの？",
        "イギリスの新しい首相は誰になった？",
        "京都の桜はもう咲いてる？",
        "スペースXは今日ロケットを打ち上げた？",
        "Steamって今みんな繋がらないの？",
    ],
}

SMALL_TALK = {
    "en": [
        "I finally finished that book last night.",
        "The new Zelda game was so much fun this weekend.",
        "I'm so tired of trains being late.",
        "My sister just had a baby!",
        "I made curry for dinner and it turned out great.",
        "Rainy days always make me sleepy.",
        "I think I'm getting a cold.",
        "I watched the match with friends, it was great.",
    ],
    "ja": [
        "昨日の夜、やっとあの本を読み終えた。",
        "週末のゼルダ、すごく楽しかった。",
        "電車の遅れにはもううんざり。",
        "姉に赤ちゃんが生まれたんだ！",
        "夕飯にカレー作ったら大成功だった。",
        "雨の日っていつも眠くなる。",
        "なんか風邪ひきそう。",
        "友達と試合を見たよ、最高だった。",
    ],
}
