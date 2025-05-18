from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user, login_required
from database import db, User, Team, Role, Project
import os, secrets
from werkzeug.utils import secure_filename
from views.team_view import TeamDetailView, TeamCreateView, TeamEditView, TeamSelectView, TeamLeaveView, TeamInviteCodeView, TeamJoinView, TeamMemberManagementView, TeamMemberRemoveView
from views.notification_view import NotificationService
from controllers.access_control import team_access_required, team_admin_required

# Создаем Blueprint для маршрутов команд
team_bp = Blueprint('team', __name__, url_prefix='/team')

# Функции контроллера для команд
@login_required
@team_access_required
def team_detail(team_id):
    """Просмотр деталей команды"""
    team = Team.query.get_or_404(team_id)
    team_members = User.query.filter_by(team_id=team_id).all()
    # Получаем список всех ролей для выпадающего списка
    roles = Role.query.all()
    # Используем метод представления для рендеринга шаблона
    return TeamDetailView.render(team, team_members, roles)

def create_team_page():
    """Страница создания команды (GET)"""
    # Используем метод представления для рендеринга шаблона
    return TeamCreateView.render_create_page()

def create_team():
    """Создание команды (POST)"""
    name = request.form.get('name')
    avatar_url = request.form.get('avatar_url')
    description = request.form.get('description')

    if Team.query.filter_by(name=name).first():
        flash("Команда с таким именем уже существует", "danger")
        return redirect(url_for('team_blueprint.create_team'))

    invite_code = secrets.token_urlsafe(6)
    team = Team(name=name, avatar_url=avatar_url, description=description, invite_code=invite_code)
    db.session.add(team)
    db.session.commit()

    teamlead_role = Role.query.filter_by(name="TeamLead").first()
    current_user.team_id = team.id
    current_user.role = teamlead_role
    db.session.commit()

    flash(f"Команда создана! Код приглашения: {invite_code}", "success")
    return redirect(url_for('team_blueprint.team_detail', team_id=team.id))

def edit_team_page():
    """Страница редактирования команды (GET)"""
    team = current_user.team
    if not team:
        flash("Вы не состоите в команде", "error")
        return redirect(url_for('user_blueprint.home'))

    # Используем метод представления для рендеринга шаблона
    return TeamEditView.render_edit_page(team)

def update_team():
    """Обновление команды (POST)"""
    team = current_user.team
    if not team:
        flash("Вы не состоите в команде", "error")
        return redirect(url_for('user_blueprint.home'))

    team.name = request.form.get('name')
    team.avatar_url = request.form.get('avatar_url')
    team.description = request.form.get('description')
    db.session.commit()
    flash("Настройки команды обновлены!", "success")
    return redirect(url_for('team_blueprint.team_detail', team_id=team.id))

def select_team_page():
    """Страница выбора команды (GET)"""
    # Используем метод представления для рендеринга шаблона
    return TeamSelectView.render_select_page()

def select_team():
    """Выбор команды (POST)"""
    invite_code = request.form.get('invite_code')
    team = Team.query.filter_by(invite_code=invite_code).first()
    
    if not team:
        flash("Неверный код приглашения", "danger")
        return redirect(url_for('team_blueprint.select_team'))
    
    member_role = Role.query.filter_by(name="Участник").first()
    current_user.team_id = team.id
    current_user.role = member_role
    db.session.commit()
    
    flash(f"Вы присоединились к команде {team.name}!", "success")
    return redirect(url_for('team_blueprint.team_detail', team_id=team.id))

def leave_team():
    """Выход из команды"""
    if not current_user.team_id:
        flash("Вы не состоите в команде", "warning")
        return redirect(url_for('user_blueprint.home'))
    
    team = current_user.team
    
    # Создаем уведомление о выходе из команды
    NotificationService.create_team_member_left_notification(current_user, team)
    
    current_user.team_id = None
    current_user.role_id = None
    db.session.commit()
    
    # Используем метод представления для перенаправления
    return TeamLeaveView.redirect_after_leave()

def refresh_invite_code():
    """Обновление кода приглашения"""
    team = current_user.team
    if not team:
        flash("Вы не состоите в команде", "error")
        return redirect(url_for('user_blueprint.home'))
    
    team.invite_code = secrets.token_urlsafe(6)
    db.session.commit()
    
    # Используем метод представления для перенаправления
    return TeamInviteCodeView.redirect_after_refresh(team.id)

def join_team_page():
    """Страница присоединения к команде (GET)"""
    # Используем метод представления для рендеринга шаблона
    return TeamJoinView.render_join_page()

def join_team():
    """Присоединение к команде (POST)"""
    code = request.form.get('invite_code')
    team = Team.query.filter_by(invite_code=code).first()

    if not team:
        flash("Неверный код приглашения", "danger")
        return redirect(url_for('team_blueprint.join_team'))

    # Присоединяем пользователя к команде без назначения роли
    # Только TeamLead получает роль при создании команды
    current_user.team_id = team.id
    # Не назначаем роль автоматически
    db.session.commit()
    
    # Создаем уведомление о присоединении к команде
    NotificationService.create_team_member_joined_notification(current_user, team)

    flash("Вы успешно присоединились к команде!", "success")
    return redirect(url_for('team_blueprint.team_detail', team_id=team.id))

@login_required
@team_admin_required
def add_team_member(team_id):
    """Добавление участника в команду или изменение его роли"""
    # Проверяем, что пользователь управляет своей командой
    if team_id != current_user.team_id and not current_user.is_admin:
        flash("Вы можете управлять только своей командой", "danger")
        return redirect(url_for('team_blueprint.team_detail', team_id=current_user.team_id))
        
    user_id = request.form.get('user_id')
    role_id = request.form.get('role_id')
    user = User.query.get(user_id)
    
    if not user:
        flash("Пользователь не найден", "danger")
        return redirect(url_for('team_blueprint.team_detail', team_id=team_id))
        
    # Проверяем, что пользователь принадлежит к этой команде
    if user.team_id != team_id:
        user.team_id = team_id
    
    # Обновляем роль пользователя
    if role_id:
        role = Role.query.get(role_id)
        if role and role.name not in ["Admin", "TeamLead"]:
            user.role_id = role.id
    else:
        # Если role_id пустой, убираем роль
        user.role_id = None
        
    db.session.commit()
    # Используем метод представления для перенаправления
    return TeamMemberManagementView.redirect_after_update(team_id)

@login_required
@team_admin_required
def remove_team_member(team_id, user_id):
    """Удаление участника из команды"""
    # Проверяем, что пользователь управляет своей командой
    if team_id != current_user.team_id and not current_user.is_admin:
        flash("Вы можете управлять только своей командой", "danger")
        return redirect(url_for('team_blueprint.team_detail', team_id=current_user.team_id))
        
    user = User.query.get_or_404(user_id)
    team = Team.query.get_or_404(team_id)
    if user.team_id != team_id:
        abort(403)
    
    # Нельзя удалить самого себя через этот метод
    if user.id == current_user.id:
        flash("Вы не можете удалить себя из команды через этот метод", "danger")
        return redirect(url_for('team_blueprint.team_detail', team_id=team_id))
    
    # Создаем уведомление о выходе из команды
    NotificationService.create_team_member_left_notification(user, team)

    user.team_id = None
    user.role = None
    db.session.commit()
    # Используем метод представления для перенаправления
    return TeamMemberRemoveView.redirect_after_remove(team_id)

# Регистрируем маршруты
team_bp.add_url_rule('/<int:team_id>', view_func=team_detail, endpoint='team_detail')
team_bp.add_url_rule('/create', view_func=create_team_page, endpoint='create_team', methods=['GET'])
team_bp.add_url_rule('/create', view_func=create_team, endpoint='create_team_post', methods=['POST'])
team_bp.add_url_rule('/edit', view_func=edit_team_page, endpoint='edit_team', methods=['GET'])
team_bp.add_url_rule('/edit', view_func=update_team, endpoint='update_team', methods=['POST'])
team_bp.add_url_rule('/select', view_func=select_team_page, endpoint='select_team', methods=['GET'])
team_bp.add_url_rule('/select', view_func=select_team, endpoint='select_team_post', methods=['POST'])
team_bp.add_url_rule('/leave', view_func=leave_team, endpoint='leave_team', methods=['POST'])
team_bp.add_url_rule('/refresh_invite_code', view_func=refresh_invite_code, endpoint='refresh_invite_code', methods=['POST'])
team_bp.add_url_rule('/join', view_func=join_team_page, endpoint='join_team', methods=['GET'])
team_bp.add_url_rule('/join', view_func=join_team, endpoint='join_team_post', methods=['POST'])
team_bp.add_url_rule('/<int:team_id>/add_member', view_func=add_team_member, endpoint='add_member', methods=['POST'])
team_bp.add_url_rule('/remove_member/<int:team_id>/<int:user_id>', view_func=remove_team_member, endpoint='remove_member', methods=['GET'])

# Сохраняем классы представлений для обратной совместимости
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.