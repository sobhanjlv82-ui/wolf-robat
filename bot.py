import os
import json
import random
from telegram import *
from telegram.ext import *

TOKEN = os.getenv("TOKEN")
CHANNEL = "@Wolfrobat1382"
DATA_FILE = "data.json"
MAX_PLAYERS = 50

# ---------- DATA ---------- #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"rooms": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ---------- CHECK MEMBER ---------- #

async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- START ---------- #

async def start(update: Update, context):

    user_id = update.effective_user.id

    if not await is_member(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 عضویت در کانال",
                    url="https://t.me/Wolfrobat1382")]]
        await update.message.reply_text(
            "🔒 اول باید عضو کانال بشی!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if update.effective_chat.type == "private":

        keyboard = [[InlineKeyboardButton(
            "➕ اضافه کردن به گروه",
            url=f"https://t.me/{context.bot.username}?startgroup=true"
        )]]

        await update.message.reply_text(
            "🐺 سلام\nمنو ببر داخل گروه تا بازی شروع شه 🔥",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        keyboard = [[InlineKeyboardButton(
            "🎮 شروع بازی",
            callback_data="create"
        )]]

        await update.message.reply_text(
            "برای شروع بازی دکمه رو بزن 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------- CREATE GAME ---------- #

async def create(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id

    data["rooms"][chat_id] = {
        "players": [],
        "scores": {},
        "turn": 0,
        "votes": {"yes": 0, "no": 0},
        "started": False
    }

    save_data()

    keyboard = [
        [InlineKeyboardButton("➕ ورود به بازی", callback_data="join")],
        [InlineKeyboardButton("🚀 شروع نهایی", callback_data="start")]
    ]

    await query.message.reply_text(
        "🎮 بازی ساخته شد",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- JOIN ---------- #

async def join(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    user_id = query.from_user.id

    room = data["rooms"].get(chat_id)
    if not room:
        return

    if user_id not in room["players"]:

        if len(room["players"]) >= MAX_PLAYERS:
            return

        room["players"].append(user_id)
        room["scores"][str(user_id)] = 0
        save_data()

        await query.message.reply_text(
            f"✅ {query.from_user.first_name} اضافه شد\nمنتظر باشید..."
        )

# ---------- START GAME ---------- #

async def start_game(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    if len(room["players"]) < 2:
        await query.message.reply_text("❌ حداقل ۲ نفر لازم است")
        return

    room["started"] = True
    save_data()

    await next_turn(chat_id, context)

# ---------- TURN ---------- #

async def next_turn(chat_id, context):

    room = data["rooms"][chat_id]

    player_id = room["players"][room["turn"]]

    keyboard = [
        [
            InlineKeyboardButton("👍 انجام داد", callback_data="yes"),
            InlineKeyboardButton("👎 انجام نداد", callback_data="no")
        ]
    ]

    await context.bot.send_message(
        chat_id,
        f"🎯 نوبت <a href='tg://user?id={player_id}'>بازیکن</a>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- VOTE ---------- #

async def vote(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    if query.data == "yes":
        room["votes"]["yes"] += 1
    else:
        room["votes"]["no"] += 1

    total = room["votes"]["yes"] + room["votes"]["no"]

    if total >= len(room["players"]):

        if room["votes"]["yes"] > room["votes"]["no"]:
            winner = room["players"][room["turn"]]
            room["scores"][str(winner)] += 1
            msg = "🔥 +1 امتیاز"
        else:
            msg = "😈 حکم اجرا میشه"

        room["votes"] = {"yes": 0, "no": 0}
        room["turn"] = (room["turn"] + 1) % len(room["players"])

        save_data()

        await query.message.reply_text(msg)
        await next_turn(chat_id, context)

# ---------- SCORE ---------- #

async def score(update: Update, context):

    chat_id = update.effective_chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    text = "🏆 جدول امتیازات:\n\n"

    for uid, sc in room["scores"].items():
        user = await context.bot.get_chat(int(uid))
        text += f"{user.first_name} ➝ {sc}\n"

    await update.message.reply_text(text)

# ---------- MAIN ---------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("score", score))
app.add_handler(CallbackQueryHandler(create, pattern="create"))
app.add_handler(CallbackQueryHandler(join, pattern="join"))
app.add_handler(CallbackQueryHandler(start_game, pattern="start"))
app.add_handler(CallbackQueryHandler(vote, pattern="yes|no"))

app.run_polling()
