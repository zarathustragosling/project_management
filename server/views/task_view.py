from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user
from database import db, User, Project, Task, TaskStatus, Comment, CommentType
from datetime import datetime, date
from .base_view import BaseView, LoginRequiredMixin

class KanbanView(BaseView, LoginRequiredMixin):
    """Представление для Kanban-доски"""
    
    def get(self):
        if not current_user.team_id:
            return redirect(url_for('team.edit_team'))

        tasks = Task.query \
            .join(Project) \
            .filter(Project.team_id == current_user.team_id) \
            .options(
                db.joinedload(Task.assigned_user),
                db.joinedload(Task.creator),
                db.joinedload(Task.project)
            ).all()

        return render_template('kanban.html', tasks=tasks)

class TaskCreateView(BaseView, LoginRequiredMixin):
    """Представление для создания задачи"""
    
    def get(self):
        if not current_user.team:
            return redirect(url_for("team.edit_team"))
        
        team_projects = Project.query.filter_by(team_id=current_user.team.id).all()
        users = current_user.team.users if current_user.team else []
        current_date = date.today().strftime('%Y-%m-%d')
        
        return render_template('task_creator.html',
                              team_projects=team_projects,
                              users=users,
                              is_edit=False,
                              current_date=current_date)
    
    def post(self):
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
            return redirect(url_for('task.task_creator'))

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
        flash("Задача создана!", "success")
        return redirect(url_for('task.kanban'))

class TaskDetailView(BaseView, LoginRequiredMixin):
    """Представление для просмотра деталей задачи"""
    
    def get(self, task_id):
        task = Task.query.options(
            db.joinedload(Task.comments)
              .joinedload(Comment.author),
            db.joinedload(Task.comments)
              .joinedload(Comment.attachments),
            db.joinedload(Task.comments)
              .joinedload(Comment.replies)
        ).get_or_404(task_id)
        
        return render_template(
            'task_detail.html',
            task=task,
            projects=Project.query.all(),
            users=User.query.all()
        )

class TaskEditView(BaseView, LoginRequiredMixin):
    """Представление для редактирования задачи"""
    
    def get(self, task_id):
        task = Task.query.get_or_404(task_id)
        
        if task.created_by != current_user.id and not current_user.is_teamlead():
            abort(403)
        
        projects = Project.query.filter_by(team_id=current_user.team_id).all()
        users = User.query.filter_by(team_id=current_user.team_id).all()
        current_date = task.created_at.strftime('%Y-%m-%d') if task.created_at else date.today().strftime('%Y-%m-%d')

        return render_template(
            'task_creator.html',
            task=task,
            projects=projects,
            users=users,
            is_edit=True,
            current_date=current_date
        )
    
    def post(self, task_id):
        task = Task.query.get_or_404(task_id)
        
        if task.created_by != current_user.id and not current_user.is_teamlead():
            abort(403)
            
        task.title = request.form.get('title', '').strip()
        task.description = request.form.get('description', '').strip()
        task.priority = request.form.get('priority', 'Средний')
        task.status = TaskStatus(request.form.get('status'))

        assigned_to = request.form.get('assigned_to')
        task.assigned_to = int(assigned_to) if assigned_to else None

        deadline = request.form.get('deadline')
        task.deadline = datetime.strptime(deadline, '%Y-%m-%d') if deadline else None

        created_at_str = request.form.get('created_at')
        if created_at_str:
            task.created_at = datetime.strptime(created_at_str, '%Y-%m-%d')

        db.session.commit()
        flash("Задача успешно обновлена!", "success")
        return redirect(url_for('task.kanban'))

class TaskDeleteView(BaseView, LoginRequiredMixin):
    """Представление для удаления задачи"""
    
    def post(self, task_id):
        task = Task.query.get_or_404(task_id)
        
        if task.created_by != current_user.id and not current_user.is_teamlead():
            abort(403)
            
        db.session.delete(task)
        db.session.commit()
        flash("Задача удалена!", "success")
        return redirect(url_for('task.kanban'))

class TaskUpdateAPIView(BaseView, LoginRequiredMixin):
    """API представление для обновления задачи"""
    
    def patch(self, task_id):
        task = Task.query.get_or_404(task_id)
        if task.created_by != current_user.id:
            return jsonify({'success': False, 'error': 'Нет прав'}), 403

        data = request.get_json()

        try:
            task.title = data.get('title', task.title)
            task.description = data.get('description', task.description)
            task.priority = data.get('priority', task.priority)
            task.status = TaskStatus(data.get('status', task.status.name))

            project_id = data.get('project_id')
            if project_id:
                task.project_id = int(project_id)

            assigned_to = data.get('assigned_to')
            task.assigned_to = int(assigned_to) if assigned_to else None

            deadline = data.get('deadline')
            if deadline:
                task.deadline = datetime.fromisoformat(deadline)

            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 400

class TaskStatusUpdateView(BaseView, LoginRequiredMixin):
    """Представление для обновления статуса задачи"""
    
    def post(self, task_id):
        task = Task.query.get_or_404(task_id)
        data = request.get_json()

        new_status = data.get('status', '').strip().upper().replace(" ", "_")
        try:
            task.status = TaskStatus[new_status]
            db.session.commit()
            return jsonify({'success': True, 'new_status': task.status.value})
        except KeyError:
            return jsonify({'success': False, 'error': f'Invalid status: {new_status}'}), 400

class ProjectUsersView(BaseView, LoginRequiredMixin):
    """Представление для получения пользователей проекта"""
    
    def get(self, project_id):
        project = Project.query.get_or_404(project_id)
        team = Team.query.get(project.team_id)
        
        if not team:
            return jsonify([])
        
        users = [{"id": u.id, "username": u.username} for u in team.users]
        return jsonify(users)