import os
import uuid
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# --- متغیرهای محیطی ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# --- مراحل گفتگو ---
TYPE, STEP1, STEP2, STEP3 = range(4)

# --- Flask app و ربات ---
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# ---------------------- دستور /start ----------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['سکه'], ['طلای آب‌شده'], ['ارز']]
    await update.message.reply_text(
        "📌 لطفاً نوع پیشنهاد خود را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TYPE

# ---------------------- انتخاب نوع ----------------------


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text
    context.user_data['type'] = user_choice

    if user_choice == 'سکه':
        await update.message.reply_text("🔢 تعداد سکه را وارد کنید:")
        return STEP1
    elif user_choice == 'طلای آب‌شده':
        await update.message.reply_text("⚖️ وزن طلای آب‌شده (به گرم) را وارد کنید:")
        return STEP1
    elif user_choice == 'ارز':
        await update.message.reply_text("💵 مقدار ارز را وارد کنید:")
        return STEP1
    else:
        await update.message.reply_text("❌ لطفاً یکی از گزینه‌ها را انتخاب کنید.")
        return TYPE

# ---------------------- مرحله ۱ ----------------------


async def step1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['value1'] = update.message.text
    type_ = context.user_data['type']

    if type_ == 'ارز':
        await update.message.reply_text("💱 نوع ارز را وارد کنید (مثلاً دلار، یورو، درهم):")
        return STEP2
    else:
        await update.message.reply_text("💰 فی فروش به ازای هر واحد را وارد کنید:")
        return STEP2

# ---------------------- مرحله ۲ ----------------------


async def step2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    type_ = context.user_data['type']
    if type_ == 'ارز' and 'currency_type' not in context.user_data:
        context.user_data['currency_type'] = update.message.text
        await update.message.reply_text("💰 فی فروش به ازای هر واحد ارز را وارد کنید:")
        return STEP3
    else:
        context.user_data['price'] = update.message.text
        return await send_summary(update, context)

# ---------------------- مرحله ۳ ----------------------


async def step3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['price'] = update.message.text
    return await send_summary(update, context)

# ---------------------- ارسال خلاصه ----------------------


async def send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    type_ = context.user_data['type']
    message = f"📣 پیشنهاد ناشناس ({type_}):\n\n"

    if type_ == 'سکه':
        message += f"🔢 تعداد: {context.user_data['value1']}\n"
        message += f"💰 فی فروش: {context.user_data['price']} تومان"
    elif type_ == 'طلای آب‌شده':
        message += f"⚖️ وزن: {context.user_data['value1']} گرم\n"
        message += f"💰 فی فروش: {context.user_data['price']} تومان"
    elif type_ == 'ارز':
        message += f"💵 مقدار: {context.user_data['value1']}\n"
        message += f"💱 نوع: {context.user_data['currency_type']}\n"
        message += f"💰 فی فروش: {context.user_data['price']} تومان"

    offer_id = str(uuid.uuid4())
    context.bot_data[offer_id] = {
        "message": message,
        "user_id": user.id,
        "user_name": user.first_name
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید", callback_data=f"confirm|{offer_id}")]
    ])

    # ارسال به کانال
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message, reply_markup=keyboard)

    # ارسال برای ادمین
    admin_text = f"📩 پیشنهاد جدید از {user.first_name} ({user.id}):\n\n" + \
        message
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

    await update.message.reply_text("✅ پیشنهاد شما با موفقیت ارسال شد. ممنون از همکاری‌تان.")
    return ConversationHandler.END

# ---------------------- تایید توسط کاربر ----------------------


async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split('|')
    if len(data) != 2:
        return

    _, offer_id = data
    offer_data = context.bot_data.get(offer_id)

    if not offer_data:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("❌ اطلاعات یافت نشد یا منقضی شده.")
        return

    offer_text = offer_data['message']
    user_id = offer_data['user_id']
    user_name = offer_data['user_name']

    admin_msg = (
        f"👤 کاربری به پیام زیر پاسخ داد:\n\n"
        f"📨 پیام:\n{offer_text}\n\n"
        f"👤 کاربر تأییدکننده:\n"
        f"نام: {user_name}\n"
        f"آی‌دی: {user_id}\n"
        f"یوزرنیم: @{query.from_user.username or 'ندارد'}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
    await context.bot.send_message(chat_id=query.from_user.id, text="✅ پیام شما برای ادمین ارسال شد.")

# ---------------------- دستور لغو ----------------------


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

# ---------------------- Handlerها ----------------------
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_type)],
        STEP1: [MessageHandler(filters.TEXT & ~filters.COMMAND, step1)],
        STEP2: [MessageHandler(filters.TEXT & ~filters.COMMAND, step2)],
        STEP3: [MessageHandler(filters.TEXT & ~filters.COMMAND, step3)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)
application.add_handler(CallbackQueryHandler(
    handle_confirm, pattern="^confirm"))

# ---------------------- Webhook Flask ----------------------


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200


@app.route("/")
def index():
    return "Bot is running!", 200


# ---------------------- اجرا ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
