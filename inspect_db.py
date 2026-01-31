import sqlite3
import pandas as pd
import os

db_path = os.path.join('database', 'user_rate_book.db')

def inspect_db():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:", tables)

    for table in tables:
        table_name = table[0]
        print(f"\n--- Schema for {table_name} ---")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
        
        print(f"\n--- Sample data for {table_name} ---")
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        print(df)

    conn.close()

if __name__ == "__main__":
    inspect_db()
