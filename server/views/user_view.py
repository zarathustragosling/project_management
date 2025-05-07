from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, login_user, logout_user, current_user
from database import db, User, Team, Role, Project, Task, Comment, CommentType
from werkzeug.utils import secure_filename
import os
from .base_view import BaseView, LoginRequiredMixin

class HomeView(BaseView):
    """Представление для главной страницы"""
    
    def get(self):
        if not current_user.is_authenticated:
            return render_template('index.html')

        if not current_user.team:
            return redirect(url_for('team.select_team'))

        elif not current_user.team.name:
            return redirect(url_for('team.edit_team'))    # Настройка уже созданной

        team_id = current_user.team.id
        feed = Comment.query \
            .filter_by(type=CommentType.FEED) \
            .order_by(Comment.created_at.desc()) \
            .limit(10).all()
        recent_tasks = Task.query.filter(Task.project.has(team_id=team_id)).order_by(Task.deadline.asc()).limit(5).all()
        team_members = User.query.filter_by(team_id=team_id).all()

        return render_template('index.html',
                               feed=feed,
                               recent_tasks=recent_tasks,
                               team_members=team_members)

class ProfileUpdateView(BaseView, LoginRequiredMixin):
    """Представление для обновления профиля"""
    
    def get(self):
        return render_template('profile.html')
    
    def post(self):
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
        flash("Профиль обновлен!", "success")
        return redirect(url_for('user.update_profile'))

class ProfileView(BaseView, LoginRequiredMixin):
    """Представление для просмотра профиля"""
    
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        return render_template('user_profile.html', user=user)

class PasswordChangeView(BaseView, LoginRequiredMixin):
    """Представление для изменения пароля"""
    
    def post(self):
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        if not current_user.check_password(old_password):
            flash("Старый пароль неверный", "danger")
            return redirect(url_for('user.update_profile'))

        current_user.set_password(new_password)
        db.session.commit()
        flash("Пароль изменен", "success")
        return redirect(url_for('user.update_profile'))

class RegisterView(BaseView):
    """Представление для регистрации"""
    
    def get(self):
        teams = Team.query.all()
        return render_template('register.html', teams=teams)
    
    def post(self):
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        team_id = request.form.get('team_id')

        if not username or not email or not password:
            flash("Все поля обязательны!", "danger")
            return redirect(url_for('user.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Пользователь с таким email уже зарегистрирован!", "warning")
            return redirect(url_for('user.register'))

        new_user = User(username=username, email=email, team_id=team_id)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Регистрация успешна! Войдите в систему.", "success")
        return redirect(url_for('user.login'))

class LoginView(BaseView):
    """Представление для входа в систему"""
    
    def get(self):
        return render_template('login.html')
    
    def post(self):
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('user.home'))
        else:
            flash("Ошибка входа! Проверьте данные.", "danger")
            return render_template('login.html')

class LogoutView(BaseView, LoginRequiredMixin):
    """Представление для выхода из системы"""
    
    def get(self):
        logout_user()
        flash("Вы вышли из системы.", "info")
        return redirect(url_for('user.login'))

def allowed_file(filename):
    """Вспомогательная функция для проверки допустимых расширений файлов"""
    from flask import current_app
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']