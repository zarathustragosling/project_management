from flask import Blueprint
from views.comment_view import AddCommentView, EditCommentView, RenderCommentView, PostFeedCommentView, MarkAsSolutionView, UnmarkAsSolutionView

# Создаем Blueprint для маршрутов комментариев
comment_bp = Blueprint('comment', __name__, url_prefix='/comment')

# Регистрируем представления
comment_bp.add_url_rule('/task/<int:task_id>', view_func=AddCommentView.as_view('add_comment'), methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/edit', view_func=EditCommentView.as_view('edit_comment'), methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/html', view_func=RenderCommentView.as_view('render_comment'))
comment_bp.add_url_rule('/feed', view_func=PostFeedCommentView.as_view('post_feed_comment'), methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/mark-as-solution', view_func=MarkAsSolutionView.as_view('mark_as_solution'), methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/unmark-as-solution', view_func=UnmarkAsSolutionView.as_view('unmark_as_solution'), methods=['POST'])

