from app import app
from database import db, Role

with app.app_context():
    for name in ["TeamLead", "Участник"]:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name))
    db.session.commit()
    print("✅ Статические роли добавлены")

