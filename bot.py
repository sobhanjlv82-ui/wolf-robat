import os
import json
import random
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG ================= #

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_USERNAME = "@Wolfrobat1382"  # ✅ کانال تو

DATA_FILE = "data.json"
TURN_TIME = 30


# ================= STORAGE ================= #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "rooms": {},
        "anonymous_links": {},
        "active_chats": {}
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
        "❌ برای استفاده از ربات باید عضو کانال شوی!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= START ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    # 🔥 چک Force Join
    if not await check_member(user.id, context):
        await force_join(update, context)
        return

    # 🔥 لینک اتاق یا چت ناشناس
    if context.args:
        code = context.args[0]

        if code.startswith("room_"):
            room_id = code.replace("room_", "")
            if room_id in data["rooms"]:
                room = data["rooms"][room_id]
                if user.id not in room["players"]:
                    room["players"].append(user.id)
                    save_data()
                    await update.message.reply_text("✅ وارد اتاق شدی!")
            return

        if code.startswith("anon_"):
            owner = code.replace("anon_", "")
            uid = str(user.id)

            data["active_chats"][uid] = owner
            data["active_chats"][owner] = uid
            save_data()

            await update.message.reply_text("🔗 چت ناشناس فعال شد!")
            return

    keyboard = [
        [InlineKeyboardButton("🎮 بازی در گروه",
                              url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("❤️ بازی در پیوی", callback_data="create_room")],
        [InlineKeyboardButton("🕵️ چت ناشناس", callback_data="create_anon")]
    ]

    await update.message.reply_text(
        f"👑 سلام {user.first_name}\n\n"
        "به ربات سرگرمی خوش اومدی 🔥",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= CREATE ROOM ================= #

async def create_room(update: Update, context):

    query = update.callback_query
    user = query.from_user

    if not await check_member(user.id, context):
        await force_join(update, context)
        return

    room_id = str(random.randint(1000, 9999))

    data["rooms"][room_id] = {
        "players": [user.id],
        "scores": {str(user.id): 0},
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

    await query.answer()


# ================= FORCE JOIN CHECK BUTTON ================= #

async def button_handler(update: Update, context):

    query = update.callback_query
    user = query.from_user

    if query.data == "check_join":
        if await check_member(user.id, context):
            await query.message.reply_text("✅ تایید شد! حالا می‌تونی استفاده کنی 🔥")
        else:
            await query.message.reply_text("❌ هنوز عضو کانال نشدی!")

    elif query.data == "create_room":
        await create_room(update, context)

    elif query.data == "create_anon":

        uid = str(user.id)
        data["anonymous_links"][uid] = True
        save_data()

        link = f"https://t.me/{context.bot.username}?start=anon_{uid}"

        keyboard = [
            [InlineKeyboardButton("🔗 لینک چت ناشناس", url=link)]
        ]

        await query.message.reply_text(
            "🕵️ لینک چت ناشناس اختصاصی شما:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await query.answer()


# ================= ANONYMOUS MESSAGE ================= #

async def forward_messages(update: Update, context):

    uid = str(update.effective_user.id)

    if uid in data["active_chats"]:
        partner = data["active_chats"][uid]

        await context.bot.send_message(
            int(partner),
            f"📩 پیام ناشناس:\n\n{update.message.text}"
        )


# ================= MAIN ================= #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_messages))

    app.run_polling()


if __name__ == "__main__":
    main()
