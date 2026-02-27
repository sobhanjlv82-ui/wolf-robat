import os
import random
import json
from telegram import *
from telegram.ext import *

TOKEN = os.getenv("TOKEN")
CHANNEL = "@Wolfrobat1382"
MAX_PLAYERS = 50
DATA_FILE = "game.json"

# ---------------- ذخیره داده ---------------- #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"rooms": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ---------------- چک عضویت اجباری ---------------- #

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

    await update.effective_message.reply_text(
        "🔒 برای بازی باید عضو کانال باشی!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- استارت ---------------- #

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
            "منو ببر داخل گروه تا بازی جرئت و حقیقت شروع شه 🎮🔥",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        keyboard = [
            [InlineKeyboardButton("🎮 شروع بازی", callback_data="create_game")]
        ]

        await update.message.reply_text(
            "🎯 برای شروع بازی روی دکمه زیر بزنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------------- ساخت بازی ---------------- #

async def create_game(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id

    data["rooms"][chat_id] = {
        "players": [],
        "scores": {},
        "turn": 0,
        "started": False
    }

    save_data()

    keyboard = [
        [InlineKeyboardButton("➕ ورود به بازی", callback_data="join_game")],
        [InlineKeyboardButton("🚀 شروع نهایی", callback_data="start_final")]
    ]

    await query.message.reply_text(
        "🎮 بازی ساخته شد!\nبازیکنان وارد بازی شوند.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- ورود به بازی ---------------- #

async def join_game(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    user_id = query.from_user.id

    room = data["rooms"].get(chat_id)
    if not room or room["started"]:
        return

    if user_id not in room["players"]:

        if len(room["players"]) >= MAX_PLAYERS:
            return

        room["players"].append(user_id)
        room["scores"][str(user_id)] = 0
        save_data()

        await query.message.reply_text(
            f"✅ {query.from_user.first_name} وارد بازی شد\n"
            "منتظر بقیه باشید..."
        )

# ---------------- شروع نهایی ---------------- #

async def start_final(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    if len(room["players"]) < 2:
        await query.message.reply_text("❌ حداقل 2 نفر لازم است.")
        return

    room["started"] = True
    save_data()

    await next_turn(chat_id, context)

# ---------------- نوبت بازی ---------------- #

async def next_turn(chat_id, context):

    room = data["rooms"][chat_id]

    player_id = room["players"][room["turn"]]

    question = random.choice([
        "جرئت 😈",
        "حقیقت 🤔"
    ])

    keyboard = [
        [
            InlineKeyboardButton("😈 جرئت", callback_data="dare"),
            InlineKeyboardButton("🤔 حقیقت", callback_data="truth")
        ]
    ]

    await context.bot.send_message(
        chat_id,
        f"🎯 نوبت <a href='tg://user?id={player_id}'>بازیکن</a>\n\n{question}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- انتخاب جرئت یا حقیقت ---------------- #

async def choose(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    if query.data == "truth":
        text = "سوال حقیقت: " + random.choice([
            "آخرین دروغی که گفتی چی بوده؟",
            "به کی علاقه داری؟"
        ])
    else:
        text = "حکم جرئت: " + random.choice([
            "یه ویس خنده‌دار بفرست 😂",
            "اسم یه نفر رو تگ کن بگو دوست دارم ❤️"
        ])

    room["turn"] = (room["turn"] + 1) % len(room["players"])
    save_data()

    await query.message.reply_text(text)
    await next_turn(chat_id, context)

# ---------------- MAIN ---------------- #

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(create_game, pattern="create_game"))
    app.add_handler(CallbackQueryHandler(join_game, pattern="join_game"))
    app.add_handler(CallbackQueryHandler(start_final, pattern="start_final"))
    app.add_handler(CallbackQueryHandler(choose, pattern="truth|dare"))
    app.add_handler(CallbackQueryHandler(lambda u, c: None, pattern="check_join"))

    app.run_polling()

if __name__ == "__main__":
    main()
