from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, login_user, logout_user, current_user
from database import db, User, Team, Role, Project, Task, Comment, CommentType, TaskStatus
from werkzeug.utils import secure_filename
import os
from views.user_view import HomeView, ProfileUpdateView, ProfileView, PasswordChangeView, RegisterView, LoginView, LogoutView, DashboardView
from controllers.access_control import team_access_required, team_admin_required

# Создаем Blueprint для маршрутов пользователей
user_bp = Blueprint('user', __name__, url_prefix='/user')

# Функции контроллера для пользователей
def home():
    """Главная страница"""
    if not current_user.is_authenticated:
        return HomeView.render()

    if not current_user.team:
        return redirect(url_for('team_blueprint.select_team'))

    elif not current_user.team.name:
        return redirect(url_for('team_blueprint.edit_team'))    # Настройка уже созданной

    team_id = current_user.team.id
    feed = Comment.query \
        .filter_by(type=CommentType.FEED) \
        .order_by(Comment.created_at.desc()) \
        .limit(10).all()
    recent_tasks = Task.query.filter(Task.project.has(team_id=team_id)).order_by(Task.deadline.asc()).limit(5).all()
    team_members = User.query.filter_by(team_id=team_id).all()

    # Используем метод представления для рендеринга шаблона
    return HomeView.render(
        feed=feed,
        recent_tasks=recent_tasks,
        team_members=team_members
    )

def dashboard():
    """Личный кабинет пользователя"""
    # Получаем задачи, где пользователь является ответственным
    assigned_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.created_at.desc()).all()
    
    # Получаем задачи, где пользователь является постановщиком
    created_tasks = Task.query.filter_by(created_by=current_user.id).order_by(Task.created_at.desc()).all()
    
    # Используем метод представления для рендеринга шаблона
    return DashboardView.render(assigned_tasks=assigned_tasks, created_tasks=created_tasks)

def edit_profile_page():
    """Страница редактирования профиля (GET)"""
    # Используем метод представления для рендеринга шаблона
    return ProfileUpdateView.render_edit_page()

def update_profile():
    """Обновление профиля (POST)"""
    username = request.form.get('username')
    file = request.files.get('avatar')
    role = request.form.get('role')
    description = request.form.get('description')

    if username:
        current_user.username = username
    if role:
        current_user.role = role
    if description:
        current_user.description = description
    if file and allowed_file(file.filename):
        from flask import current_app
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        current_user.avatar = f"/static/uploads/{filename}"

    db.session.commit()
    # Используем метод представления для перенаправления
    return ProfileUpdateView.redirect_after_update()

@login_required
def view_profile(user_id):
    """Просмотр профиля пользователя"""
    user = User.query.get_or_404(user_id)
    
    # Проверяем, что пользователь принадлежит к той же команде, что и текущий пользователь
    if not current_user.is_admin and user.team_id != current_user.team_id:
        flash("У вас нет доступа к профилю этого пользователя", "danger")
        return redirect(url_for('user_blueprint.home'))
        
    # Используем метод представления для рендеринга шаблона
    return ProfileView.render(user=user)

def change_password():
    """Изменение пароля"""
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    if not current_user.check_password(old_password):
        flash("Старый пароль неверный", "danger")
        return redirect(url_for('user_blueprint.dashboard'))

    current_user.set_password(new_password)
    db.session.commit()
    # Используем метод представления для перенаправления
    return PasswordChangeView.redirect_after_change()

def register_page():
    """Страница регистрации (GET)"""
    teams = Team.query.all()
    # Используем метод представления для рендеринга шаблона
    return RegisterView.render_register_page(teams=teams)

def register_user():
    """Регистрация пользователя (POST)"""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    team_id = request.form.get('team_id')

    if not username or not email or not password:
        flash("Все поля обязательны!", "danger")
        return redirect(url_for('user_blueprint.register'))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Пользователь с таким email уже зарегистрирован!", "warning")
        return redirect(url_for('user_blueprint.register'))

    new_user = User(username=username, email=email, team_id=team_id)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Используем метод представления для перенаправления
    return RegisterView.redirect_after_register()

def login_page():
    """Страница входа в систему (GET)"""
    # Используем метод представления для рендеринга шаблона
    return LoginView.render_login_page()

def login_user_func():
    """Вход в систему (POST)"""
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        # Используем метод представления для перенаправления
        return LoginView.redirect_after_login()
    else:
        flash("Ошибка входа! Проверьте данные.", "danger")
        # Используем метод представления для рендеринга шаблона
        return LoginView.render_login_page()

def logout_user_func():
    """Выход из системы"""
    logout_user()
    # Используем метод представления для перенаправления
    return LogoutView.redirect_after_logout()

def allowed_file(filename):
    """Вспомогательная функция для проверки допустимых расширений файлов"""
    from flask import current_app
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Регистрируем маршруты
user_bp.add_url_rule('/', view_func=home, endpoint='home')
user_bp.add_url_rule('/dashboard', view_func=dashboard, endpoint='dashboard')
user_bp.add_url_rule('/edit_profile', view_func=edit_profile_page, endpoint='edit_profile', methods=['GET'])
user_bp.add_url_rule('/edit_profile', view_func=update_profile, endpoint='update_profile', methods=['POST'])
user_bp.add_url_rule('/profile', view_func=edit_profile_page, endpoint='profile', methods=['GET'])  # Оставляем для обратной совместимости
user_bp.add_url_rule('/profile', view_func=update_profile, endpoint='profile_post', methods=['POST'])  # Оставляем для обратной совместимости
user_bp.add_url_rule('/profile/<int:user_id>', view_func=view_profile, endpoint='view_profile')
user_bp.add_url_rule('/change_password', view_func=change_password, endpoint='change_password', methods=['POST'])
user_bp.add_url_rule('/register', view_func=register_page, endpoint='register', methods=['GET'])
user_bp.add_url_rule('/register', view_func=register_user, endpoint='register_post', methods=['POST'])
user_bp.add_url_rule('/login', view_func=login_page, endpoint='login', methods=['GET'])
user_bp.add_url_rule('/login', view_func=login_user_func, endpoint='login_post', methods=['POST'])
user_bp.add_url_rule('/logout', view_func=logout_user_func, endpoint='logout')
user_bp.add_url_rule('/<int:user_id>', view_func=view_profile, endpoint='user_profile')

# Сохраняем классы представлений для обратной совместимости
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.