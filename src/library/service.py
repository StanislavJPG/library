import httpx
from bs4 import BeautifulSoup as BS
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select

from src.auth.base_config import current_user
from src.config import DEFAULT_IMAGE
from src.database import async_session_maker
from src.library.models import Book
from fastapi import status

test = APIRouter(
    prefix='/test'
)

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'}


async def specific_search(book: str):
    async with httpx.AsyncClient() as client:
        url_wiki = 'https://www.google.com/search?q=' + f'книга {book} site:uk.wikipedia.org'
        response_wiki = await client.get(url_wiki, headers=headers)
        bs_wiki = BS(response_wiki.text, 'lxml')
        data_wiki = bs_wiki.find_all('div', class_='MjjYud')

        for i, wiki_el in enumerate(data_wiki):
            if i == 0:
                full_info = wiki_el.find('a').get('href')
                page = await client.get(full_info, headers=headers)

        soup = BS(page.text, 'html.parser')

        title = soup.find('span', class_='mw-page-title-main').text
        description = soup.find('p')

        return title, description.text


async def modified_take_book(book: str):
    async with httpx.AsyncClient() as client:

        get_url = await specific_search(book)

        url_first_query = 'https://www.google.com/search?q=' + f'читати {book} filetype:pdf book'
        url_second_query = 'https://www.google.com/search?q=' + f'читати {get_url[0]} book filetype:pdf book'
        url_wiki_query = 'https://www.google.com/search?q=' + f'книга {get_url[0]} site:uk.wikipedia.org'

        urls_queries_lst = [url_first_query, url_second_query, url_wiki_query]
        scraper_result = []

        for url in urls_queries_lst:
            response_text = await client.get(url, headers=headers)
            bs = BS(response_text.text, 'lxml')
            data_book = bs.find_all('div', class_='MjjYud')
            scraper_result.append(data_book)

        lst_book = set()
        full_info = None

        try:
            for j, book_el2 in enumerate(scraper_result[1]):
                if j in [0, 1]:
                    url_book2 = book_el2.find('a').get('href')
                    if '.pdf' in url_book2:
                        lst_book.add(url_book2)
            for m, book_el1 in enumerate(scraper_result[0]):
                if m in [0, 1]:
                    url_book1 = book_el1.find('a').get('href')
                    if '.pdf' in url_book1:
                        lst_book.add(url_book1)
        except AttributeError:
            for m, book_el1 in enumerate(scraper_result[0]):
                if m == 0:
                    url_book_single = book_el1.find('a').get('href')
                    if '.pdf' in url_book_single:
                        lst_book.add(url_book_single)

        for i, wiki_el in enumerate(scraper_result[-1]):
            if i == 0:
                full_info = wiki_el.find('a').get('href')   # this is full info from wiki

        return [sorted(list(lst_book), reverse=True), full_info]


async def get_page(url: modified_take_book) -> BS:
    async with httpx.AsyncClient() as client:
        page = await client.get(url)
        soup = BS(page.content, 'html.parser')
        return soup


async def get_full_info(book: str):
    urls = await modified_take_book(book)
    page = await get_page(urls[1])

    title = page.find('span', class_='mw-page-title-main').text
    description = page.find('p')
    image_raw_url = page.find('img', alt='', class_='mw-file-element')

    try:
        image = 'https:' + str(image_raw_url.get('src'))
    except (AttributeError, IndexError):
        image_default = DEFAULT_IMAGE
        attention = f'Не знайшли нічого? Напишіть нам!'
        return image_default, title, description.text, attention
    return image, title, description.text, None


async def get_urls_info(book: str):
    urls = await modified_take_book(book)

    return urls[:-1][0]


async def get_title_info(book: str):
    urls = await modified_take_book(book)
    page = await get_page(urls[1])

    title = page.find('span', class_='mw-page-title-main').text
    return title


async def get_description_info(book: str):
    urls = await modified_take_book(book)
    page = await get_page(urls[1])

    description = page.find('p')
    return description.text


async def get_image_info(book: str):
    urls = await modified_take_book(book)
    page = await get_page(urls[1])

    attention = f'Не знайшли нічого? Напишіть нам!'
    image_raw_url = page.find('img', alt='', class_='mw-file-element')
    try:
        image = 'https:' + str(image_raw_url.get('src'))
    except (AttributeError, IndexError):
        image_default = DEFAULT_IMAGE
        return image_default, attention
    return image, attention


async def save_book_database(book: str, book_number: int, user=Depends(current_user)):
    title = await get_title_info(book)
    image = await get_image_info(book)
    description = await get_description_info(book)
    urls = await get_urls_info(book)

    url = f'http://127.0.0.1:8000/read/{book}?num={book_number % len(urls)}'

    async with async_session_maker() as session:
        select_book = select(Book).where(Book.owner_id == str(user.id))
        current_user_book = await session.scalars(select_book)
        result = current_user_book.all()

        if url not in [x.as_dict()['url'] for x in result]:
            stmt = insert(Book).values(
                title=f'№{book_number+1}. {title}',
                image=image[0],
                description=description,
                url=url,
                owner_id=user.id
            )
            await session.execute(stmt)
            await session.commit()
            return {'detail': 200}

        raise HTTPException(status_code=409,
                            detail=status.HTTP_409_CONFLICT)
