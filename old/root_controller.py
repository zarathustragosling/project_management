from flask import Blueprint, redirect, url_for

# Создаем Blueprint для корневых маршрутов
root_bp = Blueprint('root', __name__)

@root_bp.route('/')
def home():
    """Перенаправление на домашнюю страницу пользователя"""
    return redirect(url_for('user_blueprint.home'))