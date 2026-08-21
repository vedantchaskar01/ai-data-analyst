import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def extract_schema():
    """
    Dynamically extracts the schema (tables and columns) from the database.
    Also fetches 3 sample rows per table to give the LLM context.
    """
    conn = get_db_connection()
    if not conn:
        return "Failed to connect to DB."

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Query the information_schema to get tables and columns
            query = """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """
            cur.execute(query)
            rows = cur.fetchall()
            
            # Group columns by table
            schema_info = {}
            for row in rows:
                table = row['table_name']
                column = row['column_name']
                data_type = row['data_type']
                
                if table not in schema_info:
                    schema_info[table] = {"columns": [], "sample_rows": []}
                schema_info[table]["columns"].append(f"{column} ({data_type})")
            
            # 2. Fetch sample rows for each table
            for table in schema_info.keys():
                # We use string interpolation here safely because table names come from information_schema
                sample_query = f"SELECT * FROM {table} LIMIT 3;"
                try:
                    cur.execute(sample_query)
                    sample_data = cur.fetchall()
                    # Convert RealDictRow to standard dict for easier reading
                    schema_info[table]["sample_rows"] = [dict(row) for row in sample_data]
                except Exception as table_err:
                    print(f"Could not fetch sample rows for {table}: {table_err}")
            
            return schema_info
            
    except Exception as e:
        print(f"Error extracting schema: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    print("Testing Database Connection and Schema Extraction...\n")
    schema = extract_schema()
    
    if schema and isinstance(schema, dict):
        print("[SUCCESS] Schema and Samples Extracted Successfully:\n")
        for table_name, data in schema.items():
            print(f"Table: {table_name}")
            print("  Columns:")
            for col in data["columns"]:
                print(f"    - {col}")
            print("  Sample Rows:")
            for row in data["sample_rows"]:
                print(f"    {row}")
            print("-" * 40)
    else:
        print("[ERROR] Failed to extract schema.")