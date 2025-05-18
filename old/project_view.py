from flask import render_template, redirect, url_for, flash
from .base_view import BaseView, LoginRequiredMixin

class ProjectListView(BaseView, LoginRequiredMixin):
    """Представление для списка проектов"""
    
    def dispatch_request(self):
        """Обработка запроса для списка проектов"""
        # Вся бизнес-логика перенесена в контроллер project_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render(cls, projects):
        """Рендеринг списка проектов"""
        return render_template('projects.html', projects=projects)

class ProjectDetailView(BaseView, LoginRequiredMixin):
    """Представление для деталей проекта"""
    
    def dispatch_request(self, project_id):
        """Просмотр деталей проекта"""
        # Вся бизнес-логика перенесена в контроллер project_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render(cls, project):
        """Рендеринг деталей проекта"""
        return render_template('project_detail.html', project=project)

class ProjectCreateView(BaseView, LoginRequiredMixin):
    """Представление для создания проекта"""
    
    def dispatch_request(self):
        """Форма создания проекта"""
        # Вся бизнес-логика перенесена в контроллер project_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_create_page(cls, teams):
        """Рендеринг страницы создания проекта"""
        return render_template('create_project.html', teams=teams)
        
    @classmethod
    def redirect_after_create(cls):
        """Перенаправление после создания проекта"""
        flash("Проект создан!", "success")
        return redirect(url_for('project_blueprint.project_list'))

class ProjectDeleteView(BaseView, LoginRequiredMixin):
    """Представление для удаления проекта"""
    
    def dispatch_request(self, project_id):
        """Удаление проекта"""
        # Вся бизнес-логика перенесена в контроллер project_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def redirect_after_delete(cls):
        """Перенаправление после удаления проекта"""
        flash("Проект и все связанные задачи и отчеты успешно удалены!", "success")
        return redirect(url_for('project_blueprint.project_list'))

# Примечание: Эти классы представлений сохранены для обратной совместимости,
# но теперь они не содержат бизнес-логику, которая перенесена в контроллеры.
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.