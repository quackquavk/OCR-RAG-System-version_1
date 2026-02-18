
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def check_env():
    print("Checking environment configuration...")
    
    # Check Encryption Key
    encryption_key = os.getenv("SECRET_ENCRYPTION_KEY")
    if encryption_key:
        print("SECRET_ENCRYPTION_KEY is set.")
    else:
        print("SECRET_ENCRYPTION_KEY is MISSING!")

    # Check Firebase Credentials
    firebase_json_env = os.getenv("FIREBASE_CREDENTIALS_JSON")
    firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS")
    
    if firebase_json_env:
        print("FIREBASE_CREDENTIALS_JSON is set.")
    elif firebase_cred_path:
        print(f"FIREBASE_CREDENTIALS points to: {firebase_cred_path}")
        if os.path.exists(firebase_cred_path):
             print(f"Credentials file exists at: {firebase_cred_path}")
        else:
             print(f"Credentials file NOT FOUND at: {firebase_cred_path}")
    else:
        # Check default path
        default_path = "app/config/firebase-key.json"
        print(f"Checking default Firebase path: {default_path}")
        if os.path.exists(default_path):
            print(f"Default credentials file exists at: {default_path}")
        else:
            print(f"Default credentials file NOT FOUND at: {default_path}")
            print("No valid Firebase configuration found (Env var or file).")

if __name__ == "__main__":
    check_env()
