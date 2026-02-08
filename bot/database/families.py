from .db import get_connection


def create_family(user_id: int, name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO wish_families (user_id, name) VALUES (?, ?)",
        (user_id, name)
    )

    conn.commit()
    family_id = cursor.lastrowid
    conn.close()
    return family_id


def get_families(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM wish_families WHERE user_id = ? ORDER BY created_at",
        (user_id,)
    )
    families = cursor.fetchall()

    conn.close()
    return families


def get_family(family_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM wish_families WHERE id = ?", (family_id,))
    family = cursor.fetchone()

    conn.close()
    return family


def update_family_name(family_id: int, name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE wish_families SET name = ? WHERE id = ?",
        (name, family_id)
    )

    conn.commit()
    conn.close()


def delete_family(family_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Remove family_id from wishes
    cursor.execute(
        "UPDATE wishes SET family_id = NULL WHERE family_id = ?",
        (family_id,)
    )

    cursor.execute("DELETE FROM wish_families WHERE id = ?", (family_id,))

    conn.commit()
    conn.close()


def get_wishes_in_family(family_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM wishes WHERE family_id = ? ORDER BY position, created_at",
        (family_id,)
    )
    wishes = cursor.fetchall()

    conn.close()
    return wishes


def get_goals_by_family(family_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT goals.* FROM goals
           JOIN wishes ON goals.wish_id = wishes.id
           WHERE wishes.family_id = ? AND goals.status = 'done'
           ORDER BY goals.goal_date DESC""",
        (family_id,)
    )
    goals = cursor.fetchall()

    conn.close()
    return goals
