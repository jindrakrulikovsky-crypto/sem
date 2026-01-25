import sqlite3
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
# ==============================================================================
class DatabaseManager:
    def __init__(self, db_name="accounts.db"):
        self.db_name = db_name
        # We initialize the hasher ONCE here so it's ready for use
        self.ph = PasswordHasher()
        self._init_db()

    def _init_db(self):
        """Creates the database structure if it's missing."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT
        );
        """
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(create_table_sql)

    def register_user(self, username, password):
        """Hashes the password with Argon2 and saves to DB."""
        try:
            # Argon2 automatically handles salting and parameter encoding
            hashed_pw = self.ph.hash(password)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with sqlite3.connect(self.db_name) as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, hashed_pw, timestamp)
                )
            return True
        except sqlite3.IntegrityError:
            return False  # Username is already taken

    def verify_login(self, username, password):
        """
        1. Fetch the hash for the user.
        2. Verify using Argon2's internal logic.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # We ONLY search by username
            cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
            result = cursor.fetchone()

        if result:
            stored_hash = result[0]
            try:
                # Argon2 compares the provided password against the stored hash/salt
                self.ph.verify(stored_hash, password)
                return True 
            except VerifyMismatchError:
                # Password was wrong
                return False
        
        return False # Username not found