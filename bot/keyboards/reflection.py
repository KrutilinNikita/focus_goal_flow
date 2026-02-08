from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import BTN_SKIP_REFLECTION


def reflection_kb(goal_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_SKIP_REFLECTION, callback_data=f"skip_reflect:{goal_id}")]
    ])
