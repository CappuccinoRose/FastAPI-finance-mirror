# generate_hash.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "admin123"
hashed_password = pwd_context.hash(password)

print(f"Password: {password}")
print(f"Hashed Password: {hashed_password}")
