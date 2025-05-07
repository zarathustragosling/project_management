from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from database import db, User, Team, Project, Task, Comment
from werkzeug.utils import secure_filename
import os
from .base_view import BaseView, AdminRequiredMixin

class AdminPanelView(BaseView, AdminRequiredMixin):
    """Представление для административной панели"""
    
    def get(self):
        users = User.query.all()
        teams = Team.query.all()
        projects = Project.query.all()
        tasks = Task.query.all()
        comments = Comment.query.all()
        
        return render_template('system_admin_panel.html',
                              users=users,
                              teams=teams,
                              projects=projects,
                              tasks=tasks,
                              comments=comments)

class UserManagementView(BaseView, AdminRequiredMixin):
    """Представление для управления пользователями"""
    
    def post(self, user_id):
        """Удаление пользователя"""
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash("Пользователь удалён", "success")
        return redirect(url_for('admin.system_admin_panel'))
    
    def get(self, user_id):
        """Редактирование пользователя"""
        user = User.query.get_or_404(user_id)
        all_users = User.query.all()
        return render_template('admin/edit_user_admin.html', user=user, all_users=all_users)
    
    def put(self, user_id):
        """Обновление пользователя"""
        user = User.query.get_or_404(user_id)
        
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.description = request.form.get('bio')
        user.is_admin = request.form.get('is_admin') == 'on'
        
        if 'avatar' in request.files and request.files['avatar'].filename:
            avatar_file = request.files['avatar']
            filename = secure_filename(avatar_file.filename)
            avatar_path = os.path.join('static/uploads', filename)
            avatar_file.save(os.path.join('e:\\project_management', avatar_path))
            user.avatar = '/' + avatar_path.replace('\\', '/')
        
        db.session.commit()
        flash("Пользователь обновлён", "success")
        return redirect(url_for('admin.system_admin_panel'))

class TeamManagementView(BaseView, AdminRequiredMixin):
    """Представление для управления командами"""
    
    def get(self, team_id):
        """Редактирование команды"""
        team = Team.query.get_or_404(team_id)
        return render_template('admin/edit_team_admin.html', team=team)
    
    def post(self, team_id):
        """Обновление команды"""
        team = Team.query.get_or_404(team_id)
        
        if request.form.get('_method') == 'DELETE':
            # Обнуляем team_id у участников
            for user in team.users:
                user.team_id = None
            
            db.session.delete(team)
            db.session.commit()
            flash("Команда удалена", "info")
        else:
            team.name = request.form.get('name')
            team.description = request.form.get('description')
            team.avatar_url = request.form.get('avatar_url')
            db.session.commit()
            flash("Команда обновлена", "success")
            
        return redirect(url_for('admin.system_admin_panel'))

class ProjectManagementView(BaseView, AdminRequiredMixin):
    """Представление для управления проектами"""
    
    def get(self, project_id):
        """Редактирование проекта"""
        project = Project.query.get_or_404(project_id)
        return render_template('admin/edit_project_admin.html', project=project)
    
    def post(self, project_id):
        """Обновление или удаление проекта"""
        project = Project.query.get_or_404(project_id)
        
        if request.form.get('_method') == 'DELETE':
            db.session.delete(project)
            db.session.commit()
            flash("Проект удалён", "info")
        else:
            project.name = request.form.get('name')
            project.description = request.form.get('description')
            db.session.commit()
            flash("Проект обновлён", "success")
            
        return redirect(url_for('admin.system_admin_panel'))

class TaskManagementView(BaseView, AdminRequiredMixin):
    """Представление для управления задачами"""
    
    def get(self, task_id):
        """Редактирование задачи"""
        task = Task.query.get_or_404(task_id)
        return render_template('admin/edit_task_admin.html', task=task)
    
    def post(self, task_id):
        """Обновление или удаление задачи"""
        task = Task.query.get_or_404(task_id)
        
        if request.form.get('_method') == 'DELETE':
            db.session.delete(task)
            db.session.commit()
            flash("Задача удалена", "info")
        else:
            task.title = request.form.get('title')
            task.description = request.form.get('description')
            task.priority = request.form.get('priority')
            task.status = request.form.get('status')
            
            deadline = request.form.get('deadline')
            if deadline:
                from datetime import datetime
                task.deadline = datetime.strptime(deadline, '%Y-%m-%d')
            else:
                task.deadline = None
                
            db.session.commit()
            flash("Задача обновлена", "success")
            
        return redirect(url_for('admin.system_admin_panel'))

class CommentManagementView(BaseView, AdminRequiredMixin):
    """Представление для управления комментариями"""
    
    def get(self, comment_id):
        """Редактирование комментария"""
        comment = Comment.query.get_or_404(comment_id)
        return render_template('admin/edit_comment_admin.html', comment=comment)
    
    def post(self, comment_id):
        """Обновление или удаление комментария"""
        comment = Comment.query.get_or_404(comment_id)
        
        if request.form.get('_method') == 'DELETE':
            db.session.delete(comment)
            db.session.commit()
            flash("Комментарий удалён", "info")
        else:
            comment.content = request.form.get('content')
            db.session.commit()
            flash("Комментарий обновлён", "success")
            
        return redirect(url_for('admin.system_admin_panel'))