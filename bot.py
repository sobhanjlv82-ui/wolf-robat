import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@Wolfrobat1382"

players = []
game_active = False
current_player = None

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎮 شروع بازی", callback_data="join")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("به Wolf Robat خوش اومدی 🐺", reply_markup=reply_markup)

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players
    user = update.effective_user

    member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
    if member.status not in ["member", "administrator", "creator"]:

    await update.callback_query.answer(
    "❌ اول عضو کانال شو!\n\n🔗 https://t.me/Wolfrobat1382",
    show_alert=True
    )

    if user.id not in players:
        players.append(user.id)
        await update.callback_query.answer("✅ وارد بازی شدی!")

    if len(players) >= 4:
        await start_round(update, context)

async def start_round(update, context):
    global current_player
    current_player = random.choice(players)

    choice = random.choice(["truth", "dare"])

    if choice == "truth":
        question = random.choice(truths)
        text = f"🎯 نوبت <a href='tg://user?id={current_player}'>بازیکن</a>\n\n❓ حقیقت:\n{question}"
    else:
        question = random.choice(dares)
        text = f"🎯 نوبت <a href='tg://user?id={current_player}'>بازیکن</a>\n\n🔥 جرئت:\n{question}"

    await update.callback_query.message.reply_text(text, parse_mode="HTML")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(join_game, pattern="join"))
    app.run_polling()

if __name__ == "__main__":
    main()
