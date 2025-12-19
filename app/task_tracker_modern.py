"""
Современная версия GUI с использованием CustomTkinter.
Оптимизированная версия с корректным центрированием и оптимальными размерами окон.
"""

import sys
import os
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import customtkinter as ctk
from tkinter import messagebox, filedialog
from core.database import Database
from core.models import Priority, Status
from services.task_service import TaskService
from services.notification_service import NotificationService


class TaskTrackerModern:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        os.makedirs("data", exist_ok=True)
        self.db = Database("data/tasks.db")
        self.task_service = TaskService(self.db)
        self.notification_service = NotificationService(self.task_service)

        # Переменные для состояния
        self.sort_filters = {"due_date": False, "priority": False, "created_date": False}
        self.current_filter = {"priority": None, "status": None}
        self.selected_task_id = None

        self._setup_window()
        self._create_widgets()
        self.refresh_tasks()

    def _setup_window(self):
        """Настройка основного окна с центрированием"""
        self.root = ctk.CTk()
        self.root.title("Task Tracker")

        # Устанавливаем оптимальный размер основного окна
        window_width = 1200
        window_height = 700

        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Вычисляем позицию для центрирования
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Устанавливаем размер и позицию
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1000, 600)  # Минимальный размер окна

    def _center_window(self, window, width, height):
        """Центрирование любого окна на экране"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        window.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self):
        """Создание всех виджетов интерфейса"""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок
        ctk.CTkLabel(main_frame, text="Task Tracker",
                    font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

        # Панель управления
        self._create_control_panel(main_frame)
        self._create_filter_panel(main_frame)
        self._create_task_list(main_frame)

    def _create_control_panel(self, parent):
        """Создание панели с кнопками управления"""
        buttons = [
            ("➕ Новая задача", self.create_task, None),
            ("✏️ Редактировать", self.edit_task, None),
            ("✅ Выполнена", self.complete_task, None),
            ("🗑️ Удалить", self.delete_task, ("red", "darkred")),
            ("⚠️ Просроченные", self.show_overdue_notifications, ("orange", "darkorange")),
            ("💾 Экспорт в JSON", self.export_to_json, None),
            ("🔄 Обновить", self.refresh_tasks, None)
        ]

        frame = ctk.CTkFrame(parent)
        frame.pack(pady=10, padx=10, fill="x")

        for text, command, colors in buttons[:-1]:
            btn = ctk.CTkButton(frame, text=text, command=command, width=120, height=32)
            if colors:
                btn.configure(fg_color=colors[0], hover_color=colors[1])
            btn.pack(side="left", padx=5)

        ctk.CTkButton(frame, text=buttons[-1][0], command=buttons[-1][1],
                     width=100, height=32).pack(side="right", padx=5)

    def _create_filter_panel(self, parent):
        """Создание панели фильтров и сортировки"""
        frame = ctk.CTkFrame(parent)
        frame.pack(pady=5, padx=10, fill="x")

        # Сортировка
        ctk.CTkLabel(frame, text="Сортировка:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

        self.sort_buttons = {}
        for key, text in [("due_date", "📅 По сроку"), ("priority", "⭐ По приоритету"),
                         ("created_date", "📆 По дате создания")]:
            btn = ctk.CTkButton(frame, text=text, width=[100, 120, 140][list(self.sort_filters.keys()).index(key)],
                              height=28, command=lambda k=key: self._toggle_sort(k))
            btn.pack(side="left", padx=2)
            self.sort_buttons[key] = btn

        # Фильтры
        ctk.CTkLabel(frame, text="Фильтры:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(20, 5))

        self.filter_buttons = {}
        for key, text in [("priority", "⭐ По приоритету"), ("status", "📋 По статусу")]:
            btn = ctk.CTkButton(frame, text=text, width=120, height=28,
                              command=lambda k=key: self._toggle_filter(k))
            btn.pack(side="left", padx=2)
            self.filter_buttons[key] = btn

    def _create_task_list(self, parent):
        """Создание списка задач"""
        list_frame = ctk.CTkFrame(parent)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовки таблицы
        headers = ["ID", "Название", "Статус", "Приоритет", "Срок"]
        widths = [0, 400, 300, 250, 170]

        header_frame = ctk.CTkFrame(list_frame)
        header_frame.pack(fill="x", padx=5, pady=5)

        for i, (header, width) in enumerate(zip(headers, widths)):
            if width > 0:
                ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=14, weight="bold"),
                           width=width, anchor="w").grid(row=0, column=i, padx=10, pady=5, sticky="w")

        # Скроллируемая область
        self.tasks_container = ctk.CTkScrollableFrame(list_frame)
        self.tasks_container.pack(fill="both", expand=True, padx=5, pady=5)
        self.task_widgets = []

    def _toggle_sort(self, sort_type):
        """Переключение сортировки"""
        for key in self.sort_filters:
            self.sort_filters[key] = (key == sort_type) and not self.sort_filters[key]
            self.sort_buttons[key].configure(fg_color=["#3B8ED0", "#1F6AA5"] if not self.sort_filters[key] else "green")
        self.refresh_tasks()

    def _toggle_filter(self, filter_type):
        """Переключение фильтра"""
        if filter_type == "priority":
            priorities = [Priority.HIGH, Priority.MEDIUM, Priority.LOW, None]
            texts = ["⭐ Высокий", "⭐ Средний", "⭐ Низкий", "⭐ По приоритету"]
            colors = ["red", "orange", "green", ["#3B8ED0", "#1F6AA5"]]

            current_idx = priorities.index(self.current_filter["priority"]) if self.current_filter["priority"] in priorities else -1
            new_idx = (current_idx + 1) % len(priorities)
            self.current_filter["priority"] = priorities[new_idx]
            self.filter_buttons["priority"].configure(text=texts[new_idx], fg_color=colors[new_idx])

        elif filter_type == "status":
            statuses = [Status.PLANNED, Status.IN_PROGRESS, Status.COMPLETED, None]
            texts = ["📋 Запланирована", "📋 В работе", "📋 Выполнена", "📋 По статусу"]
            colors = ["blue", "orange", "green", ["#3B8ED0", "#1F6AA5"]]

            current_idx = statuses.index(self.current_filter["status"]) if self.current_filter["status"] in statuses else -1
            new_idx = (current_idx + 1) % len(statuses)
            self.current_filter["status"] = statuses[new_idx]
            self.filter_buttons["status"].configure(text=texts[new_idx], fg_color=colors[new_idx])

        self.refresh_tasks()

    def refresh_tasks(self):
        """Обновление списка задач"""
        for widget in self.tasks_container.winfo_children():
            widget.destroy()

        self.task_widgets = []
        self.selected_task_id = None

        tasks = self.task_service.get_all_tasks()

        # Применение фильтров
        if self.current_filter["priority"]:
            tasks = self.task_service.filter_tasks(tasks, priority=self.current_filter["priority"])
        if self.current_filter["status"]:
            tasks = self.task_service.filter_tasks(tasks, status=self.current_filter["status"])

        # Применение сортировки
        for sort_type, active in self.sort_filters.items():
            if active:
                tasks = self.task_service.sort_tasks(tasks, sort_type)
                break

        # Отображение задач
        for task in tasks:
            self._create_task_item(task)

    def _create_task_item(self, task):
        """Создание элемента задачи в списке"""
        # Определение цвета фона
        bg_color = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ffffff"
        if task.is_overdue() and task.status != Status.COMPLETED:
            bg_color = "#ffe6e6" if ctk.get_appearance_mode() == "Light" else "#4a0000"
        elif task.status == Status.COMPLETED:
            bg_color = "#e8f5e9" if ctk.get_appearance_mode() == "Light" else "#1a3a1a"

        task_frame = ctk.CTkFrame(self.tasks_container, fg_color=bg_color)
        task_frame.pack(fill="x", padx=5, pady=3)

        # Данные для колонок
        columns = [
            (task.title[:60] + ("..." if len(task.title) > 60 else ""), 400, None, 13),
            (self._get_status_text(task), 300, self._get_status_color(task), 13),
            (task.priority.value.upper(), 250, self._get_priority_color(task.priority), 13),
            (task.due_date, 150, None, 13)
        ]

        # Создание колонок
        for i, (text, width, color, size) in enumerate(columns):
            font_weight = "bold" if i in [1, 2] else "normal"
            label = ctk.CTkLabel(task_frame, text=text, width=width, anchor="w",
                               font=ctk.CTkFont(size=size, weight=font_weight),
                               text_color=color or ("#1a1a1a" if ctk.get_appearance_mode() == "Light" else "#ffffff"))
            label.grid(row=0, column=i+1, padx=10, pady=8, sticky="w")

        task_frame.task_id = task.id

        # Привязка событий
        task_frame.bind("<Button-1>", lambda e, tid=task.id: self._select_task(tid, task_frame))
        task_frame.bind("<Double-Button-1>", lambda e, tid=task.id: self._edit_task_by_id(tid))

        for widget in task_frame.winfo_children():
            widget.bind("<Button-1>", lambda e, tid=task.id: self._select_task(tid, task_frame))
            widget.bind("<Double-Button-1>", lambda e, tid=task.id: self._edit_task_by_id(tid))

        self.task_widgets.append(task_frame)

    def _get_status_text(self, task):
        """Получение текста статуса с учетом просрочки"""
        if task.is_overdue() and task.status != Status.COMPLETED:
            return f"{task.status.value} (ПРОСРОЧЕНО)"
        return task.status.value

    def _get_status_color(self, task):
        """Получение цвета статуса"""
        if task.is_overdue() and task.status != Status.COMPLETED:
            return "#d32f2f"
        elif task.status == Status.COMPLETED:
            return "#388e3c"
        return "#666666"

    def _get_priority_color(self, priority):
        """Получение цвета приоритета"""
        colors = {
            Priority.HIGH: "#d32f2f",
            Priority.MEDIUM: "#f57c00",
            Priority.LOW: "#388e3c"
        }
        return colors.get(priority, "#666666")

    def _select_task(self, task_id, task_frame):
        """Выбор задачи"""
        self.selected_task_id = task_id
        for widget in self.task_widgets:
            widget.configure(border_width=0)
        task_frame.configure(border_width=2, border_color="blue")

    def _edit_task_by_id(self, task_id):
        """Редактирование задачи по ID"""
        self.selected_task_id = task_id
        self.edit_task()

    def create_task(self):
        """Диалог создания задачи"""
        self._task_dialog("Создание новой задачи", self._save_new_task)

    def edit_task(self):
        """Диалог редактирования задачи"""
        if not self.selected_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу для редактирования")
            return

        task = self.task_service.get_task(self.selected_task_id)
        if not task:
            messagebox.showerror("Ошибка", "Задача не найдена")
            return

        self._task_dialog("Редактирование задачи", lambda widgets: self._save_edited_task(task, widgets), task)

    def _task_dialog(self, title, save_callback, task=None):
        """Общий диалог для создания/редактирования задачи"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()

        # Оптимальный размер диалогового окна
        dialog_width = 700
        dialog_height = 650  # Увеличил высоту, чтобы все поля поместились

        # Центрируем диалог
        self._center_window(dialog, dialog_width, dialog_height)

        # Устанавливаем минимальный размер
        dialog.minsize(650, 600)

        # Создаем основной контейнер с прокруткой
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Скроллируемый контейнер для формы
        scroll_frame = ctk.CTkScrollableFrame(main_frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Заголовок
        ctk.CTkLabel(scroll_frame, text=title,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))

        # Поля формы - ВСЕ обязательные поля
        fields = [
            ("Название:", ctk.CTkEntry(scroll_frame, height=40, font=ctk.CTkFont(size=13)),
             task.title if task else ""),
            ("Описание:", ctk.CTkTextbox(scroll_frame, height=100, font=ctk.CTkFont(size=13)),
             task.description if task else ""),
            ("Приоритет:", ctk.CTkComboBox(scroll_frame, values=["низкий", "средний", "высокий"],
                                           height=40, font=ctk.CTkFont(size=13)),
             task.priority.value if task else "средний"),
            ("Статус:", ctk.CTkComboBox(scroll_frame, values=["Запланирована", "В работе", "Выполнена"],
                                        height=40, font=ctk.CTkFont(size=13)),
             task.status.value if task else "Запланирована"),
            ("Срок выполнения (ДД.ММ.ГГГГ):", ctk.CTkEntry(scroll_frame, height=40,
                                                           font=ctk.CTkFont(size=13)),
             task.due_date if task else "")
        ]

        widgets = {}
        for label_text, widget, default_value in fields:
            # Метка поля - обязательно показываем
            ctk.CTkLabel(scroll_frame, text=label_text,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5), anchor="w")

            # Виджет ввода
            if isinstance(widget, ctk.CTkEntry):
                widget.insert(0, default_value)
            elif isinstance(widget, ctk.CTkTextbox):
                widget.insert("1.0", default_value)
            else:
                widget.set(default_value)

            # Для текстового поля делаем фиксированную высоту
            if isinstance(widget, ctk.CTkTextbox):
                widget.pack(fill="x", pady=(0, 10))
            else:
                widget.pack(fill="x", pady=(0, 15))

            # Сохраняем виджет по имени (убираем двоеточие и скобки)
            key = label_text.split(":")[0].lower().replace(" (дд.мм.гггг)", "")
            widgets[key] = widget

        # Кнопки (вне скроллируемой области)
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(button_frame, text="Сохранить",
                      command=lambda: self._execute_save(save_callback, widgets, dialog),
                      width=150, height=40,
                      font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)

        ctk.CTkButton(button_frame, text="Отмена", command=dialog.destroy,
                      width=150, height=40, fg_color="gray",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)

    def _execute_save(self, save_callback, widgets, dialog):
        """Выполнение сохранения с проверкой данных"""
        try:
            if save_callback(widgets):
                dialog.destroy()
                self.refresh_tasks()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _save_new_task(self, widgets):
        """Сохранение новой задачи"""
        title = widgets["название"].get().strip()
        due_date = widgets["срок выполнения"].get().strip()

        if not title or not due_date:
            messagebox.showwarning("Внимание", "Заполните название и срок выполнения")
            return False

        self.task_service.create_task(
            title,
            widgets["описание"].get("1.0", "end-1c").strip(),
            Priority(widgets["приоритет"].get()),
            due_date
        )
        messagebox.showinfo("Успех", "Задача создана!")
        return True

    def _save_edited_task(self, task, widgets):
        """Сохранение изменений задачи"""
        title = widgets["название"].get().strip()
        due_date = widgets["срок выполнения"].get().strip()

        if not title or not due_date:
            messagebox.showwarning("Внимание", "Заполните название и срок выполнения")
            return False

        task.title = title
        task.description = widgets["описание"].get("1.0", "end-1c").strip()
        task.priority = Priority(widgets["приоритет"].get())
        task.status = Status(widgets["статус"].get())
        task.due_date = due_date

        if task.status == Status.COMPLETED and not task.completed_date:
            task.completed_date = datetime.now().strftime('%d.%m.%Y')
        elif task.status != Status.COMPLETED:
            task.completed_date = None

        if self.task_service.update_task(task):
            messagebox.showinfo("Успех", "Задача обновлена")
            return True

        messagebox.showerror("Ошибка", "Не удалось обновить задачу")
        return False

    def complete_task(self):
        """Отметка задачи как выполненной"""
        if not self._validate_selection():
            return

        task = self.task_service.get_task(self.selected_task_id)
        if task and self.task_service.complete_task(task.id):
            messagebox.showinfo("Успех", f"Задача '{task.title}' отмечена как выполненная")
            self.selected_task_id = None
            self.refresh_tasks()

    def delete_task(self):
        """Удаление задачи"""
        if not self._validate_selection():
            return

        task = self.task_service.get_task(self.selected_task_id)
        if task and messagebox.askyesno("Подтверждение", f"Удалить задачу '{task.title}'?"):
            if self.task_service.delete_task(task.id):
                messagebox.showinfo("Успех", f"Задача '{task.title}' удалена")
                self.selected_task_id = None
                self.refresh_tasks()

    def _validate_selection(self):
        """Проверка выбора задачи"""
        if not self.selected_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу")
            return False
        return True

    def show_overdue_notifications(self):
        """Показать просроченные задачи"""
        overdue_tasks = self.notification_service.check_overdue_tasks()
        if overdue_tasks:
            self._show_overdue_dialog(overdue_tasks)
        else:
            messagebox.showinfo("Информация", "У вас нет просроченных задач!")

    def _show_overdue_dialog(self, tasks):
        """Диалог просроченных задач с оптимальным размером"""
        if hasattr(self, '_notification_window') and self._notification_window:
            try:
                self._notification_window.destroy()
            except:
                pass

        self._notification_window = ctk.CTkToplevel(self.root)
        self._notification_window.title("⚠️ Просроченные задачи")
        self._notification_window.transient(self.root)
        self._notification_window.grab_set()

        # Оптимальный размер для окна с просроченными задачами
        window_width = 800
        window_height = 600

        # Центрируем окно
        self._center_window(self._notification_window, window_width, window_height)

        # Устанавливаем минимальный размер
        self._notification_window.minsize(700, 500)

        # Основной контейнер
        main_frame = ctk.CTkFrame(self._notification_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок
        ctk.CTkLabel(main_frame, text="⚠️ ВНИМАНИЕ! У вас есть просроченные задачи:",
                    font=ctk.CTkFont(size=18, weight="bold"), text_color="#d32f2f").pack(pady=(10, 20))

        # Список задач с прокруткой
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Заголовки таблицы
        headers = ["Название задачи", "Приоритет", "Срок выполнения", "Дней просрочено"]
        widths = [350, 150, 150, 150]

        header_frame = ctk.CTkFrame(list_frame)
        header_frame.pack(fill="x", padx=5, pady=5)

        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=13, weight="bold"),
                        width=width, anchor="w").grid(row=0, column=i, padx=5, sticky="w")

        # Скроллируемая область для задач
        scroll_frame = ctk.CTkScrollableFrame(list_frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._selected_overdue_task_id = None

        # Добавляем задачи
        for task in tasks:
            self._create_overdue_item(scroll_frame, task)

        # Панель кнопок
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(button_frame, text="✅ Отметить как выполненную",
                     command=self._mark_overdue_completed, height=40,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(button_frame, text="📅 Изменить срок",
                     command=self._extend_overdue_deadline, height=40,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(button_frame, text="Закрыть",
                     command=self._notification_window.destroy, height=40,
                     fg_color="gray", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=5, expand=True, fill="x")

    def _create_overdue_item(self, parent, task):
        """Создание элемента просроченной задачи"""
        frame = ctk.CTkFrame(parent, fg_color="#ffe6e6")
        frame.pack(fill="x", padx=5, pady=3)

        days_overdue = self._calculate_days_overdue(task.due_date)
        columns = [
            (task.title[:50] + ("..." if len(task.title) > 50 else ""), 350, None),
            (task.priority.value.upper(), 150, self._get_priority_color(task.priority)),
            (task.due_date, 150, None),
            (f"{days_overdue} дн.", 150, "#d32f2f")
        ]

        for i, (text, width, color) in enumerate(columns):
            weight = "bold" if i in [1, 3] else "normal"
            ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=12, weight=weight),
                        text_color=color or "#000", width=width, anchor="w")\
                .grid(row=0, column=i, padx=5, pady=5, sticky="w")

        frame.task_id = task.id
        frame.bind("<Button-1>", lambda e, tid=task.id: self._select_overdue_task(tid, frame))

        # Привязка для дочерних виджетов
        for widget in frame.winfo_children():
            widget.bind("<Button-1>", lambda e, tid=task.id: self._select_overdue_task(tid, frame))

    def _calculate_days_overdue(self, due_date):
        """Вычисление дней просрочки"""
        try:
            due_dt = datetime.strptime(due_date, '%d.%m.%Y')
            overdue_days = (datetime.now().date() - due_dt.date()).days
            return max(0, overdue_days)
        except ValueError:
            return 0

    def _select_overdue_task(self, task_id, frame):
        """Выбор просроченной задачи"""
        self._selected_overdue_task_id = task_id

        # Снимаем выделение со всех элементов
        for widget in frame.master.winfo_children():
            if hasattr(widget, 'task_id'):
                widget.configure(border_width=0)

        # Выделяем выбранный элемент
        frame.configure(border_width=2, border_color="blue")

    def _mark_overdue_completed(self):
        """Отметка просроченной задачи как выполненной"""
        if not self._selected_overdue_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу")
            return

        task = self.task_service.get_task(self._selected_overdue_task_id)
        if task and self.task_service.complete_task(task.id):
            messagebox.showinfo("Успех", f"Задача '{task.title}' отмечена как выполненная")
            self._notification_window.destroy()
            self.refresh_tasks()

    def _extend_overdue_deadline(self):
        """Изменение срока просроченной задачи"""
        if not self._selected_overdue_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу")
            return

        task = self.task_service.get_task(self._selected_overdue_task_id)
        if not task:
            return

        # Создаем диалог изменения срока
        dialog = ctk.CTkToplevel(self._notification_window)
        dialog.title("Изменить срок выполнения")
        dialog.transient(self._notification_window)
        dialog.grab_set()

        # Оптимальный размер диалога
        dialog_width = 500
        dialog_height = 300
        self._center_window(dialog, dialog_width, dialog_height)

        # Основной контейнер
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        ctk.CTkLabel(main_frame, text="Изменение срока выполнения",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        # Информация о задаче
        ctk.CTkLabel(main_frame, text=f"Задача: {task.title}",
                    font=ctk.CTkFont(size=13)).pack(pady=5)

        ctk.CTkLabel(main_frame, text="Новый срок (ДД.ММ.ГГГГ):",
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 5))

        entry = ctk.CTkEntry(main_frame, height=40, font=ctk.CTkFont(size=13))
        entry.insert(0, task.due_date)
        entry.pack(fill="x", pady=5)

        def save():
            try:
                datetime.strptime(entry.get(), '%d.%m.%Y')
                task.due_date = entry.get()
                if self.task_service.update_task(task):
                    messagebox.showinfo("Успех", "Срок выполнения изменен")
                    dialog.destroy()
                    self._notification_window.destroy()
                    self.refresh_tasks()
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ")

        # Кнопки
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(button_frame, text="Сохранить", command=save, height=40,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(button_frame, text="Отмена", command=dialog.destroy, height=40,
                     fg_color="gray", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=5, expand=True, fill="x")

    def export_to_json(self):
        """Экспорт в JSON"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Сохранить задачи в JSON"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.db.export_to_json())
                messagebox.showinfo("Успех", f"Задачи экспортированы в:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка экспорта:\n{str(e)}")

    def run(self):
        """Запуск приложения"""
        if self.task_service.process_reminders() > 0:
            messagebox.showinfo("Напоминания", "У вас есть напоминания!")

        self._setup_periodic_notifications()
        self.root.mainloop()

    def _setup_periodic_notifications(self):
        """Настройка периодических уведомлений"""
        if self.notification_service.check_overdue_tasks():
            self.show_overdue_notifications()
        self.root.after(3600000, self._setup_periodic_notifications)


if __name__ == "__main__":
    app = TaskTrackerModern()
    app.run()