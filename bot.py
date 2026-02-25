import os
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@Wolfrobat1382"

players = []
scores = {}
current_index = 0
game_active = False
turn_task = None

TURN_TIME = 30  # تایمر هر نوبت (ثانیه)

truths = [
    "بزرگ‌ترین دروغی که گفتی چی بوده؟",
    "بدترین سوتی زندگیت چی بوده؟",
    "آخرین باری که گریه کردی کی بود؟",
    "اگه نامرئی میشدی چیکار میکردی؟"
]

dares = [
    "یه ویس خنده‌دار بفرست 😂",
    "۱۰ دقیقه اسمتو بذار گرگ 🐺",
    "به یه نفر تو گروه بگو دوستش داری 😎",
    "یه استیکر عجیب بفرست 😈"
]

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎮 ورود به بازی", callback_data="join")]]
    await update.message.reply_text(
        "🐺 بازی جرئت یا حقیقت\n\nحداقل ۲ نفر لازمه 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- CHECK MEMBERSHIP ---------------- #

async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------------- JOIN ---------------- #

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, scores, game_active

    query = update.callback_query
    user = query.from_user
    await query.answer()

    if not await is_member(user.id, context):
        keyboard = [[InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/Wolfrobat1382")]]
        await query.message.reply_text("❌ اول عضو کانال شو 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if user.id in players:
        await query.message.reply_text("⚡ قبلاً وارد شدی!")
        return

    if len(players) >= 8:
        await query.message.reply_text("🚫 ظرفیت بازی پر شده (حداکثر ۸ نفر)")
        return

    players.append(user.id)
    scores[user.id] = 0

    await query.message.reply_text(f"✅ {user.first_name} وارد بازی شد!\n👥 تعداد: {len(players)}")

    if len(players) >= 2 and not game_active:
        game_active = True
        await start_round(query, context)

# ---------------- START ROUND ---------------- #

async def start_round(query, context):
    global current_index, turn_task

    if not players:
        return

    player_id = players[current_index]
    user = await context.bot.get_chat(player_id)

    choice = random.choice(["truth", "dare"])
    question = random.choice(truths if choice == "truth" else dares)

    text = f"🎯 نوبت: {user.first_name}\n\n⏳ {TURN_TIME} ثانیه وقت داری!\n\n{'❓ حقیقت' if choice == 'truth' else '😈 جرئت'}:\n{question}"

    keyboard = [
        [InlineKeyboardButton("✅ انجام دادم", callback_data="done")],
        [InlineKeyboardButton("➡ رد کردن", callback_data="skip")],
        [InlineKeyboardButton("📊 امتیازات", callback_data="scores")],
        [InlineKeyboardButton("🛑 پایان بازی", callback_data="end")]
    ]

    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    turn_task = asyncio.create_task(turn_timeout(context))

# ---------------- TURN TIMEOUT ---------------- #

async def turn_timeout(context):
    global current_index
    await asyncio.sleep(TURN_TIME)
    await next_player(context)

# ---------------- NEXT PLAYER ---------------- #

async def next_player(context):
    global current_index
    current_index = (current_index + 1) % len(players)

# ---------------- DONE ---------------- #

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scores
    query = update.callback_query
    await query.answer()

    player_id = players[current_index]
    scores[player_id] += 1

    await query.message.reply_text("🔥 آفرین! +1 امتیاز گرفتی")

    await next_player(context)
    await start_round(query, context)

# ---------------- SKIP ---------------- #

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⛔ نوبت رد شد")

    await next_player(context)
    await start_round(query, context)

# ---------------- SHOW SCORES ---------------- #

async def show_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = "📊 امتیازات:\n\n"
    for uid, score in scores.items():
        user = await context.bot.get_chat(uid)
        text += f"{user.first_name}: {score}\n"

    await query.message.reply_text(text)

# ---------------- END GAME ---------------- #

async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, scores, current_index, game_active

    query = update.callback_query
    await query.answer()

    players = []
    scores = {}
    current_index = 0
    game_active = False

    await query.message.reply_text("🛑 بازی پایان یافت!\n/start برای شروع دوباره")

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(join_game, pattern="join"))
    app.add_handler(CallbackQueryHandler(done, pattern="done"))
    app.add_handler(CallbackQueryHandler(skip, pattern="skip"))
    app.add_handler(CallbackQueryHandler(show_scores, pattern="scores"))
    app.add_handler(CallbackQueryHandler(end_game, pattern="end"))

    app.run_polling()

if __name__ == "__main__":
    main()
