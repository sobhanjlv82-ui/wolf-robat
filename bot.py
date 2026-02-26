import os
import json
import random
import asyncio
from telegram import *
from telegram.ext import *

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔥 کانال خودتو اینجا بزار
CHANNEL_USERNAME = "@Wolfrobat1382"

DATA_FILE = "data.json"
TURN_TIME = 40
MAX_PLAYERS = 50


# ================= STORAGE ================= #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "rooms": {},
        "votes": {},
        "active_chats": {},
        "anonymous_links": {}
    }


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

    if context.args:
        code = context.args[0]

        # 🎮 ورود به اتاق بازی
        if code.startswith("room_"):
            room_id = code.replace("room_", "")
            if room_id in data["rooms"]:
                room = data["rooms"][room_id]
                if user.id not in room["players"]:
                    room["players"].append(user.id)
                    room["scores"][str(user.id)] = 0
                    save_data()
                    await update.message.reply_text("✅ وارد بازی شدی!")
            return

        # 🕵️ ورود به چت ناشناس
        if code.startswith("anon_"):
            owner = code.replace("anon_", "")
            uid = str(user.id)

            if owner == uid:
                await update.message.reply_text("❌ نمی‌تونی با خودت چت بسازی.")
                return

            data["active_chats"][uid] = owner
            data["active_chats"][owner] = uid
            save_data()

            await update.message.reply_text("🔗 چت ناشناس فعال شد!")
            return

    keyboard = [
        [InlineKeyboardButton("🎮 بازی در گروه",
                              url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🎮 بازی در پیوی", callback_data="create_room")],
        [InlineKeyboardButton("🕵️ لینک چت ناشناس", callback_data="create_anon")]
    ]

    await update.message.reply_text(
        "👑 به ربات حرفه‌ای بازی خوش اومدی 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= CREATE ROOM ================= #

async def create_room(update: Update, context):

    query = update.callback_query
    await query.answer()

    room_id = str(random.randint(1000, 9999))

    data["rooms"][room_id] = {
        "players": [query.from_user.id],
        "scores": {str(query.from_user.id): 0},
        "current": 0,
        "waiting": False
    }

    save_data()

    link = f"https://t.me/{context.bot.username}?start=room_{room_id}"

    keyboard = [
        [InlineKeyboardButton("📩 دعوت دوست", url=link)]
    ]

    await query.message.reply_text(
        f"🎮 اتاق ساخته شد\nکد: {room_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= ANONYMOUS LINK ================= #

async def create_anon(update: Update, context):

    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)

    data["anonymous_links"][uid] = True
    save_data()

    link = f"https://t.me/{context.bot.username}?start=anon_{uid}"

    keyboard = [
        [InlineKeyboardButton("🔗 کپی لینک", url=link)]
    ]

    await query.message.reply_text(
        "🕵️ لینک چت ناشناس اختصاصی شما ساخته شد:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= VOTING ================= #

async def handle_vote(update: Update, context):

    query = update.callback_query

    if query.data.startswith("vote_"):
        _, vote_type, room_id = query.data.split("_")

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

        total_votes = data["votes"][room_id]["yes"] + data["votes"][room_id]["no"]

        if total_votes >= len(room["players"]):

            if data["votes"][room_id]["yes"] > data["votes"][room_id]["no"]:
                uid = room["players"][room["current"]]
                room["scores"][str(uid)] += 1
                msg = "🔥 رأی مثبت بیشتر بود → +1 امتیاز"

            else:
                msg = "⛔ رأی منفی بیشتر بود → حکم اجرا میشه"

            room["current"] = (room["current"] + 1) % len(room["players"])
            data["votes"][room_id] = {"yes": 0, "no": 0}
            room["waiting"] = False

            save_data()

            for uid in room["players"]:
                await context.bot.send_message(uid, msg)


# ================= MESSAGE FORWARD (ANONYMOUS) ================= #

async def forward_message(update: Update, context):

    uid = str(update.effective_user.id)

    if uid in data["active_chats"]:
        partner = data["active_chats"][uid]

        await context.bot.send_message(
            int(partner),
            f"📩 پیام ناشناس:\n\n{update.message.text}"
        )


# ================= BUTTON HANDLER ================= #

async def button_handler(update: Update, context):

    query = update.callback_query

    if query.data == "create_room":
        await create_room(update, context)

    elif query.data == "create_anon":
        await create_anon(update, context)

    elif query.data.startswith("vote_"):
        await handle_vote(update, context)

    await query.answer()


# ================= MAIN ================= #

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    app.run_polling()


if __name__ == "__main__":
    main()
