from database.connection import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password     TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS connected_accounts (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            platform VARCHAR(40) NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_generated_posts (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            platform VARCHAR(50) NOT NULL,
            topic VARCHAR(255),

            caption TEXT,
            hashtags TEXT,
            image_prompt TEXT,
            image_url TEXT,

            created_at TIMESTAMPTZ DEFAULT NOW(),

            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id SERIAL PRIMARY KEY,
            generated_post_id INT NOT NULL,

            scheduled_time TIMESTAMPTZ,
            status VARCHAR(20) DEFAULT 'pending',
            published_at TIMESTAMPTZ,
            platform_post_id VARCHAR(100),

            created_at TIMESTAMPTZ DEFAULT NOW(),

            FOREIGN KEY (generated_post_id)
                REFERENCES ai_generated_posts(id)
                ON DELETE CASCADE
        );
        """)

        conn.commit()
        print("All tables created successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Error creating tables: {e}")

    finally:
        cursor.close()
        conn.close()