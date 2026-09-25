from .auth import router as auth_router
from .chat import router as chat_router
from .products import router as products_router
from .saved import router as saved_router

__all__ = [
    "auth_router",
    "chat_router",
    "products_router",
    "saved_router",
]
