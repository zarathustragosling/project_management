from flask import Blueprint
from views.user_view import HomeView, ProfileUpdateView, ProfileView, PasswordChangeView, RegisterView, LoginView, LogoutView

# Создаем Blueprint для маршрутов пользователей
user_bp = Blueprint('user', __name__, url_prefix='/user')

# Регистрируем представления
user_bp.add_url_rule('/', view_func=HomeView.as_view('home'))
user_bp.add_url_rule('/profile', view_func=ProfileUpdateView.as_view('update_profile'), methods=['GET', 'POST'])
user_bp.add_url_rule('/profile/<int:user_id>', view_func=ProfileView.as_view('view_profile'))
user_bp.add_url_rule('/change_password', view_func=PasswordChangeView.as_view('change_password'), methods=['POST'])
user_bp.add_url_rule('/register', view_func=RegisterView.as_view('register'), methods=['GET', 'POST'])
user_bp.add_url_rule('/login', view_func=LoginView.as_view('login'), methods=['GET', 'POST'])
user_bp.add_url_rule('/logout', view_func=LogoutView.as_view('logout'))
user_bp.add_url_rule('/<int:user_id>', view_func=ProfileView.as_view('user_profile'))