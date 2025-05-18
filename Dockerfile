FROM python:3.9-slim

# Установка системных зависимостей, включая клиент PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов проекта
COPY . .

# Создание директорий для загрузок и отчетов, если их нет
RUN mkdir -p static/uploads static/reports static/avatars

# Установка прав на директории
RUN chmod -R 755 static

# Копирование скриптов запуска
COPY entrypoint.sh /app/entrypoint.sh
COPY wait-for-db.sh /app/wait-for-db.sh
RUN chmod +x /app/entrypoint.sh /app/wait-for-db.sh

# Запуск приложения через скрипт запуска
CMD ["/bin/bash", "/app/entrypoint.sh"]