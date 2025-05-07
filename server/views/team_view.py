from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user
from database import db, User, Team, Role, Project
import os, secrets
from werkzeug.utils import secure_filename
from .base_view import BaseView, LoginRequiredMixin, TeamLeadRequiredMixin

class TeamDetailView(BaseView, LoginRequiredMixin):
    """Представление для просмотра деталей команды"""
    
    def get(self, team_id):
        team = Team.query.get_or_404(team_id)
        team_members = User.query.filter_by(team_id=team_id).all()
        return render_template('team_detail.html', team=team, team_members=team_members)

class TeamCreateView(BaseView, LoginRequiredMixin):
    """Представление для создания команды"""
    
    def get(self):
        return render_template('create_team.html')
    
    def post(self):
        name = request.form.get('name')
        avatar_url = request.form.get('avatar_url')
        description = request.form.get('description')

        if Team.query.filter_by(name=name).first():
            flash("Команда с таким именем уже существует", "danger")
            return redirect(url_for('team.create_team'))

        invite_code = secrets.token_urlsafe(6)
        team = Team(name=name, avatar_url=avatar_url, description=description, invite_code=invite_code)
        db.session.add(team)
        db.session.commit()

        teamlead_role = Role.query.filter_by(name="TeamLead").first()
        current_user.team_id = team.id
        current_user.role = teamlead_role
        db.session.commit()

        flash(f"Команда создана! Код приглашения: {invite_code}", "success")
        return redirect(url_for('team.team_detail', team_id=team.id))

class TeamEditView(BaseView, TeamLeadRequiredMixin):
    """Представление для редактирования команды"""
    
    def get(self):
        team = current_user.team
        if not team:
            flash("Вы не состоите в команде", "error")
            return redirect(url_for('user.home'))

        return render_template('edit_team.html', team=team)
    
    def post(self):
        team = current_user.team
        if not team:
            flash("Вы не состоите в команде", "error")
            return redirect(url_for('user.home'))

        team.name = request.form.get('name')
        team.avatar_url = request.form.get('avatar_url')
        team.description = request.form.get('description')
        db.session.commit()
        flash("Настройки команды обновлены!", "success")
        return redirect(url_for('team.team_detail', team_id=team.id))

class TeamSelectView(BaseView, LoginRequiredMixin):
    """Представление для выбора команды"""
    
    def get(self):
        return render_template('select_team.html')
    
    def post(self):
        invite_code = request.form.get('invite_code')
        team = Team.query.filter_by(invite_code=invite_code).first()
        
        if not team:
            flash("Неверный код приглашения", "danger")
            return redirect(url_for('team.select_team'))
        
        member_role = Role.query.filter_by(name="Участник").first()
        current_user.team_id = team.id
        current_user.role = member_role
        db.session.commit()
        
        flash(f"Вы присоединились к команде {team.name}!", "success")
        return redirect(url_for('team.team_detail', team_id=team.id))

class TeamLeaveView(BaseView, LoginRequiredMixin):
    """Представление для выхода из команды"""
    
    def post(self):
        if not current_user.team_id:
            flash("Вы не состоите в команде", "warning")
            return redirect(url_for('user.home'))
        
        current_user.team_id = None
        current_user.role_id = None
        db.session.commit()
        
        flash("Вы вышли из команды", "info")
        return redirect(url_for('user.home'))

class TeamInviteCodeView(BaseView, TeamLeadRequiredMixin):
    """Представление для обновления кода приглашения"""
    
    def post(self):
        team = current_user.team
        if not team:
            flash("Вы не состоите в команде", "error")
            return redirect(url_for('user.home'))
        
        team.invite_code = secrets.token_urlsafe(6)
        db.session.commit()
        
        flash("Код приглашения обновлен!", "success")
        return redirect(url_for('team.team_detail', team_id=team.id))

class TeamJoinView(BaseView, LoginRequiredMixin):
    """Представление для присоединения к команде"""
    
    def get(self):
        return render_template('join_team.html')
    
    def post(self):
        code = request.form.get('invite_code')
        team = Team.query.filter_by(invite_code=code).first()

        if not team:
            flash("Неверный код приглашения", "danger")
            return redirect(url_for('team.join_team'))

        member_role = Role.query.filter_by(name="Участник").first()
        current_user.team_id = team.id
        current_user.role = member_role
        db.session.commit()

        flash("Вы успешно присоединились к команде!", "success")
        return redirect(url_for('team.team_detail', team_id=team.id))

class TeamMemberManagementView(BaseView, LoginRequiredMixin):
    """Представление для управления участниками команды"""
    
    def post(self, team_id):
        """Добавление участника в команду"""
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            user.team_id = team_id
            db.session.commit()
        return redirect(url_for('team.team_detail', team_id=team_id))

class TeamMemberRemoveView(BaseView, TeamLeadRequiredMixin):
    """Представление для удаления участника из команды"""
    
    def get(self, team_id, user_id):
        user = User.query.get_or_404(user_id)
        if user.team_id != team_id:
            abort(403)

        user.team_id = None
        user.role = None
        db.session.commit()
        flash("Пользователь удален из команды", "success")
        return redirect(url_for('team.team_detail', team_id=team_id))