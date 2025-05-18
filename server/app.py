from flask import Flask, render_template
from database import db
from datetime import datetime


# Инициализация приложения
app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Импорт и применение конфигурации
from utils.config_controller import configure_app
configure_app(app)


db.init_app(app)

# Инициализация middleware для проверки доступа к ресурсам команды
from middleware import init_middleware
init_middleware(app)

# Инициализация менеджера аутентификации
from handlers.auth_handler import init_login_manager
init_login_manager(app)


# Импорт и регистрация Blueprint для хендлеров
# Инициализация Flask-Admin
from handlers import admin_handler
admin_handler.init_admin(app)
from handlers.task_handler import task_bp
app.register_blueprint(task_bp, name='task_blueprint')
from handlers.team_handler import team_bp
app.register_blueprint(team_bp, name='team_blueprint')
from handlers.charts_handler import charts_bp
app.register_blueprint(charts_bp, name='charts_blueprint')
from handlers.project_handler import project_bp
app.register_blueprint(project_bp, name='project_blueprint')
from handlers.report_handler import report_bp
app.register_blueprint(report_bp, name='report_blueprint')
from handlers.user_handler import user_bp
app.register_blueprint(user_bp, name='user_blueprint')
from handlers.comment_handler import comment_bp
app.register_blueprint(comment_bp, name='comment_blueprint')
from utils.utils_controller import utils_bp
app.register_blueprint(utils_bp, name='utils_blueprint')
from handlers.static_handler import static_bp
app.register_blueprint(static_bp, name='static_blueprint')
from handlers.root_handler import root_bp
app.register_blueprint(root_bp, name='root_blueprint')
from handlers.notification_handler import notification_bp
app.register_blueprint(notification_bp, name='notification_blueprint')
from handlers.auth_handler import auth_bp
app.register_blueprint(auth_bp, name='auth_blueprint')


# В файле app.py или __init__.py
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403



@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
