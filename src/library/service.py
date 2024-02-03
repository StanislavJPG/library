import httpx
from bs4 import BeautifulSoup as B_soup
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select, update
from typing import Type

from src.auth.base_config import current_optional_user, current_user
from src.auth.schemas import UserRead
from src.config import DEFAULT_IMAGE
from src.database import async_session_maker
from src.library.models import Book, Library  # , BookRating
from fastapi import status

test = APIRouter(
    prefix='/test'
)


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}


search_pattern = 'https://www.google.com/search?q='


async def specific_search(book: str):
    async with httpx.AsyncClient() as client:
        url_wiki = search_pattern + f'книга {book} site:uk.wikipedia.org'
        response_wiki = await client.get(url_wiki, headers=headers)
        bs_wiki = B_soup(response_wiki.text, 'lxml')
        data_wiki = bs_wiki.find_all('div', class_='MjjYud')

        for i, wiki_el in enumerate(data_wiki):
            if i == 0:
                full_info = wiki_el.find('a').get('href')
                page = await client.get(full_info, headers=headers)

    soup = B_soup(page.text, 'html.parser')

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
            bs = B_soup(response_text.text, 'lxml')
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


async def get_page(url) -> B_soup:
    async with httpx.AsyncClient() as client:
        page = await client.get(url)
        soup = B_soup(page.content, 'html.parser')
        return soup


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


async def save_book_db(book: str, num: int, user=Depends(current_user)):
    async with async_session_maker() as session:
        url = f'http://127.0.0.1:8000/read/{book.lower()}?num={num}'
        stmt_is_book_exists = await session.scalars(select(Book.id).where(Book.url == url))
        is_book_exists_in_db = stmt_is_book_exists.first()

        if is_book_exists_in_db is None:
            info_book = await get_full_info(book.lower())
            url_orig = info_book[4][abs(num) % len(info_book[4])]

            stmt_save = insert(Book).values(
                title=f'№{num}. «{info_book[1]}»',
                image=info_book[0],
                description=info_book[2],
                url_orig=url_orig,
                url=url,
            )
            await session.execute(stmt_save)

            stmt_is_book_exists = await session.scalars(select(Book.id).where(Book.url == url))
            book_id = stmt_is_book_exists.first()

            stmt = insert(Library).values(
                user_id=user.id,
                book_id=book_id,
                rating=None,
                is_saved_to_profile=True
            )

        else:
            is_book_exists_by_user = await session.scalars(select(Library.is_saved_to_profile).where(
                (Library.user_id == str(user.id)) & (Library.book_id == is_book_exists_in_db)
            ))
            is_book_exists_by_user = is_book_exists_by_user.first()

            if is_book_exists_by_user is None:
                stmt = insert(Library).values(
                    user_id=user.id,
                    book_id=is_book_exists_in_db,
                    rating=None,
                    is_saved_to_profile=True
                )
            else:
                if is_book_exists_by_user is False:
                    stmt = update(Library).values(is_saved_to_profile=True).where(
                        (Library.user_id == str(user.id)) & (Library.book_id == is_book_exists_in_db)
                    )
                else:
                    raise HTTPException(status_code=409, detail=status.HTTP_409_CONFLICT)

        await session.execute(stmt)
        await session.commit()
        raise HTTPException(status_code=200, detail=status.HTTP_200_OK)


async def book_url_getter_to_read(literature: str, num: int):
    info_book = await get_full_info(literature)

    book = info_book[4][abs(num) % len(info_book[4])]
    # it's important if user trying to read more books than exists atm

    return info_book, book


async def reader_session_by_user(literature: str, num: int):
    url_from_current_cite = f'http://127.0.0.1:8000/read/{literature.lower()}?num={num}'
    # this endpoint useful for keeping "DRY"

    async with async_session_maker() as session:
        stmt = select(Book.url_orig).where(
            Book.url == url_from_current_cite)
        book_session = await session.scalars(stmt)
        book = book_session.first()

        if book is None:
            book_func = await book_url_getter_to_read(literature, num)
            book = book_func[-1]

    return book
