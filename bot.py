from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = '8039143820:AAG2J9_MoEDPjPPrfzPAm2aesKscGGfgiZY'
GROUP_ID = -1002811063230  # ID вашей группы с минусом

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# message_id в группе -> user_id
message_map = {}

class AskQuestion(StatesGroup):
    waiting_for_question = State()

@dp.message_handler(commands='start')
async def start(message: types.Message):
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Задать вопрос", callback_data="ask"))
    await message.answer("Привет! Нажми кнопку ниже, чтобы задать вопрос.", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'ask')
async def ask_question(callback: types.CallbackQuery):
    await callback.message.answer("Напиши свой вопрос одним сообщением:")
    await AskQuestion.waiting_for_question.set()
    await callback.answer()

@dp.message_handler(state=AskQuestion.waiting_for_question, content_types=types.ContentTypes.TEXT)
async def receive_question(message: types.Message, state: FSMContext):
    await state.finish()
    sent = await bot.send_message(
        GROUP_ID,
        f"❓ Вопрос от пользователя @{message.from_user.username or message.from_user.id}:\n{message.text}"
    )
    message_map[sent.message_id] = message.from_user.id
    await message.reply("Ваш вопрос отправлен! Ждите ответа от участников группы.")

@dp.message_handler(lambda m: m.chat.id == GROUP_ID and m.reply_to_message, content_types=types.ContentTypes.TEXT)
async def forward_answer_to_user(message: types.Message):
    original_id = message.reply_to_message.message_id
    user_id = message_map.get(original_id)

    if user_id:
        await bot.send_message(
            user_id,
            f"💬 Ответ на ваш вопрос:\n{message.text}"
        )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
