from typing import Union

import httpx
from bs4 import BeautifulSoup as B_soup
from sqlalchemy.ext.asyncio import AsyncSession
import requests
from src.crud import read_book_directly_from_db
from src.database import RedisCache


class BookSearchService:
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    SEARCH_PATTERN = 'https://www.google.com/search?q='

    def __init__(self, book: str, session: AsyncSession = None) -> None:
        self.book = book
        self.session = session

    async def title_search(self) -> Union[str, list]:
        async with httpx.AsyncClient(headers=self.HEADERS) as client:
            url_wiki = self.SEARCH_PATTERN + f'книга {self.book} site:uk.wikipedia.org'
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

    async def modified_book_getter(self) -> dict:
        """
        This is general method that implements book search logic
        """
        async with httpx.AsyncClient(headers=self.HEADERS) as client:
            title_from_wiki = await self.title_search()  # take book title from wiki, to extend search result

            urls = []
            for query in [self.book, title_from_wiki]:
                search_url = self.SEARCH_PATTERN + f'читати {query} book filetype: pdf'
                urls.append(search_url)

            search_url_wiki = self.SEARCH_PATTERN + f'книга {title_from_wiki} site:uk.wikipedia.org'
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
            query_url_book = await read_book_directly_from_db(session=self.session, book=self.book)

            if query_url_book is not None:
                book_set.add(query_url_book)

            full_info = scraper_results[-1].find('a').get('href')  # this is full info from wiki

            return {'book_lst': list(book_set), 'full_info': full_info}

    @classmethod
    async def get_page(cls, url: str) -> B_soup:
        async with httpx.AsyncClient(headers=cls.HEADERS) as client:
            page = await client.get(url)
            soup = B_soup(page.content, 'lxml')
            return soup

    async def image_getter(self) -> str:
        async with httpx.AsyncClient(headers=self.HEADERS) as client:
            image_search_pattern = 'https://images.search.yahoo.com/search/images?p='
            # yeah:) I'm getting images from yahoo:)

            url = image_search_pattern + f'книга {self.book}'
            query = await client.get(url)
            bs = B_soup(query.text, 'lxml')

            image_url = bs.find('img', class_='').get('src')
            return image_url

    async def get_full_info(self) -> dict:
        redis = RedisCache(f'{self.book}.full_data_book')
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
