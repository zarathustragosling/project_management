from flask import Blueprint
from views.team_view import TeamDetailView, TeamCreateView, TeamEditView, TeamSelectView, TeamLeaveView, TeamInviteCodeView, TeamJoinView, TeamMemberManagementView, TeamMemberRemoveView

# Создаем Blueprint для маршрутов команд
team_bp = Blueprint('team', __name__, url_prefix='/team')

# Регистрируем представления
team_bp.add_url_rule('/<int:team_id>', view_func=TeamDetailView.as_view('team_detail'))
team_bp.add_url_rule('/create', view_func=TeamCreateView.as_view('create_team'), methods=['GET', 'POST'])
team_bp.add_url_rule('/edit', view_func=TeamEditView.as_view('edit_team'), methods=['GET', 'POST'])
team_bp.add_url_rule('/select', view_func=TeamSelectView.as_view('select_team'), methods=['GET', 'POST'])
team_bp.add_url_rule('/leave', view_func=TeamLeaveView.as_view('leave_team'), methods=['POST'])
team_bp.add_url_rule('/refresh_invite_code', view_func=TeamInviteCodeView.as_view('refresh_invite_code'), methods=['POST'])
team_bp.add_url_rule('/join', view_func=TeamJoinView.as_view('join_team'), methods=['GET', 'POST'])
team_bp.add_url_rule('/<int:team_id>/add_member', view_func=TeamMemberManagementView.as_view('add_member'), methods=['POST'])
team_bp.add_url_rule('/remove_member/<int:team_id>/<int:user_id>', view_func=TeamMemberRemoveView.as_view('remove_member'), methods=['GET'])