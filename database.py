import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
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
        print(f"db conn error: {e}")
        return None

_SCHEMA_CACHE = None

def extract_schema(force_refresh: bool = False):
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None and not force_refresh:
        return _SCHEMA_CACHE

    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """
            cur.execute(query)
            rows = cur.fetchall()
            schema_info = {}
            for row in rows:
                table = row['table_name']
                column = row['column_name']
                data_type = row['data_type']
                if table not in schema_info:
                    schema_info[table] = {"columns": [], "sample_rows": []}
                schema_info[table]["columns"].append(f"{column} ({data_type})")
            for table in schema_info.keys():
                sample_query = f"SELECT * FROM {table} LIMIT 3;"
                try:
                    cur.execute(sample_query)
                    sample_data = cur.fetchall()
                    schema_info[table]["sample_rows"] = [dict(row) for row in sample_data]
                except Exception as table_err:
                    print(f"failed to get sample rows for {table}: {table_err}")
            _SCHEMA_CACHE = schema_info
            return schema_info
    except Exception as e:
        print(f"schema extraction error: {e}")
        return None
    finally:
        conn.close()

def execute_safe_query(query: str):
    from validator import sanitize_query
    # Let ValueError propagate if query is blocked (e.g. non-SELECT or invalid syntax)
    safe_query = sanitize_query(query)
    
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to database.")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SET statement_timeout = '5s'")
            cur.execute(safe_query)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

if __name__ == "__main__":
    print("Testing extraction...")
    schema = extract_schema()
    if schema:
        print("Success! Schema:\n")
        for table_name, data in schema.items():
            print(f"Table: {table_name}")
            for col in data["columns"]:
                print(f"  - {col}")
            print("  Samples:")
            for row in data["sample_rows"]:
                print(f"    {row}")
            print("-" * 20)
    else:
        print("Failed.")