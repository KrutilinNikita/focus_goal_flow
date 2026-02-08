import logging
from datetime import date, datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from config import REMINDER_TIMES, TIMEZONE
from database.goals import get_pending_goals_for_date, close_day, get_goal_for_date
from database.db import get_connection
from keyboards.goal_actions import goal_actions_kb
from texts import MSG_REMINDER_WITH_GOAL, MSG_REMINDER_NO_GOAL, MSG_GOAL_CARD, STATUS_PENDING

logger = logging.getLogger(__name__)


def get_time_until_midnight() -> str:
    now = datetime.now()
    midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    delta = midnight - now

    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    return f"{hours}ч {minutes}мин"


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
                    goal_id, _, goal_date, goal_text, status, _, _, _ = goal
                    card = MSG_GOAL_CARD.format(
                        date=goal_date,
                        goal_text=goal_text,
                        status=STATUS_PENDING
                    )
                    await bot.send_message(
                        user_id,
                        f"{MSG_REMINDER_WITH_GOAL}\n\n{card}",
                        reply_markup=goal_actions_kb(goal_id)
                    )
            else:
                time_left = get_time_until_midnight()
                await bot.send_message(
                    user_id,
                    MSG_REMINDER_NO_GOAL.format(time_left=time_left)
                )
        except Exception as e:
            logger.error(f"Failed to send reminder to {user_id}: {e}")


async def close_day_job():
    yesterday = date.today() - timedelta(days=1)
    close_day(yesterday)
    logger.info(f"Day closed: {yesterday}")


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

    # Close day at 00:01
    scheduler.add_job(
        close_day_job,
        "cron",
        hour=0,
        minute=1
    )

    return scheduler
