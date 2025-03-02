import os
import sys
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import threading
import time

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
        self.is_processing = False  # Флаг для защиты от двойного клика
        self.folder_buttons = {}  # Словарь для хранения кнопок папок
        self.current_file = None  # Текущий обрабатываемый файл
        self.processing_lock = False  # Блокировка обработки
        self.animation_frames = []  # Кадры анимации
        self.animation_timer = None  # Таймер для анимации
        
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
        """Создает кнопки для каждой папки"""
        # Очищаем словарь кнопок
        self.folder_buttons.clear()
        
        # Удаляем старые кнопки
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # Создаем новые кнопки для каждой папки
        for i, folder in enumerate(self.folders):
            frame = ttk.Frame(self.buttons_frame)
            frame.pack(fill=tk.X, pady=2)
            
            # Создаем кнопку
            btn = ttk.Button(
                frame,
                text=folder,
            )
            # Привязываем обработчик через bind вместо command
            btn.bind('<Button-1>', lambda e, idx=i: self.handle_folder_click(e, idx))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Сохраняем кнопку в словарь
            self.folder_buttons[folder] = btn
            
            # Добавляем метку с горячей клавишей
            if folder in self.folder_hotkeys:
                hotkey_label = ttk.Label(frame, text=f"[{self.folder_hotkeys[folder]}]", padding=(5, 0))
                hotkey_label.pack(side=tk.LEFT)
            
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
    
    def handle_folder_click(self, event, folder_index):
        """Обработчик клика по кнопке папки"""
        # Получаем кнопку, на которую нажали
        btn = event.widget
        
        # Проверяем блокировки
        if self.processing_lock or str(btn['state']) == 'disabled':
            return
            
        # Проверяем базовые условия
        if not self.current_image or folder_index >= len(self.folders):
            return
            
        try:
            # Устанавливаем блокировку
            self.processing_lock = True
            
            # Проверяем, что текущий файл существует и не изменился
            if not self.current_file or self.current_file != self.image_files[self.current_index]:
                return
                
            # Проверяем, существует ли исходный файл
            src = self.image_files[self.current_index]
            if not os.path.exists(src):
                return
                
            # Блокируем все кнопки папок
            for btn in self.folder_buttons.values():
                btn.configure(state='disabled')
            
            # Создаем папку, если её нет
            folder_name = self.folders[folder_index]
            folder_path = os.path.join(self.app_path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            # Получаем путь назначения
            dst = os.path.join(folder_path, os.path.basename(src))
            
            # Закрываем текущее изображение и очищаем память
            if self.current_image:
                self.current_image.close()
            self.current_image = None
            self.current_photo = None
            self.image_label.configure(image='')
            
            # Даем время на освобождение файла
            self.root.update()
            time.sleep(0.1)
            
            # Пробуем разные способы перемещения файла
            success = False
            try:
                # Сначала пробуем просто переместить
                shutil.move(src, dst)
                success = True
            except:
                try:
                    # Если не получилось, пробуем копировать и удалить
                    shutil.copy2(src, dst)
                    os.remove(src)
                    success = True
                except:
                    pass
            
            if success:
                # Удаляем файл из списка и показываем следующий
                self.image_files.pop(self.current_index)
                if self.image_files:
                    if self.current_index >= len(self.image_files):
                        self.current_index = 0
                    self.show_image(self.current_index)
                else:
                    self.current_image = None
                    self.current_file = None
                    self.image_label.configure(image='')
                    self.status_var.set("Все изображения обработаны")
                
                # Увеличиваем счетчик обработанных изображений
                self.processed_images += 1
                self.update_counter()
            else:
                # Если не удалось переместить, просто пропускаем файл
                self.show_next_image()
            
        finally:
            # Разблокируем кнопки и снимаем блокировку
            self.processing_lock = False
            for btn in self.folder_buttons.values():
                btn.configure(state='normal')
    
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
        
        try:
            # Останавливаем предыдущую анимацию если была
            if self.animation_timer:
                self.root.after_cancel(self.animation_timer)
                self.animation_timer = None
            self.animation_frames.clear()
            
            # Сохраняем текущий файл
            self.current_file = self.image_files[index]
            
            # Загружаем и отображаем изображение
            self.current_index = index
            self.current_image = Image.open(self.image_files[index])
            
            # Проверяем, является ли изображение анимированным GIF
            is_animated = False
            try:
                is_animated = 'duration' in self.current_image.info and self.current_image.info['duration'] > 0
            except:
                pass
                
            if is_animated:
                # Загружаем все кадры анимации
                try:
                    while True:
                        # Копируем текущий кадр
                        frame = self.current_image.copy()
                        # Масштабируем кадр
                        scaled_frame = self.scale_image(frame)
                        # Конвертируем в PhotoImage
                        photo = ImageTk.PhotoImage(scaled_frame)
                        self.animation_frames.append(photo)
                        # Переходим к следующему кадру
                        self.current_image.seek(self.current_image.tell() + 1)
                except EOFError:
                    pass  # Достигнут конец файла (все кадры загружены)
                
                # Показываем первый кадр
                if self.animation_frames:
                    self.current_photo = self.animation_frames[0]
                    self.image_label.configure(image=self.animation_frames[0])
                    # Запускаем анимацию
                    self.animate_gif(0)
            else:
                # Обычное изображение
                self.update_image_size()
            
            # Обновляем информацию о файле
            filename = os.path.basename(self.image_files[index])
            filesize = os.path.getsize(self.image_files[index])
            self.filename_var.set(f"Файл: {filename}\nРазмер: {self.format_file_size(filesize)}")
            
            # Разблокируем все кнопки папок
            for btn in self.folder_buttons.values():
                btn.configure(state='normal')
            
        except Exception as e:
            self.status_var.set(f"Ошибка при загрузке изображения: {str(e)}")
    
    def animate_gif(self, frame_index):
        """Показывает следующий кадр анимированного GIF"""
        if not self.animation_frames:
            return
            
        # Показываем текущий кадр
        self.current_photo = self.animation_frames[frame_index]
        self.image_label.configure(image=self.animation_frames[frame_index])
        
        # Определяем следующий кадр
        next_frame = (frame_index + 1) % len(self.animation_frames)
        
        # Получаем длительность текущего кадра (по умолчанию 100мс)
        try:
            duration = self.current_image.info.get('duration', 100)
        except:
            duration = 100
        
        # Планируем показ следующего кадра
        self.animation_timer = self.root.after(duration, lambda: self.animate_gif(next_frame))
    
    def scale_image(self, image):
        """Масштабирует изображение под размер окна"""
        # Получаем размеры окна и изображения
        window_width = self.image_frame.winfo_width()
        window_height = self.image_frame.winfo_height()
        image_width, image_height = image.size
        
        if window_width <= 1 or window_height <= 1:
            return image
            
        # Вычисляем новые размеры с сохранением пропорций
        scale_width = window_width / image_width
        scale_height = window_height / image_height
        scale = min(scale_width, scale_height)
        
        new_width = int(image_width * scale)
        new_height = int(image_height * scale)
        
        # Масштабируем изображение
        if new_width != image_width or new_height != image_height:
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image
    
    def show_next_image(self):
        self.show_image(self.current_index + 1)
    
    def show_prev_image(self):
        self.show_image(self.current_index - 1)
    
    def move_to_folder(self, folder_index):
        """Перемещает текущее изображение в выбранную папку"""
        if not self.current_image or folder_index >= len(self.folders):
            return
            
        try:
            # Проверяем, что текущий файл не изменился
            if self.current_file != self.image_files[self.current_index]:
                return
                
            # Блокируем все кнопки папок
            for btn in self.folder_buttons.values():
                btn.configure(state='disabled')
            
            # Создаем папку, если её нет
            folder_name = self.folders[folder_index]
            folder_path = os.path.join(self.app_path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            src = self.image_files[self.current_index]
            
            # Проверяем, существует ли исходный файл
            if not os.path.exists(src):
                raise FileNotFoundError("Исходный файл не найден")
                
            dst = os.path.join(folder_path, os.path.basename(src))
            
            # Проверяем существование файла
            if os.path.exists(dst):
                base, ext = os.path.splitext(dst)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                dst = f"{base}_{counter}{ext}"
            
            # Перемещаем файл
            shutil.move(src, dst)
            
            # Удаляем файл из списка и показываем следующий
            self.image_files.pop(self.current_index)
            if self.image_files:
                if self.current_index >= len(self.image_files):
                    self.current_index = 0
                self.show_image(self.current_index)
            else:
                self.current_image = None
                self.current_file = None
                self.image_label.configure(image='')
                self.status_var.set("Все изображения обработаны")
            
            # Увеличиваем счетчик обработанных изображений
            self.processed_images += 1
            self.update_counter()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось переместить файл: {str(e)}")
            # Разблокируем кнопки в случае ошибки
            for btn in self.folder_buttons.values():
                btn.configure(state='normal')
    
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
