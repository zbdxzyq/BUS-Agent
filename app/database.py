import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "bus_agent.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    return conn

def init_database():
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gps_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT NOT NULL,
            route_id INTEGER NOT NULL,
            speed REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle (
            id TEXT PRIMARY KEY,
            route_id INTEGER NOT NULL,
            plate_number TEXT NOT NULL UNIQUE,

            FOREIGN KEY (route_id)
            REFERENCES route(id)
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database initialized: {DB_PATH}")


if __name__ == "__main__":
    init_database()