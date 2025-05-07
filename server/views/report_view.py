from flask.views import MethodView
from flask import render_template, request, redirect, url_for, flash, send_from_directory, abort, jsonify, make_response
from flask_login import current_user
from database import db, User, Project, Report, Team, Task, TaskStatus
from werkzeug.utils import secure_filename
import os
from functools import wraps
from datetime import datetime, timedelta
import io
from weasyprint import HTML, CSS
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Использование Agg бэкенда для работы без GUI
from views.base_view import BaseView, LoginRequiredMixin

class ReportsListView(LoginRequiredMixin, BaseView):
    """Представление для отображения списка отчетов"""
    
    def get(self):
        if not current_user.team_id:
            return redirect(url_for('team.select_team'))
        
        # Фильтруем проекты только по команде текущего пользователя
        # Даже для администраторов показываем только проекты их команды
        projects = Project.query.filter_by(team_id=current_user.team_id).all()
        
        # Получаем список последних 5 отчетов для проектов текущей команды
        team_projects_ids = [project.id for project in projects]
        reports = Report.query.filter(Report.project_id.in_(team_projects_ids)).order_by(Report.created_at.desc()).limit(5).all()
        
        return render_template('reports.html', projects=projects, reports=reports)

class GenerateReportView(LoginRequiredMixin, BaseView):
    """Представление для генерации PDF-отчета"""
    
    def get(self, project_id):
        project = Project.query.get_or_404(project_id)
        
        # Проверяем, принадлежит ли проект команде пользователя
        if project.team_id != current_user.team_id:
            abort(403)
        
        # Получаем данные для отчета
        team = Team.query.get(project.team_id)
        tasks = Task.query.filter_by(project_id=project.id).all()
        team_members = User.query.filter_by(team_id=team.id).all()
        
        # Проверяем наличие задач в проекте
        if not tasks:
            flash('В проекте нет задач. Отчет не может быть сгенерирован.', 'warning')
            return redirect(url_for('report.reports'))
        
        # Статистика
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.DONE)
        overdue_tasks = sum(1 for task in tasks if task.deadline and task.deadline < datetime.now().date() and task.status != TaskStatus.DONE)
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Генерация графика прогресса
        progress_chart = self.generate_progress_chart(tasks)
        
        # Получение данных для диаграммы Ганта
        gantt_data = self.generate_gantt_chart(project_id)
        
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
        
        # Возвращаем PDF как ответ
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        
        # Кодируем имя файла для корректной обработки кириллицы
        # Используем транслитерацию для filename и RFC 5987 кодирование для filename*
        from urllib.parse import quote
        
        # Создаем ASCII-версию имени файла для обратной совместимости
        ascii_filename = ''.join(c for c in filename if ord(c) < 128)
        if not ascii_filename:
            ascii_filename = 'report.pdf'
        
        # Формируем заголовок в соответствии с RFC 6266 и RFC 5987
        response.headers['Content-Disposition'] = f'inline; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(filename)}'
        
        return response
    
    def generate_progress_chart(self, tasks):
        """Функция для генерации графика прогресса"""
        # Подсчет задач по статусам
        status_counts = {
            'To Do': sum(1 for task in tasks if task.status == TaskStatus.TO_DO),
            'In Progress': sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS),
            'Done': sum(1 for task in tasks if task.status == TaskStatus.DONE)
        }
        
        # Создание графика
        plt.figure(figsize=(8, 4))
        
        # Создание круговой диаграммы
        labels = list(status_counts.keys())
        sizes = list(status_counts.values())
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')  # Равные пропорции для круговой диаграммы
        plt.title('Распределение задач по статусам')
        
        # Сохранение графика в base64 для вставки в HTML
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        
        # Кодирование в base64
        chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return chart_base64
    
    def generate_gantt_chart(self, project_id):
        """Функция для генерации диаграммы Ганта"""
        # Получаем данные для диаграммы Ганта
        project = Project.query.get_or_404(project_id)
        tasks = Task.query.filter_by(project_id=project.id).all()
        gantt_data = []

        for task in tasks:
            start_date = task.created_at.strftime('%Y-%m-%d') if task.created_at else '2024-01-01'
            end_date = task.deadline.strftime('%Y-%m-%d') if task.deadline else start_date

            gantt_data.append({
                'id': task.id,
                'name': task.title,
                'start': start_date,
                'end': end_date,
                'priority': task.priority or 'Средний',
                'description': task.description
            })
        
        return gantt_data
    
    def generate_gantt_svg(self, tasks):
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

class ViewReportView(LoginRequiredMixin, BaseView):
    """Представление для просмотра отчета"""
    
    def get(self, report_id):
        report = Report.query.get_or_404(report_id)
        
        # Получаем путь к папке uploads
        from flask import current_app
        UPLOAD_FOLDER = os.path.join(current_app.static_folder, 'uploads')
        
        return send_from_directory(UPLOAD_FOLDER, report.filename)

class DeleteReportView(LoginRequiredMixin, BaseView):
    """Представление для удаления отчета"""
    
    def post(self, report_id):
        report = Report.query.get_or_404(report_id)
        
        # Проверяем, принадлежит ли отчет проекту команды пользователя
        # Даже администраторы должны видеть только отчеты проектов своей команды
        project = Project.query.get(report.project_id)
        if project.team_id != current_user.team_id:
            abort(403)
        
        # Удаляем файл отчета
        try:
            from flask import current_app
            UPLOAD_FOLDER = os.path.join(current_app.static_folder, 'uploads')
            os.remove(os.path.join(UPLOAD_FOLDER, report.filename))
        except Exception as e:
            # Если файл не найден, просто продолжаем
            pass
        
        # Удаляем запись из базы данных
        db.session.delete(report)
        db.session.commit()
        
        flash('Отчет успешно удален!', 'success')
        return redirect(url_for('report.reports'))

class ProjectReportsView(LoginRequiredMixin, BaseView):
    """Представление для получения отчетов проекта"""
    
    def get(self, project_id):
        project = Project.query.get_or_404(project_id)
        
        # Проверяем, принадлежит ли проект команде пользователя
        # Даже администраторы должны видеть только проекты своей команды
        if project.team_id != current_user.team_id:
            abort(403)
        
        reports = Report.query.filter_by(project_id=project_id).order_by(Report.created_at.desc()).all()
        return render_template('project_reports.html', reports=reports, project=project)

class AllReportsView(LoginRequiredMixin, BaseView):
    """Представление для отображения всех отчетов с поиском и сортировкой"""
    
    def get(self):
        if not current_user.team_id:
            return redirect(url_for('team.select_team'))
        
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