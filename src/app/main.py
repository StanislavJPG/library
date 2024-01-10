from pathlib import Path

from fastapi import FastAPI, Depends

from src.auth.base_config import fastapi_users, auth_backend, current_user, current_active_user
from src.auth.schemas import UserRead, UserCreate, UserUpdate
from src.database import User
from src.library.service import test
from src.profile.service import test_profile
from src.weather.router import router as router_weather
from src.base.router import router as router_base
from src.library.router import router as router_library
from src.profile.router import router as router_profile
from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title='Helper24/7'
)

app.include_router(router_weather)
app.include_router(router_base)
app.include_router(router_library)
app.include_router(router_profile)
app.include_router(test)
app.include_router(test_profile)


app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "static"),
    name="static",
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=True),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=True),
    prefix="/users",
    tags=["users"],
)

