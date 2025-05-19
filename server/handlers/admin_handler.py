from flask import redirect, url_for, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from server.database import db, User, Team, Project, Task, Comment, Role, Report, CommentAttachment, Notification, TaskStatus, CommentType, NotificationType
from wtforms import PasswordField, SelectField, validators
import enum

# Базовый класс для всех представлений с проверкой прав администратора
class AdminBaseView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('user_blueprint.login', next=request.url))
        
    # Исправление ошибки с flags
    def scaffold_form(self):
        form_class = super(AdminBaseView, self).scaffold_form()
        return form_class

# Настраиваем главную страницу админки
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('user_blueprint.login'))
        return super(MyAdminIndexView, self).index()

# Представление для пользователей с обработкой паролей
class UserAdminView(AdminBaseView):
    column_exclude_list = ['password_hash']
    form_excluded_columns = ['password_hash', 'notifications', 'comments', 'assigned_tasks', 'created_tasks']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin', 'team_id', 'role_id']
    
    # Добавляем поле для установки пароля
    form_extra_fields = {
        'password': PasswordField('Пароль')
    }
    
    # Добавляем валидаторы для полей, чтобы избежать ошибок
    form_args = {
        'team_id': {
            'validators': []
        },
        'role_id': {
            'validators': []
        }
    }
    
    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)

# Представление для команд
class TeamAdminView(AdminBaseView):
    column_searchable_list = ['name']
    column_filters = ['name']
    form_excluded_columns = ['users', 'projects']
    
    # Добавляем пустые валидаторы для полей
    form_args = {
        'name': {
            'validators': [validators.DataRequired()]
        },
        'avatar_url': {
            'validators': []
        },
        'description': {
            'validators': []
        },
        'invite_code': {
            'validators': [validators.DataRequired()]
        }
    }

# Представление для проектов
class ProjectAdminView(AdminBaseView):
    column_searchable_list = ['name']
    column_filters = ['team_id']
    form_excluded_columns = ['tasks', 'reports']
    
    # Добавляем пустые валидаторы для полей
    form_args = {
        'name': {
            'validators': [validators.DataRequired()]
        },
        'description': {
            'validators': []
        },
        'team_id': {
            'validators': []
        }
    }

# Представление для задач
class TaskAdminView(AdminBaseView):
    column_searchable_list = ['title']
    column_filters = ['status', 'priority', 'project_id', 'assigned_to', 'created_by']
    form_excluded_columns = ['comments']
    
    # Обработка перечисления TaskStatus
    form_overrides = {
        'status': SelectField
    }
    
    def _coerce_task_status(name):
        if name is None:
            return None
        try:
            return getattr(TaskStatus, name)
        except (AttributeError, KeyError):
            return TaskStatus.TO_DO  # Возвращаем значение по умолчанию
    
    form_args = {
        'status': {
            'choices': [(status.name, status.value) for status in list(TaskStatus)],
            'coerce': _coerce_task_status
        },
        'project_id': {
            'validators': [validators.Optional()]
        },
        'assigned_to': {
            'validators': [validators.Optional()]
        },
        'created_by': {
            'validators': [validators.Optional()]
        }
    }
    
    def on_model_change(self, form, model, is_created):
        # Убедимся, что статус задачи корректно установлен
        if isinstance(model.status, str):
            try:
                model.status = getattr(TaskStatus, model.status)
            except (AttributeError, KeyError):
                pass  # Обработка ошибки, если статус не найден

# Представление для комментариев
class CommentAdminView(AdminBaseView):
    column_searchable_list = ['content']
    column_filters = ['task_id', 'user_id', 'type', 'is_solution']
    form_excluded_columns = ['replies', 'attachments']
    
    # Обработка перечисления CommentType
    form_overrides = {
        'type': SelectField
    }
    
    def _coerce_comment_type(name):
        if name is None:
            return None
        try:
            return getattr(CommentType, name)
        except (AttributeError, KeyError):
            return CommentType.COMMENT  # Возвращаем значение по умолчанию
    
    form_args = {
        'type': {
            'choices': [(type_enum.name, type_enum.value) for type_enum in list(CommentType)],
            'coerce': _coerce_comment_type
        },
        'task_id': {
            'validators': [validators.Optional()]
        },
        'user_id': {
            'validators': [validators.Optional()]
        }
    }
    
    def on_model_change(self, form, model, is_created):
        # Убедимся, что тип комментария корректно установлен
        if isinstance(model.type, str):
            try:
                model.type = getattr(CommentType, model.type)
            except (AttributeError, KeyError):
                pass  # Обработка ошибки, если тип не найден

# Представление для ролей
class RoleAdminView(AdminBaseView):
    column_searchable_list = ['name']
    form_excluded_columns = ['users']
    
    # Исправление ошибки с flags
    def scaffold_form(self):
        form_class = super(RoleAdminView, self).scaffold_form()
        return form_class

# Представление для отчетов
class ReportAdminView(AdminBaseView):
    column_searchable_list = ['filename']
    column_filters = ['project_id']
    
    form_args = {
        'project_id': {
            'validators': [validators.DataRequired(message='Необходимо выбрать проект')]
        },
        'filename': {
            'validators': [validators.DataRequired()]
        },
        'filepath': {
            'validators': [validators.DataRequired()]
        }
    }

# Представление для вложений комментариев
class CommentAttachmentAdminView(AdminBaseView):
    column_filters = ['comment_id']
    
    form_args = {
        'comment_id': {
            'validators': [validators.DataRequired(message='Необходимо выбрать комментарий')]
        },
        'filename': {
            'validators': [validators.DataRequired()]
        },
        'filepath': {
            'validators': [validators.DataRequired()]
        }
    }

# Представление для уведомлений
class NotificationAdminView(AdminBaseView):
    column_searchable_list = ['message']
    column_filters = ['user_id', 'type', 'is_read']
    
    # Обработка перечисления NotificationType
    form_overrides = {
        'type': SelectField
    }
    
    def _coerce_notification_type(name):
        if name is None:
            return None
        try:
            return getattr(NotificationType, name)
        except (AttributeError, KeyError):
            return NotificationType.TASK_DEADLINE  # Возвращаем значение по умолчанию
    
    form_args = {
        'type': {
            'choices': [(type_enum.name, type_enum.value) for type_enum in list(NotificationType)],
            'coerce': _coerce_notification_type
        },
        'user_id': {
            'validators': [validators.Optional()]
        },
        'task_id': {
            'validators': [validators.Optional()]
        }
    }
    
    def on_model_change(self, form, model, is_created):
        # Убедимся, что тип уведомления корректно установлен
        if isinstance(model.type, str):
            try:
                model.type = getattr(NotificationType, model.type)
            except (AttributeError, KeyError):
                pass  # Обработка ошибки, если тип не найден

# Функция для инициализации Flask-Admin
def init_admin(app):
    admin = Admin(
        app, 
        name='Панель администратора', 
        template_mode='bootstrap4',
        index_view=MyAdminIndexView(name='Главная')
    )
    
    # Регистрируем модели в админке
    admin.add_view(UserAdminView(User, db.session, name='Пользователи'))
    admin.add_view(TeamAdminView(Team, db.session, name='Команды'))
    admin.add_view(ProjectAdminView(Project, db.session, name='Проекты'))
    admin.add_view(TaskAdminView(Task, db.session, name='Задачи'))
    admin.add_view(CommentAdminView(Comment, db.session, name='Комментарии'))
    admin.add_view(RoleAdminView(Role, db.session, name='Роли'))
    admin.add_view(ReportAdminView(Report, db.session, name='Отчеты'))
    admin.add_view(CommentAttachmentAdminView(CommentAttachment, db.session, name='Вложения'))
    admin.add_view(NotificationAdminView(Notification, db.session, name='Уведомления'))
    
    return admin