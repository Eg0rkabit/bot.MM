import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
import os

API_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
msg_link = {}

@dp.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def start(message: Message):
    await message.answer("Привет! Напиши свой вопрос.")

@dp.message(F.chat.type == ChatType.PRIVATE)
async def handle_user_msg(message: Message):
    text = f"📩 Вопрос от @{message.from_user.username or message.from_user.full_name}:\n\n{message.text}"
    sent = await bot.send_message(GROUP_ID, text)
    msg_link[sent.message_id] = message.from_user.id
    await message.answer("✅ Вопрос отправлен!")

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_reply(message: Message):
    if message.reply_to_message and message.reply_to_message.message_id in msg_link:
        user_id = msg_link[message.reply_to_message.message_id]
        await bot.send_message(user_id, f"📬 Ответ:\n\n{message.text}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
