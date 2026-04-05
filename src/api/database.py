import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import time
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/streamrec")

def get_db_connection():
    # Retry mechanism for Docker startup
    max_retries = 15
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = True
            return conn
        except psycopg2.OperationalError as e:
            if i == max_retries - 1:
                raise e
            logger.warning(f"Database not ready. Retrying in 2 seconds... ({i+1}/{max_retries})")
            time.sleep(2)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            preferred_genres TEXT DEFAULT '[]',
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS wishlist (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            movie_title VARCHAR(255),
            movie_genres TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, movie_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id SERIAL PRIMARY KEY,
            movieId INTEGER UNIQUE NOT NULL,
            title VARCHAR(255) NOT NULL,
            genres TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.close()
    conn.close()

def seed_admin(get_hash_fn):
    """Create default admin user if not exists. Hash function provided at runtime."""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        admin_hash = get_hash_fn("admin")
        c.execute(
            '''INSERT INTO users (username, password_hash, is_admin) 
               VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING''',
            ('admin@gmail.com', admin_hash, True)
        )
    except Exception as e:
        logger.warning(f"Failed to create default admin: {e}")
    finally:
        c.close()
        conn.close()

def is_username_taken(username: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT 1 FROM users WHERE username = %s', (username,))
    exists = c.fetchone() is not None
    c.close()
    conn.close()
    return exists

def create_user(username: str, password_hash: str, preferred_genres: list = None, is_admin: bool = False):
    conn = get_db_connection()
    genres_str = json.dumps(preferred_genres or [])
    c = conn.cursor(cursor_factory=RealDictCursor)
    try:
        c.execute(
            'INSERT INTO users (username, password_hash, preferred_genres, is_admin) VALUES (%s, %s, %s, %s) RETURNING id',
            (username, password_hash, genres_str, is_admin)
        )
        user_id = c.fetchone()['id']
        return get_user_by_id(user_id)
    except psycopg2.IntegrityError:
        return None  # Username exists
    finally:
        c.close()
        conn.close()

def get_user_by_username(username: str):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = c.fetchone()
    c.close()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id: int):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = c.fetchone()
    c.close()
    conn.close()
    return dict(user) if user else None

def update_user_genres(user_id: int, genres: list):
    conn = get_db_connection()
    genres_str = json.dumps(genres)
    c = conn.cursor()
    c.execute('UPDATE users SET preferred_genres = %s WHERE id = %s', (genres_str, user_id))
    c.close()
    conn.close()

def seed_existing_users(known_users: set, get_hash_fn):
    """Seed the database with all existing users from the MovieLens matrix so they can log in seamlessly.
    get_hash_fn is expected to be passlib's get_password_hash, called at runtime inside Docker."""
    conn = get_db_connection()
    c = conn.cursor()
    # Generate the hash once and share it for all seeded users
    password_hash = get_hash_fn("password123")
    
    users_to_insert = [(f"user_{uid}@gmail.com", password_hash) for uid in known_users]

    # Batch insert only missing users (let database auto-generate IDs)
    try:
        from psycopg2.extras import execute_values
        execute_values(
            c,
            "INSERT INTO users (username, password_hash) VALUES %s ON CONFLICT (username) DO NOTHING",
            users_to_insert
        )
        conn.commit()
    except Exception as e:
        logger.warning(f"Failed to seed users: {e}")
        conn.rollback()
    finally:
        c.close()
        conn.close()

# ============================================================================
# Wishlist Functions
# ============================================================================

def add_to_wishlist(user_id: int, movie_id: int, title: str = "", genres: str = ""):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO wishlist (user_id, movie_id, movie_title, movie_genres) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id, movie_id) DO NOTHING',
            (user_id, movie_id, title, genres)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to add to wishlist: {e}")
        conn.rollback()
        return False
    finally:
        c.close()
        conn.close()

def remove_from_wishlist(user_id: int, movie_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM wishlist WHERE user_id = %s AND movie_id = %s', (user_id, movie_id))
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to remove from wishlist: {e}")
        conn.rollback()
        return False
    finally:
        c.close()
        conn.close()

def get_user_wishlist(user_id: int):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    try:
        c.execute('SELECT * FROM wishlist WHERE user_id = %s ORDER BY added_at DESC', (user_id,))
        wishlist = c.fetchall()
        return [dict(item) for item in wishlist] if wishlist else []
    except Exception as e:
        logger.warning(f"Failed to get wishlist: {e}")
        return []
    finally:
        c.close()
        conn.close()

def is_in_wishlist(user_id: int, movie_id: int) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT 1 FROM wishlist WHERE user_id = %s AND movie_id = %s', (user_id, movie_id))
        result = c.fetchone() is not None
        return result
    except Exception as e:
        logger.warning(f"Failed to check wishlist: {e}")
        return False
    finally:
        c.close()
        conn.close()

# ============================================================================
# Admin Functions
# ============================================================================

def get_all_users(limit: int = 100, offset: int = 0):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    try:
        c.execute('SELECT id, username, is_admin, created_at FROM users ORDER BY id DESC LIMIT %s OFFSET %s', (limit, offset))
        users = c.fetchall()

        # Use a separate cursor (non-RealDict) for COUNT to avoid dict indexing issues
        c_count = conn.cursor()
        c_count.execute('SELECT COUNT(*) FROM users')
        total = c_count.fetchone()[0]
        c_count.close()

        return [dict(u) for u in users] if users else [], total
    except Exception as e:
        logger.warning(f"Failed to get users: {e}")
        return [], 0
    finally:
        c.close()
        conn.close()

def delete_user(user_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM users WHERE id = %s AND id != 1', (user_id,))  # Protect admin user
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to delete user: {e}")
        conn.rollback()
        return False
    finally:
        c.close()
        conn.close()

def promote_user_to_admin(user_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('UPDATE users SET is_admin = TRUE WHERE id = %s', (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to promote user: {e}")
        conn.rollback()
        return False
    finally:
        c.close()
        conn.close()

def demote_admin_to_user(user_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('UPDATE users SET is_admin = FALSE WHERE id = %s AND id != 1', (user_id,))  # Protect main admin
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to demote admin: {e}")
        conn.rollback()
        return False
    finally:
        c.close()
        conn.close()

def get_all_movies_from_db(limit: int = 100, offset: int = 0):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    try:
        c.execute('SELECT * FROM movies ORDER BY movieId DESC LIMIT %s OFFSET %s', (limit, offset))
        movies = c.fetchall()
        c.execute('SELECT COUNT(*) FROM movies')
        total = c.fetchone()[0]
        return [dict(m) for m in movies] if movies else [], total
    except Exception as e:
        logger.warning(f"Failed to get movies from db: {e}")
        return [], 0
    finally:
        c.close()
        conn.close()

def delete_movie(movie_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM movies WHERE id = %s', (movie_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to delete movie: {e}")
        conn.rollback()
        return False
    finally:
        c.close()
        conn.close()