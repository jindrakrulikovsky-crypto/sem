import sys
import time

class UserInterface:
    def __init__(self):
        self.login_attempts = 0
        self.max_attempts = 3

    def password_strength_check(self, password):
        # Add logic here to check length, numbers, and symbols
        # This will add about 15-20 lines to your code
        score = 0
        if len(password) >= 8: score += 1
        # ... additional checks ...
        return score

    def main_menu(self):
        while True:
            print("\n--- ACCOUNT MANAGER ---")
            print("1. Sign Up")
            print("2. Login")
            print("3. Exit")
            
            choice = input("Select an option: ")

            if choice == '1':
                self.handle_signup()
            elif choice == '2':
                if self.login_attempts >= self.max_attempts:
                    print("Too many failed attempts. Access locked.")
                    time.sleep(5) # Penalty timer
                    continue
                self.handle_login()
            elif choice == '3':
                print("Goodbye!")
                sys.exit()
            else:
                print("Invalid choice, try again.")

    def handle_signup(self):
        # Here you would ask for username and password
        # Call password_strength_check() here
        pass

    def handle_login(self):
        # Here you verify the password
        # If wrong, self.login_attempts += 1
        pass

if __name__ == "__main__":
    ui = UserInterface()
    ui.main_menu()