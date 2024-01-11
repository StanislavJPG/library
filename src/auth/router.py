from fastapi import APIRouter, Request, Query, Depends, HTTPException
from starlette import status
from starlette.responses import RedirectResponse

from src.auth.base_config import current_active_user, current_user, fastapi_users, auth_backend
from src.base.router import templates


router = APIRouter(
    tags=['Auth_page']
)

@router.get('/registration')
async def registration_endpoint(request: Request, user=Depends(current_user)):
    if not user:
        return templates.TemplateResponse(
            'registration.html', {'request': request}
        )
    return {"detail": "Already authorized"}


@router.get('/login')
async def login_endpoint(request: Request, user=Depends(current_user)):
    if not user:
        return templates.TemplateResponse(
            'login.html', {'request': request}
        )
    return {"detail": "Already authorized"}


@router.get('/logout')
async def logout_endpoint(request: Request, user=Depends(current_active_user)):
    return templates.TemplateResponse(
        'logout.html', {'request': request, 'user': user}
    )
