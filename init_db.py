from server.app import app
from server.database import db, Role, User
from werkzeug.security import generate_password_hash
import os

def init_database():
    with app.app_context():
        db.create_all()

        # Только нужные роли
        desired_roles = ['Администратор', 'TeamLead', 'Постановщик', 'Исполнитель']
        existing_roles = {role.name for role in Role.query.all()}

        # Создание недостающих ролей
        new_roles = []
        for role_name in desired_roles:
            if role_name not in existing_roles:
                new_roles.append(Role(name=role_name))
                print(f"Добавлена роль: {role_name}")

        if new_roles:
            db.session.add_all(new_roles)
            db.session.commit()

        # Создание пользователя admin, если его нет
        if not User.query.filter_by(username='admin').first():
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin_role = Role.query.filter_by(name='Администратор').first()

            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash(admin_password),
                role=admin_role,
                is_admin=True
            )

            db.session.add(admin)
            db.session.commit()
            print("Создан пользователь admin с ролью 'Администратор'")
        else:
            print("Пользователь admin уже существует")

if __name__ == '__main__':
    init_database()
