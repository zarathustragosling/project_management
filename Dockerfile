FROM python:3.9-slim

# Установка системных зависимостей, включая клиент PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libffi-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && echo 'export PATH="/usr/lib/postgresql/*/bin:$PATH"' >> /etc/bash.bashrc

WORKDIR /app
ENV PYTHONPATH=/app

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