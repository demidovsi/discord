FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY common.py common_bot.py main_discord_server.py ./

# Копируем config для Docker (читает из env)
COPY config_docker.py config.py

# Порт для health check
ENV PORT=8080
EXPOSE 8080

CMD ["python", "main_discord_server.py"]
