"""
Модуль моделей данных для Task Tracker.

Содержит определения классов Task, Status и Priority,
используемых для представления задач в системе.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class Status(Enum):
    """
    Перечисление статусов задач.
    
    Используется для типобезопасного управления статусами задач
    вместо строковых значений.
    """
    PLANNED = "Запланирована"
    IN_PROGRESS = "В работе"
    COMPLETED = "Выполнена"

    @classmethod
    def get_all(cls):
        """Возвращает список всех возможных статусов в виде строк."""
        return [status.value for status in cls]


class Priority(Enum):
    """
    Перечисление приоритетов задач.
    
    Используется для типобезопасного управления приоритетами задач.
    """
    LOW = "низкий"
    MEDIUM = "средний"
    HIGH = "высокий"
    CANCELLED = "отменено"


@dataclass
class Task:
    """
    Модель задачи.
    
    Использует @dataclass для автоматического создания конструктора,
    методов сравнения и представления объекта.
    
    Атрибуты:
        id: Уникальный идентификатор задачи
        title: Название задачи (обязательное поле)
        description: Описание задачи (опционально)
        priority: Приоритет задачи (Priority enum)
        status: Статус задачи (Status enum)
        created_date: Дата создания в формате ДД.ММ.ГГГГ
        due_date: Срок выполнения в формате ДД.ММ.ГГГГ
        completed_date: Дата выполнения (если задача выполнена)
        reminder_date: Дата напоминания (если установлено)
        reminder_sent: Флаг отправки напоминания
    """
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
        """
        Преобразует задачу в словарь для сериализации.
        
        Используется при экспорте в JSON и сохранении в БД.
        
        Returns:
            Словарь с данными задачи
        """
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
        """
        Проверяет, нужно ли показать напоминание для задачи.
        
        Напоминание показывается если:
        - Задача не выполнена
        - Установлена дата напоминания
        - Дата напоминания наступила или прошла
        - Напоминание еще не было отправлено
        
        Returns:
            True если нужно показать напоминание, иначе False
        """
        if self.status == Status.COMPLETED or not self.reminder_date:
            return False

        reminder_dt = datetime.strptime(self.reminder_date, '%d.%m.%Y')
        now = datetime.now()
        return reminder_dt <= now and not self.reminder_sent

    def is_overdue(self) -> bool:
        """
        Проверяет, просрочена ли задача.
        
        Задача считается просроченной если:
        - Статус не "Выполнена"
        - Срок выполнения (due_date) меньше текущей даты
        
        Returns:
            True если задача просрочена, иначе False
        """
        if self.status == Status.COMPLETED:
            return False
        due_date = datetime.strptime(self.due_date, '%d.%m.%Y')
        return due_date < datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """
        Создает объект Task из словаря.
        
        Используется при загрузке данных из БД или десериализации JSON.
        
        Args:
            data: Словарь с данными задачи
            
        Returns:
            Объект Task
        """
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