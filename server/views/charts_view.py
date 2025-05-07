from flask.views import MethodView
from flask import render_template, jsonify, redirect, url_for
from flask_login import current_user
from database import db, Project, Task
from views.base_view import BaseView, LoginRequiredMixin

class ChartsView(LoginRequiredMixin, BaseView):
    """Представление для отображения страницы диаграмм"""
    
    def get(self):
        if not current_user.team_id:
            return redirect(url_for('team.select_team'))
        projects = Project.query.filter_by(team_id=current_user.team_id).all()
        return render_template('charts.html', projects=projects)

class GanttDataView(LoginRequiredMixin, BaseView):
    """Представление для получения данных для диаграммы Ганта"""
    
    def get(self, project_id):
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

        return jsonify(result)