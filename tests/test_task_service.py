import unittest
import os
import sys
import tempfile
from tkinter import ttk, messagebox
from unittest.mock import Mock, patch

# Добавляем корневую директорию в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models import Task, Status, Priority
from core.database import Database
from services.task_service import TaskService
from services.notification_service import NotificationService
from datetime import datetime


class TestTaskService(unittest.TestCase):

    def setUp(self):
        # Создаем временную базу данных для каждого теста
        self.temp_db = tempfile.mktemp(suffix='.db')
        self.db = Database(self.temp_db)
        self.task_service = TaskService(self.db)
    
    def tearDown(self):
        # Удаляем временную базу данных
        try:
            if hasattr(self, 'temp_db') and os.path.exists(self.temp_db):
                os.unlink(self.temp_db)
        except:
            pass  # Игнорируем ошибки при удалении

    def test_create_task_success(self):
        task = self.task_service.create_task(
            title="Тестовая задача",
            description="Описание тестовой задачи",
            priority=Priority.HIGH,
            due_date="31.12.2025"
        )

        self.assertIsNotNone(task)
        self.assertEqual(task.title, "Тестовая задача")
        self.assertEqual(task.status, Status.PLANNED)
        self.assertEqual(task.priority, Priority.HIGH)

    def test_create_task_empty_title(self):
        with self.assertRaises(ValueError):
            self.task_service.create_task(
                title="",
                description="Описание",
                priority=Priority.MEDIUM,
                due_date="31.12.2025" 
            )

    def test_create_task_invalid_date(self):
        with self.assertRaises(ValueError):
            self.task_service.create_task(
                title="Задача",
                description="Описание",
                priority=Priority.LOW,
                due_date="неправильная-дата"
            )

    def test_mark_task_completed(self):
        # Создаем задачу
        task = self.task_service.create_task(
            title="Задача для выполнения",
            description="Описание",
            priority=Priority.LOW,
            due_date="31.12.2025"
        )

        # Отмечаем как выполненную
        success = self.task_service.complete_task(task.id)
        self.assertTrue(success)

        # Проверяем что статус изменился
        updated_task = self.task_service.get_task(task.id)
        self.assertEqual(updated_task.status, Status.COMPLETED)
        self.assertIsNotNone(updated_task.completed_date)

    def test_delete_task(self):
        task = self.task_service.create_task(
            title="Задача для удаления",
            description="Описание",
            priority=Priority.MEDIUM,
            due_date="31.12.2025"
        )

        # Удаляем задачу
        success = self.task_service.delete_task(task.id)
        self.assertTrue(success)

        # Проверяем что задача удалена
        deleted_task = self.task_service.get_task(task.id)
        self.assertIsNone(deleted_task)

    def test_filter_tasks_by_status(self):
        # Создаем задачи с разными статусами
        task1 = self.task_service.create_task("Задача 1", "Описание", Priority.HIGH, "31.12.2025")
        task2 = self.task_service.create_task("Задача 2", "Описание", Priority.MEDIUM, "31.12.2025")

        # Отмечаем одну как выполненную
        self.task_service.complete_task(task1.id)

        # Фильтруем по статусу
        all_tasks = self.task_service.get_all_tasks()
        completed_tasks = self.task_service.filter_tasks(all_tasks, status=Status.COMPLETED)

        self.assertEqual(len(completed_tasks), 1)
        self.assertEqual(completed_tasks[0].id, task1.id)

    def test_search_tasks(self):
        task = self.task_service.create_task(
            title="Уникальное название задачи",
            description="Обычное описание",
            priority=Priority.HIGH,
            due_date="31.12.2025"
        )

        # Поиск по названию
        results = self.task_service.search("Уникальное")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, task.id)

        # Поиск по описанию
        results = self.task_service.search("Обычное")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, task.id)

    def test_get_overdue_tasks(self):
        # Создаем просроченную задачу
        overdue_task = self.task_service.create_task(
            "Просроченная задача",
            "Описание",
            Priority.HIGH,
            "01.01.2020"
        )

        overdue_tasks = self.task_service.get_overdue()
        self.assertTrue(len(overdue_tasks) >= 1)
        self.assertTrue(overdue_task.is_overdue())

    def test_get_all_tasks(self):
        task1 = self.task_service.create_task("Задача 1", "Описание 1", Priority.LOW, "31.12.2025")
        task2 = self.task_service.create_task("Задача 2", "Описание 2", Priority.MEDIUM, "31.12.2025")
        
        all_tasks = self.task_service.get_all_tasks()
        self.assertEqual(len(all_tasks), 2)

    def test_get_task_by_id(self):
        task = self.task_service.create_task("Тестовая задача", "Описание", Priority.HIGH, "31.12.2025")
        
        retrieved_task = self.task_service.get_task(task.id)
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.title, "Тестовая задача")
        self.assertEqual(retrieved_task.id, task.id)

    def test_get_nonexistent_task(self):
        task = self.task_service.get_task(99999)
        self.assertIsNone(task)

    def test_update_task(self):
        task = self.task_service.create_task("Исходная задача", "Описание", Priority.LOW, "31.12.2025")
        
        # Обновляем задачу
        task.title = "Обновленная задача"
        task.description = "Новое описание"
        task.priority = Priority.HIGH
        task.status = Status.IN_PROGRESS
        
        success = self.task_service.update_task(task)
        self.assertTrue(success)
        
        # Проверяем обновления
        updated_task = self.task_service.get_task(task.id)
        self.assertEqual(updated_task.title, "Обновленная задача")
        self.assertEqual(updated_task.description, "Новое описание")
        self.assertEqual(updated_task.priority, Priority.HIGH)
        self.assertEqual(updated_task.status, Status.IN_PROGRESS)

    def test_update_nonexistent_task(self):
        task = Task(
            id=99999, 
            title="Несуществующая задача",
            description="Описание",
            priority=Priority.MEDIUM,
            status=Status.PLANNED,
            due_date="31.12.2025",
            created_date=datetime.now().strftime('%d.%m.%Y')
        )
        
        success = self.task_service.update_task(task)
        self.assertFalse(success)

    def test_filter_tasks_by_priority(self):
        # Создаем задачи с разными приоритетами
        task_high = self.task_service.create_task("Высокая", "Описание", Priority.HIGH, "31.12.2025")
        task_medium = self.task_service.create_task("Средняя", "Описание", Priority.MEDIUM, "31.12.2025")
        task_low = self.task_service.create_task("Низкая", "Описание", Priority.LOW, "31.12.2025")
        
        all_tasks = self.task_service.get_all_tasks()
        
        # Фильтруем по высокому приоритету
        high_priority_tasks = self.task_service.filter_tasks(all_tasks, priority=Priority.HIGH)
        self.assertEqual(len(high_priority_tasks), 1)
        self.assertEqual(high_priority_tasks[0].id, task_high.id)

    def test_search_no_results(self):
        self.task_service.create_task("Другая задача", "Описание", Priority.MEDIUM, "31.12.2025")
        
        results = self.task_service.search("НесуществующийТекст")
        self.assertEqual(len(results), 0)

    def test_complete_nonexistent_task(self):
        success = self.task_service.complete_task(99999)
        self.assertFalse(success)

    def test_delete_nonexistent_task(self):
        success = self.task_service.delete_task(99999)
        self.assertFalse(success)

    def test_task_is_overdue(self):
        # Создаем просроченную задачу
        overdue_task = self.task_service.create_task(
            "Просроченная", 
            "Описание", 
            Priority.HIGH, 
            "01.01.2020" 
        )
        
        self.assertTrue(overdue_task.is_overdue())
        
        # Создаем непросроченную задачу
        future_task = self.task_service.create_task(
            "Будущая", 
            "Описание", 
            Priority.HIGH, 
            "01.01.2030"
        )
        
        self.assertFalse(future_task.is_overdue())


    def test_sort_tasks_by_due_date(self):
        task_late = self.task_service.create_task("Поздняя", "Описание", Priority.MEDIUM, "31.12.2025")
        task_early = self.task_service.create_task("Ранняя", "Описание", Priority.MEDIUM, "01.01.2025")
        
        tasks = [task_late, task_early]
        
        sorted_tasks = self.task_service.sort_tasks(tasks, "due_date")
        
        self.assertEqual(sorted_tasks[0].title, "Ранняя")
        self.assertEqual(sorted_tasks[1].title, "Поздняя")

    def test_create_task_with_min_title_length(self):
        task = self.task_service.create_task("а", "Описание", Priority.MEDIUM, "31.12.2025")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.title, "а")

    def test_create_task_with_long_title(self):
        long_title = "а" * 100
        
        task = self.task_service.create_task(long_title, "Описание", Priority.MEDIUM, "31.12.2025")
        
        self.assertIsNotNone(task)
        self.assertEqual(len(task.title), 100)

    def test_combined_filter_and_sort(self):
        task1 = self.task_service.create_task("Задача 1", "Описание", Priority.HIGH, "31.12.2025")
        task2 = self.task_service.create_task("Задача 2", "Описание", Priority.HIGH, "01.01.2025")
        task3 = self.task_service.create_task("Задача 3", "Описание", Priority.MEDIUM, "31.12.2025")
        
        all_tasks = self.task_service.get_all_tasks()
        filtered_tasks = self.task_service.filter_tasks(all_tasks, priority=Priority.HIGH)
        sorted_tasks = self.task_service.sort_tasks(filtered_tasks, "due_date")
        
        self.assertEqual(len(sorted_tasks), 2)
        self.assertEqual(sorted_tasks[0].title, "Задача 2")  # Ранняя дата
        self.assertEqual(sorted_tasks[1].title, "Задача 1")  # Поздняя дата

    def test_get_all_tasks_empty(self):
        tasks = self.task_service.get_all_tasks()
        
        self.assertEqual(len(tasks), 0)

    def test_filter_empty_tasks(self):
        empty_tasks = self.task_service.get_all_tasks()
        filtered_tasks = self.task_service.filter_tasks(empty_tasks, priority=Priority.HIGH)
        
        self.assertEqual(len(filtered_tasks), 0)

    def test_sort_empty_tasks(self):
        empty_tasks = self.task_service.get_all_tasks()
        sorted_tasks = self.task_service.sort_tasks(empty_tasks, "due_date")
        
        self.assertEqual(len(sorted_tasks), 0)

    def test_create_task_with_far_future_date(self):
        task = self.task_service.create_task("Далекая задача", "Описание", Priority.MEDIUM, "31.12.9999")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.due_date, "31.12.9999")
        self.assertFalse(task.is_overdue())

    def test_check_overdue_tasks_with_mock(self):
        mock_tasks = [
            Mock(is_overdue=Mock(return_value=True), title="Просроченная"),
            Mock(is_overdue=Mock(return_value=False), title="Активная")
        ]
        
        with patch.object(self.task_service, 'get_all_tasks', return_value=mock_tasks):
            notification_service = NotificationService(self.task_service)
            overdue_tasks = notification_service.check_overdue_tasks()
            
            self.assertEqual(len(overdue_tasks), 1)
            self.assertEqual(overdue_tasks[0].title, "Просроченная")

    def test_process_reminders(self):
        reminders_count = self.task_service.process_reminders()
        
        self.assertIsInstance(reminders_count, int)
        self.assertGreaterEqual(reminders_count, 0)
        
if __name__ == "__main__":
    unittest.main()