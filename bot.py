import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatType
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# === Переменные окружения ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

# === Инициализация бота ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Хранилище временное (можно заменить на базу) ===
questions_db = {}

# === Клавиатуры ===
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

# === Команды ===
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("👋 Добро пожаловать! Выберите действие:", reply_markup=main_menu())

@dp.message(Command("id"))
async def get_id(message: types.Message):
    
    await message.reply(f"ID чата: {message.chat.id}")


@dp.message(F.text == "◀️ Назад")
async def back_handler(message: types.Message):
    await start(message)

@dp.message(F.text == "❓ Задать вопрос")
async def ask_question_handler(message: types.Message):
    await message.answer("✍️ Напишите ваш вопрос:", reply_markup=back_button())

# === Отправка вопроса в группу ===
@dp.message(F.chat.type == ChatType.PRIVATE, F.text)
async def forward_question(message: types.Message):
    if message.text in ["❓ Задать вопрос", "📅 Записаться на приём", "◀️ Назад"]:
        return

    try:
        # Формируем текст
        question_text = (
            f"❓ Вопрос от {message.from_user.full_name}\n"
            f"👤 @{message.from_user.username or 'нет'}\n"
            f"🆔 {message.from_user.id}\n\n"
            f"📄 {message.text}\n\n"
            f"USER_ID:{message.from_user.id}"
        )

        # Кнопка "Ответить" (можно не использовать, но оставим)
        reply_markup = InlineKeyboardBuilder()
        reply_markup.button(text="✍️ Ответить", callback_data=f"reply_{message.from_user.id}")

        sent_msg = await bot.send_message(
            chat_id=GROUP_ID,
            text=question_text,
            reply_markup=reply_markup.as_markup()
        )

        questions_db[sent_msg.message_id] = message.from_user.id
        
        await message.answer("✅ Ваш вопрос отправлен!", reply_markup=main_menu())

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# === Обработка нажатия на кнопку (опционально) ===
@dp.callback_query(F.data.startswith("reply_"))
async def handle_reply_button(callback: types.CallbackQuery):
   
    user_id = int(callback.data.split("_")[1])
    questions_db[callback.message.message_id] = user_id

    await callback.message.reply("💬 Введите ответ для пользователя:", reply_markup=back_button())
    await callback.answer()

# === Извлечение ID из текста ===
def extract_user_id(text: str) -> int | None:
    match = re.search(r"USER_ID:(\d+)", text)
    if match:
        return int(match.group(1))
    return None

# === Обработка ответов в группе ===
@dp.message(F.chat.id == GROUP_ID, F.reply_to_message)
async def handle_admin_reply(message: types.Message):
    original_text = message.reply_to_message.text
    user_id = extract_user_id(original_text)

    if user_id:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"📩 Ответ на ваш вопрос:\n\n{message.text}"
            )
            await message.reply("✅ Ответ отправлен пользователю!")
        except Exception as e:
            await message.reply(f"❌ Ошибка отправки: {str(e)}")
    else:
        await message.reply("⚠️ Не удалось найти ID пользователя в оригинальном сообщении.")

# === Запуск бота ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    
    asyncio.run(main())
