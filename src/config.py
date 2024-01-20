from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

DEFAULT_IMAGE = os.environ.get('DEFAULT_IMAGE')

URL_WEATHER_API = os.environ.get('URL_WEATHER_API')
APPID = os.environ.get('APPID')

MAIL_NAME = os.environ.get('MAIL_NAME')
MAIL_PASS = os.environ.get('MAIL_PASS')
