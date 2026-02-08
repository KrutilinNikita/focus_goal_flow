from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command

from . import router
from database import get_user_stats
from texts import MSG_STATS


@router.message(Command("stats"))
async def show_stats(message: Message):
    stats = get_user_stats(message.from_user.id)

    await message.answer(MSG_STATS.format(**stats))
