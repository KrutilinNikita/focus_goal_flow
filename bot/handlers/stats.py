from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command

from . import router
from database import get_user_stats, get_active_wishes
from texts import MSG_STATS, MSG_STATS_NO_WISHES


def pluralize_days(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return "день"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return "дня"
    else:
        return "дней"


@router.message(Command("stats"))
async def show_stats(message: Message):
    stats = get_user_stats(message.from_user.id)

    # Get wishes for stats
    active_wishes = get_active_wishes(message.from_user.id)
    # Filter out "Без категории"
    user_wishes = [w for w in active_wishes if w[2] != "Без категории"]

    if user_wishes:
        wishes_list = "\n".join([f"• {w[2]}" for w in user_wishes])
        wishes_block = wishes_list
    else:
        wishes_block = MSG_STATS_NO_WISHES

    await message.answer(MSG_STATS.format(
        days_total=stats["days_total"],
        current_streak=stats["current_streak"],
        current_streak_word=pluralize_days(stats["current_streak"]),
        best_streak=stats["best_streak"],
        best_streak_word=pluralize_days(stats["best_streak"]),
        days_with_goals=stats["days_with_goals"],
        goals_done=stats["goals_done"],
        done_percent=stats["done_percent"],
        wishes_block=wishes_block
    ))
