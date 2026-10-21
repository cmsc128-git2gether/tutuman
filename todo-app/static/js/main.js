// For New Task Modal
const taskModal = document.getElementById("taskModal");
const newTaskBtn = document.getElementById("newTaskBtn");
const closeTaskModal = document.getElementById("closeTaskModal");
const cancelTask = document.getElementById("cancelTask");

// Open modal
function openTaskModal() {
    taskModal.classList.add("show");
}

// Close modal
function closeTaskModalView() {
    taskModal.classList.remove("show");
}

// New Task button
if (newTaskBtn) {
    newTaskBtn.addEventListener("click", openTaskModal);
}

// Close button
if (closeTaskModal) {
    closeTaskModal.addEventListener("click", closeTaskModalView);
}

// Cancel button
if (cancelTask) {
    cancelTask.addEventListener("click", closeTaskModalView);
}

// Close when clicking outside the modal
if (taskModal) {
    taskModal.addEventListener("click", function (event) {
        if (event.target === taskModal) {
            closeTaskModalView();
        }
    });
}

// For Editing Existing Task Modal
const editTaskModal = document.getElementById("editTaskModal");
const editTaskForm = document.getElementById("editTaskForm");
const closeEditBtn = document.getElementById("closeEditModal");
const cancelEditBtn = document.getElementById("cancelEdit");

// Get Exisiting Elements
document.querySelectorAll(".edit-btn").forEach(button => {
    button.addEventListener("click", function () {
        const id = this.dataset.taskId;
        document.getElementById("edit-title").value = this.dataset.title;
        document.getElementById("edit-due_date").value = this.dataset.dueDate;
        document.getElementById("edit-due_time").value = this.dataset.dueTime;
        document.querySelectorAll('input[name="priority"]').forEach(radio => {
            radio.checked = radio.value === (this.dataset.priority || "");
        });
        document.querySelectorAll('input[name="tag"]').forEach(radio => {
            radio.checked = radio.value === (this.dataset.tag || "");
        });

        editTaskForm.action = `/edit/${id}`;
        editTaskModal.classList.add("show");

    });
});

// Close Modal
function closeEditModal() {
    editTaskModal.classList.remove("show");
}

// Close Edit
if (closeEditBtn) {
    closeEditBtn.addEventListener("click", closeEditModal);
}

// Cancel Edit
if (cancelEditBtn) {
    cancelEditBtn.addEventListener("click", closeEditModal);
}

// Edit
if (editTaskModal) {
    editTaskModal.addEventListener("click", function (event) {
        if (event.target === editTaskModal) {
            closeEditModal();
        }
    });
}

// ------------- LAB 2 FUNCTION ------------- //

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.auth-form');
    if (!form) return;

    form.noValidate = true;

    // show / hide password
    form.querySelectorAll('.toggle-password').forEach((button) => {
        const input = button.parentElement.querySelector('input');
        const icon = button.querySelector('i');

        button.addEventListener('click', () => {
            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            icon.className = showing ? 'bi bi-eye' : 'bi bi-eye-slash';
            button.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
        });
    });

    // form validation
    const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    const isRegister = !!form.elements.confirm_password;

    // rules returns a message or ''
    const rules = {
        email(value) {
            if (!value.trim()) return 'Please enter your email.';
            if (!EMAIL_PATTERN.test(value.trim())) return 'Please enter a valid email address.';
            return '';
        },
        display_name(value) {
            return value.trim() ? '' : 'Please enter your display name.';
        },
        password(value) {
            if (!value) return 'Please enter a password.';
            const min = form.elements.password.minLength;
            if (min > 0 && value.length < min) {
                return `Password must be at least ${min} characters.`;
            }
            return '';
        },
        confirm_password(value) {
            if (!value) return 'Please confirm your password.';
            if (value !== form.elements.password.value) return 'Passwords do not match.';
            return '';
        },
    };

    // write error message 
    function showError(input, message) {
        const errorEl = input.closest('.field').querySelector('.field-error');
        errorEl.textContent = message;
        input.classList.toggle('invalid', message !== '');
        input.setAttribute('aria-invalid', message !== '');
    }

    // validate field using rules 
    function validateField(input) {
        const rule = rules[input.name];
        if (!rule) return '';
        const message = rule(input.value);
        showError(input, message);
        return message;
    }

    const fields = Array.from(form.querySelectorAll('input')).filter((i) => rules[i.name]);

    fields.forEach((input) => {
        // check when the user leaves a field
        input.addEventListener('blur', () => validateField(input));

        // recheck instantly as they fix it
        input.addEventListener('input', () => {
            if (input.name === 'email' || input.name === 'password') {
                // only show errors after the user has typed something
                if (input.value) validateField(input);
                else showError(input, '');
            } else if (input.classList.contains('invalid')) {
                validateField(input);
            }

            // changing the password can fix or break the confirm field
            if (input.name === 'password' && form.elements.confirm_password?.value) {
                validateField(form.elements.confirm_password);
            }
        });
    });

    // block the submit if anything is invalid
    form.addEventListener('submit', (event) => {
        let firstInvalid = null;

        fields.forEach((input) => {
            if (validateField(input) && !firstInvalid) firstInvalid = input;
        });

        if (firstInvalid) {
            event.preventDefault();
            firstInvalid.focus();
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    if (!document.querySelector('.profile-page')) return;

    // ---------- show / hide password ----------
    document.querySelectorAll('.profile-page .toggle-password').forEach((button) => {
        const input = button.parentElement.querySelector('input');
        const icon = button.querySelector('i');

        button.addEventListener('click', () => {
            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            icon.className = showing ? 'bi bi-eye' : 'bi bi-eye-slash';
            button.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
        });
    });

    // ---------- validation rules ----------
    const rules = {
        display_name(value) {
            const name = value.trim();
            if (!name) return 'Please enter your display name.';
            if (name.length > 100) return 'Display name must be 100 characters or fewer.';
            return '';
        },
        current_password(value) {
            return value ? '' : 'Please enter your current password.';
        },
        new_password(value, form) {
            if (!value) return 'Please enter a new password.';
            const min = form.elements.new_password.minLength;
            if (min > 0 && value.length < min) {
                return `Password must be at least ${min} characters.`;
            }
            if (value === form.elements.current_password.value) {
                return 'New password must be different from the current one.';
            }
            return '';
        },
        confirm_new_password(value, form) {
            if (!value) return 'Please confirm your new password.';
            if (value !== form.elements.new_password.value) return 'Passwords do not match.';
            return '';
        },
        delete_password(value) {
            return value ? '' : 'Please enter your password to confirm.';
        }
    };

    function showError(input, message) {
        const errorEl = input.closest('.field')?.querySelector('.field-error');
        if (errorEl) errorEl.textContent = message;
        input.classList.toggle('invalid', message !== '');
        input.setAttribute('aria-invalid', message !== '');
    }

    function validateField(input, form) {
        const rule = rules[input.name];
        if (!rule) return '';
        const message = rule(input.value, form);
        showError(input, message);
        return message;
    }

    function resetForm(form) {
        form.reset();
        form.querySelectorAll('input').forEach((input) => showError(input, ''));
        form.querySelectorAll('.toggle-password').forEach((button) => {
            button.parentElement.querySelector('input').type = 'password';
            button.querySelector('i').className = 'bi bi-eye';
            button.setAttribute('aria-label', 'Show password');
        });
    }

    // ---------- set up each profile form ----------
    document.querySelectorAll('.profile-form').forEach((form) => {
        form.noValidate = true;

        const fields = Array.from(form.querySelectorAll('input')).filter((i) => rules[i.name]);

        fields.forEach((input) => {
            input.addEventListener('blur', () => validateField(input, form));

            input.addEventListener('input', () => {
                if (input.classList.contains('invalid')) validateField(input, form);

                if (input.name === 'new_password' || input.name === 'current_password') {
                    const confirm = form.elements.confirm_new_password;
                    if (confirm?.value) validateField(confirm, form);

                    const newPassword = form.elements.new_password;
                    if (input.name === 'current_password' && newPassword?.classList.contains('invalid')) {
                        validateField(newPassword, form);
                    }
                }
            });
        });

        form.addEventListener('submit', (event) => {
            let firstInvalid = null;

            fields.forEach((input) => {
                if (validateField(input, form) && !firstInvalid) firstInvalid = input;
            });

            if (firstInvalid) {
                event.preventDefault();
                firstInvalid.focus();
            }
        });
    });

    // ---------- Cancel buttons ----------
    document.querySelectorAll('.profile-page [data-close]').forEach((button) => {
        button.addEventListener('click', () => {
            const details = document.getElementById(button.dataset.close);
            if (!details) return;

            details.open = false;
            const form = details.querySelector('form');
            if (form) resetForm(form);
        });
    });
});

// delete task function
// For Deleting a Task
const deleteModal = document.getElementById("deleteConfirmModal");
const closeDeleteModal = document.getElementById("closeDeleteModal");
const cancelDeleteBtn = document.getElementById("cancel-delete-btn");
const confirmDeleteBtn = document.getElementById("confirm-delete-btn");
let taskIdDelete = null;
let taskElementDelete = null;

// Toast / undo elements
const undoToast = document.getElementById("undoToast");
const undoToastMessage = document.getElementById("undoToastMessage");
const undoBtn = document.getElementById("undoBtn");

let undoTaskId = null;
let undoElement = null;
let undoParent = null;
let undoNextSibling = null;
let undoTimeoutId = null;

function openDeleteModal() {
    deleteModal.classList.add("show");
}

function closeDeleteModalView() {
    deleteModal.classList.remove("show");
    taskIdDelete = null;
    taskElementDelete = null;
}

document.querySelectorAll(".delete-btn").forEach(function (button) {
    button.addEventListener("click", function () {
        taskIdDelete = this.dataset.taskId;
        taskElementDelete = this.closest(".task-item");
        openDeleteModal();
    });
});

if (closeDeleteModal) {
    closeDeleteModal.addEventListener("click", closeDeleteModalView);
}

if (cancelDeleteBtn) {
    cancelDeleteBtn.addEventListener("click", closeDeleteModalView);
}

if (deleteModal) {
    deleteModal.addEventListener("click", function (event) {
        if (event.target === deleteModal) {
            closeDeleteModalView();
        }
    });
}
function showUndoToast(taskId, element, parent, nextSibling) {
    if (undoTimeoutId) {
        clearTimeout(undoTimeoutId);
        undoTaskId = null;
        undoElement = null;
    }

    undoTaskId = taskId;
    undoElement = element;
    undoParent = parent;
    undoNextSibling = nextSibling;

    undoToastMessage.textContent = "Task deleted";
    undoToast.classList.add("show");

    undoTimeoutId = setTimeout(function () {
        undoToast.classList.remove("show");
        undoTaskId = null;
        undoElement = null;
        undoTimeoutId = null;
    }, 5000);
}

if (undoBtn) {
    undoBtn.addEventListener("click", function () {
        if (!undoTaskId) return;

        clearTimeout(undoTimeoutId);
        undoTimeoutId = null;

        fetch(`/restore/${undoTaskId}`, { method: "POST" })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Failed to restore task (status " + response.status + ")");
                }
                // put the task element back where it was
                if (undoParent) {
                    undoParent.insertBefore(undoElement, undoNextSibling);
                }
            })
            .catch(function (error) {
                console.error("Error restoring task:", error);
                alert("Could not undo the delete. Please refresh the page.");
            })
            .finally(function () {
                undoToast.classList.remove("show");
                undoTaskId = null;
                undoElement = null;
            });
    });
}
if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", function () {
        if (!taskIdDelete) return;

        const idToDelete = taskIdDelete;
        const elementToDelete = taskElementDelete;


        const parentBeforeRemoval = elementToDelete ? elementToDelete.parentNode : null;
        const nextSiblingBeforeRemoval = elementToDelete ? elementToDelete.nextSibling : null;

        fetch(`/delete/${idToDelete}`, { method: "DELETE" })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Failed to delete task (status " + response.status + ")");
                }
                if (elementToDelete) {
                    elementToDelete.remove();
                    showUndoToast(idToDelete, elementToDelete, parentBeforeRemoval, nextSiblingBeforeRemoval);
                }
            })
            .catch(function (error) {
                console.error("Error deleting task:", error);
                alert("Could not delete the task. Please try again.");
            })
            .finally(function () {
                closeDeleteModalView();
            });
    });
}

// filter function
const filterBtn = document.getElementById("filterBtn");
const filterPanel = document.getElementById("filterPanel");

if (filterBtn && filterPanel) {
    filterBtn.addEventListener("click", function (event) {
        event.stopPropagation();
        filterPanel.classList.toggle("show");
    });

    document.addEventListener("click", function (event) {
        if (!filterPanel.contains(event.target) && event.target !== filterBtn) {
            filterPanel.classList.remove("show");
        }
    });
}

window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
        document.documentElement.style.visibility = 'hidden';
        window.location.reload();
    }
});

// listener for creating shared lists 
const newListBtn = document.getElementById("newListBtn");
if (newListBtn) {
    newListBtn.addEventListener("click", () => {
        const form = document.getElementById("newListForm");
        form.hidden = !form.hidden;
        if (!form.hidden) form.querySelector("input").focus();
    });
}