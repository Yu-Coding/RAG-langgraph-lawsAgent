# db_tool.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "uploads/contracts.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                content TEXT,
                summary TEXT
            )
        ''')
        conn.commit()

def insert_contract(filename: str, content: str, summary: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO contracts (filename, content, summary) VALUES (?, ?, ?)",
            (filename, content, summary)
        )
        conn.commit()
