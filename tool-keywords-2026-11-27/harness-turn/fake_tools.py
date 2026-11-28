"""Fake tools for scaling the tool keyword bench (#154). The intent check reads only a tool's name and description,
so these never run. They stand in for module tools a companion could have.

None of them does what a bench line asks: no clock, reminder, timer, web search or page fetch. A few sit near
those (calendar, to-do, notes), so they test confusion as the list grows. Picking one counts as a stray tool.
Keywords were written from each tool's own job, without reading the bench lines.
"""

from __future__ import annotations

import random

from cetimind.core.tools import ToolSpec

_QUERY = {"type": "object", "properties": {"text": {"type": "string"}}, "additionalProperties": False}

# name, description, keywords (any language, flat).
_FAKES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "music_play",
        "Play a song, album, or playlist on the speaker.",
        ("play", "song", "music", "playlist", "曲", "音楽", "流して"),
    ),
    ("music_pause", "Pause or resume the music that is playing.", ("pause", "resume", "一時停止", "止めて")),
    ("music_skip", "Skip to the next or previous track.", ("skip", "next track", "次の曲", "スキップ")),
    ("volume_set", "Set the speaker volume from 0 to 100.", ("volume", "louder", "quieter", "音量", "うるさい")),
    (
        "lights_set",
        "Turn room lights on or off, or set brightness.",
        ("light", "lamp", "brightness", "電気", "照明", "ライト"),
    ),
    ("lights_color", "Set the color of a room's smart lights.", ("light color", "colour", "ライトの色")),
    (
        "thermostat_set",
        "Set the heating or cooling target temperature.",
        ("thermostat", "heating", "air conditioning", "エアコン", "暖房", "冷房"),
    ),
    ("door_lock", "Lock or unlock a smart door lock.", ("lock the door", "unlock", "鍵", "ロック")),
    ("vacuum_start", "Start or stop the robot vacuum.", ("vacuum", "roomba", "掃除機", "ルンバ")),
    ("camera_snapshot", "Take a snapshot from a home camera.", ("camera", "snapshot", "カメラ")),
    ("note_add", "Save a short note.", ("note", "jot", "メモ")),
    ("note_list", "List saved notes.", ("my notes", "メモ一覧")),
    ("note_delete", "Delete a saved note by id.", ("delete note", "メモを消して")),
    ("todo_add", "Add an item to the to-do list.", ("to-do", "todo", "task list", "やること", "タスク")),
    ("todo_done", "Mark a to-do item as done.", ("done with", "finished the task", "完了")),
    ("todo_list", "List open to-do items.", ("what's on my list", "to-do list", "やることリスト")),
    ("shopping_add", "Add an item to the shopping list.", ("shopping list", "grocery", "買い物リスト")),
    ("shopping_list", "Show the shopping list.", ("what do i need to buy", "買い物リストを見せて")),
    (
        "calendar_add_event",
        "Add an event to the calendar with a date and time.",
        ("calendar", "event", "appointment", "meeting", "予定", "カレンダー", "会議"),
    ),
    ("calendar_list", "List calendar events for a day.", ("my schedule", "what's on", "今日の予定")),
    ("email_send", "Send an email to a contact.", ("email", "mail", "メール")),
    ("email_list", "List recent unread emails.", ("inbox", "unread", "受信箱", "未読")),
    ("message_send", "Send a chat message to a contact.", ("text", "message", "dm", "メッセージ", "送って")),
    ("call_start", "Start a voice call with a contact.", ("call", "phone", "電話")),
    ("contacts_find", "Look up a contact's details.", ("contact", "phone number", "連絡先", "電話番号")),
    (
        "translate_text",
        "Translate text into another language.",
        ("translate", "in english", "in japanese", "翻訳", "英語で"),
    ),
    ("define_word", "Give the dictionary meaning of a word.", ("define", "meaning of", "dictionary", "意味", "辞書")),
    (
        "calculator",
        "Evaluate an arithmetic expression.",
        ("calculate", "plus", "minus", "times", "divided", "計算", "足す"),
    ),
    (
        "unit_convert",
        "Convert between units, such as km and miles.",
        ("convert", "miles", "kilograms", "fahrenheit", "換算", "変換"),
    ),
    (
        "currency_convert",
        "Convert an amount between currencies at a stored rate.",
        ("dollars", "yen", "euros", "円", "ドル"),
    ),
    ("dice_roll", "Roll dice or flip a coin.", ("roll", "dice", "coin", "サイコロ", "コイン")),
    (
        "random_pick",
        "Pick one item at random from a list.",
        ("pick one", "choose for me", "random", "選んで", "ランダム"),
    ),
    ("joke_tell", "Return a random joke.", ("joke", "funny", "冗談", "ジョーク")),
    ("quote_daily", "Return an inspirational quote.", ("quote", "inspire", "名言")),
    (
        "recipe_find",
        "Find a recipe from saved cookbooks by dish or ingredient.",
        ("recipe", "how do i cook", "レシピ", "作り方"),
    ),
    ("pantry_list", "List what is stored in the pantry.", ("pantry", "fridge", "冷蔵庫", "食材")),
    ("habit_log", "Log a habit, such as exercise or reading, for today.", ("habit", "log my", "習慣", "記録")),
    ("habit_stats", "Show habit streaks and counts.", ("streak", "how many days", "連続")),
    ("mood_log", "Log the user's mood with a short note.", ("mood", "feeling", "気分")),
    ("sleep_log", "Log bedtime and wake time.", ("slept", "sleep log", "睡眠", "寝た")),
    # podcast_play replaced water_log, which was a fair pick for a "drink some water" line the bench scores as none.
    ("podcast_play", "Play an episode of a podcast.", ("podcast", "episode", "ポッドキャスト")),
    ("steps_today", "Return today's step count from the phone.", ("steps", "歩数")),
    ("photo_find", "Find photos by date or place.", ("photo", "picture", "写真")),
    ("photo_share", "Share a photo with a contact.", ("share the photo", "写真を送って")),
    ("game_start", "Start a small word or trivia game.", ("game", "trivia", "quiz", "ゲーム", "クイズ")),
    ("story_tell", "Tell a short bedtime story.", ("story", "bedtime", "お話", "物語")),
    ("poem_write", "Write a short poem on a theme.", ("poem", "haiku", "詩", "俳句")),
    ("drawing_make", "Make a simple drawing from a description.", ("draw", "sketch", "絵を描いて")),
    ("file_find", "Find a file on the computer by name.", ("file", "folder", "ファイル", "フォルダ")),
    ("app_open", "Open an app on the computer.", ("open the app", "launch", "起動", "アプリを開いて")),
    ("screen_shot", "Take a screenshot of the computer screen.", ("screenshot", "スクショ")),
    ("clipboard_read", "Read the text on the clipboard.", ("clipboard", "クリップボード")),
    ("battery_status", "Return the phone and laptop battery level.", ("battery", "charge", "バッテリー", "充電")),
    ("wifi_status", "Return the Wi-Fi network and signal strength.", ("wifi", "wi-fi", "signal", "ネット繋がって")),
    ("package_track", "Track a parcel by tracking number.", ("package", "parcel", "delivery", "荷物", "配達")),
    ("expense_add", "Log an expense with an amount and category.", ("spent", "expense", "出費", "使った")),
    ("budget_status", "Show this month's spending against budget.", ("budget", "予算")),
    ("plant_water_log", "Log that a plant was watered.", ("watered the plant", "plant", "植物", "水やり")),
    ("pet_feed_log", "Log that the pet was fed.", ("fed the cat", "fed the dog", "pet", "餌", "ペット")),
    ("journal_prompt", "Give a journaling prompt for the evening.", ("journaling prompt", "日記のお題")),
)

FAKE_TOOLS: tuple[ToolSpec, ...] = tuple(
    ToolSpec(name=name, description=description, parameters=_QUERY, group="fake") for name, description, _ in _FAKES
)
FAKE_KEYWORDS: dict[str, tuple[str, ...]] = {name: words for name, _, words in _FAKES}


def fake_tools(count: int, seed: int = 20261127) -> tuple[ToolSpec, ...]:
    """count fake tools, the same ones for a seed, in a mixed order so each size spans the domains."""
    order = list(FAKE_TOOLS)
    random.Random(seed).shuffle(order)
    return tuple(order[:count])
