import customtkinter as ctk

# 1. Basic configuration
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class MyAccountApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 2. Window Window Properties
        self.title("Account Manager v1.0")
        self.geometry("4000x4400")

        # 3. Adding a Widget (Button)
        self.button = ctk.CTkButton(self, text="Click Me", command=self.button_callback)
        self.button.pack(padx=20, pady=20)

    def button_callback(self):
        print("Button clicked!")

# 4. Start the Application
if __name__ == "__main__":
    app = MyAccountApp()
    app.mainloop()