from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import current_user, login_required
from server.database import db, User, Project, Task, TaskStatus, Comment, CommentType, Team
from datetime import datetime, date, timedelta
from server.utils.access_control import team_access_required, team_admin_required
from server.handlers.notification_handler import NotificationService

# Создаем Blueprint для маршрутов задач
task_bp = Blueprint('task', __name__, url_prefix='/task')

# Добавляем пользовательский фильтр для шаблона Jinja
def slice_filter(value, start, end=None):
    if end is None:
        return value[start:]
    return value[start:end]

# Регистрируем пользовательский фильтр для шаблонов
@task_bp.app_template_filter('slice')
def slice_filter_for_template(value, start, end=None):
    return slice_filter(value, start, end)

class TaskView:
    """Класс представления для задач"""
    
    @staticmethod
    def render(tasks):
        """Рендеринг Kanban-доски"""
        return render_template('kanban.html', tasks=tasks)
    
    @staticmethod
    def render_create_page(team_projects, users, is_edit=False, current_date=None, next_date=None):
        """Рендеринг страницы создания задачи"""
        return render_template(
            'task_creator.html',
            team_projects=team_projects,
            users=users,
            is_edit=is_edit,
            current_date=current_date,
            next_date=next_date
        )
    
    
    @staticmethod
    def redirect_after_create():
        """Перенаправление после создания задачи"""
        flash("Задача создана!", "success")
        return redirect(url_for('task_blueprint.kanban'))
    
    @staticmethod
    def render_detail(task, projects, users):
        """Рендеринг деталей задачи"""
        return render_template(
            'task_detail.html',
            task=task,
            projects=projects,
            users=users
        )
    
    @staticmethod
    def render_edit_page(task, projects, users, current_date):
        """Рендеринг страницы редактирования задачи"""
        return render_template(
            'task_creator.html',
            task=task,
            projects=projects,
            users=users,
            is_edit=True,
            current_date=current_date
        )
    
    @staticmethod
    def redirect_after_update():
        """Перенаправление после обновления задачи"""
        flash("Задача обновлена!", "success")
        return redirect(url_for('task_blueprint.kanban'))
    
    @staticmethod
    def redirect_after_delete():
        """Перенаправление после удаления задачи"""
        flash("Задача удалена!", "success")
        return redirect(url_for('task_blueprint.kanban'))
    
    @staticmethod
    def render_project_users(users):
        """Рендеринг списка пользователей проекта"""
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'avatar': user.avatar
        } for user in users])

class TaskController:
    """Класс контроллера для задач"""
    
    @staticmethod
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
        return TaskView.render(tasks)

    @staticmethod
    def task_creator():
        """Страница создания задачи (GET)"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return redirect(url_for('root_blueprint.login'))
            
        if not current_user.team:
            return redirect(url_for("team_blueprint.edit_team"))    # Настройка уже созданной
        
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
        return TaskView.render_create_page(
            team_projects=team_projects,
            users=users,
            is_edit=False,
            current_date=current_date,
            next_date=next_date
        )

    @staticmethod
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
        return TaskView.redirect_after_create()

    @staticmethod
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
        return TaskView.render_detail(
            task=task,
            projects=projects,
            users=users
        )

    @staticmethod
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
        return TaskView.render_edit_page(
            task=task,
            projects=projects,
            users=users,
            current_date=current_date
        )

    @staticmethod
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
        
        project_id = request.form.get('project_id')
        if project_id:
            task.project_id = int(project_id)
            
        deadline = request.form.get('deadline')
        if deadline:
            task.deadline = datetime.strptime(deadline, '%Y-%m-%d')
        else:
            task.deadline = None
            
        # Обновляем ответственного
        old_assigned_to = task.assigned_to
        assigned_to = request.form.get('assigned_to')
        if assigned_to:
            task.assigned_to = int(assigned_to)
        else:
            task.assigned_to = None
            
        # Если ответственный изменился, создаем уведомление
        if task.assigned_to and task.assigned_to != old_assigned_to:
            NotificationService.create_task_assigned_notification(task)
            
        db.session.commit()
        
        # Используем метод представления для перенаправления
        return TaskView.redirect_after_update()

    @staticmethod
    def delete_task(task_id):
        """Удаление задачи"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return redirect(url_for('root_blueprint.login'))
            
        task = Task.query.get_or_404(task_id)
        
        # Проверяем, что пользователь имеет право удалять задачу
        # Право имеют: создатель задачи, TeamLead или админ
        if task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.is_admin:
            abort(403)
            
        # Удаляем все комментарии к задаче
        Comment.query.filter_by(task_id=task.id).delete()
        
        # Удаляем саму задачу
        db.session.delete(task)
        db.session.commit()
        
        # Используем метод представления для перенаправления
        return TaskView.redirect_after_delete()

    @staticmethod
    def update_task_status():
        """Обновление статуса задачи через API"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Требуется авторизация'}), 401
            
        task_id = request.json.get('task_id')
        status = request.json.get('status')
        position = request.json.get('position')
        
        if not task_id or not status:
            return jsonify({'success': False, 'message': 'Отсутствуют обязательные параметры'}), 400
            
        task = Task.query.get_or_404(task_id)
        
        # Проверяем, что пользователь имеет право обновлять задачу
        # Право имеют: ответственный за задачу, создатель задачи, TeamLead, Постановщик или админ
        if task.assigned_to != current_user.id and task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.has_role("Постановщик") and not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403
            
        # Обновляем статус задачи
        try:
            task.status = getattr(TaskStatus, status)
        except (AttributeError, TypeError):
            # Если не удалось получить по имени, пробуем по значению
            for s in TaskStatus:
                if s.value == status:
                    task.status = s
                    break
            else:
                return jsonify({'success': False, 'message': 'Некорректный статус'}), 400
                
        # Обновляем позицию задачи, если она указана
        if position is not None:
            task.position = position
            
        db.session.commit()
        
        return jsonify({'success': True})

    @staticmethod
    def get_project_users(project_id):
        """Получение списка пользователей проекта"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Требуется авторизация'}), 401
            
        project = Project.query.get_or_404(project_id)
        
        # Проверяем, что проект принадлежит команде пользователя
        if project.team_id != current_user.team_id and not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403
            
        # Получаем пользователей команды
        users = User.query.filter_by(team_id=project.team_id).all()
        
        # Используем метод представления для рендеринга списка пользователей
        return TaskView.render_project_users(users)

    @staticmethod
    def archive_task(task_id):
        """Архивирование задачи"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Требуется авторизация'}), 401
            
        task = Task.query.get_or_404(task_id)
        
        # Проверяем, что пользователь имеет право архивировать задачу
        # Право имеют: создатель задачи, TeamLead или админ
        if task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403
            
        # Архивируем задачу
        task.is_archived = True
        db.session.commit()
        
        # Проверяем, был ли запрос AJAX или обычный
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        else:
            # Перенаправляем на канбан-доску
            return redirect(url_for('task_blueprint.kanban'))

    @staticmethod
    def unarchive_task(task_id):
        """Разархивирование задачи"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Требуется авторизация'}), 401
            
        task = Task.query.get_or_404(task_id)
        
        # Проверяем, что пользователь имеет право разархивировать задачу
        # Право имеют: создатель задачи, TeamLead или админ
        if task.created_by != current_user.id and not current_user.is_teamlead() and not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403
            
        # Разархивируем задачу
        task.is_archived = False
        db.session.commit()
        
        # Проверяем, был ли запрос AJAX или обычный
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        else:
            # Перенаправляем на страницу архива
            return redirect(url_for('task_blueprint.archive'))
    
    @staticmethod
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
task_bp.add_url_rule('/', view_func=TaskController.kanban, endpoint='kanban')
task_bp.add_url_rule('/create', view_func=TaskController.task_creator, endpoint='task_creator', methods=['GET'])
task_bp.add_url_rule('/create', view_func=TaskController.create_task, endpoint='create_task', methods=['POST'])
task_bp.add_url_rule('/<int:task_id>', view_func=TaskController.task_detail, endpoint='task_detail', methods=['GET'])
task_bp.add_url_rule('/<int:task_id>/edit', view_func=TaskController.edit_task, endpoint='edit_task', methods=['GET'])
task_bp.add_url_rule('/<int:task_id>/edit', view_func=TaskController.update_task, endpoint='update_task', methods=['POST'])
task_bp.add_url_rule('/<int:task_id>/delete', view_func=TaskController.delete_task, endpoint='delete_task', methods=['GET'])
task_bp.add_url_rule('/update-status', view_func=TaskController.update_task_status, endpoint='update_task_status', methods=['POST'])
task_bp.add_url_rule('/project/<int:project_id>/users', view_func=TaskController.get_project_users, endpoint='get_project_users', methods=['GET'])
task_bp.add_url_rule('/<int:task_id>/archive', view_func=TaskController.archive_task, endpoint='archive_task', methods=['POST'])
task_bp.add_url_rule('/<int:task_id>/unarchive', view_func=TaskController.unarchive_task, endpoint='restore_task', methods=['POST'])
task_bp.add_url_rule('/archive', view_func=TaskController.archive, endpoint='archive', methods=['GET'])