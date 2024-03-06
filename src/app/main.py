from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from src.auth.base_config import fastapi_users, auth_backend, current_user, current_optional_user
from src.auth.models import User
from src.auth.schemas import UserRead, UserCreate, UserUpdate
from src.crud import update_users_pic
from src.database import async_session_maker, get_async_session
from src.library.service import test
from PIL import Image
from sqlalchemy import update

from src.pages.router import router as router_pages, templates
from src.library.router import router as router_lib
from src.profile.router import router as router_profile

from src.admin.router import router as router_admin
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title='Library'
)


origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


app.include_router(router_admin)
app.include_router(router_pages)    # <--
app.include_router(router_lib)
app.include_router(router_profile)

app.include_router(test)


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
async def handling_error_page(request: Request, page: str, user=Depends(current_optional_user)):
    try:
        content = templates.TemplateResponse(f'{page}.html', {'request': request, 'user': user})
        return content
    except Exception:
        raise HTTPException(status_code=404, detail='Page not found')


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException, user=Depends(current_optional_user)):
    if not user:
        return templates.TemplateResponse("error.html", {"request": request, "error": exc.status_code, 'user': user},
                                          status_code=exc.status_code)
    else:
        return templates.TemplateResponse("error.html", {"request": request, "error": exc.status_code, 'user': user},
                                          status_code=exc.status_code)


@app.post('/image')
async def create_upload_file(user=Depends(current_user), session: AsyncSession = Depends(get_async_session),
                             file: UploadFile = File(...)):
    """
    Profile image upload logic
    """
    filepath = str(Path(__file__).parent.parent.absolute() / "static" / "images")
    filename = file.filename
    file_format = filename.split('.')[1].lower()

    if file_format not in ['jpg', 'jpeg', 'png', 'tiff']:
        return {'status': 'error', 'details': 'File format is not allowed'}

    token_name = str(user.id) + '_profile_img' + '.' + 'png'
    generated_name = filepath + '\\' + token_name
    file_content = await file.read()

    file_path = Path(generated_name)

    if file_path.exists():
        file_path.unlink()

    with open(generated_name, 'wb') as file:
        file.write(file_content)

    img = Image.open(generated_name)
    img = img.resize(size=(300, 250))
    img.save(generated_name)
    file.close()

    await update_users_pic(session=session, user=user, token=token_name)

    return {'status': 200}
