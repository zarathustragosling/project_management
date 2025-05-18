
document.addEventListener('DOMContentLoaded', function () {
  // Инициализация всех компонентов с анимациями
  initializeAnimations();



  // === Редактирование задачи ===
  const form = document.getElementById('editTaskForm');
  if (form) {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      
      // Анимация кнопки при отправке
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.classList.add('animate-pulse');
        submitBtn.disabled = true;
      }
      
      const taskId = form.dataset.taskId;
      const data = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        priority: document.getElementById('priority').value,
        status: document.getElementById('status').value,
        project_id: document.getElementById('project_id').value,
        assigned_to: document.getElementById('assigned_to').value,
        deadline: document.getElementById('deadline')?.value || null
      };
      
      const statusDiv = document.getElementById('saveStatus');
      statusDiv.style.display = 'block';
      statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Сохранение...';
      statusDiv.classList.add('bg-gray-700', 'text-gray-100', 'rounded', 'p-2', 'shadow-lg');
      
      try {
        const res = await fetch(`/task/${taskId}/update`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        const result = await res.json();
        
        if (result.success) {
          statusDiv.innerHTML = '<i class="fas fa-check-circle mr-2"></i> Изменения сохранены';
          statusDiv.classList.remove('bg-gray-700');
          statusDiv.classList.add('bg-green-600');
          
          // Анимация успешного сохранения
          statusDiv.animate([
            { opacity: 0.7, transform: 'scale(0.95)' },
            { opacity: 1, transform: 'scale(1)' }
          ], { duration: 300, easing: 'ease-out' });
        } else {
          statusDiv.innerHTML = '<i class="fas fa-exclamation-circle mr-2"></i> Ошибка';
          statusDiv.classList.remove('bg-gray-700');
          statusDiv.classList.add('bg-red-600');
        }
      } catch (err) {
        statusDiv.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i> Ошибка соединения';
        statusDiv.classList.remove('bg-gray-700');
        statusDiv.classList.add('bg-red-600');
        console.error('Ошибка запроса:', err);
      } finally {
        if (submitBtn) {
          submitBtn.classList.remove('animate-pulse');
          submitBtn.disabled = false;
        }
        
        // Автоматически скрыть уведомление через 3 секунды
        setTimeout(() => {
          statusDiv.animate([
            { opacity: 1 },
            { opacity: 0 }
          ], { duration: 500, easing: 'ease-out' }).onfinish = () => {
            statusDiv.style.display = 'none';
          };
        }, 3000);
      }
    });
  }
  
  // === Проект → Назначенные пользователи ===
  const projectSelect = document.getElementById("project_id");
  const assignedSelect = document.getElementById("assigned_to");
  if (projectSelect && assignedSelect) {
    projectSelect.addEventListener("change", () => {
      const projectId = projectSelect.value;
      
      // Анимация загрузки
      assignedSelect.disabled = true;
      assignedSelect.classList.add('opacity-50');
      
      // Добавляем опцию загрузки
      const loadingOption = document.createElement('option');
      loadingOption.textContent = 'Загрузка...';
      assignedSelect.innerHTML = '';
      assignedSelect.appendChild(loadingOption);
      
      fetch(`/get_project_users/${projectId}`)
        .then(response => response.json())
        .then(users => {
          // Плавная анимация обновления списка
          assignedSelect.classList.add('opacity-0');
          
          setTimeout(() => {
            assignedSelect.innerHTML = '<option value="">Не назначен</option>';
            users.forEach(user => {
              const option = document.createElement("option");
              option.value = user.id;
              option.textContent = user.username;
              assignedSelect.appendChild(option);
            });
            
            assignedSelect.disabled = false;
            assignedSelect.classList.remove('opacity-50');
            assignedSelect.classList.remove('opacity-0');
            assignedSelect.classList.add('opacity-100');
          }, 300);
        })
        .catch(error => {
          console.error('Ошибка загрузки пользователей:', error);
          assignedSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
          assignedSelect.disabled = false;
          assignedSelect.classList.remove('opacity-50');
        });
    });
  }
  
  // === Модальное окно для редактирования комментария ===
  // Создаем модальное окно для редактирования комментария, если его еще нет
  let editCommentModal = document.getElementById('editCommentModal');
  if (!editCommentModal) {
    const modalHTML = `
      <div id="editCommentModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center hidden">
        <div class="bg-gray-800 p-6 rounded-lg shadow-xl w-full max-w-lg transform transition-all">
          <h3 class="text-lg font-semibold text-white mb-4">Редактировать комментарий</h3>
          <form id="editCommentForm">
            <input type="hidden" id="editCommentId">
            <textarea id="editCommentContent" rows="4" class="w-full p-3 rounded bg-gray-900 text-white border border-gray-700 focus:border-blue-400" required></textarea>
            <div class="flex justify-end mt-4 space-x-3">
              <button type="button" id="cancelEditComment" class="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 transition">Отмена</button>
              <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 transition">Сохранить</button>
            </div>
          </form>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    editCommentModal = document.getElementById('editCommentModal');
    
    // Обработчик закрытия модального окна
    document.getElementById('cancelEditComment').addEventListener('click', () => {
      editCommentModal.classList.add('hidden');
    });
    
    // Обработчик отправки формы редактирования
    document.getElementById('editCommentForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const commentId = document.getElementById('editCommentId').value;
      const content = document.getElementById('editCommentContent').value.trim();
      
      if (!content) {
        showNotification('Комментарий не может быть пустым', 'error');
        return;
      }
      
      try {
        const response = await fetch(`/comment/${commentId}/edit`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content })
        });
        
        const data = await response.json();
        
        if (data.success) {
          // Получаем обновленный HTML комментария с сервера
          const htmlResponse = await fetch(`/comment/${commentId}/html`);
          const html = await htmlResponse.text();
          
          // Находим текущий элемент комментария
          const commentThread = document.querySelector(`[data-comment-id="${commentId}"]`);
          if (commentThread) {
            // Создаем временный элемент для нового HTML
            const wrapper = document.createElement("div");
            wrapper.innerHTML = html;
            const newCommentEl = wrapper.firstElementChild;
            
            // Сохраняем высоту и другие размеры текущего комментария
            const oldHeight = commentThread.offsetHeight;
            const oldWidth = commentThread.offsetWidth;
            
            // Заменяем старый комментарий на новый
            commentThread.parentNode.replaceChild(newCommentEl, commentThread);
            
            // Добавляем обработчик для кнопки редактирования нового комментария
            const editBtn = newCommentEl.querySelector('.edit-comment-btn');
            if (editBtn) {
              attachEditButtonHandler(editBtn);
            }
            
            // Анимация обновления комментария
            newCommentEl.style.backgroundColor = 'rgba(59, 130, 246, 0.2)';
            setTimeout(() => {
              newCommentEl.style.transition = 'background-color 1s ease-out';
              newCommentEl.style.backgroundColor = 'transparent';
            }, 50);
          }
          
          // Закрываем модальное окно
          editCommentModal.classList.add('hidden');
          
          // Показываем уведомление об успешном обновлении
          showNotification('Комментарий успешно обновлен', 'success');
        } else {
          showNotification(data.error || 'Ошибка при обновлении комментария', 'error');
        }
      } catch (error) {
        console.error('Ошибка при обновлении комментария:', error);
        showNotification('Произошла ошибка при обновлении комментария', 'error');
      }
    });
  }
  
  // Функция для обработки клика по кнопке редактирования
  function attachEditButtonHandler(btn) {
    btn.addEventListener('click', () => {
      const commentId = btn.dataset.commentId;
      const commentContent = btn.dataset.commentContent;
      
      // Заполняем форму редактирования
      document.getElementById('editCommentId').value = commentId;
      // Декодируем HTML-атрибуты перед установкой в поле ввода
      document.getElementById('editCommentContent').value = commentContent.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
      
      // Показываем модальное окно с анимацией
      editCommentModal.classList.remove('hidden');
      const modalContent = editCommentModal.querySelector('div');
      modalContent.classList.add('scale-95', 'opacity-0');
      setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
      }, 10);
      
      // Фокус на поле ввода
      document.getElementById('editCommentContent').focus();
    });
  }
  
  // Обработчики кнопок редактирования комментариев
  document.querySelectorAll('.edit-comment-btn').forEach(btn => {
    attachEditButtonHandler(btn);
  });
  
  // Делегирование событий для динамически добавленных кнопок редактирования
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('edit-comment-btn') || 
        e.target.closest('.edit-comment-btn')) {
      const btn = e.target.classList.contains('edit-comment-btn') ? 
                 e.target : e.target.closest('.edit-comment-btn');
      
      // Проверяем, есть ли уже обработчик
      const hasHandler = btn.getAttribute('data-has-handler');
      if (!hasHandler) {
        attachEditButtonHandler(btn);
        btn.setAttribute('data-has-handler', 'true');
        btn.click(); // Имитируем клик для открытия формы редактирования
      }
    }
  });
  
  // === Логика кнопки ответа ===
  const textarea = document.getElementById("commentContent");
  const parentIdInput = document.getElementById("parent_id");
  
  // Функция для обработки клика по кнопке ответа
  function attachReplyButtonHandler(btn) {
    btn.addEventListener("click", () => {
      const { username, userid, commentid } = btn.dataset;
      
      // Анимация фокуса на форме комментария
      const commentForm = document.getElementById('commentForm');
      if (commentForm) {
        commentForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
        commentForm.classList.add('ring-2', 'ring-gray-500');
        setTimeout(() => commentForm.classList.remove('ring-2', 'ring-gray-500'), 1000);
      }
      
      textarea.value = '';
      parentIdInput.value = commentid;
      textarea.focus();
      
      // Анимация текстового поля
      textarea.animate([
        { boxShadow: '0 0 0 3px rgba(107, 114, 128, 0.5)' },
        { boxShadow: 'none' }
      ], { duration: 800, easing: 'ease-out' });
    });
  }
  
  // Добавляем обработчики для существующих кнопок ответа
  document.querySelectorAll(".reply-btn").forEach(btn => {
    attachReplyButtonHandler(btn);
  });
  
  // Делегирование событий для динамически добавленных кнопок ответа
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('reply-btn') || 
        e.target.closest('.reply-btn')) {
      const btn = e.target.classList.contains('reply-btn') ? 
                 e.target : e.target.closest('.reply-btn');
      
      // Проверяем, есть ли уже обработчик
      const hasHandler = btn.getAttribute('data-has-handler');
      if (!hasHandler) {
        attachReplyButtonHandler(btn);
        btn.setAttribute('data-has-handler', 'true');
        btn.click(); // Имитируем клик для активации ответа
      }
    }
  });

  // === Обработчики кнопок удаления комментариев ===
  function attachDeleteButtonHandler(btn) {
    btn.addEventListener('click', async function(e) {
      e.preventDefault();
      
      if (!confirm('Вы уверены, что хотите удалить этот комментарий?')) {
        return;
      }
      
      const commentId = btn.dataset.commentId;
      const commentThread = document.querySelector(`[data-comment-id="${commentId}"]`);
      
      try {
        const response = await fetch(`/comment/${commentId}/delete`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        
        const data = await response.json();
        
        if (data.success) {
          // Анимация удаления комментария
          commentThread.style.transition = 'all 0.5s ease-out';
          commentThread.style.opacity = '0';
          commentThread.style.transform = 'translateY(-10px)';
          
          setTimeout(() => {
            commentThread.remove();
            showNotification('Комментарий успешно удален', 'success');
          }, 500);
        } else {
          showNotification(data.error || 'Ошибка при удалении комментария', 'error');
        }
      } catch (error) {
        console.error('Ошибка при удалении комментария:', error);
        showNotification('Произошла ошибка при удалении комментария', 'error');
      }
    });
  }
  
  // Добавляем обработчики для существующих кнопок удаления
  document.querySelectorAll('.delete-comment-btn').forEach(btn => {
    attachDeleteButtonHandler(btn);
  });
  
  // Делегирование событий для динамически добавленных кнопок удаления
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('delete-comment-btn') || 
        e.target.closest('.delete-comment-btn')) {
      const btn = e.target.classList.contains('delete-comment-btn') ? 
                 e.target : e.target.closest('.delete-comment-btn');
      
      // Проверяем, есть ли уже обработчик
      const hasHandler = btn.getAttribute('data-has-handler');
      if (!hasHandler) {
        attachDeleteButtonHandler(btn);
        btn.setAttribute('data-has-handler', 'true');
        btn.click(); // Имитируем клик для активации удаления
      }
    }
  });
  
  // === AJAX отправка комментария ===
  const commentForm = document.getElementById("commentForm");
  if (commentForm) {
    commentForm.addEventListener("submit", function (e) {
      e.preventDefault();
      
      // Анимация кнопки отправки
      const submitBtn = commentForm.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Отправка...';
        submitBtn.disabled = true;
      }
      
      const formData = new FormData(commentForm);
      const taskId = commentForm.action.split('/task/')[1].split('/')[0];
      
      fetch(`/comment/task/${taskId}`, {
        method: 'POST',
        body: formData
      })
      .then(async res => {
        const data = await res.json();
        if (!data.success) {
          showNotification(data.error || 'Ошибка сервера', 'error');
          return;
        }
      
        const newCommentId = data.comment.id;
      
        // Получаем HTML с сервера
        const html = await fetch(`/comment/${newCommentId}/html`).then(r => r.text());
      
        // Создаём временный элемент
        const wrapper = document.createElement("div");
        wrapper.innerHTML = html;
        const commentEl = wrapper.firstElementChild;
        
        // Добавляем класс для анимации
        commentEl.classList.add('opacity-0', 'transform', 'translate-y-4');
      
        // Вставляем в DOM
        const isReply = !!data.comment.parent_id;
        if (isReply) {
          const parent = document.querySelector(`[data-comment-id='${data.comment.parent_id}']`);
          let repliesBlock = parent.querySelector('.space-y-4');
          if (!repliesBlock) {
            repliesBlock = document.createElement('div');
            repliesBlock.className = 'mt-4 space-y-4';
            parent.appendChild(repliesBlock);
          }
          repliesBlock.appendChild(commentEl);
        } else {
          document.getElementById("comments-list").appendChild(commentEl);
        }
        
        // Анимируем появление комментария
        setTimeout(() => {
          commentEl.classList.remove('opacity-0', 'transform', 'translate-y-4');
          commentEl.classList.add('transition-all', 'duration-500', 'ease-out', 'opacity-100');
        }, 10);
      
        // Добавляем обработчик для кнопки "Ответить"
        const replyBtn = commentEl.querySelector('.reply-btn');
        if (replyBtn) {
          attachReplyButtonHandler(replyBtn);
        }
        
        // Добавляем обработчик для кнопки редактирования
        const editBtn = commentEl.querySelector('.edit-comment-btn');
        if (editBtn) {
          attachEditButtonHandler(editBtn);
        }
      
        commentForm.reset();
        parentIdInput.value = "";
        
        // Показываем уведомление об успешной отправке
        showNotification('Комментарий успешно добавлен', 'success');
      })
      .catch(err => {
        console.error("Ошибка отправки:", err);
        showNotification("Ошибка отправки комментария", 'error');
      })
      .finally(() => {
        // Восстанавливаем кнопку
        if (submitBtn) {
          submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i> Отправить';
          submitBtn.disabled = false;
        }
      });
    });
  }

  // === Визуальное восстановление дерева комментариев ===
  document.querySelectorAll('.comment-thread[data-is-reply="1"]').forEach(reply => {
    const parentId = reply.dataset.parentId;
    const parent = document.querySelector(`.comment-thread[data-is-reply="0"][data-comment-id="${parentId}"]`);
  
    if (parent) {
      // Добавляем reply-container если ещё не добавлен
      let replyContainer = parent.querySelector('.space-y-4');
      if (!replyContainer) {
        replyContainer = document.createElement('div');
        replyContainer.classList.add('mt-4', 'space-y-4');
        parent.appendChild(replyContainer);
      }
  
      // Вставляем ответ внутрь reply-container
      replyContainer.appendChild(reply);
    }
  });
  
  // Код для Drag and Drop перенесен в kanban.html
  
  // === Вспомогательные функции ===
  
  // Инициализация анимаций
  function initializeAnimations() {
    // Анимация заголовка
    const title = document.querySelector('.kanban-title');
    if (title) {
      setTimeout(() => {
        title.classList.add('visible');
      }, 100);
    }

    // Анимация колонок
    const columns = document.querySelectorAll('.kanban-column');
    columns.forEach((column, index) => {
      setTimeout(() => {
        column.classList.add('visible');
      }, 600 + (index * 200));
    });

    // Анимация кнопки создания задачи
    const createButton = document.querySelector('.create-task-btn');
    if (createButton) {
      setTimeout(() => {
        createButton.classList.add('visible');
      }, 1400);
    }
    
    // Анимация наведения для кнопок
    document.querySelectorAll('.btn, .btn-sm, .btn-primary').forEach(btn => {
      btn.addEventListener('mouseenter', () => {
        btn.style.transform = 'translateY(-2px)';
      });
      
      btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'translateY(0)';
      });
    });
  }
  
  // Функция для отображения уведомлений
  function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50 transform transition-all duration-500 ease-out translate-y-20 opacity-0`;
    
    // Устанавливаем цвет в зависимости от типа
    if (type === 'success') {
      notification.classList.add('bg-green-600', 'text-white');
      notification.innerHTML = `<i class="fas fa-check-circle mr-2"></i> ${message}`;
    } else if (type === 'error') {
      notification.classList.add('bg-red-600', 'text-white');
      notification.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i> ${message}`;
    } else {
      notification.classList.add('bg-gray-700', 'text-white');
      notification.innerHTML = `<i class="fas fa-info-circle mr-2"></i> ${message}`;
    }
    
    // Добавляем на страницу
    document.body.appendChild(notification);
    
    // Анимируем появление
    setTimeout(() => {
      notification.classList.remove('translate-y-20', 'opacity-0');
    }, 10);
    
    // Автоматически скрываем через 3 секунды
    setTimeout(() => {
      notification.classList.add('translate-y-20', 'opacity-0');
      setTimeout(() => {
        notification.remove();
      }, 500);
    }, 3000);
  }
});


// === AJAX отправка сообщений в ленту команды ===
const feedForm = document.querySelector('form[action*="post_feed_comment"]');
if (feedForm) {
feedForm.addEventListener('submit', function(e) {
e.preventDefault();

// Анимация кнопки отправки
const submitBtn = feedForm.querySelector('button');
if (submitBtn) {
submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Отправка...';
submitBtn.disabled = true;
}

const formData = new FormData(feedForm);

fetch(feedForm.action, {
method: 'POST',
headers: {
  'X-Requested-With': 'XMLHttpRequest'
},
body: formData
})
.then(response => response.json())
.then(data => {
if (data.success) {
// Очищаем поле ввода
feedForm.querySelector('input[name="content"]').value = '';

// Получаем текущее время для отображения
const now = new Date();
const formattedDate = now.toLocaleDateString('ru-RU') + ' ' + 
                    now.toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'});

// Создаем элемент нового сообщения
const newMessage = document.createElement('li');
newMessage.className = 'bg-zinc-700 p-3 rounded-lg shadow text-sm opacity-0 transform translate-y-4';

// Заполняем содержимое сообщения
newMessage.innerHTML = `
<a href="/user/${data.comment.author.id}" class="text-white hover:text-gray-300">
  ${data.comment.author.username}
</a>
<p class="text-slate-300 mt-1">${data.comment.content}</p>
<div class="text-xs text-gray-500 mt-1">${formattedDate}</div>
`;

// Находим список сообщений
// Используем более надежный способ поиска списка сообщений
const feedHeading = Array.from(document.querySelectorAll('h2')).find(h => h.textContent.includes('Лента команды'));
if (!feedHeading) {
console.error('Не удалось найти заголовок ленты команды');
return;
}

// Находим список после заголовка и формы
let feedList = feedHeading.nextElementSibling;
if (feedList.tagName.toLowerCase() === 'form') {
feedList = feedList.nextElementSibling;
}

// Если список пуст, удаляем сообщение о пустом списке
if (feedList.tagName.toLowerCase() === 'p' && feedList.textContent.includes('Сообщений пока нет')) {
// Создаем новый список
const newList = document.createElement('ul');
newList.className = 'space-y-3';
newList.appendChild(newMessage);
feedList.parentNode.replaceChild(newList, feedList);
} else {
// Добавляем сообщение в начало списка
feedList.insertBefore(newMessage, feedList.firstChild);
}

// Анимируем появление сообщения
setTimeout(() => {
newMessage.classList.remove('opacity-0', 'transform', 'translate-y-4');
newMessage.classList.add('transition-all', 'duration-500', 'ease-out', 'opacity-100');
}, 10);

// Показываем уведомление об успешной отправке
showNotification('Сообщение успешно отправлено', 'success');
} else {
showNotification(data.error || 'Ошибка при отправке сообщения', 'error');
}
})
.catch(error => {
console.error('Ошибка при отправке сообщения:', error);
showNotification('Произошла ошибка при отправке сообщения', 'error');
})
.finally(() => {
// Восстанавливаем кнопку
if (submitBtn) {
submitBtn.innerHTML = 'Отправить';
submitBtn.disabled = false;
}
});
});
  }
  
  // === Визуальное восстановление дерева комментариев ===
  document.querySelectorAll('.comment-thread[data-is-reply="1"]').forEach(reply => {
    const parentId = reply.dataset.parentId;
    const parent = document.querySelector(`.comment-thread[data-is-reply="0"][data-comment-id="${parentId}"]`);
  
    if (parent) {
      // Добавляем reply-container если ещё не добавлен
      let replyContainer = parent.querySelector('.space-y-4');
      if (!replyContainer) {
        replyContainer = document.createElement('div');
        replyContainer.classList.add('mt-4', 'space-y-4');
        parent.appendChild(replyContainer);
      }
  
      // Вставляем ответ внутрь reply-container
      replyContainer.appendChild(reply);
    }
  });
  
  // Код для Drag and Drop перенесен в kanban.html
  
  // === Вспомогательные функции ===
  
  // Инициализация анимаций
  function initializeAnimations() {
    // Анимация заголовка
    const title = document.querySelector('.kanban-title');
    if (title) {
      setTimeout(() => {
        title.classList.add('visible');
      }, 100);
    }

    // Анимация колонок
    const columns = document.querySelectorAll('.kanban-column');
    columns.forEach((column, index) => {
      setTimeout(() => {
        column.classList.add('visible');
      }, 600 + (index * 200));
    });

    // Анимация кнопки создания задачи
    const createButton = document.querySelector('.create-task-btn');
    if (createButton) {
      setTimeout(() => {
        createButton.classList.add('visible');
      }, 1400);
    }
    
    // Анимация наведения для кнопок
    document.querySelectorAll('.btn, .btn-sm, .btn-primary').forEach(btn => {
      btn.addEventListener('mouseenter', () => {
        btn.style.transform = 'translateY(-2px)';
      });
      
      btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'translateY(0)';
      });
    });
  }
  
  // Функция для отображения уведомлений
  function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50 transform transition-all duration-500 ease-out translate-y-20 opacity-0`;
    
    // Устанавливаем цвет в зависимости от типа
    if (type === 'success') {
      notification.classList.add('bg-green-600', 'text-white');
      notification.innerHTML = `<i class="fas fa-check-circle mr-2"></i> ${message}`;
    } else if (type === 'error') {
      notification.classList.add('bg-red-600', 'text-white');
      notification.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i> ${message}`;
    } else {
      notification.classList.add('bg-gray-700', 'text-white');
      notification.innerHTML = `<i class="fas fa-info-circle mr-2"></i> ${message}`;
    }
    
    // Добавляем на страницу
    document.body.appendChild(notification);
    
    // Анимируем появление
    setTimeout(() => {
      notification.classList.remove('translate-y-20', 'opacity-0');
    }, 10);
    
    // Автоматически скрываем через 3 секунды
    setTimeout(() => {
      notification.classList.add('translate-y-20', 'opacity-0');
      setTimeout(() => {
        notification.remove();
      }, 500);
    }, 3000);
  }
;

