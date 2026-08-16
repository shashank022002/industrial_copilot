import os
import duckdb

# Singleton connection to avoid reloading the file-backed DB repeatedly
_conn = None

def get_connection():
    global _conn
    if _conn is None:
        # Create a persistent DuckDB file in the project folder
        _conn = duckdb.connect('local_data.duckdb')
        
        # Check if the table already exists
        existing_tables = _conn.execute("SHOW TABLES").fetchdf()
        
        if 'ai4i2020' not in existing_tables['name'].values:
            csv_path = 'ai4i2020.csv'
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"Dataset not found at {csv_path}")
            
            print(f"Initializing database from {csv_path}...")
            # read_csv_auto natively infers the schema from the CSV
            _conn.execute(f'CREATE TABLE ai4i2020 AS SELECT * FROM read_csv_auto("{csv_path}")')
            
    return _conn