import os
import json
import random
import asyncio
from telegram import *
from telegram.ext import *

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 👇 کانال اجباری (اگر خواستی بعداً اضافه کنیم میذاریم)
CHANNEL_USERNAME = "@Wolfrobat1382"

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


# ================= WELCOME MESSAGE ================= #

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):

    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text(
                "سلام به WOLF ROBAT 🐺\n\n"
                "خوش اومدی 🎊🎉💥🕺🏻😎\n"
                "منو با خودت به گروهت ببر تا بچه هارو سرگرم کنم!"
            )


# ================= START GAME ================= #

async def start_game(update: Update, context):

    chat_id = update.effective_chat.id

    if chat_id not in data["rooms"]:
        data["rooms"][chat_id] = {
            "players": [],
            "scores": {},
            "current": 0,
            "waiting": False
        }

    room = data["rooms"][chat_id]

    # گرفتن اعضای گروه
    async for member in context.bot.get_chat_administrators(chat_id):
        if member.user.id not in room["players"]:
            room["players"].append(member.user.id)
            room["scores"][str(member.user.id)] = 0

    save_data()

    await next_turn(update, context)


# ================= NEXT TURN ================= #

async def next_turn(update: Update, context):

    chat_id = update.effective_chat.id
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

    asyncio.create_task(turn_timeout(chat_id, context))


# ================= TIMEOUT ================= #

async def turn_timeout(chat_id, context):

    await asyncio.sleep(TURN_TIME)

    room = data["rooms"].get(chat_id)
    if not room:
        return

    room["current"] = (room["current"] + 1) % len(room["players"])
    save_data()

    await context.bot.send_message(chat_id, "⏳ وقت تموم شد!")
    await next_turn_by_id(chat_id, context)


async def next_turn_by_id(chat_id, context):
    room = data["rooms"][chat_id]
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

async def handler(update: Update, context):

    if update.message.new_chat_members:
        await welcome(update, context)

    if update.message and update.message.text == "/startgame":
        await start_game(update, context)


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    app.add_handler(CallbackQueryHandler(handle_vote))

    app.run_polling()


if __name__ == "__main__":
    main()
