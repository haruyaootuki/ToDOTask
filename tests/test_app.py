import pytest
from flask import url_for
from app import app, tasks_storage, task_id_counter
from datetime import datetime

class TestTaskManagement:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Setup: Clear tasks storage before each test
        tasks_storage.clear()
        global task_id_counter
        task_id_counter = 1
        yield
        # Teardown: Clear tasks storage after each test
        tasks_storage.clear()

    def test_add_task_success(self, client):
        response = client.post(url_for('add_task'), data={
            'description': 'New Task',
            'csrf_token': 'valid_csrf_token'
        }, content_type='application/x-www-form-urlencoded', follow_redirects=True)
        assert response.status_code == 200
        assert len(tasks_storage) == 1
        assert tasks_storage[0]['description'] == 'New Task'

    def test_toggle_task_success(self, client):
        # Add a task first
        tasks_storage.append({
            'id': 1,
            'description': 'Task to toggle',
            'completed': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        # データをURLエンコードして送信 - 修正
        data = {'csrf_token': 'valid_csrf_token'}
        response = client.post(url_for('toggle_task', task_id=1), data=data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert tasks_storage[0]['completed'] is True

    def test_delete_task_success(self, client):
        # Add a task first
        tasks_storage.append({
            'id': 1,
            'description': 'Task to delete',
            'completed': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        # データをURLエンコードして送信 - 修正
        data = {'csrf_token': 'valid_csrf_token'}
        response = client.post(url_for('delete_task', task_id=1), data=data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 200
        assert len(tasks_storage) == 0

    def test_add_task_invalid_description(self, client):
        response = client.post(url_for('add_task'), data={
            'description': '',
            'csrf_token': 'valid_csrf_token'
        }, content_type='application/x-www-form-urlencoded', follow_redirects=True)
        assert response.status_code == 200
        assert len(tasks_storage) == 0

    def test_toggle_task_missing_csrf(self, client):
        # Add a task first
        tasks_storage.append({
            'id': 1,
            'description': 'Task to toggle',
            'completed': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        response = client.post(url_for('toggle_task', task_id=1), data={})
        assert response.status_code == 400
        assert response.json['error'] == 'CSRF token missing'

    def test_delete_task_invalid_id(self, client):
        # データをURLエンコードして送信 - 修正
        data = {'csrf_token': 'valid_csrf_token'}
        response = client.post(url_for('delete_task', task_id=999), data=data, content_type='application/x-www-form-urlencoded')
        assert response.status_code == 404
        assert response.json['error'] == 'Task not found'