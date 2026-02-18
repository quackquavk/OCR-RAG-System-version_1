
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("SECRET_ENCRYPTION_KEY")
print(f"Current Key: {key}")

try:
    if not key:
        raise ValueError("Key is empty")
    Fernet(key.encode())
    print("✅ Current key is VALID.")
except Exception as e:
    print(f"❌ Current key is INVALID: {e}")
    new_key = Fernet.generate_key().decode()
    print(f"ℹ️ Generated NEW VALID Key: {new_key}")
    print("Please update your .env file with this new key.")
