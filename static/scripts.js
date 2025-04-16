
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
      .then(async res => {
        const data = await res.json();
        if (!data.success) return alert(data.error || 'Ошибка сервера');
        const c = data.comment;

        const isReply = !!c.parent_id;

        const commentEl = document.createElement("div");
        commentEl.className = "flex items-start gap-3 mb-4 comment-box";
        commentEl.dataset.commentId = c.id;
        commentEl.dataset.isReply = isReply ? "1" : "0";

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

        const replyButton = !isReply ? `
          <button class="reply-btn text-xs mt-2 text-blue-400 hover:underline"
            data-username="${c.author.username}"
            data-userid="${c.author.id}"
            data-commentid="${c.id}">
            Ответить
          </button>` : '';

        const textHTML = `
          ${replyInfo}
          <p class="text-white mt-1 text-sm">${highlightMentions(c.content)}</p>
          ${c.attachment ? `<a href="/static/uploads/${c.attachment}" class="text-sm text-blue-400 hover:underline block mt-2">📁 ${c.attachment}</a>` : ""}
          ${replyButton}
        `;

        contentBox.appendChild(meta);
        contentBox.insertAdjacentHTML('beforeend', textHTML);
        commentEl.appendChild(avatar);
        commentEl.appendChild(contentBox);

        if (isReply) {
          const parent = document.querySelector(`[data-comment-id='${c.parent_id}']`);
          let repliesBlock = parent?.querySelector('.reply-container');
          if (!repliesBlock) {
            repliesBlock = document.createElement('div');
            repliesBlock.className = 'ml-10 mt-4 space-y-4 reply-container';
            parent.appendChild(repliesBlock);
          }
          repliesBlock.appendChild(commentEl);
        } else {
          document.getElementById("comments-list").appendChild(commentEl);
        }

        if (!isReply) {
          const replyBtn = commentEl.querySelector('.reply-btn');
          if (replyBtn) {
            replyBtn.addEventListener("click", () => {
              textarea.value = `<@${replyBtn.dataset.userid}:${replyBtn.dataset.username}> `;
              parentIdInput.value = replyBtn.dataset.commentid;
              textarea.focus();
            });
          }
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

  
    // === CHARTS: GANTT ===
    const container = document.getElementById("gantt-container");
    const select = document.getElementById("projectSelect");
    let timeline = null;

    function renderGantt(data) {
        // Создаём группы — каждая задача в своей дорожке
        const groups = new vis.DataSet(data.map((t, index) => ({
          id: index,
          content: ''
        })));
      
        // Каждая задача — item, привязанная к своей группе
        const items = new vis.DataSet(data.map((t, index) => ({
          id: t.id,
          content: `<b>${t.name}</b>`,
          start: t.start,
          end: t.end,
          group: index, // 👈 Привязка к дорожке
          className: t.status || '',
          title: `
            <div>
              <strong>${t.name}</strong><br/>
              📅 ${t.start} → ${t.end}<br/>
              📝 ${t.description || 'Без описания'}
            </div>
          `
        })));
      
        const now = new Date();
        const options = {
          currentTime: now,
          showCurrentTime: true,
          stack: false, // важно: stack = false → группировка работает
          zoomable: true,
          moveable: true,
          editable: false,
          margin: { item: 20, axis: 40 },
          orientation: 'top',
          start: new Date(new Date().setDate(new Date().getDate() - 5)),
          end: new Date(new Date().setDate(new Date().getDate() + 30)),
          timeAxis: { scale: 'day', step: 1 }
        };
      
        if (timeline) timeline.destroy();
        timeline = new vis.Timeline(container, items, groups, options); // 👈 groups сюда
      }
      

    async function loadGantt(projectId) {
      try {
        const res = await fetch(`/api/project/${projectId}/gantt`);
        const data = await res.json();
        renderGantt(data);
      } catch (err) {
        console.error("Ошибка загрузки диаграммы:", err);
      }
    }

    select.addEventListener("change", () => loadGantt(select.value));
    loadGantt(select.value); // первичная загрузка


});

