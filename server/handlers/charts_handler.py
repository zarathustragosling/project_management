from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import current_user
from server.database import db, Project, Task

# Создаем Blueprint для маршрутов диаграмм
charts_bp = Blueprint('charts', __name__, url_prefix='/charts')

class ChartsView:
    """Класс представления для диаграмм"""
    
    @staticmethod
    def render(projects=None):
        """Рендеринг страницы диаграмм"""
        return render_template('charts.html', projects=projects)
    
    @staticmethod
    def render_json(data):
        """Рендеринг JSON-данных для диаграммы Ганта"""
        return jsonify(data)

class ChartsController:
    """Класс контроллера для диаграмм"""
    
    @staticmethod
    def charts_page():
        """Отображение страницы диаграмм"""
        if not current_user.team_id:
            return redirect(url_for('team_blueprint.select_team'))
        projects = Project.query.filter_by(team_id=current_user.team_id).all()
        return ChartsView.render(projects=projects)

    @staticmethod
    def get_gantt_data(project_id):
        """Получение данных для диаграммы Ганта"""
        project = Project.query.get_or_404(project_id)
        if project.team_id != current_user.team_id:
            return jsonify({'error': 'Доступ запрещен'}), 403

        tasks = Task.query.filter_by(project_id=project.id).all()
        result = []

        for task in tasks:
            start_date = task.created_at.strftime('%Y-%m-%d') if task.created_at else '2024-01-01'
            end_date = task.deadline.strftime('%Y-%m-%d') if task.deadline else start_date

            result.append({
                'id': task.id,
                'name': task.title,
                'start': start_date,
                'end': end_date,
                'priority': task.priority or 'Средний',
                'description': task.description
            })

        return ChartsView.render_json(result)

# Регистрируем маршруты
charts_bp.add_url_rule('/', view_func=ChartsController.charts_page, endpoint='charts')
charts_bp.add_url_rule('/api/project/<int:project_id>/gantt', view_func=ChartsController.get_gantt_data, endpoint='get_gantt_data')