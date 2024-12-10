import sqlite3
from sqlite3 import Error

DATABASE_FILE = 'schedule.db'

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    day TEXT NOT NULL,
                    description TEXT NOT NULL,
                    event_time TEXT NOT NULL
                )
            ''')
            conn.commit()
        except Error as e:
            print(e)
        finally:
            conn.close()

def add_event(chat_id, day, description, event_time):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO events (chat_id, day, description, event_time)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, day, description, event_time.strftime('%Y-%m-%d %H:%M')))
            conn.commit()
        except Error as e:
            print(e)
        finally:
            conn.close()

def get_events(chat_id):
    conn = create_connection()
    events = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT day, description, event_time FROM events WHERE chat_id = ?', (chat_id,))
            events = cursor.fetchall()
        except Error as e:
            print(e)
        finally:
            conn.close()
    return events

def delete_event(event_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
            conn.commit()
        except Error as e:
            print(e)
        finally:
            conn.close()


create_table()

