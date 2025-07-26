import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatType
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Настройки
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Хранилище вопросов {message_id: user_id}
questions_db = {}

# ===== КЛАВИАТУРЫ =====
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="❓ Задать вопрос"),
        types.KeyboardButton(text="📅 Записаться на приём")
    )
    return builder.as_markup(resize_keyboard=True)

def back_button():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="◀️ Назад"))
    return builder.as_markup(resize_keyboard=True)

# ===== КОМАНДЫ =====
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать! Выберите действие:",
        reply_markup=main_menu()
    )

@dp.message(Command("id"))
async def get_id(message: types.Message):
    """Получить ID чата"""
    await message.reply(f"ID чата: {message.chat.id}")

# ===== ОБРАБОТКА КНОПОК =====
@dp.message(F.text == "◀️ Назад")
async def back_handler(message: types.Message):
    await start(message)

@dp.message(F.text == "❓ Задать вопрос")
async def ask_question_handler(message: types.Message):
    await message.answer(
        "✍️ Напишите ваш вопрос:",
        reply_markup=back_button()
    )

# ===== ПЕРЕСЫЛКА ВОПРОСОВ =====
@dp.message(F.chat.type == ChatType.PRIVATE, F.text)
async def forward_question(message: types.Message):
    if message.text in ["❓ Задать вопрос", "📅 Записаться на приём", "◀️ Назад"]:
        return

    try:
        # Формируем сообщение для группы
        question_text = (
            f"❓ Вопрос от {message.from_user.full_name}\n"
            f"👤 @{message.from_user.username or 'нет'}\n"
            f"🆔 {message.from_user.id}\n\n"
            f"📄 {message.text}"
        )
        
        # Добавляем кнопку "Ответить"
        reply_markup = InlineKeyboardBuilder()
        reply_markup.button(text="✍️ Ответить", callback_data=f"reply_{message.from_user.id}")
        
        # Отправляем в группу
        sent_msg = await bot.send_message(
            chat_id=int(os.getenv("GROUP_ID")),
            text=question_text,
            reply_markup=reply_markup.as_markup()
        )
        
        # Сохраняем связь вопроса и пользователя
        questions_db[sent_msg.message_id] = message.from_user.id
        
        await message.answer("✅ Ваш вопрос отправлен!", reply_markup=main_menu())
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# ===== ОБРАБОТКА ОТВЕТОВ =====
@dp.callback_query(F.data.startswith("reply_"))
async def handle_reply_button(callback: types.CallbackQuery):
    """Обработка нажатия кнопки 'Ответить'"""
    user_id = int(callback.data.split("_")[1])
    questions_db[callback.message.message_id] = user_id
    
    await callback.message.reply(
        "💬 Введите ответ для пользователя:",
        reply_markup=back_button()
    )
    await callback.answer()

@dp.message(F.chat.id == int(os.getenv("GROUP_ID")), F.reply_to_message)
async def handle_admin_reply(message: types.Message):
    """Обработка ответов админа в группе"""
    if message.reply_to_message.message_id in questions_db:
        user_id = questions_db[message.reply_to_message.message_id]
        
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"📩 Ответ на ваш вопрос:\n\n{message.text}"
            )
            await message.reply("✅ Ответ отправлен пользователю!")
        except Exception as e:
            await message.reply(f"❌ Ошибка отправки: {str(e)}")
    else:
        await message.reply("⚠️ Это не ответ на вопрос пользователя")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())