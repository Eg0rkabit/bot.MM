import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from keyboards import main_menu_kb, back_kb
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# Логирование
logging.basicConfig(level=logging.INFO)

# Загружаем токен и ID группы из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

# FSM состояния
class QuestionForm(StatesGroup):
    waiting_for_question = State()

# Инициализация
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Словарь для связи user_id ↔ message_id в группе
user_question_map = {}

# /start
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Привет! Выберите действие:", reply_markup=main_menu_kb)

# Выбор "Задать вопрос"
@dp.message(lambda m: m.text == "❓ Задать вопрос")
async def ask_question(message: Message, state: FSMContext):
    await message.answer("Напишите свой вопрос или нажмите «Назад»:", reply_markup=back_kb)
    await state.set_state(QuestionForm.waiting_for_question)

# Приём вопроса
@dp.message(QuestionForm.waiting_for_question)
async def receive_question(message: Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("Вы вернулись в меню.", reply_markup=main_menu_kb)
        return

    sent_msg = await bot.send_message(
        GROUP_ID,
        f"❓ Вопрос от <b>{message.from_user.full_name}</b> (id: {message.from_user.id}):\n\n{message.text}"
    )

    user_question_map[sent_msg.message_id] = message.from_user.id
    await message.answer("Ваш вопрос отправлен. Ожидайте ответа.", reply_markup=main_menu_kb)
    await state.clear()

# Ловим ответ в группе
@dp.message()
async def handle_group_reply(message: Message):
    if message.chat.id == GROUP_ID and message.reply_to_message:
        original_id = message.reply_to_message.message_id
        if original_id in user_question_map:
            user_id = user_question_map[original_id]
            await bot.send_message(user_id, f"📩 Ответ на ваш вопрос:\n\n{message.text}")

if __name__ == "__main__":
    dp.run_polling(bot)
