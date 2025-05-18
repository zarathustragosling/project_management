from flask import render_template, redirect, url_for, flash, abort, jsonify
from flask_login import current_user
from .base_view import BaseView, LoginRequiredMixin

class KanbanView(BaseView, LoginRequiredMixin):
    """Представление для Kanban-доски"""
    
    def get(self):
        """Отображение Kanban-доски"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render(cls, tasks):
        """Рендеринг Kanban-доски"""
        return render_template('kanban.html', tasks=tasks)

class TaskCreateView(BaseView, LoginRequiredMixin): 
    """Представление для создания задачи"""
    
    def get(self):
        """Страница создания задачи (GET)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Создание задачи (POST)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_create_page(cls, team_projects, users, is_edit=False, current_date=None, next_date=None):
        """Рендеринг страницы создания задачи"""
        return render_template(
            'task_creator.html',
            team_projects=team_projects,
            users=users,
            is_edit=is_edit,
            current_date=current_date,
            next_date=next_date
        )
        
    @classmethod
    def redirect_after_create(cls):
        """Перенаправление после создания задачи"""
        flash("Задача создана!", "success")
        return redirect(url_for('task_blueprint.kanban'))

class TaskDetailView(BaseView, LoginRequiredMixin):
    """Представление для просмотра деталей задачи"""
    
    def get(self, task_id):
        """Просмотр деталей задачи"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render(cls, task, projects, users):
        """Рендеринг деталей задачи"""
        return render_template(
            'task_detail.html',
            task=task,
            projects=projects,
            users=users
        )

class TaskEditView(BaseView, LoginRequiredMixin):
    """Представление для редактирования задачи"""
    
    def get(self, task_id):
        """Страница редактирования задачи (GET)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self, task_id):
        """Обновление задачи (POST)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_edit_page(cls, task, projects, users, current_date):
        """Рендеринг страницы редактирования задачи"""
        return render_template(
            'task_creator.html',
            task=task,
            projects=projects,
            users=users,
            is_edit=True,
            current_date=current_date
        )
        
    @classmethod
    def redirect_after_update(cls):
        """Перенаправление после обновления задачи"""
        flash("Задача успешно обновлена!", "success")
        return redirect(url_for('task_blueprint.kanban'))

class TaskDeleteView(BaseView, LoginRequiredMixin):
    """Представление для удаления задачи"""
    
    def post(self, task_id):
        """Удаление задачи"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def redirect_after_delete(cls):
        """Перенаправление после удаления задачи"""
        flash("Задача удалена!", "success")
        return redirect(url_for('task_blueprint.kanban'))

class TaskUpdateAPIView(BaseView, LoginRequiredMixin):
    """API представление для обновления задачи"""
    
    def patch(self, task_id):
        """API для обновления задачи"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def json_response(cls, success=True, message="", data=None):
        """Формирование JSON-ответа"""
        response = {"success": success, "message": message}
        if data:
            response["data"] = data
        return jsonify(response)

class TaskStatusUpdateView(BaseView, LoginRequiredMixin):
    """Представление для обновления статуса задачи"""
    
    def post(self, task_id):
        """Обновление статуса задачи"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def json_response(cls, success=True, message="", data=None):
        """Формирование JSON-ответа"""
        response = {"success": success, "message": message}
        if data:
            response["data"] = data
        return jsonify(response)

class ProjectUsersView(BaseView, LoginRequiredMixin):
    """Представление для получения пользователей проекта"""
    
    def get(self, project_id):
        """Получение пользователей проекта"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def json_response(cls, users):
        """Формирование JSON-ответа со списком пользователей"""
        users_list = [{
            'id': user.id,
            'name': user.name,
            'email': user.email
        } for user in users]
        return jsonify(users_list)

# Примечание: Эти классы представлений сохранены для обратной совместимости,
# но теперь они не содержат бизнес-логику, которая перенесена в контроллеры.
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.