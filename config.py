from dotenv import load_dotenv
from os import environ
from sqdb import Sqdb
from defs import YandexTranslator

load_dotenv()
token = environ['API_TOKEN']
sql = Sqdb(environ['SQL_HOST'], environ['SQL_PASSWORD'], environ['SQL_PORT'], environ['SQL_DATABASE'],
           environ['SQL_USER'])
ya = YandexTranslator(API_KEY=environ['YA_TRANSLATION_APIKEY'], folder_id=environ['YA_TRANSLATION_FOLDERID'])
