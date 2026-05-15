from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8222728148:AAGAsSkqTTJxaYPuYiOI_fk80e-8BP9bfic"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات روشن شد")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

print("Bot Started...")

app.run_polling()
