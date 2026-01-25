import sqlite3
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class DatabaseManager:
    """Handles data persistence and password hashing."""

    def __init__(self, db_name="accounts.db"):
        self.db_name = db_name
        self.ph = PasswordHasher()
        self._init_db()

    def _init_db(self):
        """Creates the table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT
        );
        """
        self._execute(create_table_sql)

    def _execute(self, sql, params=(), fetch=False):
        """Helper to run SQL safely using context manager."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None

    def register_user(self, username, password):
        """Hashes the password with Argon2 and saves to DB."""
        try:
            hashed_pw = self.ph.hash(password)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hashed_pw, timestamp),
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Username taken

    def verify_login(self, username, password):
        """
        1. Fetch the hash for the user.
        2. Verify using Argon2's internal logic.
        """
        result = self._execute(
            "SELECT password_hash, id FROM users WHERE username=?",
            (username,),
            fetch=True,
        )
        if result:
            stored_hash, user_id = result[0]
            try:
                self.ph.verify(stored_hash, password)
                return user_id
            except VerifyMismatchError:
                return None
        return None  # Username not found

    def username_exists(self, username):
        """Check if a username already exists in the database."""
        result = self._execute(
            "SELECT 1 FROM users WHERE username=?",
            (username,),
            fetch=True,
        )
        return len(result) > 0

    def get_user_profile(self, user_id):
        raise NotImplementedError("get_user_profile is not implemented")

    def update_password(self, user_id, new_password):
        raise NotImplementedError("update_password is not implemented")
