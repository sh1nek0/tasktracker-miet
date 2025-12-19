import tkinter as tk
from tkinter import ttk, messagebox
import os
from core.database import Database
from core.models import Priority, Status
from services.task_service import TaskService
from services.notification_service import NotificationService


class TaskTracker:
    def __init__(self):
        # Создаем папку data если её нет
        os.makedirs("data", exist_ok=True)
        self.db = Database("data/tasks.db")
        self.task_service = TaskService(self.db)
        self.notification_service = NotificationService(self.task_service)
        
        # Переменные для сортировки и фильтрации
        self.sort_by_due_date = False
        self.sort_by_priority = False
        self.sort_by_created_date = False
        self.priority_filter = None
        self.status_filter = None
        
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Task Tracker")
        self.root.geometry("1280x680")

        # Создаем интерфейс
        self.create_widgets()
        self.refresh_tasks()

    def create_widgets(self):
        # Панель управления
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)

        ttk.Button(control_frame, text="Новая задача",
                   command=self.create_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Редактировать",
                   command=self.edit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Выполнена",
                   command=self.complete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Удалить",
                   command=self.delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Просроченные",
                   command=self.show_overdue_notifications).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Экспорт в JSON",
                   command=self.export_to_json).pack(side=tk.LEFT, padx=5)
        # Вторая строка кнопок для сортировки и фильтров
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(pady=5)
        
        ttk.Label(filter_frame, text="Сортировка:").pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="По сроку",
                   command=self.toggle_sort_by_due_date).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="По приоритету",
                   command=self.toggle_sort_by_priority).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="По дате создания",
                   command=self.toggle_sort_by_created_date).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(filter_frame, text="Фильтры:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Button(filter_frame, text="По приоритету",
                   command=self.toggle_priority_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="По статусу",
                   command=self.toggle_status_filter).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(control_frame, text="Обновить",
                   command=self.refresh_tasks).pack(side=tk.LEFT, padx=5)

        # Список задач (добавляем скрытую колонку ID для надежной идентификации)
        self.tree = ttk.Treeview(self.root, columns=("ID", "Title", "Status", "Priority", "Due"), show="headings")
        self.tree.heading("Title", text="Название")
        self.tree.heading("Status", text="Статус")
        self.tree.heading("Priority", text="Приоритет")
        self.tree.heading("Due", text="Срок")
        
        # Скрываем колонку ID
        self.tree.column("ID", width=0, stretch=False)
        
        # Настройка цветов для просроченных задач
        self.tree.tag_configure("overdue", foreground="red", background="#ffe6e6")
        self.tree.tag_configure("completed", foreground="gray")
        self.tree.tag_configure("high_priority", foreground="darkred")
        self.tree.tag_configure("medium_priority", foreground="darkorange")
        self.tree.tag_configure("low_priority", foreground="darkgreen")

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def toggle_sort_by_due_date(self):
        """Переключает сортировку по дате срока"""
        self.sort_by_due_date = not self.sort_by_due_date
        if self.sort_by_due_date:
            self.sort_by_priority = False
            self.sort_by_created_date = False
        self.refresh_tasks()

    def toggle_sort_by_priority(self):
        """Переключает сортировку по приоритету"""
        self.sort_by_priority = not self.sort_by_priority
        if self.sort_by_priority:
            self.sort_by_due_date = False
            self.sort_by_created_date = False
        self.refresh_tasks()

    def toggle_sort_by_created_date(self):
        """Переключает сортировку по дате создания"""
        self.sort_by_created_date = not self.sort_by_created_date
        if self.sort_by_created_date:
            self.sort_by_due_date = False
            self.sort_by_priority = False
        self.refresh_tasks()

    def toggle_priority_filter(self):
        """Переключает фильтр по приоритету: Все -> Высокий -> Средний -> Низкий -> Все"""
        if self.priority_filter is None:
            self.priority_filter = Priority.HIGH
        elif self.priority_filter == Priority.HIGH:
            self.priority_filter = Priority.MEDIUM
        elif self.priority_filter == Priority.MEDIUM:
            self.priority_filter = Priority.LOW
        else:
            self.priority_filter = None
        self.refresh_tasks()

    def toggle_status_filter(self):
        """Переключает фильтр по статусу: Все -> Запланирована -> В работе -> Выполнена -> Все"""
        if self.status_filter is None:
            self.status_filter = Status.PLANNED
        elif self.status_filter == Status.PLANNED:
            self.status_filter = Status.IN_PROGRESS
        elif self.status_filter == Status.IN_PROGRESS:
            self.status_filter = Status.COMPLETED
        else:
            self.status_filter = None
        self.refresh_tasks()

    def refresh_tasks(self):
        # Очищаем список
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Загружаем задачи
        tasks = self.task_service.get_all_tasks()
        
        # Применяем фильтрацию по приоритету если включена
        if self.priority_filter:
            tasks = self.task_service.filter_tasks(tasks, priority=self.priority_filter)
        
        # Применяем фильтрацию по статусу если включена
        if self.status_filter:
            tasks = self.task_service.filter_tasks(tasks, status=self.status_filter)
        
        # Применяем сортировку
        if self.sort_by_due_date:
            tasks = self.task_service.sort_tasks(tasks, "due_date")
        elif self.sort_by_priority:
            tasks = self.task_service.sort_tasks(tasks, "priority")
        elif self.sort_by_created_date:
            tasks = self.task_service.sort_tasks(tasks, "created_date")
        
        # Отображаем задачи
        for task in tasks:
            status_text = task.status.value
            tags = []
            
            # Определяем теги для цветового выделения
            if task.is_overdue() and task.status != Status.COMPLETED:
                status_text = f"{task.status.value} (ПРОСРОЧЕНО)"
                tags.append("overdue")
            
            if task.status == Status.COMPLETED:
                tags.append("completed")
            
            # Цветовое выделение по приоритету
            if task.priority == Priority.HIGH:
                tags.append("high_priority")
            elif task.priority == Priority.MEDIUM:
                tags.append("medium_priority")
            elif task.priority == Priority.LOW:
                tags.append("low_priority")

            self.tree.insert("", tk.END, values=(
                task.id,  # ID для надежной идентификации
                task.title,
                status_text,
                task.priority.value,
                task.due_date
            ), tags=tags if tags else [])

    def create_task(self):
        # Диалог создания задачи
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая задача")
        dialog.geometry("400x300")

        # Название
        ttk.Label(dialog, text="Название:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        title_entry = ttk.Entry(dialog, width=40)
        title_entry.grid(row=0, column=1, padx=5, pady=5)

        # Описание
        ttk.Label(dialog, text="Описание:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        desc_text = tk.Text(dialog, width=40, height=4)
        desc_text.grid(row=1, column=1, padx=5, pady=5)

        # Приоритет
        ttk.Label(dialog, text="Приоритет:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        priority_var = tk.StringVar(value="средний")
        priority_combo = ttk.Combobox(dialog, textvariable=priority_var, 
                                    values=["низкий", "средний", "высокий"], state="readonly")
        priority_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Срок выполнения
        ttk.Label(dialog, text="Срок (ДД.ММ.ГГГГ):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        due_entry = ttk.Entry(dialog, width=40)
        due_entry.grid(row=3, column=1, padx=5, pady=5)

        def save_task():
            title = title_entry.get().strip()
            description = desc_text.get("1.0", tk.END).strip()
            priority = Priority(priority_var.get())
            due_date = due_entry.get().strip()

            if title and due_date:
                try:
                    self.task_service.create_task(title, description, priority, due_date)
                    dialog.destroy()
                    self.refresh_tasks()
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))
            else:
                messagebox.showwarning("Внимание", "Заполните название и срок выполнения")

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=save_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу для редактирования")
            return

        item = selected[0]
        task_id = self.tree.item(item)['values'][0]  # Получаем ID из скрытой колонки
        
        # Находим задачу по ID (более надежно, чем по названию)
        task_to_edit = self.task_service.get_task(task_id)
        
        if not task_to_edit:
            messagebox.showerror("Ошибка", "Задача не найдена")
            return

        # Диалог редактирования задачи
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактировать задачу")
        dialog.geometry("400x300")

        # Название
        ttk.Label(dialog, text="Название:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        title_entry = ttk.Entry(dialog, width=40)
        title_entry.grid(row=0, column=1, padx=5, pady=5)
        title_entry.insert(0, task_to_edit.title)

        # Описание
        ttk.Label(dialog, text="Описание:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        desc_text = tk.Text(dialog, width=40, height=4)
        desc_text.grid(row=1, column=1, padx=5, pady=5)
        desc_text.insert("1.0", task_to_edit.description)

        # Приоритет
        ttk.Label(dialog, text="Приоритет:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        priority_var = tk.StringVar(value=task_to_edit.priority.value)
        priority_combo = ttk.Combobox(dialog, textvariable=priority_var, 
                                    values=["низкий", "средний", "высокий"], state="readonly")
        priority_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Статус
        ttk.Label(dialog, text="Статус:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        status_var = tk.StringVar(value=task_to_edit.status.value)
        status_combo = ttk.Combobox(dialog, textvariable=status_var,
                                  values=["Запланирована", "В работе", "Выполнена"], state="readonly")
        status_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Срок выполнения
        ttk.Label(dialog, text="Срок (ДД.ММ.ГГГГ):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        due_entry = ttk.Entry(dialog, width=40)
        due_entry.grid(row=4, column=1, padx=5, pady=5)
        due_entry.insert(0, task_to_edit.due_date)

        def save_changes():
            title = title_entry.get().strip()
            description = desc_text.get("1.0", tk.END).strip()
            priority = priority_var.get()
            status = status_var.get()
            due_date = due_entry.get().strip()

            if not title or not due_date:
                messagebox.showwarning("Внимание", "Заполните название и срок выполнения")
                return

            try:
                # Обновляем задачу
                task_to_edit.title = title
                task_to_edit.description = description
                task_to_edit.priority = Priority(priority)
                task_to_edit.status = Status(status)
                task_to_edit.due_date = due_date

                # Если статус изменился на "Выполнена", устанавливаем дату выполнения
                if status == "Выполнена" and not task_to_edit.completed_date:
                    from datetime import datetime
                    task_to_edit.completed_date = datetime.now().strftime('%d.%m.%Y')
                elif status != "Выполнена":
                    task_to_edit.completed_date = None

                success = self.task_service.update_task(task_to_edit)
                if success:
                    messagebox.showinfo("Успех", "Задача обновлена")
                    dialog.destroy()
                    self.refresh_tasks()
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить задачу")
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e))

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def complete_task(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            task_id = self.tree.item(item)['values'][0]  # Получаем ID из скрытой колонки
            
            # Находим задачу по ID
            task_to_complete = self.task_service.get_task(task_id)
            
            if task_to_complete:
                success = self.task_service.complete_task(task_to_complete.id)
                if success:
                    messagebox.showinfo("Успех", f"Задача '{task_to_complete.title}' отмечена как выполненная")
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить задачу")
            else:
                messagebox.showerror("Ошибка", "Задача не найдена")
            
            self.refresh_tasks()
        else:
            messagebox.showwarning("Внимание", "Выберите задачу для выполнения")

    def delete_task(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            task_id = self.tree.item(item)['values'][0]  # Получаем ID из скрытой колонки
            task_title = self.tree.item(item)['values'][1]  # Название для отображения
            
            if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task_title}'?"):
                # Удаляем задачу по ID
                success = self.task_service.delete_task(task_id)
                if success:
                    messagebox.showinfo("Успех", f"Задача '{task_title}' удалена")
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить задачу")
                
                self.refresh_tasks()
        else:
            messagebox.showwarning("Внимание", "Выберите задачу для удаления")

    def show_overdue_notifications(self):
        """Показывает уведомления о просроченных задачах"""
        overdue_tasks = self.notification_service.check_overdue_tasks()
        if overdue_tasks:
            self.notification_service.show_overdue_notification(overdue_tasks)
        else:
            messagebox.showinfo("Информация", "У вас нет просроченных задач!")

    def export_to_json(self):
        """Экспортирует все задачи в файл JSON (требование ТЗ 5.5.1)"""
        from tkinter import filedialog
        import json
        
        # Запрашиваем путь для сохранения файла
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Сохранить задачи в JSON"
        )
        
        if filename:
            try:
                # Получаем JSON строку из базы данных
                json_data = self.db.export_to_json()
                
                # Сохраняем в файл
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                
                messagebox.showinfo("Успех", f"Задачи успешно экспортированы в файл:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать задачи:\n{str(e)}")

    def run(self):
        # Проверяем напоминания при запуске
        reminders_count = self.task_service.process_reminders()
        if reminders_count > 0:
            messagebox.showinfo("Напоминания", f"Есть {reminders_count} напоминаний!")

        # Запускаем периодические уведомления
        self.notification_service.show_periodic_notifications(self.root)

        self.root.mainloop()


if __name__ == "__main__":
    app = TaskTracker()
    app.run()
