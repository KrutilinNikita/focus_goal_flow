import logging
from datetime import date, datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.enums import ParseMode

from config import REMINDER_TIMES, TIMEZONE
from database.goals import get_pending_goals_for_date, close_day, get_goal_for_date, get_days_with_completed_goals
from database.db import get_connection
from keyboards.goal_actions import goal_actions_kb, set_goal_kb_tomorrow
from texts import MSG_REMINDER_WITH_GOAL, MSG_GOAL_CARD_TODAY, MSG_GOAL_CARD_TODAY_EMPTY, STATUS_PENDING, MSG_EVENING_REMINDER

logger = logging.getLogger(__name__)

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


def format_date_ru(d: date) -> str:
    return f"{d.day} {MONTHS_RU[d.month]}"


def escape_md(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def get_time_until_midnight() -> str:
    now = datetime.now()
    midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    delta = midnight - now

    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    return f"{hours} ч {minutes} мин"


async def send_reminders(bot: Bot):
    today = date.today()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    for (user_id,) in users:
        goal = get_goal_for_date(user_id, today)

        try:
            if goal:
                if goal[4] != "done":  # status is not done
                    goal_id = goal[0]
                    goal_text = goal[3]
                    card = MSG_GOAL_CARD_TODAY.format(
                        date=escape_md(format_date_ru(today)),
                        goal_text=escape_md(goal_text),
                        status=STATUS_PENDING,
                        time_left=get_time_until_midnight()
                    ).strip()
                    await bot.send_message(
                        user_id,
                        f"{MSG_REMINDER_WITH_GOAL}\n\n{card}",
                        reply_markup=goal_actions_kb(goal_id),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
            else:
                card = MSG_GOAL_CARD_TODAY_EMPTY.format(
                    date=escape_md(format_date_ru(today)),
                    time_left=get_time_until_midnight()
                )
                await bot.send_message(user_id, card, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Failed to send reminder to {user_id}: {e}")


async def close_day_job():
    yesterday = date.today() - timedelta(days=1)
    close_day(yesterday)
    logger.info(f"Day closed: {yesterday}")


async def send_evening_reminder(bot: Bot):
    """Send reminder at 23:00 to set goal for tomorrow"""
    tomorrow = date.today() + timedelta(days=1)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    for (user_id,) in users:
        # Check if user already has goal for tomorrow
        goal = get_goal_for_date(user_id, tomorrow)
        if goal:
            continue  # Skip if already has goal for tomorrow

        try:
            days_with_goals = get_days_with_completed_goals(user_id)
            message = MSG_EVENING_REMINDER.format(days_with_goals=days_with_goals)
            await bot.send_message(
                user_id,
                message,
                reply_markup=set_goal_kb_tomorrow(),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            logger.error(f"Failed to send evening reminder to {user_id}: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    # Reminders
    for time_str in REMINDER_TIMES:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(
            send_reminders,
            "cron",
            hour=hour,
            minute=minute,
            args=[bot]
        )

    # Evening reminder at 23:01 (after regular reminder)
    scheduler.add_job(
        send_evening_reminder,
        "cron",
        hour=23,
        minute=1,
        args=[bot]
    )

    # Close day at 00:01
    scheduler.add_job(
        close_day_job,
        "cron",
        hour=0,
        minute=1
    )

    return scheduler
