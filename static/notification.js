// Скрипт для работы с уведомлениями

document.addEventListener('DOMContentLoaded', function() {
    // Обновление счетчика уведомлений каждые 60 секунд
    setInterval(updateNotificationCount, 60000);
    
    // Первоначальное обновление счетчика при загрузке страницы
    updateNotificationCount();
    
    // Функция для обновления счетчика уведомлений
    function updateNotificationCount() {
        fetch('/notification/count')
            .then(response => response.json())
            .then(data => {
                const countElement = document.getElementById('notification-count');
                if (countElement) {
                    if (data.count > 0) {
                        countElement.textContent = data.count;
                        countElement.classList.remove('hidden');
                    } else {
                        countElement.classList.add('hidden');
                    }
                }
            })
            .catch(error => console.error('Ошибка при обновлении счетчика уведомлений:', error));
    }
    
    // Обработчик для кнопок отметки уведомлений как прочитанных
    const markReadButtons = document.querySelectorAll('.mark-read-btn');
    if (markReadButtons.length > 0) {
        markReadButtons.forEach(button => {
            button.addEventListener('click', function() {
                const notificationId = this.dataset.notificationId;
                markAsRead(notificationId, this);
            });
        });
    }
    
    // Функция для отметки уведомления как прочитанного
    function markAsRead(notificationId, buttonElement) {
        fetch(`/notification/mark_as_read/${notificationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Визуально отметить как прочитанное
                const notificationElement = buttonElement.closest('.border-blue-500');
                if (notificationElement) {
                    notificationElement.classList.remove('border-blue-500');
                    notificationElement.classList.add('border-gray-600');
                }
                
                // Изменить иконку кнопки
                buttonElement.querySelector('i').classList.add('text-gray-600');
                buttonElement.disabled = true;
                
                // Удалить метку "Новое"
                const newBadge = buttonElement.closest('.bg-[#2a2a2a]').querySelector('.bg-blue-600');
                if (newBadge) {
                    newBadge.remove();
                }
                
                // Обновить счетчик в навигации
                updateNotificationCount();
            }
        })
        .catch(error => console.error('Ошибка при отметке уведомления как прочитанного:', error));
    }
});