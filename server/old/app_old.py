from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database import db, User, Role, Project, Task, Report, Team, TaskStatus, Comment, CommentType
import os, random, string, re, sqlite3, secrets
from werkzeug.utils import secure_filename
from datetime import datetime, date
from markupsafe import Markup, escape
from markdown import markdown
from sqlalchemy import event
from sqlalchemy.engine import Engine
from functools import wraps

# Инициализация приложения
app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../project_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'





# Настройка папки для загрузки файлов
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


AVATAR_FOLDER = os.path.join(app.static_folder, 'avatars')
if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER)


# Создание папки для загрузки файлов, если она не существует
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# Проверка допустимых расширений файлов
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def teamlead_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teamlead():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))





@app.template_filter('highlight_mentions')
def highlight_mentions(text):
    def replace(match):
        user_id = match.group(1)
        username = match.group(2)
        return f'<a href="/user/{user_id}" class="mention text-blue-400 hover:underline">@{escape(username)}</a>'

    pattern = r'<@(\d+):([\wа-яА-ЯёЁ\s.-]+)>'
    return Markup(re.sub(pattern, replace, text))




def process_mentions(content):
    """Заменяет @username на ссылку на профиль"""
    pattern = r'@([\w\.-]+)'  # допускает email или username

    def repl(match):
        username = match.group(1)
        user = User.query.filter_by(username=username).first()
        if user:
            return f'<a href="{url_for("user_profile", user_id=user.id)}" class="mention text-blue-400 hover:underline">@{escape(username)}</a>'
        return escape(match.group(0))  # если не найден

    return Markup(re.sub(pattern, repl, content))



@app.route('/admin')
@login_required
def system_admin_panel():
    if not current_user.is_admin:
        abort(403)

    users = User.query.all()
    teams = Team.query.all()
    projects = Project.query.all()
    tasks = Task.query.all()
    comments = Comment.query.all()

    return render_template('system_admin_panel.html',
                           users=users,
                           teams=teams,
                           projects=projects,
                           tasks=tasks,
                           comments=comments)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Пользователь удалён", "success")
    return redirect(url_for('system_admin_panel'))


@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        db.session.commit()
        flash("Пользователь обновлён", "success")
        return redirect(url_for('system_admin_panel'))

    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/team/<int:team_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_team(team_id):
    if not current_user.is_admin:
        abort(403)

    team = Team.query.get_or_404(team_id)

    if request.method == 'POST':
        team.name = request.form.get('name')
        team.description = request.form.get('description')
        team.avatar_url = request.form.get('avatar_url')
        db.session.commit()
        flash("Команда обновлена", "success")
        return redirect(url_for('system_admin_panel'))

    return render_template('admin/edit_team_admin.html', team=team)

@app.route('/admin/team/<int:team_id>/delete', methods=['POST'])
@login_required
def admin_delete_team(team_id):
    if not current_user.is_admin:
        abort(403)

    team = Team.query.get_or_404(team_id)

    # Обнуляем team_id у участников
    for user in team.users:
        user.team_id = None

    db.session.delete(team)
    db.session.commit()
    flash("Команда удалена", "info")
    return redirect(url_for('system_admin_panel'))

@app.route('/admin/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_project(project_id):
    if not current_user.is_admin:
        abort(403)

    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        db.session.commit()
        flash("Проект обновлён", "success")
        return redirect(url_for('system_admin_panel'))

    return render_template('admin/edit_project_admin.html', project=project)

@app.route('/admin/project/<int:project_id>/delete', methods=['POST'])
@login_required
def admin_delete_project(project_id):
    if not current_user.is_admin:
        abort(403)

    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash("Проект удалён", "info")
    return redirect(url_for('system_admin_panel'))


@app.route('/admin/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_task(task_id):
    if not current_user.is_admin:
        abort(403)

    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        db.session.commit()
        flash("Задача обновлена", "success")
        return redirect(url_for('system_admin_panel'))

    return render_template('admin/edit_task_admin.html', task=task)

@app.route('/admin/task/<int:task_id>/delete', methods=['POST'])
@login_required
def admin_delete_task(task_id):
    if not current_user.is_admin:
        abort(403)

    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Задача удалена", "info")
    return redirect(url_for('system_admin_panel'))


@app.route('/admin/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_comment(comment_id):
    if not current_user.is_admin:
        abort(403)

    comment = Comment.query.get_or_404(comment_id)

    if request.method == 'POST':
        comment.content = request.form.get('content')
        db.session.commit()
        flash("Комментарий обновлён", "success")
        return redirect(url_for('system_admin_panel'))

    return render_template('admin/edit_comment_admin.html', comment=comment)

@app.route('/admin/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def admin_delete_comment(comment_id):
    if not current_user.is_admin:
        abort(403)

    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Комментарий удалён", "info")
    return redirect(url_for('system_admin_panel'))



@app.route('/profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        file = request.files.get('avatar')
        role = request.form.get('role')
        description = request.form.get('description')

        if username:
            current_user.username = username
        if role:
            current_user.role = role
        if description:
            current_user.description = description
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            current_user.avatar = f"/static/uploads/{filename}"

        db.session.commit()
        flash("Профиль обновлен!", "success")
        return redirect(url_for('update_profile'))

    return render_template('profile.html')

@app.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)



@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    if not current_user.check_password(old_password):
        flash("Старый пароль неверный", "danger")
        return redirect(url_for('update_profile'))

    current_user.set_password(new_password)
    db.session.commit()
    flash("Пароль изменен", "success")
    return redirect(url_for('update_profile'))




# Маршрут для выбора команды
@app.route('/select_team', methods=['GET', 'POST'])
@login_required
def select_team():
    if request.method == 'POST':
        team_id = request.form['team_id']
        current_user.team_id = team_id
        db.session.commit()
        flash('Команда успешно выбрана!', 'success')
        return redirect(url_for('home'))
    teams = Team.query.all()
    return render_template('select_team.html', teams=teams)


@app.route('/task/<int:task_id>/update', methods=['PATCH'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.created_by != current_user.id:
        return jsonify({'success': False, 'error': 'Нет прав'}), 403

    data = request.get_json()

    try:
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.priority = data.get('priority', task.priority)
        task.status = TaskStatus(data.get('status', task.status.name))

        project_id = data.get('project_id')
        if project_id:
            task.project_id = int(project_id)

        assigned_to = data.get('assigned_to')
        task.assigned_to = int(assigned_to) if assigned_to else None

        deadline = data.get('deadline')
        if deadline:
            task.deadline = datetime.fromisoformat(deadline)

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400




@app.route('/update_task_status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    new_status = data.get('status', '').strip().upper().replace(" ", "_")
    try:
        task.status = TaskStatus[new_status]
        db.session.commit()
        return jsonify({'success': True, 'new_status': task.status.value})
    except KeyError:
        return jsonify({'success': False, 'error': f'Invalid status: {new_status}'}), 400



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        team_id = request.form.get('team_id')

        if not username or not email or not password:
            flash("Все поля обязательны!", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Пользователь с таким email уже зарегистрирован!", "warning")
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, team_id=team_id)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Регистрация успешна! Войдите в систему.", "success")
        return redirect(url_for('login'))

    teams = Team.query.all()
    return render_template('register.html', teams=teams)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Ошибка входа! Проверьте данные.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user, team=current_user.team)

@app.route("/user/<int:user_id>")
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("profile.html", user=user)


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if request.method == 'POST':
        # Генерация уникального имени и email
        username = f"test_user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=5))}"
        email = f"{username}@example.com"

        # Проверка, что сгенерированные имя и email уникальны
        while User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            username = f"test_user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=5))}"
            email = f"{username}@example.com"

        # Создание нового пользователя
        new_user = User(username=username, email=email)
        new_user.set_password("test123")  # Установка пароля
        db.session.add(new_user)
        db.session.commit()

        flash(f"Тестовый пользователь {username} создан!", "success")

    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/task/<int:task_id>')
@login_required
def task_detail(task_id):
    task = Task.query.options(
        db.joinedload(Task.comments)
          .joinedload(Comment.author),
        db.joinedload(Task.comments)
          .joinedload(Comment.attachments),
        db.joinedload(Task.comments)
          .joinedload(Comment.replies)
    ).get_or_404(task_id)
    
    return render_template(
        'task_detail.html',
        task=task,
        projects=Project.query.all(),
        users=User.query.all()
    )

@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    if not current_user.team_id:
        return redirect(url_for('edit_team'))
    if request.method == 'POST':
        project_id = request.form['project_id']
        file = request.files['report_file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            new_report = Report(filename=filename, filepath=filepath, project_id=project_id)
            db.session.add(new_report)
            db.session.commit()

            flash('Отчет успешно загружен!', 'success')
        else:
            flash('Недопустимый формат файла!', 'danger')

    projects = Project.query.all()
    return render_template('reports.html', projects=projects)

@app.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], report.filename)

@app.route('/charts')
@login_required
def charts():
    if not current_user.team_id:
        return redirect(url_for('edit_team'))
    projects = Project.query.filter_by(team_id=current_user.team_id).all()
    return render_template('charts.html', projects=projects)



@app.route('/')
def home():
    if not current_user.is_authenticated:
        return render_template('index.html')

    if not current_user.team:
        return redirect(url_for('select_team'))

    elif not current_user.team.name:
        return redirect(url_for('edit_team'))    # Настройка уже созданной

    team_id = current_user.team.id
    feed = Comment.query \
        .filter_by(type=CommentType.FEED) \
        .order_by(Comment.created_at.desc()) \
        .limit(10).all()
    recent_tasks = Task.query.filter(Task.project.has(team_id=team_id)).order_by(Task.deadline.asc()).limit(5).all()
    team_members = User.query.filter_by(team_id=team_id).all()

    return render_template('index.html',
                           feed=feed,
                           recent_tasks=recent_tasks,
                           team_members=team_members)





@app.route('/edit_team', methods=['GET', 'POST'])
@login_required
@teamlead_required
def edit_team():
    team = current_user.team
    if not team:
        flash("Вы не состоите в команде", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        team.name = request.form.get('name')
        team.avatar_url = request.form.get('avatar_url')
        team.description = request.form.get('description')
        db.session.commit()
        flash("Настройки команды обновлены!", "success")
        return redirect(url_for('team_detail', team_id=team.id))

    return render_template('edit_team.html', team=team)



@app.route('/create_team', methods=['GET', 'POST'])
@login_required
def create_team():
    if request.method == 'POST':
        name = request.form.get('name')
        avatar_url = request.form.get('avatar_url')
        description = request.form.get('description')

        if Team.query.filter_by(name=name).first():
            flash("Команда с таким именем уже существует", "danger")
            return redirect(url_for('create_team'))

        invite_code = secrets.token_urlsafe(6)
        team = Team(name=name, avatar_url=avatar_url, description=description, invite_code=invite_code)
        db.session.add(team)
        db.session.commit()

        teamlead_role = Role.query.filter_by(name="TeamLead").first()
        current_user.team_id = team.id
        current_user.role = teamlead_role
        db.session.commit()

        flash(f"Команда создана! Код приглашения: {invite_code}", "success")
        return redirect(url_for('team_detail', team_id=team.id))

    return render_template('create_team.html')



@app.route('/join_team', methods=['GET', 'POST'])
@login_required
def join_team():
    if request.method == 'POST':
        code = request.form.get('invite_code')
        team = Team.query.filter_by(invite_code=code).first()

        if not team:
            flash("Неверный код приглашения", "danger")
            return redirect(url_for('join_team'))

        member_role = Role.query.filter_by(name="Участник").first()
        current_user.team_id = team.id
        current_user.role = member_role
        db.session.commit()

        flash("Вы успешно присоединились к команде!", "success")
        return redirect(url_for('team_detail', team_id=team.id))

    return render_template('join_team.html')

    







@app.route('/regenerate_invite_code', methods=['POST'])
@login_required
def regenerate_invite_code():
    team = current_user.team
    if not team:
        flash("Вы не состоите в команде", "error")
        return redirect(url_for('edit_team'))

    # Проверка роли
    if not current_user.has_role(UserRole.ADMIN):
        abort(403)

    team.invite_code = secrets.token_hex(4)
    db.session.commit()
    flash("Код приглашения обновлён!", "success")
    return redirect(url_for('edit_team'))


        
@app.route('/kanban')
@login_required
def kanban():
    if not current_user.team_id:
        return redirect(url_for('edit_team'))

    tasks = Task.query \
        .join(Project) \
        .filter(Project.team_id == current_user.team_id) \
        .options(
            db.joinedload(Task.assigned_user),
            db.joinedload(Task.creator),
            db.joinedload(Task.project)
        ).all()

    return render_template('kanban.html', tasks=tasks)


@app.route('/leave_team', methods=['POST'])
@login_required
def leave_team():
    current_user.team_id = None
    db.session.commit()
    flash("Вы покинули команду.", "info")
    return redirect(url_for('dashboard'))  # или куда хочешь



@app.route('/debug')
def debug():
    tasks = Task.query.all()
    return '<br>'.join(f"{t.id} | {t.title} | {t.status}" for t in tasks)


@app.route('/task_creator', methods=['GET', 'POST'])
@login_required

def task_creator():
    if not current_user.team:
        return redirect(url_for("edit_team"))
    
    team_projects = Project.query.filter_by(team_id=current_user.team.id).all()
    users = current_user.team.users if current_user.team else []

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority')
        status = TaskStatus.TO_DO
        project_id = request.form.get('project_id')
        deadline = request.form.get('deadline')
        assigned_to = request.form.get('assigned_to')
        created_by = request.form.get('created_by', current_user.id)
        created_at_str = request.form.get('created_at')

        if not title or not priority or not project_id:
            flash("Заполните обязательные поля", "danger")
            return redirect(url_for('task_creator'))

        created_at = datetime.strptime(created_at_str, '%Y-%m-%d') if created_at_str else datetime.utcnow()

        new_task = Task(
            title=title,
            description=description if description else None,
            priority=priority,
            status=status,
            project_id=int(project_id),
            assigned_to=int(assigned_to) if assigned_to else None,
            created_by=int(created_by),
            deadline=datetime.strptime(deadline, '%Y-%m-%d') if deadline else None,
            created_at=created_at
        )

        db.session.add(new_task)
        db.session.commit()
        flash("Задача создана!", "success")
        return redirect(url_for('kanban'))

    projects = Project.query.all()
    users = User.query.filter_by(team_id=current_user.team_id).all()
    current_date = date.today().strftime('%Y-%m-%d')
    return render_template('task_creator.html', team_projects=team_projects, users=users, is_edit=False, current_date=current_date)



@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.created_by != current_user.id and not current_user.is_teamlead():
        abort(403)


    if request.method == 'POST':
        task.title = request.form.get('title', '').strip()
        task.description = request.form.get('description', '').strip()
        task.priority = request.form.get('priority', 'Средний')
        task.status = TaskStatus(request.form.get('status'))

        assigned_to = request.form.get('assigned_to')
        task.assigned_to = int(assigned_to) if assigned_to else None

        deadline = request.form.get('deadline')
        task.deadline = datetime.strptime(deadline, '%Y-%m-%d') if deadline else None

        created_at_str = request.form.get('created_at')
        if created_at_str:
            task.created_at = datetime.strptime(created_at_str, '%Y-%m-%d')

        db.session.commit()
        flash("Задача успешно обновлена!", "success")
        return redirect(url_for('kanban'))

    
    projects = Project.query.filter_by(team_id=current_user.team_id).all()
    users = User.query.filter_by(team_id=current_user.team_id).all()
    current_date = task.created_at.strftime('%Y-%m-%d') if task.created_at else date.today().strftime('%Y-%m-%d')

    return render_template(
        'task_creator.html',
        task=task,
        projects=projects,
        users=users,
        is_edit=True,
        current_date=current_date
    )

@app.route('/delete_task/<int:task_id>', methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.created_by != current_user.id:
        abort(403)

    # Удаляем комментарии вручную
    Comment.query.filter_by(task_id=task.id).delete()

    # Теперь можно удалить задачу
    db.session.delete(task)
    db.session.commit()

    flash("Задача удалена.", "success")
    return redirect(url_for('kanban'))


    




@app.route('/task/<int:task_id>/comment', methods=['POST'])
@login_required
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user.team_id != task.project.team_id:
        return jsonify(success=False, error="Нет доступа к задаче"), 403

    content = request.form.get("content", "").strip()
    parent_id = request.form.get("parent_id")
    attachment = request.files.get("attachment")

    if not content:
        return jsonify(success=False, error="Комментарий пуст")

    # Поиск упомянутого <@user_id:username> для подсветки
    match = re.search(r"<@(\d+):(.+?)>", content)
    if match:
        parent_id = parent_id or match.group(1)

    comment = Comment(
        content=content,
        user_id=current_user.id,
        task_id=task_id,
        parent_id=parent_id if parent_id else None
    )

    # Обработка файла и добавление комментария
    if attachment and attachment.filename and allowed_file(attachment.filename):
        filename = secure_filename(attachment.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        attachment.save(save_path)

        db.session.add(comment)
        db.session.flush()  # Чтобы получить comment.id

        comment.attachments.append(CommentAttachment(
            filename=filename,
            filepath=f'uploads/{filename}',  # путь относительный от static/
            comment_id=comment.id
        ))
    else:
        db.session.add(comment)

    db.session.commit()

    author = {
        "id": current_user.id,
        "username": current_user.username,
        "avatar": current_user.avatar or url_for('static', filename='default_avatar.png')
    }

    return jsonify(success=True, comment={
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at.strftime('%d.%m.%Y %H:%M'),
        "author": author,
        "attachment": attachment.filename if attachment else None,
        "parent_id": comment.parent_id,
        "parent_author": comment.parent.author.username if comment.parent else None
    })







@app.route('/projects', methods=['GET', 'POST'])
@login_required
def project_list():
    # Если пользователь без команды — редирект на выбор
    if not current_user.team:
        return redirect(url_for('edit_team'))

    # Создание проекта (POST)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        if name:
            new_project = Project(name=name, description=description, team_id=current_user.team.id)
            db.session.add(new_project)
            db.session.commit()
            return redirect(url_for('project_list'))

    # Фильтрация и сортировка (GET)
    q = request.args.get('q', '', type=str).strip()
    sort = request.args.get('sort', 'newest')

    query = Project.query.filter_by(team_id=current_user.team.id)

    if q:
        query = query.filter(Project.name.ilike(f'%{q}%'))

    if sort == 'name':
        query = query.order_by(Project.name.asc())
    elif sort == 'oldest':
        query = query.order_by(Project.id.asc())
    else:  # newest
        query = query.order_by(Project.id.desc())

    projects = query.all()
    return render_template('projects.html', projects=projects)



    
    
@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@app.route('/delete_project/<int:project_id>')
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)

    # Удаляем все задачи, связанные с проектом
    Task.query.filter_by(project_id=project.id).delete()

    # Удаляем все отчеты, связанные с проектом
    Report.query.filter_by(project_id=project.id).delete()

    # Удаляем сам проект
    db.session.delete(project)
    db.session.commit()

    flash("Проект и все связанные задачи и отчеты успешно удалены!", "success")
    return redirect(url_for('home'))



@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        team_id = request.form.get('team_id')

        if not name or not team_id:
            flash("Название проекта и команда обязательны", "danger")
            return redirect(url_for('create_project'))

        new_project = Project(
            name=name,
            description=description if description else None,
            team_id=int(team_id)
        )

        db.session.add(new_project)
        db.session.commit()
        flash("Проект создан!", "success")
        return redirect(url_for('project_list'))

    teams = Team.query.all()
    return render_template('create_project.html', teams=teams)



@app.route('/team/<int:team_id>')
@login_required
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)
    all_users = User.query.all()
    return render_template('team_detail.html', team=team, all_users=all_users)

@app.route('/team/<int:team_id>/add_member', methods=['POST'])
@login_required
def add_member(team_id):
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    if user:
        user.team_id = team_id
        db.session.commit()
    return redirect(url_for('team_detail', team_id=team_id))

@app.route('/remove_member/<int:team_id>/<int:user_id>', methods=['GET'])
@login_required
@teamlead_required
def remove_member(team_id, user_id):
    user = User.query.get_or_404(user_id)
    if user.team_id != team_id:
        abort(403)

    user.team_id = None
    user.role = None
    db.session.commit()
    flash("Пользователь удален из команды", "success")
    return redirect(url_for('team_detail', team_id=team_id))


@app.route('/api/project/<int:project_id>/gantt')
@login_required
def get_gantt_data(project_id):
    project = Project.query.get_or_404(project_id)
    if project.team_id != current_user.team_id:
        return jsonify({'error': 'Доступ запрещен'}), 403

    tasks = Task.query.filter_by(project_id=project.id).all()
    result = []

    for task in tasks:
        start_date = task.created_at.strftime('%Y-%m-%d') if task.created_at else '2024-01-01'
        end_date = task.deadline.strftime('%Y-%m-%d') if task.deadline else start_date

        result.append({
            'id': task.id,
            'name': task.title,
            'start': start_date,
            'end': end_date,
            'priority': task.priority or 'Средний',
            'description': task.description
        })

    return jsonify(result)



@app.route("/comment/<int:comment_id>/html")
def render_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return render_template("_comment_block.html", comment=comment, current_user=current_user)

@app.route("/post_feed_comment", methods=["POST"])
@login_required
def post_feed_comment():
    content = request.form.get("content", "").strip()

    if not content:
        flash("Сообщение не может быть пустым", "warning")
        return redirect(url_for("home"))

    comment = Comment(
        content=content,
        user_id=current_user.id,
        type=CommentType.FEED
    )
    db.session.add(comment)
    db.session.commit()

    flash("Сообщение отправлено", "success")
    return redirect(url_for("home"))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
