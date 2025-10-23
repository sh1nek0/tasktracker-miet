import unittest
from datetime import datetime
from core.models import Task, Status, Priority
from core.database import Database
from services.task_service import TaskService


class TestTaskService(unittest.TestCase):

    def setUp(self):
        self.db = Database("task.db")  # In-memory база для тестов
        self.task_service = TaskService(self.db)

# тест создания задачи
    def test_create_task_success(self):
        task = self.task_service.create_task(
            title="Тестовая задача",
            description="Описание тестовой задачи",
            priority=Priority.HIGH,
            due_date="2025-12-31"
        )

        self.assertIsNotNone(task)
        self.assertEqual(task.title, "Тестовая задача")
        self.assertEqual(task.status, Status.PLANNED)
        self.assertEqual(task.priority, Priority.HIGH)

# тест создания задачи с пустым названием
    def test_create_task_empty_title(self):
        with self.assertRaises(ValueError):
            self.task_service.create_task(
                title="",
                description="Описание",
                priority=Priority.MEDIUM,
                due_date="2025-12-31"
            )

# тест создания задачи с неверной датой
    def test_create_task_invalid_date(self):
        with self.assertRaises(ValueError):
            self.task_service.create_task(
                title="Задача",
                description="Описание",
                priority=Priority.LOW,
                due_date="неправильная-дата"
            )

# тест отметки задачи выполненной
    def test_mark_task_completed(self):
        # Создаем задачу
        task = self.task_service.create_task(
            title="Задача для выполнения",
            description="Описание",
            priority=Priority.LOW,
            due_date="2025-12-31"
        )

        # Отмечаем как выполненную
        success = self.task_service.mark_task_completed(task.id)
        self.assertTrue(success)

        # Проверяем что статус изменился
        updated_task = self.task_service.get_task_by_id(task.id)
        self.assertEqual(updated_task.status, Status.COMPLETED)
        self.assertIsNotNone(updated_task.completed_date)

# тест удаления задачи
    def test_delete_task(self):
        task = self.task_service.create_task(
            title="Задача для удаления",
            description="Описание",
            priority=Priority.MEDIUM,
            due_date="2025-12-31"
        )

        # Удаляем задачу
        success = self.task_service.delete_task(task.id)
        self.assertTrue(success)

        # Проверяем что задача удалена
        deleted_task = self.task_service.get_task_by_id(task.id)
        self.assertIsNone(deleted_task)

# тест фильтр по статусу
    def test_filter_tasks_by_status(self):
        # Создаем задачи с разными статусами
        task1 = self.task_service.create_task("Задача 1", "Описание", Priority.HIGH, "2025-12-31")
        task2 = self.task_service.create_task("Задача 2", "Описание", Priority.MEDIUM, "2025-12-31")

        # Отмечаем одну как выполненную
        self.task_service.mark_task_completed(task1.id)

        # Фильтруем по статусу
        all_tasks = self.task_service.get_all_tasks()
        completed_tasks = self.task_service.filter_tasks(all_tasks, status=Status.COMPLETED)

        self.assertEqual(len(completed_tasks), 1)
        self.assertEqual(completed_tasks[0].id, task1.id)

# тест поиска задач
    def test_search_tasks(self):
        task = self.task_service.create_task(
            title="Уникальное название задачи",
            description="Обычное описание",
            priority=Priority.HIGH,
            due_date="2025-12-31"
        )

        # Поиск по названию
        results = self.task_service.search_tasks("Уникальное")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, task.id)

        # Поиск по описанию
        results = self.task_service.search_tasks("Обычное")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, task.id)

# тест получения просроченных задач
    def test_get_overdue_tasks(self):
        # Создаем просроченную задачу
        overdue_task = self.task_service.create_task(
            "Просроченная задача",
            "Описание",
            Priority.HIGH,
            "2020-01-01"  # Прошлая дата
        )

        overdue_tasks = self.task_service.get_overdue_tasks()
        self.assertTrue(len(overdue_tasks) >= 1)
        self.assertTrue(overdue_task.is_overdue())


if __name__ == "__main__":
    unittest.main()