import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
from typing import List
from core.models import Task, Status
from services.task_service import TaskService


class NotificationService:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service
        self.notification_window = None
        self.last_check = None

    def check_overdue_tasks(self) -> List[Task]:
        """Проверяет просроченные задачи"""
        all_tasks = self.task_service.get_all_tasks()
        overdue_tasks = []
        
        for task in all_tasks:
            if task.status != Status.COMPLETED and task.is_overdue():
                overdue_tasks.append(task)
        
        return overdue_tasks

    def show_overdue_notification(self, overdue_tasks: List[Task]):
        """Показывает уведомление о просроченных задачах"""
        if not overdue_tasks:
            return

        # Закрываем предыдущее окно уведомления если оно открыто
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.destroy()

        # Создаем новое окно уведомления
        self.notification_window = tk.Toplevel()
        self.notification_window.title("Просроченные задачи")
        self.notification_window.geometry("500x400")
        self.notification_window.resizable(False, False)
        
        # Делаем окно модальным
        self.notification_window.transient()
        self.notification_window.grab_set()

        # Заголовок
        header_frame = ttk.Frame(self.notification_window)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="⚠️ ВНИМАНИЕ! У вас есть просроченные задачи:", 
                 font=("Arial", 12, "bold"), foreground="red").pack()

        # Список просроченных задач
        list_frame = ttk.Frame(self.notification_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Создаем Treeview для отображения задач
        columns = ("Title", "Priority", "DueDate", "DaysOverdue")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        # Настройка колонок
        tree.heading("Title", text="Название задачи")
        tree.heading("Priority", text="Приоритет")
        tree.heading("DueDate", text="Срок выполнения")
        tree.heading("DaysOverdue", text="Дней просрочено")
        
        tree.column("Title", width=200)
        tree.column("Priority", width=80)
        tree.column("DueDate", width=120)
        tree.column("DaysOverdue", width=100)

        # Добавляем задачи в список
        for task in overdue_tasks:
            days_overdue = self._calculate_days_overdue(task.due_date)
            priority_color = self._get_priority_color(task.priority.value)
            
            item = tree.insert("", tk.END, values=(
                task.title,
                task.priority.value,
                task.due_date,
                f"{days_overdue} дн."
            ))
            
            # Цветовое выделение по приоритету
            if priority_color:
                tree.set(item, "Priority", task.priority.value)

        # Скроллбар
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопки
        button_frame = ttk.Frame(self.notification_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Отметить как выполненную", 
                  command=lambda: self._mark_selected_completed(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Изменить срок", 
                  command=lambda: self._extend_deadline(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Закрыть", 
                  command=self.notification_window.destroy).pack(side=tk.RIGHT, padx=5)

        # Центрируем окно
        self._center_window(self.notification_window)

    def _calculate_days_overdue(self, due_date: str) -> int:
        """Вычисляет количество дней просрочки"""
        try:
            due_dt = datetime.strptime(due_date, '%d.%m.%Y')
            today = datetime.now().date()
            overdue_days = (today - due_dt.date()).days
            return max(0, overdue_days)
        except ValueError:
            return 0

    def _get_priority_color(self, priority: str) -> str:
        """Возвращает цвет для приоритета"""
        colors = {
            "высокий": "red",
            "средний": "orange", 
            "низкий": "yellow"
        }
        return colors.get(priority, "black")

    def _mark_selected_completed(self, tree):
        """Отмечает выбранную задачу как выполненную"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу для отметки как выполненной")
            return

        item = selected[0]
        task_title = tree.item(item)['values'][0]
        
        # Находим задачу
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
                # Обновляем список
                self._refresh_notification_list(tree)
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить задачу")

    def _extend_deadline(self, tree):
        """Продлевает срок выполнения выбранной задачи"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу для изменения срока")
            return

        item = selected[0]
        task_title = tree.item(item)['values'][0]
        
        # Находим задачу
        tasks = self.task_service.get_all_tasks()
        task_to_extend = None
        for task in tasks:
            if task.title == task_title:
                task_to_extend = task
                break

        if not task_to_extend:
            messagebox.showerror("Ошибка", "Задача не найдена")
            return

        # Диалог для ввода нового срока
        dialog = tk.Toplevel(self.notification_window)
        dialog.title("Изменить срок выполнения")
        dialog.geometry("300x150")
        dialog.transient()
        dialog.grab_set()

        ttk.Label(dialog, text=f"Задача: {task_title}").pack(pady=5)
        ttk.Label(dialog, text="Новый срок (ГГГГ-ММ-ДД):").pack(pady=5)
        
        due_entry = ttk.Entry(dialog, width=20)
        due_entry.pack(pady=5)
        due_entry.insert(0, task_to_extend.due_date)

        def save_new_deadline():
            new_due_date = due_entry.get().strip()
            try:
                # Проверяем формат даты
                datetime.strptime(new_due_date, '%d.%m.%Y')
                
                # Обновляем задачу
                task_to_extend.due_date = new_due_date
                success = self.task_service.update_task(task_to_extend)
                
                if success:
                    messagebox.showinfo("Успех", "Срок выполнения изменен")
                    dialog.destroy()
                    self._refresh_notification_list(tree)
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить задачу")
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ")

        ttk.Button(dialog, text="Сохранить", command=save_new_deadline).pack(pady=10)

    def _refresh_notification_list(self, tree):
        """Обновляет список в окне уведомления"""
        # Очищаем список
        for item in tree.get_children():
            tree.delete(item)
        
        # Загружаем обновленные просроченные задачи
        overdue_tasks = self.check_overdue_tasks()
        for task in overdue_tasks:
            days_overdue = self._calculate_days_overdue(task.due_date)
            tree.insert("", tk.END, values=(
                task.title,
                task.priority.value,
                task.due_date,
                f"{days_overdue} дн."
            ))

    def _center_window(self, window):
        """Центрирует окно на экране"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def should_show_notification(self) -> bool:
        """Проверяет, нужно ли показывать уведомление"""
        # Показываем уведомление не чаще чем раз в час
        now = datetime.now()
        if self.last_check is None or (now - self.last_check).seconds >= 3600:
            self.last_check = now
            return True
        return False

    def show_periodic_notifications(self, parent_window):
        """Показывает периодические уведомления"""
        if not self.should_show_notification():
            return

        overdue_tasks = self.check_overdue_tasks()
        if overdue_tasks:
            self.show_overdue_notification(overdue_tasks)
        
        # Планируем следующую проверку через час
        parent_window.after(3600000, lambda: self.show_periodic_notifications(parent_window))
