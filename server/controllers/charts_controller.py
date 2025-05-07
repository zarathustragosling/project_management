from flask import Blueprint
from views.charts_view import ChartsView, GanttDataView

# Создаем Blueprint для маршрутов диаграмм
charts_bp = Blueprint('charts', __name__, url_prefix='/charts')

# Регистрируем представления
charts_bp.add_url_rule('/', view_func=ChartsView.as_view('charts'))
charts_bp.add_url_rule('/api/project/<int:project_id>/gantt', view_func=GanttDataView.as_view('get_gantt_data'))
