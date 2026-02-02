import os
from dotenv import load_dotenv

load_dotenv()

URL = os.environ.get('API_URL', "http://159.223.0.234:5000/")
_URL = os.environ.get('API_URL', "http://127.0.0.1:5000/")
schema_name = os.environ.get('SCHEMA_NAME', 'urban')
app_lang = os.environ.get('APP_LANG', 'ru')
kirill = os.environ.get('KIRILL', "wqzDi8OVw43DjcOOwoTCncKZwpM=")
discord_token = os.environ.get('DISCORD_TOKEN', "")
