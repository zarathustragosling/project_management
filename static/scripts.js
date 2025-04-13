document.addEventListener('DOMContentLoaded', function () {
    const columns = document.querySelectorAll('.kanban-column');
    const tasks = document.querySelectorAll('.task-card');


    document.querySelectorAll('.reply-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const form = btn.nextElementSibling;
            form.classList.toggle('hidden');
        });
    });


    const replyButtons = document.querySelectorAll('.reply-btn');
    const textarea = document.getElementById('commentContent');
    const parentInput = document.getElementById('parent_id');
  
    replyButtons.forEach(button => {
      button.addEventListener('click', () => {
        const username = button.dataset.username;
        const parentId = button.dataset.parentId;
  
        textarea.value = `@${username} ` + textarea.value;
        textarea.focus();
        parentInput.value = parentId;
      });
    });



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
                    if (!data.success) {
                        alert('Ошибка обновления: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Ошибка запроса:', error);
                });
            }
        });
    });

    const form = document.getElementById('editTaskForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
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

                if (result.success) {
                    statusDiv.textContent = 'Изменения сохранены ✅';
                } else {
                    statusDiv.textContent = 'Ошибка ❌';
                    console.error(result.error);
                }
            } catch (err) {
                statusDiv.textContent = 'Ошибка соединения ❌';
                console.error('Ошибка запроса:', err);
            }
        });
    }

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
});
