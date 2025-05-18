from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, login_user, logout_user, current_user
from database import db, User, Team, Role, Project, Task, Comment, CommentType, TaskStatus
from werkzeug.utils import secure_filename
import os
from utils.access_control import team_access_required, team_admin_required

# Создаем Blueprint для маршрутов пользователей
user_bp = Blueprint('user', __name__, url_prefix='/user')

class UserView:
    """Класс представления для пользователей"""
    
    @staticmethod
    def render(feed=None, recent_tasks=None, team_members=None):
        """Рендеринг главной страницы"""
        return render_template('home.html', feed=feed, recent_tasks=recent_tasks, team_members=team_members)
    
    @staticmethod
    def render_dashboard(assigned_tasks=None, created_tasks=None):
        """Рендеринг личного кабинета пользователя"""
        return render_template('dashboard.html', assigned_tasks=assigned_tasks, created_tasks=created_tasks)
    
    @staticmethod
    def render_edit_page():
        """Рендеринг страницы редактирования профиля"""
        return render_template('edit_profile.html')
    
    @staticmethod
    def redirect_after_update():
        """Перенаправление после обновления профиля"""
        flash("Профиль обновлен!", "success")
        return redirect(url_for('user_blueprint.dashboard'))
    
    @staticmethod
    def render_profile(user):
        """Рендеринг профиля пользователя"""
        return render_template('profile.html', user=user)
    
    @staticmethod
    def redirect_after_change():
        """Перенаправление после изменения пароля"""
        flash("Пароль успешно изменен", "success")
        return redirect(url_for('user_blueprint.dashboard'))
    
    @staticmethod
    def render_register_page(teams=None):
        """Рендеринг страницы регистрации"""
        return render_template('register.html', teams=teams)
    
    @staticmethod
    def redirect_after_register():
        """Перенаправление после успешной регистрации"""
        flash("Регистрация успешна! Теперь вы можете войти в систему", "success")
        return redirect(url_for('auth_blueprint.login'))
    
    @staticmethod
    def render_login_page():
        """Рендеринг страницы входа в систему"""
        return render_template('login.html')
    
    @staticmethod
    def redirect_after_login():
        """Перенаправление после успешного входа"""
        flash("Вы успешно вошли в систему", "success")
        return redirect(url_for('user_blueprint.home'))
    
    @staticmethod
    def redirect_after_logout():
        """Перенаправление после выхода из системы"""
        flash("Вы вышли из системы", "info")
        return redirect(url_for('auth_blueprint.login'))

class UserController:
    """Класс контроллера для пользователей"""
    
    @staticmethod
    def allowed_file(filename):
        """Вспомогательная функция для проверки допустимых расширений файлов"""
        from flask import current_app
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    @staticmethod
    def home():
        """Главная страница"""
        if not current_user.is_authenticated:
            return UserView.render()

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
        return UserView.render(
            feed=feed,
            recent_tasks=recent_tasks,
            team_members=team_members
        )

    @staticmethod
    def dashboard():
        """Личный кабинет пользователя"""
        # Получаем задачи, где пользователь является ответственным
        assigned_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.created_at.desc()).all()
        
        # Получаем задачи, где пользователь является постановщиком
        created_tasks = Task.query.filter_by(created_by=current_user.id).order_by(Task.created_at.desc()).all()
        
        # Используем метод представления для рендеринга шаблона
        return UserView.render_dashboard(assigned_tasks=assigned_tasks, created_tasks=created_tasks)

    @staticmethod
    def edit_profile_page():
        """Страница редактирования профиля (GET)"""
        # Используем метод представления для рендеринга шаблона
        return UserView.render_edit_page()

    @staticmethod
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
        if file and UserController.allowed_file(file.filename):
            from flask import current_app
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            current_user.avatar = f"/static/uploads/{filename}"

        db.session.commit()
        # Используем метод представления для перенаправления
        return UserView.redirect_after_update()

    @staticmethod
    @login_required
    def view_profile(user_id):
        """Просмотр профиля пользователя"""
        user = User.query.get_or_404(user_id)
        
        # Проверяем, что пользователь принадлежит к той же команде, что и текущий пользователь
        if not current_user.is_admin and user.team_id != current_user.team_id:
            flash("У вас нет доступа к профилю этого пользователя", "danger")
            return redirect(url_for('user_blueprint.home'))
            
        # Используем метод представления для рендеринга шаблона
        return UserView.render_profile(user=user)

    @staticmethod
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
        return UserView.redirect_after_change()

    @staticmethod
    def register_page():
        """Страница регистрации (GET)"""
        teams = Team.query.all()
        # Используем метод представления для рендеринга шаблона
        return UserView.render_register_page(teams=teams)

    @staticmethod
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
        return UserView.redirect_after_register()

    @staticmethod
    def login_page():
        """Страница входа в систему (GET)"""
        # Используем метод представления для рендеринга шаблона
        return UserView.render_login_page()

    @staticmethod
    def login_user_func():
        """Вход в систему (POST)"""
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            # Используем метод представления для перенаправления
            return UserView.redirect_after_login()
        else:
            flash("Ошибка входа! Проверьте данные.", "danger")
            # Используем метод представления для рендеринга шаблона
            return UserView.render_login_page()

    @staticmethod
    def logout_user_func():
        """Выход из системы"""
        logout_user()
        # Используем метод представления для перенаправления
        return UserView.redirect_after_logout()

# Регистрируем маршруты
user_bp.add_url_rule('/', view_func=UserController.home, endpoint='home')
user_bp.add_url_rule('/dashboard', view_func=UserController.dashboard, endpoint='dashboard')
user_bp.add_url_rule('/edit_profile', view_func=UserController.edit_profile_page, endpoint='edit_profile', methods=['GET'])
user_bp.add_url_rule('/edit_profile', view_func=UserController.update_profile, endpoint='update_profile', methods=['POST'])
user_bp.add_url_rule('/profile', view_func=UserController.edit_profile_page, endpoint='profile', methods=['GET'])  # Оставляем для обратной совместимости
user_bp.add_url_rule('/profile', view_func=UserController.update_profile, endpoint='profile_post', methods=['POST'])  # Оставляем для обратной совместимости
user_bp.add_url_rule('/profile/<int:user_id>', view_func=UserController.view_profile, endpoint='view_profile')
user_bp.add_url_rule('/change_password', view_func=UserController.change_password, endpoint='change_password', methods=['POST'])
user_bp.add_url_rule('/register', view_func=UserController.register_page, endpoint='register', methods=['GET'])
user_bp.add_url_rule('/register', view_func=UserController.register_user, endpoint='register_post', methods=['POST'])
user_bp.add_url_rule('/login', view_func=UserController.login_page, endpoint='login', methods=['GET'])
user_bp.add_url_rule('/login', view_func=UserController.login_user_func, endpoint='login_post', methods=['POST'])
user_bp.add_url_rule('/logout', view_func=UserController.logout_user_func, endpoint='logout')
user_bp.add_url_rule('/<int:user_id>', view_func=UserController.view_profile, endpoint='user_profile')