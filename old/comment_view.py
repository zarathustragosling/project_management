from flask.views import MethodView
from flask import render_template, redirect, url_for, flash, jsonify
from views.base_view import BaseView, LoginRequiredMixin

class AddCommentView(LoginRequiredMixin, BaseView):
    """Представление для добавления комментария к задаче"""
    
    def post(self, task_id):
        # Вся бизнес-логика перенесена в контроллер comment_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def render_json_response(success, comment=None, error=None, status_code=200):
        """Рендеринг JSON-ответа для добавления комментария"""
        if success:
            return jsonify(success=True, comment=comment)
        else:
            return jsonify(success=False, error=error), status_code

class EditCommentView(LoginRequiredMixin, BaseView):
    """Представление для редактирования комментария"""
    
    def post(self, comment_id):
        # Вся бизнес-логика перенесена в контроллер comment_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def render_json_response(success, comment=None, error=None, status_code=200):
        """Рендеринг JSON-ответа для редактирования комментария"""
        if success:
            return jsonify(success=True, comment=comment)
        else:
            return jsonify(success=False, error=error), status_code

class RenderCommentView(BaseView):
    """Представление для рендеринга HTML комментария"""
    
    def get(self, comment_id):
        # Вся бизнес-логика перенесена в контроллер comment_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def render(comment, current_user):
        """Рендеринг HTML комментария"""
        return render_template("_comment_block.html", comment=comment, current_user=current_user)

class PostFeedCommentView(LoginRequiredMixin, BaseView):
    """Представление для публикации комментария в ленте"""
    
    def post(self):
        # Вся бизнес-логика перенесена в контроллер comment_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def redirect_after_post():
        """Перенаправление после публикации комментария в ленте"""
        flash("Сообщение отправлено", "success")
        return redirect(url_for("user_blueprint.home"))

class MarkAsSolutionView(LoginRequiredMixin, BaseView):
    """Представление для отметки комментария как решения"""
    
    def post(self, comment_id):
        # Вся бизнес-логика перенесена в контроллер comment_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def redirect_after_mark(task_id):
        """Перенаправление после отметки комментария как решения"""
        flash("Комментарий помечен как решение задачи", "success")
        return redirect(url_for("task_blueprint.task_detail", task_id=task_id))

class UnmarkAsSolutionView(LoginRequiredMixin, BaseView):
    """Представление для снятия отметки решения с комментария"""
    
    def post(self, comment_id):
        # Вся бизнес-логика перенесена в контроллер comment_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def redirect_after_unmark(task_id):
        """Перенаправление после снятия отметки решения с комментария"""
        flash("Отметка решения снята с комментария", "success")
        return redirect(url_for("task_blueprint.task_detail", task_id=task_id))

class DeleteCommentView(LoginRequiredMixin, BaseView):
    """Представление для удаления комментария"""
    
    def post(self, comment_id):
        # Вся бизнес-логика перенесена в контроллер comment_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def redirect_after_delete(task_id=None):
        """Перенаправление после удаления комментария"""
        flash("Комментарий удален", "success")
        if task_id:
            return redirect(url_for("task_blueprint.task_detail", task_id=task_id))
        else:
            return redirect(url_for("user_blueprint.home"))

# Примечание: Эти классы представлений сохранены для обратной совместимости,
# но теперь они не содержат бизнес-логику, которая перенесена в контроллеры.
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.