import os
import json
import random
from telegram import *
from telegram.ext import *

TOKEN = os.getenv("TOKEN")
CHANNEL = "@Wolfrobat1382"
DATA_FILE = "game_data.json"
MAX_PLAYERS = 50

# ================= DATA ================= #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"rooms": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ================= FORCE JOIN ================= #

async def check_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def force_join(update, context):
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/Wolfrobat1382")],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ]

    await update.message.reply_text(
        "🔒 برای استفاده از بازی باید عضو کانال باشی!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= START (WELCOME IN PRIVATE) ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not await check_member(user_id, context):
        await force_join(update, context)
        return

    if update.effective_chat.type == "private":

        keyboard = [
            [InlineKeyboardButton("➕ اضافه کردن به گروه",
                                  url=f"https://t.me/{context.bot.username}?startgroup=true")]
        ]

        await update.message.reply_text(
            "سلام به WOLF ROBAT 🐺\n\n"
            "منو ببر داخل گروه تا بازی جرئت و حقیقت شروع شه 🎮🔥\n\n"
            "بعد از اضافه کردن من به گروه روی شروع بازی بزن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        keyboard = [
            [InlineKeyboardButton("🎮 شروع بازی", callback_data="create_game")]
        ]

        await update.message.reply_text(
            "🎯 برای شروع بازی روی دکمه زیر بزن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ================= CREATE GAME ================= #

async def create_game(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id

    data["rooms"][chat_id] = {
        "players": [],
        "scores": {},
        "turn": 0,
        "started": False,
        "votes": {"yes": 0, "no": 0}
    }

    save_data()

    keyboard = [
        [InlineKeyboardButton("➕ ورود به بازی", callback_data="join_game")],
        [InlineKeyboardButton("🚀 شروع نهایی", callback_data="start_final")]
    ]

    await query.message.reply_text(
        "🎮 بازی ساخته شد!\nبازیکنان وارد شوند.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= JOIN ================= #

async def join_game(update: Update, context):

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
            f"✅ {query.from_user.first_name} وارد بازی شد\n"
            "منتظر نفر بعدی باشید..."
        )

# ================= START FINAL ================= #

async def start_final(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    if len(room["players"]) < 2:
        await query.message.reply_text("❌ حداقل ۲ نفر لازم است.")
        return

    room["started"] = True
    save_data()

    await next_turn(chat_id, context)

# ================= TURN SYSTEM ================= #

async def next_turn(chat_id, context):

    room = data["rooms"][chat_id]

    if not room["players"]:
        return

    player_id = room["players"][room["turn"]]

    keyboard = [
        [
            InlineKeyboardButton("👍 انجام داد", callback_data="vote_yes"),
            InlineKeyboardButton("👎 انجام نداد", callback_data="vote_no")
        ]
    ]

    await context.bot.send_message(
        chat_id,
        f"🎯 نوبت <a href='tg://user?id={player_id}'>بازیکن</a>\n"
        "جرئت یا حقیقت؟",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= VOTE ================= #

async def vote(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    if query.data == "vote_yes":
        room["votes"]["yes"] += 1
    else:
        room["votes"]["no"] += 1

    total = room["votes"]["yes"] + room["votes"]["no"]

    if total >= len(room["players"]):

        if room["votes"]["yes"] > room["votes"]["no"]:
            winner = room["players"][room["turn"]]
            room["scores"][str(winner)] += 1
            msg = "🔥 قبول شد +1 امتیاز"
        else:
            msg = "😈 حکم اجرا میشه!"

        room["votes"] = {"yes": 0, "no": 0}
        room["turn"] = (room["turn"] + 1) % len(room["players"])

        save_data()

        await query.message.reply_text(msg)
        await next_turn(chat_id, context)

# ================= SCORE TABLE ================= #

async def score(update: Update, context):

    chat_id = update.effective_chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    text = "🏆 جدول امتیازات:\n\n"

    for uid, score in room["scores"].items():
        user = await context.bot.get_chat(int(uid))
        text += f"{user.first_name} ➝ {score} امتیاز\n"

    await update.message.reply_text(text)

# ================= MAIN ================= #

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CallbackQueryHandler(create_game, pattern="create_game"))
    app.add_handler(CallbackQueryHandler(join_game, pattern="join_game"))
    app.add_handler(CallbackQueryHandler(start_final, pattern="start_final"))
    app.add_handler(CallbackQueryHandler(vote, pattern="vote_"))

    app.run_polling()

if __name__ == "__main__":
    main()
