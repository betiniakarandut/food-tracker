import sqlite3
import os

db_file = "meals.db"

if not os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id TEXT NOT NULL,
            meal_time TEXT NOT NULL,
            date_served TEXT NOT NULL,
            time_served TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database file '{db_file}' created successfully.")
else:
    print(f"Database file '{db_file}' already exists.")