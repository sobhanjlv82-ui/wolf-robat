import os
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

rooms = {}
TURN_TIME = 30

truths = [
    "بزرگ‌ترین دروغی که گفتی چی بوده؟",
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


# ================= START ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 ساخت اتاق", callback_data="create_room")],
        [InlineKeyboardButton("🔑 ورود به اتاق", callback_data="join_room")],
    ]

    await update.message.reply_text(
        "🐺 بازی جرئت یا حقیقت\n\nیکی از گزینه‌ها رو انتخاب کن 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================= CREATE ROOM ================= #

async def create_room(update: Update, context):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    room_id = str(random.randint(1000, 9999))

    rooms[room_id] = {
        "players": [user.id],
        "scores": {user.id: 0},
        "current": 0,
        "waiting": False,
    }

    keyboard = [
        [InlineKeyboardButton("📩 دعوت دوست", url=f"https://t.me/{context.bot.username}?start={room_id}")],
        [InlineKeyboardButton("🚀 شروع بازی", callback_data=f"start_{room_id}")],
    ]

    await query.message.reply_text(
        f"🎮 اتاق ساخته شد!\n\nکد: {room_id}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================= JOIN ROOM ================= #

async def join_room(update: Update, context):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("🔑 لطفاً کد اتاق را بفرست:\n/start 1234")


# ================= HANDLE START WITH ROOM ================= #

async def start_with_room(update: Update, context):
    room_id = context.args[0] if context.args else None
    user = update.effective_user

    if not room_id or room_id not in rooms:
        await update.message.reply_text("❌ اتاق پیدا نشد.")
        return

    room = rooms[room_id]

    if user.id not in room["players"]:
        room["players"].append(user.id)
        room["scores"][user.id] = 0

    await update.message.reply_text("✅ وارد اتاق شدی!")

    if len(room["players"]) >= 2:
        await start_round(room_id, context)


# ================= START ROUND ================= #

async def start_round(room_id, context):
    room = rooms[room_id]
    player_id = room["players"][room["current"]]
    user = await context.bot.get_chat(player_id)

    choice = random.choice(["truth", "dare"])
    question = random.choice(truths if choice == "truth" else dares)

    room["waiting"] = True

    text = (
        f"🎯 نوبت: {user.first_name}\n"
        f"⏳ {TURN_TIME} ثانیه وقت داری\n\n"
        f"{'❓ حقیقت' if choice=='truth' else '😈 جرئت'}:\n{question}"
    )

    keyboard = [
        [InlineKeyboardButton("✅ انجام شد", callback_data=f"done_{room_id}")],
        [InlineKeyboardButton("❌ انجام نشد", callback_data=f"fail_{room_id}")],
        [InlineKeyboardButton("📊 امتیازات", callback_data=f"scores_{room_id}")],
    ]

    await context.bot.send_message(
        room_id if room_id.startswith("-") else player_id,
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    asyncio.create_task(turn_timeout(room_id, context))


# ================= TIMEOUT ================= #

async def turn_timeout(room_id, context):
    await asyncio.sleep(TURN_TIME)

    room = rooms.get(room_id)
    if not room or not room["waiting"]:
        return

    punishment = random.choice(punishments)

    await context.bot.send_message(
        room_id,
        f"⛔ وقت تموم شد!\n{punishment}",
    )

    room["waiting"] = False
    room["current"] = (room["current"] + 1) % len(room["players"])

    await start_round(room_id, context)


# ================= CALLBACK HANDLER ================= #

async def button_handler(update: Update, context):
    query = update.callback_query
    data = query.data

    if data == "create_room":
        await create_room(update, context)

    elif data == "join_room":
        await join_room(update, context)

    elif data.startswith("done_"):
        room_id = data.split("_")[1]
        room = rooms.get(room_id)

        if room:
            user_id = query.from_user.id
            room["scores"][user_id] += 1
            room["waiting"] = False
            await query.message.reply_text("🔥 +1 امتیاز گرفتی!")
            await start_round(room_id, context)

    elif data.startswith("fail_"):
        room_id = data.split("_")[1]
        await query.message.reply_text("😈 حکم اجرا میشه!")

    elif data.startswith("scores_"):
        room_id = data.split("_")[1]
        room = rooms.get(room_id)

        text = "📊 امتیازات:\n\n"
        for uid, score in room["scores"].items():
            user = await context.bot.get_chat(uid)
            text += f"{user.first_name}: {score}\n"

        await query.message.reply_text(text)


# ================= MAIN ================= #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start", start_with_room))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start_with_room))

    app.run_polling()


if __name__ == "__main__":
    main()
