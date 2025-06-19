import pytest
from unittest.mock import MagicMock
from main import CallCenterApp
from database import Database

@pytest.fixture
def app():
    """Создает экземпляр приложения с мокированной базой данных."""
    root = MagicMock()
    app = CallCenterApp(root)
    app.db = MagicMock(spec=Database)  # Мок базы данных
    return app

def test_add_client(app):
    """Тест добавления клиента."""
    app.db.add_client.return_value = True
    result = app.save_client(
        MagicMock(), "Иван", "+79123456789", "ivan@example.com", "ООО 'Ромашка'"
    )
    assert app.db.add_client.called
    assert app.db.add_client.call_args[0] == ("Иван", "+79123456789", "ivan@example.com", "ООО 'Ромашка'")

def test_get_clients(app):
    """Тест получения списка клиентов."""
    app.db.get_clients.return_value = [
        (1, "Иван", "+79123456789", "ivan@example.com", "ООО 'Ромашка'")
    ]
    app.load_clients()
    assert app.clients_listbox.get(0) == "Иван (+79123456789)"

def test_add_call(app):
    """Тест добавления звонка."""
    app.db.get_clients.return_value = [(1, "Иван", "+79123456789", "ivan@example.com", "ООО 'Ромашка'")]
    app.db.add_call.return_value = True
    app.add_call()
    assert app.db.add_call.called
    assert app.db.add_call.call_args[0][0] == 1  # ID клиента

def test_get_calls(app):
    """Тест получения списка звонков."""
    app.db.get_calls.return_value = [
        (1, 1, "in", 120, "2023-10-01", "recordings/call_1.wav"),
        (2, 1, "out", 60, "2023-10-02", None)
    ]
    app.load_calls()
    assert app.calls_listbox.get(0) == "Звонок in (120 сек) - ✅ Запись есть"
    assert app.calls_listbox.get(1) == "Звонок out (60 сек) - ❌ Записи нет"

def test_add_task(app):
    """Тест добавления задачи."""
    app.db.get_clients.return_value = [(1, "Иван", "+79123456789", "ivan@example.com", "ООО 'Ромашка'")]
    app.db.add_task.return_value = True
    app.add_task()
    assert app.db.add_task.called
    assert app.db.add_task.call_args[0] == (1, "Описание задачи", "2023-10-10", "Ответственный")