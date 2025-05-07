from flask.views import MethodView
from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import current_user
from database import db, User, Comment, Task, CommentType, CommentAttachment
from werkzeug.utils import secure_filename
import os, re
from markupsafe import escape
from views.base_view import BaseView, LoginRequiredMixin

# Вспомогательная функция для проверки допустимых расширений файлов
def allowed_file(filename):
    from flask import current_app
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

class AddCommentView(LoginRequiredMixin, BaseView):
    """Представление для добавления комментария к задаче"""
    
    def post(self, task_id):
        task = Task.query.get_or_404(task_id)
        if current_user.team_id != task.project.team_id:
            return jsonify(success=False, error="Нет доступа к задаче"), 403

        content = request.form.get("content", "").strip()
        parent_id = request.form.get("parent_id")
        attachment = request.files.get("attachment")

        if not content:
            return jsonify(success=False, error="Комментарий пуст")

        # Поиск упомянутого <@user_id:username> для подсветки
        def format_mentions(content):
            pattern = r'<@(\d+):([^>]+)>'
            matches = re.finditer(pattern, content)
            formatted_content = content
            for match in matches:
                user_id, username = match.groups()
                formatted_content = formatted_content.replace(
                    match.group(0),
                    f'<a href="{url_for("user.view_profile", user_id=user_id)}" class="text-blue-400 hover:underline">@{username}</a>'
                )
            return formatted_content

        content = format_mentions(content)
        match = re.search(r'<@(\d+):([^>]+)>', content)
        if match:
            parent_id = parent_id or match.group(1)

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

        return jsonify(success=True, comment={
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.strftime('%d.%m.%Y %H:%M'),
            "author": author,
            "attachment": attachment.filename if attachment else None,
            "parent_id": comment.parent_id,
            "parent_author": comment.parent.author.username if comment.parent else None
        })

class EditCommentView(LoginRequiredMixin, BaseView):
    """Представление для редактирования комментария"""
    
    def post(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        
        # Проверка прав доступа - только автор может редактировать
        if comment.user_id != current_user.id:
            return jsonify(success=False, error="У вас нет прав на редактирование этого комментария"), 403
        
        content = request.json.get("content", "").strip()
        
        if not content:
            return jsonify(success=False, error="Комментарий не может быть пустым")
        
        comment.content = content
        db.session.commit()
        
        return jsonify(success=True, comment={
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.strftime('%d.%m.%Y %H:%M')
        })

class RenderCommentView(BaseView):
    """Представление для рендеринга HTML комментария"""
    
    def get(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        return render_template("_comment_block.html", comment=comment, current_user=current_user)

class PostFeedCommentView(LoginRequiredMixin, BaseView):
    """Представление для публикации комментария в ленте"""
    
    def post(self):
        content = request.form.get("content", "").strip()

        if not content:
            flash("Сообщение не может быть пустым", "warning")
            return redirect(url_for("user.home"))

        comment = Comment(
            content=content,
            user_id=current_user.id,
            type=CommentType.FEED
        )
        db.session.add(comment)
        db.session.commit()

        flash("Сообщение отправлено", "success")
        return redirect(url_for("user.home"))

class MarkAsSolutionView(LoginRequiredMixin, BaseView):
    """Представление для отметки комментария как решения"""
    
    def post(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        task = comment.task
        
        # Проверка прав доступа - только создатель задачи или тимлид может пометить комментарий как решение
        if current_user.id != task.created_by and not current_user.is_teamlead():
            flash("У вас нет прав для выполнения этого действия", "danger")
            return redirect(url_for("task.task_detail", task_id=task.id))
        
        # Сбросить флаг решения для всех комментариев задачи
        for c in task.comments:
            if c.is_solution:
                c.is_solution = False
        
        # Пометить текущий комментарий как решение
        comment.is_solution = True
        db.session.commit()
        
        flash("Комментарий помечен как решение задачи", "success")
        return redirect(url_for("task.task_detail", task_id=task.id))

class UnmarkAsSolutionView(LoginRequiredMixin, BaseView):
    """Представление для снятия отметки решения с комментария"""
    
    def post(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        task = comment.task
        
        # Проверка прав доступа - только создатель задачи или тимлид может снять отметку решения
        if current_user.id != task.created_by and not current_user.is_teamlead():
            flash("У вас нет прав для выполнения этого действия", "danger")
            return redirect(url_for("task.task_detail", task_id=task.id))
        
        # Снять отметку решения
        comment.is_solution = False
        db.session.commit()
        
        flash("Отметка решения снята с комментария", "success")
        return redirect(url_for("task.task_detail", task_id=task.id))