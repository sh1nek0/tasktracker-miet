import logging
from datetime import datetime, timedelta
from typing import List, Optional
from core.models import Task, Status, Priority
from core.database import Database

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, db: Database):
        self.db = db

    def create_task(self, title: str, description: str, priority: Priority,
                    due_date: str, reminder_days: int = None) -> Optional[Task]:
        if not title.strip():
            raise ValueError("Название задачи не может быть пустым")

        # Проверяем дату
        try:
            datetime.strptime(due_date, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Неверный формат даты. Используйте ДД.ММ.ГГГГ")

        # Рассчитываем дату напоминания если нужно
        reminder_date = None
        if reminder_days:
            due_dt = datetime.strptime(due_date, '%d.%m.%Y')
            reminder_dt = due_dt - timedelta(days=reminder_days)
            reminder_date = reminder_dt.strftime('%d.%m.%Y')

        task = Task(
            id=0,
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            status=Status.PLANNED,
            created_date=datetime.now().strftime('%d.%m.%Y'),
            due_date=due_date,
            reminder_date=reminder_date,
            reminder_sent=False
        )

        task_id = self.db.create_task(task)
        return self.db.get_task_by_id(task_id)

    def process_reminders(self) -> int:
        reminders = self.get_reminders()
        sent_count = 0

        for task in reminders:
            print(f"НАПОМИНАНИЕ: '{task.title}' - срок: {task.due_date}")
            if self.mark_reminder_sent(task.id):
                sent_count += 1

        return sent_count
    def get_all_tasks(self) -> List[Task]:
        return self.db.get_all_tasks()

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.db.get_task_by_id(task_id)

    def update_task(self, task: Task) -> bool:
        if not task.title.strip():
            raise ValueError("Название задачи не может быть пустым")
        return self.db.update_task(task)

    def delete_task(self, task_id: int) -> bool:
        return self.db.delete_task(task_id)

    def complete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False

        task.status = Status.COMPLETED
        task.completed_date = datetime.now().strftime('%d.%m.%Y')
        return self.update_task(task)

    def change_status(self, task_id: int, status: Status) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False

        task.status = status

        # Если задача выполнена - ставим дату выполнения
        if status == Status.COMPLETED and not task.completed_date:
            task.completed_date = datetime.now().strftime('%d.%m.%Y')
        elif status != Status.COMPLETED:
            task.completed_date = None

        return self.update_task(task)

    def get_reminders(self) -> List[Task]:
        tasks = self.get_all_tasks()
        return [task for task in tasks if task.needs_reminder()]

    def mark_reminder_sent(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False

        task.reminder_sent = True
        return self.update_task(task)

    def search(self, query: str) -> List[Task]:
        if not query.strip():
            return self.get_all_tasks()

        query = query.lower().strip()
        tasks = self.get_all_tasks()

        return [
            task for task in tasks
            if query in task.title.lower() or query in task.description.lower()
        ]

    def get_overdue(self) -> List[Task]:
        tasks = self.get_all_tasks()
        return [task for task in tasks if task.is_overdue()]

    def filter_tasks(self, tasks: List[Task], status: Status = None, priority: Priority = None) -> List[Task]:
        result = tasks

        if status:
            result = [task for task in result if task.status == status]

        if priority:
            result = [task for task in result if task.priority == priority]

        return result

    def sort_tasks(self, tasks: List[Task], by: str = "created_date") -> List[Task]:
        if not tasks:
            return tasks

        if by == "due_date":
            return sorted(tasks, key=lambda x: datetime.strptime(x.due_date, '%d.%m.%Y'))
        elif by == "due_date_desc":
            return sorted(tasks, key=lambda x: datetime.strptime(x.due_date, '%d.%m.%Y'), reverse=True)
        elif by == "priority":
            priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
            return sorted(tasks, key=lambda x: priority_order[x.priority])
        elif by == "created_date":
            return sorted(tasks, key=lambda x: datetime.strptime(x.created_date, '%d.%m.%Y'), reverse=True)
        else:  # created_date по умолчанию
            return sorted(tasks, key=lambda x: datetime.strptime(x.created_date, '%d.%m.%Y'), reverse=True)