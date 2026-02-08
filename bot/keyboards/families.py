from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import BTN_CREATE_PATH, BTN_BACK, BTN_WISH_DELETE


def families_menu_kb(families: list):
    keyboard = []

    for family in families:
        family_id, user_id, name, created_at = family
        keyboard.append([InlineKeyboardButton(
            text=f"🛤 {name}",
            callback_data=f"path:{family_id}"
        )])

    keyboard.append([InlineKeyboardButton(text=BTN_CREATE_PATH, callback_data="create_path")])
    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="wishes_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def family_actions_kb(family_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить хочу", callback_data=f"add_wish_to_path:{family_id}")],
        [InlineKeyboardButton(text=BTN_WISH_DELETE, callback_data=f"path_delete:{family_id}")],
        [InlineKeyboardButton(text=BTN_BACK, callback_data="paths_menu")]
    ])


def select_family_kb(wishes: list, family_id: int):
    keyboard = []

    for wish in wishes:
        wish_id, user_id, text, status, fam_id, created_at, archived_at, position = wish
        keyboard.append([InlineKeyboardButton(
            text=f"💫 {text[:30]}{'...' if len(text) > 30 else ''}",
            callback_data=f"assign_wish_to_path:{wish_id}:{family_id}"
        )])

    keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data=f"path:{family_id}")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
