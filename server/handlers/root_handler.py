from flask import Blueprint, redirect, url_for

# Создаем Blueprint для корневых маршрутов
root_bp = Blueprint('root', __name__)

class RootView:
    """Класс представления для корневых маршрутов"""
    
    @staticmethod
    def redirect_to_home():
        """Перенаправление на домашнюю страницу пользователя"""
        return redirect(url_for('user_blueprint.home'))

class RootController:
    """Класс контроллера для корневых маршрутов"""
    
    @staticmethod
    def home():
        """Перенаправление на домашнюю страницу пользователя"""
        return RootView.redirect_to_home()

# Регистрируем маршруты
root_bp.add_url_rule('/', view_func=RootController.home, endpoint='home')