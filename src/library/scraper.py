from abc import ABC, abstractmethod
from typing import Union

import httpx
from bs4 import BeautifulSoup as B_soup
from sqlalchemy.ext.asyncio import AsyncSession
import src.crud as base_crud
from src.database import RedisCache


class AbstractBookService(ABC):
    @abstractmethod
    async def __search_book_title(self) -> Union[str, list]:
        ...

    @abstractmethod
    async def __complex_book_scraper(self) -> dict:
        ...

    @classmethod
    @abstractmethod
    async def __get_page_content(cls, url: str) -> B_soup:
        ...

    @abstractmethod
    async def __search_book_image(self) -> str:
        ...

    @abstractmethod
    async def get_full_book_info(self) -> dict:
        ...

    @abstractmethod
    async def get_read_url(self, num: int) -> dict:
        ...


class BookSearchService(AbstractBookService):
    _HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    _SEARCH_PATTERN = 'https://www.google.com/search?q='

    def __init__(self, book: str, session: AsyncSession = None) -> None:
        self.book = book
        self.session = session

    async def __search_book_title(self) -> Union[str, list]:
        async with httpx.AsyncClient(headers=self._HEADERS) as client:
            url_wiki = self._SEARCH_PATTERN + f'книга {self.book} site:uk.wikipedia.org'
            response_wiki = await client.get(url_wiki)
            bs_wiki = B_soup(response_wiki.text, 'lxml')
            data_wiki = bs_wiki.find_all('div', class_='MjjYud')

            for i, wiki_el in enumerate(data_wiki):
                if i == 0:
                    full_info = wiki_el.find('a').get('href')
                    page = await client.get(full_info)
        try:
            soup = B_soup(page.text, 'lxml')
            info = soup.find('span', class_='mw-page-title-main').text
        except UnboundLocalError:
            return []
        return info

    async def __complex_book_scraper(self) -> dict:
        """
        This is general method that implements book search logic
        """
        async with httpx.AsyncClient(headers=self._HEADERS) as client:
            title_from_wiki = await self.__search_book_title()  # take book title from wiki, to extend search result

            urls = []
            for query in [self.book, title_from_wiki]:
                search_url = self._SEARCH_PATTERN + f'читати {query} book filetype: pdf'
                urls.append(search_url)

            search_url_wiki = self._SEARCH_PATTERN + f'книга {title_from_wiki} site:uk.wikipedia.org'
            urls.append(search_url_wiki)
            scraper_results = []

            for url in urls:
                response = await client.get(url)
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
            query_url_book = await base_crud.read_book_directly_from_db(session=self.session, book=self.book)

            if query_url_book is not None:
                book_set.add(query_url_book)

            full_info = scraper_results[-1].find('a').get('href')  # this is full info from wiki

            return {'book_urls_lst': list(book_set), 'full_info': full_info}

    @classmethod
    async def __get_page_content(cls, url: str) -> B_soup:
        async with httpx.AsyncClient(headers=cls._HEADERS) as client:
            page = await client.get(url)
            soup = B_soup(page.content, 'lxml')
            return soup

    async def __search_book_image(self) -> str:
        async with httpx.AsyncClient(headers=self._HEADERS) as client:
            image_search_pattern = 'https://images.search.yahoo.com/search/images?p='
            # yeah:) I'm getting images from yahoo:)

            url = image_search_pattern + f'книга {self.book}'
            query = await client.get(url)
            bs = B_soup(query.text, 'lxml')

            image_url = bs.find('img', class_='').get('src')
            return image_url

    async def get_full_book_info(self) -> dict:
        redis = RedisCache(f'{self.book}.full_data_book')

        if await redis.exist():
            data = await redis.get()
        else:
            url = await self.__complex_book_scraper()
            page = await self.__get_page_content(url['full_info'])

            image = await self.__search_book_image()
            title = page.find('span', class_='mw-page-title-main').text
            description = page.find('p')

            data = await redis.executor(data={'image': image, 'title': title,
                                              'description': description.text, 'urls': url['book_urls_lst']},
                                        ex=180)
        return data

    async def get_read_url(self, num: int) -> dict:
        info_book = await self.get_full_book_info()

        book = info_book['urls'][abs(num) % len(info_book['urls'])]
        # it's important if user trying to read more books than exists atm

        return {'info_about_book': info_book, 'book': book}
