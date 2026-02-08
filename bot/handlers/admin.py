import csv
import logging
from datetime import date, timedelta
from pathlib import Path
from aiogram import F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from . import router
from config import ADMINS_FILE, BASE_DIR
from database.db import get_connection
from texts import MSG_NOT_ADMIN

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    if not ADMINS_FILE.exists():
        return False

    with open(ADMINS_FILE, "r") as f:
        admin_ids = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    return str(user_id) in admin_ids


async def check_admin(message: Message) -> bool:
    if is_admin(message.from_user.id):
        return True
    await message.answer(MSG_NOT_ADMIN.format(user_id=message.from_user.id))
    return False


@router.message(Command("admin_stats"))
async def admin_stats(message: Message):
    if not await check_admin(message):
        return

    logger.info(f"admin command /admin_stats by {message.from_user.id}")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM goals")
    total_goals = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM goals WHERE goal_date = ?",
        (date.today().isoformat(),)
    )
    goals_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM goals WHERE status = 'done'")
    done_goals = cursor.fetchone()[0]

    done_percent = round(done_goals / total_goals * 100) if total_goals > 0 else 0

    conn.close()

    await message.answer(
        f"📊 Статистика бота:\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"🎯 Всего целей: {total_goals}\n"
        f"📅 Целей сегодня: {goals_today}\n"
        f"✅ Процент выполненных: {done_percent}%"
    )


@router.message(Command("admin_export"))
async def admin_export(message: Message):
    if not await check_admin(message):
        return

    logger.info(f"admin command /admin_export by {message.from_user.id}")

    conn = get_connection()
    cursor = conn.cursor()

    # Export users
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    users_file = BASE_DIR / "users.csv"
    with open(users_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "username", "first_name", "first_seen_at"])
        writer.writerows(users)

    # Export goals
    cursor.execute("SELECT * FROM goals")
    goals = cursor.fetchall()

    goals_file = BASE_DIR / "goals.csv"
    with open(goals_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "user_id", "goal_date", "goal_text", "status", "created_at", "completed_at", "locked_after_done"])
        writer.writerows(goals)

    conn.close()

    await message.answer_document(FSInputFile(users_file))
    await message.answer_document(FSInputFile(goals_file))


@router.message(Command("admin_metric"))
async def admin_metric(message: Message):
    if not await check_admin(message):
        return

    logger.info(f"admin command /admin_metric by {message.from_user.id}")

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        await message.answer("❌ matplotlib не установлен")
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Get data for last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    cursor.execute(
        """SELECT goal_date, COUNT(DISTINCT user_id), COUNT(*)
           FROM goals
           WHERE goal_date >= ? AND goal_date <= ?
           GROUP BY goal_date
           ORDER BY goal_date""",
        (start_date.isoformat(), end_date.isoformat())
    )
    data = cursor.fetchall()
    conn.close()

    if not data:
        await message.answer("📊 Нет данных для графика")
        return

    dates = [row[0] for row in data]
    users_count = [row[1] for row in data]
    goals_count = [row[2] for row in data]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.bar(dates, users_count, color='steelblue')
    ax1.set_title('Пользователей с целями по дням')
    ax1.tick_params(axis='x', rotation=45)

    ax2.bar(dates, goals_count, color='coral')
    ax2.set_title('Целей по дням')
    ax2.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    chart_path = BASE_DIR / "metric.png"
    plt.savefig(chart_path, dpi=100)
    plt.close()

    await message.answer_photo(FSInputFile(chart_path))
