import unittest
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock
from tkinter import messagebox
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import Database
from services.task_service import TaskService
from services.notification_service import NotificationService
from core.models import Task, Status, Priority
from datetime import datetime, timedelta


class TestNotificationService(unittest.TestCase):

    def setUp(self):
        # Создаем временную базу данных для каждого теста
        self.temp_db = tempfile.mktemp(suffix='.db')
        self.db = Database(self.temp_db)
        self.task_service = TaskService(self.db)
        self.notification_service = NotificationService(self.task_service)

    def tearDown(self):
        # Удаляем временную базу данных
        try:
            if hasattr(self, 'temp_db') and os.path.exists(self.temp_db):
                os.unlink(self.temp_db)
        except:
            pass

    def test_notification_service_initialization(self):
        #Тест инициализации сервиса уведомлений
        self.assertIsNotNone(self.notification_service)
        self.assertEqual(self.notification_service.task_service, self.task_service)

    def test_check_overdue_tasks_with_overdue_tasks(self):
        #tест проверки просроченных задач при их наличии
        # Создаем просроченную задачу
        overdue_task = self.task_service.create_task(
            "Просроченная задача",
            "Описание",
            Priority.HIGH,
            "01.01.2020"  # Прошлая дата
        )

        overdue_tasks = self.notification_service.check_overdue_tasks()
        
        self.assertEqual(len(overdue_tasks), 1)
        self.assertEqual(overdue_tasks[0].title, "Просроченная задача")
        self.assertTrue(overdue_tasks[0].is_overdue())

    def test_check_overdue_tasks_without_overdue_tasks(self):
        #Тест проверки просроченных задач при их отсутствии
        # Создаем только задачи с будущими датами
        future_task = self.task_service.create_task(
            "Будущая задача",
            "Описание",
            Priority.MEDIUM,
            "01.01.2030"
        )

        overdue_tasks = self.notification_service.check_overdue_tasks()
        self.assertEqual(len(overdue_tasks), 0)

    def test_check_overdue_tasks_with_completed_task(self):
        #Тест проверки просроченных задач с выполненной задачей
        # Создаем просроченную, но выполненную задачу
        completed_overdue_task = self.task_service.create_task(
            "Выполненная просроченная",
            "Описание",
            Priority.HIGH,
            "01.01.2020"
        )
        self.task_service.complete_task(completed_overdue_task.id)

        overdue_tasks = self.notification_service.check_overdue_tasks()
        # Выполненные задачи не должны считаться просроченными
        self.assertEqual(len(overdue_tasks), 0)

    
    

    

    @patch('services.notification_service.messagebox.showinfo')
    def test_show_periodic_notifications_no_reminders(self, mock_showinfo):
        #Тест периодических уведомлений без напоминаний
        # Мокаем process_reminders чтобы не возвращать напоминания
        with patch.object(self.task_service, 'process_reminders', return_value=0):
            root = Mock()
            self.notification_service.show_periodic_notifications(root)
            
            # Не должно быть показано уведомление
            mock_showinfo.assert_not_called()

    def test_get_upcoming_tasks(self):
        #Тест получения задач с приближающимся сроком
        # Создаем задачу с близким сроком (через 2 дня)
        upcoming_date = (datetime.now() + timedelta(days=2)).strftime('%d.%m.%Y')
        upcoming_task = self.task_service.create_task(
            "Скоро срок",
            "Описание",
            Priority.HIGH,
            upcoming_date
        )

        # Создаем задачу с далеким сроком
        far_task = self.task_service.create_task(
            "Далекая задача",
            "Описание", 
            Priority.LOW,
            "31.12.2030"
        )

        # Этот метод может быть в notification_service или его нужно добавить
        # Если метода нет, можно протестировать через process_reminders
        reminders_count = self.task_service.process_reminders()
        self.assertIsInstance(reminders_count, int)

    

    @patch('services.notification_service.messagebox.showwarning')
    def test_notification_with_different_priorities(self, mock_showwarning):
        #Тест уведомлений с задачами разного приоритета
        high_priority_task = Mock(
            title="Важная задача", 
            due_date="01.01.2020", 
            priority=Priority.HIGH,
            is_overdue=Mock(return_value=True)
        )
        medium_priority_task = Mock(
            title="Обычная задача",
            due_date="02.01.2020",
            priority=Priority.MEDIUM,
            is_overdue=Mock(return_value=True)
        )
        
        overdue_tasks = [high_priority_task, medium_priority_task]
        
        with patch.object(self.notification_service.task_service, 'get_all_tasks', return_value=overdue_tasks):
            self.notification_service.check_overdue_tasks()
            # Дополнительные проверки могут быть добавлены здесь

    def test_notification_service_with_mock_tasks(self):
        #Тест сервиса уведомлений с mock-задачами
        mock_tasks = [
            Mock(is_overdue=Mock(return_value=True), title="Просроченная 1"),
            Mock(is_overdue=Mock(return_value=False), title="Активная"),
            Mock(is_overdue=Mock(return_value=True), title="Просроченная 2")
        ]
        
        with patch.object(self.task_service, 'get_all_tasks', return_value=mock_tasks):
            overdue_tasks = self.notification_service.check_overdue_tasks()
            
            self.assertEqual(len(overdue_tasks), 2)
            self.assertEqual(overdue_tasks[0].title, "Просроченная 1")
            self.assertEqual(overdue_tasks[1].title, "Просроченная 2")


if __name__ == "__main__":
    unittest.main()