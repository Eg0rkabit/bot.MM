import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

questions_map = {}  # {group_message_id: (user_id, question_text)}

class States(StatesGroup):
    waiting_for_question = State()

def get_main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Задать вопрос")]],
        resize_keyboard=True
    )

def get_waiting_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Вернуться в меню")]],
        resize_keyboard=True
    )

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Нажмите кнопку ниже, чтобы задать вопрос.",
        reply_markup=get_main_menu_kb()
    )

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

@router.message(F.text.in_({"Отмена", "Вернуться в меню"}))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_kb()
    )

@router.message(States.waiting_for_question, F.chat.type == ChatType.PRIVATE)
async def forward_question(message: Message, state: FSMContext):
    question_text = f"❓ Вопрос от пользователя:\n\n{message.text}"
    sent = await bot.send_message(GROUP_ID, question_text)
    questions_map[sent.message_id] = (message.from_user.id, message.text)
    
    await state.clear()
    await message.answer(
        "✅ Вопрос отправлен! Ожидайте ответа.",
        reply_markup=get_waiting_kb()
    )

@router.message(
    F.chat.id == GROUP_ID,
    F.reply_to_message,
    F.reply_to_message.from_user.id == bot.id
)
async def handle_group_reply(message: Message):
    if message.reply_to_message.message_id not in questions_map:
        return
    
    user_id, original_question = questions_map[message.reply_to_message.message_id]
    response_text = f"💬 Ответ на ваш вопрос:\n\n{message.text}"
    
    try:
        await bot.send_message(user_id, response_text, reply_markup=get_main_menu_kb())
    except Exception:
        await message.reply("❌ Не удалось отправить ответ")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())