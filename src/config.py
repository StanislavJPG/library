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
