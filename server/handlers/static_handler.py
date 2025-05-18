from flask import Blueprint, send_from_directory, make_response
import os

# Создаем Blueprint для статических ресурсов
static_bp = Blueprint('static_resources', __name__)

class StaticView:
    """Класс представления для статических ресурсов"""
    
    @staticmethod
    def render_favicon(favicon_file):
        """Рендеринг favicon.ico"""
        response = make_response(favicon_file)
        response.headers['Cache-Control'] = 'public, max-age=604800'  # 7 дней
        return response

class StaticController:
    """Класс контроллера для статических ресурсов"""
    
    @staticmethod
    def favicon():
        """Отдача favicon.ico"""
        from flask import current_app
        favicon_file = send_from_directory(
            os.path.join(current_app.root_path, 'static'), 
            'favicon.ico', 
            mimetype='image/vnd.microsoft.icon'
        )
        return StaticView.render_favicon(favicon_file)

# Регистрируем маршруты
static_bp.add_url_rule('/favicon.ico', view_func=StaticController.favicon, endpoint='favicon')