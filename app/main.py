from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(chat_router)
