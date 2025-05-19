from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import current_user
from server.database import db, User, Comment, Task, CommentType, CommentAttachment
from werkzeug.utils import secure_filename
import os, re
from markupsafe import escape
from flask.views import MethodView
from server.utils.base_view import BaseView, LoginRequiredMixin

# Создаем Blueprint для маршрутов комментариев
comment_bp = Blueprint('comment', __name__, url_prefix='/comment')

class CommentView:
    """Класс представления для комментариев"""
    
    @staticmethod
    def render_json_response(success, comment=None, error=None, status_code=200):
        """Рендеринг JSON-ответа для добавления/редактирования комментария"""
        if success:
            return jsonify(success=True, comment=comment)
        else:
            return jsonify(success=False, error=error), status_code
    
    @staticmethod
    def render_comment_html(comment, current_user):
        """Рендеринг HTML комментария"""
        return render_template("_comment_block.html", comment=comment, current_user=current_user)
    
    @staticmethod
    def redirect_after_feed_post():
        """Перенаправление после публикации комментария в ленте"""
        flash("Сообщение отправлено", "success")
        return redirect(url_for("user_blueprint.home"))
    
    @staticmethod
    def redirect_after_mark_solution(task_id):
        """Перенаправление после отметки комментария как решения"""
        flash("Комментарий помечен как решение задачи", "success")
        return redirect(url_for("task_blueprint.task_detail", task_id=task_id))
    
    @staticmethod
    def redirect_after_unmark_solution(task_id):
        """Перенаправление после снятия отметки решения с комментария"""
        flash("Отметка решения снята с комментария", "success")
        return redirect(url_for("task_blueprint.task_detail", task_id=task_id))
    
    @staticmethod
    def redirect_after_delete(task_id):
        """Перенаправление после удаления комментария"""
        if task_id:
            flash("Комментарий удален", "success")
            return redirect(url_for("task_blueprint.task_detail", task_id=task_id))
        else:
            flash("Комментарий удален", "success")
            return redirect(url_for("user_blueprint.home"))

class CommentController:
    """Класс контроллера для комментариев"""
    
    # Вспомогательная функция для проверки допустимых расширений файлов
    @staticmethod
    def allowed_file(filename):
        from flask import current_app
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    @staticmethod
    def add_comment(task_id):
        """Добавление комментария к задаче"""
        task = Task.query.get_or_404(task_id)
        if current_user.team_id != task.project.team_id:
            return CommentView.render_json_response(success=False, error="Нет доступа к задаче", status_code=403)

        content = request.form.get("content", "").strip()
        parent_id = request.form.get("parent_id")
        attachment = request.files.get("attachment")

        if not content:
            return CommentView.render_json_response(success=False, error="Комментарий пуст")

        # Очищаем контент от HTML-тегов
        content = escape(content)

        comment = Comment(
            content=content,
            user_id=current_user.id,
            task_id=task_id,
            parent_id=parent_id if parent_id else None
        )

        # Обработка файла и добавление комментария
        if attachment and attachment.filename and CommentController.allowed_file(attachment.filename):
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
        return CommentView.render_json_response(success=True, comment=comment_data)

    @staticmethod
    def edit_comment(comment_id):
        """Редактирование комментария"""
        comment = Comment.query.get_or_404(comment_id)
        
        # Проверка прав доступа - только автор может редактировать
        if comment.user_id != current_user.id:
            return CommentView.render_json_response(success=False, error="У вас нет прав на редактирование этого комментария", status_code=403)
        
        content = request.json.get("content", "").strip()
        
        if not content:
            return CommentView.render_json_response(success=False, error="Комментарий не может быть пустым")
        
        comment.content = content
        db.session.commit()
        
        comment_data = {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.strftime('%d.%m.%Y %H:%M')
        }
        return CommentView.render_json_response(success=True, comment=comment_data)

    @staticmethod
    def render_comment(comment_id):
        """Рендеринг HTML комментария"""
        comment = Comment.query.get_or_404(comment_id)
        return CommentView.render_comment_html(comment=comment, current_user=current_user)

    @staticmethod
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

        return CommentView.redirect_after_feed_post()

    @staticmethod
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
        
        return CommentView.redirect_after_mark_solution(task.id)

    @staticmethod
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
        
        return CommentView.redirect_after_unmark_solution(task.id)

    @staticmethod
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

    @staticmethod
    def delete_comment(comment_id):
        """Удаление комментария"""
        comment = Comment.query.get_or_404(comment_id)
        
        # Проверка прав доступа - только автор комментария или тимлид может удалить комментарий
        if comment.user_id != current_user.id and not current_user.is_teamlead():
            if comment.task:
                return CommentView.render_json_response(success=False, error="У вас нет прав для удаления этого комментария", status_code=403)
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
        return CommentView.redirect_after_delete(task_id)

# Регистрируем маршруты
comment_bp.add_url_rule('/task/<int:task_id>', view_func=CommentController.add_comment, endpoint='add_comment', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/edit', view_func=CommentController.edit_comment, endpoint='edit_comment', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/html', view_func=CommentController.render_comment, endpoint='render_comment')
comment_bp.add_url_rule('/feed', view_func=CommentController.post_feed_comment, endpoint='post_feed_comment', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/mark-as-solution', view_func=CommentController.mark_as_solution, endpoint='mark_as_solution', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/unmark-as-solution', view_func=CommentController.unmark_as_solution, endpoint='unmark_as_solution', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/delete', view_func=CommentController.delete_comment, endpoint='delete_comment', methods=['POST'])
comment_bp.add_url_rule('/<int:comment_id>/attachment', view_func=CommentController.create_comment_attachment, endpoint='create_comment_attachment', methods=['POST'])