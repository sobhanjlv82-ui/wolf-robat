import os
import json
import random
from telegram import *
from telegram.ext import *

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "group_data.json"
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

# ================= START ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    # اگر پیوی بود
    if chat.type == "private":

        keyboard = [
            [InlineKeyboardButton(
                "➕ افزودن به گروه",
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )]
        ]

        await update.message.reply_text(
            "سلام به WOLF ROBAT 🐺\n\n"
            "خوش اومدی 🎊🎉💥🕺🏻😎\n\n"
            "منو با خودت به گروهت ببر تا بچه هارو سرگرم کنم!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # اگر گروه بود
    else:
        keyboard = [
            [InlineKeyboardButton("🎮 شروع بازی", callback_data="start_game")]
        ]

        await update.message.reply_text(
            "برای شروع بازی روی دکمه بزن 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ================= START GAME ================= #

async def start_game(update: Update, context):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id

    members = []
    async for member in context.bot.get_chat_members(chat_id):
        if not member.user.is_bot:
            members.append(member.user.id)

    if len(members) < 2:
        await query.message.reply_text("❌ حداقل ۲ نفر برای شروع بازی لازم است.")
        return

    if len(members) > MAX_PLAYERS:
        members = members[:MAX_PLAYERS]

    data["rooms"][chat_id] = {
        "players": members,
        "scores": {str(uid): 0 for uid in members},
        "current": 0,
        "votes": {"yes": 0, "no": 0}
    }

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

# ================= MAIN ================= #

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_game, pattern="start_game"))
    app.add_handler(CallbackQueryHandler(handle_vote, pattern="vote_"))

    app.run_polling()

if __name__ == "__main__":
    main()
