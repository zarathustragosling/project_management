from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from database import db, User, Project, Task, Report, Team
from datetime import datetime
from functools import wraps
from views.project_view import ProjectListView, ProjectDetailView, ProjectCreateView, ProjectDeleteView
from controllers.access_control import team_access_required, team_admin_required

# Создаем Blueprint для маршрутов проектов
project_bp = Blueprint('project', __name__, url_prefix='/project')

# Вспомогательные функции для проверки прав
def check_project_permissions():
    """Проверка прав на управление проектами"""
    if not current_user.is_authenticated:
        return False
    return current_user.is_teamlead() or current_user.is_admin or current_user.has_role("Постановщик")

# Контроллер для проектов
@project_bp.route('/list', methods=['GET'])
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
    return ProjectListView.render(projects)

@project_bp.route('/list', methods=['POST'])
@login_required
def create_project_quick():
    """Быстрое создание нового проекта из списка проектов"""
    # Проверяем права
    if not check_project_permissions():
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

@project_bp.route('/<int:project_id>', methods=['GET'])
@login_required
@team_access_required
def project_detail(project_id):
    """Просмотр деталей проекта"""
    project = Project.query.get_or_404(project_id)
    # Используем метод представления для рендеринга шаблона
    return ProjectDetailView.render(project)

@project_bp.route('/create', methods=['GET'])
@login_required
@team_admin_required
def create_project_form():
    """Форма создания проекта"""
    # Проверяем права
    if not check_project_permissions():
        flash("У вас нет прав для создания проектов", "danger")
        return redirect(url_for('project_blueprint.project_list'))
        
    # Показываем только команду пользователя
    teams = [current_user.team] if current_user.team else []
    # Используем метод представления для рендеринга шаблона
    return ProjectCreateView.render_create_page(teams)

@project_bp.route('/create', methods=['POST'])
@login_required
@team_admin_required
def create_project():
    """Обработка создания проекта"""
    # Проверяем права
    if not check_project_permissions():
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
    return ProjectCreateView.redirect_after_create()

@project_bp.route('/delete/<int:project_id>', methods=['GET'])
@login_required
def delete_project(project_id):
    """Удаление проекта"""
    # Проверяем права
    if not check_project_permissions():
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
    return ProjectDeleteView.redirect_after_delete()