import os
import sys
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import threading

class ImageSorter:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Sorter")
        self.root.geometry("1200x800")  # Фиксированный начальный размер окна
        
        # Инициализируем переменные
        self.current_image = None
        self.current_photo = None  # Сохраняем ссылку на PhotoImage
        self.image_files = []
        self.current_index = -1
        self.folders = []
        self.folder_hotkeys = {}  # Словарь для хранения горячих клавиш папок
        self.processed_images = 0  # Счетчик обработанных изображений
        self.total_images = 0  # Общее количество изображений
        self.resize_timer = None  # Таймер для отложенного обновления размера
        
        # Получаем путь к папке, в которой находится скрипт
        if getattr(sys, 'frozen', False):
            self.app_path = os.path.dirname(sys.executable)
        else:
            self.app_path = os.path.dirname(os.path.abspath(__file__))
        
        # Поддерживаемые форматы изображений
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # Создаем интерфейс
        self.create_ui()
        
        # Привязываем обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Запускаем загрузку в фоне после создания интерфейса
        self.root.after(100, self.initialize_app)
    
    def initialize_app(self):
        """Инициализация приложения после создания интерфейса"""
        # Загружаем список папок
        self.folders = self.get_existing_folders()
        self.create_folder_buttons()
        
        # Загружаем изображения
        self.load_images()
        
        # Привязываем горячие клавиши
        self.bind_keys()
        
        # Добавляем обработчики изменения размера окна
        self.root.bind("<Configure>", self.on_window_resize)
        self.root.bind("<F11>", self.on_fullscreen)  # Для F11
        self.root.bind("<Escape>", self.on_fullscreen)  # Для выхода из полноэкранного режима
        
        # Отслеживаем состояние полноэкранного режима
        self.is_fullscreen = False
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        # Очищаем ссылки на изображения
        self.current_image = None
        self.current_photo = None
        self.image_label.configure(image='')
        
        # Закрываем окно
        self.root.quit()
        self.root.destroy()
    
    def get_existing_folders(self):
        """Получает список существующих папок в директории"""
        folders = []
        for item in os.listdir(self.app_path):
            item_path = os.path.join(self.app_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                folders.append(item)
        return sorted(folders)
    
    def create_ui(self):
        """Создает пользовательский интерфейс"""
        # Главный контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Боковая панель
        sidebar = ttk.Frame(main_container, padding=(10, 10), width=300)  # Фиксированная ширина
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar.pack_propagate(False)  # Запрещаем изменение размера
        
        # Кнопка "Пропустить"
        skip_frame = ttk.Frame(sidebar)
        skip_frame.pack(fill=tk.X, pady=(0, 10))
        
        skip_btn = ttk.Button(
            skip_frame,
            text="Пропустить",
            command=self.show_next_image
        )
        skip_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Метка с хоткеем для пропуска
        skip_hotkey = ttk.Label(skip_frame, text="[Space]", padding=(5, 0))
        skip_hotkey.pack(side=tk.LEFT)
        
        # Создаем фрейм для списка папок
        self.folders_frame = ttk.Frame(sidebar)
        self.folders_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для кнопок папок
        self.buttons_frame = ttk.Frame(self.folders_frame)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем кнопки для папок
        self.create_folder_buttons()
        
        # Кнопка добавления новой папки
        add_btn = ttk.Button(sidebar, text="+ Добавить папку", command=self.add_folder)
        add_btn.pack(fill=tk.X, pady=(10, 0))
        
        # Информация
        info_frame = ttk.LabelFrame(sidebar, text="Информация", padding=(5, 5))
        info_frame.pack(fill=tk.X, pady=10)
        
        # Текущий файл
        self.filename_var = tk.StringVar()
        filename_label = ttk.Label(info_frame, textvariable=self.filename_var, wraplength=250)  # Ограничиваем ширину текста
        filename_label.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)
        
        # Счетчик обработанных
        self.images_count_var = tk.StringVar(value="Обработано: 0")
        ttk.Label(info_frame, textvariable=self.images_count_var).pack(anchor=tk.W)
        
        # Статус
        self.status_var = tk.StringVar(value="Загрузка изображений...")
        ttk.Label(sidebar, textvariable=self.status_var).pack(anchor=tk.W, pady=10)
        
        # Контейнер для изображения
        self.image_frame = ttk.Frame(main_container)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Метка для отображения изображения
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
    
    def create_folder_buttons(self):
        """Создает кнопки для всех папок"""
        # Очищаем фрейм кнопок
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # Создаем кнопки для папок
        for i, folder in enumerate(self.folders):
            frame = ttk.Frame(self.buttons_frame)
            frame.pack(fill=tk.X, pady=2)
            
            # Кнопка для перемещения файла
            btn = ttk.Button(
                frame,
                text=folder,
                command=lambda idx=i: self.move_to_folder(idx)
            )
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Кнопка выбора горячей клавиши
            hotkey = self.folder_hotkeys.get(folder, str(i + 1))
            hotkey_btn = ttk.Button(
                frame,
                text=f"[{hotkey}]",
                width=4,
                command=lambda f=folder: self.show_hotkey_menu(f)
            )
            hotkey_btn.pack(side=tk.LEFT, padx=2)
            
            # Кнопка редактирования
            edit_btn = ttk.Button(
                frame,
                text="✎",
                width=3,
                command=lambda f=folder: self.rename_folder(f)
            )
            edit_btn.pack(side=tk.LEFT, padx=2)
            
            # Кнопка удаления
            del_btn = ttk.Button(
                frame,
                text="✖",
                width=3,
                command=lambda f=folder: self.delete_folder(f)
            )
            del_btn.pack(side=tk.LEFT)
    
    def show_hotkey_menu(self, folder):
        """Показывает меню выбора горячей клавиши"""
        menu = tk.Menu(self.root, tearoff=0)
        
        # Добавляем пункты меню для каждой цифры
        for i in range(1, 10):
            # Проверяем, не занята ли эта горячая клавиша другой папкой
            used_by = None
            for f, h in self.folder_hotkeys.items():
                if h == str(i) and f != folder:
                    used_by = f
                    break
            
            if used_by:
                # Если клавиша занята, показываем это в меню
                menu.add_command(
                    label=f"{i} (используется для '{used_by}')",
                    state='disabled'
                )
            else:
                # Если клавиша свободна, позволяем её выбрать
                menu.add_command(
                    label=str(i),
                    command=lambda num=i: self.set_folder_hotkey(folder, str(num))
                )
        
        # Показываем меню под кнопкой
        menu.post(
            self.root.winfo_pointerx(),
            self.root.winfo_pointery()
        )
    
    def set_folder_hotkey(self, folder, hotkey):
        """Устанавливает горячую клавишу для папки"""
        self.folder_hotkeys[folder] = hotkey
        self.create_folder_buttons()
        self.bind_keys()
    
    def add_folder(self):
        """Добавляет новую папку"""
        name = simpledialog.askstring("Новая папка", "Введите название папки:")
        if name:
            if name in self.folders:
                messagebox.showerror("Ошибка", "Папка с таким названием уже существует")
                return
            
            try:
                # Создаем папку
                folder_path = os.path.join(self.app_path, name)
                os.makedirs(folder_path)
                
                # Добавляем в список
                self.folders.append(name)
                self.folders.sort()  # Сортируем список папок
                
                # Обновляем интерфейс
                self.create_folder_buttons()
                self.status_var.set(f"Добавлена папка: {name}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку: {str(e)}")
    
    def rename_folder(self, old_name):
        """Переименовывает существующую папку"""
        new_name = simpledialog.askstring("Переименовать папку", 
                                        "Введите новое название папки:", 
                                        initialvalue=old_name)
        if new_name and new_name != old_name:
            if new_name in self.folders:
                messagebox.showerror("Ошибка", "Папка с таким названием уже существует")
                return
            
            try:
                # Переименовываем папку
                old_path = os.path.join(self.app_path, old_name)
                new_path = os.path.join(self.app_path, new_name)
                os.rename(old_path, new_path)
                
                # Обновляем список
                idx = self.folders.index(old_name)
                self.folders[idx] = new_name
                self.folders.sort()  # Сортируем список папок
                
                # Обновляем интерфейс
                self.create_folder_buttons()
                self.status_var.set(f"Папка переименована: {old_name} → {new_name}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переименовать папку: {str(e)}")
    
    def delete_folder(self, folder_name):
        """Удаляет папку"""
        if len(self.folders) <= 1:
            messagebox.showerror("Ошибка", "Нельзя удалить последнюю папку")
            return
        
        if messagebox.askyesno("Подтверждение", 
                              f"Удалить папку '{folder_name}'?\n\n" +
                              "Внимание: все файлы в папке также будут удалены!"):
            try:
                # Удаляем папку
                folder_path = os.path.join(self.app_path, folder_name)
                shutil.rmtree(folder_path)
                
                # Обновляем список
                self.folders.remove(folder_name)
                
                # Обновляем интерфейс
                self.create_folder_buttons()
                self.status_var.set(f"Папка удалена: {folder_name}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить папку: {str(e)}")
    
    def bind_keys(self):
        """Привязка горячих клавиш"""
        # Навигация
        self.root.bind("<Right>", lambda event: self.show_next_image())
        self.root.bind("<Left>", lambda event: self.show_prev_image())
        self.root.bind("<space>", lambda event: self.show_next_image())  # Пропуск изображения
        
        # Горячие клавиши для папок
        # Сначала удаляем все старые привязки цифр
        for i in range(1, 10):
            self.root.unbind(str(i))
        
        # Создаем словарь для быстрого поиска индекса папки по горячей клавише
        hotkey_to_index = {}
        for i, folder in enumerate(self.folders):
            hotkey = self.folder_hotkeys.get(folder, str(i + 1))
            hotkey_to_index[hotkey] = i
        
        # Привязываем горячие клавиши
        for hotkey, idx in hotkey_to_index.items():
            self.root.bind(hotkey, lambda e, idx=idx: self.move_to_folder(idx))
    
    def load_images(self):
        """Загружает список изображений из текущей директории"""
        try:
            # Получаем список всех файлов с изображениями
            self.image_files = [
                os.path.join(self.app_path, f) for f in os.listdir(self.app_path)
                if os.path.isfile(os.path.join(self.app_path, f)) and  # Проверяем что это файл
                os.path.splitext(f)[1].lower() in self.image_extensions
            ]
            
            if self.image_files:
                # Сортируем файлы по имени
                self.image_files.sort()
                # Обновляем общее количество изображений
                self.total_images = len(self.image_files)
                # Обновляем счетчик
                self.update_counter()
                # Показываем первое изображение
                self.show_image(0)
                self.status_var.set("Готово")
            else:
                self.status_var.set("Изображения не найдены в текущей папке")
                
        except Exception as e:
            self.status_var.set(f"Ошибка при сканировании: {str(e)}")
    
    def update_counter(self):
        """Обновляет счетчик обработанных изображений"""
        self.images_count_var.set(f"Обработано: {self.processed_images}/{self.total_images}")
    
    def on_window_resize(self, event):
        """Обработчик изменения размера окна"""
        # Проверяем, что событие пришло от главного окна
        if event.widget == self.root:
            # Отменяем предыдущий отложенный вызов
            if self.resize_timer:
                self.root.after_cancel(self.resize_timer)
            # Создаем новый отложенный вызов
            self.resize_timer = self.root.after(100, self.update_image_size)
    
    def update_image_size(self):
        """Обновляет размер изображения в соответствии с размером окна"""
        if not self.current_image:
            return
            
        # Получаем размеры области отображения
        frame_width = self.image_frame.winfo_width()
        frame_height = self.image_frame.winfo_height()
        
        if frame_width <= 1 or frame_height <= 1:  # Окно еще не отрисовано
            self.resize_timer = self.image_frame.after(100, self.update_image_size)
            return
            
        # Получаем размеры изображения
        img_width, img_height = self.current_image.size
        
        # Вычисляем соотношение сторон
        frame_ratio = frame_width / frame_height
        img_ratio = img_width / img_height
        
        # Определяем новые размеры
        if frame_ratio > img_ratio:
            # Ограничение по высоте
            new_height = frame_height
            new_width = int(new_height * img_ratio)
        else:
            # Ограничение по ширине
            new_width = frame_width
            new_height = int(new_width / img_ratio)
        
        # Масштабируем изображение
        resized_image = self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Создаем новый PhotoImage и сохраняем ссылку
        self.current_photo = ImageTk.PhotoImage(resized_image)
        self.image_label.configure(image=self.current_photo)
    
    def show_image(self, index):
        """Показывает изображение с указанным индексом"""
        if not self.image_files or index < 0 or index >= len(self.image_files):
            return
        
        self.current_index = index
        file_path = self.image_files[index]
        file_name = os.path.basename(file_path)
        name, ext = os.path.splitext(file_name)
        
        # Обновляем имя файла
        self.filename_var.set(f"Файл: {name} [{ext.lower()}]")
        
        try:
            # Загружаем изображение с помощью PIL
            self.current_image = Image.open(file_path)
            
            # Привязываем обновление размера к следующему циклу событий
            self.root.after_idle(self.update_image_size)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")
    
    def show_next_image(self):
        self.show_image(self.current_index + 1)
    
    def show_prev_image(self):
        self.show_image(self.current_index - 1)
    
    def move_to_folder(self, folder_index):
        """Перемещает текущее изображение в выбранную папку"""
        if not self.current_image or folder_index >= len(self.folders):
            return
        
        try:
            # Создаем папку, если её нет
            folder_name = self.folders[folder_index]
            folder_path = os.path.join(self.app_path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            # Перемещаем файл
            src = self.image_files[self.current_index]
            dst = os.path.join(folder_path, os.path.basename(src))
            shutil.move(src, dst)
            
            # Удаляем файл из списка и показываем следующий
            self.image_files.pop(self.current_index)
            if self.image_files:
                if self.current_index >= len(self.image_files):
                    self.current_index = 0
                self.show_image(self.current_index)
            else:
                self.current_image = None
                self.image_label.configure(image='')
                self.status_var.set("Все изображения обработаны")
            
            # Увеличиваем счетчик обработанных изображений
            self.processed_images += 1
            self.update_counter()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось переместить файл: {str(e)}")
    
    def format_file_size(self, bytes):
        """Форматирует размер файла в читаемый вид"""
        if bytes < 1024:
            return f"{bytes} байт"
        elif bytes < 1048576:
            return f"{bytes/1024:.1f} КБ"
        else:
            return f"{bytes/1048576:.1f} МБ"
    
    def on_window_map(self, event):
        """Обработчик изменения состояния окна (максимизация/восстановление)"""
        # Используем after, чтобы дать окну время обновить свои размеры
        self.root.after(100, self.update_image_size)
    
    def on_fullscreen(self, event=None):
        """Обработчик переключения полноэкранного режима"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        # Используем after, чтобы дать окну время обновить свои размеры
        self.root.after(100, self.update_image_size)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSorter(root)
    root.mainloop()
