from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❓ Задать вопрос")],
        [KeyboardButton(text="📅 Записаться на консультацию")]
    ],
    resize_keyboard=True
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)
