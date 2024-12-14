from genetic import WEEK_DAYS, generate_weekly_schedule, format_time
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QWidget,
    QMessageBox, QHeaderView, QHBoxLayout, QFrame)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt
from datetime import datetime, timedelta

START_TIME = 6
END_TIME = 27

class ScheduleApp(QMainWindow):
    def __init__(self, weekly_schedule, daily_driver_info):
        super().__init__()
        self.weekly_schedule = weekly_schedule
        self.daily_driver_info = daily_driver_info

        self.setWindowTitle("Расписание автобусов")
        self.setGeometry(100, 100, 1000, 750)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.setup_ui()
        self.update_schedule_table()

    def setup_ui(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f0f4f7;
            }
            QLabel {
                color: #003366;
            }
            QPushButton {
                background-color: #0056b3;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #007acc;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #b3cde3;
                padding: 2px;
            }
            QTableWidget {
                border: 1px solid #b3cde3;
                gridline-color: #b3cde3;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            """
        )

        header_label = QLabel("Расписание автобусов")
        header_label.setFont(QFont("Arial", 20, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
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
        self.schedule_table.setStyleSheet(
            "alternate-background-color: #f7faff; background-color: #ffffff;"
        )

        self.layout.addWidget(self.schedule_table)

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #b3cde3;")
        return line

    def format_time(self, time_obj):
        if isinstance(time_obj, str):
            time_obj = datetime.strptime(time_obj, "%H:%M")
        if isinstance(time_obj, datetime):
            return time_obj.strftime("%H:%M:%S")
        elif isinstance(time_obj, timedelta):
            total_seconds = int(time_obj.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            hours = hours % 24
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        else:
            raise TypeError("Unsupported type for time_obj")

    def convert_to_minutes(self, time_obj):
        if isinstance(time_obj, str):
            time_obj = datetime.strptime(time_obj, "%H:%M")
        if isinstance(time_obj, datetime):
            return time_obj.hour * 60 + time_obj.minute
        elif isinstance(time_obj, timedelta):
            total_seconds = int(time_obj.total_seconds())
            return total_seconds // 60
        else:
            raise TypeError("Unsupported type for time_obj")

    def update_schedule_table(self):
        day_index = self.day_selector.currentIndex()
        schedule = self.weekly_schedule[day_index]

        active_buses_count = {t: 0 for t in range(START_TIME * 60, END_TIME * 60 + 1, 5)}

        self.schedule_table.setRowCount(len(schedule))
        for row, record in enumerate(schedule):
            start_time = record['start_time']
            end_time = record['end_time']

            start_minutes = self.convert_to_minutes(start_time)
            end_minutes = self.convert_to_minutes(end_time)

            for t in range(start_minutes, end_minutes, 5):
                if t in active_buses_count:
                    active_buses_count[t] += 1

            start_time_str = self.format_time(start_time)
            end_time_str = self.format_time(end_time)

            self.schedule_table.setItem(row, 0, QTableWidgetItem(str(record['bus'])))
            self.schedule_table.setItem(row, 1, QTableWidgetItem(record['driver_type']))
            self.schedule_table.setItem(row, 2, QTableWidgetItem(record['driver_id']))
            self.schedule_table.setItem(row, 3, QTableWidgetItem(start_time_str))
            self.schedule_table.setItem(row, 4, QTableWidgetItem(end_time_str))

            active_buses = active_buses_count[start_minutes]
            self.schedule_table.setItem(row, 5, QTableWidgetItem(str(active_buses)))

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

weekly_schedule, daily_driver_info = generate_weekly_schedule(num_buses, drivers_type_a, drivers_type_b)

app = QApplication(sys.argv)
window = ScheduleApp(weekly_schedule, daily_driver_info)
window.show()
sys.exit(app.exec_())
