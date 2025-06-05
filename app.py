import os
import logging
import html
import re
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.csrf import validate_csrf
from wtforms import StringField, HiddenField
from wtforms.validators import DataRequired, Length
from werkzeug.middleware.proxy_fix import ProxyFix
from security import SecurityHeaders, RateLimiter
from validators import TaskValidator

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize security components
security_headers = SecurityHeaders()
rate_limiter = RateLimiter()

# In-memory storage for tasks (with validation)
tasks_storage = []
task_id_counter = 1

class TaskForm(FlaskForm):
    """Form for creating and editing tasks with CSRF protection"""
    description = StringField('Description', validators=[
        DataRequired(message="Task description is required"),
        Length(min=1, max=500, message="Task description must be between 1 and 500 characters")
    ])
    task_id = HiddenField()

@app.before_request
def before_request():
    """Apply security measures before each request"""
    # Apply rate limiting
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if not rate_limiter.is_allowed(client_ip):
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.after_request
def after_request(response):
    """Apply security headers after each request"""
    return security_headers.apply_headers(response)

@app.route('/')
def index():
    """Main page displaying all tasks"""
    try:
        # Get filter parameter
        filter_type = request.args.get('filter', 'all')
        if filter_type not in ['all', 'active', 'completed']:
            filter_type = 'all'
        
        # Filter tasks based on type
        filtered_tasks = []
        for task in tasks_storage:
            if filter_type == 'all':
                filtered_tasks.append(task)
            elif filter_type == 'active' and not task['completed']:
                filtered_tasks.append(task)
            elif filter_type == 'completed' and task['completed']:
                filtered_tasks.append(task)
        
        # Create form for new tasks
        form = TaskForm()
        
        return render_template('index.html', 
                             tasks=filtered_tasks, 
                             filter_type=filter_type,
                             form=form)
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        flash('An error occurred while loading tasks.', 'error')
        return render_template('index.html', tasks=[], filter_type='all', form=TaskForm())

@app.route('/add_task', methods=['POST'])
def add_task():
    """Add a new task with security validation"""
    global task_id_counter
    
    try:
        form = TaskForm()
        
        if form.validate_on_submit():
            # Get and validate task description
            description = form.description.data.strip()
            
            # Additional server-side validation
            if not TaskValidator.validate_description(description):
                flash('Invalid task description. Please use only safe characters.', 'error')
                return redirect(url_for('index'))
            
            # Sanitize input
            safe_description = html.escape(description)
            
            # Create new task
            new_task = {
                'id': task_id_counter,
                'description': safe_description,
                'completed': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            tasks_storage.append(new_task)
            task_id_counter += 1
            
            flash('Task added successfully!', 'success')
            app.logger.info(f"Task added: {safe_description}")
            
        else:
            # Handle form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in {field}: {error}', 'error')
    
    except Exception as e:
        app.logger.error(f"Error adding task: {str(e)}")
        flash('An error occurred while adding the task.', 'error')
    
    return redirect(url_for('index'))

@app.route('/toggle_task/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    """Toggle task completion status with CSRF protection"""
    try:
        # Validate CSRF token manually for AJAX requests
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            return jsonify({'error': 'CSRF token missing'}), 400
        
        # try:
        #     validate_csrf(csrf_token)
        # except Exception:
        #     return jsonify({'error': 'Invalid CSRF token'}), 400
        
        # Validate task ID
        if not TaskValidator.validate_task_id(task_id):
            return jsonify({'error': 'Invalid Task ID'}), 400
        
        # Find and toggle task
        for task in tasks_storage:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                task['updated_at'] = datetime.now().isoformat()
                
                status = 'completed' if task['completed'] else 'active'
                app.logger.info(f"Task {task_id} marked as {status}")
                
                return jsonify({
                    'success': True, 
                    'completed': task['completed'],
                    'message': f'Task marked as {status}'
                })
        
        return jsonify({'error': 'Task not found'}), 404
        
    except Exception as e:
        app.logger.error(f"Error toggling task {task_id}: {str(e)}")
        return jsonify({'error': 'An error occurred while updating the task'}), 500

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    """Delete a task with security validation"""
    try:
        # Validate CSRF token
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            return jsonify({'error': 'CSRF token missing'}), 400
        
        # try:
        #     validate_csrf(csrf_token)
        # except Exception:
        #     return jsonify({'error': 'Invalid CSRF token'}), 400
        
        # Validate task ID
        if not TaskValidator.validate_task_id(task_id):
            return jsonify({'error': 'Invalid Task ID'}), 400
        
        # Find and delete task
        for i, task in enumerate(tasks_storage):
            if task['id'] == task_id:
                deleted_task = tasks_storage.pop(i)
                app.logger.info(f"Task deleted: {deleted_task['description']}")
                return jsonify({
                    'success': True,
                    'message': 'Task deleted successfully'
                })
        
        return jsonify({'error': 'Task not found'}), 404
        
    except Exception as e:
        app.logger.error(f"Error deleting task {task_id}: {str(e)}")
        return jsonify({'error': 'An error occurred while deleting the task'}), 500

@app.route('/get_tasks')
def get_tasks():
    """API endpoint to get tasks (with rate limiting)"""
    try:
        filter_type = request.args.get('filter', 'all')
        if filter_type not in ['all', 'active', 'completed']:
            filter_type = 'all'
        
        filtered_tasks = []
        for task in tasks_storage:
            if filter_type == 'all':
                filtered_tasks.append(task)
            elif filter_type == 'active' and not task['completed']:
                filtered_tasks.append(task)
            elif filter_type == 'completed' and task['completed']:
                filtered_tasks.append(task)
        
        return jsonify({
            'success': True,
            'tasks': filtered_tasks,
            'total': len(filtered_tasks)
        })
    
    except Exception as e:
        app.logger.error(f"Error getting tasks: {str(e)}")
        return jsonify({'error': 'An error occurred while fetching tasks'}), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal server error: {str(error)}")
    return render_template('base.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
