import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ⏬ Получаем переменные окружения (на DockHost указываются в панели)
BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_ID = int(os.environ["GROUP_ID"])  # пример: -1001234567890

# 📦 Словарь: id сообщения в группе -> id пользователя
user_question_map = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Задать вопрос", callback_data="ask_question")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Нажми кнопку, чтобы задать вопрос.", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Напиши свой вопрос одним сообщением.")
    context.user_data["awaiting_question"] = True

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_question"):
        context.user_data["awaiting_question"] = False
        user_id = update.message.from_user.id
        user_name = update.message.from_user.full_name
        question = update.message.text

        sent = await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"📩 Вопрос от {user_name}:\n\n{question}\n\n🔁 Ответьте на это сообщение, чтобы переслать ответ обратно.",
        )

        user_question_map[sent.message_id] = user_id
        await update.message.reply_text("✅ Вопрос отправлен! Жди ответа.")
    else:
        await update.message.reply_text("Нажми кнопку, чтобы задать вопрос.")

async def handle_group_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        original_msg_id = update.message.reply_to_message.message_id
        if original_msg_id in user_question_map:
            user_id = user_question_map[original_msg_id]
            answer = update.message.text
            responder = update.message.from_user.full_name

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"💬 Ответ от {responder}:\n\n{answer}"
                )
                await update.message.reply_text("✅ Ответ отправлен пользователю.")
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка при отправке: {e}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_private_message))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_reply))

    print("✅ Бот запущен.")
    application.run_polling()

if __name__ == "__main__":
    main()
