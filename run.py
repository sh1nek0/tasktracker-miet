"""
Точка входа для Task Tracker.

Использование:
    python run.py              # Запуск стандартной версии (Tkinter)
    python run.py --classic    # Запуск современной версии (CustomTkinter)
"""

import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Запускаем приложение
if __name__ == "__main__":
    # Проверяем аргументы командной строки
    use_classic = "--classic" in sys.argv or "-c" in sys.argv
    
    if use_classic:
        # Запуск классической версии (Tkinter)
        from app.task_tracker import TaskTracker
        print("Запуск классической версии интерфейса (Tkinter)...")
    else:
        # По умолчанию используем современную версию (CustomTkinter)
        try:
            from app.task_tracker_modern import TaskTrackerModern as TaskTracker
            print("Запуск современной версии интерфейса (CustomTkinter)...")
        except ImportError:
            print("Ошибка: CustomTkinter не установлен!")
            print("Установите его командой: pip install customtkinter")
            print("Запуск классической версии...")
            from app.task_tracker import TaskTracker
    
    app = TaskTracker()
    app.run()
