import sqlite3
from datetime import datetime

DATABASE_NAME = 'tasks.db'

bd = {}

def db_connect():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

def create_table():
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            description TEXT,
            event_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_task(chat_id, description, event_time):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (chat_id, description, event_time) VALUES (?, ?, ?)',
                   (chat_id, description, event_time.isoformat()))
    conn.commit()
    conn.close()

def get_tasks(chat_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute('SELECT description, event_time FROM tasks WHERE chat_id = ?', (chat_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks


