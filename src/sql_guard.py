import os
import sqlglot
from sqlglot import exp

def validate_sql(raw_query: str) -> tuple[bool, str]:
    """
    Validates LLM-authored SQL to ensure it is:
    - SELECT-only
    - A single statement
    - Only referencing the 'ai4i2020' table
    - Row capped
    """
    try:
        # Parse the query into a list of AST statements using DuckDB 
        statements = sqlglot.parse(raw_query, dialect="duckdb")
        
        # 1. Single statement constraint
        if not statements or len(statements) != 1:
            return False, "Query must contain exactly one SQL statement."
            
        stmt = statements[0]
        
        # 2. SELECT-only constraint
        if not isinstance(stmt, exp.Select):
            return False, "Only SELECT queries are allowed. Modifications are forbidden."
            
        # 3. Known table constraint
        # Extract all table names referenced in the AST
        tables = [table.name.lower() for table in stmt.find_all(exp.Table)]
        if not tables:
            return False, "Query does not reference any tables."
            
        for table in tables:
            if table != 'ai4i2020':
                return False, f"Unauthorized table referenced: '{table}'. Only 'ai4i2020' is allowed."
                
        # 4. Row cap enforcement
        # Fetch the cap from config, default to 500 if missing
        row_cap = int(os.environ.get("SQL_ROW_CAP", 500))
        
        # Check if the LLM provided a LIMIT clause
        current_limit = stmt.args.get("limit")
        
        # If no limit is set, or if the LLM's limit exceeds the system cap, override it
        if not current_limit or int(current_limit.expression.name) > row_cap:
            # sqlglot allows us to safely mutate the AST to enforce the limit
            stmt = stmt.limit(row_cap)
            
        # Compile the safe AST back into a raw DuckDB SQL string
        safe_query = stmt.sql(dialect="duckdb")
        return True, safe_query

    except sqlglot.errors.ParseError as e:
        return False, f"SQL Syntax Error: Could not parse query. ({str(e)})"
    except Exception as e:
        return False, f"Validation Error: {str(e)}"