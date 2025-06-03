from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import os
import sqlite3
import csv
from datetime import datetime

app = FastAPI()

BROWSER_PATHS = {
    "brave": os.path.expanduser("~") + "/AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/History",
    "chrome": os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data/Default/History",
    "edge": os.path.expanduser("~") + "/AppData/Local/Microsoft/Edge/User Data/Default/History"
}

TEMP_DB_PATH = "browser_history.db"
CSV_EXPORT_PATH = "youtube_history.csv"

def extract_history(from_date: str, to_date: str):
    history_data = []
    for browser, path in BROWSER_PATHS.items():
        if os.path.exists(path):
            try:
                os.system(f"copy {path} {TEMP_DB_PATH}")  # Avoid locked files
                conn = sqlite3.connect(TEMP_DB_PATH)
                cursor = conn.cursor()
                query = """
                    SELECT datetime(last_visit_time/1000000-11644473600, 'unixepoch'), title, url 
                    FROM urls WHERE url LIKE '%youtube.com%' 
                    AND datetime(last_visit_time/1000000-11644473600, 'unixepoch') BETWEEN ? AND ?
                """
                cursor.execute(query, (from_date, to_date))
                history_data.extend(cursor.fetchall())
                conn.close()
                os.remove(TEMP_DB_PATH)
            except Exception as e:
                print(f"Error extracting history from {browser}: {e}")
    return history_data

@app.get("/history")
def get_history(from_date: str = Query(...), to_date: str = Query(...)):
    data = extract_history(from_date, to_date)
    return [{"date": d, "title": t, "url": u} for d, t, u in data]

@app.get("/export")
def export_csv():
    data = extract_history("2000-01-01", datetime.today().strftime("%Y-%m-%d"))
    with open(CSV_EXPORT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Title", "URL"])
        writer.writerows(data)
    return FileResponse(CSV_EXPORT_PATH, media_type='text/csv', filename="youtube_history.csv")
