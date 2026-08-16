import pandas as pd
from data_store import get_connection
from sql_guard import validate_sql

def get_machine_record(product_id: str) -> str:
    """
    Retrieves the complete snapshot record for a single machine based on its Product ID.
    
    Args:
        product_id: The exact Product ID of the machine (e.g., 'M14860', 'L47181', 'H29424').
    """
    conn = get_connection()
    # Safe parameterization for DuckDB
    df = conn.execute("SELECT * FROM ai4i2020 WHERE \"Product ID\" = ?", [product_id]).fetchdf()
    
    if df.empty:
        return f"No machine found with Product ID: {product_id}"
    return df.to_json(orient="records")

def summarize_column(column_name: str) -> str:
    """
    Provides summary statistics (count, average, min, max) for a specific numeric column in the dataset.
    
    Args:
        column_name: The name of the column to summarize (e.g., 'Air temperature [K]', 'Torque [Nm]').
    """
    conn = get_connection()
    # Note: Column names cannot be parameterized in standard SQL, so string formatting is used.
    query = f'''
        SELECT 
            count("{column_name}") as record_count, 
            avg("{column_name}") as average, 
            min("{column_name}") as minimum, 
            max("{column_name}") as maximum 
        FROM ai4i2020
    '''
    df = conn.execute(query).fetchdf()
    return df.to_json(orient="records")

def compare_groups(target_column: str, group_by_column: str) -> str:
    """
    Calculates the average of a target numeric metric, broken down by categories in another column.
    
    Args:
        target_column: The numeric metric to average (e.g., 'Torque [Nm]', 'Rotational speed [rpm]').
        group_by_column: The categorical column to group by (e.g., 'Type', 'Machine failure').
    """
    conn = get_connection()
    query = f'''
        SELECT "{group_by_column}", avg("{target_column}") as avg_{target_column.replace(" ", "_")} 
        FROM ai4i2020 
        GROUP BY "{group_by_column}"
    '''
    df = conn.execute(query).fetchdf()
    return df.to_json(orient="records")

def failure_breakdown() -> str:
    """
    Returns the total count of machines, total failures, and the specific breakdown across all 5 failure modes.
    """
    conn = get_connection()
    query = '''
        SELECT 
            count(*) as Total_Machines,
            sum("Machine failure") as Total_Failures,
            sum("TWF") as Tool_Wear_Failures,
            sum("HDF") as Heat_Dissipation_Failures,
            sum("PWF") as Power_Failures,
            sum("OSF") as Overstrain_Failures,
            sum("RNF") as Random_Failures
        FROM ai4i2020
    '''
    df = conn.execute(query).fetchdf()
    return df.to_json(orient="records")

def correlation_analysis(column1: str, column2: str) -> str:
    """
    Calculates the statistical correlation between two numeric columns.
    
    Args:
        column1: First numeric column name.
        column2: Second numeric column name.
    """
    conn = get_connection()
    query = f'SELECT corr("{column1}", "{column2}") as correlation_coefficient FROM ai4i2020'
    df = conn.execute(query).fetchdf()
    return df.to_json(orient="records")

def run_sql_query(query: str) -> str:
    """
    Executes a custom SQL query. Use this as a fallback when the fixed tools cannot answer the user's question.
    
    Args:
        query: The raw SQL query to execute against the ai4i2020 table.
    """
    is_valid, safe_query_or_error = validate_sql(query)
    
    if not is_valid:
        return f"Execution rejected by sql_guard: {safe_query_or_error}"
        
    conn = get_connection()
    try:
        df = conn.execute(safe_query_or_error).fetchdf()
        return df.to_json(orient="records")
    except Exception as e:
        return f"Database execution failed: {str(e)}"