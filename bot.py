import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart
from aiogram.enums.chat_type import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Для связи вопросов и ответов
questions_map = {}  # {message_id_in_group: user_id}

class States(StatesGroup):
    waiting_for_question = State()

# Старт
@router.message(CommandStart())
async def start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Задать вопрос")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Привет! Нажми кнопку ниже, чтобы задать вопрос нашей команде.",
        reply_markup=kb
    )

# Начало вопроса
@router.message(F.text == "Задать вопрос")
async def ask_question(message: Message, state: FSMContext):
    await state.set_state(States.waiting_for_question)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Напишите ваш вопрос:",
        reply_markup=kb
    )

# Отмена
@router.message(F.text == "Отмена")
@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )

# Пересылка вопроса в группу
@router.message(States.waiting_for_question)
async def forward_question(message: Message, state: FSMContext):
    # Формируем сообщение с именем пользователя
    user_name = message.from_user.full_name
    question_text = f"❓ Вопрос от {user_name}:\n\n{message.text}"
    
    # Отправляем в группу
    sent_message = await bot.send_message(
        GROUP_ID,
        question_text
    )
    
    # Сохраняем связь
    questions_map[sent_message.message_id] = message.from_user.id
    
    await state.clear()
    await message.answer(
        "✅ Ваш вопрос отправлен! Ожидайте ответа.",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработка ответов из группы
@router.message(F.chat.type.in_({"group", "supergroup"}), F.reply_to_message)
async def handle_group_reply(message: Message):
    replied_msg = message.reply_to_message
    if replied_msg.message_id not in questions_map:
        return
    
    user_id = questions_map[replied_msg.message_id]
    responder_name = message.from_user.full_name
    
    # Формируем ответ
    response_text = f"💬 {responder_name} ответил(а) на ваш вопрос:\n\n{message.text}"
    
    try:
        await bot.send_message(user_id, response_text)
    except Exception as e:
        await message.reply("❌ Не удалось отправить ответ пользователю")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())