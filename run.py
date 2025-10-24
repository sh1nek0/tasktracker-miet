#!/usr/bin/env python3
import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Запускаем приложение
if __name__ == "__main__":
    from app.main import TaskTracker
    app = TaskTracker()
    app.run()
