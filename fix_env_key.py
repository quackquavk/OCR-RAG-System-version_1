
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Generate a valid key
new_key = Fernet.generate_key().decode()
print(f"Generated Key: {new_key}")

env_path = ".env"
new_lines = []
key_updated = False

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    for line in lines:
        if line.strip().startswith("SECRET_ENCRYPTION_KEY="):
            new_lines.append(f"SECRET_ENCRYPTION_KEY={new_key}\n")
            key_updated = True
        else:
            new_lines.append(line)
    
    if not key_updated:
        new_lines.append(f"\nSECRET_ENCRYPTION_KEY={new_key}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)
    
    print("✅ Successfully updated .env with new valid key.")
else:
    print("❌ .env file not found.")
