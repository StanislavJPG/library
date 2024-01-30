from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from starlette.responses import HTMLResponse

from src.auth.base_config import fastapi_users, auth_backend
from src.auth.schemas import UserRead, UserCreate, UserUpdate
from src.library.service import test
from src.profile.service import test_profile

# from src.weather.router import router as router_weather
from src.base.router import router as router_base, templates
from src.library.router import router as router_library
from src.profile.router import router as router_profile
from src.auth.router import router as router_auth

from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title='Library'
)

# app.include_router(router_weather)
app.include_router(router_base)
app.include_router(router_library)
app.include_router(router_profile)
app.include_router(test)
app.include_router(test_profile)
app.include_router(router_auth)


app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "static"),
    name="static",
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=False),
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


@app.get('/{page}', response_class=HTMLResponse)
async def handling_error_page(request: Request, page: str):
    try:
        content = templates.TemplateResponse(f'{page}.html', {'request': request})
        return content
    except Exception:
        raise HTTPException(status_code=401, detail='Page not found')


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("error.html", {"request": request, "error": exc.status_code},
                                      status_code=exc.status_code)
