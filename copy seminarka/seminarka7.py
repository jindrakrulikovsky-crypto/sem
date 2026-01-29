import sys
from database_manager import DatabaseManager


def cmd_register(db: DatabaseManager, username: str, password: str) -> int:
    if db.register_user(username, password):
        print(f"Registered user '{username}'")
        return 0
    print(f"Username '{username}' is already taken")
    return 1


def cmd_login(db: DatabaseManager, username: str, password: str) -> int:
    user_id = db.verify_login(username, password)
    if user_id is not None:
        print(f"Login OK (user_id={user_id})")
        return 0
    print("Login failed: invalid credentials")
    return 1


def cmd_check(db: DatabaseManager, username: str) -> int:
    exists = db.username_exists(username)
    if exists:
        print(f"Username '{username}' exists")
    else:
        print(f"Username '{username}' not found")
    return 0


def print_usage() -> None:
    msg = (
        "Usage:\n"
        "  python seminarka7.py register <username> <password>\n"
        "  python seminarka7.py login <username> <password>\n"
        "  python seminarka7.py check <username>\n"
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


def main() -> int:
    opts = parse_args(sys.argv[1:])
    db = DatabaseManager()  # always use default path

    cmd = opts["command"]
    if cmd == "register":
        return cmd_register(db, opts["username"], opts["password"])
    if cmd == "login":
        return cmd_login(db, opts["username"], opts["password"])
    if cmd == "check":
        return cmd_check(db, opts["username"])

    print_usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
