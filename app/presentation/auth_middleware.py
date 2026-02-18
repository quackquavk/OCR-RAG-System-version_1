
import os
import jwt
import logging
from typing import Optional
from dotenv import load_dotenv
from fastapi import Request, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
from typing import Optional

load_dotenv()

# Note: Ensure JWT_SECRET is set in your .env file
JWT_SECRET = os.getenv("SECRET_KEY")
# ALGORITHM = "HS256"

security = HTTPBearer()

async def get_user_id_from_header(
    x_user_id: Optional[str]  = Header(None, alias="X-User-Id")
) -> str:
    """
    Extracts the user ID directly from the X-User-Id header.
    Bypasses JWT validation for specific endpoints that require simplified identification.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header"
        )
    return x_user_id or "test-user-1"

# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     x_active_company: str = Header(...),
#     x_company_name: Optional[str] = Header(None)
# ) -> dict:
#     """
#     Decodes and validates JWT token, ensuring the user has access to the requested company.
#     """
#     token = credentials.credentials
#     try:
#         # SECURE: Always verify the signature in production
#         # payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM],options={"verify_signature": False})
#         payload = jwt.decode(token, JWT_SECRET, options={"verify_signature": False})


#         # Validate required fields
#         if "userId" not in payload:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED, 
#                 detail="Invalid token payload: missing userId"
#             )

#         # Inject context for the rest of the request lifecycle
#         payload["activeCompany"] = x_active_company
#         payload["companyName"] = x_company_name

#         return payload

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
#     except jwt.InvalidTokenError as e:
#         logger.error(f"JWT Validation Error: {e}")
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
   




# ============================================================================
# TEST CODE (ACTIVE) - Bypasses authentication for testing
# ============================================================================
from fastapi import Header
from typing import Optional

async def get_current_user(
    x_active_company: Optional[str] = Header(default="test-company-1"),
    x_company_name: Optional[str] = Header(default="Brand Builder 1"),
) -> dict:
    """
    TEST VERSION - Returns mock user data for testing without authentication.

    This bypasses JWT validation and returns a test user.

    Optional Headers (will use defaults if not provided):
    - X-Active-Company: Company ID (default: "test-company-123")
    - X-Company-Name: Company name (default: "Test Company Ltd")

    Returns a mock user with:
    - userId: "test-user-001"
    - companies: ["test-company-123", "test-company-456"]
    - activeCompany: From header or default
    - companyName: From header or default
    """
    # print("⚠️  WARNING: Using TEST authentication - No JWT validation!")
    # print(f"📝 Test User ID: test-user-001")
    # print(f"🏢 Test Company: {x_company_name} (ID: {x_active_company})")

    return {
        "userId": "test-user-1",
        "companies": ["test-company-1", "test-company-456"],
        "activeCompany": x_active_company,
        "companyName": x_company_name,
    }