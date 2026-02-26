import os
import json
import random
import asyncio
from telegram import *
from telegram.ext import *

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "group_data.json"
TURN_TIME = 40


# ================= STORAGE ================= #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"rooms": {}}


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


data = load_data()


# ================= START (PRIVATE MESSAGE UI) ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 بازی در گروه",
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton(
                "➕ افزودن به گروه",
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )
        ]
    ]

    await update.message.reply_text(
        "سلام به WOLF ROBAT 🐺\n\n"
        "خوش اومدی 🎊🎉💥🕺🏻😎\n\n"
        "منو با خودت به گروهت ببر تا بچه‌ها رو سرگرم کنم 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= WELCOME WHEN BOT ADDED ================= #

async def welcome(update: Update, context):

    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text(
                "🎉 سلام گروه!\n\n"
                "من آماده‌ام بازی جرئت و حقیقت رو شروع کنم 😎\n\n"
                "برای شروع بنویسید:\n/startgame"
            )


# ================= START GAME (GROUP ONLY) ================= #

async def start_game(update: Update, context):

    chat_id = update.effective_chat.id

    if chat_id not in data["rooms"]:
        data["rooms"][chat_id] = {
            "players": [],
            "scores": {},
            "current": 0
        }

    room = data["rooms"][chat_id]

    # جمع کردن اعضای گروه
    members = []
    async for member in context.bot.get_chat_administrators(chat_id):
        members.append(member.user.id)

    room["players"] = members
    for uid in members:
        if str(uid) not in room["scores"]:
            room["scores"][str(uid)] = 0

    save_data()

    await next_turn(chat_id, context)


# ================= NEXT TURN ================= #

async def next_turn(chat_id, context):

    room = data["rooms"][chat_id]

    if not room["players"]:
        return

    player_id = room["players"][room["current"]]

    question = random.choice([
        "یه راز بگو 😈",
        "یه حرکت خفن انجام بده 🎭",
        "یه کار خجالت‌آور انجام بده 😂"
    ])

    keyboard = [
        [InlineKeyboardButton("👍 انجام داد", callback_data=f"vote_yes_{chat_id}")],
        [InlineKeyboardButton("👎 انجام نداد", callback_data=f"vote_no_{chat_id}")]
    ]

    await context.bot.send_message(
        chat_id,
        f"🎯 نوبت <a href='tg://user?id={player_id}'>بازیکن</a>\n\n{question}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= VOTE ================= #

async def handle_vote(update: Update, context):

    query = update.callback_query
    _, vote_type, chat_id = query.data.split("_")

    chat_id = int(chat_id)
    room = data["rooms"].get(chat_id)

    if not room:
        return

    if "votes" not in room:
        room["votes"] = {"yes": 0, "no": 0}

    room["votes"][vote_type] += 1
    save_data()

    await query.answer("رأی ثبت شد ✅")


# ================= HANDLER ================= #

async def message_handler(update: Update, context):

    if update.message.new_chat_members:
        await welcome(update, context)

    if update.message.text == "/startgame":
        await start_game(update, context)


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(CallbackQueryHandler(handle_vote))

    app.run_polling()


if __name__ == "__main__":
    main()
