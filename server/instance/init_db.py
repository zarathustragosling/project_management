from app import app, db
from database import Role, User, Team, Project, Task

def init_db():
    """Инициализация базы данных и создание необходимых ролей"""
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        
        # Проверяем, существуют ли уже роли
        if Role.query.count() == 0:
            # Создаем роли
            admin_role = Role(name="Admin")
            teamlead_role = Role(name="TeamLead")
            creator_role = Role(name="Постановщик")
            executor_role = Role(name="Исполнитель")
            
            # Добавляем роли в сессию
            db.session.add(admin_role)
            db.session.add(teamlead_role)
            db.session.add(creator_role)
            db.session.add(executor_role)
            
            # Сохраняем изменения
            db.session.commit()
            print("Роли успешно созданы")
        else:
            # Проверяем наличие новых ролей и создаем их при необходимости
            roles = ["Admin", "TeamLead", "Постановщик", "Исполнитель"]
            existing_roles = [role.name for role in Role.query.all()]
            
            for role_name in roles:
                if role_name not in existing_roles:
                    new_role = Role(name=role_name)
                    db.session.add(new_role)
                    print(f"Создана новая роль: {role_name}")
            
            # Если была роль "Участник", удаляем ее
            member_role = Role.query.filter_by(name="Участник").first()
            if member_role:
                # Переназначаем пользователей с ролью "Участник" на роль "Исполнитель"
                executor_role = Role.query.filter_by(name="Исполнитель").first()
                for user in User.query.filter_by(role_id=member_role.id).all():
                    user.role_id = executor_role.id
                
                # Удаляем роль "Участник"
                db.session.delete(member_role)
                print("Роль 'Участник' удалена, пользователи переназначены на роль 'Исполнитель'")
            
            db.session.commit()

if __name__ == "__main__":
    init_db()