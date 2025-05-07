from flask import Blueprint
from views.admin_view import AdminPanelView, UserManagementView, TeamManagementView, ProjectManagementView, TaskManagementView, CommentManagementView

# Создаем Blueprint для административных маршрутов
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Регистрируем представления
admin_bp.add_url_rule('/', view_func=AdminPanelView.as_view('system_admin_panel'))

# Маршруты для управления пользователями
admin_bp.add_url_rule('/user/<int:user_id>', view_func=UserManagementView.as_view('user_management'), methods=['GET', 'POST', 'PUT'])

# Маршруты для управления командами
admin_bp.add_url_rule('/team/<int:team_id>', view_func=TeamManagementView.as_view('team_management'), methods=['GET', 'POST'])

# Маршруты для управления проектами
admin_bp.add_url_rule('/project/<int:project_id>', view_func=ProjectManagementView.as_view('project_management'), methods=['GET', 'POST'])

# Маршруты для управления задачами
admin_bp.add_url_rule('/task/<int:task_id>', view_func=TaskManagementView.as_view('task_management'), methods=['GET', 'POST'])

# Маршруты для управления комментариями
admin_bp.add_url_rule('/comment/<int:comment_id>', view_func=CommentManagementView.as_view('comment_management'), methods=['GET', 'POST'])