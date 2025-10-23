import os
from core.database import Database


def main():

    # Создаем папку data если её нет
    os.makedirs("data", exist_ok=True)

    # Создаем базу данных - она автоматически инициализируется
    db = Database("data/tasks.db")

    # Проверяем что база работает
    tasks = db.get_all_tasks()
    print(f"База данных создана: data/tasks.db")
    print(f"Задач в базе: {len(tasks)}")

    # Создаем тестовую задачу для проверки
    from core.models import Task, Status, Priority
    from datetime import datetime

    test_task = Task(
        id=0,
        title="Добро пожаловать в Task Tracker!",
        description="Это первая тестовая задача",
        priority=Priority.MEDIUM,
        status=Status.PLANNED,
        created_date=datetime.now().strftime('%Y-%m-%d'),
        due_date="2025-10-23"
    )

    task_id = db.create_task(test_task)

if __name__ == "__main__":
    main()