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
questions_map = {}  # {message_id_in_group: (user_id, original_question)}

class States(StatesGroup):
    waiting_for_question = State()
    waiting_for_feedback = State()

# Клавиатуры
def get_main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Задать вопрос")],
        ],
        resize_keyboard=True
    )

def get_feedback_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Задать ещё вопрос")],
            [KeyboardButton(text="Завершить диалог")]
        ],
        resize_keyboard=True
    )

# Старт
@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Приветствую!",
        reply_markup=get_main_menu_kb()
    )

# Начало вопроса
@router.message(F.text == "Задать вопрос")
async def ask_question(message: Message, state: FSMContext):
    await state.set_state(States.waiting_for_question)
    await message.answer(
        "Напишите ваш вопрос:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]],
            resize_keyboard=True
        )
    )

# Отмена
@router.message(F.text == "Отмена")
@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_menu_kb()
    )

# Пересылка вопроса в группу
@router.message(States.waiting_for_question)
async def forward_question(message: Message, state: FSMContext):
    user_name = message.from_user.full_name
    question_text = f"❓ Вопрос от {user_name}:\n\n{message.text}"
    
    sent_message = await bot.send_message(GROUP_ID, question_text)
    
    # Сохраняем вопрос и пользователя
    questions_map[sent_message.message_id] = (message.from_user.id, message.text)
    
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
    
    user_id, original_question = questions_map[replied_msg.message_id]
    response_text = (
        f"💬 Ответ на ваш вопрос:\n"
        f"❓ Ваш вопрос: {original_question}\n\n"
        f"📩 Ответ: {message.text}\n\n"
        f"Вы можете задать ещё вопрос или завершить диалог"
    )
    
    try:
        await bot.send_message(
            user_id, 
            response_text,
            reply_markup=get_feedback_menu_kb()
        )
        await bot.send_message(user_id, "Что вы хотите сделать дальше?")
    except Exception:
        await message.reply("❌ Не удалось отправить ответ пользователю")

# Обработка обратной связи
@router.message(F.text == "Задать ещё вопрос")
async def ask_another_question(message: Message, state: FSMContext):
    await ask_question(message, state)

@router.message(F.text == "Завершить диалог")
async def finish_dialog(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Диалог завершён. Вы можете начать новый в любое время.",
        reply_markup=get_main_menu_kb()
    )

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())