"""Long tool results for #143: does the spoken reply find an answer that sits deep in a fetched page or search?

Each case is a line that needs http_get or web_search. Its canned result is long synthetic text with one answer
sentence planted early, in the middle, or late, and one distractor sentence near the start: a related value that is
not the answer (last season's date, the weekday closing time). Everything is synthetic.

English pages are about 6,000 characters, the http_get cap (HTTP_TEXT_CAP). Japanese pages are about 2,500
characters: the server runs a 6,144-token context, and a 6,000-character Japanese page (about 1 token per character)
would overflow the tool rounds. Search results follow format_hits: 10 hits with 300-character snippets.
"""

from __future__ import annotations

from lines import Case

POSITIONS = ("early", "mid", "late")
# Where the answer sentence goes, as a share of the page. The distractor always sits near the start.
_AT = {"early": 0.07, "mid": 0.45, "late": 0.85}
_PAGE_CHARS = {"en": 6000, "ja": 2500}
_DISTRACTOR_AT = 0.03
# Search snippets are padded to about this many characters, under the 300-character SEARCH_SNIPPET_CAP.
_SNIPPET_CHARS = {"en": 280, "ja": 200}
_PAD = {
    "en": " Readers in the comments asked about entry fees, start times, and where to park on the day.",
    "ja": "コメント欄では参加費やスタート時刻、当日の駐車場についての質問が多かった。",
}


_PAGES = {
    "season": {
        "url": "https://playtide.example/patch-notes",
        "line": {
            "en": "Can you read https://playtide.example/patch-notes and tell me when Season 4 starts?",
            "ja": "https://playtide.example/patch-notes を読んで、シーズン4がいつ始まるか教えて。",
        },
        "answer": {
            "en": "Season 4, Tidebreak, starts on June 12 for every region.",
            "ja": "シーズン4「タイドブレイク」は全地域で6月12日に始まります。",
        },
        "distractor": {
            "en": "For reference, Season 3 began on March 3 after a short delay.",
            "ja": "参考までに、シーズン3は少し遅れて3月3日に始まりました。",
        },
        "keys": ("June 12", "12 June", "6月12日", "6/12"),
        "wrong": ("March 3", "3月3日"),
        "filler": {
            "en": [
                "The harbor map gets new cover near the lighthouse, so long sight lines over the water are shorter.",
                "Crab traps now despawn after ten minutes when no player is nearby, which cuts server load.",
                "We fixed a bug where the fishing rod kept its glow after the player swapped to the lantern.",
                "Storm weather now warns players with a horn sound thirty seconds before the waves rise.",
                "The trading post lists items in the order players last viewed them instead of by price.",
                "Controller players can now remap the dive button from the accessibility menu.",
                "Several dock planks no longer flicker at long draw distance on lower graphics settings.",
                "Ranked matchmaking widens its search range more slowly during the first two minutes.",
                "The tutorial island has new signs that point to the net mending bench and the cook fire.",
                "Voice chat volume is now saved per player, so muting one teammate stays muted next session.",
            ],
            "ja": [
                "灯台近くの港マップに遮蔽物が増え、海上の見通しが短くなりました。",
                "近くにプレイヤーがいないカニ罠は10分で消え、サーバー負荷が減ります。",
                "ランタンに持ち替えても釣り竿が光り続ける不具合を直しました。",
                "嵐の天候では波が高くなる30秒前に汽笛で知らせます。",
                "交易所の品物は価格順ではなく最後に見た順に並びます。",
                "コントローラーで潜水ボタンをアクセシビリティ設定から変更できます。",
                "低画質設定で遠くの桟橋の板がちらつく問題を直しました。",
                "ランク戦のマッチングは最初の2分間、検索範囲をゆっくり広げます。",
            ],
        },
    },
    "library": {
        "url": "https://citylib.example/hours",
        "line": {
            "en": "Check https://citylib.example/hours. What time does the library close on Saturday?",
            "ja": "https://citylib.example/hours を見て。土曜日は図書館が何時に閉まる？",
        },
        "answer": {
            "en": "On Saturdays the main branch closes at 5:30 PM.",
            "ja": "土曜日の本館は17時30分に閉館します。",
        },
        "distractor": {
            "en": "On weekdays the main branch stays open until 8 PM.",
            "ja": "平日の本館は20時まで開いています。",
        },
        "keys": ("5:30", "17:30", "five thirty", "half past five", "17時30分", "5時半", "17時半", "午後5時30分"),
        "wrong": ("8 PM", "8:00", "20:00", "8pm", "20時", "午後8時"),
        "filler": {
            "en": [
                "Library cards are free for anyone who lives, works, or studies in the city.",
                "The study rooms on the second floor can be booked up to a week ahead with a card number.",
                "Returned items are checked in within one business day, and fines are no longer charged.",
                "The makerspace has two 3D printers, a laser cutter, and a sewing machine for card holders.",
                "Story time for children under five runs in the reading garden when the weather allows.",
                "Printing costs ten cents a page in black and white and fifty cents a page in color.",
                "The local history room keeps old maps, newspapers, and photographs of the waterfront.",
                "Free wifi covers the whole building and the courtyard, and no password is needed.",
                "The book sale in the lobby is run by volunteers, and all money goes to the youth programs.",
                "Lockers near the entrance take a coin that is returned when the locker is opened again.",
            ],
            "ja": [
                "市内に住む人、働く人、通学する人は誰でも無料で利用カードを作れます。",
                "2階の学習室はカード番号で1週間前から予約できます。",
                "返却された資料は1営業日以内に処理され、延滞料はかかりません。",
                "工作室には3Dプリンター2台、レーザーカッター、ミシンがあります。",
                "5歳以下向けのおはなし会は、天気が良ければ読書の庭で開きます。",
                "印刷は白黒1枚10円、カラー1枚50円です。",
                "郷土資料室には港の古い地図や新聞、写真があります。",
                "館内と中庭は無料Wi-Fiが使え、パスワードはいりません。",
            ],
        },
    },
    "ferry": {
        "url": "https://islandferry.example/timetable",
        "line": {
            "en": "Look at https://islandferry.example/timetable and tell me the last ferry back from the island on "
            "Sunday.",
            "ja": "https://islandferry.example/timetable を見て、日曜日に島から戻る最終フェリーは何時？",
        },
        "answer": {
            "en": "On Sundays the last ferry from the island back to the mainland leaves at 6:40 PM.",
            "ja": "日曜日、島から本土へ戻る最終フェリーは18時40分発です。",
        },
        "distractor": {
            "en": "On weekdays the last ferry from the island leaves at 9:15 PM.",
            "ja": "平日の島発の最終フェリーは21時15分発です。",
        },
        "keys": ("6:40", "18:40", "18時40分", "6時40分"),
        "wrong": ("9:15", "21:15", "21時15分", "9時15分"),
        "filler": {
            "en": [
                "Tickets can be bought at the pier kiosk or on board, and cash and cards are both accepted.",
                "Bicycles ride free, but there is room for only twelve on each crossing.",
                "The crossing takes about thirty-five minutes in calm weather and longer in strong wind.",
                "Dogs on a lead are welcome on the open upper deck but not in the cabin.",
                "The cafe on the lower deck sells coffee, soup, and sandwiches until twenty minutes before docking.",
                "Crossings may be cancelled at short notice in a storm, and the pier board shows the latest status.",
                "Car spaces must be booked a day ahead, and drivers should arrive twenty minutes early.",
                "Monthly passes for island residents can be renewed at the harbor office.",
                "Wheelchair users can board by the lower ramp, and staff will help on request.",
                "Lost property is kept at the harbor office for thirty days.",
            ],
            "ja": [
                "乗船券は桟橋の売店か船内で買え、現金もカードも使えます。",
                "自転車は無料ですが、1便につき12台までです。",
                "穏やかな日は約35分で渡れますが、強風の日は長くかかります。",
                "リードをつけた犬は上の甲板なら乗れますが、客室には入れません。",
                "下の甲板のカフェでは、着岸20分前までコーヒーとスープを売っています。",
                "嵐の日は急に欠航することがあり、桟橋の掲示板に最新情報が出ます。",
                "車での乗船は前日までに予約し、20分前に来てください。",
                "島民用の月間パスは港の事務所で更新できます。",
            ],
        },
    },
    "bread": {
        "url": "https://breadbook.example/country-sourdough",
        "line": {
            "en": "Open https://breadbook.example/country-sourdough. How long do I bake it?",
            "ja": "https://breadbook.example/country-sourdough を開いて。焼き時間はどれくらい？",
        },
        "answer": {
            "en": "Bake the loaf for 42 minutes in total: 20 with the lid on, then 22 with the lid off.",
            "ja": "焼き時間は合計42分です。ふたをして20分、ふたを取って22分焼きます。",
        },
        "distractor": {
            "en": "Let the shaped dough proof in the fridge for 12 hours before it goes in the oven.",
            "ja": "成形した生地は、焼く前に冷蔵庫で12時間発酵させます。",
        },
        "keys": ("42 minutes", "42 min", "forty-two minutes", "forty two minutes", "42分"),
        "wrong": ("12 hours", "12時間"),
        "filler": {
            "en": [
                "Feed the starter the night before so it is bubbly and smells sweet by morning.",
                "Mix the flour and water first and let them rest for an hour before adding the salt.",
                "Stretch and fold the dough four times, about thirty minutes apart, during the first rise.",
                "A wetter dough gives a more open crumb, but it is harder to shape on the bench.",
                "Dust the basket with rice flour, which sticks less than wheat flour.",
                "Score the top with one long cut at a shallow angle so the loaf opens into an ear.",
                "Preheat the pot inside the oven so the dough meets a hot surface right away.",
                "Let the bread cool for at least an hour before cutting, or the crumb will be gummy.",
                "Whole wheat flour drinks more water, so add a little more if you swap some in.",
                "Store the cut loaf face down on a board, and it will stay fresh for two or three days.",
            ],
            "ja": [
                "前の晩に元種に餌をやり、朝には泡立って甘い香りがする状態にします。",
                "まず粉と水を混ぜ、1時間休ませてから塩を加えます。",
                "一次発酵の間に、30分ごとに4回ほど生地を伸ばして折りたたみます。",
                "水分の多い生地は気泡が大きくなりますが、成形は難しくなります。",
                "発酵かごには小麦粉より付きにくい米粉を振ります。",
                "表面に浅い角度で1本長いクープを入れると、きれいに開きます。",
                "鍋ごとオーブンで予熱し、生地がすぐ熱い面に触れるようにします。",
                "切る前に最低1時間冷まさないと、中がべたつきます。",
            ],
        },
    },
}

_SEARCH = {
    "line": {
        "en": "Search who won the women's race at the 2026 Tokyo Marathon.",
        "ja": "2026年の東京マラソン女子の優勝者を検索して。",
    },
    "answer": {
        "en": ("Tokyo Marathon 2026: Haruka Mori wins women's race", "tokyo-news.example/marathon-2026",
               "Haruka Mori won the women's race at the 2026 Tokyo Marathon in 2:19:48, pulling away after 35 km."),
        "ja": ("東京マラソン2026 女子は森遥が優勝", "tokyo-news.example/marathon-2026",
               "2026年の東京マラソン女子は森遥が2時間19分48秒で優勝し、35キロ過ぎから抜け出した。"),
    },
    "distractor": {
        "en": ("Tokyo Marathon 2025 results", "runnersweek.example/tokyo-2025",
               "Aiko Tanaka won the women's race at the 2025 Tokyo Marathon in a close finish."),
        "ja": ("東京マラソン2025 結果", "runnersweek.example/tokyo-2025",
               "2025年の東京マラソン女子は田中愛子が接戦を制して優勝した。"),
    },
    "keys": ("Haruka Mori", "Mori", "森遥", "森 遥", "森さん", "森選手"),
    "wrong": ("Aiko Tanaka", "Tanaka", "田中愛子", "田中"),
    "filler": {
        "en": [
            ("How to train for your first marathon", "runcoach.example/first-marathon",
             "A sixteen-week plan with three easy runs, one long run, and one rest day each week."),
            ("Tokyo Marathon course map", "tokyo-marathon.example/course",
             "The course starts at the city hall, passes the old shopping streets, and finishes near the station."),
            ("Best running shoes this year", "gearlab.example/shoes",
             "We tested twenty pairs for cushioning, weight, and grip on wet roads."),
            ("Road closures on marathon day", "city.example/closures",
             "Main roads in the center are closed from early morning until mid afternoon."),
            ("Marathon nutrition guide", "fuelrun.example/guide",
             "Take a gel every forty-five minutes and drink at every second water station."),
            ("Volunteer at the Tokyo Marathon", "tokyo-marathon.example/volunteer",
             "Volunteers hand out water, guide runners, and help at the finish area."),
            ("Weather on race morning", "weather.example/tokyo",
             "Clear skies and a light north wind, with a start temperature near six degrees."),
            ("Elite field announced", "runnersweek.example/elite-field",
             "Organizers named the invited runners for the men's and women's races."),
            ("Spectator guide", "tokyo-marathon.example/spectators",
             "The best places to watch are near the river bridges and the last two kilometers."),
        ],
        "ja": [
            ("初めてのマラソンの練習法", "runcoach.example/first-marathon",
             "週3回の軽いラン、1回のロング走、1日の休養を16週間続ける計画。"),
            ("東京マラソンのコース図", "tokyo-marathon.example/course",
             "都庁をスタートし、古い商店街を通って駅の近くでゴールする。"),
            ("今年のおすすめランニングシューズ", "gearlab.example/shoes",
             "20足をクッション性、重さ、濡れた路面でのグリップで比べた。"),
            ("マラソン当日の交通規制", "city.example/closures",
             "中心部の幹線道路は早朝から午後まで通行止めになる。"),
            ("マラソンの補給ガイド", "fuelrun.example/guide",
             "45分ごとにジェルをとり、給水所は1つおきに利用する。"),
            ("東京マラソンのボランティア募集", "tokyo-marathon.example/volunteer",
             "給水、ランナーの誘導、ゴール付近の手伝いをする。"),
            ("レース当日朝の天気", "weather.example/tokyo",
             "快晴で北風は弱く、スタート時の気温は6度前後。"),
            ("招待選手が発表", "runnersweek.example/elite-field",
             "主催者が男女の招待選手を発表した。"),
            ("観戦ガイド", "tokyo-marathon.example/spectators",
             "おすすめの観戦場所は川の橋の近くと最後の2キロ。"),
        ],
    },
}
# The answer hit's place among the 10 hits, by position. The distractor is always hit 2.
_SEARCH_HIT = {"early": 1, "mid": 5, "late": 9}


def _page(topic: dict, lang: str, position: str) -> str:
    """Filler paragraphs to the page size, with the distractor near the start and the answer at its position."""
    size = _PAGE_CHARS[lang]
    sentences = topic["filler"][lang]
    gap = "" if lang == "ja" else " "
    paragraphs: list[str] = []
    length = 0
    i = 0
    while length < size:
        para = gap.join(sentences[(i + k) % len(sentences)] for k in range(3))
        paragraphs.append(para)
        length += len(para) + 2
        i += 1
    marks = {_DISTRACTOR_AT: topic["distractor"][lang], _AT[position]: topic["answer"][lang]}
    for share in sorted(marks, reverse=True):
        # Insert at the paragraph boundary nearest the share, counted on the pages so far.
        target = share * length
        run = 0
        at = len(paragraphs)
        for index, para in enumerate(paragraphs):
            if run >= target:
                at = index
                break
            run += len(para) + 2
        paragraphs.insert(at, marks[share])
    text = "\n\n".join(paragraphs)
    if len(text) > size:
        # The same cut and note as fetched_text, so the page looks like a real http_get result.
        text = text[:size] + f"\n[Cut: the body was longer. This is only the first part, at most {size} characters.]"
    return text


def _search(lang: str, position: str) -> str:
    """Ten hits in format_hits style: the distractor at hit 2 and the answer at its position."""
    hits = list(_SEARCH["filler"][lang])
    # Insert the earlier hit first. An answer at hit 1, inserted after the distractor, would push it to hit 3.
    placed = [(1, _SEARCH["distractor"][lang]),
              (_SEARCH_HIT[position] - 1, _SEARCH["answer"][lang])]
    for at, hit in sorted(placed):
        hits.insert(at, hit)
    blocks = []
    for number, (title, url, snippet) in enumerate(hits[:10], start=1):
        while len(snippet) < _SNIPPET_CHARS[lang]:
            snippet += _PAD[lang]
        snippet = snippet[: _SNIPPET_CHARS[lang]].rstrip()
        blocks.append(f"{number}. {title}\n   https://{url}\n   {snippet}")
    return "\n".join(blocks)


# Spoken forms the persona uses: number words, kanji numerals, and common misspellings. Matched after _flat.
_SPOKEN = {
    "season": ("june twelfth", "twelfth of june", "六月十二日"),
    "library": ("five-thirty", "five thirty", "half five", "五時三十分", "五時半", "十七時三十分", "十七時半"),
    "ferry": ("six-forty", "six forty", "twenty to seven", "六時四十分", "十八時四十分", "18時40"),
    "bread": ("forty-two", "fourty-two", "forty two", "四十二分"),
    "marathon": (),
}


def _flat(text: str) -> str:
    """Lowercase with spaces and hyphens removed, so "6 月 12 日" and "five-thirty" match their keys."""
    return "".join(ch for ch in text.lower() if not ch.isspace() and ch not in "-‐–")


def says_answer(case_id: str, keys: tuple[str, ...], reply: str) -> bool:
    """True when the reply names the answer in any written or spoken form."""
    flat = _flat(reply)
    forms = keys + _SPOKEN[case_id.split("-", 1)[0]]
    return any(_flat(form) in flat for form in forms)


def answer_offset(text: str, keys: tuple[str, ...]) -> int:
    """Characters before the first answer key in a result. -1 when none is found."""
    found = [text.find(key) for key in keys if key in text]
    return min(found) if found else -1


def cases() -> list[Case]:
    out: list[Case] = []
    for name, topic in _PAGES.items():
        for position in POSITIONS:
            for lang in ("en", "ja"):
                out.append(Case(f"{name}-{position}-{lang}", lang, topic["line"][lang], "any",
                                frozenset({"http_get"}), topic["keys"],
                                {"http_get": _page(topic, lang, position)}))
    for position in POSITIONS:
        for lang in ("en", "ja"):
            out.append(Case(f"marathon-{position}-{lang}", lang, _SEARCH["line"][lang], "any",
                            frozenset({"web_search"}), _SEARCH["keys"],
                            {"web_search": _search(lang, position)}))
    return out


def wrong_marks(case_id: str) -> tuple[str, ...]:
    """The distractor's values for a case: saying one of these without the answer is a wrong answer."""
    topic = case_id.split("-", 1)[0]
    return _SEARCH["wrong"] if topic == "marathon" else _PAGES[topic]["wrong"]


def position(case_id: str) -> str:
    return case_id.split("-")[1]
