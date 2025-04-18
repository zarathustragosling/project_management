
  document.addEventListener('DOMContentLoaded', function () {


    
  

    function highlightMentions(text) {
        return text.replace(/<@(\d+):([\wА-яёЁ.-]+)>/g, (_, id, name) =>
          `<a href="/user/${id}" class="text-blue-400 hover:underline">@${name}</a>`
        );
      }



    // === Drag'n'Drop ===
    const columns = document.querySelectorAll('.kanban-column');
    const tasks = document.querySelectorAll('.task-card');
  
    tasks.forEach(task => {
      task.setAttribute('draggable', true);
      task.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', task.dataset.taskId);
        task.classList.add('dragging');
        task.style.opacity = '0.5';
      });
      task.addEventListener('dragend', () => {
        task.classList.remove('dragging');
        task.style.opacity = '1';
      });
    });
  
    columns.forEach(column => {
      column.addEventListener('dragover', (e) => {
        e.preventDefault();
        column.classList.add('dragover');
      });
      column.addEventListener('dragleave', () => {
        column.classList.remove('dragover');
      });
      column.addEventListener('drop', (e) => {
        e.preventDefault();
        column.classList.remove('dragover');
        const taskId = e.dataTransfer.getData('text/plain');
        const taskCard = document.querySelector(`.task-card[data-task-id='${taskId}']`);
        if (taskCard && column !== taskCard.parentElement) {
          const statusKey = column.id.replace('-column', '').toUpperCase().replace('-', '_');
          column.appendChild(taskCard);
          fetch(`/update_task_status/${taskId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: statusKey })
          })
          .then(res => res.json())
          .then(data => {
            if (!data.success) alert('Ошибка обновления: ' + data.error);
          })
          .catch(error => console.error('Ошибка запроса:', error));
        }
      });
    });
  
    // === Patch Task ===
    const form = document.getElementById('editTaskForm');
    if (form) {
      form.addEventListener('submit', async function (e) {
        e.preventDefault();
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
        statusDiv.textContent = 'Сохранение...';
        try {
          const res = await fetch(`/task/${taskId}/update`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          const result = await res.json();
          statusDiv.textContent = result.success ? 'Изменения сохранены ✅' : 'Ошибка ❌';
        } catch (err) {
          statusDiv.textContent = 'Ошибка соединения ❌';
          console.error('Ошибка запроса:', err);
        }
      });
    }
  
    // === Project → Assigned users ===
    const projectSelect = document.getElementById("project_id");
    const assignedSelect = document.getElementById("assigned_to");
    if (projectSelect && assignedSelect) {
      projectSelect.addEventListener("change", () => {
        const projectId = projectSelect.value;
        fetch(`/get_project_users/${projectId}`)
          .then(response => response.json())
          .then(users => {
            assignedSelect.innerHTML = '<option value="">Не назначен</option>';
            users.forEach(user => {
              const option = document.createElement("option");
              option.value = user.id;
              option.textContent = user.username;
              assignedSelect.appendChild(option);
            });
          });
      });
    }
  
     // Reply btn logic (initial)
  const textarea = document.getElementById("commentContent");
  const parentIdInput = document.getElementById("parent_id");
  document.querySelectorAll(".reply-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const { username, userid, commentid } = btn.dataset;
      textarea.value = `<@${userid}:${username}> `;
      parentIdInput.value = commentid;
      textarea.focus();
    });
  });

  // AJAX Comment Submit
  const commentForm = document.getElementById("commentForm");
  if (commentForm) {
    commentForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const formData = new FormData(commentForm);
      const taskId = commentForm.action.split('/task/')[1].split('/')[0];
      fetch(`/task/${taskId}/comment`, {
        method: 'POST',
        body: formData
      })
      // --- Новый блок замены fetch(...).then(...) внутри commentForm.addEventListener

      .then(async res => {
        const data = await res.json();
        if (!data.success) return alert(data.error || 'Ошибка сервера');
      
        const newCommentId = data.comment.id;
      
        // 👇 Получаем HTML с сервера
        const html = await fetch(`/comment/${newCommentId}/html`).then(r => r.text());
      
        // 👇 Создаём временный элемент
        const wrapper = document.createElement("div");
        wrapper.innerHTML = html;
        const commentEl = wrapper.firstElementChild;
      
        // 👇 Вставляем в DOM
        const isReply = !!data.comment.parent_id;
        if (isReply) {
          const parent = document.querySelector(`[data-comment-id='${data.comment.parent_id}']`);
          let repliesBlock = parent.querySelector('.reply-container');
          if (!repliesBlock) {
            repliesBlock = document.createElement('div');
            repliesBlock.className = 'reply-container ml-10 mt-4 space-y-4';
            parent.appendChild(repliesBlock);
          }
          repliesBlock.appendChild(commentEl);
        } else {
          document.getElementById("comments-list").appendChild(commentEl);
        }
      
        // Повесим кнопку "Ответить"
        const replyBtn = commentEl.querySelector('.reply-btn');
        if (replyBtn) {
          replyBtn.addEventListener("click", () => {
            textarea.value = `<@${replyBtn.dataset.userid}:${replyBtn.dataset.username}> `;
            parentIdInput.value = replyBtn.dataset.commentid;
            textarea.focus();
          });
        }
      
        commentForm.reset();
        parentIdInput.value = "";
      })
      
  
      
      .catch(err => {
        console.error("Ошибка отправки:", err);
        alert("Ошибка отправки комментария.");
      });
    });
  }



  // === Визуальное восстановление дерева комментариев ===
document.querySelectorAll('.comment-box[data-is-reply="1"]').forEach(reply => {
    const parentId = reply.dataset.parentId;
    const parent = document.querySelector(`.comment-box[data-is-reply="0"][data-comment-id="${parentId}"]`);
  
    if (parent) {
      // Добавляем reply-container если ещё не добавлен
      let replyContainer = parent.querySelector('.reply-container');
      if (!replyContainer) {
        replyContainer = document.createElement('div');
        replyContainer.classList.add('reply-container', 'ml-10', 'mt-4', 'space-y-2');
        parent.appendChild(replyContainer);
      }
  
      // Вставляем ответ внутрь reply-container
      replyContainer.appendChild(reply);
  
      
    }
  });

  
    

});

