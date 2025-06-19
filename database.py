import sqlite3

class Database:
    def __init__(self):
        """
        Инициализация базы данных.
        Создаются таблицы, если они еще не существуют.
        """
        self.conn = sqlite3.connect("call_center.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """
        Создает таблицы в базе данных, если их еще нет.
        """
        # Таблица пользователей
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # Таблица клиентов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                company TEXT
            )
        """)

        # Таблица звонков
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                call_type TEXT NOT NULL,
                duration INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                recording TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        # Таблица задач
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT NOT NULL,
                assigned_to TEXT NOT NULL,
                status TEXT DEFAULT 'in_progress',
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        # Таблица заметок
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                note TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        self.conn.commit()

    def add_user(self, username, password):
        """
        Добавляет нового пользователя в базу данных.
        Возвращает True, если пользователь успешно добавлен.
        """
        try:
            self.cursor.execute("""
                INSERT INTO users (username, password)
                VALUES (?, ?)
            """, (username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Пользователь уже существует

    def authenticate_user(self, username, password):
        """
        Проверяет аутентификацию пользователя.
        Возвращает True, если логин и пароль совпадают.
        """
        self.cursor.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ?
        """, (username, password))
        return self.cursor.fetchone() is not None

    def add_client(self, name, phone, email, company):
        """
        Добавляет нового клиента в базу данных.
        """
        try:
            self.cursor.execute("""
                INSERT INTO clients (name, phone, email, company)
                VALUES (?, ?, ?, ?)
            """, (name, phone, email, company))
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Клиент с таким телефоном уже существует.")

    def get_clients(self):
        """
        Возвращает список всех клиентов.
        """
        self.cursor.execute("SELECT * FROM clients")
        return self.cursor.fetchall()

    def add_call(self, client_id, call_type, duration=None):
        """
        Добавляет новый звонок в базу данных.
        """
        self.cursor.execute("""
            INSERT INTO calls (client_id, call_type, duration)
            VALUES (?, ?, ?)
        """, (client_id, call_type, duration))
        self.conn.commit()

    def update_task_status(self, task_id, status):
        """
        Обновляет статус задачи.
        """
        self.cursor.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        self.conn.commit()

    def update_call_duration(self, call_id, duration):
        """
        Обновляет длительность звонка.
        """
        self.cursor.execute("""
            UPDATE calls
            SET duration = ?
            WHERE id = ?
        """, (duration, call_id))
        self.conn.commit()

    def update_call_recording(self, call_id, recording_path):
        """
        Обновляет путь к записи звонка.
        """
        self.cursor.execute("""
            UPDATE calls
            SET recording = ?
            WHERE id = ?
        """, (recording_path, call_id))
        self.conn.commit()

    def get_calls(self):
        """
        Возвращает список всех звонков.
        """
        self.cursor.execute("SELECT * FROM calls")
        return self.cursor.fetchall()

    def add_task(self, client_id, description, due_date, assigned_to):
        """
        Добавляет новую задачу в базу данных.
        """
        self.cursor.execute("""
            INSERT INTO tasks (client_id, description, due_date, assigned_to)
            VALUES (?, ?, ?, ?)
        """, (client_id, description, due_date, assigned_to))
        self.conn.commit()

    def get_tasks(self):
        """
        Возвращает список всех задач.
        """
        self.cursor.execute("SELECT * FROM tasks")
        return self.cursor.fetchall()

    def add_note(self, client_id, note):
        """
        Добавляет новую заметку для клиента.
        """
        self.cursor.execute("""
            INSERT INTO notes (client_id, note)
            VALUES (?, ?)
        """, (client_id, note))
        self.conn.commit()

    def get_notes(self, client_id):
        """
        Возвращает список заметок для указанного клиента.
        """
        self.cursor.execute("""
            SELECT * FROM notes
            WHERE client_id = ?
        """, (client_id,))
        return self.cursor.fetchall()

    def close(self):
        """
        Закрывает соединение с базой данных.
        """
        self.conn.close()
        
    def search_clients(self, query):
        """
        Поиск клиентов по имени, телефону или компании.
        """
        self.cursor.execute("""
            SELECT * FROM clients
            WHERE name LIKE ? OR phone LIKE ? OR company LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return self.cursor.fetchall()

    def filter_calls(self, call_type=None, has_recording=None):
        """
        Фильтрация звонков по типу и наличию записи.
        """
        query = "SELECT * FROM calls"
        conditions = []
        params = []

        if call_type:
            conditions.append("call_type = ?")
            params.append(call_type)
        if has_recording is not None:
            conditions.append("recording IS NOT NULL" if has_recording else "recording IS NULL")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def filter_tasks(self, status=None):
        """
        Фильтрация задач по статусу.
        """
        query = "SELECT * FROM tasks"
        params = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        self.cursor.execute(query, params)
        return self.cursor.fetchall()
