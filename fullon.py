import sqlite3
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class DatabaseManager:
    """Handles data persistence and password hashing, and rate limiting."""

    def __init__(self, db_name="accounts.db"):
        self.db_name = db_name
        self.ph = PasswordHasher()
        self._init_db()

    def _init_db(self):
        """Creates the table if it doesn't exist."""
        create_users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT
        );
        """
        self._execute(create_users_sql)

        create_attempts_sql = """
        CREATE TABLE IF NOT EXISTS login_attempts (
            username TEXT PRIMARY KEY COLLATE NOCASE,
            attempt_count INTEGER DEFAULT 0,
            last_attempt_time REAL
        );
        """
        self._execute(create_attempts_sql)

    def _execute(self, sql, params=(), fetch=False):
        """Helper to run SQL safely using context manager."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
        
    def validate_credentials(self, username, password):
        """
        Validates username and password strength.
        - Username: 3-20 alphanumeric characters.
        - Password: Minimum 8 characters.
        """
        if not (username and isinstance(username, str) and username.isalnum()):
            return False, "Username must be alphanumeric."
        if not (3 <= len(username) <= 20):
            return False, "Username must be between 3 and 20 characters."
        if not (password and len(password) >= 8):
            return False, "Password must be at least 8 characters long."
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain at least one uppercase letter, one lowercase letter, and one number."
        return True, "Success"

    def register_user(self, username, password):
        """Hashes the password with Argon2 and saves to DB."""
        is_valid, message = self.validate_credentials(username, password)
        if not is_valid:
            return False, message
        try:
            hashed_pw = self.ph.hash(password)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hashed_pw, timestamp),
            )
            return True, "Success"
        except sqlite3.IntegrityError:
            return False, "Username already exists."

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
        return None

    def username_exists(self, username):
        """Check if a username already exists in the database."""
        result = self._execute(
            "SELECT 1 FROM users WHERE username=?",
            (username,),
            fetch=True,
        )
        return len(result) > 0
    def get_lockout_status(self, username, max_attempts=3, lockout_duration=60):
        """
        Checks if the user is currently locked out.
        Returns: (is_locked: bool, seconds_remaining: int)
        """
        row = self._execute(
            "SELECT attempt_count, last_attempt_time FROM login_attempts WHERE username=?",
            (username,),
            fetch=True,
        )
        if not row:
            return False, 0
        attempts, last_time = row[0]
        if last_time is None: last_time = 0

        time_passed = time.time() - last_time
        if time_passed > lockout_duration:
            return False, 0
        
        if attempts >= max_attempts:
            return True, int(lockout_duration - time_passed)
        
        return False, 0
    
    def handle_successful_login(self, username):
        """Resets the failed login attempt count on successful login."""
        self._execute(
            "DELETE FROM login_attempts WHERE username=?",
            (username,),
        )
    
    def handle_failed_login(self, username, lockout_duration=60):
        """Increments the failure counter or resets it if the lockout period expired."""
        current_time = time.time()

        row = self._execute(
            "SELECT attempt_count, last_attempt_time FROM login_attempts WHERE username=?",
            (username,),
            fetch=True,
        )

        if row:
            attempts, last_time = row[0]
            if last_time is None: last_time = 0

            if (current_time - last_time) > lockout_duration:
                new_count = 1
            else:
                new_count = attempts + 1
        else:
            new_count = 1

        self._execute(
            "REPLACE INTO login_attempts (username, attempt_count, last_attempt_time) VALUES (?, ?, ?)",
            (username, new_count, current_time),
        )
        return new_count

import os
import sys
import time
import getpass

class UserInterface:
    def __init__(self):
        self.max_attempts = 3
        self.db = DatabaseManager()

    def cmd_register(self, username, password):
        success, message = self.db.register_user(username, password)
        if success:
            print(f"Registered user '{username}'")
            return 0
        print(f"Registration failed: {message}", file=sys.stderr)
        return 1


    def cmd_login(self, username, password):
        is_locked, wait_time = self.db.get_lockout_status(username)
        if is_locked:
            print(f"Account '{username}' locked. Try again in {wait_time} seconds", file=sys.stderr)
            return 1
        
        user_id = self.db.verify_login(username, password)
        
        if user_id is not None:
            self.db.handle_successful_login(username)
            print(f"Login OK (user_id={user_id})")
            return 0
        
        new_count = self.db.handle_failed_login(username)
        if new_count >= self.max_attempts:
            print(f"Login failed: Account locked for 60 seconds", file=sys.stderr)
        else:
            remaining = self.max_attempts - new_count
            print(f"Login failed: invalid credentials ({remaining} attempts remaining)", file=sys.stderr)
        return 1

    def cmd_check(self, username):
        exists = self.db.username_exists(username)
        if exists:
            print(f"Username '{username}' exists")
        else:
            print(f"Username '{username}' not found")
        return 0

    def run_command(self, opts):
        cmd = opts["command"]
        if cmd == "register":
            return self.cmd_register(opts["username"], opts["password"])
        if cmd == "login":
            return self.cmd_login(opts["username"], opts["password"])
        if cmd == "check":
            return self.cmd_check(opts["username"])
        print_usage()
        return 2
    
def print_usage() -> None:
    script_name = os.path.basename(sys.argv[0])
    msg = (
        "Usage:\n"
        f"  python {script_name} register <username>\n"
        f"  python {script_name} login <username>\n"
        f"  python {script_name} check <username>\n"
    )
    print(msg, file=sys.stderr)

def get_secure_password():
    """
    In interactive terminals, 
    it uses getpass to hide keystrokes from the screen, 
    while in non-interactive modes, 
    it reads directly from standard input to support automation, 
    ensuring passwords are never stored in unsafe shell history logs.
    """
    if sys.stdin.isatty():
        return getpass.getpass("Enter password: ")
    return sys.stdin.readline().strip()


def parse_args(argv: list[str]):
    args = list(argv)
    
    if not args:
        print_usage()
        raise SystemExit(2)

    command = args[0]
    rest = args[1:]

    if command == "register":
        if len(rest) != 1:
            print("Error: register needs <username>", file=sys.stderr)
            print_usage()
            raise SystemExit(2)
        return {"command": command, "username": rest[0], "password": get_secure_password()}

    if command == "login":
        if len(rest) != 1:
            print("Error: login needs <username>", file=sys.stderr)
            print_usage()
            raise SystemExit(2)
        return {"command": command, "username": rest[0], "password": get_secure_password()}

    if command == "check":
        if len(rest) != 1:
            print("Error: check needs <username>", file=sys.stderr)
            print_usage()
            raise SystemExit(2)
        return {"command": command, "username": rest[0]}
        
    print(f"Error: unknown command '{command}'", file=sys.stderr)
    print_usage()
    raise SystemExit(2)


def main():
    opts = parse_args(sys.argv[1:])
    ui = UserInterface()
    return ui.run_command(opts)


if __name__ == "__main__":
    raise SystemExit(main())