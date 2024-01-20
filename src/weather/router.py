import asyncio
from math import floor
from googletrans import Translator
import httpx
from fastapi import APIRouter, Request, Depends

from src.auth.base_config import current_optional_user
from src.config import URL_WEATHER_API, APPID
from src.base.router import templates

router = APIRouter(
    tags=['Weather_page']
)


async def weather(city):
    async with httpx.AsyncClient() as client:
        url = URL_WEATHER_API
        params = {'q': city, 'APPID': APPID}

        response = await client.get(url, params=params)
        weather_json = response.json()

        if response.status_code == 200:
            description = Translator().translate(weather_json['weather'][0]['description'].title(), dest='uk')
            return {'City': city.title(), 'Weather': weather_json,
                    'Description': description.text, 'Humidity': weather_json['main']['humidity'],
                    'Feels_like': str(floor(weather_json['main']['feels_like'] - 273.15)) + '°C',
                    'Pressure': weather_json['main']['pressure'],
                    'Temperature': str(floor(weather_json['main']['temp'] - 273.15)) + '°C'}
        else:
            return {'Error': response.status_code}


@router.get('/weather')
def get_weather_page(request: Request,
                           user=Depends(current_optional_user)):
    return templates.TemplateResponse(
        'weather.html',
        {'request': request, 'user': user}
    )


@router.get('/weather/{city}')
async def get_weather_operation(request: Request, city: str,
                           user=Depends(current_optional_user)):
    task = asyncio.create_task(weather(city))

    result = await asyncio.gather(task)
    return templates.TemplateResponse(
        'weather.html',
        {'request': request, 'city': result[0],
         'user': user}
    )
