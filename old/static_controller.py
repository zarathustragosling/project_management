from flask import Blueprint, send_from_directory, make_response
import os

# Создаем Blueprint для статических ресурсов
static_bp = Blueprint('static_resources', __name__)

@static_bp.route('/favicon.ico')
def favicon():
    from flask import current_app
    response = make_response(send_from_directory(
        os.path.join(current_app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon'
    ))
    response.headers['Cache-Control'] = 'public, max-age=604800'  # 7 дней
    return response