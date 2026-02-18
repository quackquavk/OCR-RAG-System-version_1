
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"
STATUS_ENDPOINT = "/api/v1/groq/status"
USER_ID = "test_user_new_123"

def check_status():
    url = f"{BASE_URL}{STATUS_ENDPOINT}"
    headers = {"X-User-Id": USER_ID}

    logger.info(f"Checking status for user: {USER_ID}")
    try:
        response = requests.get(url, headers=headers, timeout=5)
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response Data: {data}")
            if data.get("has_key") is False:
                logger.info("SUCCESS: API correctly reports no key for new user.")
            else:
                logger.error("FAILURE: API reports key exists for new user!")
        else:
            logger.error(f"FAILURE: API returned unexpected status code: {response.text}")
    
    except Exception as e:
        logger.error(f"Request failed: {e}")

if __name__ == "__main__":
    check_status()
