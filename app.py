import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QSpinBox
from PyQt5.QtCore import QTimer, Qt
import psutil
import sqlite3

class ResourceMonitorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.recording = False
        self.start_time = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)


        self.conn = sqlite3.connect('resource_monitor.db')
        self.cursor = self.conn.cursor()
        self.create_table()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Уровень загруженности")
        self.setGeometry(100, 100, 200, 300)

        layout = QVBoxLayout()


        self.cpu_label = QLabel("ЦП: 0%", self)
        self.ram_label = QLabel("ОЗУ: 0% / 0 GB", self)
        self.disk_label = QLabel("ПЗУ: 0% / 0 GB", self)

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.disk_label)


        self.interval_label = QLabel("Интервал (мс):", self)
        self.interval_spinbox = QSpinBox(self)
        self.interval_spinbox.setMinimum(500)
        self.interval_spinbox.setMaximum(5000)
        self.interval_spinbox.setValue(1000)

        layout.addWidget(self.interval_label)
        layout.addWidget(self.interval_spinbox)


        self.start_btn = QPushButton("Начать запись", self)
        self.start_btn.clicked.connect(self.start_recording)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Остановить", self)
        self.stop_btn.clicked.connect(self.stop_recording)
        layout.addWidget(self.stop_btn)
        self.stop_btn.hide()  

        self.timer_label = QLabel("", self)
        self.timer_label.setAlignment(Qt.AlignCenter) 
        layout.addWidget(self.timer_label)

        self.setLayout(layout)

        self.max_ram = psutil.virtual_memory().total / (1024 ** 3)  
        self.max_disk = psutil.disk_usage('/').total / (1024 ** 3)  
        self.update_stats()  

    def update_stats(self):
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().used / (1024 ** 3)
        disk_usage = psutil.disk_usage('/').used / (1024 ** 3)

        self.cpu_label.setText(f"ЦП: {cpu_usage}%")
        self.ram_label.setText(f"ОЗУ: {ram_usage:.2f} GB / {self.max_ram:.2f} GB")
        self.disk_label.setText(f"ПЗУ: {disk_usage:.2f} GB / {self.max_disk:.2f} GB")

        if self.recording:
            self.save_to_db(cpu_usage, ram_usage, disk_usage)
            elapsed_time = int(time.time() - self.start_time)
            self.timer_label.setText(f"{elapsed_time // 60}:{elapsed_time - (elapsed_time // 60 * 60)}")

    def start_recording(self):
        self.start_time = time.time()
        self.recording = True
        self.start_btn.hide()  
        self.stop_btn.show()  
        self.timer.start(self.interval_spinbox.value())

    def stop_recording(self):
        self.recording = False
        self.start_btn.show()  
        self.stop_btn.hide()
        self.timer_label.setText("")
        self.timer.stop()

    def save_to_db(self, cpu, ram, disk):
        self.cursor.execute(
            "INSERT INTO resource_stats (timestamp, cpu, ram, disk) VALUES (?, ?, ?, ?)",
            (time.strftime('%Y-%m-%d %H:%M:%S'), cpu, ram, disk)
        )
        self.conn.commit()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu REAL,
                ram REAL,
                disk REAL
            )
        """)
        self.conn.commit()



    def closeEvent(self, event):
        self.conn.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ResourceMonitorApp()
    window.show()
    sys.exit(app.exec_())