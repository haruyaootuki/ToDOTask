"""
Data models for the ToDo application
Since we're using in-memory storage, these are just data structures
"""

from datetime import datetime
from typing import Dict, List, Optional

class Task:
    """Task model with validation"""
    
    def __init__(self, task_id: int, description: str):
        self.id = task_id
        self.description = description
        self.completed = False
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary"""
        return {
            'id': self.id,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def toggle_completion(self):
        """Toggle task completion status"""
        self.completed = not self.completed
        self.updated_at = datetime.now().isoformat()
    
    def update_description(self, new_description: str):
        """Update task description"""
        self.description = new_description
        self.updated_at = datetime.now().isoformat()

class TaskStorage:
    """In-memory task storage with validation"""
    
    def __init__(self):
        self.tasks: List[Dict] = []
        self.next_id = 1
    
    def add_task(self, description: str) -> Dict:
        """Add a new task"""
        task = Task(self.next_id, description)
        self.tasks.append(task.to_dict())
        self.next_id += 1
        return task.to_dict()
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get a task by ID"""
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks"""
        return self.tasks.copy()
    
    def get_filtered_tasks(self, filter_type: str) -> List[Dict]:
        """Get filtered tasks"""
        if filter_type == 'active':
            return [task for task in self.tasks if not task['completed']]
        elif filter_type == 'completed':
            return [task for task in self.tasks if task['completed']]
        else:  # 'all'
            return self.tasks.copy()
    
    def toggle_task(self, task_id: int) -> bool:
        """Toggle task completion"""
        for task in self.tasks:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                task['updated_at'] = datetime.now().isoformat()
                return True
        return False
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                self.tasks.pop(i)
                return True
        return False
    
    def get_task_count(self) -> Dict[str, int]:
        """Get task counts by status"""
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task['completed'])
        active = total - completed
        
        return {
            'total': total,
            'active': active,
            'completed': completed
        }
