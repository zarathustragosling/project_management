from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, abort, jsonify, make_response
from flask_login import current_user, login_required
from database import db, User, Project, Report, Team, Task, TaskStatus
from controllers.access_control import team_access_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import io
from weasyprint import HTML, CSS
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Использование Agg бэкенда для работы без GUI

# Создаем Blueprint для маршрутов отчетов
report_bp = Blueprint('report', __name__, url_prefix='/report')

# Функции контроллера для отчетов
def reports_list():
    """Отображение списка отчетов"""
    if not current_user.team_id:
        return redirect(url_for('team_blueprint.select_team'))
    
    # Фильтруем проекты только по команде текущего пользователя
    # Даже для администраторов показываем только проекты их команды
    projects = Project.query.filter_by(team_id=current_user.team_id).all()
    
    # Получаем список последних 5 отчетов для проектов текущей команды
    team_projects_ids = [project.id for project in projects]
    reports = Report.query.filter(Report.project_id.in_(team_projects_ids)).order_by(Report.created_at.desc()).limit(5).all()
    
    return render_template('reports.html', projects=projects, reports=reports)

def create_report():
    """Создание отчета вручную"""
    if not current_user.team_id:
        return redirect(url_for('team_blueprint.select_team'))
    
    filename = request.form.get('filename')
    filepath = request.form.get('filepath')
    project_id = request.form.get('project_id')
    
    if not filename or not filepath or not project_id:
        flash('Все поля обязательны для заполнения', 'danger')
        return redirect(url_for('report_blueprint.reports'))
    
    try:
        # Преобразуем project_id в целое число
        project_id = int(project_id)
        
        # Проверяем, существует ли проект и принадлежит ли он команде пользователя
        project = Project.query.get_or_404(project_id)
        if project.team_id != current_user.team_id and not current_user.is_admin:
            abort(403)
        
        new_report = Report(
            filename=filename,
            filepath=filepath,
            project_id=project_id
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        flash('Отчет успешно создан!', 'success')
        return redirect(url_for('report_blueprint.reports'))
    except ValueError:
        flash('Некорректный идентификатор проекта', 'danger')
        return redirect(url_for('report_blueprint.reports'))
    except Exception as e:
        flash(f'Ошибка при создании отчета: {str(e)}', 'danger')
        return redirect(url_for('report_blueprint.reports'))

def generate_progress_chart(tasks):
    """Генерация графика прогресса задач"""
    # Подсчет задач по статусам
    status_counts = {
        'To Do': sum(1 for task in tasks if task.status == TaskStatus.TO_DO),
        'In Progress': sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS),
        'Done': sum(1 for task in tasks if task.status == TaskStatus.DONE)
    }
    
    # Создание графика
    plt.figure(figsize=(8, 4))
    plt.bar(status_counts.keys(), status_counts.values(), color=['#f87171', '#facc15', '#4ade80'])
    plt.title('Статус задач проекта')
    plt.ylabel('Количество задач')
    
    # Сохранение графика в base64 для вставки в HTML
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')

def generate_gantt_chart(project_id):
    """Генерация данных для диаграммы Ганта"""
    tasks = Task.query.filter_by(project_id=project_id).all()
    gantt_data = []
    
    for task in tasks:
        start_date = task.created_at.strftime('%Y-%m-%d') if task.created_at else '2024-01-01'
        end_date = task.deadline.strftime('%Y-%m-%d') if task.deadline else start_date
        
        gantt_data.append({
            'id': task.id,
            'name': task.title,
            'start': start_date,
            'end': end_date,
            'priority': task.priority,
            'status': task.status.value
        })
    
    return gantt_data

@login_required
@team_access_required
def generate_report(project_id):
    """Генерация PDF-отчета"""
    project = Project.query.get_or_404(project_id)
    
    # Проверяем, что проект принадлежит команде пользователя
    if project.team_id != current_user.team_id and not current_user.is_admin:
        flash("У вас нет доступа к этому проекту", "danger")
        return redirect(url_for('report_blueprint.reports'))
    
    # Получаем данные для отчета
    team = Team.query.get(project.team_id)
    tasks = Task.query.filter_by(project_id=project.id).all()
    team_members = User.query.filter_by(team_id=team.id).all()
    
    # Проверяем наличие задач в проекте
    if not tasks:
        flash('В проекте нет задач. Отчет не может быть сгенерирован.', 'warning')
        return redirect(url_for('report_blueprint.reports'))
    
    # Статистика
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.DONE)
    overdue_tasks = sum(1 for task in tasks if task.deadline and task.deadline < datetime.now().date() and task.status != TaskStatus.DONE)
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Генерация графика прогресса
    progress_chart = generate_progress_chart(tasks)
    
    # Получение данных для диаграммы Ганта
    gantt_data = generate_gantt_chart(project_id)
    
    # Генерация HTML для отчета
    html_content = render_template(
        'report_template.html',
        project=project,
        team=team,
        tasks=tasks,
        team_members=team_members,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        completion_percentage=completion_percentage,
        progress_chart=progress_chart,
        gantt_data=gantt_data,
        current_user=current_user,
        generation_date=datetime.now().strftime('%d.%m.%Y %H:%M')
    )
    
    # Генерация PDF из HTML
    from flask import current_app
    css_path = os.path.join(current_app.static_folder, 'css', 'pdf_report.css')
    pdf = HTML(string=html_content).write_pdf(stylesheets=[CSS(css_path)])
    
    # Создаем запись о новом отчете в базе данных
    filename = f"report_{project.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    UPLOAD_FOLDER = os.path.join(current_app.static_folder, 'uploads')
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Сохраняем PDF на диск
    with open(filepath, 'wb') as f:
        f.write(pdf)
    
    # Создаем запись в базе данных
    new_report = Report(filename=filename, filepath=filepath, project_id=project_id)
    db.session.add(new_report)
    db.session.commit()
    
    flash('Отчет успешно сгенерирован!', 'success')
    return redirect(url_for('report_blueprint.view_report', report_id=new_report.id))

def view_report(report_id):
    """Просмотр отчета"""
    report = Report.query.get_or_404(report_id)
    
    # Проверяем, принадлежит ли отчет проекту команды пользователя
    project = Project.query.get(report.project_id)
    if project.team_id != current_user.team_id and not current_user.is_admin:
        abort(403)
    
    # Отправляем файл пользователю
    from flask import current_app
    directory = os.path.dirname(report.filepath)
    filename = os.path.basename(report.filepath)
    return send_from_directory(directory, filename)

def delete_report(report_id):
    """Удаление отчета"""
    report = Report.query.get_or_404(report_id)
    
    # Проверяем, принадлежит ли отчет проекту команды пользователя
    project = Project.query.get(report.project_id)
    if project.team_id != current_user.team_id and not current_user.is_admin:
        abort(403)
    
    # Удаляем файл с диска
    if os.path.exists(report.filepath):
        os.remove(report.filepath)
    
    # Удаляем запись из базы данных
    db.session.delete(report)
    db.session.commit()
    
    flash('Отчет успешно удален!', 'success')
    return redirect(url_for('report_blueprint.reports'))

@login_required
@team_access_required
def project_reports(project_id):
    """Отображение отчетов проекта"""
    project = Project.query.get_or_404(project_id)
    
    # Проверяем, принадлежит ли проект команде пользователя
    if project.team_id != current_user.team_id and not current_user.is_admin:
        abort(403)
    
    reports = Report.query.filter_by(project_id=project_id).order_by(Report.created_at.desc()).all()
    return render_template('project_reports.html', project=project, reports=reports)

@login_required
def all_reports():
    """Отображение всех отчетов с поиском и сортировкой"""
    if not current_user.team_id:
        flash("Вы не состоите в команде", "warning")
        return redirect(url_for('team_blueprint.select_team'))
    
    # Получаем параметры поиска и сортировки
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'date_desc')
    
    # Фильтруем проекты только по команде текущего пользователя
    projects = Project.query.filter_by(team_id=current_user.team_id).all()
    team_projects_ids = [project.id for project in projects]
    
    # Базовый запрос для отчетов
    query = Report.query.filter(Report.project_id.in_(team_projects_ids))
    
    # Применяем поиск по проекту, если указан
    if search_query:
        # Получаем проекты, соответствующие поисковому запросу
        matching_projects = Project.query.filter(
            Project.team_id == current_user.team_id,
            Project.name.ilike(f'%{search_query}%')
        ).all()
        matching_project_ids = [p.id for p in matching_projects]
        query = query.filter(Report.project_id.in_(matching_project_ids))
    
    # Применяем сортировку
    if sort_by == 'date_asc':
        query = query.order_by(Report.created_at.asc())
    else:  # По умолчанию сортировка по дате (по убыванию)
        query = query.order_by(Report.created_at.desc())
    
    # Получаем отчеты
    reports = query.all()
    
    return render_template('all_reports.html', 
                           reports=reports, 
                           projects=projects, 
                           search_query=search_query, 
                           sort_by=sort_by)

def generate_gantt_svg(tasks):
    """Функция для генерации SVG-диаграммы Ганта"""
    if not tasks:
        return ""
        
    # Определяем временные рамки проекта
    
    # Находим минимальную и максимальную даты
    min_date = datetime.now().date()
    max_date = datetime.now().date()
    
    for task in tasks:
        if task.created_at and task.created_at.date() < min_date:
            min_date = task.created_at.date()
        if task.deadline and task.deadline > max_date:
            max_date = task.deadline
    
    # Добавляем запас в 5 дней с обеих сторон
    min_date = min_date - timedelta(days=5)
    max_date = max_date + timedelta(days=5)
    
    # Общая продолжительность проекта в днях
    total_days = (max_date - min_date).days
    if total_days <= 0:
        total_days = 30  # Минимальная длительность, если даты некорректны
    
    # Параметры SVG
    svg_width = 800
    svg_height = 30 * (len(tasks) + 1)  # Высота зависит от количества задач
    day_width = svg_width / total_days
    
    # Создаем SVG
    svg = f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">'
    
    # Добавляем заголовок и временную шкалу
    svg += '<style>'
    svg += '.task-bar { fill: #2563eb; rx: 5; ry: 5; }'  # Скругленные углы для задач
    svg += '.task-text { font-family: Arial; font-size: 12px; fill: white; }'  # Стиль текста
    svg += '.timeline-text { font-family: Arial; font-size: 10px; fill: #666; }'  # Стиль временной шкалы
    svg += '</style>'
    
    # Рисуем временную шкалу (каждые 7 дней)
    for i in range(0, total_days + 1, 7):
        x_pos = i * day_width
        date = min_date + timedelta(days=i)
        date_str = date.strftime('%d.%m')
        
        # Вертикальная линия
        svg += f'<line x1="{x_pos}" y1="0" x2="{x_pos}" y2="{svg_height}" stroke="#ddd" stroke-width="1" />'
        # Текст даты
        svg += f'<text x="{x_pos + 2}" y="15" class="timeline-text">{date_str}</text>'
    
    # Рисуем задачи
    for i, task in enumerate(tasks):
        if not task.created_at or not task.deadline:
            continue
            
        # Вычисляем позицию и длину полосы задачи
        start_days = (task.created_at.date() - min_date).days
        end_days = (task.deadline - min_date).days
        
        if start_days < 0:
            start_days = 0
        if end_days < start_days:
            end_days = start_days + 1
            
        task_width = (end_days - start_days) * day_width
        if task_width < 2:
            task_width = 2  # Минимальная ширина для видимости
            
        x_pos = start_days * day_width
        y_pos = 30 * (i + 1)
        
        # Определяем цвет в зависимости от статуса
        color = '#2563eb'  # По умолчанию синий
        if task.status == TaskStatus.DONE:
            color = '#10b981'  # Зеленый для завершенных
        elif task.status == TaskStatus.IN_PROGRESS:
            color = '#f59e0b'  # Оранжевый для в процессе
        elif task.deadline and task.deadline < datetime.now().date() and task.status != TaskStatus.DONE:
            color = '#ef4444'  # Красный для просроченных
        
        # Рисуем полосу задачи
        svg += f'<rect x="{x_pos}" y="{y_pos}" width="{task_width}" height="20" class="task-bar" fill="{color}" />'
        
        # Добавляем название задачи
        text_x = x_pos + 5
        text_y = y_pos + 15
        task_title = task.title
        if len(task_title) > 30:  # Ограничиваем длину названия
            task_title = task_title[:27] + '...'
        svg += f'<text x="{text_x}" y="{text_y}" class="task-text">{task_title}</text>'
    
    svg += '</svg>'
    
    # Кодируем SVG в base64 для вставки в HTML
    svg_bytes = svg.encode('utf-8')
    svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
    
    return svg_base64

# Регистрируем маршруты
report_bp.add_url_rule('/list', view_func=reports_list, endpoint='reports')
report_bp.add_url_rule('/create', view_func=create_report, endpoint='create_report', methods=['POST'])
report_bp.add_url_rule('/generate/<int:project_id>', view_func=generate_report, endpoint='generate_report')
report_bp.add_url_rule('/<int:report_id>', view_func=view_report, endpoint='view_report')
report_bp.add_url_rule('/delete/<int:report_id>', view_func=delete_report, endpoint='delete_report', methods=['POST'])
report_bp.add_url_rule('/project/<int:project_id>/reports', view_func=project_reports, endpoint='project_reports')
report_bp.add_url_rule('/all', view_func=all_reports, endpoint='all_reports')

# Сохраняем классы представлений для обратной совместимости
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.
from views.report_view import ReportsListView, GenerateReportView, ViewReportView, DeleteReportView, ProjectReportsView, AllReportsView

# Переопределяем методы классов представлений для обратной совместимости
ReportsListView.get = lambda self: reports_list()
GenerateReportView.get = lambda self, project_id: generate_report(project_id)
ViewReportView.get = lambda self, report_id: view_report(report_id)
DeleteReportView.post = lambda self, report_id: delete_report(report_id)
ProjectReportsView.get = lambda self, project_id: project_reports(project_id)
AllReportsView.get = lambda self: all_reports()