from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from texts import BTN_GOAL_TODAY, BTN_GOAL_TOMORROW


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_GOAL_TODAY), KeyboardButton(text=BTN_GOAL_TOMORROW)]
        ],
        resize_keyboard=True
    )
