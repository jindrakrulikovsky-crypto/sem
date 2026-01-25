from argon2 import PasswordHasher

# 1. Initialize the hasher
ph = PasswordHasher()

# 2. Hash a password (One-way encoding)
# This produces a string that includes the salt and the parameters used
hashed_pw = ph.hash("1")
print(hashed_pw) 

# 3. Verify a password later
try:
    ph.verify(hashed_pw, "user_password_123")
    print("Login Successful!")
except:
    print("Invalid Password!")