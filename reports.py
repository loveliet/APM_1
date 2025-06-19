from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from database import Database  # Импорт для работы с базой данных

def generate_call_report():
    """
    Генерирует PDF-отчет по звонкам из базы данных.
    """
    try:
        # Регистрация шрифта DejaVuSans с поддержкой Unicode
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

        # Создаем PDF-документ
        pdf_file = "call_report.pdf"
        c = canvas.Canvas(pdf_file, pagesize=letter)
        width, height = letter  # Размеры страницы

        # Устанавливаем шрифт с поддержкой Unicode
        c.setFont("DejaVuSans", 12)

        # Заголовок отчета
        c.drawString(50, height - 50, "Отчет по звонкам")
        c.setFont("DejaVuSans", 10)  # Меньший шрифт для основного текста

        # Подключаемся к базе данных
        db = Database()
        calls = db.get_calls()

        # Проверяем, есть ли звонки
        if not calls:
            c.drawString(50, height - 70, "Нет данных о звонках.")
        else:
            y_position = height - 70  # Начальная позиция текста
            for call in calls:
                call_id, client_id, call_type, duration, timestamp, recording = call

                # Получаем данные клиента
                clients = db.get_clients()
                client = next((client for client in clients if client[0] == client_id), None)
                client_name = client[1] if client else "Неизвестный клиент"
                client_phone = client[2] if client else "Неизвестный телефон"

                # Формируем строку для звонка
                call_info = f"Звонок #{call_id}: {client_name} ({client_phone})"
                call_info += f" | Тип: {call_type} | Длительность: {duration} сек"
                if recording:
                    call_info += f" | Запись: {recording}"

                # Размещаем текст на странице
                c.drawString(50, y_position, call_info)
                y_position -= 20  # Сдвигаем позицию вниз

                # Если остается мало места, добавляем новую страницу
                if y_position < 50:
                    c.showPage()  # Новая страница
                    y_position = height - 50
                    c.setFont("DejaVuSans", 10)

        # Сохраняем PDF
        c.save()
        print(f"PDF-файл успешно создан: {pdf_file}")
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
