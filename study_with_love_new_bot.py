import logging
import random
import sqlite3
import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from math import gcd
from zoneinfo import ZoneInfo

from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

TOKEN = "9130330555:AAFShmgLR70vXdORodDJqnCibtVaivKCPNo"
ADMIN_ID = 844782548  # Telegram ID администратора для отчётов и проверки фото.
TZ = ZoneInfo("Asia/Baku")
DB_NAME = "study_with_love.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📐 Математика", "📚 Повторить темы"],
        ["📊 Мой прогресс", "📅 Дни занятий"],
        ["💌 Послание"],
    ],
    resize_keyboard=True,
)

MESSAGES = [
    "Ты большая умничка! ❤️ Я горжусь твоими стараниями.",
    "Даже один решённый пример — это шаг вперёд. 🌸",
    "У тебя получится, моя хорошая. Не торопись и верь в себя. 💗",
    "Ошибки — это часть обучения. Главное, что ты пробуешь! ❤️",
    "Ты умнее, чем иногда думаешь. Просто дай себе время. ✨",
    "Каждая тема делает тебя чуточку сильнее. 📚",
    "Я верю в тебя даже в те дни, когда ты сама сомневаешься. 💕",
    "Не обязательно быть идеальной. Достаточно не сдаваться. 🌷",
    "Маленькие шаги однажды приведут тебя к большой цели. ❤️",
    "Пусть сегодня получится хотя бы немного — это уже победа! 🏆",
    "Ты заслуживаешь похвалы за старания, а не только за результат. 💖",
    "Вдохни поглубже, улыбнись и реши следующий пример. 😊",
    "Умница! Твоя настойчивость обязательно принесёт результат. 🌟",
    "Не сравнивай свой путь с чужим. Ты идёшь в своём темпе. 💗",
    "Даже сложная задача становится легче по маленьким шагам. 🧩",
    "Я отправляю тебе немного поддержки и много любви. ❤️",
    "Сегодняшние усилия — это завтрашняя уверенность. 🌸",
    "Если устала, отдохни. Потом продолжишь, и всё получится. ☁️",
    "Ты можешь больше, чем тебе кажется. Я в тебя верю! 💪",
    "Ещё одна тема позади — ещё одна маленькая победа! 🎉",
    "Пусть математика сегодня будет к тебе добра. А ты — к себе. 💞",
    "Главное — не скорость, а то, что ты продолжаешь учиться. 📖",
    "Ты молодец уже потому, что находишь время для себя и учёбы. ❤️",
    "Не бойся трудных вопросов: именно они помогают расти. 🌱",
    "Каждый день ты строишь свою большую победу из маленьких шагов. 🏅",
    "Я знаю, что у тебя получится. Просто продолжай, моя умничка. 💝",
    "Пять минут занятий лучше, чем бесконечное откладывание. 😉",
    "Пусть сегодня будет повод сказать себе: «Я справилась!» 🌷",
    "Ты заслуживаешь спокойствия, отдыха и веры в свои силы. 💗",
    "Обнимаю на расстоянии и желаю тебе продуктивного дня! 🤗",
]

CHAPTERS = {
    "1️⃣ Натуральные числа и действия с ними": [
        "1.1. Натуральные числа",
        "1.2. Сравнение и упорядочивание",
        "1.3. Округление натуральных чисел",
        "1.4. Сложение и вычитание натуральных чисел",
        "1.5. Квадрат и куб натурального числа",
        "1.6. Умножение и деление натуральных чисел",
        "1.7. Числовые выражения",
        "1.8. Делители и кратные числа",
    ],
    "2️⃣ Обыкновенные дроби": [
        "2.1. Правильные и неправильные дроби",
        "2.2. Сравнение и упорядочивание",
        "2.3. Сложение и вычитание дробей с разными знаменателями",
        "2.4. Сложение смешанных чисел",
        "2.5. Вычитание смешанных чисел",
        "2.6. Умножение обыкновенных дробей",
        "2.7. Умножение смешанных чисел",
        "2.8. Деление обыкновенных дробей",
        "2.9. Деление смешанных чисел",
        "2.10. Нахождение части числа и числа по его части",
    ],
    "3️⃣ Десятичные дроби": [
        "3.1. Десятичные дроби",
        "3.2. Сравнение и упорядочивание",
        "3.3. Округление десятичных дробей",
        "3.4. Перевод обыкновенной дроби в десятичную и наоборот",
        "3.5. Сложение и вычитание десятичных дробей",
        "3.6. Умножение и деление десятичных дробей на степени числа 10",
        "3.7. Умножение десятичной дроби на натуральное число",
        "3.8. Умножение десятичных дробей",
        "3.9. Деление десятичной дроби на натуральное число",
        "3.10. Деление числа на десятичную дробь",
        "3.11. Действия над обыкновенными и десятичными дробями",
    ],
    "4️⃣ Процент": [
        "4.1. Процент, обыкновенная дробь, десятичная дробь",
        "4.2. Процент от числа",
        "4.3. Нахождение числа по проценту",
        "4.4. Увеличение и уменьшение величины на определённый процент",
    ],
}


# ---------------------------------------------------------------------------
# Настройки поведения
# ---------------------------------------------------------------------------
SESSION_MINUTES = 45          # сколько минут даётся на всю проверку
START_GRACE_MINUTES = 5       # если за это время после примеров нет ни одного ответа —
                              # администратор сразу получает уведомление «не приступила»
CHECK_INTERVAL_SECONDS = 20   # как часто бот сверяется с расписанием

RU_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
ALL_TOPICS = [t for topics in CHAPTERS.values() for t in topics]
CHAPTER_NAMES = list(CHAPTERS.keys())


# ---------------------------------------------------------------------------
# База данных
# ---------------------------------------------------------------------------
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                chat_id INTEGER PRIMARY KEY,
                completed INTEGER NOT NULL DEFAULT 0,
                last_topic TEXT,
                last_completed_date TEXT
            )
        """)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(progress)")}
        if "last_completed_date" not in columns:
            conn.execute("ALTER TABLE progress ADD COLUMN last_completed_date TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS completed_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                completed_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                plan_date TEXT NOT NULL,
                plan_time TEXT,
                topics TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'draft',
                UNIQUE(chat_id, plan_date)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)


def remember_user(update: Update):
    user = update.effective_user
    if not user or not update.effective_chat:
        return
    name = user.first_name or user.username or str(user.id)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO users (chat_id, name) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET name = excluded.name",
            (update.effective_chat.id, name),
        )


def display_name(chat_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT name FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
    return row[0] if row and row[0] else f"ученица ({chat_id})"


def get_progress(chat_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT completed, last_topic, last_completed_date "
            "FROM progress WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
    return row if row else (0, None, None)


def save_completed(chat_id, topics):
    """Одно засчитанное занятие; каждая тема попадает в список пройденных."""
    now = datetime.now(TZ)
    today = now.date().isoformat()
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO progress (chat_id, completed, last_topic, last_completed_date)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                completed = completed + 1,
                last_topic = excluded.last_topic,
                last_completed_date = excluded.last_completed_date
        """, (chat_id, topics[-1], today))
        for topic in topics:
            conn.execute(
                "INSERT INTO completed_topics (chat_id, topic, completed_at) VALUES (?, ?, ?)",
                (chat_id, topic, now.strftime("%Y-%m-%d %H:%M:%S")),
            )


def get_completed_topics(chat_id):
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute(
            "SELECT topic, completed_at FROM completed_topics "
            "WHERE chat_id = ? ORDER BY id DESC",
            (chat_id,),
        ).fetchall()
    return rows


# ---------------------------------------------------------------------------
# Расписание по неделям (хранится в базе, конкретные даты)
# ---------------------------------------------------------------------------
def get_plan(chat_id, day_iso):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT plan_time, topics, status FROM plan WHERE chat_id = ? AND plan_date = ?",
            (chat_id, day_iso),
        ).fetchone()
    if not row:
        return None
    return {"time": row[0], "topics": json.loads(row[1] or "[]"), "status": row[2]}


def save_plan(chat_id, day_iso, plan_time, topics):
    topics = sorted({t for t in topics if t in ALL_TOPICS}, key=ALL_TOPICS.index)
    status = "pending" if plan_time and topics else "draft"
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """INSERT INTO plan (chat_id, plan_date, plan_time, topics, status)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(chat_id, plan_date) DO UPDATE SET
                 plan_time = excluded.plan_time,
                 topics = excluded.topics,
                 status = excluded.status""",
            (chat_id, day_iso, plan_time, json.dumps(topics, ensure_ascii=False), status),
        )


def delete_plan(chat_id, day_iso):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM plan WHERE chat_id = ? AND plan_date = ?", (chat_id, day_iso))


def set_plan_status(plan_id, status):
    if plan_id is None:
        return
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE plan SET status = ? WHERE id = ?", (status, plan_id))


def get_week_plans(chat_id, start):
    end = start + timedelta(days=6)
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute(
            "SELECT plan_date, plan_time, topics, status FROM plan "
            "WHERE chat_id = ? AND plan_date BETWEEN ? AND ?",
            (chat_id, start.isoformat(), end.isoformat()),
        ).fetchall()
    return {
        r[0]: {"time": r[1], "topics": json.loads(r[2] or "[]"), "status": r[3]}
        for r in rows
    }


def today_date():
    return datetime.now(TZ).date()


def week_start(day):
    return day - timedelta(days=day.weekday())


def topic_key(topic):
    return topic.split()[0].rstrip(".")


STATUS_ICON = {"draft": "✏️", "pending": "🕒", "sent": "📝", "done": "✅", "missed": "❌"}


def week_view(chat_id, offset):
    start = week_start(today_date()) + timedelta(weeks=offset)
    end = start + timedelta(days=6)
    plans = get_week_plans(chat_id, start)
    rows = []
    for i in range(7):
        day = start + timedelta(days=i)
        plan = plans.get(day.isoformat())
        if plan:
            keys = ", ".join(topic_key(t) for t in plan["topics"]) or "темы?"
            label = (f"{STATUS_ICON.get(plan['status'], '▫️')} {RU_DAYS[i]} {day:%d.%m} · "
                     f"{plan['time'] or 'время?'} · {keys}")
        else:
            label = f"▫️ {RU_DAYS[i]} {day:%d.%m}"
        rows.append([InlineKeyboardButton(label, callback_data=f"pd_{day.isoformat()}")])
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton("◀️ Назад", callback_data=f"wk_{offset - 1}"))
    if offset != 0:
        nav.append(InlineKeyboardButton("Эта неделя", callback_data="wk_0"))
    if offset < 12:
        nav.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"wk_{offset + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("📋 Скопировать на следующую неделю",
                                      callback_data=f"pcopy_{offset}")])
    text = (
        f"📅 НЕДЕЛЯ {start:%d.%m} – {end:%d.%m}\n\n"
        "Нажми на день, чтобы выбрать темы и время занятия.\n"
        "🕒 — запланировано, ✏️ — не хватает темы или времени, "
        "📝 — идёт проверка, ✅ — зачтено, ❌ — не зачтено."
    )
    return text, InlineKeyboardMarkup(rows)


def day_menu(chat_id, day):
    plan = get_plan(chat_id, day.isoformat())
    topics = plan["topics"] if plan else []
    clock = plan["time"] if plan and plan["time"] else "не задано"
    status = plan["status"] if plan else None
    offset = (week_start(day) - week_start(today_date())).days // 7
    lines = [
        f"📅 {RU_DAYS[day.weekday()]}, {day:%d.%m.%Y}",
        "",
        f"🕒 Время: {clock}",
        "",
        "📚 Темы:",
    ]
    lines += [f"• {t}" for t in topics] if topics else ["не выбраны"]
    lines.append("")
    if status in ("sent", "done"):
        lines.append("Занятие этого дня уже началось — менять нельзя.")
        kb = [[InlineKeyboardButton("⬅️ К неделе", callback_data=f"wk_{offset}")]]
        return "\n".join(lines), InlineKeyboardMarkup(kb)
    if plan and plan["time"] and topics:
        lines.append("✅ В это время придут 3 примера именно по этим темам.")
    else:
        lines.append("Задай время и выбери хотя бы одну тему.")
    kb = [
        [InlineKeyboardButton("📚 Выбрать темы", callback_data=f"pc_{day.isoformat()}")],
        [InlineKeyboardButton("🕒 Задать время", callback_data=f"pt_{day.isoformat()}")],
        [InlineKeyboardButton("🗑 Очистить день", callback_data=f"px_{day.isoformat()}")],
        [InlineKeyboardButton("⬅️ К неделе", callback_data=f"wk_{offset}")],
    ]
    return "\n".join(lines), InlineKeyboardMarkup(kb)


def chapters_menu(day):
    rows = [
        [InlineKeyboardButton(name, callback_data=f"pch_{day.isoformat()}_{ci}")]
        for ci, name in enumerate(CHAPTER_NAMES)
    ]
    rows.append([InlineKeyboardButton("✅ Готово", callback_data=f"pd_{day.isoformat()}")])
    return "📚 Выбери раздел, затем отметь темы для этого дня:", InlineKeyboardMarkup(rows)


def topics_menu(chat_id, day, ci):
    plan = get_plan(chat_id, day.isoformat())
    chosen = set(plan["topics"]) if plan else set()
    chapter = CHAPTER_NAMES[ci]
    rows = []
    for ti, topic in enumerate(CHAPTERS[chapter]):
        mark = "✅" if topic in chosen else "▫️"
        rows.append([InlineKeyboardButton(f"{mark} {topic}",
                                          callback_data=f"pk_{day.isoformat()}_{ci}_{ti}")])
    rows.append([
        InlineKeyboardButton("⬅️ К разделам", callback_data=f"pc_{day.isoformat()}"),
        InlineKeyboardButton("✅ Готово", callback_data=f"pd_{day.isoformat()}"),
    ])
    return f"{chapter}\n\nОтметь темы (можно несколько):", InlineKeyboardMarkup(rows)


async def safe_edit(query, text, markup):
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except BadRequest as exc:
        if "not modified" not in str(exc).lower():
            raise


async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    parts = query.data.split("_")
    action = parts[0]

    if action == "wk":
        await query.answer()
        offset = max(0, min(int(parts[1]), 12))
        text, markup = week_view(chat_id, offset)
        await safe_edit(query, text, markup)
        return

    if action == "pcopy":
        offset = max(0, min(int(parts[1]), 12))
        start = week_start(today_date()) + timedelta(weeks=offset)
        copied = 0
        for day_iso, plan in get_week_plans(chat_id, start).items():
            if not (plan["time"] and plan["topics"]):
                continue
            target = date.fromisoformat(day_iso) + timedelta(days=7)
            if get_plan(chat_id, target.isoformat()):
                continue
            save_plan(chat_id, target.isoformat(), plan["time"], plan["topics"])
            copied += 1
        await query.answer(
            f"Скопировано дней: {copied}" if copied else "Нечего копировать "
            "(или дни следующей недели уже заполнены).",
            show_alert=True,
        )
        text, markup = week_view(chat_id, min(offset + 1, 12))
        await safe_edit(query, text, markup)
        return

    day = date.fromisoformat(parts[1])
    if day < today_date():
        await query.answer("Этот день уже прошёл.", show_alert=True)
        return
    plan = get_plan(chat_id, day.isoformat())
    if action != "pd" and plan and plan["status"] in ("sent", "done"):
        await query.answer("Занятие этого дня уже началось.", show_alert=True)
        return
    await query.answer()

    if action == "pd":
        text, markup = day_menu(chat_id, day)
    elif action == "pt":
        context.user_data["awaiting_plan_time"] = day.isoformat()
        await query.message.reply_text(
            f"Введи время для {RU_DAYS[day.weekday()]} {day:%d.%m} в формате ЧЧ:ММ, "
            "например 17:30."
        )
        return
    elif action == "px":
        delete_plan(chat_id, day.isoformat())
        text, markup = day_menu(chat_id, day)
    elif action == "pc":
        text, markup = chapters_menu(day)
    elif action == "pch":
        text, markup = topics_menu(chat_id, day, int(parts[2]))
    elif action == "pk":
        ci, ti = int(parts[2]), int(parts[3])
        topic = CHAPTERS[CHAPTER_NAMES[ci]][ti]
        topics = set(plan["topics"]) if plan else set()
        topics.symmetric_difference_update({topic})
        save_plan(chat_id, day.isoformat(), plan["time"] if plan else None, topics)
        text, markup = topics_menu(chat_id, day, ci)
    else:
        return
    await safe_edit(query, text, markup)


# ---------------------------------------------------------------------------
# Генераторы проверочных примеров по темам учебника
# ---------------------------------------------------------------------------
def rnd(a, b):
    return random.randint(a, b)


def fnum(n):
    return f"{n:,}".replace(",", "\u00a0")


def dec(x):
    """Fraction с конечной десятичной записью -> строка с запятой."""
    x = Fraction(x)
    d = Decimal(x.numerator) / Decimal(x.denominator)
    return format(d.normalize(), "f").replace(".", ",")


def round_nat(n, p):
    return (n + p // 2) // p * p


def round_dec(x, places):
    d = Decimal(x.numerator) / Decimal(x.denominator)
    q = Decimal(1).scaleb(-places)
    return Fraction(str(d.quantize(q, rounding=ROUND_HALF_UP)))


def pf(maxd=9):
    d = rnd(2, maxd)
    return rnd(1, d - 1), d


def mixed(maxd=8):
    d = rnd(2, maxd)
    return rnd(1, 5), rnd(1, d - 1), d


def mtxt(m):
    return f"{m[0]} {m[1]}/{m[2]}"


def mval(m):
    return Fraction(m[0] * m[2] + m[1], m[2])


def g_1_1():
    v = random.choice(["next", "prev", "digit", "compose"])
    if v == "next":
        n = rnd(100, 99998)
        return f"Какое число идёт сразу после {fnum(n)}?", n + 1
    if v == "prev":
        n = rnd(101, 99999)
        return f"Какое число стоит сразу перед {fnum(n)}?", n - 1
    if v == "digit":
        n = rnd(10000, 99999)
        place, div = random.choice([("тысяч", 1000), ("сотен", 100), ("десятков", 10)])
        return f"Какая цифра стоит в разряде {place} в числе {fnum(n)}?", (n // div) % 10
    a, b, c, d = rnd(1, 9), rnd(0, 9), rnd(0, 9), rnd(1, 9)
    return (f"Запиши число: {a} тысяч, {b} сотен, {c} десятков и {d} единиц.",
            1000 * a + 100 * b + 10 * c + d)


def g_1_2():
    v = random.choice(["max", "min", "between"])
    if v == "between":
        a = rnd(10, 500)
        b = a + rnd(4, 30)
        return f"Сколько натуральных чисел лежит между {a} и {b} (сами числа не считаем)?", b - a - 1
    nums = random.sample(range(100, 9999), 4)
    s = ", ".join(str(n) for n in nums)
    if v == "max":
        return f"Какое из чисел наибольшее: {s}?", max(nums)
    return f"Какое из чисел наименьшее: {s}?", min(nums)


def g_1_3():
    p, name = random.choice([(10, "десятков"), (100, "сотен"), (1000, "тысяч")])
    n = rnd(1001, 99999)
    return f"Округли число {n} до {name}.", round_nat(n, p)


def g_1_4():
    if random.random() < 0.5:
        a, b = rnd(120, 9999), rnd(120, 9999)
        return f"{a} + {b} = ?", a + b
    a, b = rnd(1000, 9999), rnd(100, 999)
    return f"{a} − {b} = ?", a - b


def g_1_5():
    v = random.choice(["sq", "cube", "mix"])
    if v == "sq":
        a = rnd(2, 20)
        return f"Чему равен квадрат числа {a}?", a * a
    if v == "cube":
        a = rnd(2, 7)
        return f"Чему равен куб числа {a}?", a ** 3
    a, b = rnd(2, 9), rnd(2, 5)
    return f"Найди значение выражения: {a}² + {b}³", a * a + b ** 3


def g_1_6():
    v = random.choice(["m1", "m2", "d"])
    if v == "m1":
        a, b = rnd(12, 99), rnd(3, 9)
        return f"{a} × {b} = ?", a * b
    if v == "m2":
        a, b = rnd(12, 45), rnd(11, 29)
        return f"{a} × {b} = ?", a * b
    q, b = rnd(12, 99), rnd(3, 12)
    return f"{q * b} ÷ {b} = ?", q


def g_1_7():
    a, b, c = rnd(2, 12), rnd(2, 12), rnd(2, 12)
    v = rnd(0, 3)
    if v == 0:
        return f"{a} + {b} × {c} = ?", a + b * c
    if v == 1:
        return f"({a} + {b}) × {c} = ?", (a + b) * c
    if v == 2:
        c2 = rnd(1, a * b - 1)
        return f"{a} × {b} − {c2} = ?", a * b - c2
    return f"{a * b} ÷ {b} + {c} = ?", a + c


def g_1_8():
    v = random.choice(["count", "gcd", "lcm", "mult"])
    if v == "count":
        n = random.choice([12, 16, 18, 20, 24, 28, 30, 36, 40, 42, 48, 60])
        return f"Сколько всего делителей у числа {n}?", sum(1 for d in range(1, n + 1) if n % d == 0)
    if v == "gcd":
        while True:
            g = rnd(2, 9)
            a, b = g * rnd(2, 6), g * rnd(2, 6)
            if a != b:
                break
        return f"Найди наибольший общий делитель чисел {a} и {b}.", gcd(a, b)
    if v == "lcm":
        a, b = random.choice([(4, 6), (6, 8), (6, 9), (10, 15), (12, 18), (8, 12),
                              (4, 10), (9, 12), (15, 20), (6, 10)])
        return f"Найди наименьшее общее кратное чисел {a} и {b}.", a * b // gcd(a, b)
    k, n = rnd(3, 15), rnd(4, 9)
    return f"Найди {n}-е по счёту кратное числа {k}.", n * k


def g_2_1():
    v = random.choice(["improper", "whole", "count"])
    if v == "improper":
        m = mixed()
        return f"Запиши смешанное число {mtxt(m)} в виде неправильной дроби.", mval(m)
    if v == "whole":
        d = rnd(2, 9)
        while True:
            p = rnd(d + 1, 9 * d)
            if p % d:
                break
        return f"Сколько целых содержится в неправильной дроби {p}/{d}?", p // d
    fracs = []
    while len(fracs) < 6:
        n, d = rnd(1, 12), rnd(2, 9)
        if n != d:
            fracs.append((n, d))
    txt = ", ".join(f"{n}/{d}" for n, d in fracs)
    return f"Сколько правильных дробей среди: {txt}?", sum(1 for n, d in fracs if n < d)


def g_2_2():
    while True:
        pairs = [pf(12) for _ in range(3)]
        vals = [Fraction(n, d) for n, d in pairs]
        if len(set(vals)) == 3:
            break
    txt = ", ".join(f"{n}/{d}" for n, d in pairs)
    v = random.choice(["max", "min", "mid"])
    if v == "max":
        return f"Какая из дробей наибольшая: {txt}?", max(vals)
    if v == "min":
        return f"Какая из дробей наименьшая: {txt}?", min(vals)
    return f"Какая из дробей средняя по величине: {txt}?", sorted(vals)[1]


def g_2_3():
    while True:
        (a, b), (c, d) = pf(9), pf(9)
        x, y = Fraction(a, b), Fraction(c, d)
        if b != d and x != y:
            break
    if random.random() < 0.5:
        return f"{a}/{b} + {c}/{d} = ?", x + y
    if x < y:
        a, b, c, d = c, d, a, b
        x, y = y, x
    return f"{a}/{b} − {c}/{d} = ?", x - y


def g_2_4():
    m1, m2 = mixed(), mixed()
    return f"{mtxt(m1)} + {mtxt(m2)} = ? (ответ — неправильной дробью)", mval(m1) + mval(m2)


def g_2_5():
    while True:
        m1, m2 = mixed(), mixed()
        if mval(m1) > mval(m2):
            break
    return f"{mtxt(m1)} − {mtxt(m2)} = ? (ответ — неправильной дробью)", mval(m1) - mval(m2)


def g_2_6():
    (a, b), (c, d) = pf(9), pf(9)
    return f"{a}/{b} × {c}/{d} = ?", Fraction(a, b) * Fraction(c, d)


def g_2_7():
    m1, m2 = mixed(6), mixed(6)
    return f"{mtxt(m1)} × {mtxt(m2)} = ? (ответ — неправильной дробью)", mval(m1) * mval(m2)


def g_2_8():
    (a, b), (c, d) = pf(9), pf(9)
    return f"{a}/{b} ÷ {c}/{d} = ?", Fraction(a, b) / Fraction(c, d)


def g_2_9():
    m1, m2 = mixed(6), mixed(6)
    return f"{mtxt(m1)} ÷ {mtxt(m2)} = ? (ответ — неправильной дробью)", mval(m1) / mval(m2)


def g_2_10():
    d = rnd(2, 9)
    n = rnd(1, d - 1)
    k = rnd(2, 12)
    if random.random() < 0.5:
        return f"Найди {n}/{d} от числа {d * k}.", n * k
    return f"{n}/{d} некоторого числа равны {n * k}. Найди это число.", d * k


def g_3_1():
    v = random.choice(["tofrac", "digit", "compose"])
    if v == "tofrac":
        den = random.choice([10, 100, 1000])
        n = rnd(1, den - 1)
        return f"Запиши обыкновенную дробь {n}/{den} в виде десятичной.", Fraction(n, den)
    if v == "digit":
        n = rnd(10000, 99999)
        frac_part = f"{n % 1000:03d}"
        s = f"{n // 1000},{frac_part}"
        place, idx = random.choice([("десятых", 0), ("сотых", 1), ("тысячных", 2)])
        return f"Какая цифра стоит в разряде {place} в числе {s}?", int(frac_part[idx])
    w, h = rnd(1, 30), rnd(1, 9)
    return f"Запиши десятичной дробью: {w} целых и {h} сотых.", w + Fraction(h, 100)


def g_3_2():
    while True:
        base = rnd(1, 9)
        vals = [base + Fraction(rnd(1, 99), 100),
                base + Fraction(rnd(1, 9), 10),
                base + Fraction(rnd(1, 999), 1000)]
        if len(set(vals)) == 3:
            break
    txt = "; ".join(dec(x) for x in vals)
    if random.random() < 0.5:
        return f"Какое из чисел наибольшее: {txt}?", max(vals)
    return f"Какое из чисел наименьшее: {txt}?", min(vals)


def g_3_3():
    places, name = random.choice([(0, "целых"), (1, "десятых"), (2, "сотых")])
    x = Fraction(rnd(1000, 99999), 1000)
    return f"Округли число {dec(x)} до {name}.", round_dec(x, places)


def g_3_4():
    if random.random() < 0.5:
        d = random.choice([2, 4, 5, 8, 10, 20, 25, 50])
        n = rnd(1, d - 1)
        return f"Запиши дробь {n}/{d} в виде десятичной.", Fraction(n, d)
    x = Fraction(rnd(1, 99), 100)
    return f"Запиши десятичную дробь {dec(x)} в виде обыкновенной (можно сократить).", x


def g_3_5():
    a = Fraction(rnd(10, 9999), 100)
    b = Fraction(rnd(10, 9999), random.choice([10, 100]))
    if random.random() < 0.5:
        return f"{dec(a)} + {dec(b)} = ?", a + b
    if a == b:
        a += 1
    if a < b:
        a, b = b, a
    return f"{dec(a)} − {dec(b)} = ?", a - b


def g_3_6():
    p = random.choice([10, 100, 1000])
    x = Fraction(rnd(1, 99999), random.choice([1, 10, 100, 1000]))
    if random.random() < 0.5:
        return f"{dec(x)} × {p} = ?", x * p
    return f"{dec(x)} ÷ {p} = ?", x / p


def g_3_7():
    x = Fraction(rnd(11, 999), random.choice([10, 100]))
    k = rnd(2, 9)
    return f"{dec(x)} × {k} = ?", x * k


def g_3_8():
    a = Fraction(rnd(2, 99), 10)
    b = Fraction(rnd(2, 99), random.choice([10, 100]))
    return f"{dec(a)} × {dec(b)} = ?", a * b


def g_3_9():
    r = Fraction(rnd(11, 999), random.choice([10, 100]))
    k = rnd(2, 9)
    return f"{dec(r * k)} ÷ {k} = ?", r


def g_3_10():
    dv = random.choice([Fraction(2, 10), Fraction(4, 10), Fraction(5, 10), Fraction(6, 10),
                        Fraction(8, 10), Fraction(15, 10), Fraction(25, 10),
                        Fraction(25, 100), Fraction(5, 100), Fraction(12, 100)])
    q = rnd(2, 40)
    return f"{dec(q * dv)} ÷ {dec(dv)} = ?", q


def g_3_11():
    while True:
        n, d = random.choice([(1, 2), (1, 4), (3, 4), (1, 5), (2, 5), (3, 5), (4, 5),
                              (1, 8), (3, 8), (1, 10), (7, 10), (1, 20)])
        y = Fraction(rnd(1, 99), 100)
        frac = Fraction(n, d)
        if frac != y:
            break
    op = random.choice(["+", "−", "×"])
    if op == "+":
        return f"{n}/{d} + {dec(y)} = ? (ответ — дробью, обыкновенной или десятичной)", frac + y
    if op == "−":
        if frac > y:
            return f"{n}/{d} − {dec(y)} = ? (ответ — обыкновенной или десятичной дробью)", frac - y
        return f"{dec(y)} − {n}/{d} = ? (ответ — обыкновенной или десятичной дробью)", y - frac
    return f"{n}/{d} × {dec(y)} = ? (ответ — обыкновенной или десятичной дробью)", frac * y


def g_4_1():
    v = random.choice(["pf", "pd", "fp", "dp"])
    if v in ("pf", "pd"):
        p = random.choice([5, 10, 12, 15, 20, 25, 35, 40, 50, 60, 75, 80])
        if v == "pf":
            return f"Запиши {p}% в виде обыкновенной дроби.", Fraction(p, 100)
        return f"Запиши {p}% в виде десятичной дроби.", Fraction(p, 100)
    if v == "fp":
        n, d = random.choice([(1, 2), (1, 4), (3, 4), (1, 5), (2, 5), (3, 5), (4, 5),
                              (1, 10), (3, 10), (1, 20), (3, 20), (7, 20), (1, 25)])
        return f"Запиши дробь {n}/{d} в процентах (число без знака %).", Fraction(n, d) * 100
    x = Fraction(rnd(1, 99), 100)
    return f"Запиши десятичную дробь {dec(x)} в процентах (число без знака %).", x * 100


def g_4_2():
    p = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80])
    n = 20 * rnd(2, 40)
    return f"Найди {p}% от числа {n}.", Fraction(p * n, 100)


def g_4_3():
    p = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80])
    n = 20 * rnd(2, 40)
    return f"{p}% некоторого числа равны {p * n // 100}. Найди это число.", n


def g_4_4():
    n = 20 * rnd(2, 40)
    p = random.choice([5, 10, 15, 20, 25, 30, 40, 50])
    v = rnd(0, 3)
    if v == 0:
        return f"Число {n} увеличили на {p}%. Какое число получилось?", Fraction(n * (100 + p), 100)
    if v == 1:
        return f"Число {n} уменьшили на {p}%. Какое число получилось?", Fraction(n * (100 - p), 100)
    if v == 2:
        return (f"Товар стоил {n} манатов. Цену повысили на {p}%. "
                "Сколько манатов стоит товар теперь?"), Fraction(n * (100 + p), 100)
    return (f"Товар стоил {n} манатов. Цену снизили на {p}%. "
            "Сколько манатов стоит товар теперь?"), Fraction(n * (100 - p), 100)


GENERATORS = {
    "1.1": g_1_1, "1.2": g_1_2, "1.3": g_1_3, "1.4": g_1_4,
    "1.5": g_1_5, "1.6": g_1_6, "1.7": g_1_7, "1.8": g_1_8,
    "2.1": g_2_1, "2.2": g_2_2, "2.3": g_2_3, "2.4": g_2_4, "2.5": g_2_5,
    "2.6": g_2_6, "2.7": g_2_7, "2.8": g_2_8, "2.9": g_2_9, "2.10": g_2_10,
    "3.1": g_3_1, "3.2": g_3_2, "3.3": g_3_3, "3.4": g_3_4, "3.5": g_3_5,
    "3.6": g_3_6, "3.7": g_3_7, "3.8": g_3_8, "3.9": g_3_9, "3.10": g_3_10,
    "3.11": g_3_11,
    "4.1": g_4_1, "4.2": g_4_2, "4.3": g_4_3, "4.4": g_4_4,
}


def make_questions(topics):
    """3 примера строго по выбранным темам (по кругу, если тем несколько)."""
    keys = [topic_key(t) for t in topics if topic_key(t) in GENERATORS]
    if not keys:
        return []
    random.shuffle(keys)
    questions, seen, i = [], set(), 0
    while len(questions) < 3 and i < 60:
        text, value = GENERATORS[keys[i % len(keys)]]()
        i += 1
        if text in seen:
            continue
        seen.add(text)
        questions.append((text, Fraction(value)))
    return questions


def parse_number(token):
    t = token.strip().rstrip("%").replace(",", ".").replace("−", "-")
    try:
        return Fraction(t)
    except (ValueError, ZeroDivisionError):
        return None


def check_answers(questions, text):
    tokens = [t.strip(",;") for t in text.replace(";", " ").split()]
    tokens = [t for t in tokens if t]
    if len(tokens) != len(questions):
        return None
    return [parse_number(tok) == answer for tok, (_, answer) in zip(tokens, questions)]


# ---------------------------------------------------------------------------
# Проверка: сессии, планировщик, уведомления администратору
# ---------------------------------------------------------------------------
def examples_text(session, scheduled):
    body = "\n".join(f"{i}. {q}" for i, (q, _) in enumerate(session["questions"], 1))
    topics = "\n".join(f"• {t}" for t in session["topics"])
    head = "⏰ ВРЕМЯ ЗАНЯТИЯ!" if scheduled else "📝 ПРОВЕРОЧНЫЕ ПРИМЕРЫ"
    return (
        f"{head}\n\n"
        f"Темы:\n{topics}\n\n"
        f"{body}\n\n"
        "Отправь три ответа одним сообщением через пробел.\n"
        "Дроби пиши через «/» (например 7/12), смешанные числа — неправильной дробью, "
        "десятичные — через запятую (3,5).\n\n"
        "После трёх правильных ответов пришли фото решения в тетради. "
        f"На всё даётся {SESSION_MINUTES} минут. ❤️"
    )


def cancel_jobs(context, chat_id):
    for name in (f"deadline_{chat_id}", f"startcheck_{chat_id}"):
        for job in context.job_queue.get_jobs_by_name(name):
            job.schedule_removal()


async def begin_session(context, chat_id, topics, plan_id=None):
    """Сразу отправляет 3 примера по выбранным темам. True — примеры отправлены."""
    sessions = context.application.bot_data.setdefault("active_sessions", {})
    session = sessions.get(chat_id)
    scheduled = plan_id is not None

    if session and session.get("stage") == "review":
        if not scheduled:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Твоё фото уже у администратора. Дождись его решения. ❤️",
                reply_markup=MAIN_KEYBOARD,
            )
        return False

    if session and not scheduled:
        if session.get("stage") == "photo":
            await context.bot.send_message(
                chat_id=chat_id,
                text="Примеры уже решены правильно. Пришли фото решения в тетради. 📸",
                reply_markup=MAIN_KEYBOARD,
            )
            return True
        if session.get("stage") == "answers":
            await context.bot.send_message(
                chat_id=chat_id, text=examples_text(session, False),
                reply_markup=MAIN_KEYBOARD,
            )
            return True

    questions = make_questions(topics)
    if not questions:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Для этой темы пока нет примеров. Выбери тему из списка. 🌸",
            reply_markup=MAIN_KEYBOARD,
        )
        return False

    cancel_jobs(context, chat_id)
    token = datetime.now(TZ).isoformat()
    session = {
        "questions": questions,
        "stage": "answers",
        "token": token,
        "topics": list(topics),
        "plan_id": plan_id,
        "engaged": False,
        "alerted": False,
    }
    sessions[chat_id] = session
    await context.bot.send_message(
        chat_id=chat_id, text=examples_text(session, scheduled),
        reply_markup=MAIN_KEYBOARD,
    )
    context.job_queue.run_once(
        session_deadline, when=SESSION_MINUTES * 60, chat_id=chat_id,
        data=token, name=f"deadline_{chat_id}",
    )
    if scheduled:
        context.job_queue.run_once(
            start_check, when=START_GRACE_MINUTES * 60, chat_id=chat_id,
            data=token, name=f"startcheck_{chat_id}",
        )
    return True


async def check_plan(context: ContextTypes.DEFAULT_TYPE):
    """Раз в несколько секунд сверяется с расписанием и запускает занятия."""
    now = datetime.now(TZ)
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute(
            "SELECT id, chat_id, plan_date, plan_time, topics FROM plan WHERE status = 'pending'"
        ).fetchall()
    for plan_id, chat_id, day_iso, clock, topics_json in rows:
        try:
            when = datetime.fromisoformat(f"{day_iso}T{clock}").replace(tzinfo=TZ)
            if when > now:
                continue
            if now - when > timedelta(minutes=SESSION_MINUTES):
                set_plan_status(plan_id, "missed")
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"⚠️ Занятие {display_name(chat_id)} на {day_iso} {clock} не состоялось: "
                         "бот не был запущен в это время.",
                )
                continue
            if await begin_session(context, chat_id, json.loads(topics_json), plan_id=plan_id):
                set_plan_status(plan_id, "sent")
                logger.info("Занятие запущено: chat=%s %s %s", chat_id, day_iso, clock)
        except Exception:
            logger.exception("Ошибка при запуске занятия plan_id=%s", plan_id)


async def start_check(context: ContextTypes.DEFAULT_TYPE):
    """Ученица не ответила на примеры — администратор узнаёт об этом сразу."""
    chat_id = context.job.chat_id
    sessions = context.application.bot_data.setdefault("active_sessions", {})
    session = sessions.get(chat_id)
    if (session and session.get("token") == context.job.data
            and session.get("stage") == "answers" and not session.get("engaged")):
        session["alerted"] = True
        topics = "; ".join(session["topics"])
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ {display_name(chat_id)} не приступила к занятию.\n"
                 f"Примеры отправлены {START_GRACE_MINUTES} мин назад, ответов нет.\n"
                 f"Темы: {topics}",
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text="Занятие уже началось, а ответов пока нет. Реши примеры и отправь ответы. ❤️",
        )


async def session_deadline(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    sessions = context.application.bot_data.setdefault("active_sessions", {})
    session = sessions.get(chat_id)
    if (session and session.get("token") == context.job.data
            and session.get("stage") in ("answers", "photo")):
        sessions.pop(chat_id, None)
        set_plan_status(session.get("plan_id"), "missed")
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏰ Время проверки истекло. Занятие не засчитано. "
                 "Если возникла уважительная причина, обсуди перенос с администратором.",
        )
        if session.get("engaged") or not session.get("alerted"):
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ ПРОПУСК ЗАНЯТИЯ\n{display_name(chat_id)} не завершила проверку "
                     f"за {SESSION_MINUTES} минут.\nТемы: {'; '.join(session['topics'])}",
            )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sessions = context.application.bot_data.setdefault("active_sessions", {})
    session = sessions.get(chat_id)
    if session and session.get("stage") == "review":
        await update.message.reply_text("Фото уже у администратора. Дождись его решения. ❤️")
        return
    if not session or session.get("stage") != "photo":
        await update.message.reply_text(
            "Сейчас бот не ожидает фото решения. Сначала пройди проверку примеров."
        )
        return

    session["engaged"] = True
    photo = update.message.photo[-1]
    caption = (
        "📸 Фото решения для проверки\n"
        f"Ученица: {display_name(chat_id)}\n"
        f"Темы: {'; '.join(session['topics'])}\n"
        "Проверь фото и выбери результат ниже."
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Принять", callback_data=f"review_ok_{chat_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"review_no_{chat_id}"),
    ]])
    sent = await context.bot.send_photo(
        chat_id=ADMIN_ID, photo=photo.file_id, caption=caption, reply_markup=keyboard,
    )
    session["stage"] = "review"
    session["review_message_id"] = sent.message_id
    await update.message.reply_text(
        "Фото отправлено администратору. Занятие пока не засчитано — "
        "ожидай его решения. ❤️"
    )


async def review_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("Эта кнопка доступна только администратору.", show_alert=True)
        return
    await query.answer()
    action, raw_chat_id = query.data.rsplit("_", 1)
    student_id = int(raw_chat_id)
    sessions = context.application.bot_data.setdefault("active_sessions", {})
    session = sessions.get(student_id)

    if action == "review_ok":
        topics = (session or {}).get("topics") or ["Проверочное занятие"]
        save_completed(student_id, topics)
        set_plan_status((session or {}).get("plan_id"), "done")
        sessions.pop(student_id, None)
        cancel_jobs(context, student_id)
        await context.bot.send_message(
            chat_id=student_id,
            text="🎉 Фото принято! Проверка пройдена, занятие засчитано. Молодец! ❤️",
        )
        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\n✅ Результат принят.",
            reply_markup=None,
        )
    elif action == "review_no":
        set_plan_status((session or {}).get("plan_id"), "missed")
        sessions.pop(student_id, None)
        cancel_jobs(context, student_id)
        await context.bot.send_message(
            chat_id=student_id,
            text="Фото пока не принято. Обсуди с администратором, что нужно исправить, "
                 "и нажми «✅ Я позанималась», чтобы пройти проверку заново.",
        )
        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\n❌ Фото отклонено.",
            reply_markup=None,
        )


def menu_texts():
    texts = {
        "📐 Математика", "📚 Повторить темы", "✅ Я позанималась", "📊 Мой прогресс",
        "⏳ Отложить", "❌ Не сделано", "💌 Послание", "📅 Дни занятий",
        "⬅️ К разделам", "⬅️ Главное меню",
    }
    texts.update(CHAPTERS)
    texts.update(ALL_TOPICS)
    return texts


MENU_TEXTS = menu_texts()


async def process_study_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sessions = context.application.bot_data.setdefault("active_sessions", {})
    session = sessions.get(chat_id)
    if not session or session.get("stage") != "answers":
        return False
    if update.message.text in MENU_TEXTS:
        return False

    session["engaged"] = True
    results = check_answers(session["questions"], update.message.text)
    if results is None:
        await update.message.reply_text(
            "Нужно ответить сразу на все примеры: отправь ответы одним сообщением "
            "через пробел, по порядку. ❤️"
        )
        return True
    if not all(results):
        marks = "  ".join(f"{i}. {'✅' if ok else '❌'}" for i, ok in enumerate(results, 1))
        await update.message.reply_text(
            f"{marks}\n\nЕсть ошибки. Пересчитай и отправь все ответы заново. ❤️"
        )
        return True

    session["stage"] = "photo"
    await update.message.reply_text(
        "✅ Все ответы правильные!\n\n"
        "Теперь пришли одно чёткое фото решения этих примеров в тетради. "
        "На фото должны быть видны записи и ответы. После этого я отправлю его администратору."
    )
    return True


# ---------------------------------------------------------------------------
# Клавиатуры и обработчики меню
# ---------------------------------------------------------------------------
def chapters_keyboard():
    return ReplyKeyboardMarkup(
        [[chapter] for chapter in CHAPTERS] + [["⬅️ Главное меню"]],
        resize_keyboard=True,
    )


def topics_keyboard(chapter):
    return ReplyKeyboardMarkup(
        [[topic] for topic in CHAPTERS[chapter]]
        + [["⬅️ К разделам", "⬅️ Главное меню"]],
        resize_keyboard=True,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)
    if update.effective_chat.id == ADMIN_ID:
        await update.message.reply_text(
            "Администратор подключён. Сюда будут приходить уведомления о пропусках "
            "и фотографии для проверки.",
            reply_markup=MAIN_KEYBOARD,
        )
        return
    await update.message.reply_text(
        "Привет, Назка! ❤️\n\n"
        "Я твой помощник в учёбе.\n\n"
        "В разделе «📅 Дни занятий» выбери день недели, темы и время — в это время "
        "я пришлю 3 примера именно по этим темам. После правильных ответов отправь фото "
        "решения в тетради.\n"
        "Фото проверяет администратор, и занятие засчитывается только после этого.\n"
        f"На выполнение отводится {SESSION_MINUTES} минут.\n\n"
        "Позаниматься можно и в любой момент: выбери тему в «📐 Математика» "
        "и нажми «✅ Я позанималась».",
        reply_markup=MAIN_KEYBOARD,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — открыть меню\n"
        "/help — помощь\n\n"
        "«📅 Дни занятий» — расписание по неделям: день, темы и время.\n"
        "«✅ Я позанималась» (после выбора темы) — примеры приходят сразу.\n"
        "Зачёт занятия требует правильных ответов на три примера и фото тетради. "
        "Бот должен быть запущен, чтобы напоминания приходили."
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text
    chat_id = update.effective_chat.id
    remember_user(update)

    if "awaiting_plan_time" in context.user_data:
        if text in MENU_TEXTS:
            context.user_data.pop("awaiting_plan_time", None)
        else:
            day = date.fromisoformat(context.user_data["awaiting_plan_time"])
            match = re.fullmatch(r"\s*(\d{1,2})[:.](\d{2})\s*", text)
            if not match or int(match.group(1)) > 23 or int(match.group(2)) > 59:
                await update.message.reply_text("Неверный формат. Введи время как 17:30.")
                return
            clock = f"{int(match.group(1)):02d}:{match.group(2)}"
            when = datetime.fromisoformat(f"{day.isoformat()}T{clock}").replace(tzinfo=TZ)
            if when <= datetime.now(TZ):
                await update.message.reply_text(
                    "Это время уже прошло. Введи другое время (например 17:30)."
                )
                return
            context.user_data.pop("awaiting_plan_time", None)
            plan = get_plan(chat_id, day.isoformat())
            save_plan(chat_id, day.isoformat(), clock, plan["topics"] if plan else [])
            menu_text, markup = day_menu(chat_id, day)
            await update.message.reply_text(f"Время сохранено: {clock}.", reply_markup=MAIN_KEYBOARD)
            await update.message.reply_text(menu_text, reply_markup=markup)
            return

    if await process_study_answers(update, context):
        return

    if text in ("📐 Математика", "📚 Повторить темы", "⬅️ К разделам"):
        await update.message.reply_text("📐 Выбери раздел из учебника:",
                                        reply_markup=chapters_keyboard())
        return

    if text in CHAPTERS:
        context.user_data["selected_chapter"] = text
        await update.message.reply_text(f"{text}\n\nВыбери тему для занятия:",
                                        reply_markup=topics_keyboard(text))
        return

    if text in ALL_TOPICS:
        context.user_data["selected_topic"] = text
        kb = ReplyKeyboardMarkup(
            [["✅ Я позанималась"], ["⏳ Отложить"], ["❌ Не сделано"]],
            resize_keyboard=True,
        )
        await update.message.reply_text(
            f"📖 Тема на сегодня:\n{text}\n\n"
            "Нажми «✅ Я позанималась» — я сразу пришлю 3 проверочных примера по этой теме. ❤️",
            reply_markup=kb,
        )
        return

    if text == "⬅️ Главное меню":
        await update.message.reply_text("Главное меню ❤️", reply_markup=MAIN_KEYBOARD)

    elif text == "✅ Я позанималась":
        topic = context.user_data.get("selected_topic")
        if not topic:
            await update.message.reply_text(
                "Сначала выбери тему в разделе «📐 Математика». 🌸",
                reply_markup=MAIN_KEYBOARD,
            )
        else:
            await begin_session(context, chat_id, [topic])

    elif text == "⏳ Отложить":
        context.job_queue.run_once(
            send_reminder, when=30 * 60, chat_id=chat_id,
            data="⏰ Напоминаю: пора вернуться к занятию. У тебя получится! ❤️")
        await update.message.reply_text("Хорошо, напомню через 30 минут. ❤️",
                                        reply_markup=MAIN_KEYBOARD)

    elif text == "❌ Не сделано":
        await update.message.reply_text(
            "Ничего страшного. Занятие не записано. Можно вернуться к нему позже. 🌷",
            reply_markup=MAIN_KEYBOARD)

    elif text == "📅 Дни занятий":
        plan_text, markup = week_view(chat_id, 0)
        await update.message.reply_text(plan_text, reply_markup=markup)

    elif text == "📊 Мой прогресс":
        completed, last_topic, completed_date = get_progress(chat_id)
        history = get_completed_topics(chat_id)
        unique_topics = {topic for topic, _ in history}

        xp = completed * 10
        level = xp // 50 + 1
        xp_in_level = xp % 50
        overall_done = len(unique_topics & set(ALL_TOPICS))
        overall_percent = round(overall_done / len(ALL_TOPICS) * 100) if ALL_TOPICS else 0
        lines = [
            "📊 ТВОЙ ПРОГРЕСС",
            "",
            f"⭐ Уровень: {level}",
            f"✨ Опыт: {xp} XP",
            f"До следующего уровня: {50 - xp_in_level} XP",
            "",
            f"🏆 Уникальных тем пройдено: {overall_done}/{len(ALL_TOPICS)}",
            f"Общий прогресс: {overall_percent}%",
            "",
            "📚 ПРОГРЕСС ПО РАЗДЕЛАМ",
        ]
        for chapter, topics in CHAPTERS.items():
            done_in_chapter = len(set(topics) & unique_topics)
            percent = round(done_in_chapter / len(topics) * 100)
            lines.append(f"{chapter}: {done_in_chapter}/{len(topics)} — {percent}%")

        lines.extend(["", "✅ СПИСОК ВЫПОЛНЕННЫХ ТЕМ"])
        if history:
            for index, (topic, completed_at) in enumerate(history, 1):
                lines.append(f"{index}. {topic} — {completed_at}")
        else:
            lines.append("Пока нет отмеченных тем. Выбери тему и начни свой путь! ❤️")

        lines.extend([
            "",
            f"📅 Занималась сегодня: "
            f"{'Да' if completed_date == datetime.now(TZ).date().isoformat() else 'Пока нет'}",
            f"📝 Всего засчитанных занятий: {completed}",
        ])
        await update.message.reply_text("\n".join(lines), reply_markup=MAIN_KEYBOARD)

    elif text == "💌 Послание":
        await update.message.reply_text(random.choice(MESSAGES),
                                        reply_markup=MAIN_KEYBOARD)
    else:
        await update.message.reply_text("Выбери действие с помощью кнопок меню 🌸",
                                        reply_markup=MAIN_KEYBOARD)


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=context.job.chat_id, text=context.job.data)


async def on_startup(app: Application):
    app.job_queue.run_repeating(
        check_plan, interval=CHECK_INTERVAL_SECONDS, first=3, name="plan_checker"
    )
    logger.info("Планировщик запущен (проверка каждые %s сек)", CHECK_INTERVAL_SECONDS)


async def on_error(update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Ошибка в обработчике:", exc_info=context.error)


def main():
    if TOKEN == "ВСТАВЬ_НОВЫЙ_TOKEN" or not TOKEN.strip():
        raise SystemExit("Сначала вставь TOKEN нового бота от @BotFather.")

    init_db()
    app = Application.builder().token(TOKEN).post_init(on_startup).build()
    if app.job_queue is None:
        raise SystemExit(
            "JobQueue недоступен — напоминания работать не будут.\n"
            'Установи: pip install "python-telegram-bot[job-queue]"'
        )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(review_callback, pattern=r"^review_(ok|no)_"))
    app.add_handler(CallbackQueryHandler(
        plan_callback, pattern=r"^(wk|pd|pt|pc|pch|pk|px|pcopy)_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_error_handler(on_error)

    print("Study with Love запущен ❤️")
    print("Часовой пояс: Asia/Baku")
    app.run_polling()


if __name__ == "__main__":
    main()
