from flask import Blueprint
from views.report_view import ReportsListView, GenerateReportView, ViewReportView, DeleteReportView, ProjectReportsView, AllReportsView

# Создаем Blueprint для маршрутов отчетов
report_bp = Blueprint('report', __name__, url_prefix='/report')

# Регистрируем представления
report_bp.add_url_rule('/list', view_func=ReportsListView.as_view('reports'), methods=['GET', 'POST'])
report_bp.add_url_rule('/generate/<int:project_id>', view_func=GenerateReportView.as_view('generate_report'), methods=['GET'])
report_bp.add_url_rule('/<int:report_id>', view_func=ViewReportView.as_view('view_report'))
report_bp.add_url_rule('/delete/<int:report_id>', view_func=DeleteReportView.as_view('delete_report'), methods=['POST'])
report_bp.add_url_rule('/project/<int:project_id>/reports', view_func=ProjectReportsView.as_view('project_reports'))
report_bp.add_url_rule('/all', view_func=AllReportsView.as_view('all_reports'), methods=['GET'])