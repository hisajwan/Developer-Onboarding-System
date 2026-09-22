from fastapi import APIRouter, Depends

from app.api.deps import require_session
from app.api.routes import auth, chat, documents, health, projects

api_router = APIRouter()

# Public: health, and the login routes themselves.
api_router.include_router(health.router)
api_router.include_router(auth.router)

# Everything else requires a valid session. New protected routers go here.
protected = [Depends(require_session)]
api_router.include_router(projects.router, dependencies=protected)
api_router.include_router(chat.router, dependencies=protected)
api_router.include_router(documents.router, dependencies=protected)
