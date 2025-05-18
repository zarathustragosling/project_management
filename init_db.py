from server.app import app
from server.database import db, Role, User
from werkzeug.security import generate_password_hash
import os
from server.app import app

def init_database():
    with app.app_context():
        # Создание всех таблиц
        db.create_all()
        
        # Проверка, существуют ли уже роли
        if Role.query.count() == 0:
            # Создание ролей
            admin_role = Role(name='Администратор')
            manager_role = Role(name='Менеджер')
            developer_role = Role(name='Разработчик')
            
            db.session.add_all([admin_role, manager_role, developer_role])
            db.session.commit()
            
            # Создание администратора по умолчанию
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash(admin_password),
                role=admin_role,
                is_admin=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print('База данных инициализирована. Создан пользователь admin с паролем из переменной окружения ADMIN_PASSWORD')
        else:
            print('База данных уже инициализирована')

if __name__ == '__main__':
    init_database()