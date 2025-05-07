from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from database import db, User, Project, Task, Report, Team
from datetime import datetime
from .base_view import BaseView, LoginRequiredMixin

class ProjectListView(BaseView, LoginRequiredMixin):
    """Представление для списка проектов"""
    
    def get(self):
        """Отображение списка проектов"""
        if not current_user.team:
            return redirect(url_for('team.select_team'))
            
        # Фильтрация и сортировка
        q = request.args.get('q', '', type=str).strip()
        sort = request.args.get('sort', 'newest')
        
        query = Project.query.filter_by(team_id=current_user.team.id)
        
        if q:
            query = query.filter(Project.name.ilike(f'%{q}%'))
        
        if sort == 'name':
            query = query.order_by(Project.name.asc())
        elif sort == 'oldest':
            query = query.order_by(Project.id.asc())
        else:  # newest
            query = query.order_by(Project.id.desc())
        
        projects = query.all()
        return render_template('projects.html', projects=projects)
    
    def post(self):
        """Создание нового проекта"""
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if name:
            new_project = Project(
                name=name,
                description=description,
                team_id=current_user.team.id
            )
            db.session.add(new_project)
            db.session.commit()
            
        return redirect(url_for('project.project_list'))

class ProjectDetailView(BaseView, LoginRequiredMixin):
    """Представление для деталей проекта"""
    
    def get(self, project_id):
        """Просмотр деталей проекта"""
        project = Project.query.get_or_404(project_id)
        return render_template('project_detail.html', project=project)

class ProjectCreateView(BaseView, LoginRequiredMixin):
    """Представление для создания проекта"""
    
    def get(self):
        """Форма создания проекта"""
        teams = Team.query.all()
        return render_template('create_project.html', teams=teams)
    
    def post(self):
        """Обработка создания проекта"""
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        team_id = request.form.get('team_id')
        
        if not name or not team_id:
            flash("Название проекта и команда обязательны", "danger")
            return redirect(url_for('project.create_project'))
        
        new_project = Project(
            name=name,
            description=description if description else None,
            team_id=int(team_id)
        )
        
        db.session.add(new_project)
        db.session.commit()
        flash("Проект создан!", "success")
        return redirect(url_for('project.project_list'))

class ProjectDeleteView(BaseView, LoginRequiredMixin):
    """Представление для удаления проекта"""
    
    def get(self, project_id):
        """Удаление проекта"""
        project = Project.query.get_or_404(project_id)
        
        # Удаляем все задачи, связанные с проектом
        Task.query.filter_by(project_id=project.id).delete()
        
        # Удаляем все отчеты, связанные с проектом
        Report.query.filter_by(project_id=project.id).delete()
        
        # Удаляем сам проект
        db.session.delete(project)
        db.session.commit()
        
        flash("Проект и все связанные задачи и отчеты успешно удалены!", "success")
        return redirect(url_for('project.project_list'))