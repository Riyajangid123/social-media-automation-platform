from database.connection import get_connection
import json

def get_or_create_user(username: str, email: str, hashed_password: str = None) -> int:
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM social_users WHERE email = %s",
            (email,)
        )
        row = cursor.fetchone()
        if row:
            return row[0] 

        cursor.execute(
            "INSERT INTO social_users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
            (username, email, hashed_password)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    finally:
        cursor.close()
        conn.close()

def save_connected_account(user_id: int, platform: str, access_token: str,
                           refresh_token: str = None, expires_at=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if isinstance(expires_at, int):
            sql_query = """
                INSERT INTO connected_accounts (user_id, platform, access_token, refresh_token, expires_at)
                VALUES (%s, %s, %s, %s, NOW() + %s * INTERVAL '1 second')
                ON CONFLICT (user_id, platform)
                DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at
            """
        else:
            sql_query = """
                INSERT INTO connected_accounts (user_id, platform, access_token, refresh_token, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, platform)
                DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at
            """

        cursor.execute(sql_query, (user_id, platform, access_token, refresh_token, expires_at))
        conn.commit()
    except Exception as db_err:
        print(f"❌ DATABASE CRASH: {db_err}") 
        raise db_err
    finally:
        cursor.close()
        conn.close()

def get_connected_account(user_id: int, platform: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT access_token, refresh_token, expires_at
            FROM connected_accounts
            WHERE user_id = %s AND platform = %s
        """, (user_id, platform))
        row = cursor.fetchone()
        if row:
            return {
                "access_token":  row[0],
                "refresh_token": row[1],
                "expires_at":    row[2]
            }
        return None
    finally:
        cursor.close()
        conn.close()


def save_generated_post(user_id: int, platform: str, topic: str,
                         caption: str, hashtags: list, image_prompt: str = None,
                         image_url: str = None, retry_count: int = 0,
                         human_approved: bool = False) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ai_generated_posts
            (user_id, platform, topic, caption, hashtags, image_prompt, image_url, retry_count, human_approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id, platform, topic, caption,
            json.dumps(hashtags), image_prompt, image_url,
            retry_count, human_approved
        ))
        post_id = cursor.fetchone()[0]
        conn.commit()
        return post_id
    finally:
        cursor.close()
        conn.close()


def mark_post_approved(post_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE ai_generated_posts SET human_approved = TRUE WHERE id = %s",
            (post_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def save_scheduled_post(generated_post_id: int, scheduled_time=None,
                         status: str = "pending") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO scheduled_posts (generated_post_id, scheduled_time, status)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (generated_post_id, scheduled_time, status))
        scheduled_id = cursor.fetchone()[0]
        conn.commit()
        return scheduled_id
    finally:
        cursor.close()
        conn.close()


def mark_post_published(scheduled_id: int, platform_post_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE scheduled_posts
            SET status = 'posted', published_at = NOW(), platform_post_id = %s
            WHERE id = %s
        """, (platform_post_id, scheduled_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def mark_post_failed(scheduled_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE scheduled_posts SET status = 'failed' WHERE id = %s",
            (scheduled_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_pending_scheduled_posts():
    """Used by a background job to find posts that need publishing now"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT sp.id, sp.scheduled_time, gp.platform, gp.caption, gp.hashtags, gp.image_url
            FROM scheduled_posts sp
            JOIN ai_generated_posts gp ON sp.generated_post_id = gp.id
            WHERE sp.status = 'pending' AND sp.scheduled_time <= NOW()
        """)
        rows = cursor.fetchall()
        return [
            {
                "scheduled_id":  r[0],
                "scheduled_time": r[1],
                "platform":      r[2],
                "caption":       r[3],
                "hashtags":      json.loads(r[4]) if r[4] else [],
                "image_url":     r[5]
            }
            for r in rows
        ]
    finally:
        cursor.close()
        conn.close()


def create_user(username: str, email: str, hashed_password: str) -> int:
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO social_users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
            (username, email, hashed_password)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email: str) -> dict:
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, username, email, password FROM social_users WHERE email = %s",
            (email,)
        )
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "email": row[2], "password": row[3]}
        return None
    finally:
        cursor.close()
        conn.close()