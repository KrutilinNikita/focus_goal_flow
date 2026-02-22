from datetime import date, datetime, timedelta
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from . import router
from database import (
    create_goal, get_goal_for_date, get_goal_by_id,
    update_goal_status, update_goal_text, delete_goal,
    get_active_wishes, get_wish, add_reflection
)
from keyboards import main_menu_kb, goal_actions_kb, goal_done_actions_kb, set_goal_kb, cancel_goal_kb, set_goal_kb_tomorrow, cancel_goal_kb_tomorrow, goal_completed_kb
from keyboards.wishes import select_wish_kb
from keyboards.reflection import reflection_kb
from texts import (
    BTN_GOAL_TODAY, BTN_GOAL_TOMORROW,
    MSG_ENTER_GOAL, MSG_GOAL_SAVED_TODAY, MSG_GOAL_SAVED_TOMORROW,
    MSG_GOAL_CARD_TODAY, MSG_GOAL_CARD_TODAY_EMPTY, MSG_GOAL_CARD_TODAY_INPUT, MSG_GOAL_CARD_TODAY_DONE,
    MSG_GOAL_CARD_TOMORROW, MSG_GOAL_CARD_TOMORROW_EMPTY, MSG_GOAL_CARD_TOMORROW_INPUT,
    MSG_GOAL_UNDONE, MSG_GOAL_DELETED, MSG_GOAL_EDITED,
    MSG_CANNOT_EDIT_DONE, STATUS_PENDING, STATUS_DONE, STATUS_FAILED,
    MSG_SELECT_WISH, MSG_ASK_REFLECTION, MSG_ENTER_REFLECTION,
    MSG_REFLECTION_SAVED, MSG_REFLECTION_SKIPPED, DEFAULT_WISH_TEXT
)


class GoalStates(StatesGroup):
    waiting_for_goal = State()
    waiting_for_wish = State()
    waiting_for_edit = State()
    waiting_for_reflection = State()


MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


def get_status_text(status: str) -> str:
    return {
        "pending": STATUS_PENDING,
        "done": STATUS_DONE,
        "failed": STATUS_FAILED
    }.get(status, status)


def escape_md(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_date_ru(d: date) -> str:
    return f"{d.day} {MONTHS_RU[d.month]}"


def get_time_until_midnight() -> str:
    now = datetime.now()
    midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    delta = midnight - now
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} ч {minutes} мин"


def format_goal_card(goal, is_today: bool = True, use_done_template: bool = False) -> str:
    # goal structure: id, user_id, goal_date, goal_text, status, created_at, completed_at, locked, wish_id, family_snapshot, reflection
    goal_id = goal[0]
    goal_date_str = goal[2]
    goal_text = goal[3]
    status = goal[4]
    wish_id = goal[8] if len(goal) > 8 else None
    reflection = goal[10] if len(goal) > 10 else None

    # Parse date
    goal_date = date.fromisoformat(goal_date_str)
    date_formatted = format_date_ru(goal_date)

    # Wish text
    wish_line = ""
    if wish_id:
        wish = get_wish(wish_id)
        if wish and wish[2] != "Без категории":
            wish_line = f"\n💫 {escape_md(wish[2])}"

    if is_today:
        # Use done template for completed goals
        if use_done_template and status == "done":
            reflection_text = reflection if reflection else ""
            return MSG_GOAL_CARD_TODAY_DONE.format(
                date=escape_md(date_formatted),
                goal_text=escape_md(goal_text),
                reflection=escape_md(reflection_text)
            ).strip() + wish_line
        else:
            return MSG_GOAL_CARD_TODAY.format(
                date=escape_md(date_formatted),
                goal_text=escape_md(goal_text),
                status=get_status_text(status),
                time_left=get_time_until_midnight()
            ).strip() + wish_line
    else:
        return MSG_GOAL_CARD_TOMORROW.format(
            date=escape_md(date_formatted),
            goal_text=escape_md(goal_text),
            status=get_status_text(status)
        ).strip() + wish_line


@router.message(F.text == BTN_GOAL_TODAY)
async def goal_today(message: Message, state: FSMContext):
    await show_goal_today(message, state, message.from_user.id)


@router.callback_query(F.data == "goal_today")
async def goal_today_callback(callback: CallbackQuery, state: FSMContext):
    await show_goal_today(callback.message, state, callback.from_user.id)
    await callback.answer()


async def show_goal_today(message: Message, state: FSMContext, user_id: int):
    today = date.today()
    goal = get_goal_for_date(user_id, today)

    if goal:
        if goal[4] == "done":
            # Show completed goal with done template
            await message.answer(format_goal_card(goal, is_today=True, use_done_template=True), reply_markup=goal_completed_kb(), parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await message.answer(format_goal_card(goal, is_today=True), reply_markup=goal_actions_kb(goal[0]), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        # Show empty card with "Set" button
        empty_card = MSG_GOAL_CARD_TODAY_EMPTY.format(
            date=escape_md(format_date_ru(today)),
            time_left=get_time_until_midnight()
        )
        await message.answer(empty_card, reply_markup=set_goal_kb(), parse_mode=ParseMode.MARKDOWN_V2)


@router.callback_query(F.data == "set_goal")
async def set_goal_handler(callback: CallbackQuery, state: FSMContext):
    today = date.today()

    # Update message to input mode
    input_card = MSG_GOAL_CARD_TODAY_INPUT.format(
        date=escape_md(format_date_ru(today)),
        time_left=get_time_until_midnight()
    )
    await callback.message.edit_text(input_card, reply_markup=cancel_goal_kb(), parse_mode=ParseMode.MARKDOWN_V2)

    await state.update_data(goal_date=today)
    await state.set_state(GoalStates.waiting_for_goal)
    await callback.answer()


@router.callback_query(F.data == "cancel_goal")
async def cancel_goal_handler(callback: CallbackQuery, state: FSMContext):
    today = date.today()

    # Return to empty card
    empty_card = MSG_GOAL_CARD_TODAY_EMPTY.format(
        date=escape_md(format_date_ru(today)),
        time_left=get_time_until_midnight()
    )
    await callback.message.edit_text(empty_card, reply_markup=set_goal_kb(), parse_mode=ParseMode.MARKDOWN_V2)

    await state.clear()
    await callback.answer()


@router.message(F.text == BTN_GOAL_TOMORROW)
async def goal_tomorrow(message: Message, state: FSMContext):
    tomorrow = date.today() + timedelta(days=1)
    goal = get_goal_for_date(message.from_user.id, tomorrow)

    if goal:
        kb = goal_actions_kb(goal[0])
        await message.answer(format_goal_card(goal, is_today=False), reply_markup=kb, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        # Show empty card with "Set" button
        empty_card = MSG_GOAL_CARD_TOMORROW_EMPTY.format(
            date=escape_md(format_date_ru(tomorrow))
        )
        await message.answer(empty_card, reply_markup=set_goal_kb_tomorrow(), parse_mode=ParseMode.MARKDOWN_V2)


@router.callback_query(F.data == "set_goal_tomorrow")
async def set_goal_tomorrow_handler(callback: CallbackQuery, state: FSMContext):
    tomorrow = date.today() + timedelta(days=1)

    # Update message to input mode
    input_card = MSG_GOAL_CARD_TOMORROW_INPUT.format(
        date=escape_md(format_date_ru(tomorrow))
    )
    await callback.message.edit_text(input_card, reply_markup=cancel_goal_kb_tomorrow(), parse_mode=ParseMode.MARKDOWN_V2)

    await state.update_data(goal_date=tomorrow)
    await state.set_state(GoalStates.waiting_for_goal)
    await callback.answer()


@router.callback_query(F.data == "cancel_goal_tomorrow")
async def cancel_goal_tomorrow_handler(callback: CallbackQuery, state: FSMContext):
    tomorrow = date.today() + timedelta(days=1)

    # Return to empty card
    empty_card = MSG_GOAL_CARD_TOMORROW_EMPTY.format(
        date=escape_md(format_date_ru(tomorrow))
    )
    await callback.message.edit_text(empty_card, reply_markup=set_goal_kb_tomorrow(), parse_mode=ParseMode.MARKDOWN_V2)

    await state.clear()
    await callback.answer()


@router.message(GoalStates.waiting_for_goal)
async def save_goal_text(message: Message, state: FSMContext):
    await state.update_data(goal_text=message.text)

    # Check if user has custom wishes (not "Без категории")
    active_wishes = get_active_wishes(message.from_user.id)
    custom_wishes = [w for w in active_wishes if w[2] != DEFAULT_WISH_TEXT]

    if custom_wishes:
        # User has custom wishes - show selection
        await state.set_state(GoalStates.waiting_for_wish)
        await message.answer(MSG_SELECT_WISH, reply_markup=select_wish_kb(active_wishes))
    else:
        # No custom wishes - save goal with default "Без категории"
        default_wish = next((w for w in active_wishes if w[2] == DEFAULT_WISH_TEXT), None)
        default_wish_id = default_wish[0] if default_wish else None
        await save_goal_with_wish(message, state, default_wish_id)


@router.callback_query(F.data.startswith("select_wish:"))
async def select_wish_for_goal(callback: CallbackQuery, state: FSMContext):
    wish_id = int(callback.data.split(":")[1])

    await save_goal_with_wish(callback.message, state, wish_id, callback.from_user.id)
    await callback.answer()


async def save_goal_with_wish(message: Message, state: FSMContext, wish_id: int = None, user_id: int = None):
    data = await state.get_data()
    goal_date = data["goal_date"]
    goal_text = data["goal_text"]

    # Get family_id_snapshot if wish exists
    family_id_snapshot = None
    if wish_id:
        wish = get_wish(wish_id)
        if wish:
            family_id_snapshot = wish[4]  # family_id

    uid = user_id or message.from_user.id
    create_goal(uid, goal_date, goal_text, wish_id, family_id_snapshot)

    await state.clear()

    if goal_date == date.today():
        goal = get_goal_for_date(uid, goal_date)
        await message.answer(MSG_GOAL_SAVED_TODAY, reply_markup=main_menu_kb())
        await message.answer(format_goal_card(goal, is_today=True), reply_markup=goal_actions_kb(goal[0]), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        goal = get_goal_for_date(uid, goal_date)
        await message.answer(MSG_GOAL_SAVED_TOMORROW, reply_markup=main_menu_kb())
        if goal:
            await message.answer(format_goal_card(goal, is_today=False), parse_mode=ParseMode.MARKDOWN_V2)


@router.callback_query(F.data.startswith("done:"))
async def mark_done(callback: CallbackQuery, state: FSMContext):
    goal_id = int(callback.data.split(":")[1])
    update_goal_status(goal_id, "done")

    goal = get_goal_by_id(goal_id)

    # Ask for reflection - directly enter text input mode
    await state.update_data(reflection_goal_id=goal_id)
    await state.set_state(GoalStates.waiting_for_reflection)
    await callback.message.edit_text(format_goal_card(goal, is_today=True), parse_mode=ParseMode.MARKDOWN_V2)
    await callback.message.answer(MSG_ASK_REFLECTION, reply_markup=reflection_kb(goal_id))
    await callback.answer()


@router.message(GoalStates.waiting_for_reflection)
async def save_reflection(message: Message, state: FSMContext):
    data = await state.get_data()
    goal_id = data["reflection_goal_id"]

    add_reflection(goal_id, message.text)
    await state.clear()

    goal = get_goal_by_id(goal_id)
    await message.answer(MSG_REFLECTION_SAVED, reply_markup=main_menu_kb())
    await message.answer(format_goal_card(goal, is_today=True, use_done_template=True), reply_markup=goal_completed_kb(), parse_mode=ParseMode.MARKDOWN_V2)


@router.callback_query(F.data.startswith("skip_reflect:"))
async def skip_reflection(callback: CallbackQuery, state: FSMContext):
    goal_id = int(callback.data.split(":")[1])
    goal = get_goal_by_id(goal_id)

    await state.clear()
    await callback.message.edit_text(MSG_REFLECTION_SKIPPED)
    await callback.message.answer(format_goal_card(goal, is_today=True, use_done_template=True), reply_markup=goal_completed_kb(), parse_mode=ParseMode.MARKDOWN_V2)
    await callback.answer()


@router.callback_query(F.data == "goto_goal_tomorrow")
async def goto_goal_tomorrow(callback: CallbackQuery, state: FSMContext):
    tomorrow = date.today() + timedelta(days=1)
    goal = get_goal_for_date(callback.from_user.id, tomorrow)

    if goal:
        kb = goal_actions_kb(goal[0])
        await callback.message.answer(format_goal_card(goal, is_today=False), reply_markup=kb, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        # Show empty card with "Set" button
        empty_card = MSG_GOAL_CARD_TOMORROW_EMPTY.format(
            date=escape_md(format_date_ru(tomorrow))
        )
        await callback.message.answer(empty_card, reply_markup=set_goal_kb_tomorrow(), parse_mode=ParseMode.MARKDOWN_V2)
    await callback.answer()


@router.callback_query(F.data.startswith("undone:"))
async def mark_undone(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    goal_id = int(callback.data.split(":")[1])
    update_goal_status(goal_id, "pending")

    goal = get_goal_by_id(goal_id)
    await callback.message.edit_text(format_goal_card(goal, is_today=True), reply_markup=goal_actions_kb(goal_id), parse_mode=ParseMode.MARKDOWN_V2)
    await callback.answer(MSG_GOAL_UNDONE)


@router.callback_query(F.data.startswith("edit:"))
async def edit_goal(callback: CallbackQuery, state: FSMContext):
    goal_id = int(callback.data.split(":")[1])
    goal = get_goal_by_id(goal_id)

    if goal and goal[4] == "done":
        await callback.answer(MSG_CANNOT_EDIT_DONE, show_alert=True)
        return

    await state.update_data(edit_goal_id=goal_id)
    await state.set_state(GoalStates.waiting_for_edit)
    await callback.message.answer(MSG_ENTER_GOAL)
    await callback.answer()


@router.message(GoalStates.waiting_for_edit)
async def save_edited_goal(message: Message, state: FSMContext):
    data = await state.get_data()
    goal_id = data["edit_goal_id"]

    update_goal_text(goal_id, message.text)
    await state.clear()

    goal = get_goal_by_id(goal_id)
    await message.answer(MSG_GOAL_EDITED, reply_markup=main_menu_kb())
    await message.answer(format_goal_card(goal, is_today=True), reply_markup=goal_actions_kb(goal_id), parse_mode=ParseMode.MARKDOWN_V2)


@router.callback_query(F.data.startswith("delete:"))
async def delete_goal_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    goal_id = int(callback.data.split(":")[1])
    delete_goal(goal_id)

    await callback.message.edit_text(MSG_GOAL_DELETED)
    await callback.answer()
