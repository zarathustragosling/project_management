from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import current_user, login_required
from database import db, Notification, User, Team, Task, NotificationType
from datetime import datetime, timedelta
from views.notification_view import NotificationService

# Создаем Blueprint для маршрутов уведомлений
notification_bp = Blueprint('notification', __name__, url_prefix='/notification')

# Функции контроллера для уведомлений
@login_required
def notification_list():
    """Отображение списка уведомлений"""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)

@login_required
def mark_as_read(notification_id):
    """Отметка уведомления как прочитанного"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Проверяем, что уведомление принадлежит текущему пользователю
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

def notification_count():
    """Получение количества непрочитанных уведомлений"""
    # Проверяем, авторизован ли пользователь
    if current_user.is_authenticated:
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return jsonify({'count': count})
    else:
        # Если пользователь не авторизован, возвращаем 0 уведомлений
        return jsonify({'count': 0})

@login_required
def mark_all_as_read():
    """Отметка всех уведомлений как прочитанных"""
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

# Сервисные функции для создания уведомлений
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
                'user_id': user.id
            }
        )
        
        db.session.add(notification)
    
    db.session.commit()

def create_team_member_left_notification(user, team):
    """Создает уведомление о выходе участника из команды"""
    # Получаем всех оставшихся участников команды
    team_members = User.query.filter_by(team_id=team.id).all()
    
    message = f"Пользователь {user.username} покинул команду"
    
    for member in team_members:
        notification = Notification(
            user_id=member.id,
            type=NotificationType.TEAM_MEMBER_LEFT,
            message=message,
            notification_data={
                'team_id': team.id,
                'user_id': user.id
            }
        )
        
        db.session.add(notification)
    
    db.session.commit()

def check_upcoming_deadlines():
    """Проверяет приближающиеся дедлайны и создает уведомления"""
    tomorrow = datetime.now().date() + timedelta(days=1)
    
    # Находим задачи с дедлайном завтра
    tasks_with_deadline = Task.query.filter(
        Task.deadline == tomorrow,
        Task.assigned_to.isnot(None)
    ).all()
    
    for task in tasks_with_deadline:
        # Проверяем, не было ли уже создано уведомление для этой задачи
        existing_notification = Notification.query.filter(
            Notification.task_id == task.id,
            Notification.type == NotificationType.TASK_DEADLINE,
            Notification.user_id == task.assigned_to
        ).first()
        
        if not existing_notification:
            create_task_deadline_notification(task)

# Регистрируем маршруты
notification_bp.add_url_rule('/', view_func=notification_list, endpoint='notification_list')
notification_bp.add_url_rule('/mark_as_read/<int:notification_id>', view_func=mark_as_read, endpoint='mark_as_read', methods=['POST'])
notification_bp.add_url_rule('/count', view_func=notification_count, endpoint='notification_count')
notification_bp.add_url_rule('/mark_all_as_read', view_func=mark_all_as_read, endpoint='mark_all_as_read', methods=['POST'])

# Сохраняем классы представлений для обратной совместимости
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.