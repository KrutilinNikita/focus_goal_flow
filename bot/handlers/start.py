from aiogram import F
from aiogram.types import Message
from aiogram.filters import CommandStart

from . import router
from database import get_or_create_user
from keyboards import main_menu_kb
from texts import MSG_WELCOME


@router.message(CommandStart())
async def cmd_start(message: Message):
    get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    await message.answer(MSG_WELCOME, reply_markup=main_menu_kb())
