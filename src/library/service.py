import httpx
from bs4 import BeautifulSoup as BS
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select, update
from typing import Type

from src.auth.base_config import current_optional_user
from src.config import DEFAULT_IMAGE
from src.database import async_session_maker
from src.library.models import Book, BookRating
from fastapi import status

test = APIRouter(
    prefix='/test'
)


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}


search_pattern = 'https://www.google.com/search?q='


@test.get('/test/header')
async def specific_search(book: str):
    async with httpx.AsyncClient() as client:
        url_wiki = search_pattern + f'книга {book} site:uk.wikipedia.org'
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


async def modified_book_getter(book: str):
    async with httpx.AsyncClient() as client:

        info_from_wiki = await specific_search(book)   # take full info about book from wiki, to extend search result

        url_first_query = search_pattern + f'читати {book} book filetype:pdf book'
        url_second_query = search_pattern + f'читати {info_from_wiki[0]} book filetype:pdf book'
        url_wiki_query = search_pattern + f'книга {info_from_wiki[0]} site:uk.wikipedia.org'

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
                if j in range(2):
                    url_book2 = book_el2.find('a').get('href')
                    if '.pdf' in url_book2:
                        lst_book.add(url_book2)

            for m, book_el1 in enumerate(scraper_result[0]):
                if m in range(2):
                    url_book1 = book_el1.find('a').get('href')
                    if '.pdf' in url_book1:
                        lst_book.add(url_book1)
        except AttributeError:
            for w, book_el1 in enumerate(scraper_result[0]):
                if w == 0:
                    url_book_single = book_el1.find('a').get('href')
                    if '.pdf' in url_book_single:
                        lst_book.add(url_book_single)
        for i, wiki_el in enumerate(scraper_result[-1]):
            if i == 0:
                full_info = wiki_el.find('a').get('href')  # this is full info from wiki

        return [sorted(list(lst_book), reverse=True), full_info]


async def get_page(url) -> BS:
    async with httpx.AsyncClient() as client:
        page = await client.get(url)
        soup = BS(page.content, 'html.parser')
        return soup

@test.get('/test/lp/{book}')
async def get_full_info(book: str):
    urls = await modified_book_getter(book)
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
    return image, title, description.text, None, urls[:-1][0]


async def get_book_attr_by_user(user_id: str, book: Type[Book]):
    async with async_session_maker() as session:
        stmt = select(book).where(Book.owner_id == user_id)
        current_user_book = await session.scalars(stmt)
        url_by_user = current_user_book.all()
        return url_by_user


async def save_book_to_database(book: str, book_number: int, user=Depends(current_optional_user)):
    url = f'http://127.0.0.1:8000/read/{book.lower()}?num={book_number}'

    stmt_is_rated_book_in_db = select(Book).where(
        (Book.owner_id == str(user.id)) &
        (Book.saved_to_profile == False) & (Book.url == url))

    async with async_session_maker() as session:
        is_rated_book_in_db = await session.scalars(stmt_is_rated_book_in_db)
        is_rated_book_in_db = is_rated_book_in_db.first()

        if is_rated_book_in_db is None:
            info_book = await get_full_info(book.lower())
            url_orig = info_book[4][abs(book_number) % len(info_book[4])]
            url_by_user = await get_book_attr_by_user(user.id, Book.url_orig)

            if info_book[4][abs(book_number) % len(info_book[4])] not in url_by_user:
                stmt = insert(Book).values(
                    title=f'№{book_number}. {info_book[1]}',
                    image=info_book[0],
                    description=info_book[2],
                    url_orig=url_orig,
                    url=url,
                    owner_id=user.id,
                    saved_to_profile=True
                )
                await session.execute(stmt)
                await session.commit()
                return {'success': 200}
        else:
            stmt = update(Book).values(saved_to_profile=True).where(
                (Book.owner_id == str(user.id)) &
                (Book.saved_to_profile == False) & (Book.url == url))
            await session.execute(stmt)
            await session.commit()
            return {'success': 200}

    raise HTTPException(status_code=409,
                        detail=status.HTTP_409_CONFLICT)


async def book_url_getter_to_read(literature: str, num: int):
    info_book = await get_full_info(literature)

    book = info_book[4][abs(num) % len(info_book[4])]
    # it's important if user trying to read more books than exists atm

    return book


async def reader_session_by_user(literature: str, num: int):
    url_from_current_cite = f'http://127.0.0.1:8000/read/{literature.lower()}?num={num}'

    async with async_session_maker() as session:
        stmt = select(BookRating.url_orig).where(
            BookRating.url == url_from_current_cite)
        book_session = await session.scalars(stmt)
        book = book_session.first()

        if book is None:
            book = await book_url_getter_to_read(literature, num)

    return book
