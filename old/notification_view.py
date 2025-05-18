from flask import render_template, redirect, url_for, jsonify, request
from flask_login import current_user, login_required
from database import db, Notification, User, Team, Task, NotificationType
from datetime import datetime, timedelta
from .base_view import BaseView, LoginRequiredMixin

class NotificationListView(BaseView, LoginRequiredMixin):
    """Представление для списка уведомлений"""
    
    def get(self):
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        from controllers.notification_controller import notification_list
        return notification_list()

class NotificationMarkAsReadView(BaseView, LoginRequiredMixin):
    """Представление для отметки уведомления как прочитанного"""
    
    def post(self, notification_id):
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        from controllers.notification_controller import mark_as_read
        return mark_as_read(notification_id)

class NotificationCountView(BaseView, LoginRequiredMixin):
    """Представление для получения количества непрочитанных уведомлений"""
    
    def get(self):
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        from controllers.notification_controller import notification_count
        return notification_count()

class NotificationMarkAllAsReadView(BaseView, LoginRequiredMixin):
    """Представление для отметки всех уведомлений как прочитанных"""
    
    def post(self):
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        from controllers.notification_controller import mark_all_as_read
        return mark_all_as_read()

class NotificationService:
    """Сервис для создания уведомлений"""
    
    @staticmethod
    def create_task_deadline_notification(task):
        """Создает уведомление о приближающемся дедлайне задачи"""
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        from controllers.notification_controller import create_task_deadline_notification
        return create_task_deadline_notification(task)
    
    @staticmethod
    def create_task_assigned_notification(task):
        """Создает уведомление о назначении ответственным за задачу"""
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        from controllers.notification_controller import create_task_assigned_notification
        return create_task_assigned_notification(task)
    
    @staticmethod
    def create_team_member_joined_notification(user, team):
        """Создает уведомление о присоединении нового участника к команде"""
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        from controllers.notification_controller import create_team_member_joined_notification
        return create_team_member_joined_notification(user, team)
    
    @staticmethod
    def create_team_member_left_notification(user, team):
        """Создает уведомление о выходе участника из команды"""
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        from controllers.notification_controller import create_team_member_left_notification
        return create_team_member_left_notification(user, team)
    
    @staticmethod
    def check_upcoming_deadlines():
        """Проверяет приближающиеся дедлайны и создает уведомления"""
        # Вся бизнес-логика перенесена в контроллер notification_controller.py
        from controllers.notification_controller import check_upcoming_deadlines
        return check_upcoming_deadlines()

# Примечание: Эти классы представлений сохранены для обратной совместимости,
# но теперь они не содержат бизнес-логику, которая перенесена в контроллеры.
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.