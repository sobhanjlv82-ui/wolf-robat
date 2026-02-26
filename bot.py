import os
import json
import random
import asyncio
from telegram import *
from telegram.ext import *

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@Wolfrobat1382"

DATA_FILE = "data.json"
TURN_TIME = 40
MAX_PLAYERS = 50


# ================= STORAGE ================= #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"rooms": {}, "votes": {}, "active_chats": {}}


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


data = load_data()


# ================= FORCE JOIN ================= #

async def check_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


async def force_join(update, context):
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال",
                              url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ]

    await update.effective_message.reply_text(
        "❌ برای استفاده باید عضو کانال باشی!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= START ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not await check_member(user.id, context):
        await force_join(update, context)
        return

    keyboard = [
        [InlineKeyboardButton("🎮 ساخت اتاق", callback_data="create_room")],
        [InlineKeyboardButton("🕵️ چت ناشناس", callback_data="create_anon")]
    ]

    await update.message.reply_text(
        f"👑 سلام {user.first_name}\n\nنسخه حرفه‌ای بازی فعال شد 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= CREATE ROOM ================= #

async def create_room(update: Update, context):

    query = update.callback_query
    await query.answer()

    room_id = str(random.randint(1000, 9999))

    data["rooms"][room_id] = {
        "players": [query.from_user.id],
        "scores": {},
        "current": 0,
        "waiting": False
    }

    data["rooms"][room_id]["scores"][str(query.from_user.id)] = 0
    save_data()

    link = f"https://t.me/{context.bot.username}?start=room_{room_id}"

    keyboard = [
        [InlineKeyboardButton("📩 دعوت دوست", url=link)]
    ]

    await query.message.reply_text(
        f"🎮 اتاق ساخته شد\nکد: {room_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= GAME ROUND ================= #

async def start_round(room_id, context):

    room = data["rooms"][room_id]

    if not room["players"]:
        return

    player_id = room["players"][room["current"]]

    question = random.choice([
        "یه راز بگو 😈",
        "یه حرکت خفن انجام بده 🎭",
        "یه کار خجالت‌آور بکن 😂"
    ])

    room["waiting"] = True
    save_data()

    keyboard = [
        [InlineKeyboardButton("👍 انجام داد", callback_data=f"vote_yes_{room_id}")],
        [InlineKeyboardButton("👎 انجام نداد", callback_data=f"vote_no_{room_id}")]
    ]

    for uid in room["players"]:
        await context.bot.send_message(
            uid,
            f"🎯 نوبت <a href='tg://user?id={player_id}'>بازیکن</a>\n\n{question}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    asyncio.create_task(turn_timeout(room_id, context))


# ================= VOTING SYSTEM ================= #

async def handle_vote(update: Update, context):

    query = update.callback_query
    data_vote = query.data

    if data_vote.startswith("vote_"):

        _, vote_type, room_id = data_vote.split("_")

        room = data["rooms"].get(room_id)
        if not room:
            return

        if room_id not in data["votes"]:
            data["votes"][room_id] = {"yes": 0, "no": 0}

        if vote_type == "yes":
            data["votes"][room_id]["yes"] += 1
        else:
            data["votes"][room_id]["no"] += 1

        save_data()

        await query.answer("رأی ثبت شد ✅")

        # اگر رأی کامل شد
        total_votes = data["votes"][room_id]["yes"] + data["votes"][room_id]["no"]

        if total_votes >= len(room["players"]):

            if data["votes"][room_id]["yes"] > data["votes"][room_id]["no"]:
                uid = room["players"][room["current"]]
                room["scores"][str(uid)] += 1
                msg = "🔥 بازیکن قبول شد +1 امتیاز"

            else:
                msg = "⛔ رأی منفی بیشتر بود → حکم اجرا میشه"

            room["current"] = (room["current"] + 1) % len(room["players"])
            room["waiting"] = False
            data["votes"][room_id] = {"yes": 0, "no": 0}

            save_data()

            for uid in room["players"]:
                await context.bot.send_message(uid, msg)

            await start_round(room_id, context)


# ================= TIMEOUT ================= #

async def turn_timeout(room_id, context):

    await asyncio.sleep(TURN_TIME)

    room = data["rooms"].get(room_id)
    if not room or not room["waiting"]:
        return

    room["waiting"] = False
    room["current"] = (room["current"] + 1) % len(room["players"])
    save_data()

    await start_round(room_id, context)


# ================= BUTTON HANDLER ================= #

async def button_handler(update: Update, context):

    query = update.callback_query

    if query.data == "create_room":
        await create_room(update, context)

    elif query.data.startswith("vote_"):
        await handle_vote(update, context)

    await query.answer()


# ================= MAIN ================= #

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
