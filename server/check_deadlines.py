from flask import Flask
from database import db, Task
from views.notification_view import NotificationService
import os

def create_app():
    """Создает экземпляр приложения Flask для запуска скрипта"""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    
    # Импорт и применение конфигурации
    from controllers.config_controller import configure_app
    configure_app(app)
    
    db.init_app(app)
    return app

def check_deadlines():
    """Проверяет приближающиеся дедлайны и создает уведомления"""
    app = create_app()
    
    with app.app_context():
        # Проверяем задачи с приближающимися дедлайнами
        NotificationService.check_upcoming_deadlines()
        print("Проверка дедлайнов завершена. Уведомления созданы.")

if __name__ == "__main__":
    check_deadlines()