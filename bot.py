import os
import random
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

games = {}

TURN_TIME = 30

truths = [
    "بزرگ‌ترین دروغت چی بوده؟",
    "آخرین باری که گریه کردی کی بود؟",
    "بدترین سوتی زندگیت چی بوده؟",
]

dares = [
    "یه ویس خنده‌دار بفرست 😂",
    "۱۰ دقیقه اسمتو بذار گرگ 🐺",
    "به یکی از اعضا بگو دوستش داری 😎",
]

punishments = [
    "حکم: یه استیکر خنده‌دار بفرست 😂",
    "حکم: اسم پروفایلتو ۵ دقیقه بذار بازنده 😈",
    "حکم: یه پیام با ۱۰ تا ایموجی بفرست 🔥"
]

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐺 بازی جرئت یا حقیقت\n\n"
        "برای ورود بنویس: join\n"
        "برای پایان: end\n"
        "حداقل ۲ نفر لازم است."
    )

# ---------------- JOIN ---------------- #

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games:
        games[chat_id] = {
            "players": [],
            "scores": {},
            "current": 0,
            "active": False,
            "waiting": False
        }

    game = games[chat_id]

    if user.id in game["players"]:
        await update.message.reply_text("قبلاً وارد شدی 😎")
        return

    if len(game["players"]) >= 8:
        await update.message.reply_text("ظرفیت پر شده (حداکثر ۸ نفر)")
        return

    game["players"].append(user.id)
    game["scores"][user.id] = 0

    await update.message.reply_text(
        f"{user.first_name} وارد بازی شد 👥 ({len(game['players'])})"
    )

    if len(game["players"]) >= 2 and not game["active"]:
        game["active"] = True
        await start_round(chat_id, context)

# ---------------- START ROUND ---------------- #

async def start_round(chat_id, context):
    game = games[chat_id]

    if not game["players"]:
        return

    player_id = game["players"][game["current"]]
    user = await context.bot.get_chat(player_id)

    choice = random.choice(["truth", "dare"])
    question = random.choice(truths if choice == "truth" else dares)

    game["waiting"] = True

    await context.bot.send_message(
        chat_id,
        f"🎯 نوبت {user.first_name}\n"
        f"⏳ {TURN_TIME} ثانیه وقت داری!\n\n"
        f"{'❓ حقیقت' if choice=='truth' else '😈 جرئت'}:\n{question}"
    )

    asyncio.create_task(turn_timeout(chat_id, context))

# ---------------- TIMEOUT ---------------- #

async def turn_timeout(chat_id, context):
    await asyncio.sleep(TURN_TIME)

    game = games.get(chat_id)
    if not game or not game["waiting"]:
        return

    player_id = game["players"][game["current"]]
    punishment = random.choice(punishments)

    await context.bot.send_message(
        chat_id,
        f"⛔ وقت تموم شد!\n{punishment}"
    )

    game["waiting"] = False
    game["current"] = (game["current"] + 1) % len(game["players"])
    await start_round(chat_id, context)

# ---------------- HANDLE MESSAGE ---------------- #

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games:
        return

    game = games[chat_id]

    if not game["active"] or not game["waiting"]:
        return

    current_player = game["players"][game["current"]]

    if user.id != current_player:
        return

    # اگه پیام داد یعنی انجام داده
    game["scores"][user.id] += 1
    game["waiting"] = False

    await update.message.reply_text("🔥 آفرین! +1 امتیاز گرفتی")

    game["current"] = (game["current"] + 1) % len(game["players"]]
    await start_round(chat_id, context)

# ---------------- END ---------------- #

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in games:
        del games[chat_id]
    await update.message.reply_text("🛑 بازی پایان یافت.\n/start برای شروع دوباره")

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^join$"), join))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^end$"), end))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
