from flask import render_template, redirect, url_for, flash, abort, jsonify
from flask_login import current_user
from .base_view import BaseView, LoginRequiredMixin, TeamLeadRequiredMixin

class TeamDetailView(BaseView, LoginRequiredMixin):
    """Представление для просмотра деталей команды"""
    
    def get(self, team_id):
        """Просмотр деталей команды"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render(cls, team, team_members, roles):
        """Рендеринг шаблона деталей команды"""
        return render_template('team_detail.html', team=team, team_members=team_members, roles=roles)

class TeamCreateView(BaseView, LoginRequiredMixin):
    """Представление для создания команды"""
    
    def get(self):
        """Страница создания команды (GET)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Создание команды (POST)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_create_page(cls):
        """Рендеринг страницы создания команды"""
        return render_template('create_team.html')

class TeamEditView(BaseView, TeamLeadRequiredMixin):
    """Представление для редактирования команды"""
    
    def get(self):
        """Страница редактирования команды (GET)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Обновление команды (POST)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_edit_page(cls, team):
        """Рендеринг страницы редактирования команды"""
        return render_template('edit_team.html', team=team)

class TeamSelectView(BaseView, LoginRequiredMixin):
    """Представление для выбора команды"""
    
    def get(self):
        """Страница выбора команды (GET)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Выбор команды (POST)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_select_page(cls):
        """Рендеринг страницы выбора команды"""
        return render_template('select_team.html')

class TeamLeaveView(BaseView, LoginRequiredMixin):
    """Представление для выхода из команды"""
    
    def post(self):
        """Выход из команды"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def redirect_after_leave(cls):
        """Перенаправление после выхода из команды"""
        flash("Вы вышли из команды", "info")
        return redirect(url_for('user_blueprint.home'))

class TeamInviteCodeView(BaseView, TeamLeadRequiredMixin):
    """Представление для обновления кода приглашения"""
    
    def post(self):
        """Обновление кода приглашения"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def redirect_after_refresh(cls, team_id):
        """Перенаправление после обновления кода приглашения"""
        flash("Код приглашения обновлен!", "success")
        return redirect(url_for('team_blueprint.team_detail', team_id=team_id))

class TeamJoinView(BaseView, LoginRequiredMixin):
    """Представление для присоединения к команде"""
    
    def get(self):
        """Страница присоединения к команде (GET)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
    
    def post(self):
        """Присоединение к команде (POST)"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def render_join_page(cls):
        """Рендеринг страницы присоединения к команде"""
        return render_template('join_team.html')

class TeamMemberManagementView(BaseView, TeamLeadRequiredMixin):
    """Представление для управления участниками команды"""
    
    def post(self, team_id):
        """Добавление участника в команду или изменение его роли"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def redirect_after_update(cls, team_id):
        """Перенаправление после обновления участника команды"""
        flash("Роль пользователя обновлена", "success")
        return redirect(url_for('team_blueprint.team_detail', team_id=team_id))

class TeamMemberRemoveView(BaseView, TeamLeadRequiredMixin):
    """Представление для удаления участника из команды"""
    
    def get(self, team_id, user_id):
        """Удаление участника из команды"""
        # Этот метод не будет вызываться напрямую, так как маршруты теперь
        # указывают на функции контроллера
        pass
        
    @classmethod
    def redirect_after_remove(cls, team_id):
        """Перенаправление после удаления участника команды"""
        flash("Пользователь удален из команды", "success")
        return redirect(url_for('team_blueprint.team_detail', team_id=team_id))

# Примечание: Эти классы представлений сохранены для обратной совместимости,
# но теперь они не содержат бизнес-логику, которая перенесена в контроллеры.
# В будущем эти классы могут быть полностью удалены, когда все ссылки на них
# будут заменены на прямые вызовы функций контроллера.