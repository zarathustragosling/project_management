from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user, login_required
from database import db, User, Team, Role, Project
import os, secrets
from werkzeug.utils import secure_filename
from utils.access_control import team_access_required, team_admin_required
from handlers.notification_handler import NotificationService

# Создаем Blueprint для маршрутов команд
team_bp = Blueprint('team', __name__, url_prefix='/team')

class TeamView:
    """Класс представления для команд"""
    
    @staticmethod
    def render(team, team_members, roles):
        """Рендеринг деталей команды"""
        return render_template('team_detail.html', team=team, team_members=team_members, roles=roles)
    
    @staticmethod
    def render_create_page():
        """Рендеринг страницы создания команды"""
        return render_template('create_team.html')
    
    @staticmethod
    def render_edit_page(team):
        """Рендеринг страницы редактирования команды"""
        return render_template('edit_team.html', team=team)
    
    @staticmethod
    def render_select_page():
        """Рендеринг страницы выбора команды"""
        return render_template('select_team.html')
    
    @staticmethod
    def render_join_page():
        """Рендеринг страницы присоединения к команде"""
        return render_template('join_team.html')
    
    @staticmethod
    def redirect_after_leave():
        """Перенаправление после выхода из команды"""
        flash("Вы вышли из команды", "success")
        return redirect(url_for('user_blueprint.home'))
    
    @staticmethod
    def redirect_after_refresh(team_id):
        """Перенаправление после обновления кода приглашения"""
        flash("Код приглашения обновлен", "success")
        return redirect(url_for('team_blueprint.team_detail', team_id=team_id))
    
    @staticmethod
    def redirect_after_update(team_id):
        """Перенаправление после обновления участника команды"""
        flash("Роль участника обновлена", "success")
        return redirect(url_for('team_blueprint.team_detail', team_id=team_id))
    
    @staticmethod
    def redirect_after_remove(team_id):
        """Перенаправление после удаления участника из команды"""
        flash("Участник удален из команды", "success")
        return redirect(url_for('team_blueprint.team_detail', team_id=team_id))

class TeamController:
    """Класс контроллера для команд"""
    
    @staticmethod
    @login_required
    @team_access_required
    def team_detail(team_id):
        """Просмотр деталей команды"""
        team = Team.query.get_or_404(team_id)
        team_members = User.query.filter_by(team_id=team_id).all()
        # Получаем список всех ролей для выпадающего списка
        roles = Role.query.all()
        # Используем метод представления для рендеринга шаблона
        return TeamView.render(team, team_members, roles)

    @staticmethod
    def create_team_page():
        """Страница создания команды (GET)"""
        # Используем метод представления для рендеринга шаблона
        return TeamView.render_create_page()

    @staticmethod
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

    @staticmethod
    def edit_team_page():
        """Страница редактирования команды (GET)"""
        team = current_user.team
        if not team:
            flash("Вы не состоите в команде", "error")
            return redirect(url_for('user_blueprint.home'))

        # Используем метод представления для рендеринга шаблона
        return TeamView.render_edit_page(team)

    @staticmethod
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

    @staticmethod
    def select_team_page():
        """Страница выбора команды (GET)"""
        # Используем метод представления для рендеринга шаблона
        return TeamView.render_select_page()

    @staticmethod
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

    @staticmethod
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
        return TeamView.redirect_after_leave()

    @staticmethod
    def refresh_invite_code():
        """Обновление кода приглашения"""
        team = current_user.team
        if not team:
            flash("Вы не состоите в команде", "error")
            return redirect(url_for('user_blueprint.home'))
        
        team.invite_code = secrets.token_urlsafe(6)
        db.session.commit()
        
        # Используем метод представления для перенаправления
        return TeamView.redirect_after_refresh(team.id)

    @staticmethod
    def join_team_page():
        """Страница присоединения к команде (GET)"""
        # Используем метод представления для рендеринга шаблона
        return TeamView.render_join_page()

    @staticmethod
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

    @staticmethod
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
        return TeamView.redirect_after_update(team_id)

    @staticmethod
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
        
        # Нельзя удалить себя из команды через этот метод
        if user.id == current_user.id:
            flash("Вы не можете удалить себя из команды через этот метод", "danger")
            return redirect(url_for('team_blueprint.team_detail', team_id=team_id))
            
        # Создаем уведомление об удалении из команды
        NotificationService.create_team_member_left_notification(user, team)
        
        # Удаляем пользователя из команды
        user.team_id = None
        user.role_id = None
        db.session.commit()
        
        # Используем метод представления для перенаправления
        return TeamView.redirect_after_remove(team_id)

# Регистрируем маршруты
team_bp.add_url_rule('/<int:team_id>', view_func=TeamController.team_detail, endpoint='team_detail')
team_bp.add_url_rule('/create', view_func=TeamController.create_team_page, endpoint='create_team', methods=['GET'])
team_bp.add_url_rule('/create', view_func=TeamController.create_team, endpoint='create_team_post', methods=['POST'])
team_bp.add_url_rule('/edit', view_func=TeamController.edit_team_page, endpoint='edit_team', methods=['GET'])
team_bp.add_url_rule('/edit', view_func=TeamController.update_team, endpoint='update_team', methods=['POST'])
team_bp.add_url_rule('/select', view_func=TeamController.select_team_page, endpoint='select_team', methods=['GET'])
team_bp.add_url_rule('/select', view_func=TeamController.select_team, endpoint='select_team_post', methods=['POST'])
team_bp.add_url_rule('/leave', view_func=TeamController.leave_team, endpoint='leave_team')
team_bp.add_url_rule('/refresh-invite', view_func=TeamController.refresh_invite_code, endpoint='refresh_invite_code')
team_bp.add_url_rule('/join', view_func=TeamController.join_team_page, endpoint='join_team', methods=['GET'])
team_bp.add_url_rule('/join', view_func=TeamController.join_team, endpoint='join_team_post', methods=['POST'])
team_bp.add_url_rule('/<int:team_id>/members', view_func=TeamController.add_team_member, endpoint='add_team_member', methods=['POST'])
team_bp.add_url_rule('/<int:team_id>/members/<int:user_id>/remove', view_func=TeamController.remove_team_member, endpoint='remove_team_member')