from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from admin.routes import router as admin_router
from config.settings import settings
from database.session import AsyncSessionLocal
from services.prompt_service import prompt_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Инициализирует промпты по умолчанию при старте админки."""
    async with AsyncSessionLocal() as session:
        await prompt_service.ensure_defaults(session=session)
    yield


def create_admin_app() -> FastAPI:
    """Создаёт FastAPI-приложение админки."""
    app = FastAPI(title='AI Interviewer Admin', lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.admin_secret_key.get_secret_value(),
        session_cookie='ai_interviewer_admin',
        https_only=False,
    )

    static_dir = Path(__file__).resolve().parent / 'static'
    app.mount('/static', StaticFiles(directory=str(static_dir)), name='static')
    app.include_router(admin_router, prefix='/admin')
    return app


app = create_admin_app()


async def start_admin_server() -> None:
    """Запускает uvicorn-сервер админки."""
    config = uvicorn.Config(
        app=app,
        host=settings.admin_host,
        port=settings.admin_port,
        log_level='info',
    )
    server = uvicorn.Server(config)
    await server.serve()
