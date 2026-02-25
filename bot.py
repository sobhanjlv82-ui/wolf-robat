import os
import json
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TURN_TIME = 30
DATA_FILE = "rooms.json"


# ---------------- FILE STORAGE ---------------- #

def load_rooms():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_rooms():
    with open(DATA_FILE, "w") as f:
        json.dump(rooms, f)


rooms = load_rooms()

truths = [
    "بزرگ‌ترین دروغت چی بوده؟",
    "بدترین سوتی زندگیت چی بوده؟",
    "آخرین باری که گریه کردی کی بود؟",
]

dares = [
    "یه ویس خنده‌دار بفرست 😂",
    "۱۰ دقیقه اسمتو بذار گرگ 🐺",
    "به یکی بگو دوستش داری 😎",
]

punishments = [
    "حکم: یه استیکر بفرست 😈",
    "حکم: یه پیام با ۱۰ ایموجی بفرست 🔥",
]


# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 ساخت اتاق", callback_data="create")],
        [InlineKeyboardButton("🔑 ورود با کد", callback_data="join")],
    ]

    await update.message.reply_text(
        "🐺 بازی جرئت یا حقیقت",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- CREATE ROOM ---------------- #

async def create_room(update: Update, context):
    query = update.callback_query
    await query.answer()

    room_id = str(random.randint(1000, 9999))

    rooms[room_id] = {
        "players": [query.from_user.id],
        "scores": {str(query.from_user.id): 0},
        "current": 0,
        "waiting": False,
    }

    save_rooms()

    keyboard = [
        [InlineKeyboardButton("📩 دعوت دوست", url=f"https://t.me/{context.bot.username}?start={room_id}")]
    ]

    await query.message.reply_text(
        f"🎮 اتاق ساخته شد\nکد: {room_id}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- JOIN WITH CODE ---------------- #

async def join_with_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return

    room_id = context.args[0]

    if room_id not in rooms:
        await update.message.reply_text("❌ اتاق پیدا نشد.")
        return

    room = rooms[room_id]
    user_id = update.effective_user.id

    if user_id in room["players"]:
        await update.message.reply_text("قبلاً وارد شدی 😎")
        return

    room["players"].append(user_id)
    room["scores"][str(user_id)] = 0
    save_rooms()

    await update.message.reply_text("✅ وارد اتاق شدی!")

    if len(room["players"]) >= 2:
        await start_round(room_id, context)


# ---------------- START ROUND ---------------- #

async def start_round(room_id, context):
    room = rooms[room_id]
    player_id = room["players"][room["current"]]

    choice = random.choice(["truth", "dare"])
    question = random.choice(truths if choice == "truth" else dares)

    room["waiting"] = True
    save_rooms()

    keyboard = [
        [InlineKeyboardButton("✅ انجام شد", callback_data=f"done_{room_id}")],
        [InlineKeyboardButton("❌ انجام نشد", callback_data=f"fail_{room_id}")]
    ]

    await context.bot.send_message(
        player_id,
        f"🎯 نوبت تو\n⏳ {TURN_TIME} ثانیه وقت داری\n\n{question}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    asyncio.create_task(turn_timeout(room_id, context))


# ---------------- TIMEOUT ---------------- #

async def turn_timeout(room_id, context):
    await asyncio.sleep(TURN_TIME)

    room = rooms.get(room_id)
    if not room or not room["waiting"]:
        return

    punishment = random.choice(punishments)

    await context.bot.send_message(
        room["players"][room["current"]],
        f"⛔ وقت تموم شد!\n{punishment}"
    )

    room["waiting"] = False
    room["current"] = (room["current"] + 1) % len(room["players"])
    save_rooms()

    await start_round(room_id, context)


# ---------------- BUTTON HANDLER ---------------- #

async def button_handler(update: Update, context):
    query = update.callback_query
    data = query.data

    if data == "create":
        await create_room(update, context)

    elif data.startswith("done_"):
        room_id = data.split("_")[1]
        room = rooms.get(room_id)

        if room:
            user_id = query.from_user.id
            room["scores"][str(user_id)] += 1
            room["waiting"] = False
            room["current"] = (room["current"] + 1) % len(room["players"])
            save_rooms()

            await query.message.reply_text("🔥 +1 امتیاز گرفتی!")
            await start_round(room_id, context)

    elif data.startswith("fail_"):
        await query.message.reply_text("😈 حکم اجرا شد!")

    await query.answer()


# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start", join_with_code))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
