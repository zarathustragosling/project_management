from flask.views import MethodView
from flask_login import login_required
from functools import wraps

class BaseView(MethodView):
    """Базовый класс для всех представлений"""
    
    decorators = []
    
    def __init__(self):
        super().__init__()
        
    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        """Обертка для добавления декораторов к представлению"""
        view = super().as_view(name, *class_args, **class_kwargs)
        
        # Применяем декораторы в обратном порядке
        for decorator in reversed(cls.decorators):
            view = decorator(view)
            
        return view

class LoginRequiredMixin:
    """Миксин для добавления требования авторизации"""
    decorators = [login_required]

class AdminRequiredMixin:
    """Миксин для добавления требования прав администратора"""
    
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_admin:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    
    decorators = [admin_required, login_required]

class TeamLeadRequiredMixin:
    """Миксин для добавления требования прав тимлида"""
    
    def teamlead_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.is_teamlead():
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    
    decorators = [teamlead_required, login_required]