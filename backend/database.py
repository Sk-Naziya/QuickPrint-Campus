import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'quickprint.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student','admin')),
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_number TEXT NOT NULL UNIQUE,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            copies INTEGER NOT NULL,
            color_mode TEXT NOT NULL,
            page_range TEXT,
            paper_size TEXT NOT NULL,
            pickup_date TEXT NOT NULL,
            pickup_time TEXT NOT NULL,
            total_amount REAL NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Pending',
            order_status TEXT NOT NULL DEFAULT 'Received',
            qr_token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS interest_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
