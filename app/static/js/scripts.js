// scripts.js

document.addEventListener('DOMContentLoaded', () => {
    // Handle task completion
    document.querySelectorAll('.complete-task-btn').forEach(button => {
        button.addEventListener('click', () => {
            const taskId = button.dataset.taskId;
            fetch(`/tasks/${taskId}/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            })
            .then(response => {
                if (response.ok) {
                    alert('Task marked as completed.');
                    location.reload();
                } else {
                    alert('Failed to mark task as completed.');
                }
            });
        });
    });

    // Handle file upload
    document.querySelectorAll('.upload-file-form').forEach(form => {
        form.addEventListener('submit', event => {
            event.preventDefault();
            const taskId = form.dataset.taskId;
            const fileInput = form.querySelector('input[type="file"]');
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            fetch(`/tasks/${taskId}/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    alert('File uploaded successfully.');
                    location.reload();
                } else {
                    alert('File upload failed.');
                }
            });
        });
    });
});
