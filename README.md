# Library 24/7 :blue_book: :orange_book: :green_book:

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11-orange)
![Gitea Forks](https://img.shields.io/github/forks/StanislavJPG/library)

### **Library pet project + Books scraper.** 
**Using:**

 :small_orange_diamond: **FastAPI**

 :small_orange_diamond: **Redis**

 :small_orange_diamond: **SQLAlchemy (PostgreSQL)**

 :small_orange_diamond: **Fastapi-Users (Auth)**

 :small_orange_diamond: **Asyncpg**

 :small_orange_diamond: **BeautifulSoup**

 :small_orange_diamond: **Pytest**

 :small_orange_diamond: **Docker**

----

## About this project

The main goal of this project is to provide easy book searching and reading tailored to your preferences.
Any user can search for any books and then save it to their profile for the further management for any time.
Additionally, there is a flexible rating system that automatically generate a top-10 list of the best-rated books on the homepage.

---

### Installation

**From GitHub:**

```commandline
pip install https://github.com/StanislavJPG/library.git
```

**Then install the project dependencies with**
```commandline
pip install -r requirements.txt
```

### Usage
**You can create your own .env file to optimize the project according to your preferences.**
**config.py:**

```python
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

TEST_DB_HOST = os.environ.get('TEST_DB_HOST')
TEST_DB_PORT = os.environ.get('TEST_DB_PORT')
TEST_DB_NAME = os.environ.get('TEST_DB_NAME')
TEST_DB_USER = os.environ.get('TEST_DB_USER')
TEST_DB_PASS = os.environ.get('TEST_DB_PASS')

MAIL_NAME = os.environ.get('MAIL_NAME')
MAIL_PASS = os.environ.get('MAIL_PASS')

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')

SECRET = os.environ.get('SECRET')

```

**Now you can run the project using this command**

```commandline
uvicorn main:app --reload
```
