import sqlite3
import sys
from random import choice

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel,
    QCalendarWidget, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QHBoxLayout, QDateEdit
)

# создание бд
DB_NAME = "finance_tracker.db"
test_mode = 1
date_format = 'dd-MM-yyyy'


def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        date TEXT,
        item TEXT,
        amount REAL,
        category TEXT
    )
    """)
    conn.commit()
    conn.close()


class TestMode:
    @staticmethod
    def random_item():
        with open('random_items.txt') as f:
            read_data = f.read().split('\n')
            return choice(read_data)

    @staticmethod
    def random_amount():
        with open('random_amount.txt') as f:
            read_data = f.read().split('\n')
            return choice(read_data)


class FinanceTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        setup_database()
        self.setWindowTitle("Finance Tracker")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()

        self.msg_label = None

        # календарь
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        main_layout.addWidget(self.calendar)

        # поля
        input_layout = QHBoxLayout()
        self.item_input = QLineEdit()
        self.item_input.setPlaceholderText("Покупка")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Стоимость")
        self.category_input = QComboBox()
        self.category_input.addItems(["Еда", "Электроника", "Одежда", "Другое"])

        if test_mode == 1:
            self.item_input.setText(TestMode.random_item())
            self.amount_input.setText(TestMode.random_amount())

        input_layout.addWidget(self.item_input)
        input_layout.addWidget(self.amount_input)
        input_layout.addWidget(self.category_input)
        main_layout.addLayout(input_layout)

        # кнопки
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить покупку")
        self.add_button.clicked.connect(self.add_transaction)

        self.stats_button = QPushButton("Показать статистику за заданный период")
        self.stats_button.clicked.connect(self.show_statistics)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.stats_button)
        main_layout.addLayout(button_layout)

        # временные рамки
        date_range_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        date_range_layout.addWidget(QLabel("Начиная:"))
        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("Заканчивая:"))
        date_range_layout.addWidget(self.end_date)
        main_layout.addLayout(date_range_layout)

        # список загруженных товаров
        down_layout = QHBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Добавляем столбец для ID
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Покупка", "Стоимость", "Категория"])
        self.table.hideColumn(0)  # Скрываем столбец с ID
        self.load_transactions()
        self.table.cellChanged.connect(self.update_transaction)
        down_layout.addWidget(self.table)

        pixmap = QPixmap("python_norm.png")
        lbl = QLabel(self)
        lbl.setPixmap(pixmap)
        down_layout.addWidget(lbl)

        main_layout.addLayout(down_layout)

        # основной виджет
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def add_transaction(self):
        date = self.calendar.selectedDate().toString(date_format)
        item = self.item_input.text()
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            self.show_message("Введено значение не того типа. Пожалуйста введите цифру.")
            return
        category = self.category_input.currentText()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (date, item, amount, category) VALUES (?, ?, ?, ?)",
            (date, item, amount, category),
        )
        conn.commit()
        conn.close()

        self.show_message("Покупка добавлена успешно!")
        self.load_transactions()
        if test_mode == 1:
            self.item_input.setText(TestMode.random_item())
            self.amount_input.setText(TestMode.random_amount())
        else:
            self.item_input.clear()
            self.amount_input.clear()

    def load_transactions(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, item, amount, category FROM transactions")
        transactions = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(transactions))
        for row_idx, row_data in enumerate(transactions):
            for col_idx, col_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

    def update_transaction(self, row, column):
        # Получаем ID записи
        record_id = self.table.item(row, 0).text()  # ID скрыт в первой колонке
        new_value = self.table.item(row, column).text()
        print(new_value)

        # Определяем, какое поле обновляется
        field_map = {1: "date", 2: "item", 3: "amount", 4: "category"}
        field = field_map.get(column)

        if not field:
            return  # Игнорируем изменения в несуществующих столбцах

        # Если это "amount", убедимся, что введено корректное число
        if field == "amount":
            try:
                new_value = float(new_value)
            except ValueError:
                self.show_message("Некорректное значение для стоимости. Введите число.")
                self.load_transactions()  # Перезагрузка для отмены некорректного ввода
                return

        # Обновляем запись в базе данных
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute(f"UPDATE transactions SET {field} = ? WHERE id = ?", (new_value, record_id))
            conn.commit()
            # self.show_message("Изменения сохранены в базе данных.")
        except sqlite3.Error as e:
            self.show_message(f"Ошибка при сохранении: {e}")
        finally:
            conn.close()

    def show_statistics(self):
        start_date = self.start_date.date().toString(date_format)
        end_date = self.end_date.date().toString(date_format)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount)
            FROM transactions
            WHERE date BETWEEN ? AND ?
            GROUP BY category
        """, (start_date, end_date))
        stats = cursor.fetchall()
        conn.close()

        message = f"Статистика с {start_date} по {end_date}:\n"
        for category, total in stats:
            message += f"{category}: {total:.2f}\n"

        self.show_message(message)

    def show_message(self, message):
        self.msg_label = QLabel(message)
        self.msg_label.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinanceTracker()
    window.show()
    sys.exit(app.exec())
