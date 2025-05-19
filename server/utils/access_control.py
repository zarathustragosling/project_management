from flask import abort, redirect, url_for, flash
from flask_login import current_user
from functools import wraps
from server.database import db, Project, Task, Team, User




def team_access_required(f):
    """
    Декоратор для проверки доступа к ресурсам команды.
    Проверяет, принадлежит ли запрашиваемый ресурс к команде текущего пользователя.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем, аутентифицирован ли пользователь
        if not current_user.is_authenticated:
            return redirect(url_for('root_blueprint.login'))
            
        # Проверяем, состоит ли пользователь в команде
        if not current_user.team_id:
            flash("Вы не состоите в команде", "warning")
            return redirect(url_for('team_blueprint.select_team'))
            
        # Проверяем доступ к проекту
        if 'project_id' in kwargs:
            project = Project.query.get_or_404(kwargs['project_id'])
            if project.team_id != current_user.team_id and not current_user.is_admin:
                flash("У вас нет доступа к этому проекту", "danger")
                return abort(403)
                
        # Проверяем доступ к задаче
        if 'task_id' in kwargs:
            task = Task.query.get_or_404(kwargs['task_id'])
            project = Project.query.get_or_404(task.project_id)
            if project.team_id != current_user.team_id and not current_user.is_admin:
                flash("У вас нет доступа к этой задаче", "danger")
                return abort(403)
                
        # Проверяем доступ к команде
        if 'team_id' in kwargs:
            team = Team.query.get_or_404(kwargs['team_id'])
            if team.id != current_user.team_id and not current_user.is_admin:
                flash("У вас нет доступа к этой команде", "danger")
                return abort(403)
                
        # Проверяем доступ к пользователю (только для просмотра профиля)
        if 'user_id' in kwargs:
            user = User.query.get_or_404(kwargs['user_id'])
            if user.team_id != current_user.team_id and not current_user.is_admin:
                flash("У вас нет доступа к профилю этого пользователя", "danger")
                return abort(403)
                
        return f(*args, **kwargs)
    return decorated_function

def team_admin_required(f):
    """
    Декоратор для проверки прав администратора команды (TeamLead).
    Проверяет, имеет ли пользователь роль TeamLead в своей команде.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем, аутентифицирован ли пользователь
        if not current_user.is_authenticated:
            return redirect(url_for('root_blueprint.login'))
            
        # Проверяем, состоит ли пользователь в команде
        if not current_user.team_id:
            flash("Вы не состоите в команде", "warning")
            return redirect(url_for('team_blueprint.select_team'))
            
        # Проверяем, является ли пользователь TeamLead или администратором
        if not current_user.is_teamlead() and not current_user.is_admin:
            flash("У вас нет прав для выполнения этого действия", "danger")
            return abort(403)
            
        # Если в запросе есть team_id, проверяем, что это команда пользователя
        if 'team_id' in kwargs and not current_user.is_admin:
            team_id = int(kwargs['team_id'])
            if team_id != current_user.team_id:
                flash("Вы можете управлять только своей командой", "danger")
                return abort(403)
                
        return f(*args, **kwargs)
    return decorated_function