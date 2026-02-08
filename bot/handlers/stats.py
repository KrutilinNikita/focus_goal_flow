from aiogram import F
from aiogram.types import Message

from . import router
from database import get_user_stats
from texts import BTN_STATS, MSG_STATS


@router.message(F.text == BTN_STATS)
async def show_stats(message: Message):
    stats = get_user_stats(message.from_user.id)

    await message.answer(MSG_STATS.format(**stats))
