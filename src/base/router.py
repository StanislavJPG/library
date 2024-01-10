from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends

from src.auth.base_config import current_user

router = APIRouter(
    prefix='/base',
    tags=['Base_page']
)

templates = Jinja2Templates(directory='src/templates')


@router.get('/')
def get_base_page(request: Request,
                           user=Depends(current_user)):
    return templates.TemplateResponse(
        'base.html',
        {'request': request, 'user': user}
    )
