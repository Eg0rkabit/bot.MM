import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.enums.chat_type import ChatType

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))  # укажи ID группы здесь или через .env

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Словарь: message_id в группе -> user_id
message_map = {}

# Приветствие
@router.message(CommandStart())
async def start_handler(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Задать вопрос")]],
        resize_keyboard=True
    )
    await message.answer("Привет! Нажми 'Задать вопрос', чтобы задать анонимный вопрос.", reply_markup=kb)

# Получение вопроса
@router.message(F.text == "Задать вопрос")
async def ask_question(message: Message):
    await message.answer("Напиши свой вопрос, и мы отправим его в группу.")

# Обработка текста от пользователя
@router.message(F.chat.type == ChatType.PRIVATE)
async def forward_to_group(message: Message):
    sent = await bot.send_message(GROUP_ID, f"❓ Новый вопрос:\n\n{message.text}")
    message_map[sent.message_id] = message.chat.id

# Обработка ответа в группе (reply)
@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def handle_group_reply(message: Message):
    if message.reply_to_message and message.reply_to_message.message_id in message_map:
        user_id = message_map[message.reply_to_message.message_id]
        answer = f"💬 Ответ на ваш вопрос:\n\n{message.text}"
        try:
            await bot.send_message(user_id, answer)
        except Exception as e:
            await message.reply("❌ Не удалось доставить сообщение пользователю.")
