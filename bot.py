import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@Wolfrobat1382"

players = []

truths = [
    "بزرگ‌ترین دروغی که گفتی چی بوده؟",
    "کیو بیشتر از همه دوست داری؟",
    "آخرین باری که گریه کردی کی بود؟"
]

dares = [
    "یه ویس خنده‌دار بفرست 😂",
    "۱۰ دقیقه اسمتو بذار گرگ 🐺",
    "یه جمله عاشقانه بگو 😎"
]

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎮 شروع بازی", callback_data="join")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🐺 به Wolf Robat خوش اومدی\n\nبرای شروع روی دکمه بزن 👇",
        reply_markup=reply_markup
    )

# ---------------- CHECK MEMBERSHIP ---------------- #

async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------------- JOIN GAME ---------------- #

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players

    query = update.callback_query
    user = query.from_user

    await query.answer()

    if not await is_member(user.id, context):
        keyboard = [[InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/Wolfrobat1382")]]
        await query.message.reply_text(
            "❌ برای ورود باید عضو کانال باشی 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if user.id not in players:
        players.append(user.id)
        await query.message.reply_text("✅ وارد بازی شدی!")
    else:
        await query.message.reply_text("⚡ قبلاً وارد شدی!")

    if len(players) >= 4:
        await start_round(query)

# ---------------- START ROUND ---------------- #

async def start_round(query):
    choice = random.choice(["truth", "dare"])

    if choice == "truth":
        question = random.choice(truths)
        text = f"🎯 حقیقت:\n{question}"
    else:
        question = random.choice(dares)
        text = f"🔥 جرئت:\n{question}"

    await query.message.reply_text(text)

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(join_game, pattern="join"))

    app.run_polling()

if __name__ == "__main__":
    main()
