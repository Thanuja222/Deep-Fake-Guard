import sqlite3
from datetime import datetime

DB_NAME = "deepfake_guard.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL NOT NULL,
            file_hash TEXT NOT NULL,
            processing_time REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def log_analysis(filename, prediction, confidence, file_hash, processing_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO analysis_history (filename, prediction, confidence, file_hash, processing_time, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, prediction, confidence, file_hash, processing_time, timestamp))
    conn.commit()
    conn.close()

def get_all_history():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analysis_history ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]