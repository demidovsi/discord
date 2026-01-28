FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY common.py common_bot.py main_discord_server.py ./

# Создаём config.py который читает из переменных окружения
COPY <<EOF config.py
import os

URL = os.environ.get('API_URL', "http://159.223.0.234:5000/")
schema_name = os.environ.get('SCHEMA_NAME', 'urban')
app_lang = os.environ.get('APP_LANG', 'ru')
kirill = os.environ.get('KIRILL', "")
discord_token = os.environ.get('DISCORD_TOKEN', "")
EOF

# Порт для health check
ENV PORT=8080
EXPOSE 8080

CMD ["python", "main_discord_server.py"]
