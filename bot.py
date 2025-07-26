import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Хранилище вопросов
questions_db = {}

# ===== КЛАВИАТУРЫ =====
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="❓ Задать вопрос Наталье"),
        types.KeyboardButton(text="📅 Записаться на приём")
    )
    return builder.as_markup(resize_keyboard=True)

def back_button():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="◀️ Назад"))
    return builder.as_markup(resize_keyboard=True)

# ===== ОБРАБОТЧИКИ =====
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_menu()
    )

@dp.message(F.text == "◀️ Назад")
async def back_handler(message: types.Message):
    await start(message)

@dp.message(F.text == "❓ Задать вопрос Наталье")
async def ask_question_handler(message: types.Message):
    await message.answer(
        "Напишите ваш вопрос:",
        reply_markup=back_button()
    )

@dp.message(F.text == "📅 Записаться на приём")
async def appointment_handler(message: types.Message):
    await message.answer(
        "Функция записи на прием в разработке",
        reply_markup=back_button()
    )

# Пересылка вопросов в группу
@dp.message(F.text & ~F.text.in_(["❓ Задать вопрос Наталье", "📅 Записаться на приём", "◀️ Назад"]))
async def forward_question(message: types.Message):
    user = message.from_user
    
    # Формируем сообщение для группы
    question_text = (
        f"❓ <b>Новый вопрос</b>\n"
        f"👤 {user.full_name}\n"
        f"🆔 {user.id}\n"
        f"📱 @{user.username}\n\n"
        f"📄 {message.text}"
    )
    
    # Кнопка "Ответить"
    reply_markup = InlineKeyboardBuilder()
    reply_markup.button(text="✍️ Ответить", callback_data=f"reply_{user.id}")
    
    # Отправляем в группу
    sent_msg = await bot.send_message(
        chat_id=GROUP_ID,
        text=question_text,
        reply_markup=reply_markup.as_markup()
    )
    
    # Сохраняем вопрос
    questions_db[sent_msg.message_id] = {
        "user_id": user.id,
        "question": message.text
    }
    
    await message.answer(
        "✅ Ваш вопрос отправлен!",
        reply_markup=main_menu()
    )

# Обработка ответов из группы
@dp.callback_query(F.data.startswith("reply_"))
async def reply_handler(callback: types.CallbackQuery):
    await callback.message.reply(
        "Введите ваш ответ:",
        reply_markup=back_button()
    )
    questions_db[callback.message.message_id]["admin_msg"] = callback.message

@dp.message(F.chat.id == GROUP_ID & F.reply_to_message)
async def send_reply(message: types.Message):
    if message.reply_to_message.message_id in questions_db:
        question_data = questions_db[message.reply_to_message.message_id]
        try:
            await bot.send_message(
                chat_id=question_data["user_id"],
                text=f"📨 <b>Ответ на ваш вопрос:</b>\n\n{message.text}"
            )
            await message.reply("✅ Ответ отправлен!")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {str(e)}")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())