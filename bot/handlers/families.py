import logging
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from . import router
from database import (
    create_family, get_families, get_family,
    update_family_name, delete_family, get_wishes_in_family,
    set_wish_family, get_active_wishes
)
from keyboards.families import families_menu_kb, family_actions_kb, select_family_kb
from texts import (
    MSG_PATHS_INTRO, MSG_PATHS_EMPTY, MSG_ENTER_PATH_NAME,
    MSG_PATH_CREATED, MSG_PATH_DELETED, MSG_SELECT_PATH, BTN_PATHS
)

logger = logging.getLogger(__name__)


class FamilyStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_edit = State()


@router.callback_query(F.data == "paths_menu")
async def paths_menu(callback: CallbackQuery):
    families = get_families(callback.from_user.id)

    text = MSG_PATHS_INTRO + "\n\n"

    if families:
        for family in families:
            wishes = get_wishes_in_family(family[0])
            text += f"🛤 <b>{family[2]}</b> ({len(wishes)} хочу)\n"
    else:
        text += MSG_PATHS_EMPTY

    await callback.message.edit_text(text, reply_markup=families_menu_kb(families))
    await callback.answer()


@router.callback_query(F.data == "create_path")
async def create_path_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FamilyStates.waiting_for_name)
    await callback.message.answer(MSG_ENTER_PATH_NAME)
    await callback.answer()


@router.message(FamilyStates.waiting_for_name)
async def save_path(message: Message, state: FSMContext):
    create_family(message.from_user.id, message.text)
    logger.info(f"User {message.from_user.id} created a path")

    await state.clear()

    # Show paths menu
    families = get_families(message.from_user.id)
    text = MSG_PATHS_INTRO + "\n\n"
    for family in families:
        wishes = get_wishes_in_family(family[0])
        text += f"🛤 <b>{family[2]}</b> ({len(wishes)} хочу)\n"

    await message.answer(text, reply_markup=families_menu_kb(families))


@router.callback_query(F.data.startswith("path:"))
async def show_path(callback: CallbackQuery):
    family_id = int(callback.data.split(":")[1])
    family = get_family(family_id)

    if not family:
        await callback.answer("Путь не найден", show_alert=True)
        return

    wishes = get_wishes_in_family(family_id)

    text = f"🛤 <b>{family[2]}</b>\n\n"
    if wishes:
        text += "Хочу в этом пути:\n"
        for wish in wishes:
            text += f"• {wish[2]}\n"
    else:
        text += "В этом пути пока нет «хочу»"

    await callback.message.edit_text(text, reply_markup=family_actions_kb(family_id))
    await callback.answer()


@router.callback_query(F.data.startswith("path_delete:"))
async def delete_path_handler(callback: CallbackQuery):
    family_id = int(callback.data.split(":")[1])
    delete_family(family_id)
    logger.info(f"User {callback.from_user.id} deleted path {family_id}")

    await callback.answer(MSG_PATH_DELETED)

    # Return to paths menu
    families = get_families(callback.from_user.id)
    text = MSG_PATHS_INTRO + "\n\n"
    if families:
        for family in families:
            wishes = get_wishes_in_family(family[0])
            text += f"🛤 <b>{family[2]}</b> ({len(wishes)} хочу)\n"
    else:
        text += MSG_PATHS_EMPTY

    await callback.message.edit_text(text, reply_markup=families_menu_kb(families))


@router.callback_query(F.data.startswith("add_wish_to_path:"))
async def add_wish_to_path_menu(callback: CallbackQuery, state: FSMContext):
    family_id = int(callback.data.split(":")[1])
    await state.update_data(target_family_id=family_id)

    wishes = get_active_wishes(callback.from_user.id)
    if not wishes:
        await callback.answer("У вас нет активных «хочу»", show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите «хочу» для добавления в путь:",
        reply_markup=select_family_kb(wishes, family_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign_wish_to_path:"))
async def assign_wish_to_path(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    wish_id = int(parts[1])
    family_id = int(parts[2])

    set_wish_family(wish_id, family_id)
    logger.info(f"User {callback.from_user.id} assigned wish {wish_id} to path {family_id}")

    await callback.answer("✅ Добавлено!")

    # Return to path view
    family = get_family(family_id)
    wishes = get_wishes_in_family(family_id)

    text = f"🛤 <b>{family[2]}</b>\n\n"
    if wishes:
        text += "Хочу в этом пути:\n"
        for wish in wishes:
            text += f"• {wish[2]}\n"
    else:
        text += "В этом пути пока нет «хочу»"

    await callback.message.edit_text(text, reply_markup=family_actions_kb(family_id))
