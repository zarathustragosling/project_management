from flask import request, redirect, url_for, flash, abort
from flask_login import current_user
from database import db, Project, Task, Team, User
import re

def init_middleware(app):
    """
    Инициализация промежуточного ПО для проверки доступа к ресурсам команды.
    """
    @app.before_request
    def check_team_access():
        # Пропускаем запросы к статическим файлам и авторизации
        if request.path.startswith('/static') or \
           request.path.startswith('/login') or \
           request.path.startswith('/register') or \
           request.path == '/' or \
           request.path.startswith('/team/select') or \
           request.path.startswith('/team/create') or \
           request.path.startswith('/team/join'):
            return None
            
        # Проверяем, аутентифицирован ли пользователь
        if not current_user.is_authenticated:
            return None  # Обработка будет выполнена декоратором login_required
            
        # Администраторы имеют доступ ко всему
        if current_user.is_admin:
            return None
            
        # Проверяем, состоит ли пользователь в команде
        if not current_user.team_id and not request.path.startswith('/team/select'):
            flash("Вы не состоите в команде", "warning")
            return redirect(url_for('team_blueprint.select_team'))
            
        # Проверяем доступ к проекту
        project_pattern = re.compile(r'/project/(\d+)')
        project_match = project_pattern.match(request.path)
        if project_match:
            project_id = int(project_match.group(1))
            project = Project.query.get(project_id)
            if project and project.team_id != current_user.team_id:
                flash("У вас нет доступа к этому проекту", "danger")
                return abort(403)
                
        # Проверяем доступ к задаче
        task_pattern = re.compile(r'/task/(?!kanban|archive|create)([\w-]+)/(\d+)')
        task_match = task_pattern.match(request.path)
        if task_match:
            task_id = int(task_match.group(2))
            task = Task.query.get(task_id)
            if task:
                project = Project.query.get(task.project_id)
                if project and project.team_id != current_user.team_id:
                    flash("У вас нет доступа к этой задаче", "danger")
                    return abort(403)
                    
        # Проверяем доступ к команде
        team_pattern = re.compile(r'/team/(\d+)')
        team_match = team_pattern.match(request.path)
        if team_match:
            team_id = int(team_match.group(1))
            if team_id != current_user.team_id:
                flash("У вас нет доступа к этой команде", "danger")
                return abort(403)
                
        # Проверяем доступ к пользователю
        user_pattern = re.compile(r'/user/profile/(\d+)')
        user_match = user_pattern.match(request.path)
        if user_match:
            user_id = int(user_match.group(1))
            user = User.query.get(user_id)
            if user and user.team_id != current_user.team_id:
                flash("У вас нет доступа к профилю этого пользователя", "danger")
                return abort(403)
                
        return None