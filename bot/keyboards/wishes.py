from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import (
    BTN_CREATE_WISH, BTN_OTHER_WISHES, BTN_BACK, BTN_PATHS,
    BTN_WISH_HISTORY, BTN_WISH_EDIT, BTN_WISH_DELETE,
    BTN_WISH_ACTIVATE, BTN_WISH_DEACTIVATE, BTN_WISH_ARCHIVE
)


def wishes_menu_kb(active_wishes: list):
    keyboard = []
    default_wish = None

    # Active wishes as buttons (except "Без категории")
    for wish in active_wishes:
        wish_id, user_id, text, status, family_id, created_at, archived_at, position = wish
        if text == "Без категории":
            default_wish = wish
        else:
            keyboard.append([InlineKeyboardButton(
                text=f"💫 {text[:30]}{'...' if len(text) > 30 else ''}",
                callback_data=f"wish:{wish_id}"
            )])

    # "Без категории" at the bottom
    if default_wish:
        keyboard.append([InlineKeyboardButton(
            text="📁 Без категории",
            callback_data=f"wish:{default_wish[0]}"
        )])

    # Create new button
    keyboard.append([InlineKeyboardButton(text=BTN_CREATE_WISH, callback_data="create_wish")])

    # Other wishes button
    keyboard.append([InlineKeyboardButton(text=BTN_OTHER_WISHES, callback_data="other_wishes")])

    # Paths button
    keyboard.append([InlineKeyboardButton(text=BTN_PATHS, callback_data="paths_menu")])

    # Back to main menu
    keyboard.append([InlineKeyboardButton(text="🏠 К целям", callback_data="back_to_main")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def all_wishes_kb(wishes: list):
    keyboard = []

    for wish in wishes:
        wish_id, user_id, text, status, family_id, created_at, archived_at, position = wish
        status_icon = "⏸" if status == "inactive" else "📦"
        keyboard.append([InlineKeyboardButton(
            text=f"{status_icon} {text[:30]}{'...' if len(text) > 30 else ''}",
            callback_data=f"wish:{wish_id}"
        )])

    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="wishes_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def wish_actions_kb(wish):
    wish_id, user_id, text, status, family_id, created_at, archived_at, position = wish

    keyboard = []

    # History button
    keyboard.append([InlineKeyboardButton(text=BTN_WISH_HISTORY, callback_data=f"wish_history:{wish_id}")])

    # Edit button
    keyboard.append([InlineKeyboardButton(text=BTN_WISH_EDIT, callback_data=f"wish_edit:{wish_id}")])

    # Status change buttons
    if status == "active":
        keyboard.append([
            InlineKeyboardButton(text=BTN_WISH_DEACTIVATE, callback_data=f"wish_deactivate:{wish_id}"),
            InlineKeyboardButton(text=BTN_WISH_ARCHIVE, callback_data=f"wish_archive:{wish_id}")
        ])
    elif status == "inactive":
        keyboard.append([
            InlineKeyboardButton(text=BTN_WISH_ACTIVATE, callback_data=f"wish_activate:{wish_id}"),
            InlineKeyboardButton(text=BTN_WISH_ARCHIVE, callback_data=f"wish_archive:{wish_id}")
        ])
    else:  # archived
        keyboard.append([
            InlineKeyboardButton(text=BTN_WISH_ACTIVATE, callback_data=f"wish_activate:{wish_id}")
        ])

    # Delete button
    keyboard.append([InlineKeyboardButton(text=BTN_WISH_DELETE, callback_data=f"wish_delete:{wish_id}")])

    # Back button
    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="wishes_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_to_wishes_kb(wish_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_BACK, callback_data=f"wish:{wish_id}")]
    ])


def select_wish_kb(wishes: list):
    """Show wishes for goal binding. 'Без категории' shown last."""
    keyboard = []
    default_wish = None

    # Other wishes first
    for wish in wishes:
        wish_id, user_id, text, status, family_id, created_at, archived_at, position = wish
        if text == "Без категории":
            default_wish = wish
        else:
            keyboard.append([InlineKeyboardButton(
                text=f"💫 {text[:30]}{'...' if len(text) > 30 else ''}",
                callback_data=f"select_wish:{wish_id}"
            )])

    # "Без категории" at the bottom
    if default_wish:
        keyboard.append([InlineKeyboardButton(
            text="📁 Без категории",
            callback_data=f"select_wish:{default_wish[0]}"
        )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
