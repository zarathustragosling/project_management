from flask import Blueprint
import os

# Создаем Blueprint для конфигурации
config_bp = Blueprint('config', __name__)

# Функция для настройки конфигурации приложения
def configure_app(app):
    # Настройка базы данных
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../project_management.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'supersecretkey'
    
    # Настройка папок для загрузки файлов
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    app.config['AVATAR_FOLDER'] = os.path.join(app.static_folder, 'avatars')
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpeg', 'png'}
    
    # Создание папок, если они не существуют
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['AVATAR_FOLDER'], exist_ok=True)
    
    return app