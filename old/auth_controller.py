from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user
from database import User, db
from werkzeug.security import generate_password_hash, check_password_hash
from views.auth_view import LoginView, LogoutView, RegisterView

# Создаем Blueprint для аутентификации
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Инициализация менеджера аутентификации
login_manager = LoginManager()

def init_login_manager(app):
    """Инициализация менеджера аутентификации для приложения"""
    login_manager.init_app(app)
    login_manager.login_view = 'user_blueprint.login'  # Перенаправление на страницу входа
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return login_manager

# Функции контроллера для аутентификации
def login_page():
    """Страница входа в систему (GET)"""
    if current_user.is_authenticated:
        return redirect(url_for('user_blueprint.home'))
    return LoginView.render_login_page()

def login_user_func():
    """Вход в систему (POST)"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash("Пожалуйста, заполните все поля", "danger")
        return redirect(url_for('auth_blueprint.login'))
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return LoginView.redirect_after_login()
    else:
        flash("Неверный email или пароль", "danger")
        return redirect(url_for('auth_blueprint.login'))

def logout_user_func():
    """Выход из системы"""
    logout_user()
    return LogoutView.redirect_after_logout()

def register_page():
    """Страница регистрации (GET)"""
    if current_user.is_authenticated:
        return redirect(url_for('user_blueprint.home'))
    return RegisterView.render_register_page()

def register_user():
    """Регистрация пользователя (POST)"""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')
    
    if not username or not email or not password:
        flash("Пожалуйста, заполните все обязательные поля", "danger")
        return redirect(url_for('auth_blueprint.register'))
    
    if password != password_confirm:
        flash("Пароли не совпадают", "danger")
        return redirect(url_for('auth_blueprint.register'))
    
    if User.query.filter_by(email=email).first():
        flash("Пользователь с таким email уже существует", "danger")
        return redirect(url_for('auth_blueprint.register'))
    
    if User.query.filter_by(username=username).first():
        flash("Пользователь с таким именем уже существует", "danger")
        return redirect(url_for('auth_blueprint.register'))
    
    user = User(username=username, email=email)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return RegisterView.redirect_after_register()

# Регистрируем маршруты
auth_bp.add_url_rule('/login', view_func=login_page, endpoint='login', methods=['GET'])
auth_bp.add_url_rule('/login', view_func=login_user_func, endpoint='login_post', methods=['POST'])
auth_bp.add_url_rule('/logout', view_func=logout_user_func, endpoint='logout')
auth_bp.add_url_rule('/register', view_func=register_page, endpoint='register', methods=['GET'])
auth_bp.add_url_rule('/register', view_func=register_user, endpoint='register_post', methods=['POST'])