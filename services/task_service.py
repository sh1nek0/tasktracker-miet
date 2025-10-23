import logging
import os
import sys
from datetime import datetime
from typing import List, Optional
from ..core.models import Task, Status, Priority
from ..core.database import Database

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

class TaskService:

    def __init__(self, db: Database):
        self.db = db
        logger.info("TaskService инициализирован")

    def create_task(self, title: str, description: str, priority: Priority,
                    due_date: str) -> Optional[Task]:
        try:
            # ВАЛИДАЦИЯ ДАННЫХ
            if not title or not title.strip():
                raise ValueError("Название задачи не может быть пустым")

            if not due_date:
                raise ValueError("Дата выполнения обязательна")

            # Проверка формата даты
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Неверный формат даты. Используйте ГГГГ-ММ-ДД")

            # СОЗДАНИЕ ЗАДАЧИ
            task = Task(
                id=0,  # ID установится в базе данных
                title=title.strip(),
                description=description.strip(),
                priority=priority,
                status=Status.PLANNED,
                created_date=datetime.now().strftime('%Y-%m-%d'),
                due_date=due_date,
                completed_date=None
            )

            # СОХРАНЕНИЕ В БАЗЕ
            task_id = self.db.create_task(task)
            created_task = self.db.get_task_by_id(task_id)

            logger.info(f"Создана новая задача: {title} (ID: {task_id})")
            return created_task

        except Exception as e:
            logger.error(f"Ошибка создания задачи: {e}")
            raise

    def get_all_tasks(self) -> List[Task]:
        tasks = self.db.get_all_tasks()
        logger.info(f"Получено {len(tasks)} задач")
        return tasks

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        try:
            task = self.db.get_task_by_id(task_id)
            if task:
                logger.info(f"Получена задача ID: {task_id}")
            else:
                logger.warning(f"Задача не найдена ID: {task_id}")
            return task
        except Exception as e:
            logger.error(f"Ошибка получения задачи {task_id}: {e}")
            return None

    def update_task(self, task: Task) -> bool:
        try:
            # ДОПОЛНИТЕЛЬНАЯ ВАЛИДАЦИЯ
            if not task.title or not task.title.strip():
                raise ValueError("Название задачи не может быть пустым")

            success = self.db.update_task(task)
            if success:
                logger.info(f"Задача обновлена: {task.title} (ID: {task.id})")
            else:
                logger.warning(f"Не удалось обновить задачу ID: {task.id}")

            return success

        except Exception as e:
            logger.error(f"Ошибка обновления задачи: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        try:
            # ПРОВЕРКА СУЩЕСТВОВАНИЯ ЗАДАЧИ
            task = self.db.get_task_by_id(task_id)
            if not task:
                logger.warning(f"Попытка удаления несуществующей задачи ID: {task_id}")
                return False

            success = self.db.delete_task(task_id)
            if success:
                logger.info(f"Задача удалена ID: {task_id}")
            else:
                logger.warning(f"Не удалось удалить задачу ID: {task_id}")

            return success

        except Exception as e:
            logger.error(f"Ошибка удаления задачи {task_id}: {e}")
            return False

    def mark_task_completed(self, task_id: int) -> bool:
        try:
            task = self.db.get_task_by_id(task_id)
            if not task:
                logger.warning(f"Задача не найдена для отметки выполнения ID: {task_id}")
                return False

            # ИЗМЕНЕНИЕ СТАТУСА
            task.status = Status.COMPLETED
            task.completed_date = datetime.now().strftime('%Y-%m-%d')

            success = self.db.update_task(task)
            if success:
                logger.info(f"Задача отмечена как выполненная ID: {task_id}")
            else:
                logger.warning(f"Не удалось обновить статус задачи ID: {task_id}")

            return success

        except Exception as e:
            logger.error(f"Ошибка отметки задачи как выполненной {task_id}: {e}")
            return False

    def change_task_status(self, task_id: int, status: Status) -> bool:
        try:
            task = self.db.get_task_by_id(task_id)
            if not task:
                logger.warning(f"Задача не найдена для изменения статуса ID: {task_id}")
                return False

            # ОБНОВЛЕНИЕ СТАТУСА И ДАТЫ
            task.status = status

            if status == Status.COMPLETED and not task.completed_date:
                task.completed_date = datetime.now().strftime('%Y-%m-%d')
            elif status != Status.COMPLETED:
                task.completed_date = None

            success = self.db.update_task(task)
            if success:
                logger.info(f"Статус задачи изменен на {status.value} ID: {task_id}")
            else:
                logger.warning(f"Не удалось изменить статус задачи ID: {task_id}")

            return success

        except Exception as e:
            logger.error(f"Ошибка изменения статуса задачи {task_id}: {e}")
            return False

    def filter_tasks(self, tasks: List[Task], status: Optional[Status] = None,
                     priority: Optional[Priority] = None) -> List[Task]:
        filtered_tasks = tasks

        if status:
            filtered_tasks = [task for task in filtered_tasks if task.status == status]
            logger.debug(f"Фильтрация по статусу {status.value}: {len(filtered_tasks)} задач")

        if priority:
            filtered_tasks = [task for task in filtered_tasks if task.priority == priority]
            logger.debug(f"Фильтрация по приоритету {priority.value}: {len(filtered_tasks)} задач")

        return filtered_tasks

    def sort_tasks(self, tasks: List[Task], sort_by: str = "created_date") -> List[Task]:
        if not tasks:
            return tasks

        if sort_by == "created_date":
            sorted_tasks = sorted(tasks, key=lambda x: x.created_date, reverse=True)
            logger.debug("Задачи отсортированы по дате создания")
        elif sort_by == "due_date":
            sorted_tasks = sorted(tasks, key=lambda x: x.due_date)
            logger.debug("Задачи отсортированы по сроку выполнения")
        elif sort_by == "priority":
            priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
            sorted_tasks = sorted(tasks, key=lambda x: priority_order[x.priority])
            logger.debug("Задачи отсортированы по приоритету")
        else:
            sorted_tasks = tasks
            logger.warning(f"Неизвестный критерий сортировки: {sort_by}")

        return sorted_tasks

    def search_tasks(self, query: str) -> List[Task]:
        if not query or not query.strip():
            return self.get_all_tasks()

        search_query = query.lower().strip()
        all_tasks = self.get_all_tasks()

        found_tasks = [
            task for task in all_tasks
            if (search_query in task.title.lower() or
                search_query in task.description.lower())
        ]

        logger.info(f"Поиск '{query}': найдено {len(found_tasks)} задач")
        return found_tasks

    def get_overdue_tasks(self) -> List[Task]:
        all_tasks = self.get_all_tasks()
        overdue_tasks = [task for task in all_tasks if task.is_overdue()]

        logger.info(f"Найдено {len(overdue_tasks)} просроченных задач")
        return overdue_tasks

    def get_tasks_by_status(self, status: Status) -> List[Task]:
        all_tasks = self.get_all_tasks()
        status_tasks = [task for task in all_tasks if task.status == status]

        logger.info(f"Найдено {len(status_tasks)} задач со статусом {status.value}")
        return status_tasks