from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# статусы задач
class Status(Enum):
    PLANNED = "Запланировано"
    IN_PROGRESS = "В работе"
    COMPLETED = "Выполнено"

    @classmethod
    def get_all(cls):
        return [status.value for status in cls]

# приоритеты задач
class Priority(Enum):
    LOW = "низкий"
    MEDIUM = "средний"
    HIGH = "высокий"

# модель задачи
@dataclass # для автоматического создания конструктора и методов.
class Task:
    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    created_date: str
    due_date: str
    completed_date: Optional[str] = None

    # проверка просрочки задачи
    def is_overdue(self) -> bool:
        if self.status == Status.COMPLETED:
            return False
        due_date = datetime.strptime(self.due_date, '%Y-%m-%d')
        return due_date < datetime.now()

    # конвертирует задачи в словарь для сохранения в JSON
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_date': self.created_date,
            'due_date': self.due_date,
            'completed_date': self.completed_date
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        # деконвертируем из словаря в Task
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            priority=Priority(data['priority']),
            status=Status(data['status']),
            created_date=data['created_date'],
            due_date=data['due_date'],
            completed_date=data.get('completed_date')
        )