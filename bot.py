import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "Wolfrobat1382"  # بدون @ بهتر کار میکنه

players = []

truths = [
    "بزرگ‌ترین دروغی که گفتی چی بوده؟",
    "کیو بیشتر از همه دوست داری؟",
    "آخرین باری که گریه کردی کی بود؟"
]

dares = [
    "یه ویس خنده‌دار بفرست 😂",
    "۱۰ دقیقه اسم خودتو عوض کن به گرگ 🐺",
    "یه جمله عاشقانه به نفر سمت راستت بگو 😎"
]

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 شروع بازی", callback_data="join")],
        [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "🐺 به Wolf Robat خوش اومدی\n\nقبل شروع بازی عضو کانال شو 👇",
            reply_markup=reply_markup
        )

# ---------------- JOIN GAME ---------------- #

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players

    query = update.callback_query
    user = query.from_user

    # چک عضویت با URL ساده (بدون get_chat_member که خطا میده)
    keyboard = [
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check")],
        [InlineKeyboardButton("📢 رفتن به کانال", url=f"https://t.me/{CHANNEL_USERNAME}")]
    ]

    await query.answer()
    await query.message.reply_text(
        "برای ورود به بازی اول عضو کانال شو 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- CHECK BUTTON ---------------- #

async def check_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    if user.id not in players:
        players.append(user.id)

    await query.answer("✅ وارد بازی شدی!")

    if len(players) >= 4:
        await start_round(query)

# ---------------- START ROUND ---------------- #

async def start_round(query):
    player = random.choice(players)
    choice = random.choice(["truth", "dare"])

    if choice == "truth":
        question = random.choice(truths)
        text = f"🎯 نوبت بازیکن\n❓ حقیقت:\n{question}"
    else:
        question = random.choice(dares)
        text = f"🔥 نوبت بازیکن\n😈 جرئت:\n{question}"

    await query.message.reply_text(text)

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(join_game, pattern="join"))
    app.add_handler(CallbackQueryHandler(check_member, pattern="check"))

    app.run_polling()

if __name__ == "__main__":
    main()
