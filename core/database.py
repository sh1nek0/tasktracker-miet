"""
Модуль для работы с базой данных SQLite.

Содержит класс Database для выполнения всех операций с БД:
создание, чтение, обновление и удаление задач.
"""

import sqlite3
import logging
from typing import List, Optional
from core.models import Task, Status

logger = logging.getLogger(__name__)


class Database:
    """
    Класс для работы с базой данных SQLite.
    
    Инкапсулирует все операции с БД, предоставляя высокоуровневый
    интерфейс для работы с задачами. Автоматически создает таблицу
    при первом обращении.
    
    Атрибуты:
        db_path: Путь к файлу базы данных SQLite
    """
    
    def __init__(self, db_path: str = "tasks.db"):
        """
        Инициализирует подключение к базе данных.
        
        Args:
            db_path: Путь к файлу БД (по умолчанию "tasks.db")
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """
        Создает таблицу tasks в БД, если она не существует.
        
        Вызывается автоматически при инициализации класса.
        Устанавливает ограничения на данные через CHECK constraints.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL CHECK(length(title) <= 500),
                        description TEXT CHECK(description IS NULL OR length(description) <= 2000),
                        priority TEXT NOT NULL CHECK(priority IN ('низкий', 'средний', 'высокий')),
                        status TEXT NOT NULL CHECK(status IN ('Запланирована', 'В работе', 'Выполнена')),
                        created_date TEXT NOT NULL,
                        due_date TEXT NOT NULL,
                        completed_date TEXT,
                        reminder_date TEXT,
                        reminder_sent BOOLEAN DEFAULT 0,
                        CHECK (due_date IS NULL OR due_date GLOB '[0-9][0-9].[0-9][0-9].[0-9][0-9][0-9][0-9]')
                )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    def create_task(self, task: Task) -> int:
        """
        Создает новую задачу в базе данных.
        
        Args:
            task: Объект Task для сохранения
            
        Returns:
            ID созданной задачи
            
        Raises:
            sqlite3.Error: При ошибке работы с БД
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks (title, description, priority, status, created_date, due_date, completed_date, reminder_date, reminder_sent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.title, task.description, task.priority.value,
                    task.status.value, task.created_date, task.due_date,
                    task.completed_date, task.reminder_date, task.reminder_sent
                ))
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания задачи: {e}")
            raise

    def get_all_tasks(self) -> List[Task]:
        """
        Получает все задачи из базы данных.
        
        Returns:
            Список объектов Task. Возвращает пустой список при ошибке.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks')
                tasks = []
                for row in cursor.fetchall():
                    task_dict = {
                        'id': row[0],
                        'title': row[1],
                        'description': row[2],
                        'priority': row[3],
                        'status': row[4],
                        'created_date': row[5],
                        'due_date': row[6],
                        'completed_date': row[7],
                        'reminder_date': row[8],
                        'reminder_sent': bool(row[9])
                    }
                    tasks.append(Task.from_dict(task_dict))
                return tasks
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения задач: {e}")
            return []

    def update_task(self, task: Task) -> bool:
        """
        Обновляет существующую задачу в базе данных.
        
        Args:
            task: Объект Task с обновленными данными (должен содержать id)
            
        Returns:
            True если задача обновлена, False если ошибка или задача не найдена
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tasks 
                    SET title=?, description=?, priority=?, status=?, 
                        due_date=?, completed_date=?, reminder_date=?, reminder_sent=?
                    WHERE id=?
                ''', (
                    task.title, task.description, task.priority.value,
                    task.status.value, task.due_date, task.completed_date,
                    task.reminder_date, task.reminder_sent,
                    task.id
                ))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления задачи: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        """
        Удаляет задачу из базы данных по ID.
        
        Args:
            task_id: ID задачи для удаления
            
        Returns:
            True если задача удалена, False если ошибка или задача не найдена
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления задачи: {e}")
            return False

    def export_to_json(self) -> str:
        """
        Экспортирует все задачи в формат JSON (требование ТЗ 5.5.1).
        
        Returns:
            JSON строка с данными всех задач в формате:
            {"tasks": [{"id": 1, "title": "...", ...}, ...]}
            
        Note:
            Использует кодировку UTF-8 для корректного отображения
            русских символов (ensure_ascii=False).
        """
        import json
        tasks = self.get_all_tasks()
        tasks_data = [task.to_dict() for task in tasks]
        return json.dumps({"tasks": tasks_data}, ensure_ascii=False, indent=2)

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        Получает задачу по её ID.
        
        Args:
            task_id: ID задачи
            
        Returns:
            Объект Task или None если задача не найдена
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
                row = cursor.fetchone()

                if row:
                    task_dict = {
                        'id': row[0],
                        'title': row[1],
                        'description': row[2],
                        'priority': row[3],
                        'status': row[4],
                        'created_date': row[5],
                        'due_date': row[6],
                        'completed_date': row[7],
                        'reminder_date': row[8],  # ДОБАВИТЬ
                        'reminder_sent': bool(row[9])  # ДОБАВИТЬ
                    }
                    return Task.from_dict(task_dict)
                return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения задачи {task_id}: {e}")
            return None

    def get_tasks_by_status(self, status: Status) -> List[Task]:
        """
        Получает все задачи с указанным статусом.
        
        Args:
            status: Статус для фильтрации (Status enum)
            
        Returns:
            Список задач с указанным статусом
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE status = ?', (status.value,))
                tasks = []
                for row in cursor.fetchall():
                    task_dict = {
                        'id': row[0],
                        'title': row[1],
                        'description': row[2],
                        'priority': row[3],
                        'status': row[4],
                        'created_date': row[5],
                        'due_date': row[6],
                        'completed_date': row[7],
                        'reminder_date': row[8],  # ДОБАВИТЬ
                        'reminder_sent': bool(row[9])  # ДОБАВИТЬ
                    }
                    tasks.append(Task.from_dict(task_dict))
                return tasks
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения задач по статусу {status}: {e}")
            return []