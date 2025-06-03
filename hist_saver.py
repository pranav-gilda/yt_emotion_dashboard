import os
import sqlite3
import shutil
import csv
from datetime import datetime
import sys
from PyQt5 import QtWidgets, QtGui, QtCore

# Paths to browser history databases (adjust if needed)
BROWSER_PATHS = {
    "brave": os.path.expanduser("~") + "/AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/History",
    "chrome": os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data/Default/History",
    "edge": os.path.expanduser("~") + "/AppData/Local/Microsoft/Edge/User Data/Default/History"
}

# Temporary path to copy the database
TEMP_DB_PATH = "browser_history.db"


class BrowserHistorySaver(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.history_data = []
        self.load_history()

    def initUI(self):
        self.setWindowTitle("YouTube History Saver")
        self.setGeometry(100, 100, 800, 600)

        layout = QtWidgets.QVBoxLayout()

        # Date Range Inputs
        date_layout = QtWidgets.QHBoxLayout()

        self.from_date = QtWidgets.QDateEdit(self)
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(datetime.today())
        date_layout.addWidget(QtWidgets.QLabel("From Date:"))
        date_layout.addWidget(self.from_date)

        self.to_date = QtWidgets.QDateEdit(self)
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(datetime.today())
        date_layout.addWidget(QtWidgets.QLabel("To Date:"))
        date_layout.addWidget(self.to_date)

        self.filter_btn = QtWidgets.QPushButton("Filter Dates", self)
        self.filter_btn.clicked.connect(self.filter_by_date)
        date_layout.addWidget(self.filter_btn)

        layout.addLayout(date_layout)

        # History Table
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Date", "Title", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Export Button
        self.export_btn = QtWidgets.QPushButton("Export to CSV", self)
        self.export_btn.clicked.connect(self.export_history)
        layout.addWidget(self.export_btn)

        self.setLayout(layout)

    def load_history(self):
        """Loads browsing history from Brave, Chrome, and Edge, filtering only YouTube URLs."""
        self.history_data = []

        urls_seen = set()  # Track unique URLs

        for browser, path in BROWSER_PATHS.items():
            if os.path.exists(path):
                self.extract_history(path, browser, urls_seen)

        self.display_history()

    def extract_history(self, db_path, browser, urls_seen):
        """Extracts only YouTube history from browser databases."""
        try:
            shutil.copy2(db_path, TEMP_DB_PATH)

            conn = sqlite3.connect(TEMP_DB_PATH)
            cursor = conn.cursor()

            query = """
                SELECT datetime(last_visit_time/1000000-11644473600, 'unixepoch'), title, url 
                FROM urls WHERE url LIKE '%youtube.com%'
            """

            cursor.execute(query)
            results = cursor.fetchall()

            for date, title, url in results:
                if url not in urls_seen:  # Avoid duplicates
                    urls_seen.add(url)
                    self.history_data.append((date, title, url))

            conn.close()
            os.remove(TEMP_DB_PATH)

        except Exception as e:
            print(f"Error extracting history from {browser}: {e}")

    def display_history(self):
        """Displays history in the table."""
        self.table.setRowCount(len(self.history_data))
        for row, (date, title, url) in enumerate(self.history_data):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(date))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(title))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(url))

    def filter_by_date(self):
        """Filters history based on the selected date range."""
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")

        filtered_data = [
            (date, title, url)
            for date, title, url in self.history_data
            if from_date <= date[:10] <= to_date  # Extract date part from datetime
        ]

        self.table.setRowCount(len(filtered_data))
        for row, (date, title, url) in enumerate(filtered_data):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(date))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(title))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(url))

    def export_history(self):
        """Exports history to a CSV file."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save History", "", "CSV Files (*.csv)")

        if filename:
            with open(filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Title", "URL"])
                writer.writerows(self.history_data)  # Write filtered data
            QtWidgets.QMessageBox.information(self, "Success", "History exported successfully!")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = BrowserHistorySaver()
    window.show()
    sys.exit(app.exec_())
