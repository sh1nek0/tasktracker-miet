from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# статусы задач
class Status(Enum):
    PLANNED = "Запланирована"
    IN_PROGRESS = "В работе"
    COMPLETED = "Выполнена"

    @classmethod
    def get_all(cls):
        return [status.value for status in cls]

# приоритеты задач
class Priority(Enum):
    LOW = "низкий"
    MEDIUM = "средний"
    HIGH = "высокий"
    CANCELLED = "отменено"

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
    reminder_date: Optional[str] = None
    reminder_sent: bool = False

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_date': self.created_date,
            'due_date': self.due_date,
            'completed_date': self.completed_date,
            'reminder_date': self.reminder_date,
            'reminder_sent': self.reminder_sent
        }

    def needs_reminder(self) -> bool:
        if self.status == Status.COMPLETED or not self.reminder_date:
            return False

        reminder_dt = datetime.strptime(self.reminder_date, '%d.%m.%Y')
        now = datetime.now()
        return reminder_dt <= now and not self.reminder_sent

    def is_overdue(self) -> bool:
        if self.status == Status.COMPLETED:
            return False
        due_date = datetime.strptime(self.due_date, '%d.%m.%Y')
        return due_date < datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            priority=Priority(data['priority']),
            status=Status(data['status']),
            created_date=data['created_date'],
            due_date=data['due_date'],
            completed_date=data.get('completed_date'),
            reminder_date=data.get('reminder_date'),
            reminder_sent=data.get('reminder_sent', False)
        )