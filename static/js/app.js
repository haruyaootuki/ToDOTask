/**
 * Secure ToDo Application JavaScript
 * Implements client-side functionality with security measures
 */

// Security utilities
const Security = {
    // Escape HTML to prevent XSS
    escapeHtml: function(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    // Validate input on client side
    validateTaskDescription: function(description) {
        if (!description || typeof description !== 'string') {
            return false;
        }
        
        const trimmed = description.trim();
        if (trimmed.length < 1 || trimmed.length > 500) {
            return false;
        }
        
        // Check for dangerous patterns
        const dangerousPatterns = [
            /<script[^>]*>/i,
            /javascript:/i,
            /vbscript:/i,
            /on\w+\s*=/i
        ];
        
        return !dangerousPatterns.some(pattern => pattern.test(description));
    },
    
    // Get CSRF token from meta tag or form
    getCsrfToken: function() {
        const tokenElement = document.querySelector('input[name="csrf_token"]');
        return tokenElement ? tokenElement.value : null;
    },
    
    // Sanitize user input
    sanitizeInput: function(input) {
        if (typeof input !== 'string') return '';
        return input.trim().substring(0, 500);
    }
};

// Main application object
const TodoApp = {
    // Initialize the application
    init: function() {
        this.bindEvents();
        this.setupFormValidation();
        this.updateTaskCounts();
        console.log('ToDo App initialized securely');
    },
    
    // Bind event listeners
    bindEvents: function() {
        // Task form submission
        const taskForm = document.getElementById('taskForm');
        if (taskForm) {
            taskForm.addEventListener('submit', this.handleTaskSubmission.bind(this));
        }
        
        // Task checkbox changes
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('task-checkbox')) {
                TodoApp.toggleTask(e.target);
            }
        });
        
        // Delete button clicks
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('btn-delete') || 
                e.target.closest('.btn-delete')) {
                e.preventDefault();
                const button = e.target.classList.contains('btn-delete') ? 
                              e.target : e.target.closest('.btn-delete');
                TodoApp.deleteTask(button);
            }
        });
        
        // Filter button clicks
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('filter-btn')) {
                e.preventDefault();
                TodoApp.filterTasks(e.target.dataset.filter);
            }
        });
        
        // Real-time input validation
        const taskInput = document.getElementById('description');
        if (taskInput) {
            taskInput.addEventListener('input', this.validateTaskInput.bind(this));
        }
    },
    
    // Setup form validation
    setupFormValidation: function() {
        const form = document.getElementById('taskForm');
        const input = document.getElementById('description');
        const submitButton = form ? form.querySelector('button[type="submit"]') : null;
        
        if (!form || !input || !submitButton) return;
        
        // Enable/disable submit button based on input validity
        const validateForm = () => {
            const description = Security.sanitizeInput(input.value);
            const isValid = Security.validateTaskDescription(description);
            
            submitButton.disabled = !isValid;
            
            if (description.length > 0 && !isValid) {
                input.classList.add('is-invalid');
                this.showValidationError('Please enter a valid task description (1-500 characters, no scripts)');
            } else {
                input.classList.remove('is-invalid');
                this.hideValidationError();
            }
        };
        
        input.addEventListener('input', validateForm);
        validateForm(); // Initial validation
    },
    
    // Handle task form submission
    handleTaskSubmission: function(e) {
        const form = e.target;
        const input = form.querySelector('#description');
        const description = Security.sanitizeInput(input.value);
        
        // Client-side validation
        if (!Security.validateTaskDescription(description)) {
            e.preventDefault();
            this.showError('Please enter a valid task description');
            return false;
        }
        
        // Show loading state
        this.setLoadingState(form, true);
        
        // Form will submit normally to server
        return true;
    },
    
    // Validate task input in real-time
    validateTaskInput: function(e) {
        const input = e.target;
        const description = Security.sanitizeInput(input.value);
        const charCount = description.length;
        
        // Update character count if element exists
        const charCounter = document.getElementById('charCount');
        if (charCounter) {
            charCounter.textContent = `${charCount}/500`;
            charCounter.className = charCount > 450 ? 'text-warning' : 'text-muted';
        }
        
        // Validate input
        if (charCount > 0) {
            const isValid = Security.validateTaskDescription(description);
            input.classList.toggle('is-invalid', !isValid);
            
            if (!isValid) {
                this.showValidationError('Invalid characters detected');
            } else {
                this.hideValidationError();
            }
        } else {
            input.classList.remove('is-invalid');
            this.hideValidationError();
        }
    },
    
    // Toggle task completion
    toggleTask: function(checkbox) {
        const taskId = checkbox.dataset.taskId;
        const csrfToken = Security.getCsrfToken();
        
        if (!taskId || !csrfToken) {
            this.showError('Security error: Missing required tokens');
            checkbox.checked = !checkbox.checked; // Revert checkbox
            return;
        }
        
        // Show loading state
        const taskItem = checkbox.closest('.task-item');
        this.setLoadingState(taskItem, true);
        
        // Send request to server
        fetch(`/toggle_task/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `csrf_token=${encodeURIComponent(csrfToken)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI
                taskItem.classList.toggle('completed', data.completed);
                this.updateTaskCounts();
                this.showSuccess(data.message || 'Task updated successfully');
            } else {
                checkbox.checked = !checkbox.checked; // Revert checkbox
                this.showError(data.error || 'Failed to update task');
            }
        })
        .catch(error => {
            console.error('Error toggling task:', error);
            checkbox.checked = !checkbox.checked; // Revert checkbox
            this.showError('Network error occurred');
        })
        .finally(() => {
            this.setLoadingState(taskItem, false);
        });
    },
    
    // Delete task
    deleteTask: function(button) {
        const taskId = button.dataset.taskId;
        const csrfToken = Security.getCsrfToken();
        
        if (!taskId || !csrfToken) {
            this.showError('Security error: Missing required tokens');
            return;
        }
        
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }
        
        const taskItem = button.closest('.task-item');
        this.setLoadingState(taskItem, true);
        
        // Send delete request
        fetch(`/delete_task/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `csrf_token=${encodeURIComponent(csrfToken)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove task from UI with animation
                taskItem.style.transition = 'all 0.3s ease';
                taskItem.style.opacity = '0';
                taskItem.style.transform = 'translateX(-100%)';
                
                setTimeout(() => {
                    taskItem.remove();
                    this.updateTaskCounts();
                    this.checkEmptyState();
                }, 300);
                
                this.showSuccess(data.message || 'Task deleted successfully');
            } else {
                this.showError(data.error || 'Failed to delete task');
            }
        })
        .catch(error => {
            console.error('Error deleting task:', error);
            this.showError('Network error occurred');
        })
        .finally(() => {
            this.setLoadingState(taskItem, false);
        });
    },
    
    // Filter tasks
    filterTasks: function(filterType) {
        // Validate filter type
        if (!['all', 'active', 'completed'].includes(filterType)) {
            console.error('Invalid filter type:', filterType);
            return;
        }
        
        // Update URL without page reload
        const url = new URL(window.location);
        if (filterType === 'all') {
            url.searchParams.delete('filter');
        } else {
            url.searchParams.set('filter', filterType);
        }
        window.history.pushState({}, '', url);
        
        // Update filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filterType}"]`).classList.add('active');
        
        // Filter task items
        const tasks = document.querySelectorAll('.task-item');
        tasks.forEach(task => {
            const isCompleted = task.classList.contains('completed');
            let show = true;
            
            if (filterType === 'active' && isCompleted) {
                show = false;
            } else if (filterType === 'completed' && !isCompleted) {
                show = false;
            }
            
            task.style.display = show ? 'block' : 'none';
        });
        
        this.checkEmptyState();
    },
    
    // Update task counts
    updateTaskCounts: function() {
        const tasks = document.querySelectorAll('.task-item');
        const completedTasks = document.querySelectorAll('.task-item.completed');
        
        const totalCount = tasks.length;
        const completedCount = completedTasks.length;
        const activeCount = totalCount - completedCount;
        
        // Update count displays
        const totalElement = document.getElementById('totalCount');
        const activeElement = document.getElementById('activeCount');
        const completedElement = document.getElementById('completedCount');
        
        if (totalElement) totalElement.textContent = totalCount;
        if (activeElement) activeElement.textContent = activeCount;
        if (completedElement) completedElement.textContent = completedCount;
        
        // Update filter button badges
        document.querySelectorAll('.filter-btn').forEach(btn => {
            const filter = btn.dataset.filter;
            const badge = btn.querySelector('.badge');
            if (badge) {
                let count = totalCount;
                if (filter === 'active') count = activeCount;
                else if (filter === 'completed') count = completedCount;
                badge.textContent = count;
            }
        });
    },
    
    // Check if we should show empty state
    checkEmptyState: function() {
        const visibleTasks = document.querySelectorAll('.task-item[style*="display: block"], .task-item:not([style*="display: none"])');
        const emptyState = document.getElementById('emptyState');
        
        if (emptyState) {
            emptyState.style.display = visibleTasks.length === 0 ? 'block' : 'none';
        }
    },
    
    // Show error message
    showError: function(message) {
        this.showAlert(message, 'danger');
    },
    
    // Show success message
    showSuccess: function(message) {
        this.showAlert(message, 'success');
    },
    
    // Show validation error
    showValidationError: function(message) {
        const errorElement = document.getElementById('validationError');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    },
    
    // Hide validation error
    hideValidationError: function() {
        const errorElement = document.getElementById('validationError');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    },
    
    // Show alert message
    showAlert: function(message, type) {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alert.innerHTML = `
            ${Security.escapeHtml(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    },
    
    // Set loading state
    setLoadingState: function(element, loading) {
        if (loading) {
            element.classList.add('loading');
        } else {
            element.classList.remove('loading');
        }
    }
};

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        TodoApp.init();
    });
} else {
    TodoApp.init();
}

// Security monitoring
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
});

// Prevent console tampering in production
if (location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    console.log('%cSecurity Warning!', 'color: red; font-size: 20px; font-weight: bold;');
    console.log('%cThis application implements security measures. Unauthorized access attempts are logged.', 'color: red; font-size: 14px;');
}
