from flask import Blueprint, url_for
from markupsafe import Markup, escape
from server.database import User
import re

# Создаем Blueprint для утилит
utils_bp = Blueprint('utils', __name__)

# Вспомогательная функция для проверки допустимых расширений файлов
def allowed_file(filename):
    from flask import current_app
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Фильтр для подсветки упоминаний в шаблонах
@utils_bp.app_template_filter('highlight_mentions')
def highlight_mentions(text):
    def replace(match):
        user_id = match.group(1)
        username = match.group(2)
        return f'<a href="{url_for("user_blueprint.user_profile", user_id=user_id)}" class="mention text-blue-400 hover:underline">@{escape(username)}</a>'

    pattern = r'<@(\d+):([\wа-яА-ЯёЁ\s.-]+)>'
    return Markup(re.sub(pattern, replace, text))

# Функция для обработки упоминаний в тексте
def process_mentions(content):
    """Заменяет @username на ссылку на профиль"""
    pattern = r'@([\w\.-]+)'  # допускает email или username

    def repl(match):
        username = match.group(1)
        user = User.query.filter_by(username=username).first()
        if user:
            return f'<a href="{url_for("user_blueprint.user_profile", user_id=user.id)}" class="mention text-blue-400 hover:underline">@{escape(username)}</a>'
        return escape(match.group(0))  # если не найден

    return Markup(re.sub(pattern, repl, content))

# Декоратор для проверки прав тимлида
def teamlead_required(f):
    from functools import wraps
    from flask import abort
    from flask_login import current_user
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teamlead():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function