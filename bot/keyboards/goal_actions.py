from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import BTN_DONE, BTN_UNDONE, BTN_EDIT, BTN_DELETE, BTN_SET_GOAL, BTN_CANCEL, BTN_GOAL_TOMORROW


def set_goal_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_SET_GOAL, callback_data="set_goal")]
        ]
    )


def cancel_goal_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_goal")]
        ]
    )


def set_goal_kb_tomorrow():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_SET_GOAL, callback_data="set_goal_tomorrow")]
        ]
    )


def cancel_goal_kb_tomorrow():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_goal_tomorrow")]
        ]
    )


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


def goal_completed_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_GOAL_TOMORROW, callback_data="goto_goal_tomorrow")]
        ]
    )
