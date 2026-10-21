"""FastAPI Backend Server Launcher."""

import uvicorn
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} Backend on http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.DEBUG
    )
