from typing import Optional, Union

import httpx
from bs4 import BeautifulSoup as B_soup
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select, update

from src.auth.base_config import current_optional_user
from src.database import async_session_maker, RedisCash
from src.library.models import Book, Library
from fastapi import status

from src.library.shemas import RatingService

test = APIRouter(
    prefix='/test'
)


class BookSearchService:
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    SEARCH_PATTERN = 'https://www.google.com/search?q='

    def __init__(self, book: str):
        self.book = book

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
            async with async_session_maker() as session:
                query_url_book = await session.scalar(select(Book.url_orig).where(
                    Book.title.like(f'%{self.book.split(" ")[0][1:]}%'))
                )

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

    async def book_url_getter_to_read(self, num: int):
        info_book = await self.get_full_info()

        book = info_book['urls'][abs(num) % len(info_book['urls'])]
        # it's important if user trying to read more books than exists atm

        return {'info_about_book': info_book, 'book': book}


class BookConnection:
    def __init__(self, book: Optional[str] = None, rating_schema: Optional[RatingService] = None,
                 num: Optional[int] = None,
                 user=Depends(current_optional_user)):
        self.book = book
        self.num = num
        self.rating_schema = rating_schema
        self.user = user

    async def save_book_db(self) -> None:
        async with async_session_maker() as session:
            redis = RedisCash(f'user_profile.{self.user.id}')

            url = f'http://127.0.0.1:8000/read/{self.book.lower()}?num={self.num}'
            book_orig_url = await session.scalar(select(Book.url_orig).where(Book.url == url))

            # Creating book in tables (Book, Library) if book is not exists in database
            if book_orig_url is None:
                query_book_search = BookSearchService(self.book)
                info_book = await query_book_search.get_full_info()

                url_orig = info_book['urls'][abs(self.num) % len(info_book['urls'])]
                stmt_save_book = insert(Book).values(
                    title=f'№{self.num}. «{info_book["title"]}»',
                    image=info_book['image'],
                    description=info_book['description'],
                    url_orig=url_orig,
                    url=url,
                )
                await session.execute(stmt_save_book)
                book_id = await session.scalar(select(Book.id).where(Book.url == url))

                stmt = insert(Library).values(
                    user_id=self.user.id,
                    book_id=book_id,
                    rating=None,
                    is_saved_to_profile=True
                )
            # in other case it checks is the book is saved to profile
            else:
                book_id = await session.scalar(select(Book.id).where(Book.url == url))
                is_book_saved_to_profile = await session.scalar(select(Library.is_saved_to_profile).where(
                    (Library.user_id == str(self.user.id)) & (Library.book_id == book_id)
                ))
                # creating book by user in Library if it's not
                if is_book_saved_to_profile is None:
                    stmt = insert(Library).values(
                        user_id=self.user.id,
                        book_id=book_id,
                        rating=None,
                        is_saved_to_profile=True
                    )
                # in other case it checks is the argument `is_saved_to_profile` is True of False
                # pulls book to profile if it's False
                else:
                    if is_book_saved_to_profile is False:
                        stmt = update(Library).values(is_saved_to_profile=True).where(
                            (Library.user_id == str(self.user.id)) & (Library.book_id == book_id)
                        )
                    # raising HTTPException if it's True (CONFLICT 409)
                    else:
                        raise HTTPException(status_code=409, detail=status.HTTP_409_CONFLICT)

            await redis.delete()
            await session.execute(stmt)
            await session.commit()

    async def save_rating_db(self) -> None:
        async with async_session_maker() as session:
            redis = RedisCash(f'user_profile.{self.user.id}')
            query_book_search = BookSearchService(self.book)

            book = await self.get_book_id()
            has_book = await session.scalar(select(Library.book_id).where(
                (Library.book_id == book['book_id']) & (Library.user_id == str(self.user.id))
            ))  # taking book id by current user (if it exists)

            if has_book is not None:
                stmt = update(Library).values(rating=self.rating_schema.user_rating).where(
                    (Library.book_id == book['book_id']) & (Library.user_id == str(self.user.id))
                )  # if book exists it updates rating to new value
            else:
                if book['book_id'] is None:
                    """
                    If book does not exist in book table and in library table -
                     - It's creating a new book in book table and library table + rating
                    """

                    info_book_func = await query_book_search.book_url_getter_to_read(
                        self.rating_schema.num
                    )
                    info_book = info_book_func['info_about_book']

                    stmt_save = insert(Book).values(
                        title=f'№{self.rating_schema.num}. «{info_book["title"]}»',
                        image=info_book['image'],
                        description=info_book['description'],
                        url_orig=info_book_func['book'],
                        url=book['url'],
                    )
                    await session.execute(stmt_save)
                    await session.commit()

                book_new = await self.get_book_id()

                stmt = insert(Library).values(
                    user_id=self.user.id,
                    book_id=book_new['book_id'],
                    rating=self.rating_schema.user_rating,
                    is_saved_to_profile=False
                )  # book WILL not save in profile if user set rating but DO not save a book

            # when user making any operations with book in profile it updates hash by deleting it
            # (and then making again)
            await redis.delete()
            await session.execute(stmt)
            await session.commit()

    async def url_reader_by_user(self) -> str:
        """
        This endpoint made for keep "DRY"
        It's created for getting book's ORIGINAL url directly from database if it exists
        But it will search books at first if it's not
        """
        async with async_session_maker() as session:
            redis = RedisCash(f'{self.book.lower()}.{self.num}')
            query_book_search = BookSearchService(self.book)

            url_from_current_cite = f'http://127.0.0.1:8000/read/{self.book.lower()}?num={self.num}'
            query_book = await session.scalar(select(Book.url_orig).where(
                Book.url == url_from_current_cite))

            if query_book is None:
                book_func = await query_book_search.book_url_getter_to_read(self.num)
                book_url = book_func['book']
            else:
                book_url = query_book

            book = await redis.executor(data=book_url, ex=120)

        return book

    async def get_book_id(self) -> dict:
        """
        Taking specific book id from database
        """
        async with async_session_maker() as session:
            url = f'http://127.0.0.1:8000/read/{self.rating_schema.title.lower()}?num={self.rating_schema.num}'

            book_id = await session.scalar(select(Book.id).where(
                (Book.url_orig == self.rating_schema.current_book_url) & (Book.url == url)
            ))
        return {'book_id': book_id, 'url': url}
