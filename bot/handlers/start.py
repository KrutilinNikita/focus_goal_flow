from aiogram import F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command

from . import router
from database import get_or_create_user, create_wish
from database.wishes import get_all_wishes
from keyboards import main_menu_kb
from config import ADMINS_FILE
from texts import MSG_WELCOME, MSG_WELCOME_EMOJI, MSG_HELP, MSG_HELP_ADMIN, DEFAULT_WISH_TEXT


def welcome_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Цель на сегодня", callback_data="goal_today")]
    ])


def is_admin(user_id: int) -> bool:
    if not ADMINS_FILE.exists():
        return False
    with open(ADMINS_FILE, "r") as f:
        admin_ids = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return str(user_id) in admin_ids


def ensure_default_wish(user_id: int):
    """Create default 'Без категории' wish if user has no wishes"""
    all_wishes = get_all_wishes(user_id)
    has_default = any(w[2] == DEFAULT_WISH_TEXT for w in all_wishes)
    if not has_default:
        create_wish(user_id, DEFAULT_WISH_TEXT)


@router.message(CommandStart())
async def cmd_start(message: Message):
    get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    # Ensure default wish exists
    ensure_default_wish(message.from_user.id)

    # Send greeting emoji
    await message.answer(MSG_WELCOME_EMOJI, reply_markup=main_menu_kb())
    # Send welcome message with MarkdownV2 formatting and inline button
    await message.answer(MSG_WELCOME, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=welcome_kb())


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = MSG_HELP
    if is_admin(message.from_user.id):
        text += MSG_HELP_ADMIN
    await message.answer(text)
