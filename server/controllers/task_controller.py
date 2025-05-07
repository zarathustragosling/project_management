from flask import Blueprint
from views.task_view import KanbanView, TaskCreateView, TaskDetailView, TaskEditView, TaskDeleteView, TaskUpdateAPIView, TaskStatusUpdateView, ProjectUsersView

# Создаем Blueprint для маршрутов задач
task_bp = Blueprint('task', __name__, url_prefix='/task')

# Регистрируем представления
task_bp.add_url_rule('/kanban', view_func=KanbanView.as_view('kanban'))
task_bp.add_url_rule('/create', view_func=TaskCreateView.as_view('task_creator'), methods=['GET', 'POST'])
task_bp.add_url_rule('/<int:task_id>', view_func=TaskDetailView.as_view('task_detail'))
task_bp.add_url_rule('/edit/<int:task_id>', view_func=TaskEditView.as_view('edit_task'), methods=['GET', 'POST'])
task_bp.add_url_rule('/delete/<int:task_id>', view_func=TaskDeleteView.as_view('delete_task'), methods=['POST'])
task_bp.add_url_rule('/<int:task_id>/update', view_func=TaskUpdateAPIView.as_view('update_task'), methods=['PATCH'])
task_bp.add_url_rule('/get_project_users/<int:project_id>', view_func=ProjectUsersView.as_view('get_project_users'))
task_bp.add_url_rule('/update_task_status/<int:task_id>', view_func=TaskStatusUpdateView.as_view('update_task_status'), methods=['POST'])

# Маршрут для отладки задач
@task_bp.route('/debug')
def debug():
    tasks = Task.query.all()
    return '<br>'.join(f"{t.id} | {t.title} | {t.status}" for t in tasks)