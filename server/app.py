from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, abort, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database import db, User, Role, Project, Task, Report, Team, TaskStatus, Comment, CommentType
import os
from werkzeug.utils import secure_filename
from datetime import datetime, date
from markupsafe import Markup, escape
from sqlalchemy import event
from sqlalchemy.engine import Engine
from functools import wraps

# Инициализация приложения
app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Импорт и применение конфигурации
from controllers.config_controller import configure_app
configure_app(app)


db.init_app(app)

# Инициализация менеджера аутентификации
from controllers.auth_controller import init_login_manager
init_login_manager(app)


# Импорт и регистрация Blueprint для контроллеров
from controllers.admin_controller import admin_bp
app.register_blueprint(admin_bp)
from controllers.task_controller import task_bp
app.register_blueprint(task_bp)
from controllers.team_controller import team_bp
app.register_blueprint(team_bp)
from controllers.charts_controller import charts_bp
app.register_blueprint(charts_bp)
from controllers.project_controller import project_bp
app.register_blueprint(project_bp)
from controllers.report_controller import report_bp
app.register_blueprint(report_bp)
from controllers.user_controller import user_bp
app.register_blueprint(user_bp)
from controllers.comment_controller import comment_bp
app.register_blueprint(comment_bp)
from controllers.utils_controller import utils_bp
app.register_blueprint(utils_bp)
from controllers.static_controller import static_bp
app.register_blueprint(static_bp)
from controllers.root_controller import root_bp
app.register_blueprint(root_bp)


# В файле app.py или __init__.py


from datetime import datetime

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
