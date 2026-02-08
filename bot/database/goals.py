from datetime import datetime, date
from .db import get_connection


def create_goal(user_id: int, goal_date: date, goal_text: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT OR REPLACE INTO goals (user_id, goal_date, goal_text, status, created_at)
           VALUES (?, ?, ?, 'pending', ?)""",
        (user_id, goal_date.isoformat(), goal_text, datetime.now())
    )

    conn.commit()
    conn.close()


def get_goal_for_date(user_id: int, goal_date: date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM goals WHERE user_id = ? AND goal_date = ?",
        (user_id, goal_date.isoformat())
    )
    goal = cursor.fetchone()

    conn.close()
    return goal


def update_goal_status(goal_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()

    completed_at = datetime.now() if status == "done" else None
    locked = 1 if status == "done" else 0

    cursor.execute(
        "UPDATE goals SET status = ?, completed_at = ?, locked_after_done = ? WHERE id = ?",
        (status, completed_at, locked, goal_id)
    )

    conn.commit()
    conn.close()


def update_goal_text(goal_id: int, new_text: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE goals SET goal_text = ? WHERE id = ?",
        (new_text, goal_id)
    )

    conn.commit()
    conn.close()


def delete_goal(goal_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))

    conn.commit()
    conn.close()


def get_user_stats(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Days in system
    cursor.execute(
        "SELECT first_seen_at FROM users WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    if result and result[0]:
        first_seen = datetime.fromisoformat(result[0])
        days_total = (datetime.now() - first_seen).days + 1
    else:
        days_total = 1

    # Goals stats
    cursor.execute(
        "SELECT COUNT(*) FROM goals WHERE user_id = ?",
        (user_id,)
    )
    days_with_goals = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'done'",
        (user_id,)
    )
    goals_done = cursor.fetchone()[0]

    done_percent = round(goals_done / days_with_goals * 100) if days_with_goals > 0 else 0

    # Streaks
    cursor.execute(
        """SELECT goal_date, status FROM goals
           WHERE user_id = ?
           ORDER BY goal_date DESC""",
        (user_id,)
    )
    goals = cursor.fetchall()

    current_streak = 0
    best_streak = 0
    temp_streak = 0

    for goal_date, status in goals:
        if status == "done":
            temp_streak += 1
            best_streak = max(best_streak, temp_streak)
        else:
            temp_streak = 0

    # Current streak
    for goal_date, status in goals:
        if status == "done":
            current_streak += 1
        else:
            break

    conn.close()

    return {
        "days_total": days_total,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "days_with_goals": days_with_goals,
        "goals_done": goals_done,
        "done_percent": done_percent
    }


def get_pending_goals_for_date(goal_date: date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM goals WHERE goal_date = ? AND status = 'pending'",
        (goal_date.isoformat(),)
    )
    goals = cursor.fetchall()

    conn.close()
    return goals


def close_day(goal_date: date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE goals SET status = 'failed' WHERE goal_date = ? AND status = 'pending'",
        (goal_date.isoformat(),)
    )

    conn.commit()
    conn.close()
