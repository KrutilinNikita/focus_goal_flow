import logging
from datetime import date, datetime, timedelta
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from . import router
from .goals import format_goal_card, format_date_ru, get_time_until_midnight, escape_md
from database import (
    create_wish, get_active_wishes, get_all_wishes, get_wish,
    update_wish_status, update_wish_text, delete_wish,
    count_active_wishes, get_goals_by_wish, get_goal_for_date
)
from keyboards.wishes import (
    wishes_menu_kb, wish_actions_kb, all_wishes_kb, back_to_wishes_kb
)
from keyboards import main_menu_kb, goal_actions_kb, set_goal_kb, goal_completed_kb
from texts import (
    MSG_WISHES_INTRO, MSG_WISHES_EMPTY, MSG_WISHES_ACTIVE, MSG_WISHES_CTA,
    MSG_ENTER_WISH, MSG_WISH_CREATED, MSG_WISH_LIMIT,
    MSG_WISH_UPDATED, MSG_WISH_DELETED, MSG_WISH_CARD,
    MSG_WISH_ACTIVATED, MSG_WISH_DEACTIVATED, MSG_WISH_ARCHIVED,
    MSG_WISH_HISTORY_EMPTY, MSG_WISH_HISTORY_TITLE, MSG_HISTORY_ITEM,
    WISH_STATUS_ACTIVE, WISH_STATUS_INACTIVE, WISH_STATUS_ARCHIVED,
    MSG_GOAL_CARD_TODAY, MSG_GOAL_CARD_TODAY_EMPTY, MSG_GOAL_CARD_TODAY_DONE,
    STATUS_PENDING, STATUS_DONE, STATUS_FAILED
)

logger = logging.getLogger(__name__)


class WishStates(StatesGroup):
    waiting_for_wish = State()
    waiting_for_edit = State()


def get_status_display(status: str) -> str:
    return {
        "active": WISH_STATUS_ACTIVE,
        "inactive": WISH_STATUS_INACTIVE,
        "archived": WISH_STATUS_ARCHIVED
    }.get(status, status)


def format_wish_card(wish, goals_count: int) -> str:
    wish_id, user_id, text, status, family_id, created_at, archived_at, position = wish
    return MSG_WISH_CARD.format(
        text=text,
        status=get_status_display(status),
        created_at=created_at[:10] if created_at else "",
        goals_count=goals_count
    )


@router.message(Command("wants"))
async def cmd_wants(message: Message):
    logger.info(f"User {message.from_user.id} opened /wants")

    active_wishes = get_active_wishes(message.from_user.id)

    text = MSG_WISHES_INTRO + "\n\n"

    if active_wishes:
        text += MSG_WISHES_ACTIVE
        for wish in active_wishes:
            text += f"\n• {wish[2]}"
    else:
        text += MSG_WISHES_EMPTY

    text += MSG_WISHES_CTA

    await message.answer(text, reply_markup=wishes_menu_kb(active_wishes))


@router.callback_query(F.data == "wishes_menu")
async def wishes_menu(callback: CallbackQuery):
    active_wishes = get_active_wishes(callback.from_user.id)

    text = MSG_WISHES_INTRO + "\n\n"

    if active_wishes:
        text += MSG_WISHES_ACTIVE
        for wish in active_wishes:
            text += f"\n• {wish[2]}"
    else:
        text += MSG_WISHES_EMPTY

    text += MSG_WISHES_CTA

    await callback.message.edit_text(text, reply_markup=wishes_menu_kb(active_wishes))
    await callback.answer()


@router.callback_query(F.data == "create_wish")
async def create_wish_start(callback: CallbackQuery, state: FSMContext):
    if count_active_wishes(callback.from_user.id) >= 2:
        await callback.answer(MSG_WISH_LIMIT, show_alert=True)
        return

    await state.set_state(WishStates.waiting_for_wish)
    await callback.message.answer(MSG_ENTER_WISH)
    await callback.answer()


@router.message(WishStates.waiting_for_wish)
async def save_wish(message: Message, state: FSMContext):
    create_wish(message.from_user.id, message.text)
    logger.info(f"User {message.from_user.id} created a wish")

    await state.clear()
    await message.answer(MSG_WISH_CREATED)

    # Show updated wishes menu
    active_wishes = get_active_wishes(message.from_user.id)
    text = MSG_WISHES_INTRO + "\n\n" + MSG_WISHES_ACTIVE
    for wish in active_wishes:
        text += f"\n• {wish[2]}"
    text += MSG_WISHES_CTA

    await message.answer(text, reply_markup=wishes_menu_kb(active_wishes))


@router.callback_query(F.data == "other_wishes")
async def show_other_wishes(callback: CallbackQuery):
    all_wishes = get_all_wishes(callback.from_user.id)

    inactive_archived = [w for w in all_wishes if w[3] != "active"]

    if not inactive_archived:
        await callback.answer("Нет других «хочу»", show_alert=True)
        return

    text = "📋 <b>Остальные хочу:</b>"
    await callback.message.edit_text(text, reply_markup=all_wishes_kb(inactive_archived))
    await callback.answer()


@router.callback_query(F.data.startswith("wish:"))
async def show_wish(callback: CallbackQuery):
    wish_id = int(callback.data.split(":")[1])
    wish = get_wish(wish_id)

    if not wish:
        await callback.answer("«Хочу» не найдено", show_alert=True)
        return

    goals = get_goals_by_wish(wish_id)
    card = format_wish_card(wish, len(goals))

    await callback.message.edit_text(card, reply_markup=wish_actions_kb(wish))
    await callback.answer()


@router.callback_query(F.data.startswith("wish_activate:"))
async def activate_wish(callback: CallbackQuery):
    wish_id = int(callback.data.split(":")[1])

    if count_active_wishes(callback.from_user.id) >= 2:
        await callback.answer(MSG_WISH_LIMIT, show_alert=True)
        return

    update_wish_status(wish_id, "active")
    logger.info(f"User {callback.from_user.id} activated wish {wish_id}")

    await callback.answer(MSG_WISH_ACTIVATED)

    # Refresh wish card
    wish = get_wish(wish_id)
    goals = get_goals_by_wish(wish_id)
    card = format_wish_card(wish, len(goals))
    await callback.message.edit_text(card, reply_markup=wish_actions_kb(wish))


@router.callback_query(F.data.startswith("wish_deactivate:"))
async def deactivate_wish(callback: CallbackQuery):
    wish_id = int(callback.data.split(":")[1])
    update_wish_status(wish_id, "inactive")
    logger.info(f"User {callback.from_user.id} deactivated wish {wish_id}")

    await callback.answer(MSG_WISH_DEACTIVATED)

    wish = get_wish(wish_id)
    goals = get_goals_by_wish(wish_id)
    card = format_wish_card(wish, len(goals))
    await callback.message.edit_text(card, reply_markup=wish_actions_kb(wish))


@router.callback_query(F.data.startswith("wish_archive:"))
async def archive_wish(callback: CallbackQuery):
    wish_id = int(callback.data.split(":")[1])
    update_wish_status(wish_id, "archived")
    logger.info(f"User {callback.from_user.id} archived wish {wish_id}")

    await callback.answer(MSG_WISH_ARCHIVED)

    wish = get_wish(wish_id)
    goals = get_goals_by_wish(wish_id)
    card = format_wish_card(wish, len(goals))
    await callback.message.edit_text(card, reply_markup=wish_actions_kb(wish))


@router.callback_query(F.data.startswith("wish_edit:"))
async def edit_wish_start(callback: CallbackQuery, state: FSMContext):
    wish_id = int(callback.data.split(":")[1])
    await state.update_data(edit_wish_id=wish_id)
    await state.set_state(WishStates.waiting_for_edit)
    await callback.message.answer(MSG_ENTER_WISH)
    await callback.answer()


@router.message(WishStates.waiting_for_edit)
async def save_edited_wish(message: Message, state: FSMContext):
    data = await state.get_data()
    wish_id = data["edit_wish_id"]

    update_wish_text(wish_id, message.text)
    logger.info(f"User {message.from_user.id} edited wish {wish_id}")

    await state.clear()
    await message.answer(MSG_WISH_UPDATED)

    wish = get_wish(wish_id)
    goals = get_goals_by_wish(wish_id)
    card = format_wish_card(wish, len(goals))
    await message.answer(card, reply_markup=wish_actions_kb(wish))


@router.callback_query(F.data.startswith("wish_delete:"))
async def delete_wish_handler(callback: CallbackQuery):
    wish_id = int(callback.data.split(":")[1])
    delete_wish(wish_id)
    logger.info(f"User {callback.from_user.id} deleted wish {wish_id}")

    await callback.answer(MSG_WISH_DELETED)

    # Return to wishes menu
    active_wishes = get_active_wishes(callback.from_user.id)
    text = MSG_WISHES_INTRO + "\n\n"
    if active_wishes:
        text += MSG_WISHES_ACTIVE
        for wish in active_wishes:
            text += f"\n• {wish[2]}"
    else:
        text += MSG_WISHES_EMPTY
    text += MSG_WISHES_CTA

    await callback.message.edit_text(text, reply_markup=wishes_menu_kb(active_wishes))


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.delete()

    today = date.today()
    goal = get_goal_for_date(callback.from_user.id, today)

    if goal:
        if goal[4] == "done":
            # Show completed goal
            await callback.message.answer(
                format_goal_card(goal, is_today=True, use_done_template=True),
                reply_markup=goal_completed_kb(),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            # Show pending goal
            await callback.message.answer(
                format_goal_card(goal, is_today=True),
                reply_markup=goal_actions_kb(goal[0]),
                parse_mode=ParseMode.MARKDOWN_V2
            )
    else:
        # No goal - show empty card
        empty_card = MSG_GOAL_CARD_TODAY_EMPTY.format(
            date=escape_md(format_date_ru(today)),
            time_left=get_time_until_midnight()
        )
        await callback.message.answer(empty_card, reply_markup=set_goal_kb(), parse_mode=ParseMode.MARKDOWN_V2)

    await callback.answer()


@router.callback_query(F.data.startswith("wish_history:"))
async def show_wish_history(callback: CallbackQuery):
    wish_id = int(callback.data.split(":")[1])
    wish = get_wish(wish_id)
    goals = get_goals_by_wish(wish_id)

    if not goals:
        await callback.answer(MSG_WISH_HISTORY_EMPTY, show_alert=True)
        return

    text = MSG_WISH_HISTORY_TITLE.format(wish_text=wish[2])

    for goal in goals[:20]:  # Limit to 20 entries
        goal_id, user_id, goal_date, goal_text, status, created_at, completed_at, locked, wish_id_g, family_snapshot, reflection = goal
        reflection_text = f"💭 {reflection}" if reflection else ""
        text += MSG_HISTORY_ITEM.format(
            date=goal_date,
            goal_text=goal_text,
            reflection=reflection_text
        )

    await callback.message.edit_text(text, reply_markup=back_to_wishes_kb(wish_id))
    await callback.answer()
