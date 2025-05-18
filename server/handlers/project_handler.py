from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from database import db, User, Project, Task, Report, Team
from datetime import datetime
from functools import wraps
from utils.access_control import team_access_required, team_admin_required

# Создаем Blueprint для маршрутов проектов
project_bp = Blueprint('project', __name__, url_prefix='/project')

class ProjectView:
    """Класс представления для проектов"""
    
    @staticmethod
    def render(projects):
        """Рендеринг списка проектов"""
        return render_template('projects.html', projects=projects)
    
    @staticmethod
    def render_detail(project):
        """Рендеринг деталей проекта"""
        return render_template('project_detail.html', project=project)
    
    @staticmethod
    def render_create_page(teams):
        """Рендеринг страницы создания проекта"""
        return render_template('create_project.html', teams=teams)
    
    @staticmethod
    def redirect_after_create():
        """Перенаправление после создания проекта"""
        flash("Проект создан!", "success")
        return redirect(url_for('project_blueprint.project_list'))
    
    @staticmethod
    def redirect_after_delete():
        """Перенаправление после удаления проекта"""
        flash("Проект и все связанные задачи и отчеты успешно удалены!", "success")
        return redirect(url_for('project_blueprint.project_list'))

class ProjectController:
    """Класс контроллера для проектов"""
    
    @staticmethod
    def check_project_permissions():
        """Проверка прав на управление проектами"""
        if not current_user.is_authenticated:
            return False
        return current_user.is_teamlead() or current_user.is_admin or current_user.has_role("Постановщик")
    
    @staticmethod
    @login_required
    def project_list():
        """Отображение списка проектов"""
        if not current_user.team:
            return redirect(url_for('team_blueprint.select_team'))
            
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
        # Используем метод представления для рендеринга шаблона
        return ProjectView.render(projects)

    @staticmethod
    @login_required
    def create_project_quick():
        """Быстрое создание нового проекта из списка проектов"""
        # Проверяем права
        if not ProjectController.check_project_permissions():
            flash("У вас нет прав для создания проектов", "danger")
            return redirect(url_for('project_blueprint.project_list'))
            
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
            flash("Проект создан!", "success")
            
        return redirect(url_for('project_blueprint.project_list'))

    @staticmethod
    @login_required
    @team_access_required
    def project_detail(project_id):
        """Просмотр деталей проекта"""
        project = Project.query.get_or_404(project_id)
        # Используем метод представления для рендеринга шаблона
        return ProjectView.render_detail(project)

    @staticmethod
    @login_required
    @team_admin_required
    def create_project_form():
        """Форма создания проекта"""
        # Проверяем права
        if not ProjectController.check_project_permissions():
            flash("У вас нет прав для создания проектов", "danger")
            return redirect(url_for('project_blueprint.project_list'))
            
        # Показываем только команду пользователя
        teams = [current_user.team] if current_user.team else []
        # Используем метод представления для рендеринга шаблона
        return ProjectView.render_create_page(teams)

    @staticmethod
    @login_required
    @team_admin_required
    def create_project():
        """Обработка создания проекта"""
        # Проверяем права
        if not ProjectController.check_project_permissions():
            flash("У вас нет прав для создания проектов", "danger")
            return redirect(url_for('project_blueprint.project_list'))
            
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        team_id = request.form.get('team_id')
        
        if not name or not team_id:
            flash("Название проекта и команда обязательны", "danger")
            return redirect(url_for('project_blueprint.create_project'))
        
        new_project = Project(
            name=name,
            description=description if description else None,
            team_id=int(team_id)
        )
        
        db.session.add(new_project)
        db.session.commit()
        # Используем метод представления для перенаправления
        return ProjectView.redirect_after_create()

    @staticmethod
    @login_required
    def delete_project(project_id):
        """Удаление проекта"""
        # Проверяем права
        if not ProjectController.check_project_permissions():
            flash("У вас нет прав для удаления проектов", "danger")
            return redirect(url_for('project_blueprint.project_list'))
            
        project = Project.query.get_or_404(project_id)
        
        # Удаляем все задачи, связанные с проектом
        Task.query.filter_by(project_id=project.id).delete()
        
        # Удаляем все отчеты, связанные с проектом
        Report.query.filter_by(project_id=project.id).delete()
        
        # Удаляем сам проект
        db.session.delete(project)
        db.session.commit()
        
        # Используем метод представления для перенаправления
        return ProjectView.redirect_after_delete()

# Регистрируем маршруты
project_bp.add_url_rule('/list', view_func=ProjectController.project_list, endpoint='project_list', methods=['GET'])
project_bp.add_url_rule('/list', view_func=ProjectController.create_project_quick, endpoint='create_project_quick', methods=['POST'])
project_bp.add_url_rule('/<int:project_id>', view_func=ProjectController.project_detail, endpoint='project_detail', methods=['GET'])
project_bp.add_url_rule('/create', view_func=ProjectController.create_project_form, endpoint='create_project', methods=['GET'])
project_bp.add_url_rule('/create', view_func=ProjectController.create_project, endpoint='create_project_post', methods=['POST'])
project_bp.add_url_rule('/delete/<int:project_id>', view_func=ProjectController.delete_project, endpoint='delete_project', methods=['GET'])