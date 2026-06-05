# -*- coding: utf-8 -*-

import sqlite3
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================================
# CONFIG
# =========================================

TOKEN = "8222728148:AAH3hosn2sdScPfGqdAjrW9rHJtxZKDq1rg"

FORCE_CHANNEL = "@Wolfrobat1382"
AD_CHANNEL = "@Wolfrobat1382"

BOT_USERNAME = "Wolf_Robat_bot"

ADMIN_ID = 6715557122

SUPPORT_PHONE = "09961299503"
SUPPORT_ID = "@Sobhanjlv1382"

CARD_NUMBER = "6219861829754943"

# =========================================
# DATABASE
# =========================================

db = sqlite3.connect(
    "cpa_system.db",
    check_same_thread=False
)

cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    coins REAL DEFAULT 0,
    total_earned REAL DEFAULT 0,
    invited_by INTEGER DEFAULT 0,
    join_date TEXT DEFAULT '',
    last_bonus TEXT DEFAULT '',
    claimed TEXT DEFAULT ''
)
""")

db.commit()

# =========================================
# KEYBOARD
# =========================================

main_keyboard = ReplyKeyboardMarkup(

    [
        ["📦 سفارش ممبر", "💎 خرید الماس"],
        ["👤 حساب کاربری", "🎁 الماس رایگان"],
        ["👥 زیرمجموعه گیری", "📞 پشتیبانی"]
    ],

    resize_keyboard=True
)

# =========================================
# FORCE JOIN
# =========================================

async def check_force(bot, user_id):

    try:

        member = await bot.get_chat_member(
            FORCE_CHANNEL,
            user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except:
        return False

# =========================================
# START
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # عضویت اجباری
    if not await check_force(context.bot, user_id):

        keyboard = [

            [
                InlineKeyboardButton(
                    "📢 عضویت در کانال",
                    url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"
                )
            ]

        ]

        await update.message.reply_text(

            "❌ ابتدا عضو کانال شوید سپس دوباره /start بزنید",

            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    inviter = 0

    if context.args:

        try:
            inviter = int(context.args[0])
        except:
            inviter = 0

    cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cur.fetchone()

    if not user:

        join_date = datetime.now().strftime("%Y-%m-%d")

        cur.execute(
            """
            INSERT INTO users(
                user_id,
                invited_by,
                join_date
            )
            VALUES(?,?,?)
            """,
            (
                user_id,
                inviter,
                join_date
            )
        )

        db.commit()

        # پاداش زیرمجموعه
        if inviter != 0 and inviter != user_id:

            cur.execute(
                """
                UPDATE users
                SET
                coins = coins + 5,
                total_earned = total_earned + 5
                WHERE user_id=?
                """,
                (inviter,)
            )

            cur.execute(
                """
                UPDATE users
                SET
                coins = coins + 2,
                total_earned = total_earned + 2
                WHERE user_id=?
                """,
                (user_id,)
            )

            db.commit()

    text = f"""
🤖 ربات حرفه‌ای CPA

━━━━━━━━━━━━━━━

✅ امکانات:

• سفارش ممبر واقعی
• خرید الماس
• تایید رسید خرید
• زیرمجموعه گیری
• الماس رایگان 24 ساعته
• حساب کاربری حرفه‌ای
• ضد هنگ و ضد قطع

━━━━━━━━━━━━━━━

📢 کانال:
{FORCE_CHANNEL}

📞 پشتیبانی:
{SUPPORT_ID}
"""

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard
    )

# =========================================
# HANDLE
# =========================================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # =====================================
    # رسید خرید
    # =====================================

    if update.message.photo:

        if "buy_amount" not in context.user_data:
            return

        amount = context.user_data["buy_amount"]

        photo = update.message.photo[-1].file_id

        keyboard = InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "✅ تایید",
                    callback_data=f"ok|{user_id}|{amount}"
                ),

                InlineKeyboardButton(
                    "❌ رد",
                    callback_data=f"no|{user_id}|{amount}"
                )

            ]

        ])

        await context.bot.send_photo(

            ADMIN_ID,

            photo=photo,

            caption=f"""
💳 خرید جدید

👤 کاربر:
{user_id}

💎 مقدار:
{amount}
""",

            reply_markup=keyboard
        )

        await update.message.reply_text(
            "✅ رسید شما برای مدیریت ارسال شد"
        )

        context.user_data.pop("buy_amount")

        return

    text = update.message.text

    # =====================================
    # حساب کاربری
    # =====================================

    if text == "👤 حساب کاربری":

        cur.execute(
            """
            SELECT
            coins,
            total_earned,
            join_date
            FROM users
            WHERE user_id=?
            """,
            (user_id,)
        )

        data = cur.fetchone()

        coins = data[0]
        total = data[1]
        join_date = data[2]

        # کل زیرمجموعه
        cur.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE invited_by=?
            """,
            (user_id,)
        )

        total_refs = cur.fetchone()[0]

        # زیرمجموعه امروز
        today = datetime.now().strftime("%Y-%m-%d")

        cur.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE invited_by=?
            AND join_date=?
            """,
            (
                user_id,
                today
            )
        )

        today_refs = cur.fetchone()[0]

        name = update.effective_user.first_name

        username = update.effective_user.username

        if username:
            username = "@" + username
        else:
            username = "ندارد"

        await update.message.reply_text(

f"""
🗣 نام کاربری:
{name}

🆔 یوزرنیم:
{username}

🔰 شماره کاربری:
{user_id}

📆 تاریخ عضویت:
{join_date}

━━━━━━━━━━━━━━━

👥 زیرمجموعه امروز:
{today_refs}

👤 کل زیرمجموعه:
{total_refs}

━━━━━━━━━━━━━━━

🔷 مجموع موجودی کسب شده:
{total}

✅ موجودی:
{coins} الماس
"""
        )

    # =====================================
    # الماس رایگان
    # =====================================

    elif text == "🎁 الماس رایگان":

        cur.execute(
            "SELECT last_bonus FROM users WHERE user_id=?",
            (user_id,)
        )

        data = cur.fetchone()

        now = datetime.now()

        if data and data[0]:

            try:

                old = datetime.strptime(
                    data[0],
                    "%Y-%m-%d %H:%M:%S"
                )

                if now - old < timedelta(hours=24):

                    remain = timedelta(hours=24) - (now - old)

                    hours = remain.seconds // 3600

                    await update.message.reply_text(
                        f"⏳ هنوز باید {hours} ساعت صبر کنی"
                    )

                    return

            except:
                pass

        cur.execute(
            """
            UPDATE users
            SET
            coins = coins + 3,
            total_earned = total_earned + 3,
            last_bonus=?
            WHERE user_id=?
            """,
            (
                now.strftime("%Y-%m-%d %H:%M:%S"),
                user_id
            )
        )

        db.commit()

        await update.message.reply_text(
            "✅ 3 الماس رایگان دریافت کردی"
        )

    # =====================================
    # خرید الماس
    # =====================================

    elif text == "💎 خرید الماس":

        keyboard = ReplyKeyboardMarkup(

            [
                ["10 الماس", "20 الماس"],
                ["50 الماس", "100 الماس"],
                ["🔙 بازگشت"]
            ],

            resize_keyboard=True
        )

        await update.message.reply_text(

            "💎 پلن خرید را انتخاب کن",

            reply_markup=keyboard
        )

    elif text in ["10 الماس", "20 الماس", "50 الماس", "100 الماس"]:

        prices = {

            "10 الماس": ("10", "5 تومان"),
            "20 الماس": ("20", "10 تومان"),
            "50 الماس": ("50", "25 تومان"),
            "100 الماس": ("100", "50 تومان")

        }

        amount, price = prices[text]

        context.user_data["buy_amount"] = amount

        await update.message.reply_text(

f"""
💎 خرید الماس

📦 مقدار:
{amount} الماس

💵 قیمت:
{price}

💳 شماره کارت:
{CARD_NUMBER}

📸 بعد از واریز عکس رسید را ارسال کن
"""
        )

    # =====================================
    # سفارش ممبر
    # =====================================

    elif text == "📦 سفارش ممبر":

        keyboard = ReplyKeyboardMarkup(

            [
                ["50 ممبر", "80 ممبر"],
                ["120 ممبر"],
                ["🔙 بازگشت"]
            ],

            resize_keyboard=True
        )

        await update.message.reply_text(

            "📦 پلن ممبر را انتخاب کن",

            reply_markup=keyboard
        )

    elif text in ["50 ممبر", "80 ممبر", "120 ممبر"]:

        plans = {

            "50 ممبر": (50, 70),
            "80 ممبر": (80, 100),
            "120 ممبر": (120, 150)

        }

        members, cost = plans[text]

        context.user_data["members"] = members
        context.user_data["cost"] = cost

        await update.message.reply_text(
            "🔗 آیدی کانال را با @ ارسال کن"
        )

    elif text.startswith("@"):

        if "members" not in context.user_data:
            return

        cur.execute(
            "SELECT coins FROM users WHERE user_id=?",
            (user_id,)
        )

        coins = cur.fetchone()[0]

        cost = context.user_data["cost"]

        if coins < cost:

            await update.message.reply_text(
                "❌ موجودی کافی نیست"
            )

            return

        cur.execute(
            """
            UPDATE users
            SET coins = coins - ?
            WHERE user_id=?
            """,
            (
                cost,
                user_id
            )
        )

        db.commit()

        members = context.user_data["members"]

        keyboard = [

            [

                InlineKeyboardButton(
                    "📢 عضویت",
                    url=f"https://t.me/{text.replace('@','')}"
                )

            ],

            [

                InlineKeyboardButton(
                    "💎 دریافت الماس",
                    callback_data=f"claim|{text}"
                )

            ]

        ]

        await context.bot.send_message(

            AD_CHANNEL,

f"""
📢 سفارش جدید ممبر

🔗 لینک:
{text}

👥 تعداد:
{members}

🎁 جایزه:
3 الماس
""",

            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text(
            "✅ سفارش ثبت شد",
            reply_markup=main_keyboard
        )

        context.user_data.clear()

    # =====================================
    # زیرمجموعه گیری
    # =====================================

    elif text == "👥 زیرمجموعه گیری":

        await update.message.reply_text(

f"""
👥 لینک زیرمجموعه گیری شما:

https://t.me/{BOT_USERNAME}?start={user_id}

🎁 با دعوت هر نفر:
5 الماس دریافت میکنی
"""
        )

    # =====================================
    # پشتیبانی
    # =====================================

    elif text == "📞 پشتیبانی":

        await update.message.reply_text(

f"""
📞 پشتیبانی

📱 شماره:
{SUPPORT_PHONE}

👤 آیدی:
{SUPPORT_ID}
"""
        )

    # =====================================
    # بازگشت
    # =====================================

    elif text == "🔙 بازگشت":

        await update.message.reply_text(
            "🏠 منوی اصلی",
            reply_markup=main_keyboard
        )

# =========================================
# CALLBACK
# =========================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    user_id = query.from_user.id

    await query.answer()

    # =====================================
    # دریافت الماس
    # =====================================

    if query.data.startswith("claim|"):

        target = query.data.split("|")[1]

        try:

            member = await context.bot.get_chat_member(
                target,
                user_id
            )

            if member.status not in [
                "member",
                "administrator",
                "creator"
            ]:

                await query.answer(
                    "❌ عضو کانال نیستی",
                    show_alert=True
                )

                return

            cur.execute(
                "SELECT claimed FROM users WHERE user_id=?",
                (user_id,)
            )

            old = cur.fetchone()[0]

            if target in str(old):

                await query.answer(
                    "❌ قبلاً دریافت کردی",
                    show_alert=True
                )

                return

            cur.execute(
                """
                UPDATE users
                SET
                coins = coins + 3,
                total_earned = total_earned + 3,
                claimed = claimed || ?
                WHERE user_id=?
                """,
                (
                    f"{target},",
                    user_id
                )
            )

            db.commit()

            await query.message.reply_text(
                "✅ 3 الماس اضافه شد"
            )

        except Exception as e:

            print(e)

            await query.answer(
                "❌ خطا در بررسی عضویت",
                show_alert=True
            )

    # =====================================
    # تایید خرید
    # =====================================

    elif query.data.startswith("ok|"):

        if user_id != ADMIN_ID:
            return

        _, target_id, amount = query.data.split("|")

        try:

            cur.execute(
                """
                UPDATE users
                SET
                coins = coins + ?,
                total_earned = total_earned + ?
                WHERE user_id=?
                """,
                (
                    float(amount),
                    float(amount),
                    int(target_id)
                )
            )

            db.commit()

            await context.bot.send_message(

                int(target_id),

f"""
✅ خرید شما تایید شد

💎 {amount} الماس
به حسابت اضافه شد
"""
            )

            await query.message.reply_text(
                "✅ خرید تایید شد"
            )

        except Exception as e:

            print(e)

            await query.message.reply_text(
                "❌ خطا در تایید خرید"
            )

    # =====================================
    # رد خرید
    # =====================================

    elif query.data.startswith("no|"):

        if user_id != ADMIN_ID:
            return

        _, target_id, amount = query.data.split("|")

        await context.bot.send_message(
            int(target_id),
            "❌ رسید شما رد شد"
        )

        await query.message.reply_text(
            "❌ خرید رد شد"
        )

# =========================================
# MAIN
# =========================================

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT | filters.PHOTO,
            handle
        )
    )

    print("✅ Bot Running...")

    app.run_polling(
        drop_pending_updates=True
    )

# =========================================
# ANTI CRASH
# =========================================

while True:

    try:

        print("🚀 Bot Starting...")

        main()

    except Exception as e:

        print("ERROR:", e)

        import time
        time.sleep(5)
