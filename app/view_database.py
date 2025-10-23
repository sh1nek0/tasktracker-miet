import sqlite3
from core.database import Database


def view_database():
    print(" ==== Просмотр базы данных ====")

    db_path = "data/tasks.db"

    # Подключаемся к базе
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Показываем все таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nТаблицы в базе:")
    for table in tables:
        print(f"  - {table[0]}")

    print(f"\nСтруктура таблицы 'tasks':")
    cursor.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]}. {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")

    # Показываем данные в таблице tasks
    print(f"\nДанные в таблице 'tasks':")
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    if not tasks:
        print("Задач нет")
    else:
        for task in tasks:
            print(f"  ID: {task[0]}, Название: '{task[1]}', Статус: {task[4]}")

    # Показываем количество задач
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    print(f"\nВсего задач: {count}")

    conn.close()


if __name__ == "__main__":
    view_database()