
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
  
    // === Reply btn logic (initial) ===
    const textarea = document.getElementById("commentContent");
    const parentIdInput = document.getElementById("parent_id");
    document.querySelectorAll(".reply-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const username = btn.dataset.username;
        const userId = btn.dataset.userid;
        const commentId = btn.dataset.commentid;
        textarea.value = `<@${userId}:${username}> `;
        parentIdInput.value = commentId;
        textarea.focus();
      });
    });
  
    // === AJAX Comment Submit ===
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
        .then(async res => {
          if (!res.ok) throw new Error("HTTP " + res.status);
          const data = await res.json();
          if (data.success) {
            const c = data.comment;
            const commentEl = document.createElement("div");
            commentEl.className = "flex items-start gap-3 mb-4";
            commentEl.dataset.commentId = c.id;
            const avatar = document.createElement("img");
            avatar.src = c.author.avatar;
            avatar.alt = "avatar";
            avatar.className = "w-8 h-8 rounded-full object-cover mt-1";
            const contentBox = document.createElement("div");
            contentBox.className = "bg-gray-800 p-4 rounded-lg w-full";
            const meta = document.createElement("div");
            meta.className = "flex items-center gap-2";
            meta.innerHTML = `
              <a href="/user/${c.author.id}" class="text-sm font-bold text-white hover:underline">${c.author.username}</a>
              <span class="text-xs text-gray-400">${c.created_at}</span>
            `;
            const replyInfo = c.parent_author ? `
              <div class="text-xs text-blue-300 mb-1">
                Ответ на <a href="/user/${c.parent_id}" class="hover:underline">@${c.parent_author}</a>
              </div>` : '';
            const textHTML = `
              ${replyInfo}
              <p class="text-white mt-1 text-sm">${highlightMentions(c.content)}</p>
              ${c.attachment ? `<a href="/static/uploads/${c.attachment}" class="text-sm text-blue-400 hover:underline block mt-2">📁 ${c.attachment}</a>` : ""}
              <button class="reply-btn text-xs mt-2 text-blue-400 hover:underline"
                      data-username="${c.author.username}"
                      data-userid="${c.author.id}"
                      data-commentid="${c.id}">Ответить</button>
            `;
            contentBox.appendChild(meta);
            contentBox.insertAdjacentHTML('beforeend', textHTML);
            commentEl.appendChild(avatar);
            commentEl.appendChild(contentBox);
  
            if (c.parent_id) {
              const parent = document.querySelector(`[data-comment-id='${c.parent_id}']`);
              let repliesBlock = parent?.querySelector('.reply-container');
              if (!repliesBlock) {
                repliesBlock = document.createElement('div');
                repliesBlock.className = 'ml-10 mt-4 space-y-4 reply-container';
                parent.appendChild(repliesBlock);
              }
              repliesBlock.appendChild(commentEl);
              if (!parent.querySelector(".toggle-thread")) {
                const toggle = document.createElement("button");
                toggle.type = "button";
                toggle.className = "toggle-thread text-xs text-gray-400 ml-2";
                toggle.textContent = "Свернуть ветку";
                toggle.addEventListener("click", () => {
                  repliesBlock.classList.toggle("hidden");
                  toggle.textContent = repliesBlock.classList.contains("hidden") ? "Показать ветку" : "Свернуть ветку";
                });
                parent.querySelector(".bg-gray-800")?.appendChild(toggle);
              }
            } else {
              document.getElementById("comments-list").appendChild(commentEl);
            }
  
            const newReplyBtn = commentEl.querySelector('.reply-btn');
            if (newReplyBtn) {
              newReplyBtn.addEventListener("click", () => {
                textarea.value = `<@${newReplyBtn.dataset.userid}:${newReplyBtn.dataset.username}> `;
                parentIdInput.value = newReplyBtn.dataset.commentid;
                textarea.focus();
              });
            }
  
            commentForm.reset();
            parentIdInput.value = "";
          } else {
            alert(data.error || "Ошибка сервера");
          }
        })
        .catch(err => {
          console.error("Ошибка отправки:", err);
          alert("Ошибка отправки комментария.");
        });
      });
    }

    document.querySelectorAll('.comment-box[data-is-reply="1"] .reply-btn')
    .forEach(btn => btn.remove());
  
 

    document.querySelectorAll('.comment-box').forEach(comment => {
        const repliesBlock = comment.querySelector('.replies');
        if (repliesBlock && repliesBlock.children.length > 0) {
          const toggleBtn = document.createElement('button');
          toggleBtn.textContent = 'Свернуть ветку';
          toggleBtn.className = 'toggle-thread text-xs text-blue-400 mt-2 block';
    
          toggleBtn.addEventListener('click', () => {
            repliesBlock.classList.toggle('hidden');
            toggleBtn.textContent = repliesBlock.classList.contains('hidden')
              ? 'Показать ветку'
              : 'Свернуть ветку';
          });
    
          comment.appendChild(toggleBtn);
        }
      });
    
      // Обработчик кнопки "Ответить"
      document.querySelectorAll('.reply-btn').forEach(button => {
        button.addEventListener('click', () => {
          const username = button.dataset.username;
          const userId = button.dataset.userid;
          const commentId = button.dataset.commentid;
    
          const input = document.querySelector('#comment-input');
          input.value = `<@${userId}:${username}> `;
          input.focus();
    
          const parentIdInput = document.querySelector('#parent-comment-id');
          if (parentIdInput) parentIdInput.value = commentId;
        });
      });



      

  });
  