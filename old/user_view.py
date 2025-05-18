from flask import render_template, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from .base_view import BaseView, LoginRequiredMixin

class HomeView(BaseView):
    """Представление для главной страницы"""
    
    def get(self):
        """Главная страница"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render(cls, feed=None, recent_tasks=None, team_members=None):
        """Рендеринг главной страницы"""
        return render_template('index.html', feed=feed, recent_tasks=recent_tasks, team_members=team_members)

class DashboardView(BaseView, LoginRequiredMixin):
    """Представление для личного кабинета пользователя"""
    
    def get(self):
        """Личный кабинет пользователя"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render(cls, assigned_tasks, created_tasks):
        """Рендеринг личного кабинета пользователя"""
        return render_template('dashboard.html', assigned_tasks=assigned_tasks, created_tasks=created_tasks)

class ProfileUpdateView(BaseView, LoginRequiredMixin):
    """Представление для обновления профиля"""
    
    def get(self):
        """Страница редактирования профиля (GET)"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Обновление профиля (POST)"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_edit_page(cls):
        """Рендеринг страницы редактирования профиля"""
        return render_template('edit_profile.html')
        
    @classmethod
    def redirect_after_update(cls):
        """Перенаправление после обновления профиля"""
        flash("Профиль обновлен!", "success")
        return redirect(url_for('user_blueprint.dashboard'))

class ProfileView(BaseView, LoginRequiredMixin):
    """Представление для просмотра профиля"""
    
    def get(self, user_id):
        """Просмотр профиля пользователя"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render(cls, user):
        """Рендеринг профиля пользователя"""
        return render_template('user_profile.html', user=user)

class PasswordChangeView(BaseView, LoginRequiredMixin):
    """Представление для изменения пароля"""
    
    def post(self):
        """Изменение пароля"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def redirect_after_change(cls):
        """Перенаправление после изменения пароля"""
        flash("Пароль изменен", "success")
        return redirect(url_for('user_blueprint.dashboard'))

class RegisterView(BaseView):
    """Представление для регистрации"""
    
    def get(self):
        """Страница регистрации (GET)"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Регистрация пользователя (POST)"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_register_page(cls, teams):
        """Рендеринг страницы регистрации"""
        return render_template('register.html', teams=teams)
        
    @classmethod
    def redirect_after_register(cls):
        """Перенаправление после регистрации"""
        flash("Регистрация успешна! Войдите в систему.", "success")
        return redirect(url_for('user_blueprint.login'))

class LoginView(BaseView):
    """Представление для входа в систему"""
    
    def get(self):
        """Страница входа в систему (GET)"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Вход в систему (POST)"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_login_page(cls, error=None):
        """Рендеринг страницы входа в систему"""
        return render_template('login.html')
        
    @classmethod
    def redirect_after_login(cls):
        """Перенаправление после входа в систему"""
        return redirect(url_for('user_blueprint.home'))

class LogoutView(BaseView, LoginRequiredMixin):
    """Представление для выхода из системы"""
    
    def get(self):
        """Выход из системы"""
        # Вся бизнес-логика перенесена в контроллер user_controller.py
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def redirect_after_logout(cls):
        """Перенаправление после выхода из системы"""
        flash("Вы вышли из системы.", "info")
        return redirect(url_for('user_blueprint.login'))

# Примечание: Эти классы представлений сохранены для обратной совместимости,
# но теперь они не содержат бизнес-логику, которая перенесена в контроллеры.
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.