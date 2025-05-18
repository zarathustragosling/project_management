from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, abort, jsonify, make_response
from flask_login import current_user, login_required
from database import db, User, Project, Report, Team, Task, TaskStatus
from utils.access_control import team_access_required
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

class ReportView:
    """Класс представления для отчетов"""
    
    @staticmethod
    def render_list(projects, reports):
        """Рендеринг списка отчетов"""
        return render_template('reports.html', projects=projects, reports=reports)
    
    @staticmethod
    def render_report(report_id):
        """Рендеринг отчета"""
        return redirect(url_for('static', filename=f'reports/{report_id}.pdf'))
    
    @staticmethod
    def render_project_reports(reports):
        """Рендеринг отчетов проекта"""
        return jsonify([{
            'id': report.id,
            'filename': report.filename,
            'created_at': report.created_at.strftime('%d.%m.%Y %H:%M')
        } for report in reports])
    
    @staticmethod
    def render_all_reports(reports, total_count):
        """Рендеринг всех отчетов с поиском и сортировкой"""
        return render_template('all_reports.html', reports=reports, total_count=total_count)

class ReportController:
    """Класс контроллера для отчетов"""
    
    @staticmethod
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
        
        return ReportView.render_list(projects, reports)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def generate_gantt_chart(project_id):
        """Генерация данных для диаграммы Ганта"""
        tasks = Task.query.filter_by(project_id=project_id).order_by(Task.deadline).all()
        
        # Формируем данные для диаграммы Ганта
        gantt_data = []
        for task in tasks:
            if task.deadline:
                # Определяем цвет в зависимости от статуса
                color = '#f87171'  # Красный для To Do
                if task.status == TaskStatus.IN_PROGRESS:
                    color = '#facc15'  # Желтый для In Progress
                elif task.status == TaskStatus.DONE:
                    color = '#4ade80'  # Зеленый для Done
                
                # Добавляем задачу в данные для диаграммы
                gantt_data.append({
                    'id': task.id,
                    'title': task.title,
                    'start': task.created_at.strftime('%Y-%m-%d'),
                    'end': task.deadline.strftime('%Y-%m-%d'),
                    'color': color,
                    'status': task.status.value
                })
        
        return gantt_data

    @staticmethod
    def generate_report(project_id):
        """Генерация PDF-отчета"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return redirect(url_for('auth_blueprint.login'))
        
        # Получаем проект
        project = Project.query.get_or_404(project_id)
        
        # Проверяем, что проект принадлежит команде пользователя
        if project.team_id != current_user.team_id and not current_user.is_admin:
            abort(403)
        
        # Получаем задачи проекта
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        # Рассчитываем статистику
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.DONE)
        overdue_tasks = sum(1 for task in tasks if task.deadline and task.deadline < datetime.now().date() and task.status != TaskStatus.DONE)
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Получаем участников команды
        team_members = User.query.filter_by(team_id=project.team_id).all()
        
        # Генерируем график прогресса
        progress_chart = ReportController.generate_progress_chart(tasks)
        
        # Генерируем данные для диаграммы Ганта
        gantt_data = ReportController.generate_gantt_chart(project_id)
        
        # Формируем HTML для отчета
        html_content = render_template(
            'report_template.html',
            project=project,
            team=project.team,
            tasks=tasks,
            team_members=team_members,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            completion_percentage=completion_percentage,
            progress_chart=progress_chart,
            gantt_data=gantt_data,
            generation_date=datetime.now().strftime('%d.%m.%Y'),
            current_user=current_user
        )
        
        # Создаем PDF из HTML
        html = HTML(string=html_content)
        # Используем внешний CSS файл для стилизации PDF
        from flask import current_app
        css_path = os.path.join(current_app.static_folder, 'css', 'pdf_report.css')
        css = CSS(filename=css_path)
        pdf = html.write_pdf(stylesheets=[css])
        
        # Создаем запись о отчете в базе данных
        report_filename = f"Отчет по проекту {project.name} от {datetime.now().strftime('%d.%m.%Y')}"
        report_filepath = f"reports/{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        
        # Сохраняем PDF в файл
        from flask import current_app
        os.makedirs(os.path.join(current_app.static_folder, 'reports'), exist_ok=True)
        with open(os.path.join(current_app.static_folder, report_filepath), 'wb') as f:
            f.write(pdf)
        
        # Создаем запись в базе данных
        new_report = Report(
            filename=report_filename,
            filepath=report_filepath,
            project_id=project_id
        )
        db.session.add(new_report)
        db.session.commit()
        
        # Возвращаем PDF как ответ
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        # Используем ASCII-совместимое имя файла для предотвращения ошибки кодировки
        safe_filename = report_filename.encode('ascii', 'ignore').decode('ascii')
        response.headers['Content-Disposition'] = f'inline; filename={safe_filename}.pdf'
        return response

    @staticmethod
    def view_report(report_id):
        """Просмотр отчета"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return redirect(url_for('auth_blueprint.login'))
        
        # Получаем отчет
        report = Report.query.get_or_404(report_id)
        
        # Проверяем, что отчет принадлежит проекту команды пользователя
        project = Project.query.get(report.project_id)
        if not project or (project.team_id != current_user.team_id and not current_user.is_admin):
            abort(403)
        
        # Возвращаем файл отчета
        from flask import current_app
        return send_from_directory(current_app.static_folder, report.filepath)

    @staticmethod
    def delete_report(report_id):
        """Удаление отчета"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return redirect(url_for('auth_blueprint.login'))
        
        # Получаем отчет
        report = Report.query.get_or_404(report_id)
        
        # Проверяем, что отчет принадлежит проекту команды пользователя
        project = Project.query.get(report.project_id)
        if not project or (project.team_id != current_user.team_id and not current_user.is_admin):
            abort(403)
        
        # Удаляем файл отчета
        from flask import current_app
        try:
            os.remove(os.path.join(current_app.static_folder, report.filepath))
        except:
            # Если файл не существует, просто продолжаем
            pass
        
        # Удаляем запись из базы данных
        db.session.delete(report)
        db.session.commit()
        
        flash('Отчет успешно удален!', 'success')
        return redirect(url_for('report_blueprint.reports'))

    @staticmethod
    def project_reports(project_id):
        """Получение отчетов проекта"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Требуется авторизация'}), 401
        
        # Получаем проект
        project = Project.query.get_or_404(project_id)
        
        # Проверяем, что проект принадлежит команде пользователя
        if project.team_id != current_user.team_id and not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403
        
        # Получаем отчеты проекта
        reports = Report.query.filter_by(project_id=project_id).order_by(Report.created_at.desc()).all()
        
        # Возвращаем отчеты в формате JSON
        return ReportView.render_project_reports(reports)

    @staticmethod
    def all_reports():
        """Отображение всех отчетов с поиском и сортировкой"""
        # Проверяем, что пользователь аутентифицирован
        if not current_user.is_authenticated:
            return redirect(url_for('auth_blueprint.login'))
        
        # Получаем параметры запроса
        q = request.args.get('q', '')
        sort = request.args.get('sort', 'newest')
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Формируем запрос
        query = Report.query.join(Project).filter(Project.team_id == current_user.team_id)
        
        # Применяем поиск
        if q:
            query = query.filter(Report.filename.ilike(f'%{q}%'))
        
        # Применяем сортировку
        if sort == 'oldest':
            query = query.order_by(Report.created_at.asc())
        elif sort == 'name':
            query = query.order_by(Report.filename.asc())
        else:  # newest
            query = query.order_by(Report.created_at.desc())
        
        # Получаем общее количество отчетов
        total_count = query.count()
        
        # Применяем пагинацию
        reports = query.paginate(page=page, per_page=per_page, error_out=False).items
        
        # Возвращаем отчеты
        return ReportView.render_all_reports(reports, total_count)

# Регистрируем маршруты
report_bp.add_url_rule('/', view_func=ReportController.reports_list, endpoint='reports')
report_bp.add_url_rule('/create', view_func=ReportController.create_report, endpoint='create_report', methods=['POST'])
report_bp.add_url_rule('/generate/<int:project_id>', view_func=ReportController.generate_report, endpoint='generate_report')
report_bp.add_url_rule('/view/<int:report_id>', view_func=ReportController.view_report, endpoint='view_report')
report_bp.add_url_rule('/delete/<int:report_id>', view_func=ReportController.delete_report, endpoint='delete_report', methods=['POST'])
report_bp.add_url_rule('/project/<int:project_id>', view_func=ReportController.project_reports, endpoint='project_reports')
report_bp.add_url_rule('/all', view_func=ReportController.all_reports, endpoint='all_reports')