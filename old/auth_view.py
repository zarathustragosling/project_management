from flask import render_template, redirect, url_for, flash
from views.base_view import BaseView, LoginRequiredMixin

class LoginView(BaseView):
    """Представление для входа в систему"""
    
    def get(self):
        """Страница входа в систему (GET)"""
        # Вся бизнес-логика перенесена в контроллер auth_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Вход в систему (POST)"""
        # Вся бизнес-логика перенесена в контроллер auth_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def render_login_page():
        """Рендеринг страницы входа в систему"""
        return render_template('login.html')
    
    @staticmethod
    def redirect_after_login():
        """Перенаправление после успешного входа"""
        flash("Вы успешно вошли в систему", "success")
        return redirect(url_for('user_blueprint.home'))

class LogoutView(BaseView, LoginRequiredMixin):
    """Представление для выхода из системы"""
    
    def get(self):
        """Выход из системы"""
        # Вся бизнес-логика перенесена в контроллер auth_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def redirect_after_logout():
        """Перенаправление после выхода из системы"""
        flash("Вы вышли из системы", "info")
        return redirect(url_for('auth_blueprint.login'))

class RegisterView(BaseView):
    """Представление для регистрации"""
    
    def get(self):
        """Страница регистрации (GET)"""
        # Вся бизнес-логика перенесена в контроллер auth_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Регистрация пользователя (POST)"""
        # Вся бизнес-логика перенесена в контроллер auth_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    @staticmethod
    def render_register_page(teams=None):
        """Рендеринг страницы регистрации"""
        return render_template('register.html', teams=teams)
    
    @staticmethod
    def redirect_after_register():
        """Перенаправление после успешной регистрации"""
        flash("Регистрация успешна! Теперь вы можете войти в систему", "success")
        return redirect(url_for('auth_blueprint.login'))

# Примечание: Эти классы представлений сохранены для обратной совместимости,
# но теперь они не содержат бизнес-логику, которая перенесена в контроллеры.
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.