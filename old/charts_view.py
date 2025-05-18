from flask.views import MethodView
from flask import render_template, jsonify
from views.base_view import BaseView, LoginRequiredMixin

class ChartsView(LoginRequiredMixin, BaseView):
    """Представление для отображения страницы диаграмм"""
    
    def get(self):
        # Вся бизнес-логика перенесена в контроллер charts_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def render(projects=None):
        """Рендеринг страницы диаграмм"""
        return render_template('charts.html', projects=projects)

class GanttDataView(LoginRequiredMixin, BaseView):
    """Представление для получения данных для диаграммы Ганта"""
    
    def get(self, project_id):
        # Вся бизнес-логика перенесена в контроллер charts_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def render_json(data):
        """Рендеринг JSON-данных для диаграммы Ганта"""
        return jsonify(data)

# Примечание: Эти классы представлений сохранены для обратной совместимости,
# но теперь они не содержат бизнес-логику, которая перенесена в контроллеры.
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.