from datetime import datetime
from tkinter import messagebox
from database import Database

def notify_overdue_tasks():
    db = Database()
    tasks = db.get_tasks()
    overdue_tasks = [
        task for task in tasks
        if task[3] and datetime.strptime(task[3], "%Y-%m-%d") < datetime.now() and task[5] == "pending"
    ]
    if overdue_tasks:
        message = "Просроченные задачи:\n" + "\n".join(
            f"{task[2]} (до {task[3]}) - Ответственный: {task[4]}" for task in overdue_tasks
        )
        messagebox.showwarning("Просроченные задачи", message)
    db.close()
