import tkinter as tk
from ui import CallCenterApp
from tasks import notify_overdue_tasks

if __name__ == "__main__":
    root = tk.Tk()
    app = CallCenterApp(root)
    notify_overdue_tasks()  
    root.mainloop()