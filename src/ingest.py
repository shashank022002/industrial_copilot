import duckdb

def load_csv_to_duckdb(csv_file: str, db_file: str, table_name: str):
    # Connecting to a file path creates a persistent database.
    conn = duckdb.connect(db_file)
    
    try:
        # read_csv_auto infers schema and data types automatically
        query = f"""
            CREATE TABLE {table_name} AS 
            SELECT * FROM read_csv_auto('{csv_file}')
        """
        conn.execute(query)
        print(f"Successfully loaded '{csv_file}' into table '{table_name}'.")
        
        # Verify the ingestion
        preview = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchdf()
        print("\nData preview:")
        print(preview)
        
    except duckdb.CatalogException as e:
        print(f"Error: Table '{table_name}' might already exist. ({e})")
    except Exception as e:
        print(f"Execution failed: {e}")
    finally:
        # Explicitly close the connection to release the file lock
        conn.close()

if __name__ == "__main__":
    load_csv_to_duckdb(
        csv_file="docs/csv/ai4i2020.csv", 
        db_file='local_data.duckdb', 
        table_name='my_table'
    )