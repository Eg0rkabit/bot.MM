import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from keyboards import main_menu_kb, back_kb
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

if not TOKEN or not GROUP_ID:
    raise ValueError("BOT_TOKEN или GROUP_ID не заданы в переменных окружения!")

class QuestionForm(StatesGroup):
    waiting_for_question = State()

class ConsultationForm(StatesGroup):
    waiting_for_message = State()

bot = Bot(token=TOKEN)
bot.default_parse_mode = ParseMode.HTML
dp = Dispatcher(storage=MemoryStorage())

user_question_map = {}

@dp.message(Command("start"))
async def start_cmd(message: Message):
    if message.chat.type != "private":
        return
    await message.answer("Привет! Выберите действие:", reply_markup=main_menu_kb)

@dp.message(lambda m: m.text == "❓ Задать вопрос")
async def ask_question(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return
    await message.answer("Напишите свой вопрос или нажмите «🔙 Назад»:", reply_markup=back_kb)
    await state.set_state(QuestionForm.waiting_for_question)

@dp.message(QuestionForm.waiting_for_question)
async def receive_question(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return
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

@dp.message(lambda m: m.text == "📅 Записаться на консультацию")
async def consultation(message: Message, state: FSMContext):
    await message.answer(
        "Чтобы записаться на консультацию, напишите Наталье:\n"
        "https://t.me/n_a_loginova"
        "Для возврата в главное меню нажмите «🔙 Назад».",
        reply_markup=back_kb
    )

@dp.message(ConsultationForm.waiting_for_message)
async def receive_consultation_message(message: Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("Вы вернулись в главное меню.", reply_markup=main_menu_kb)
        return
    # Здесь можно переслать в группу или сохранить — по желанию
    await message.answer("Спасибо за сообщение! Мы свяжемся с вами в ближайшее время.")

@dp.message(lambda m: m.text == "🔙 Назад")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вернулись в меню.", reply_markup=main_menu_kb)

@dp.message()
async def handle_group_reply(message: Message):
    if message.chat.id == GROUP_ID and message.reply_to_message:
        original_id = message.reply_to_message.message_id
        if original_id in user_question_map:
            user_id = user_question_map[original_id]
            await bot.send_message(user_id, f"📩 Ответ на ваш вопрос:\n\n{message.text}")

if __name__ == "__main__":
    dp.run_polling(bot)
