import sqlite3
from tkinter import ttk
table = ttk.Treeview(table_frame, columns=columns, show="headings")

def delete_from_database(callsign):
    conn = sqlite3.connect("logbook.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logbook WHERE callsign = ?", (callsign,))
    conn.commit()
    conn.close()


def add_to_database(entry_data):
    conn = sqlite3.connect("logbook.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO logbook (date_time, callsign, rst_sent, rst_received, band, mode, power, grid_square, distance, name, country, comment)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, entry_data)
    conn.commit()
    conn.close()


def initialize_database():
    conn = sqlite3.connect("logbook.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logbook (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_time TEXT,
        callsign TEXT,
        rst_sent TEXT,
        rst_received TEXT,
        band TEXT,
        mode TEXT,
        power TEXT,
        grid_square TEXT,
        distance REAL,
        name TEXT,
        country TEXT,
        comment TEXT
    )
    """)
    conn.commit()
    conn.close()

    # Dodanie kolumn 'grid_square' i 'distance' w przypadku istniejącej tabeli bez tych kolumn
    conn = sqlite3.connect("logbook.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(logbook)")
    columns = [col[1] for col in cursor.fetchall()]
    if "grid_square" not in columns:
        cursor.execute("ALTER TABLE logbook ADD COLUMN grid_square TEXT")
    if "distance" not in columns:
        cursor.execute("ALTER TABLE logbook ADD COLUMN distance REAL")
    conn.commit()
    conn.close()

    # Aktualizacja tabeli
def update_table():
    for row in table.get_children():
        table.delete(row)
    
    conn = sqlite3.connect("logbook.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date_time, callsign, rst_sent, rst_received, band, mode, power, grid_square, distance, name, country, comment FROM logbook")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        table.insert("", tk.END, values=row)