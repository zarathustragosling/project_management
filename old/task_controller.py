from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user, login_required
from database import db, User, Project, Task, TaskStatus, Comment, CommentType, Team
from datetime import datetime, date, timedelta
from views.task_view import KanbanView, TaskCreateView, TaskDetailView, TaskEditView, TaskDeleteView, TaskUpdateAPIView, TaskStatusUpdateView, ProjectUsersView
from views.notification_view import NotificationService
from controllers.access_control import team_access_required, team_admin_required

# Добавляем пользовательский фильтр для шаблона Jinja
def slice_filter(value, start, end=None):
    if end is None:
        return value[start:]
    return value[start:end]

# Создаем Blueprint для маршрутов задач
task_bp = Blueprint('task', __name__, url_prefix='/task')

# Регистрируем пользовательский фильтр для шаблонов
@task_bp.app_template_filter('slice')
def slice_filter_for_template(value, start, end=None):
    return slice_filter(value, start, end)

# Функции контроллера для задач
@login_required
def kanban():
    """Отображение Kanban-доски"""
    # Проверяем, что пользователь состоит в команде
    if not current_user.team_id:
        flash("Вы не состоите в команде", "warning")
        return redirect(url_for('team_blueprint.select_team'))

    # Получаем все задачи команды, включая архивные
    tasks = Task.query \
        .join(Project) \
        .filter(Project.team_id == current_user.team_id) \
        .options(
            db.joinedload(Task.assigned_user),
            db.joinedload(Task.creator),
            db.joinedload(Task.project)
        ) \
        .order_by(Task.created_at.desc()) \
        .all()

    # Используем метод представления для рендеринга шаблона
    return KanbanView.render(tasks)

def task_creator():
    """Страница создания задачи (GET)"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return redirect(url_for('root_blueprint.login'))
        
    if not current_user.team:
        return redirect(url_for("team_blueprint.edit_team"))
    
    # Проверяем, что пользователь имеет роль постановщика (TeamLead или Постановщик)
    if not current_user.is_teamlead() and not current_user.is_admin and not current_user.has_role("Постановщик"):
        flash("У вас нет прав для создания задач", "danger")
        return redirect(url_for('task_blueprint.kanban'))
    
    team_projects = Project.query.filter_by(team_id=current_user.team.id).all()
    users = current_user.team.users if current_user.team else []
    
    current_date_obj = date.today()
    current_date = current_date_obj.strftime('%Y-%m-%d')
    next_date = (current_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')

    # Используем метод представления для рендеринга шаблона
    return TaskCreateView.render_create_page(
        team_projects=team_projects,
        users=users,
        is_edit=False,
        current_date=current_date,
        next_date=next_date
    )

def create_task():
    """Создание задачи (POST)"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return redirect(url_for('root_blueprint.login'))
    
    # Проверяем, что пользователь имеет роль постановщика (TeamLead или Постановщик)
    if not current_user.is_teamlead() and not current_user.is_admin and not current_user.has_role("Постановщик"):
        flash("У вас нет прав для создания задач", "danger")
        return redirect(url_for('task_blueprint.kanban'))
        
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority')
    project_id = request.form.get('project_id')
    deadline = request.form.get('deadline')
    assigned_to = request.form.get('assigned_to')
    created_by = request.form.get('created_by', current_user.id)
    created_at_str = request.form.get('created_at')

    if not title or not priority or not project_id:
        flash("Заполните обязательные поля", "danger")
        return redirect(url_for('task_blueprint.task_creator'))

    created_at = datetime.strptime(created_at_str, '%Y-%m-%d') if created_at_str else datetime.utcnow()

    new_task = Task(
        title=title,
        description=description if description else None,
        priority=priority,
        status=TaskStatus.TO_DO,
        project_id=int(project_id),
        assigned_to=int(assigned_to) if assigned_to else None,
        created_by=int(created_by),
        deadline=datetime.strptime(deadline, '%Y-%m-%d') if deadline else None,
        created_at=created_at
    )

    db.session.add(new_task)
    db.session.commit()
    
    # Создаем уведомление о назначении ответственным, если задача кому-то назначена
    if new_task.assigned_to:
        NotificationService.create_task_assigned_notification(new_task)
        
    # Используем метод представления для перенаправления
    return TaskCreateView.redirect_after_create()

@team_access_required
def task_detail(task_id):
    """Просмотр деталей задачи"""
    task = Task.query.options(
        db.joinedload(Task.comments)
          .joinedload(Comment.author),
        db.joinedload(Task.comments)
          .joinedload(Comment.attachments),
        db.joinedload(Task.comments)
          .joinedload(Comment.replies)
    ).get_or_404(task_id)
    
    # Получаем только проекты команды пользователя
    projects = Project.query.filter_by(team_id=current_user.team_id).all()
    # Получаем только пользователей команды
    users = User.query.filter_by(team_id=current_user.team_id).all()
    
    # Используем метод представления для рендеринга шаблона
    return TaskDetailView.render(
        task=task,
        projects=projects,
        users=users
    )

def edit_task(task_id):
    """Страница редактирования задачи (GET)"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return redirect(url_for('root_blueprint.login'))
        
    task = Task.query.get_or_404(task_id)
    
    # Проверяем, что пользователь имеет право редактировать задачу
    # Право имеют: создатель задачи, TeamLead, Постановщик или админ
    if task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.has_role("Постановщик") and not current_user.is_admin:
        abort(403)
    
    projects = Project.query.filter_by(team_id=current_user.team_id).all()
    users = User.query.filter_by(team_id=current_user.team_id).all()
    current_date = task.created_at.strftime('%Y-%m-%d') if task.created_at else date.today().strftime('%Y-%m-%d')

    # Используем метод представления для рендеринга шаблона
    return TaskEditView.render_edit_page(
        task=task,
        projects=projects,
        users=users,
        current_date=current_date
    )

def update_task(task_id):
    """Обновление задачи (POST)"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return redirect(url_for('root_blueprint.login'))
        
    task = Task.query.get_or_404(task_id)
    
    # Проверяем, что пользователь имеет право редактировать задачу
    # Право имеют: создатель задачи, TeamLead, Постановщик или админ
    if task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.has_role("Постановщик") and not current_user.is_admin:
        abort(403)
        
    task.title = request.form.get('title', '').strip()
    task.description = request.form.get('description', '').strip()
    task.priority = request.form.get('priority', 'Средний')
    status_value = request.form.get('status')
    if isinstance(status_value, TaskStatus):
        task.status = status_value
    elif status_value:
        try:
            task.status = getattr(TaskStatus, status_value)
        except (AttributeError, TypeError):
            # Если не удалось получить по имени, пробуем по значению
            for status in TaskStatus:
                if status.value == status_value:
                    task.status = status
                    break

    assigned_to = request.form.get('assigned_to')
    old_assigned_to = task.assigned_to
    task.assigned_to = int(assigned_to) if assigned_to else None

    deadline = request.form.get('deadline')
    task.deadline = datetime.strptime(deadline, '%Y-%m-%d') if deadline else None
    
    # Если назначен новый ответственный, создаем уведомление
    if task.assigned_to and task.assigned_to != old_assigned_to:  
        NotificationService.create_task_assigned_notification(task)

    created_at_str = request.form.get('created_at')
    if created_at_str:
        task.created_at = datetime.strptime(created_at_str, '%Y-%m-%d')

    db.session.commit()
    # Используем метод представления для перенаправления
    return TaskEditView.redirect_after_update()

def delete_task(task_id):
    """Удаление задачи"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return redirect(url_for('root_blueprint.login'))
        
    task = Task.query.get_or_404(task_id)
    
    # Проверяем, что пользователь имеет право редактировать задачу
    # Право имеют: создатель задачи, TeamLead, Постановщик или админ
    if task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.has_role("Постановщик") and not current_user.is_admin:
        abort(403)
        
    db.session.delete(task)
    db.session.commit()
    # Используем метод представления для перенаправления
    return TaskDeleteView.redirect_after_delete()

def update_task_api(task_id):
    """API для обновления задачи"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return TaskUpdateAPIView.json_response(success=False, message="Требуется авторизация")
        
    task = Task.query.get_or_404(task_id)
    if task.created_by != current_user.id:
        return TaskUpdateAPIView.json_response(success=False, message="Нет прав")

    data = request.get_json()

    try:
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.priority = data.get('priority', task.priority)
        status_value = data.get('status', task.status.name)
        task.status = status_value if isinstance(status_value, TaskStatus) else TaskStatus(status_value).value

        project_id = data.get('project_id')
        if project_id:
            task.project_id = int(project_id)

        assigned_to = data.get('assigned_to')
        old_assigned_to = task.assigned_to
        task.assigned_to = int(assigned_to) if assigned_to else None

        deadline = data.get('deadline')
        if deadline:
            task.deadline = datetime.fromisoformat(deadline)
            
        # Если назначен новый ответственный, создаем уведомление
        if task.assigned_to and task.assigned_to != old_assigned_to:  
            NotificationService.create_task_assigned_notification(task)

        db.session.commit()
        return TaskUpdateAPIView.json_response(success=True)
    except Exception as e:
        db.session.rollback()
        return TaskUpdateAPIView.json_response(success=False, message=str(e))

def update_task_status(task_id):
    """Обновление статуса задачи"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return TaskUpdateAPIView.json_response(success=False, message="Требуется авторизация")
        
    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    new_status = data.get('status', '').strip().upper().replace(" ", "_")
    try:
        # Обновляем статус задачи
        task.status = TaskStatus[new_status]
        
        # Получаем все задачи в новой колонке и обновляем их позиции
        tasks_in_column = Task.query.filter_by(status=task.status).order_by(Task.position).all()
        max_position = max([t.position for t in tasks_in_column]) if tasks_in_column else -1
        task.position = max_position + 1
        
        db.session.commit()
        return TaskStatusUpdateView.json_response(success=True, data={'new_status': task.status.value})
    except KeyError:
        return TaskStatusUpdateView.json_response(success=False, message=f'Некорректный статус: {new_status}')

def get_project_users(project_id):
    """Получение пользователей проекта"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return ProjectUsersView.json_response([])
        
    project = Project.query.get_or_404(project_id)
    team = Team.query.get(project.team_id)
    
    if not team:
        return ProjectUsersView.json_response([])
    
    users = team.users
    return ProjectUsersView.json_response(users)

def archive_task(task_id):
    """Архивирование задачи"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return redirect(url_for('root_blueprint.login'))
        
    task = Task.query.get_or_404(task_id)
    
    # Проверяем, что пользователь имеет право архивировать задачу
    # Право имеют: создатель задачи, TeamLead, Постановщик или админ
    if task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.has_role("Постановщик") and not current_user.is_admin:
        abort(403)
    
    task.is_archived = True
    db.session.commit()
    
    flash("Задача перемещена в архив", "success")
    return redirect(url_for('task_blueprint.kanban'))

def restore_task(task_id):
    """Восстановление задачи из архива"""
    # Проверяем, что пользователь аутентифицирован
    if not current_user.is_authenticated:
        return redirect(url_for('root_blueprint.login'))
        
    task = Task.query.get_or_404(task_id)
    
    # Проверяем, что пользователь имеет право восстанавливать задачу
    # Право имеют: создатель задачи, TeamLead, Постановщик или админ
    if task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.has_role("Постановщик") and not current_user.is_admin:
        abort(403)
    
    task.is_archived = False
    db.session.commit()
    
    flash("Задача восстановлена из архива", "success")
    return redirect(url_for('task_blueprint.task_detail', task_id=task_id))

@login_required
def archive():
    """Отображение списка архивированных задач"""
    # Проверяем, что пользователь состоит в команде
    if not current_user.team_id:
        flash("Вы не состоите в команде", "warning")
        return redirect(url_for('team_blueprint.select_team'))

    archived_tasks = Task.query \
        .join(Project) \
        .filter(Project.team_id == current_user.team_id) \
        .filter(Task.is_archived == True) \
        .options(
            db.joinedload(Task.assigned_user),
            db.joinedload(Task.creator),
            db.joinedload(Task.project)
        ) \
        .order_by(Task.created_at.desc()) \
        .all()

    return render_template('archive.html', tasks=archived_tasks)

# Регистрируем маршруты
task_bp.add_url_rule('/kanban', view_func=kanban, endpoint='kanban')
task_bp.add_url_rule('/create', view_func=task_creator, endpoint='task_creator', methods=['GET'])
task_bp.add_url_rule('/create', view_func=create_task, endpoint='create_task', methods=['POST'])
task_bp.add_url_rule('/<int:task_id>', view_func=task_detail, endpoint='task_detail')
task_bp.add_url_rule('/edit/<int:task_id>', view_func=edit_task, endpoint='edit_task', methods=['GET'])
task_bp.add_url_rule('/edit/<int:task_id>', view_func=update_task, endpoint='update_task', methods=['POST'])
task_bp.add_url_rule('/delete/<int:task_id>', view_func=delete_task, endpoint='delete_task', methods=['POST'])
task_bp.add_url_rule('/<int:task_id>/update', view_func=update_task_api, endpoint='update_task_api', methods=['PATCH'])
task_bp.add_url_rule('/get_project_users/<int:project_id>', view_func=get_project_users, endpoint='get_project_users')
task_bp.add_url_rule('/update_task_status/<int:task_id>', view_func=update_task_status, endpoint='update_task_status', methods=['POST'])
task_bp.add_url_rule('/archive/<int:task_id>', view_func=archive_task, endpoint='archive_task', methods=['POST'])
task_bp.add_url_rule('/restore/<int:task_id>', view_func=restore_task, endpoint='restore_task', methods=['POST'])
task_bp.add_url_rule('/archive', view_func=archive, endpoint='archive')

# Маршрут для отладки задач
@task_bp.route('/debug')
def debug():
    tasks = Task.query.all()
    return '<br>'.join(f"{t.id} | {t.title} | {t.status} | {t.is_archived}" for t in tasks)

# Сохраняем классы представлений для обратной совместимости
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.