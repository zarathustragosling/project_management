from flask.views import MethodView
from flask import render_template
from views.base_view import BaseView, LoginRequiredMixin
# Импорты функций контроллера выполняются внутри методов классов для избежания циклических импортов

class ReportsListView(LoginRequiredMixin, BaseView):
    """Представление для отображения списка отчетов"""
    
    def get(self):
        # Вся бизнес-логика перенесена в контроллер report_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        from controllers.report_controller import reports_list
        return reports_list()

class GenerateReportView(LoginRequiredMixin, BaseView):
    """Представление для генерации PDF-отчета"""
    
    def get(self, project_id):
        # Вся бизнес-логика перенесена в контроллер report_controller.py
        from controllers.report_controller import generate_report
        return generate_report(project_id)

class ViewReportView(LoginRequiredMixin, BaseView):
    """Представление для просмотра отчета"""
    
    def get(self, report_id):
        from controllers.report_controller import view_report
        return view_report(report_id)

class DeleteReportView(LoginRequiredMixin, BaseView):
    """Представление для удаления отчета"""
    
    def post(self, report_id):
        from controllers.report_controller import delete_report
        return delete_report(report_id)

class ProjectReportsView(LoginRequiredMixin, BaseView):
    """Представление для получения отчетов проекта"""
    
    def get(self, project_id):
        from controllers.report_controller import project_reports
        return project_reports(project_id)

class AllReportsView(LoginRequiredMixin, BaseView):
    """Представление для отображения всех отчетов с поиском и сортировкой"""
    
    def get(self):
        from controllers.report_controller import all_reports
        return all_reports()