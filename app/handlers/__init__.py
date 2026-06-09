from aiogram import Router
from app.handlers.start import router as start_router
from app.handlers.messages import router as messages_router
from app.handlers.actions import router as actions_router
from app.handlers.support import router as support_router
from app.handlers.admin import router as admin_router


def get_main_router() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(actions_router)
    router.include_router(support_router)
    router.include_router(admin_router)
    router.include_router(messages_router)
    return router
