from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from texts import BTN_GOAL_TODAY, BTN_GOAL_TOMORROW, BTN_STATS


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_GOAL_TODAY), KeyboardButton(text=BTN_GOAL_TOMORROW)],
            [KeyboardButton(text=BTN_STATS)]
        ],
        resize_keyboard=True
    )
