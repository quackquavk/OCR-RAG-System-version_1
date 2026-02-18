"""Privacy Policy page route."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Legal"])


@router.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy():
    return """
    <html>
    <head><title>Privacy Policy</title></head>
    <body>
        <h1>Privacy Policy</h1>
        <p>Your privacy is important to us. This policy explains how we collect, use, and protect your data.</p>
    </body>
    </html>
    """
