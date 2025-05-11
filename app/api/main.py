from fastapi import APIRouter

from app.api.routes import home_page, users,admin

api_router = APIRouter()
api_router.include_router(users.router, tags=["User"],prefix="/user")
api_router.include_router(admin.router, tags=["Admin"],prefix="/admin")
api_router.include_router(home_page.router, tags=["Home page"],prefix="/home")

