# Инструкция по деплою проекта управления проектами

## Подготовка сервера Ubuntu 22.04

1. Обновите пакеты системы:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Установите Docker и Docker Compose:
   ```bash
   sudo apt install -y docker.io docker-compose
   ```

3. Настройте автозапуск Docker:
   ```bash
   sudo systemctl enable docker
   sudo systemctl start docker
   ```

4. Добавьте вашего пользователя в группу docker (чтобы не использовать sudo):
   ```bash
   sudo usermod -aG docker $USER
   ```
   После этого выйдите из системы и войдите снова, чтобы изменения вступили в силу.

## Деплой приложения

1. Скопируйте файлы проекта на сервер:
   ```bash
   scp -r project_management user@your_server_ip:/path/to/destination
   ```
   или клонируйте репозиторий, если используете Git.

2. Перейдите в директорию проекта:
   ```bash
   cd /path/to/destination/project_management
   ```

3. Запустите приложение с помощью Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Проверьте, что все контейнеры запущены:
   ```bash
   docker-compose ps
   ```

## Инициализация базы данных

При первом запуске необходимо инициализировать базу данных:

```bash
docker-compose exec web python -c "from server.app import app; from database import db; app.app_context().push(); db.create_all()"
```

## Обновление приложения

Для обновления приложения:

1. Остановите контейнеры:
   ```bash
   docker-compose down
   ```

2. Обновите файлы проекта.

3. Пересоберите и запустите контейнеры:
   ```bash
   docker-compose up -d --build
   ```

## Резервное копирование базы данных

Для создания резервной копии базы данных:

```bash
docker-compose exec db mysqldump -u pmuser -ppmpassword project_management > backup.sql
```

## Мониторинг логов

Для просмотра логов приложения:

```bash
docker-compose logs -f web
```

Для просмотра логов базы данных:

```bash
docker-compose logs -f db
```

Для просмотра логов Nginx:

```bash
docker-compose logs -f nginx
```

## Доступ к приложению

После успешного деплоя приложение будет доступно по адресу: http://your_server_ip

## Настройка HTTPS (рекомендуется)

Для настройки HTTPS рекомендуется использовать Certbot с Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com
```

После этого обновите конфигурацию Nginx в docker-compose.yml, чтобы монтировать сертификаты.