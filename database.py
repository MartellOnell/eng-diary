"""Database module for storing users and words."""

import sqlite3
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

DATABASE_NAME = "eng_diary.db"


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with required tables."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word_type TEXT NOT NULL,
                word1 TEXT NOT NULL,
                word2 TEXT NOT NULL,
                word3 TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        conn.commit()


def register_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> bool:
    """Register a new user. Returns True if new user, False if already exists."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return False
        
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, datetime.now().isoformat())
        )
        conn.commit()
        return True


def add_translation_word(user_id: int, english: str, russian: str) -> int:
    """Add a translation word pair. Returns the word ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO words (user_id, word_type, word1, word2, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, "translation", english, russian, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid


def add_irregular_verb(user_id: int, form_from: str, form_to: str, form_pair: str) -> int:
    """Add an irregular verb pair. form_pair is '1-2' or '2-3'. Returns the word ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO words (user_id, word_type, word1, word2, word3, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "irregular", form_from, form_to, form_pair, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid


def get_all_words(user_id: int, word_type: Optional[str] = None) -> list:
    """Get all words for a user, optionally filtered by type."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if word_type:
            cursor.execute(
                "SELECT * FROM words WHERE user_id = ? AND word_type = ? ORDER BY created_at",
                (user_id, word_type)
            )
        else:
            cursor.execute(
                "SELECT * FROM words WHERE user_id = ? ORDER BY created_at",
                (user_id,)
            )
        return [dict(row) for row in cursor.fetchall()]


def get_last_words(user_id: int, limit: int = 30, word_type: Optional[str] = None) -> list:
    """Get last N words for a user, optionally filtered by type."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if word_type:
            cursor.execute(
                "SELECT * FROM words WHERE user_id = ? AND word_type = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, word_type, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM words WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
        return [dict(row) for row in cursor.fetchall()]


def get_words_for_wrong_answers(user_id: int, word_type: str, exclude_id: int) -> list:
    """Get words of the same type for generating wrong answers, excluding the current word."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM words WHERE user_id = ? AND word_type = ? AND id != ?",
            (user_id, word_type, exclude_id)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_word_count(user_id: int, word_type: Optional[str] = None) -> int:
    """Get the count of words for a user, optionally filtered by type."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if word_type:
            cursor.execute(
                "SELECT COUNT(*) FROM words WHERE user_id = ? AND word_type = ?",
                (user_id, word_type)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM words WHERE user_id = ?",
                (user_id,)
            )
        return cursor.fetchone()[0]


def get_words_paginated(user_id: int, offset: int = 0, limit: int = 5) -> list:
    """Get words for a user with pagination."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM words WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]


def delete_word(user_id: int, word_id: int) -> bool:
    """Delete a word by ID. Returns True if word was deleted."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM words WHERE id = ? AND user_id = ?",
            (word_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
