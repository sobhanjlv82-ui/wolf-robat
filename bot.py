import os
from telegram import *
from telegram.ext import *

TOKEN = os.getenv("TOKEN")
CHANNEL = "@Wolfrobat1382"

# ---------- چک عضویت ---------- #

async def check_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- پیام اجبار عضویت ---------- #

async def force_join(update, context):
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال",
                              url="https://t.me/Wolfrobat1382")],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ]

    await update.message.reply_text(
        "🔒 برای استفاده از ربات باید عضو کانال باشی!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- START ---------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not await check_member(user_id, context):
        await force_join(update, context)
        return

    if update.effective_chat.type == "private":

        keyboard = [
            [InlineKeyboardButton(
                "➕ اضافه کردن به گروه",
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )]
        ]

        await update.message.reply_text(
            "🐺 سلام به ربات\n\n"
            "منو ببر داخل گروه تا آماده بازی بشم 🎮🔥",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------- چک عضویت دکمه ---------- #

async def check_join(update: Update, context):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if await check_member(user_id, context):
        await query.message.reply_text("✅ عضویت تایید شد!")
    else:
        await query.answer("❌ هنوز عضو نشدی!", show_alert=True)

# ---------- MAIN ---------- #

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    app.run_polling()

if __name__ == "__main__":
    main()
