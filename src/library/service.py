import httpx
from bs4 import BeautifulSoup as B_soup
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select, update

from src.auth.base_config import current_optional_user, current_user
from src.database import async_session_maker
from src.library.models import Book, Library
from fastapi import status

from src.library.shemas import RatingService

test = APIRouter(
    prefix='/test'
)


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}


search_pattern = 'https://www.google.com/search?q='


class BookService:
    @staticmethod
    async def title_search(book: str):
        async with httpx.AsyncClient() as client:
            url_wiki = search_pattern + f'книга {book} site:uk.wikipedia.org'
            response_wiki = await client.get(url_wiki, headers=headers)
            bs_wiki = B_soup(response_wiki.text, 'lxml')
            data_wiki = bs_wiki.find_all('div', class_='MjjYud')

            for i, wiki_el in enumerate(data_wiki):
                if i == 0:
                    full_info = wiki_el.find('a').get('href')
                    page = await client.get(full_info, headers=headers)
        try:
            soup = B_soup(page.text, 'html.parser')
            title = soup.find('span', class_='mw-page-title-main').text
        except UnboundLocalError:
            return []

        return title

    @classmethod
    async def modified_book_getter(cls, book: str):
        """
        This is general method that implements book search logic
        """
        async with httpx.AsyncClient() as client:
            title_from_wiki = await cls.title_search(book)    # take book title from wiki, to extend search result

            urls = []
            for query in [book, title_from_wiki]:
                search_url = search_pattern + f'читати {query} book filetype: pdf'
                urls.append(search_url)

            search_url_wiki = search_pattern + f'книга {title_from_wiki} site:uk.wikipedia.org'
            urls.append(search_url_wiki)
            scraper_results = []

            for url in urls:
                response = await client.get(url, headers=headers)
                bs = B_soup(response.text, 'lxml')
                if 'wikipedia' not in url:
                    data_book = bs.find_all('div', class_='MjjYud', limit=5)
                else:
                    data_book = bs.find_all('div', class_='MjjYud', limit=1)

                scraper_results.extend(data_book)

            book_set = set()

            for book_el in scraper_results[:-1]:
                url_book = book_el.find('a').get('href')
                if '.pdf' in url_book:
                    book_set.add(url_book)

            async with async_session_maker() as session:
                query_url_book = await session.scalar(select(Book.url_orig).where(
                    Book.title.like(f'%{book[1:]}%'))
                )

            if query_url_book is not None:
                book_set.add(query_url_book)

            full_info = scraper_results[-1].find('a').get('href')  # this is full info from wiki

            return [list(book_set), full_info]

    @staticmethod
    async def get_page(url) -> B_soup:
        async with httpx.AsyncClient() as client:
            page = await client.get(url)
            soup = B_soup(page.content, 'html.parser')
            return soup

    @staticmethod
    async def image_getter(title: str):
        async with httpx.AsyncClient() as client:
            image_search_pattern = 'https://images.search.yahoo.com/search/images?p='
            # yeah:) I'm getting images from yahoo:)

            url = image_search_pattern + f'книга {title}'
            query = await client.get(url, headers=headers)
            bs = B_soup(query.text, 'lxml')

            image_url = bs.find('img', class_='').get('src')
            return image_url

    @classmethod
    async def get_full_info(cls, book: str):
        urls = await cls.modified_book_getter(book)
        page = await cls.get_page(urls[1])

        image = await cls.image_getter(book)
        title = page.find('span', class_='mw-page-title-main').text
        description = page.find('p')

        return {'image': image, 'title': title, 'description': description.text, 'urls': urls[:-1][0]}

    @classmethod
    async def book_url_getter_to_read(cls, literature: str, num: int):
        info_book = await cls.get_full_info(literature)

        book = info_book['urls'][abs(num) % len(info_book['urls'])]
        # it's important if user trying to read more books than exists atm

        return {'info_about_book': info_book, 'book': book}


class DatabaseInteract:
    @staticmethod
    async def save_book_db(book: str, num: int, user=Depends(current_user)):
        async with async_session_maker() as session:
            url = f'http://127.0.0.1:8000/read/{book.lower()}?num={num}'
            book_orig_url = await session.scalar(select(Book.url_orig).where(Book.url == url))

            if book_orig_url is None:
                info_book = await BookService.get_full_info(book.lower())
                url_orig = info_book['urls'][abs(num) % len(info_book['urls'])]
                stmt_save_book = insert(Book).values(
                    title=f'№{num}. «{info_book["title"]}»',
                    image=info_book['image'],
                    description=info_book['description'],
                    url_orig=url_orig,
                    url=url,
                )
                await session.execute(stmt_save_book)
                book_id = await session.scalar(select(Book.id).where(Book.url == url))

                stmt = insert(Library).values(
                    user_id=user.id,
                    book_id=book_id,
                    rating=None,
                    is_saved_to_profile=True
                )
            else:
                book_id = await session.scalar(select(Book.id).where(Book.url == url))
                is_book_saved_to_profile = await session.scalar(select(Library.is_saved_to_profile).where(
                    (Library.user_id == str(user.id)) & (Library.book_id == book_id)
                ))
                if is_book_saved_to_profile is None:
                    stmt = insert(Library).values(
                        user_id=user.id,
                        book_id=book_id,
                        rating=None,
                        is_saved_to_profile=True
                    )
                else:
                    if is_book_saved_to_profile is False:
                        stmt = update(Library).values(is_saved_to_profile=True).where(
                            (Library.user_id == str(user.id)) & (Library.book_id == book_id)
                        )
                    else:
                        raise HTTPException(status_code=409, detail=status.HTTP_409_CONFLICT)

            await session.execute(stmt)
            await session.commit()
            raise HTTPException(status_code=200, detail=status.HTTP_200_OK)

    @classmethod
    async def book_id(cls, rating_schema: RatingService):
        """
        Taking specific book id from database
        """
        async with async_session_maker() as session:
            url = f'http://127.0.0.1:8000/read/{rating_schema.title.lower()}?num={rating_schema.num}'

            book_id = await session.scalar(select(Book.id).where(
                (Book.url_orig == rating_schema.current_book_url) & (Book.url == url)
            ))

        return {'book_id': book_id, 'url': url}

    @classmethod
    async def save_rating_db(cls, rating_schema: RatingService, user=Depends(current_optional_user)):
        async with async_session_maker() as session:
            book = await cls.book_id(rating_schema)
            has_book = await session.scalar(select(Library.book_id).where(
                (Library.book_id == book['book_id']) & (Library.user_id == str(user.id))
            ))  # taking book id by current user (if it exists)

            if has_book is not None:
                stmt = update(Library).values(rating=rating_schema.user_rating).where(
                    (Library.book_id == book['book_id']) & (Library.user_id == str(user.id))
                )   # if book exists it updates rating to new value
            else:
                if book['book_id'] is None:
                    """
                    If book does not exist in book table and in library table -
                     - It's creating a new book in book table and library table + rating
                    """
                    info_book_func = await BookService.book_url_getter_to_read(
                        rating_schema.title.lower(), rating_schema.num
                    )
                    info_book = info_book_func['info_about_book']
                    url_orig = info_book_func['book']

                    stmt_save = insert(Book).values(
                        title=f'№{rating_schema.num}. {info_book["title"]}',
                        image=info_book['image'],
                        description=info_book['description'],
                        url_orig=url_orig,
                        url=book['url'],
                    )
                    await session.execute(stmt_save)

                    book = await cls.book_id(rating_schema)

                stmt = insert(Library).values(
                    user_id=user.id,
                    book_id=book['book_id'],
                    rating=rating_schema.user_rating,
                    is_saved_to_profile=False
                )   # book WILL not save in profile if user set rating but DO not save a book

            await session.execute(stmt)
            await session.commit()


async def reader_session_by_user(literature: str, num: int):
    """
    this endpoint made for keeping method "DRY"
    """
    url_from_current_cite = f'http://127.0.0.1:8000/read/{literature.lower()}?num={num}'

    async with async_session_maker() as session:
        book = await session.scalar(select(Book.url_orig).where(
            Book.url == url_from_current_cite))

        if book is None:
            book_func = await BookService.book_url_getter_to_read(literature, num)
            book = book_func['book']

    return book
