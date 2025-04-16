import enum 
from sqlalchemy import Enum as PgEnum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    users = db.relationship('User', backref='team', lazy=True)
    projects = db.relationship('Project', back_populates='team', lazy=True)  # Use back_populates
    avatar_url = db.Column(db.String(300), nullable=True)  # URL к изображению
    description = db.Column(db.Text, nullable=True)        # Описание


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    avatar = db.Column(db.String(200), nullable=True)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    tasks = db.relationship('Task', back_populates='project', lazy=True)  # Use back_populates
    reports = db.relationship('Report', back_populates='project', lazy=True)  # Use back_populates

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)  # Corrected indentation

    # Отношение к команде
    team = db.relationship('Team', back_populates='projects')  # Matches back_populates in Team

class TaskStatus(enum.Enum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), nullable=False, default='Средний')
    status = db.Column(PgEnum(TaskStatus, name='taskstatus'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    deadline = db.Column(db.Date)
    comments = db.relationship('Comment', back_populates='task', lazy='joined')
    project = db.relationship('Project', back_populates='tasks')  # Matches back_populates in Project
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)  # Имя файла
    filepath = db.Column(db.String(200), nullable=False)  # Путь к файлу
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project = db.relationship('Project', back_populates='reports')  # Matches back_populates in Project


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    task = db.relationship('Task', back_populates='comments')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    
    
    author = db.relationship('User', backref='comments')
    replies = db.relationship(
    'Comment',
    backref=db.backref('parent', remote_side=[id]),
    lazy='joined'  # ✅ теперь можно eager-load
)

    attachments = db.relationship('CommentAttachment', 
                                backref='comment', 
                                lazy=True)

    
class CommentAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)


