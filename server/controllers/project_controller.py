from flask import Blueprint
from views.project_view import ProjectListView, ProjectDetailView, ProjectCreateView, ProjectDeleteView

# Создаем Blueprint для маршрутов проектов
project_bp = Blueprint('project', __name__, url_prefix='/project')

# Регистрируем представления
project_bp.add_url_rule('/list', view_func=ProjectListView.as_view('project_list'))
project_bp.add_url_rule('/<int:project_id>', view_func=ProjectDetailView.as_view('project_detail'))
project_bp.add_url_rule('/create', view_func=ProjectCreateView.as_view('create_project'))
project_bp.add_url_rule('/delete/<int:project_id>', view_func=ProjectDeleteView.as_view('delete_project'))