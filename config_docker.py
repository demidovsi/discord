import os

URL = os.environ.get("API_URL", "http://159.223.0.234:5000/")
schema_name = os.environ.get("SCHEMA_NAME", "urban")
app_lang = os.environ.get("APP_LANG", "ru")
kirill = os.environ.get("ENCODED_PASSWORD", "")
discord_token = os.environ.get("DISCORD_TOKEN", "")
