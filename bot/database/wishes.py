from datetime import datetime
from .db import get_connection


def create_wish(user_id: int, text: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO wishes (user_id, text) VALUES (?, ?)",
        (user_id, text)
    )

    conn.commit()
    wish_id = cursor.lastrowid
    conn.close()
    return wish_id


def get_active_wishes(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM wishes WHERE user_id = ? AND status = 'active' ORDER BY position, created_at",
        (user_id,)
    )
    wishes = cursor.fetchall()

    conn.close()
    return wishes


def get_all_wishes(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM wishes WHERE user_id = ? ORDER BY status, position, created_at",
        (user_id,)
    )
    wishes = cursor.fetchall()

    conn.close()
    return wishes


def get_wish(wish_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM wishes WHERE id = ?", (wish_id,))
    wish = cursor.fetchone()

    conn.close()
    return wish


def update_wish_status(wish_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()

    archived_at = datetime.now() if status == "archived" else None

    cursor.execute(
        "UPDATE wishes SET status = ?, archived_at = ? WHERE id = ?",
        (status, archived_at, wish_id)
    )

    conn.commit()
    conn.close()


def update_wish_text(wish_id: int, text: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE wishes SET text = ? WHERE id = ?",
        (text, wish_id)
    )

    conn.commit()
    conn.close()


def delete_wish(wish_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM wishes WHERE id = ?", (wish_id,))

    conn.commit()
    conn.close()


def count_active_wishes(user_id: int) -> int:
    """Count active wishes excluding 'Без категории'"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM wishes WHERE user_id = ? AND status = 'active' AND text != 'Без категории'",
        (user_id,)
    )
    count = cursor.fetchone()[0]

    conn.close()
    return count


def set_wish_family(wish_id: int, family_id: int = None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE wishes SET family_id = ? WHERE id = ?",
        (family_id, wish_id)
    )

    conn.commit()
    conn.close()


def get_goals_by_wish(wish_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT * FROM goals
           WHERE wish_id = ? AND status = 'done'
           ORDER BY goal_date DESC""",
        (wish_id,)
    )
    goals = cursor.fetchall()

    conn.close()
    return goals
