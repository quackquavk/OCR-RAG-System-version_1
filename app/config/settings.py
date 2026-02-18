# import firebase_admin
# from firebase_admin import credentials, db
# import logging

# logger = logging.getLogger(__name__)

# _firebase_app = None


# def init_firebase():
#     global _firebase_app

#     if _firebase_app is not None:
#         return db

#     try:
#         cred = credentials.Certificate("app/config/serviceAccountKey.json")
#         _firebase_app = firebase_admin.initialize_app(
#             cred,
#             {"databaseURL": "https://ocr-system-b3084-default-rtdb.firebaseio.com/"},
#         )
#         logger.info("Firebase Realtime Database initialized successfully!")
#         return db

#     except Exception as e:
#         logger.exception(f"Error initializing Firebase: {e}")
#         raise

# ================================================================================================



import os
import json
import firebase_admin
from firebase_admin import credentials, db, firestore
import logging

logger = logging.getLogger(__name__)

_firebase_app = None
_firestore_client = None


def init_firebase():
    global _firebase_app, _firestore_client

    if _firebase_app is not None:
        if _firestore_client is None:
             _firestore_client = firestore.client()
        return db

    try:
        # Check if credentials are provided in environment variable as JSON string
        firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_json:
            logger.info("Initializing Firebase using FIREBASE_CREDENTIALS_JSON")
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback to local file
            cred_path = os.getenv("FIREBASE_CREDENTIALS", "app/config/firebase-key.json")
            logger.info(f"Initializing Firebase using file: {cred_path}")
            cred = credentials.Certificate(cred_path)

        _firebase_app = firebase_admin.initialize_app(
            cred,
            {"databaseURL": "https://receipt-ai-37f50-default-rtdb.asia-southeast1.firebasedatabase.app/"},
        )
        _firestore_client = firestore.client()
        logger.info("Firebase Realtime Database and Firestore initialized successfully!")
        return db

    except Exception as e:
        logger.exception(f"Error initializing Firebase: {e}")
        raise


def get_firestore_client():
    global _firestore_client
    if _firestore_client is None:
        init_firebase()
    return _firestore_client
