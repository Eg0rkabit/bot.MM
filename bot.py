import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# ID группы для пересылки вопросов
GROUP_ID = int(os.getenv("GROUP_ID"))

# Хранилище для связи вопросов
questions_db = {}

# Главное меню
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="❓ Задать вопрос Наталье"),
        types.KeyboardButton(text="📅 Записаться на приём")
    )
    return builder.as_markup(resize_keyboard=True)

# Кнопка "Назад"
def back_button():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="◀️ Назад"))
    return builder.as_markup(resize_keyboard=True)

# Обработчик /start
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu()
    )

# Обработчик кнопки "Задать вопрос"
@dp.message(F.text == "❓ Задать вопрос Наталье")
async def ask_question(message: types.Message):
    await message.answer(
        "Напишите ваш вопрос Наталье:",
        reply_markup=back_button()
    )

# Обработчик кнопки "Назад"
@dp.message(F.text == "◀️ Назад")
async def back_to_menu(message: types.Message):
    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu()
    )

# Пересылка вопроса в группу
@dp.message(F.text & ~F.text.in_(["❓ Задать вопрос Наталье", "📅 Записаться на приём", "◀️ Назад"]))
async def forward_question(message: types.Message):
    user = message.from_user
    
    # Формируем сообщение для группы
    question_text = (
        f"❓ Вопрос от {user.full_name}\n"
        f"👤 @{user.username}\n"
        f"📱 {user.id}\n\n"
        f"📄 {message.text}"
    )
    
    # Кнопка "Ответить" под сообщением
    reply_markup = InlineKeyboardBuilder()
    reply_markup.button(
        text="✍️ Ответить", 
        callback_data=f"reply_{user.id}"
    )
    
    # Отправляем в группу
    sent_msg = await bot.send_message(
        chat_id=GROUP_ID,
        text=question_text,
        reply_markup=reply_markup.as_markup()
    )
    
    # Сохраняем связь
    questions_db[sent_msg.message_id] = {
        "user_id": user.id,
        "question": message.text
    }
    
    await message.answer(
        "✅ Ваш вопрос отправлен Наталье!",
        reply_markup=main_menu()
    )

# Обработчик ответов из группы
@dp.callback_query(F.data.startswith("reply_"))
async def reply_to_question(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.reply(
        f"✍️ Введите ответ для пользователя:",
        reply_markup=back_button()
    )
    questions_db[callback.message.message_id]["admin_msg"] = callback.message

# Отправка ответа пользователю
@dp.message(F.chat.id == GROUP_ID & F.reply_to_message)
async def send_reply(message: types.Message):
    if message.reply_to_message.message_id in questions_db:
        question_data = questions_db[message.reply_to_message.message_id]
        try:
            await bot.send_message(
                chat_id=question_data["user_id"],
                text=f"📨 Ответ на ваш вопрос:\n\n{message.text}"
            )
            await message.reply("✅ Ответ отправлен!")
        except:
            await message.reply("❌ Не удалось отправить ответ")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())