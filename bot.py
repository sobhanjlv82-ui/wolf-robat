import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================= تنظیمات =================
TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
CHANNEL_USERNAME = "@Wolfrobat1382"

logging.basicConfig(level=logging.INFO)

games = {}

truth_questions = [
    "آخرین دروغی که گفتی چی بود؟ 😅",
    "به کی کراش داری؟ 😎",
    "بزرگ‌ترین ترست چیه؟ 😬",
    "بدترین سوتی زندگیت چی بوده؟ 😂",
]

dare_questions = [
    "یک ویس خنده‌دار بفرست 😂",
    "اسم یکیو تگ کن بگو عاشقتم ❤️",
    "تا ۱۰ برعکس بشمار 😜",
    "یه جمله با ایموجی بگو 🤪",
]

# ================= چک عضویت =================
async def force_join(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ اضافه کردن به گروه",
                url=f"https://t.me/{context.bot.username}?startgroup=true",
            )
        ]
    ]

    await update.message.reply_text(
        "🐺 سلام به WOLF ROBAT خوش اومدی\n\n"
        "منو ببر داخل گروههات تا بازی جرئت یا حقیقت اجرا کنم 🎮🔥",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================= شروع بازی =================
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    games[chat_id] = {
        "players": [],
        "started": False,
        "turn": 0,
    }

    keyboard = [
        [InlineKeyboardButton("🎮 ورود به بازی", callback_data="join")],
        [InlineKeyboardButton("🚀 شروع بازی", callback_data="begin")],
    ]

    await update.message.reply_text(
        "🔥 بازی جرئت یا حقیقت شروع شد\n"
        "حداقل ۲ نفر باید وارد بشن",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================= دکمه ها =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    user = query.from_user

    # چک عضویت کانال
    if not await force_join(user.id, context.bot):
        keyboard = [
            [
                InlineKeyboardButton(
                    "عضویت در کانال",
                    url="https://t.me/Wolfrobat1382",
                )
            ]
        ]

        await query.message.reply_text(
            "🔒 اول باید عضو کانال بشی بعد بازی کنی",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if chat_id not in games:
        return

    game = games[chat_id]

    # ورود به بازی
    if query.data == "join":
        if user.id not in game["players"]:
            game["players"].append(user.id)
            await query.message.reply_text(
                f"✅ {user.first_name} وارد بازی شد!"
            )

    # شروع رسمی
    elif query.data == "begin":
        if len(game["players"]) < 2:
            await query.message.reply_text("❌ حداقل ۲ نفر لازم است")
            return

        game["started"] = True
        game["turn"] = 0
        await next_turn(chat_id, context)

    # انتخاب جرئت یا حقیقت
    elif query.data in ["truth", "dare"]:
        if not game["started"]:
            return

        if query.data == "truth":
            question = random.choice(truth_questions)
        else:
            question = random.choice(dare_questions)

        await query.message.reply_text(f"🎲 سوال:\n{question}")

        game["turn"] = (game["turn"] + 1) % len(game["players"])
        await next_turn(chat_id, context)


# ================= نوبت بعدی =================
async def next_turn(chat_id, context):
    game = games[chat_id]
    player_id = game["players"][game["turn"]]

    user = await context.bot.get_chat(player_id)

    keyboard = [
        [
            InlineKeyboardButton("😈 جرئت", callback_data="dare"),
            InlineKeyboardButton("🤔 حقیقت", callback_data="truth"),
        ]
    ]

    await context.bot.send_message(
        chat_id,
        f"🎯 نوبت {user.first_name} است\n"
        "جرئت یا حقیقت؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================= main =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("startgame", start_game))
    app.add_handler(CallbackQueryHandler(buttons, pattern="join|begin|truth|dare"))

    app.run_polling()


if __name__ == "__main__":
    main()
