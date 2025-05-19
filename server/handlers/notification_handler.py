from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import current_user, login_required
from server.database import db, Notification, User, Team, Task, NotificationType
from datetime import datetime, timedelta

# Создаем Blueprint для маршрутов уведомлений
notification_bp = Blueprint('notification', __name__, url_prefix='/notification')

class NotificationView:
    """Класс представления для уведомлений"""
    
    @staticmethod
    def render_list(notifications):
        """Рендеринг списка уведомлений"""
        return render_template('notifications.html', notifications=notifications)
    
    @staticmethod
    def render_mark_as_read(success, message=None, status_code=200):
        """Рендеринг ответа на отметку уведомления как прочитанного"""
        if message:
            return jsonify({'success': success, 'message': message}), status_code
        return jsonify({'success': success})
    
    @staticmethod
    def render_notification_count(count):
        """Рендеринг количества непрочитанных уведомлений"""
        return jsonify({'count': count})
    
    @staticmethod
    def render_mark_all_as_read(success):
        """Рендеринг ответа на отметку всех уведомлений как прочитанных"""
        return jsonify({'success': success})

class NotificationController:
    """Класс контроллера для уведомлений"""
    
    @staticmethod
    @login_required
    def notification_list():
        """Отображение списка уведомлений"""
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
        return NotificationView.render_list(notifications)

    @staticmethod
    @login_required
    def mark_as_read(notification_id):
        """Отметка уведомления как прочитанного"""
        notification = Notification.query.get_or_404(notification_id)
        
        # Проверяем, что уведомление принадлежит текущему пользователю
        if notification.user_id != current_user.id:
            return NotificationView.render_mark_as_read(False, 'Доступ запрещен', 403)
        
        notification.is_read = True
        db.session.commit()
        
        return NotificationView.render_mark_as_read(True)

    @staticmethod
    def notification_count():
        """Получение количества непрочитанных уведомлений"""
        # Проверяем, авторизован ли пользователь
        if current_user.is_authenticated:
            count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return NotificationView.render_notification_count(count)
        else:
            # Если пользователь не авторизован, возвращаем 0 уведомлений
            return NotificationView.render_notification_count(0)

    @staticmethod
    @login_required
    def mark_all_as_read():
        """Отметка всех уведомлений как прочитанных"""
        notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
        for notification in notifications:
            notification.is_read = True
        db.session.commit()
        return NotificationView.render_mark_all_as_read(True)

class NotificationService:
    """Сервис для создания уведомлений"""
    
    @staticmethod
    def create_task_deadline_notification(task):
        """Создает уведомление о приближающемся дедлайне задачи"""
        if not task.assigned_to:
            return
            
        message = f"Приближается срок выполнения задачи '{task.title}'. Дедлайн: {task.deadline.strftime('%d.%m.%Y')}"
        
        notification = Notification(
            user_id=task.assigned_to,
            type=NotificationType.TASK_DEADLINE,
            message=message,
            task_id=task.id,
            notification_data={
                'project_id': task.project_id,
                'deadline': task.deadline.strftime('%Y-%m-%d')
            }
        )
        
        db.session.add(notification)
        db.session.commit()

    @staticmethod
    def create_task_assigned_notification(task):
        """Создает уведомление о назначении ответственным за задачу"""
        if not task.assigned_to:
            return
            
        message = f"Вы назначены ответственным за задачу '{task.title}'"
        
        notification = Notification(
            user_id=task.assigned_to,
            type=NotificationType.TASK_ASSIGNED,
            message=message,
            task_id=task.id,
            notification_data={
                'project_id': task.project_id
            }
        )
        
        db.session.add(notification)
        db.session.commit()

    @staticmethod
    def create_team_member_joined_notification(user, team):
        """Создает уведомление о присоединении нового участника к команде"""
        # Получаем всех участников команды, кроме нового участника
        team_members = User.query.filter(User.team_id == team.id, User.id != user.id).all()
        
        message = f"Пользователь {user.username} присоединился к команде"
        
        for member in team_members:
            notification = Notification(
                user_id=member.id,
                type=NotificationType.TEAM_MEMBER_JOINED,
                message=message,
                notification_data={
                    'team_id': team.id,
                    'user_id': user.id,
                    'username': user.username
                }
            )
            db.session.add(notification)
        
        db.session.commit()

    @staticmethod
    def create_team_member_left_notification(user, team):
        """Создает уведомление о выходе участника из команды"""
        # Получаем всех участников команды, кроме уходящего участника
        team_members = User.query.filter(User.team_id == team.id, User.id != user.id).all()
        
        message = f"Пользователь {user.username} покинул команду"
        
        for member in team_members:
            notification = Notification(
                user_id=member.id,
                type=NotificationType.TEAM_MEMBER_LEFT,
                message=message,
                notification_data={
                    'team_id': team.id,
                    'user_id': user.id,
                    'username': user.username
                }
            )
            db.session.add(notification)
        
        db.session.commit()

    @staticmethod
    def check_upcoming_deadlines():
        """Проверяет приближающиеся дедлайны и создает уведомления"""
        # Получаем текущую дату
        today = datetime.utcnow().date()
        # Получаем дату через 3 дня
        three_days_later = today + timedelta(days=3)
        
        # Получаем все задачи с дедлайном через 3 дня, у которых есть ответственный
        tasks = Task.query.filter(
            Task.deadline == three_days_later,
            Task.assigned_to.isnot(None),
            Task.status != TaskStatus.DONE
        ).all()
        
        # Создаем уведомления для каждой задачи
        for task in tasks:
            NotificationService.create_task_deadline_notification(task)

# Регистрируем маршруты
notification_bp.add_url_rule('/', view_func=NotificationController.notification_list, endpoint='notifications')
notification_bp.add_url_rule('/<int:notification_id>/read', view_func=NotificationController.mark_as_read, endpoint='mark_as_read', methods=['POST'])
notification_bp.add_url_rule('/count', view_func=NotificationController.notification_count, endpoint='notification_count')
notification_bp.add_url_rule('/mark-all-read', view_func=NotificationController.mark_all_as_read, endpoint='mark_all_as_read', methods=['POST'])