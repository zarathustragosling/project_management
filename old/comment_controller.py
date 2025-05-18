from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import current_user
from database import db, User, Comment, Task, CommentType, CommentAttachment
from werkzeug.utils import secure_filename
import os, re
from markupsafe import escape
from views.comment_view import AddCommentView, EditCommentView, RenderCommentView, PostFeedCommentView, MarkAsSolutionView, UnmarkAsSolutionView, DeleteCommentView

# Создаем Blueprint для маршрутов комментариев
comment_bp = Blueprint('comment', __name__, url_prefix='/comment')

# Вспомогательная функция для проверки допустимых расширений файлов
def allowed_file(filename):
    from flask import current_app
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Функции контроллера для комментариев
def add_comment(task_id):
    """Добавление комментария к задаче"""
    task = Task.query.get_or_404(task_id)
    if current_user.team_id != task.project.team_id:
        return AddCommentView.render_json_response(success=False, error="Нет доступа к задаче", status_code=403)

    content = request.form.get("content", "").strip()
    parent_id = request.form.get("parent_id")
    attachment = request.files.get("attachment")

    if not content:
        return AddCommentView.render_json_response(success=False, error="Комментарий пуст")

    # Очищаем контент от HTML-тегов
    content = escape(content)

    comment = Comment(
        content=content,
        user_id=current_user.id,
        task_id=task_id,
        parent_id=parent_id if parent_id else None
    )

    # Обработка файла и добавление комментария
    if attachment and attachment.filename and allowed_file(attachment.filename):
        from flask import current_app
        filename = secure_filename(attachment.filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        attachment.save(save_path)

        db.session.add(comment)
        db.session.flush()  # Чтобы получить comment.id

        comment.attachments.append(CommentAttachment(
            filename=filename,
            filepath=f'uploads/{filename}',  # путь относительный от static/
            comment_id=comment.id
        ))
    else:
        db.session.add(comment)

    db.session.commit()

    author = {
        "id": current_user.id,
        "username": current_user.username,
        "avatar": current_user.avatar or url_for('static', filename='default_avatar.png')
    }

    comment_data = {
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at.strftime('%d.%m.%Y %H:%M'),
        "author": author,
        "attachment": attachment.filename if attachment else None,
        "parent_id": comment.parent_id,
        "parent_author": comment.parent.author.username if comment.parent else None
    }
    return AddCommentView.render_json_response(success=True, comment=comment_data)

def edit_comment(comment_id):
    """Редактирование комментария"""
    comment = Comment.query.get_or_404(comment_id)
    
    # Проверка прав доступа - только автор может редактировать
    if comment.user_id != current_user.id:
        return EditCommentView.render_json_response(success=False, error="У вас нет прав на редактирование этого комментария", status_code=403)
    
    content = request.json.get("content", "").strip()
    
    if not content:
        return EditCommentView.render_json_response(success=False, error="Комментарий не может быть пустым")
    
    comment.content = content
    db.session.commit()
    
    comment_data = {
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at.strftime('%d.%m.%Y %H:%M')
    }
    return EditCommentView.render_json_response(success=True, comment=comment_data)

def render_comment(comment_id):
    """Рендеринг HTML комментария"""
    comment = Comment.query.get_or_404(comment_id)
    return RenderCommentView.render(comment=comment, current_user=current_user)

def post_feed_comment():
    """Публикация комментария в ленте"""
    content = request.form.get("content", "").strip()

    if not content:
        flash("Сообщение не может быть пустым", "warning")
        return redirect(url_for("user_blueprint.home"))

    comment = Comment(
        content=content,
        user_id=current_user.id,
        type=CommentType.FEED
    )
    db.session.add(comment)
    db.session.commit()

    return PostFeedCommentView.redirect_after_post()

def mark_as_solution(comment_id):
    """Отметка комментария как решения"""
    comment = Comment.query.get_or_404(comment_id)
    task = comment.task
    
    # Проверка прав доступа - только создатель задачи или тимлид может пометить комментарий как решение
    if current_user.id != task.created_by and not current_user.is_teamlead():
        flash("У вас нет прав для выполнения этого действия", "danger")
        return redirect(url_for("task_blueprint.task_detail", task_id=task.id))
    
    # Сбросить флаг решения для всех комментариев задачи
    for c in task.comments:
        if c.is_solution:
            c.is_solution = False
    
    # Пометить текущий комментарий как решение
    comment.is_solution = True
    db.session.commit()
    
    return MarkAsSolutionView.redirect_after_mark(task.id)

def unmark_as_solution(comment_id):
    """Снятие отметки решения с комментария"""
    comment = Comment.query.get_or_404(comment_id)
    task = comment.task
    
    # Проверка прав доступа - только создатель задачи или тимлид может снять отметку решения
    if current_user.id != task.created_by and not current_user.is_teamlead():
        flash("У вас нет прав для выполнения этого действия", "danger")
        return redirect(url_for("task_blueprint.task_detail", task_id=task.id))
    
    # Снять отметку решения
    comment.is_solution = False
    db.session.commit()
    
    return UnmarkAsSolutionView.redirect_after_unmark(task.id)

def create_comment_attachment(comment_id):
    """Создание вложения для комментария"""
    comment = Comment.query.get_or_404(comment_id)
    
    # Проверка прав доступа - только автор комментария может добавлять вложения
    if comment.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    filename = request.form.get('filename')
    filepath = request.form.get('filepath')
    
    if not filename or not filepath:
        return jsonify({'success': False, 'message': 'Необходимо указать имя файла и путь'}), 400
    
    attachment = CommentAttachment(
        filename=filename,
        filepath=filepath,
        comment_id=comment_id
    )
    
    db.session.add(attachment)
    db.session.commit()
    
    return jsonify({'success': True, 'attachment_id': attachment.id})

def delete_comment(comment_id):
    """Удаление комментария"""
    comment = Comment.query.get_or_404(comment_id)
    
    # Проверка прав доступа - только автор комментария или тимлид может удалить комментарий
    if comment.user_id != current_user.id and not current_user.is_teamlead():
        if comment.task:
            return AddCommentView.render_json_response(success=False, error="У вас нет прав для удаления этого комментария", status_code=403)
        else:
            flash("У вас нет прав для удаления этого комментария", "danger")
            return redirect(url_for("user_blueprint.home"))
    
    # Если у комментария есть задача, запоминаем её ID для редиректа
    task_id = comment.task_id
    
    # Проверяем, является ли комментарий решением задачи
    if comment.is_solution and comment.task:
        # Снимаем отметку решения с задачи
        comment.is_solution = False
    
    # Удаляем сначала все вложения комментария
    for attachment in comment.attachments:
        db.session.delete(attachment)
    
    # Удаляем комментарий
    db.session.delete(comment)
    db.session.commit()
    
    # Если запрос был AJAX, возвращаем JSON-ответ
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True)
    
    # Иначе делаем редирект на страницу задачи или домашнюю страницу
    return DeleteCommentView.redirect_after_delete(task_id)

# Регистрируем маршруты
comment_bp.add_url_rule('/task/<int:task_id>', view_func=add_comment, endpoint='add_comment', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/edit', view_func=edit_comment, endpoint='edit_comment', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/html', view_func=render_comment, endpoint='render_comment')
comment_bp.add_url_rule('/feed', view_func=post_feed_comment, endpoint='post_feed_comment', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/mark-as-solution', view_func=mark_as_solution, endpoint='mark_as_solution', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/unmark-as-solution', view_func=unmark_as_solution, endpoint='unmark_as_solution', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/delete', view_func=delete_comment, endpoint='delete_comment', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/attachment', view_func=create_comment_attachment, endpoint='create_comment_attachment', methods=['POST'])

# Сохраняем классы представлений для обратной совместимости
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.

