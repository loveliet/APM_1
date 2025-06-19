import tkinter as tk
from tkinter import messagebox, simpledialog
import re  # Для работы с регулярными выражениями
import os
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import threading
from database import Database

# Глобальные настройки дизайна
BG_COLOR = "#F5F5F5"  #
PRIMARY_COLOR = "#3700FF"  
SECONDARY_COLOR = "#00FFD5"  
TEXT_COLOR = "#333333"  
FONT_STYLE = ("Arial", 12)  

class CallCenterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("АРМ Оператора Колл-Центра")
        self.db = Database()

        self.current_user = None
        self.current_frame = None  
        self.recording_file = None 
        self.is_recording = False  
        self.fs = 48000  
        self.microphone_data = []  
        self.system_audio_data = [] 
        self.microphone_stream = None  
        self.system_audio_stream = None  

        self.root.geometry("1920x1080")
        self.root.resizable(True, True)
        self.root.config(bg=BG_COLOR) 

        self.show_login_screen()

    def clear_frame(self):
        """Очищает текущее содержимое окна."""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.current_frame.pack(pady=20)

    def show_login_screen(self):
        self.clear_frame()

        tk.Label(
            self.current_frame,
            text="Вход в систему",
            font=("Arial", 24, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, columnspan=2, pady=20)

        tk.Label(
            self.current_frame,
            text="Логин:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.username_entry = tk.Entry(self.current_frame, font=FONT_STYLE)
        self.username_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(
            self.current_frame,
            text="Пароль:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.password_entry = tk.Entry(self.current_frame, show="*", font=FONT_STYLE)
        self.password_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(
            self.current_frame,
            text="Войти",
            command=self.login,
            font=FONT_STYLE,
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=3, column=0, columnspan=2, pady=10)

        tk.Button(
            self.current_frame,
            text="Зарегистрироваться",
            command=self.register,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=4, column=0, columnspan=2, pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.db.authenticate_user(username, password):
            self.current_user = username
            self.show_main_menu()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.db.add_user(username, password):
            messagebox.showinfo("Успех", "Пользователь зарегистрирован")
        else:
            messagebox.showerror("Ошибка", "Пользователь уже существует")

    def show_main_menu(self):
        self.clear_frame()

        tk.Label(
            self.current_frame,
            text="Главное меню",
            font=("Arial", 24, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, pady=20)

        tk.Button(
            self.current_frame,
            text="Клиенты",
            command=self.show_clients,
            font=FONT_STYLE,
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=1, column=0, pady=10)

        tk.Button(
            self.current_frame,
            text="Звонки",
            command=self.show_calls,
            font=FONT_STYLE,
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=2, column=0, pady=10)

        tk.Button(
            self.current_frame,
            text="Задачи",
            command=self.show_tasks,
            font=FONT_STYLE,
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=3, column=0, pady=10)

        tk.Button(
            self.current_frame,
            text="Отчеты",
            command=self.generate_reports,
            font=FONT_STYLE,
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=4, column=0, pady=10)

    def show_calls(self):
        self.clear_frame()
        tk.Label(
            self.current_frame,
            text="Звонки",
            font=("Arial", 24, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, pady=20)

        # Кнопка "Назад"
        tk.Button(
            self.current_frame,
            text="Назад",
            command=self.show_main_menu,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=1, column=0, pady=10)

        tk.Button(
            self.current_frame,
            text="Добавить звонок",
            command=self.add_call,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=8, column=0, pady=10)

        # Фильтры
        tk.Label(
            self.current_frame,
            text="Тип звонка:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        call_type_var = tk.StringVar()
        call_type_options = ["Все", "in", "out"]
        call_type_menu = tk.OptionMenu(self.current_frame, call_type_var, *call_type_options)
        call_type_menu.config(font=FONT_STYLE, bg=SECONDARY_COLOR, fg="white")
        call_type_menu.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(
            self.current_frame,
            text="Наличие записи:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        recording_var = tk.StringVar()
        recording_options = ["Все", "Есть запись", "Нет записи"]
        recording_menu = tk.OptionMenu(self.current_frame, recording_var, *recording_options)
        recording_menu.config(font=FONT_STYLE, bg=SECONDARY_COLOR, fg="white")
        recording_menu.grid(row=3, column=1, padx=10, pady=5)

        tk.Button(
            self.current_frame,
            text="Применить фильтры",
            command=lambda: self.filter_calls(call_type_var.get(), recording_var.get()),
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=4, column=0, columnspan=2, pady=10)

        # Список звонков
        self.calls_listbox = tk.Listbox(
            self.current_frame,
            width=50,
            height=10,
            font=FONT_STYLE,
            bg="#FFFFFF",
            fg=TEXT_COLOR
        )
        self.calls_listbox.grid(row=5, column=0, pady=10)
        tk.Button(
            self.current_frame,
            text="Воспроизвести запись",
            command=self.play_recording,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=6, column=0, pady=5)
        tk.Button(
            self.current_frame,
            text="Остановить воспроизведение",
            command=self.stop_playback,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=7, column=0, pady=5)
        self.load_calls()

    def filter_calls(self, call_type, recording_status):
        call_type = None if call_type == "Все" else call_type
        has_recording = None
        if recording_status == "Есть запись":
            has_recording = True
        elif recording_status == "Нет записи":
            has_recording = False

        calls = self.db.filter_calls(call_type, has_recording)
        self.calls_listbox.delete(0, tk.END)
        for call in calls:
            recording_status = "✅ Запись есть" if call[5] else "❌ Записи нет"
            self.calls_listbox.insert(tk.END, f"Звонок {call[2]} ({call[3]} сек) - {recording_status}")

    def load_calls(self):
        self.calls_listbox.delete(0, tk.END)
        calls = self.db.get_calls()
        for call in calls:
            recording_status = "✅ Запись есть" if call[5] else "❌ Записи нет"
            self.calls_listbox.insert(tk.END, f"Звонок {call[2]} ({call[3]} сек) - {recording_status}")

    def add_call(self):
        add_call_window = tk.Toplevel(self.root)
        add_call_window.title("Добавить звонок")
        add_call_window.geometry("600x600")
        add_call_window.resizable(True, True)
        add_call_window.config(bg=BG_COLOR)
        add_call_window.transient(self.root)
        add_call_window.grab_set()

        tk.Label(
            add_call_window,
            text="Добавить звонок",
            font=("Arial", 18, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, columnspan=2, pady=20)

        tk.Label(
            add_call_window,
            text="Телефон клиента (+7XXXXXXXXXX):",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        phone_entry = tk.Entry(add_call_window, font=FONT_STYLE)
        phone_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(
            add_call_window,
            text="Тип звонка:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        call_type_var = tk.StringVar(value="in") 
        tk.Radiobutton(
            add_call_window,
            text="Входящий",
            variable=call_type_var,
            value="in",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=2, column=1, padx=10, pady=5, sticky="w")
        tk.Radiobutton(
            add_call_window,
            text="Исходящий",
            variable=call_type_var,
            value="out",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=3, column=1, padx=10, pady=5, sticky="w")

        record_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            add_call_window,
            text="Записать разговор",
            variable=record_var,
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=4, column=0, columnspan=2, pady=10)

        tk.Label(
            add_call_window,
            text="Продолжительность (сек):",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=5, column=0, padx=10, pady=5, sticky="w")
        duration_entry = tk.Entry(add_call_window, font=FONT_STYLE)
        duration_entry.grid(row=5, column=1, padx=10, pady=5)

        def save_call():
            phone = phone_entry.get().strip()
            call_type = call_type_var.get()
            duration = duration_entry.get().strip()
            record = record_var.get()

            if not re.match(r"^\+7\d{10}$", phone):
                messagebox.showwarning("Ошибка", "Неправильный формат номера телефона. Пример: +79123456789.")
                return

            if not duration.isdigit():
                messagebox.showwarning("Ошибка", "Введите корректную продолжительность звонка (число секунд).")
                return

            clients = self.db.get_clients()
            client_id = next((client[0] for client in clients if client[2] == phone), None)
            if not client_id:
                messagebox.showwarning("Ошибка", "Клиент с таким телефоном не найден.")
                return

            self.db.add_call(client_id, call_type, duration=int(duration))

            if record:
                calls = self.db.get_calls()
                call_id = calls[-1][0]
                self.start_recording(call_id)
            else:
                messagebox.showinfo("Успех", "Звонок успешно добавлен!")
                add_call_window.destroy()

        tk.Button(
            add_call_window,
            text="Сохранить",
            command=save_call,
            font=FONT_STYLE,
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=6, column=0, pady=10)

        tk.Button(
            add_call_window,
            text="Отмена",
            command=add_call_window.destroy,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=6, column=1, pady=10)

    def save_task(self, window, phone, description, due_date, assigned_to):
        # Валидация телефона клиента
        phone_pattern = r"^\+7\d{10}$"
        if not re.match(phone_pattern, phone):
            messagebox.showwarning("Ошибка", "Неправильный формат номера телефона. Пример: +79123456789.")
            return

        # Проверка обязательных полей
        if not all([description, due_date, assigned_to]):
            messagebox.showwarning("Ошибка", "Заполните все поля.")
            return

        # Поиск ID клиента по телефону
        clients = self.db.get_clients()
        client_id = next((client[0] for client in clients if client[2] == phone), None)
        if not client_id:
            messagebox.showwarning("Ошибка", "Клиент с таким телефоном не найден.")
            return

        # Добавление задачи в базу данных
        self.db.add_task(client_id, description, due_date, assigned_to)
        self.load_tasks()  # Обновляем список задач
        messagebox.showinfo("Успех", "Задача успешно добавлена!")
        window.destroy()  # Закрытие окна добавления задачи

    def start_recording(self, call_id):
        """
        Начинает запись разговора с микрофона и системного аудио.
        """
        if self.is_recording:
            messagebox.showwarning("Ошибка", "Запись уже запущена.")
            return
        self.is_recording = True
        self.microphone_data = []
        self.system_audio_data = []
        recording_window = tk.Toplevel(self.root)
        recording_window.title("Запись разговора")
        recording_window.geometry("400x200")
        recording_window.resizable(False, False)
        recording_window.config(bg=BG_COLOR)
        recording_window.transient(self.root)
        recording_window.grab_set()

        tk.Label(
            recording_window,
            text="Идет запись разговора...",
            font=("Arial", 16, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).pack(pady=20)

        stop_button = tk.Button(
            recording_window,
            text="Завершить запись",
            command=lambda: self.stop_recording(recording_window, call_id),
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat"
        )
        stop_button.pack(pady=20)
        threading.Thread(target=self.record_microphone).start()
        threading.Thread(target=self.record_system_audio).start()

    def record_microphone(self):
        try:
            with sd.InputStream(samplerate=self.fs, channels=2, callback=self.microphone_callback) as stream:
                self.microphone_stream = stream
                while self.is_recording:
                    pass  
        except Exception as e:
            print(f"Ошибка записи микрофона: {e}")

    def microphone_callback(self, indata, frames, time, status):
        if self.is_recording:
            indata = np.clip(indata, -1.0, 1.0)
            self.microphone_data.append(indata.copy())

    def record_system_audio(self):
        import pyaudio
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = self.fs  
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
            self.system_audio_stream = stream
            while self.is_recording:
                data = stream.read(CHUNK, exception_on_overflow=False)
                self.system_audio_data.append(np.frombuffer(data, dtype=np.int16))
        except Exception as e:
            print(f"Ошибка записи системного звука: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def stop_recording(self, window, call_id):
        if not self.is_recording:
            messagebox.showwarning("Ошибка", "Запись не запущена.")
            return

        self.is_recording = False

        if self.microphone_stream:
            self.microphone_stream.abort()
        if self.system_audio_stream:
            self.system_audio_stream.stop_stream()

        import time
        time.sleep(0.5)
        recording_dir = "recordings"
        os.makedirs(recording_dir, exist_ok=True)
        recording_file = os.path.join(recording_dir, f"call_{call_id}.wav")

        combined_data = self.combine_audio_streams()

        write(recording_file, self.fs, combined_data)

        self.db.update_call_recording(call_id, recording_file)
        messagebox.showinfo("Запись разговора", f"Запись сохранена: {recording_file}")

        window.destroy()

        self.complete_call_details(call_id)

    def combine_audio_streams(self):
        microphone_audio = np.concatenate(self.microphone_data, axis=0)
        system_audio = np.concatenate(self.system_audio_data, axis=0)

        min_length = min(len(microphone_audio), len(system_audio))
        microphone_audio = microphone_audio[:min_length]
        system_audio = system_audio[:min_length]

        if system_audio.ndim == 1: 
            system_audio = np.column_stack((system_audio, system_audio)) 

        combined_audio = (microphone_audio + system_audio) / 2

        return combined_audio.astype(np.int16)

    def complete_call_details(self, call_id):
        details_window = tk.Toplevel(self.root)
        details_window.title("Завершение добавления звонка")
        details_window.geometry("600x600")
        details_window.resizable(True, True)
        details_window.config(bg=BG_COLOR)

        details_window.transient(self.root)
        details_window.grab_set()

        tk.Label(
            details_window,
            text="Завершение добавления звонка",
            font=("Arial", 18, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, columnspan=2, pady=20)

        tk.Label(
            details_window,
            text="Продолжительность звонка (сек):",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        duration_entry = tk.Entry(details_window, font=FONT_STYLE)
        duration_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(
            details_window,
            text="Сохранить",
            command=lambda: self.save_call_details(details_window, call_id, duration_entry),
            font=FONT_STYLE,
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=2, column=0, columnspan=2, pady=10)

    def save_call_details(self, window, call_id, duration_entry):
        duration = duration_entry.get().strip()

        if not duration.isdigit():
            messagebox.showwarning("Ошибка", "Введите корректную продолжительность звонка (число секунд).")
            return

        try:
            self.db.update_call_duration(call_id, int(duration))
            self.load_calls() 
            messagebox.showinfo("Успех", "Звонок успешно добавлен!")
            window.destroy() 
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {e}")

    def play_recording(self):

        selected_call = self.calls_listbox.curselection()
        if not selected_call:
            messagebox.showwarning("Ошибка", "Выберите звонок")
            return

        call_id = self.db.get_calls()[selected_call[0]][0]
        recording_path = self.db.get_calls()[selected_call[0]][5] 

        if not recording_path or not os.path.exists(recording_path):
            messagebox.showwarning("Ошибка", "Запись отсутствует")
            return

        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(recording_path)
            pygame.mixer.music.play()
            messagebox.showinfo("Воспроизведение", "Запись воспроизводится...")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось воспроизвести запись: {e}")

    def stop_playback(self):
        try:
            import pygame
            pygame.mixer.music.stop()
            messagebox.showinfo("Воспроизведение", "Воспроизведение остановлено.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось остановить воспроизведение: {e}")

    def load_clients(self):
        self.clients_listbox.delete(0, tk.END)
        clients = self.db.get_clients()
        for client in clients:
            self.clients_listbox.insert(tk.END, f"{client[1]} ({client[2]})")

    def add_client_window(self):
        add_client_window = tk.Toplevel(self.root)
        add_client_window.title("Добавить клиента")
        add_client_window.geometry("600x600")
        add_client_window.resizable(True, True)
        add_client_window.config(bg=BG_COLOR)

        add_client_window.transient(self.root)
        add_client_window.grab_set()

        tk.Label(
            add_client_window,
            text="Добавить клиента",
            font=("Arial", 18, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, columnspan=2, pady=20)

        tk.Label(
            add_client_window,
            text="Имя:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        name_entry = tk.Entry(add_client_window, font=FONT_STYLE)
        name_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(
            add_client_window,
            text="Телефон (+7XXXXXXXXXX):",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        phone_entry = tk.Entry(add_client_window, font=FONT_STYLE)
        phone_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(
            add_client_window,
            text="Email (необязательно):",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        email_entry = tk.Entry(add_client_window, font=FONT_STYLE)
        email_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Label(
            add_client_window,
            text="Компания:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        company_entry = tk.Entry(add_client_window, font=FONT_STYLE)
        company_entry.grid(row=4, column=1, padx=10, pady=5)

        tk.Button(
            add_client_window,
            text="Сохранить",
            command=lambda: self.save_client(
                add_client_window, name_entry, phone_entry, email_entry, company_entry
            ),
            font=FONT_STYLE,
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=5, column=0, columnspan=2, pady=10)

    def save_client(self, window, name_entry, phone_entry, email_entry, company_entry):
        name = name_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()
        company = company_entry.get().strip()

        if not name:
            messagebox.showwarning("Ошибка", "Введите имя клиента.")
            return

        phone_pattern = r"^\+7\d{10}$"
        if not re.match(phone_pattern, phone):
            phone_entry.config(bg="red")  
            messagebox.showwarning("Ошибка", "Неправильный формат номера телефона. Пример: +79123456789.")
            return
        else:
            phone_entry.config(bg="white")  

        if email:
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(email_pattern, email):
                email_entry.config(bg="red") 
                messagebox.showwarning("Ошибка", "Неправильный формат email.")
                return
            else:
                email_entry.config(bg="white") 

        self.db.add_client(name, phone, email, company)
        self.load_clients()
        messagebox.showinfo("Успех", "Клиент успешно добавлен!")
        window.destroy() 

    def view_client_details(self):
        selected_client = self.clients_listbox.curselection()
        if not selected_client:
            messagebox.showwarning("Ошибка", "Выберите клиента")
            return
        client = self.db.get_clients()[selected_client[0]]
        client_id = client[0]
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Данные клиента: {client[1]}")
        details_window.geometry("1920x1080")
        details_window.resizable(True, True)
        details_window.config(bg=BG_COLOR)
        # Делаем окно модальным
        details_window.transient(self.root)
        details_window.grab_set()
        # Заголовок
        tk.Label(
            details_window,
            text=f"Данные клиента: {client[1]}",
            font=("Arial", 24, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, padx=10, pady=20)
        # Информация о клиенте
        tk.Label(
            details_window,
            text=f"Имя: {client[1]}",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=1, column=0, padx=10, pady=5)
        tk.Label(
            details_window,
            text=f"Телефон: {client[2]}",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=2, column=0, padx=10, pady=5)
        tk.Label(
            details_window,
            text=f"Email: {client[3]}",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=3, column=0, padx=10, pady=5)
        tk.Label(
            details_window,
            text=f"Компания: {client[4]}",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=4, column=0, padx=10, pady=5)
        tk.Label(
            details_window,
            text="Заметки:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=5, column=0, padx=10, pady=5)
        notes_listbox = tk.Listbox(
            details_window,
            width=50,
            height=10,
            font=FONT_STYLE,
            bg="#FFFFFF",
            fg=TEXT_COLOR
        )
        notes_listbox.grid(row=6, column=0, padx=10, pady=5)
        notes = self.db.get_notes(client_id)
        for note in notes:
            notes_listbox.insert(tk.END, f"{note[2]} ({note[3]})")
        tk.Button(
            details_window,
            text="Добавить заметку",
            command=lambda: self.add_note(client_id),
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=7, column=0, pady=10)
        tk.Button(
            details_window,
            text="Назад",
            command=details_window.destroy,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=8, column=0, pady=10)

    def add_note(self, client_id):
        note_text = simpledialog.askstring("Добавить заметку", "Текст заметки:")
        if note_text:
            self.db.add_note(client_id, note_text)
            messagebox.showinfo("Успех", "Заметка добавлена!")

    def show_tasks(self):
        self.clear_frame()
        tk.Label(
            self.current_frame,
            text="Задачи",
            font=("Arial", 24, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, pady=20)

        tk.Button(
            self.current_frame,
            text="Назад",
            command=self.show_main_menu,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=1, column=0, pady=10)

        tk.Button(
            self.current_frame,
            text="Добавить задачу",
            command=self.add_task,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=1, column=1, pady=10)
        tk.Button(
            self.current_frame,
            text="Отметить как выполненную",
            command=self.mark_task_completed,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=2, column=0, pady=10)
        tk.Label(
            self.current_frame,
            text="Статус:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        status_var = tk.StringVar()
        status_options = ["Все", "in_progress", "completed"]
        status_menu = tk.OptionMenu(self.current_frame, status_var, *status_options)
        status_menu.config(font=FONT_STYLE, bg=SECONDARY_COLOR, fg="white")
        status_menu.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(
            self.current_frame,
            text="Применить фильтр",
            command=lambda: self.filter_tasks(status_var.get()),
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=3, column=0, columnspan=2, pady=10)

        self.tasks_listbox = tk.Listbox(
            self.current_frame,
            width=50,
            height=10,
            font=FONT_STYLE,
            bg="#FFFFFF",
            fg=TEXT_COLOR
        )
        self.tasks_listbox.grid(row=4, column=0, pady=10)
        self.load_tasks()

    def mark_task_completed(self):
        selected_task = self.tasks_listbox.curselection()
        if not selected_task:
            messagebox.showwarning("Ошибка", "Выберите задачу")
            return
        task_id = self.db.get_tasks()[selected_task[0]][0]  # Получаем ID выбранной задачи
        try:
            self.db.update_task_status(task_id, "completed")  # Обновляем статус в базе данных
            self.load_tasks()  # Обновляем список задач
            messagebox.showinfo("Успех", "Задача отмечена как выполненная!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить статус задачи: {e}")

    def filter_tasks(self, status):
        status = None if status == "Все" else status
        tasks = self.db.filter_tasks(status)
        self.tasks_listbox.delete(0, tk.END)
        for task in tasks:
            task_status = "✅ Выполнено" if task[5] == "completed" else "❌ В процессе"
            self.tasks_listbox.insert(tk.END, f"{task[2]} (до {task[3]}) - {task_status}")

    def load_tasks(self):
        self.tasks_listbox.delete(0, tk.END)
        tasks = self.db.get_tasks()
        for task in tasks:
            status = "✅ Выполнено" if task[5] == "completed" else "❌ В процессе"
            self.tasks_listbox.insert(tk.END, f"{task[2]} (до {task[3]}) - {status}")

    def add_task(self):
        client_phone = simpledialog.askstring("Добавить задачу", "Телефон клиента:")
        description = simpledialog.askstring("Добавить задачу", "Описание задачи:")
        due_date = simpledialog.askstring("Добавить задачу", "Дата выполнения (YYYY-MM-DD):")
        assigned_to = simpledialog.askstring("Добавить задачу", "Ответственный:")

        clients = self.db.get_clients()
        client_id = next((client[0] for client in clients if client[2] == client_phone), None)

        if client_id and description and due_date and assigned_to:
            self.db.add_task(client_id, description, due_date, assigned_to)
            self.load_tasks()
        else:
            messagebox.showwarning("Ошибка", "Заполните все поля")

    def generate_reports(self):
        try:
            from reports import generate_call_report
            generate_call_report()
            messagebox.showinfo("Успех", "Отчет сформирован!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сформировать отчет: {e}")
    def show_clients(self):
        """Показывает раздел клиентов."""
        self.clear_frame()
        tk.Label(
            self.current_frame,
            text="Клиенты",
            font=("Arial", 24, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        ).grid(row=0, column=0, pady=20)

        tk.Label(
            self.current_frame,
            text="Поиск:",
            font=FONT_STYLE,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        search_entry = tk.Entry(self.current_frame, font=FONT_STYLE)
        search_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(
            self.current_frame,
            text="Найти",
            command=lambda: self.search_clients(search_entry.get()),
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat"
        ).grid(row=1, column=2, pady=5)

        tk.Button(
            self.current_frame,
            text="Добавить клиента",
            command=self.add_client_window,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=2, column=0, pady=10)

        tk.Button(
            self.current_frame,
            text="Просмотреть данные клиента",
            command=self.view_client_details,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=2, column=1, pady=10)

        tk.Button(
            self.current_frame,
            text="Назад",
            command=self.show_main_menu,
            font=FONT_STYLE,
            bg=SECONDARY_COLOR,
            fg="white",
            relief="flat",
            width=20
        ).grid(row=3, column=0, pady=10)

        self.clients_listbox = tk.Listbox(
            self.current_frame,
            width=50,
            height=10,
            font=FONT_STYLE,
            bg="#FFFFFF",
            fg=TEXT_COLOR
        )
        self.clients_listbox.grid(row=4, column=0, pady=10)
        self.load_clients()

    def search_clients(self, query):
        """Выполняет поиск клиентов."""
        if query.strip():
            clients = self.db.search_clients(query)
        else:
            clients = self.db.get_clients()
        self.clients_listbox.delete(0, tk.END)
        for client in clients:
            self.clients_listbox.insert(tk.END, f"{client[1]} ({client[2]})")        
