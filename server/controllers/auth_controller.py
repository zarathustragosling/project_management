from flask import Blueprint, current_app
from flask_login import LoginManager
from database import User

# Создаем Blueprint для аутентификации
auth_bp = Blueprint('auth', __name__)

# Инициализация менеджера аутентификации
login_manager = LoginManager()

def init_login_manager(app):
    """Инициализация менеджера аутентификации для приложения"""
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'  # Перенаправление на страницу входа
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return login_manager