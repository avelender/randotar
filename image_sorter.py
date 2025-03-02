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
        self.root.title("Сортировщик изображений")
        self.root.geometry("1200x700")
        
        # Получаем путь к папке, в которой находится скрипт
        if getattr(sys, 'frozen', False):
            self.app_path = os.path.dirname(sys.executable)
        else:
            self.app_path = os.path.dirname(os.path.abspath(__file__))
        
        # Поддерживаемые форматы изображений
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
        # Загружаем список папок
        self.folders = self.get_existing_folders()
        
        # Список изображений
        self.image_files = []
        self.current_index = 0
        
        # Создаем интерфейс
        self.create_ui()
        
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
        
        # Добавляем обработчик для кнопки максимизации окна
        self.root.bind("<Map>", self.on_window_map)
        self.root.bind("<Unmap>", self.on_window_map)
        
        # Текущее изображение
        self.current_image = None
        
        # Показываем первое изображение
        if self.image_files:
            self.show_image(0)
        else:
            self.status_var.set("Изображения не найдены в текущей папке")
    
    def get_existing_folders(self):
        """Получает список существующих папок в директории"""
        folders = []
        for item in os.listdir(self.app_path):
            item_path = os.path.join(self.app_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                folders.append(item)
        return sorted(folders)
    
    def create_ui(self):
        # Создаем фрейм для боковой панели
        sidebar = ttk.Frame(self.root, width=250, padding=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Заголовок
        ttk.Label(sidebar, text="Сортировка", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Кнопки управления папками
        folder_controls = ttk.Frame(sidebar)
        folder_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(folder_controls, text="+ Добавить папку", 
                  command=self.add_folder).pack(side=tk.LEFT, padx=2)
        
        # Создаем фрейм для списка папок
        self.folders_frame = ttk.Frame(sidebar)
        self.folders_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем кнопки для папок
        self.create_folder_buttons()
        
        # Информация о файле
        info_frame = ttk.LabelFrame(sidebar, text="Информация", padding=5)
        info_frame.pack(fill=tk.X, pady=10)
        
        self.file_info_var = tk.StringVar(value="Файл: ")
        ttk.Label(info_frame, textvariable=self.file_info_var).pack(anchor=tk.W)
        
        self.file_size_var = tk.StringVar(value="Размер: ")
        ttk.Label(info_frame, textvariable=self.file_size_var).pack(anchor=tk.W)
        
        self.progress_var = tk.StringVar(value="0 из 0")
        ttk.Label(info_frame, textvariable=self.progress_var).pack(anchor=tk.W)
        
        # Горячие клавиши
        keys_frame = ttk.LabelFrame(sidebar, text="Горячие клавиши", padding=5)
        keys_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(keys_frame, text="→ - Следующее изображение").pack(anchor=tk.W)
        ttk.Label(keys_frame, text="← - Предыдущее изображение").pack(anchor=tk.W)
        ttk.Label(keys_frame, text="Del - Удалить текущую папку").pack(anchor=tk.W)
        ttk.Label(keys_frame, text="F2 - Переименовать папку").pack(anchor=tk.W)
        
        # Статус
        self.status_var = tk.StringVar(value="Загрузка изображений...")
        ttk.Label(sidebar, textvariable=self.status_var).pack(anchor=tk.W, pady=10)
        
        # Создаем фрейм для изображения
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Метка для отображения изображения
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
    
    def create_folder_buttons(self):
        """Создает кнопки для всех папок"""
        # Очищаем фрейм
        for widget in self.folders_frame.winfo_children():
            widget.destroy()
        
        # Создаем новые кнопки
        self.folder_buttons = []
        for i, folder in enumerate(self.folders):
            frame = ttk.Frame(self.folders_frame)
            frame.pack(fill=tk.X, pady=2)
            
            # Кнопка для перемещения файла
            btn = ttk.Button(
                frame,
                text=f"{i+1}. {folder}",
                command=lambda f=folder, idx=i: self.move_to_folder(idx)
            )
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
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
            
            self.folder_buttons.append(btn)
    
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
        # Навигация
        self.root.bind("<Right>", lambda event: self.show_next_image())
        self.root.bind("<Left>", lambda event: self.show_prev_image())
        
        # Быстрые клавиши для папок (1-9)
        for i in range(9):
            self.root.bind(str(i+1), lambda event, idx=i: self.move_to_folder(idx) 
                         if idx < len(self.folders) else None)
    
    def load_images(self):
        threading.Thread(target=self._load_images_thread, daemon=True).start()
    
    def _load_images_thread(self):
        self.image_files = []
        
        # Сканируем текущую папку на наличие изображений
        for file in os.listdir(self.app_path):
            file_path = os.path.join(self.app_path, file)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in self.image_extensions:
                    self.image_files.append(file_path)
        
        # Сортируем файлы по имени
        self.image_files.sort()
        
        # Обновляем интерфейс в основном потоке
        self.root.after(0, self._update_after_load)
    
    def _update_after_load(self):
        if self.image_files:
            self.status_var.set(f"Найдено {len(self.image_files)} изображений")
            self.show_image(0)
        else:
            self.status_var.set("Изображения не найдены в текущей папке")
    
    def show_image(self, index):
        if not self.image_files:
            return
        
        # Обеспечиваем, что индекс находится в допустимом диапазоне
        self.current_index = (index + len(self.image_files)) % len(self.image_files)
        
        file_path = self.image_files[self.current_index]
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Обновляем информацию о файле
        self.file_info_var.set(f"Файл: {file_name}")
        self.file_size_var.set(f"Размер: {self.format_file_size(file_size)}")
        self.progress_var.set(f"{self.current_index + 1} из {len(self.image_files)}")
        
        try:
            # Загружаем изображение с помощью PIL
            self.current_image = Image.open(file_path)
            self.update_image_size()
            
            self.status_var.set("Изображение загружено")
        except Exception as e:
            self.status_var.set(f"Ошибка при загрузке изображения: {str(e)}")
    
    def update_image_size(self):
        """Обновляет размер изображения в соответствии с размером окна"""
        if not self.current_image:
            return
            
        # Получаем размеры фрейма для изображения
        frame_width = self.image_frame.winfo_width()
        frame_height = self.image_frame.winfo_height()
        
        # Если размеры фрейма еще не определены, используем значения по умолчанию
        if frame_width <= 1:
            frame_width = 800
        if frame_height <= 1:
            frame_height = 600
        
        # Масштабируем изображение, сохраняя пропорции
        img_width, img_height = self.current_image.size
        scale = min(frame_width / img_width, frame_height / img_height)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Изменяем размер изображения
        resized_image = self.current_image.resize((new_width, new_height), Image.LANCZOS)
        
        # Преобразуем в формат, подходящий для Tkinter
        photo = ImageTk.PhotoImage(resized_image)
        
        # Обновляем изображение в метке
        self.image_label.configure(image=photo)
        self.image_label.image = photo
    
    def on_window_resize(self, event):
        """Обработчик изменения размера окна"""
        # Проверяем, что событие пришло от главного окна
        if event.widget == self.root:
            self.update_image_size()
    
    def show_next_image(self):
        self.show_image(self.current_index + 1)
    
    def show_prev_image(self):
        self.show_image(self.current_index - 1)
    
    def move_to_folder(self, folder_index):
        if not self.image_files or self.current_index >= len(self.image_files):
            return
        
        if folder_index >= len(self.folders):
            return
        
        source_path = self.image_files[self.current_index]
        file_name = os.path.basename(source_path)
        target_folder = os.path.join(self.app_path, self.folders[folder_index])
        target_path = os.path.join(target_folder, file_name)
        
        try:
            # Перемещаем файл
            shutil.move(source_path, target_path)
            
            # Удаляем файл из списка
            self.image_files.pop(self.current_index)
            
            self.status_var.set(f"Файл перемещен в {self.folders[folder_index]}")
            
            # Показываем следующее изображение или обновляем интерфейс
            if self.image_files:
                # Если текущий индекс выходит за пределы, корректируем его
                if self.current_index >= len(self.image_files):
                    self.current_index = len(self.image_files) - 1
                self.show_image(self.current_index)
            else:
                # Очищаем интерфейс, если изображений больше нет
                self.image_label.configure(image=None)
                self.image_label.image = None
                self.file_info_var.set("Файл: ")
                self.file_size_var.set("Размер: ")
                self.progress_var.set("0 из 0")
                self.status_var.set("Все изображения отсортированы")
        except Exception as e:
            self.status_var.set(f"Ошибка при перемещении файла: {str(e)}")
    
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
