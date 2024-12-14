from vlob import WEEK_DAYS, generate_schedule_for_week, format_time
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QWidget,
    QMessageBox, QHeaderView, QHBoxLayout, QFrame)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt

class ScheduleApp(QMainWindow):
    def __init__(self, weekly_schedule, daily_driver_info):
        super().__init__()
        self.weekly_schedule = weekly_schedule
        self.daily_driver_info = daily_driver_info

        self.setWindowTitle("Расписание автобусов")
        self.setGeometry(100, 100, 900, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.setup_ui()
        self.update_schedule_table()

    def setup_ui(self):
        header_label = QLabel("Расписание автобусов")
        header_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #007ACC;")
        self.layout.addWidget(header_label)

        self.layout.addWidget(self.create_separator())

        controls_layout = QHBoxLayout()
        self.day_selector = QComboBox()
        self.day_selector.addItems(WEEK_DAYS)
        self.day_selector.currentIndexChanged.connect(self.update_schedule_table)

        controls_layout.addWidget(QLabel("Выберите день недели:"))
        controls_layout.addWidget(self.day_selector)
        controls_layout.addStretch()

        self.show_drivers_button = QPushButton("Показать сотрудников")
        self.show_drivers_button.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        self.show_drivers_button.clicked.connect(self.show_driver_info)

        controls_layout.addWidget(self.show_drivers_button)

        self.layout.addLayout(controls_layout)

        self.layout.addWidget(self.create_separator())

        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(6)
        self.schedule_table.setHorizontalHeaderLabels([
            "Автобус", "Тип водителя", "ID водителя", "Начало маршрута", "Конец маршрута", "Активные автобусы"
        ])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.setAlternatingRowColors(True)

        self.schedule_table.setStyleSheet("""
            background-color: #f9f9f9;
            alternate-background-color: #f1f1f1;
            color: #333333;
        """)

        self.layout.addWidget(self.schedule_table)

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def update_schedule_table(self):
        day_index = self.day_selector.currentIndex()
        schedule = self.weekly_schedule[day_index]

        self.schedule_table.setRowCount(len(schedule))
        for row, record in enumerate(schedule):
            self.schedule_table.setItem(row, 0, QTableWidgetItem(str(record['bus'])))
            self.schedule_table.setItem(row, 1, QTableWidgetItem(record['driver_type']))
            self.schedule_table.setItem(row, 2, QTableWidgetItem(record['driver_id']))
            self.schedule_table.setItem(row, 3, QTableWidgetItem(format_time(record['start_time'])))
            self.schedule_table.setItem(row, 4, QTableWidgetItem(format_time(record['end_time'])))
            self.schedule_table.setItem(row, 5, QTableWidgetItem(str(record['active_buses'])))

            if record['active_buses'] > 0:
                self.set_row_color(row, QColor(144, 238, 144))
            else:
                self.set_row_color(row, QColor(255, 99, 71))

            if row % 2 == 0:
                self.set_row_color(row, QColor(240, 248, 255))

    def set_row_color(self, row, color):
        for column in range(self.schedule_table.columnCount()):
            item = self.schedule_table.item(row, column)
            if item:
                item.setBackground(color)

    def show_driver_info(self):
        day_index = self.day_selector.currentIndex()
        day = WEEK_DAYS[day_index]
        drivers = self.daily_driver_info[day]
        if not drivers:
            QMessageBox.information(self, "Сотрудники", f"В {day} не было работающих сотрудников.")
            return

        driver_list = "\n".join(sorted(drivers))
        QMessageBox.information(self, "Сотрудники", f"В {day} работали следующие сотрудники:\n{driver_list}")


num_buses = 10
drivers_type_a = 5
drivers_type_b = 7

weekly_schedule, daily_driver_info = generate_schedule_for_week(num_buses, drivers_type_a, drivers_type_b)

app = QApplication(sys.argv)
window = ScheduleApp(weekly_schedule, daily_driver_info)
window.show()
sys.exit(app.exec_())