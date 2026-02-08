from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import BTN_DONE, BTN_UNDONE, BTN_EDIT, BTN_DELETE


def goal_actions_kb(goal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_DONE, callback_data=f"done:{goal_id}")],
            [
                InlineKeyboardButton(text=BTN_EDIT, callback_data=f"edit:{goal_id}"),
                InlineKeyboardButton(text=BTN_DELETE, callback_data=f"delete:{goal_id}")
            ]
        ]
    )


def goal_done_actions_kb(goal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_UNDONE, callback_data=f"undone:{goal_id}")],
            [InlineKeyboardButton(text=BTN_DELETE, callback_data=f"delete:{goal_id}")]
        ]
    )
