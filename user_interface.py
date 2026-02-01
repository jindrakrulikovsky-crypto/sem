from database_manager import DatabaseManager
import os
import sys
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