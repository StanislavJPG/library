from fastapi import APIRouter, Request, Depends

from src.auth.base_config import current_user, current_optional_user
from src.base.router import templates


router = APIRouter(
    tags=['auth_page']
)


@router.get('/registration')
async def registration_endpoint(request: Request, user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'registration.html', {'request': request, 'user': user}
    )


@router.get('/login')
async def login_endpoint(request: Request, user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'login.html', {'request': request, 'user': user}
    )


@router.get('/logout')
async def logout_endpoint(request: Request, user=Depends(current_user)):
    return templates.TemplateResponse(
        'logout.html', {'request': request, 'user': user}
    )
