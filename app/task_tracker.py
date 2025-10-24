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
        self.priority_filter = None
        
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
        ttk.Button(control_frame, text="Сортировка по сроку",
                   command=self.toggle_sort_by_due_date).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Фильтр по приоритету",
                   command=self.toggle_priority_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Обновить",
                   command=self.refresh_tasks).pack(side=tk.LEFT, padx=5)

        # Список задач
        self.tree = ttk.Treeview(self.root, columns=("Title", "Status", "Priority", "Due"), show="headings")
        self.tree.heading("Title", text="Название")
        self.tree.heading("Status", text="Статус")
        self.tree.heading("Priority", text="Приоритет")
        self.tree.heading("Due", text="Срок")

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def toggle_sort_by_due_date(self):
        """Переключает сортировку по дате срока"""
        self.sort_by_due_date = not self.sort_by_due_date
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

    def refresh_tasks(self):
        # Очищаем список
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Загружаем задачи
        tasks = self.task_service.get_all_tasks()
        
        # Применяем фильтрацию по приоритету если включена
        if self.priority_filter:
            tasks = self.task_service.filter_tasks(tasks, priority=self.priority_filter)
        
        # Применяем сортировку по дате срока если включена
        if self.sort_by_due_date:
            tasks = self.task_service.sort_tasks(tasks, "due_date")
        
        # Отображаем задачи
        for task in tasks:
            status_text = task.status.value
            if task.is_overdue() and task.status.value != "Выполнена":
                status_text = f"{task.status.value} (ПРОСРОЧЕНО)"

            self.tree.insert("", tk.END, values=(
                task.title,
                status_text,
                task.priority.value,
                task.due_date
            ))

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
        task_title = self.tree.item(item)['values'][0]
        
        # Находим задачу по названию
        tasks = self.task_service.get_all_tasks()
        task_to_edit = None
        for task in tasks:
            if task.title == task_title:
                task_to_edit = task
                break
        
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
            task_title = self.tree.item(item)['values'][0]
            
            # Находим задачу по названию
            tasks = self.task_service.get_all_tasks()
            task_to_complete = None
            for task in tasks:
                if task.title == task_title:
                    task_to_complete = task
                    break
            
            if task_to_complete:
                success = self.task_service.complete_task(task_to_complete.id)
                if success:
                    messagebox.showinfo("Успех", f"Задача '{task_title}' отмечена как выполненная")
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
            task_title = self.tree.item(item)['values'][0]
            
            if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task_title}'?"):
                # Находим задачу по названию
                tasks = self.task_service.get_all_tasks()
                task_to_delete = None
                for task in tasks:
                    if task.title == task_title:
                        task_to_delete = task
                        break
                
                if task_to_delete:
                    success = self.task_service.delete_task(task_to_delete.id)
                    if success:
                        messagebox.showinfo("Успех", f"Задача '{task_title}' удалена")
                    else:
                        messagebox.showerror("Ошибка", "Не удалось удалить задачу")
                else:
                    messagebox.showerror("Ошибка", "Задача не найдена")
                
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
