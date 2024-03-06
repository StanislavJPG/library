from typing import Union

import httpx
from bs4 import BeautifulSoup as B_soup
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_optional_user
from src.crud import read_is_book_exists, create_book_and_change_data_for_library, create_book_in_library, \
    read_is_book_saved_to_profile, update_book_back_to_profile, \
    read_book_id_from_library_by_curr_user, update_rating_by_book_and_curr_user, read_book_directly_from_db, \
    read_book_url_orig_by_url, get_url, read_book_id_by_url
from src.database import RedisCash
from fastapi import status

from src.library.shemas import RatingService

test = APIRouter(
    prefix='/test'
)


class BookSearchService:
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    SEARCH_PATTERN = 'https://www.google.com/search?q='

    def __init__(self, book: str, session: AsyncSession = None) -> None:
        self.book = book
        self.session = session

    async def title_search(self) -> Union[str, list]:
        # list always empty (UnboundLocalError)
        async with httpx.AsyncClient() as client:
            url_wiki = self.SEARCH_PATTERN + f'книга {self.book} site:uk.wikipedia.org'
            response_wiki = await client.get(url_wiki, headers=self.HEADERS)
            bs_wiki = B_soup(response_wiki.text, 'lxml')
            data_wiki = bs_wiki.find_all('div', class_='MjjYud')

            for i, wiki_el in enumerate(data_wiki):
                if i == 0:
                    full_info = wiki_el.find('a').get('href')
                    page = await client.get(full_info, headers=self.HEADERS)
        try:
            soup = B_soup(page.text, 'lxml')
            info = soup.find('span', class_='mw-page-title-main').text
        except UnboundLocalError:
            return []
        return info

    async def modified_book_getter(self) -> dict:
        """
        This is general method that implements book search logic
        """
        async with httpx.AsyncClient() as client:
            title_from_wiki = await self.title_search()  # take book title from wiki, to extend search result

            urls = []
            for query in [self.book, title_from_wiki]:
                search_url = self.SEARCH_PATTERN + f'читати {query} book filetype: pdf'
                urls.append(search_url)

            search_url_wiki = self.SEARCH_PATTERN + f'книга {title_from_wiki} site:uk.wikipedia.org'
            urls.append(search_url_wiki)
            scraper_results = []

            for url in urls:
                response = await client.get(url, headers=self.HEADERS)
                bs = B_soup(response.text, 'lxml')
                if 'wikipedia' not in url:
                    data_book = bs.find_all('div', class_='MjjYud', limit=3)
                else:
                    data_book = bs.find_all('div', class_='MjjYud', limit=1)

                scraper_results.extend(data_book)

            book_set = set()

            for book_el in scraper_results[:-1]:
                url_book = book_el.find('a').get('href')
                if '.pdf' in url_book:
                    book_set.add(url_book)

            # load book directly from database if book is in there
            query_url_book = await read_book_directly_from_db(session=self.session, book=self.book)

            if query_url_book is not None:
                book_set.add(query_url_book)

            full_info = scraper_results[-1].find('a').get('href')  # this is full info from wiki

            return {'book_lst': list(book_set), 'full_info': full_info}

    @staticmethod
    async def get_page(url: str) -> B_soup:
        async with httpx.AsyncClient() as client:
            page = await client.get(url)
            soup = B_soup(page.content, 'lxml')
            return soup

    async def image_getter(self) -> str:
        async with httpx.AsyncClient() as client:
            image_search_pattern = 'https://images.search.yahoo.com/search/images?p='
            # yeah:) I'm getting images from yahoo:)

            url = image_search_pattern + f'книга {self.book}'
            query = await client.get(url, headers=self.HEADERS)
            bs = B_soup(query.text, 'lxml')

            image_url = bs.find('img', class_='').get('src')
            return image_url

    async def get_full_info(self) -> dict:
        redis = RedisCash(f'{self.book}.full_data_book')
        is_cache_exists = await redis.check()

        if is_cache_exists:
            data = await redis.get()
        else:
            urls = await self.modified_book_getter()
            page = await self.get_page(urls['full_info'])

            image = await self.image_getter()
            title = page.find('span', class_='mw-page-title-main').text
            description = page.find('p')

            data = await redis.executor(data={'image': image, 'title': title,
                                              'description': description.text, 'urls': urls['book_lst']},
                                        ex=180)
        return data

    async def book_url_getter_to_read(self, num: int) -> dict:
        info_book = await self.get_full_info()

        book = info_book['urls'][abs(num) % len(info_book['urls'])]
        # it's important if user trying to read more books than exists atm

        return {'info_about_book': info_book, 'book': book}


async def save_book_database(book: str, num: int, session: AsyncSession,
                             rating: int = None, user=Depends(current_optional_user)) -> None:
    redis = RedisCash(f'user_profile.{user.id}')
    book_id = await read_is_book_exists(book, num, session)

    data = {
        'user_id': str(user.id),
        'book_id': book_id,
        'rating': rating,
        'is_saved_to_profile': True
    }
    # Creating book in tables (Book, Library) if book is not exists in database
    if book_id is None:
        info_book = await BookSearchService(book).get_full_info()
        data = await create_book_and_change_data_for_library(book, num, data, info_book, session)

        await create_book_in_library(session, **data)
    else:
        # in other case it checks is the book is saved to profile
        is_book_saved_to_profile = await read_is_book_saved_to_profile(session, user, book_id)

        # creating book by user in Library if it's not
        if is_book_saved_to_profile is None:
            await create_book_in_library(session, **data)
        # in other case it checks is the argument `is_saved_to_profile` is True of False
        # pulls book to profile if it's False
        else:
            if is_book_saved_to_profile is False:
                await update_book_back_to_profile(session, user, book_id)
            # raising HTTPException if it's True (CONFLICT 409)
            else:
                raise HTTPException(status_code=409, detail=status.HTTP_409_CONFLICT)
    # clearing all the cache after all the operations with book
    await redis.delete()


async def save_rating_db(rating_schema: RatingService, session: AsyncSession, user=Depends(current_optional_user)
                         ) -> None:
    redis = RedisCash(f'user_profile.{user.id}')
    # book_id returning book's id and url from table Book
    book = await get_book_id(session, rating_schema)
    # taking book id from table Library by current user (if it exists)
    book_id = await read_book_id_from_library_by_curr_user(session=session, book=book, user=user)

    # updating if book_id exists
    if book_id is not None:
        # if book exists it updates rating to new value
        await update_rating_by_book_and_curr_user(session, book, rating_schema.user_rating, user)
    else:
        if book['book_id'] is None:
            """
            If book does not exist in book table and in library table -
             - It's creating a new book in book table and library table + rating
            """
            await save_book_database(book=rating_schema.title, rating=rating_schema.user_rating,
                                     num=rating_schema.num, user=user, session=session)

        book = await get_book_id(session, rating_schema)

        data = {'user_id': user.id,
                'book_id': book['book_id'],
                'rating': rating_schema.user_rating,
                'is_saved_to_profile': False}
        # book will NOT be saved in profile if user set any rating but DOES NOT save a book
        await create_book_in_library(session, **data)

    # when user making any operations with book in profile it updates hash by deleting it
    # (and then after updating a page it's making again)
    await redis.delete()


async def url_reader_by_user(session: AsyncSession, book, num) -> str:
    """
    This endpoint made for keep "DRY"
    It's created for getting book's ORIGINAL url directly from database if it exists
    But it will search books at first if it's not
    """
    redis = RedisCash(f'{book.lower()}.{num}')
    query_book_search = BookSearchService(book)

    query_book = await read_book_url_orig_by_url(session=session, book=book, num=num)

    if query_book is None:
        book_func = await query_book_search.book_url_getter_to_read(num)
        book_url = book_func['book']
    else:
        book_url = query_book

    book = await redis.executor(data=book_url, ex=120)

    return book


async def get_book_id(session: AsyncSession, rating_schema: RatingService) -> dict:
    """
    Taking specific book id from database
    """
    url = await get_url(rating_schema.title, rating_schema.num)
    book_id = await read_book_id_by_url(session, rating_schema.title,
                                        rating_schema.num, url_orig=rating_schema.current_book_url)
    return {'book_id': book_id, 'url': url}
