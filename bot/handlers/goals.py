from datetime import date, timedelta
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from . import router
from database import (
    create_goal, get_goal_for_date, get_goal_by_id,
    update_goal_status, update_goal_text, delete_goal,
    get_active_wishes, get_wish, add_reflection
)
from keyboards import main_menu_kb, goal_actions_kb, goal_done_actions_kb
from keyboards.wishes import select_wish_kb
from keyboards.reflection import reflection_kb
from texts import (
    BTN_GOAL_TODAY, BTN_GOAL_TOMORROW,
    MSG_ENTER_GOAL, MSG_GOAL_SAVED_TODAY, MSG_GOAL_SAVED_TOMORROW,
    MSG_GOAL_CARD, MSG_GOAL_UNDONE, MSG_GOAL_DELETED, MSG_GOAL_EDITED,
    MSG_CANNOT_EDIT_DONE, STATUS_PENDING, STATUS_DONE, STATUS_FAILED,
    MSG_SELECT_WISH, MSG_ASK_REFLECTION, MSG_ENTER_REFLECTION,
    MSG_REFLECTION_SAVED, MSG_REFLECTION_SKIPPED
)


class GoalStates(StatesGroup):
    waiting_for_goal = State()
    waiting_for_wish = State()
    waiting_for_edit = State()
    waiting_for_reflection = State()


def get_status_text(status: str) -> str:
    return {
        "pending": STATUS_PENDING,
        "done": STATUS_DONE,
        "failed": STATUS_FAILED
    }.get(status, status)


def format_goal_card(goal) -> str:
    # goal structure: id, user_id, goal_date, goal_text, status, created_at, completed_at, locked, wish_id, family_snapshot, reflection
    goal_id = goal[0]
    goal_date = goal[2]
    goal_text = goal[3]
    status = goal[4]
    wish_id = goal[8] if len(goal) > 8 else None

    wish_text = ""
    if wish_id:
        wish = get_wish(wish_id)
        if wish:
            wish_text = f"\n💫 {wish[2]}"

    return MSG_GOAL_CARD.format(
        date=goal_date,
        goal_text=goal_text,
        status=get_status_text(status)
    ) + wish_text


@router.message(F.text == BTN_GOAL_TODAY)
async def goal_today(message: Message, state: FSMContext):
    today = date.today()
    goal = get_goal_for_date(message.from_user.id, today)

    if goal:
        kb = goal_done_actions_kb(goal[0]) if goal[4] == "done" else goal_actions_kb(goal[0])
        await message.answer(format_goal_card(goal), reply_markup=kb)
    else:
        await state.update_data(goal_date=today)
        await state.set_state(GoalStates.waiting_for_goal)
        await message.answer(MSG_ENTER_GOAL)


@router.message(F.text == BTN_GOAL_TOMORROW)
async def goal_tomorrow(message: Message, state: FSMContext):
    tomorrow = date.today() + timedelta(days=1)

    await state.update_data(goal_date=tomorrow)
    await state.set_state(GoalStates.waiting_for_goal)
    await message.answer(MSG_ENTER_GOAL)


@router.message(GoalStates.waiting_for_goal)
async def save_goal_text(message: Message, state: FSMContext):
    await state.update_data(goal_text=message.text)

    # Check if user has active wishes
    active_wishes = get_active_wishes(message.from_user.id)

    if active_wishes:
        await state.set_state(GoalStates.waiting_for_wish)
        await message.answer(MSG_SELECT_WISH, reply_markup=select_wish_kb(active_wishes))
    else:
        # No wishes - save goal directly
        await save_goal_with_wish(message, state, None)


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
        await message.answer(format_goal_card(goal), reply_markup=goal_actions_kb(goal[0]))
    else:
        await message.answer(MSG_GOAL_SAVED_TOMORROW, reply_markup=main_menu_kb())


@router.callback_query(F.data.startswith("done:"))
async def mark_done(callback: CallbackQuery, state: FSMContext):
    goal_id = int(callback.data.split(":")[1])
    update_goal_status(goal_id, "done")

    goal = get_goal_by_id(goal_id)

    # Ask for reflection - directly enter text input mode
    await state.update_data(reflection_goal_id=goal_id)
    await state.set_state(GoalStates.waiting_for_reflection)
    await callback.message.edit_text(format_goal_card(goal))
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
    await message.answer(format_goal_card(goal), reply_markup=goal_done_actions_kb(goal_id))


@router.callback_query(F.data.startswith("skip_reflect:"))
async def skip_reflection(callback: CallbackQuery, state: FSMContext):
    goal_id = int(callback.data.split(":")[1])
    goal = get_goal_by_id(goal_id)

    await state.clear()
    await callback.message.edit_text(MSG_REFLECTION_SKIPPED)
    await callback.message.answer(format_goal_card(goal), reply_markup=goal_done_actions_kb(goal_id))
    await callback.answer()


@router.callback_query(F.data.startswith("undone:"))
async def mark_undone(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    goal_id = int(callback.data.split(":")[1])
    update_goal_status(goal_id, "pending")

    goal = get_goal_by_id(goal_id)
    await callback.message.edit_text(format_goal_card(goal), reply_markup=goal_actions_kb(goal_id))
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
    await message.answer(format_goal_card(goal), reply_markup=goal_actions_kb(goal_id))


@router.callback_query(F.data.startswith("delete:"))
async def delete_goal_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    goal_id = int(callback.data.split(":")[1])
    delete_goal(goal_id)

    await callback.message.edit_text(MSG_GOAL_DELETED)
    await callback.answer()
