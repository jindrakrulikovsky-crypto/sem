from database_manager import DatabaseManager
import json
import os
import sys
import time

class UserInterface:
    def __init__(self):
        self.login_attempts_file = "login_attempts.json"
        self.max_attempts = 3
        self.db = DatabaseManager()
        self.login_attempts = self._load_attempts()
    
    def _load_attempts(self):
        try:
            with open(self.login_attempts_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_attempts(self):
        with open(self.login_attempts_file, 'w') as f:
            json.dump(self.login_attempts, f)

    def cmd_register(self, username, password):
        if self.db.register_user(username, password):
            print(f"Registered user '{username}'")
            return 0
        print(f"Username '{username}' is already taken")
        return 1


    def cmd_login(self, username, password):
        raw_data = self.login_attempts.get(username, {})
        attempt_data = {"attempts": 0, "timestamp": 0}
        attempt_data.update(raw_data)
        attempts = attempt_data["attempts"]
        timestamp = attempt_data["timestamp"]
        
        if attempts >= self.max_attempts:
            time_locked = time.time() - timestamp
            if time_locked < 60:
                seconds_remaining = int(60 - time_locked)
                print(f"Account '{username}' locked. Try again in {seconds_remaining} seconds", file=sys.stderr)
                return 1
            else:
                self.login_attempts[username] = {"attempts": 0, "timestamp": 0}
                self._save_attempts()
                attempts = 0
                timestamp = 0
        
        user_id = self.db.verify_login(username, password)

        if user_id is not None:
            print(f"Login OK (user_id={user_id})")
            self.login_attempts[username] = {"attempts": 0, "timestamp": 0}
            self._save_attempts()
            return 0
        
        attempts += 1
        if attempts >= self.max_attempts:
            self.login_attempts[username] = {
                "attempts": attempts,
                "timestamp": time.time()
            }
            print(f"Login failed: Account locked for 60 seconds", file=sys.stderr)
        else:
            self.login_attempts[username] = {
                "attempts": attempts,
                "timestamp": 0
            }
            remaining = self.max_attempts - attempts
            print(f"Login failed: invalid credentials ({remaining} attempts remaining)", file=sys.stderr)
        
        self._save_attempts()
        return 1


    def cmd_check(self, username):
        exists = self.db.username_exists(username)
        if exists:
            print(f"Username '{username}' exists")
        else:
            print(f"Username '{username}' not found")
        return 0

    def run_command(self, opts: dict) -> int:
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
        f"  python {script_name} register <username> <password>\n"
        f"  python {script_name} login <username> <password>\n"
        f"  python {script_name} check <username>\n"
    )
    print(msg, file=sys.stderr)


def parse_args(argv: list[str]) -> dict:
    args = list(argv)
    
    if not args:
        print_usage()
        raise SystemExit(2)

    command = args[0]
    rest = args[1:]

    if command == "register":
        if len(rest) != 2:
            print("Error: register needs <username> <password>", file=sys.stderr)
            print_usage()
            raise SystemExit(2)
        return {"command": command, "username": rest[0], "password": rest[1]}

    if command == "login":
        if len(rest) != 2:
            print("Error: login needs <username> <password>", file=sys.stderr)
            print_usage()
            raise SystemExit(2)
        return {"command": command, "username": rest[0], "password": rest[1]}

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
