"""Terms and Conditions page route."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Legal"])


@router.get("/terms-and-conditions", response_class=HTMLResponse)
async def terms_and_conditions():
    return """
    <html>
    <head><title>Terms and Conditions</title></head>
    <body>
        <h1>Terms and Conditions</h1>
        <p>By using this service, you agree to the following terms and conditions.</p>
    </body>
    </html>
    """
