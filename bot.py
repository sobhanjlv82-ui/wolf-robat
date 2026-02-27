import os
import json
import random
from telegram import *
from telegram.ext import *

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@Wolfrobat1382"
DATA_FILE = "game_data.json"
MAX_PLAYERS = 50

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

# ================= FORCE JOIN ================= #

async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def force_join_message(update, context):
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال",
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ]

    if update.callback_query:
        await update.callback_query.message.reply_text(
            "❌ برای استفاده از بازی باید عضو کانال باشی!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "❌ برای استفاده از بازی باید عضو کانال باشی!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ================= START ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat
    user_id = update.effective_user.id

    if not await is_member(user_id, context):
        await force_join_message(update, context)
        return

    if chat.type == "private":

        keyboard = [[InlineKeyboardButton(
            "➕ افزودن به گروه",
            url=f"https://t.me/{context.bot.username}?startgroup=true"
        )]]

        await update.message.reply_text(
            "سلام به WOLF ROBAT 🐺\n\nخوش اومدی 🎊",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        keyboard = [[InlineKeyboardButton("🎮 شروع بازی", callback_data="create_game")]]

        await update.message.reply_text(
            "برای ساخت بازی روی دکمه بزن 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ================= CREATE GAME ================= #

async def create_game(update: Update, context):

    query = update.callback_query
    user_id = query.from_user.id

    if not await is_member(user_id, context):
        await force_join_message(update, context)
        return

    await query.answer()

    chat_id = query.message.chat.id

    data["rooms"][chat_id] = {
        "players": [],
        "scores": {},
        "current": 0,
        "votes": {"yes": 0, "no": 0},
        "started": False
    }

    save_data()

    keyboard = [
        [InlineKeyboardButton("➕ ورود به بازی", callback_data="join_game")],
        [InlineKeyboardButton("🚀 شروع نهایی", callback_data="final_start")]
    ]

    await query.message.reply_text(
        "🎮 بازی ساخته شد!\n\nبازیکنان روی ورود بزنن.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= JOIN GAME (آپدیت شده حرفه‌ای) ================= #

async def join_game(update: Update, context):

    query = update.callback_query
    user_id = query.from_user.id

    if not await is_member(user_id, context):
        await force_join_message(update, context)
        return

    await query.answer()

    chat_id = query.message.chat.id
    room = data["rooms"].get(chat_id)

    if not room or room["started"]:
        return

    if user_id in room["players"]:
        await query.answer("قبلاً وارد شدی ✅", show_alert=True)
        return

    if len(room["players"]) >= MAX_PLAYERS:
        await query.answer("ظرفیت پر شده ❌", show_alert=True)
        return

    # ✅ اضافه شدن بازیکن
    room["players"].append(user_id)
    room["scores"][str(user_id)] = 0
    save_data()

    players_count = len(room["players"])

    # ✅ آپدیت همون پیام داخل گروه
    try:
        await query.message.edit_text(
            f"🎮 بازی در حال آماده‌سازی...\n\n"
            f"👤 <a href='tg://user?id={user_id}'>یک بازیکن</a> وارد شد ✅\n\n"
            f"👥 تعداد بازیکنان: {players_count}/{MAX_PLAYERS}\n\n"
            "⏳ منتظر بازیکن‌های دیگر هستیم...",
            parse_mode="HTML",
            reply_markup=query.message.reply_markup
        )
    except:
        pass

    await query.answer("وارد بازی شدی ✅", show_alert=True)

# ================= FINAL START ================= #

async def final_start(update: Update, context):

    query = update.callback_query
    user_id = query.from_user.id

    if not await is_member(user_id, context):
        await force_join_message(update, context)
        return

    await query.answer()

    chat_id = query.message.chat.id
    room = data["rooms"].get(chat_id)

    if not room:
        return

    if len(room["players"]) < 2:
        await query.answer("حداقل ۲ نفر لازم است ❌", show_alert=True)
        return

    room["started"] = True
    save_data()

    await next_turn(chat_id, context)

# ================= NEXT TURN ================= #

async def next_turn(chat_id, context):

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
    await query.answer()

    _, vote_type, chat_id = query.data.split("_")
    chat_id = int(chat_id)

    room = data["rooms"].get(chat_id)
    if not room:
        return

    room["votes"][vote_type] += 1

    total_votes = room["votes"]["yes"] + room["votes"]["no"]

    if total_votes >= len(room["players"]):

        if room["votes"]["yes"] > room["votes"]["no"]:
            player_id = room["players"][room["current"]]
            room["scores"][str(player_id)] += 1
            msg = "🔥 قبول شد! +1 امتیاز"
        else:
            msg = "⛔ رأی منفی بیشتر بود! حکم اجرا میشه 😈"

        room["votes"] = {"yes": 0, "no": 0}
        room["current"] = (room["current"] + 1) % len(room["players"])
        save_data()

        await query.message.reply_text(msg)
        await next_turn(chat_id, context)

# ================= CHECK JOIN ================= #

async def check_join(update: Update, context):

    query = update.callback_query
    user_id = query.from_user.id

    if await is_member(user_id, context):
        await query.answer("عضویت تایید شد ✅", show_alert=True)
    else:
        await query.answer("هنوز عضو نشدی ❌", show_alert=True)

# ================= MAIN ================= #

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(create_game, pattern="create_game"))
    app.add_handler(CallbackQueryHandler(join_game, pattern="join_game"))
    app.add_handler(CallbackQueryHandler(final_start, pattern="final_start"))
    app.add_handler(CallbackQueryHandler(handle_vote, pattern="vote_"))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    app.run_polling()

if __name__ == "__main__":
    main()
