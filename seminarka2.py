import sqlite3
import customtkinter as ctk
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# ==============================================================================
# 1. MODEL: DATABASE LAYER
#    Handles data persistence and business logic (hashing).
# ==============================================================================
class DatabaseManager:
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
                (username, hashed_pw, timestamp)
            )
            return True
        except sqlite3.IntegrityError:
            return False # Username taken

    def verify_login(self, username, password):
        """
        1. Fetch the hash for the user.
        2. Verify using Argon2's internal logic.
        """
        result = self._execute(
            "SELECT password_hash, id FROM users WHERE username=?", 
            (username,), 
            fetch=True
        )

        if result:
            stored_hash, user_id = result[0]
            try:
                # Argon2 compares the provided password against the stored hash/salt
                self.ph.verify(stored_hash, password)
                return user_id
            except VerifyMismatchError:
                # Password was wrong
                return None
        
        return None # Username not found
    def username_exists(self, username):
        """Check if a username already exists in the database."""
        result = self._execute(
            "SELECT 1 FROM users WHERE username=?", 
            (username,), 
            fetch=True
        )
        return len(result) > 0

    def get_user_profile(self, user_id):
        None
    def update_password(self, user_id, new_password):
        None

    
"""
# ==============================================================================
# 2. VIEW & CONTROLLER: GUI LAYER
#    Handles user interaction and updates the display.
# ==============================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Profi Auth System")
        self.geometry("600x400")
        
        # Initialize Logic
        self.db = DatabaseManager()
        self.current_user_id = None

        # Container for stacking frames
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        # We loop through our Frame classes to create them all at start
        for F in (LoginFrame, RegisterFrame, DashboardFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginFrame)

    def show_frame(self, frame_class):
        """"""Lifts the requested frame to the top.""""""
        frame = self.frames[frame_class]
        frame.tkraise()

    def login_success(self, user_id):
        self.current_user_id = user_id
        # Example of interface "changing IRL" -> Update dashboard data before showing
        self.frames[DashboardFrame].update_display(user_id)
        self.show_frame(DashboardFrame)


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # UI Elements
        label = ctk.CTkLabel(self, text="System Login", font=("Arial", 24))
        label.pack(pady=20)

        self.entry_user = ctk.CTkEntry(self, placeholder_text="Username")
        self.entry_user.pack(pady=10)

        self.entry_pass = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.entry_pass.pack(pady=10)

        btn_login = ctk.CTkButton(self, text="Login", command=self.attempt_login)
        btn_login.pack(pady=10)
        
        btn_reg = ctk.CTkButton(self, text="Go to Register", 
                                command=lambda: controller.show_frame(RegisterFrame),
                                fg_color="transparent", border_width=2)
        btn_reg.pack(pady=10)

    def attempt_login(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        
        # Logic is delegated to the main App controller
        if self.controller.db.verify_login(u, p):
            print("Access Granted")
            self.controller.login_success(u)
        else:
            print("Access Denied") # In real app, show a label error
            self.entry_pass.configure(border_color="red") # Visual feedback

class RegisterFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = ctk.CTkLabel(self, text="Create Account", font=("Arial", 24))
        label.pack(pady=20)
        
        self.entry_user = ctk.CTkEntry(self, placeholder_text="New Username")
        self.entry_user.pack(pady=10)
        
        self.entry_pass = ctk.CTkEntry(self, placeholder_text="New Password", show="*")
        self.entry_pass.pack(pady=10)

        btn_reg = ctk.CTkButton(self, text="Create Account", command=self.register)
        btn_reg.pack(pady=10)
        
        btn_back = ctk.CTkButton(self, text="Back", 
                                 command=lambda: controller.show_frame(LoginFrame),
                                 fg_color="gray")
        btn_back.pack(pady=10)

    def register(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        if self.controller.db.register_user(u, p):
            print("Registered!")
            self.controller.show_frame(LoginFrame)
        else:
            print("Username taken")

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.label = ctk.CTkLabel(self, text="Welcome...", font=("Arial", 24))
        self.label.pack(pady=50)
        
        btn_logout = ctk.CTkButton(self, text="Logout", 
                                   command=lambda: controller.show_frame(LoginFrame))
        btn_logout.pack()

    def update_display(self, username):
        """"""Called when switching to this frame to update dynamic info""""""
        self.label.configure(text=f"Welcome back, {username}!")
"""

# --- ENTRY POINT ---
if __name__ == "__main__":
    app = App()
    app.mainloop()