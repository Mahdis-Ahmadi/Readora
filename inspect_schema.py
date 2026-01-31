import sqlite3
import pandas as pd

db_path = 'database/user_rate_book.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    for table in tables:
        table_name = table[0]
        print(f"\nSchema for {table_name}:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        # Preview data
        print(f"Preview {table_name}:")
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        print(df)
        print("-" * 20)

    conn.close()
except Exception as e:
    print(f"Error: {e}")
