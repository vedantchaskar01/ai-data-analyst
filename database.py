import os
import re
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
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
                table = row["table_name"]
                column = row["column_name"]
                data_type = row["data_type"]
                if table not in schema_info:
                    schema_info[table] = {"columns": [], "sample_rows": []}
                schema_info[table]["columns"].append(f"{column} ({data_type})")
            for table in schema_info.keys():
                sample_query = f'SELECT * FROM "{table}" LIMIT 3;'
                try:
                    cur.execute(sample_query)
                    sample_data = cur.fetchall()
                    schema_info[table]["sample_rows"] = [dict(row) for row in sample_data]
                except Exception as table_err:
                    print(f"sample rows error for {table}: {table_err}")
            _SCHEMA_CACHE = schema_info
            return schema_info
    except Exception as e:
        print(f"schema extraction error: {e}")
        return None
    finally:
        conn.close()

def execute_safe_query(query: str):
    from validator import sanitize_query
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

def import_dataframe_to_db(df: pd.DataFrame, table_name: str) -> int:
    global _SCHEMA_CACHE
    clean_table = re.sub(r"[^a-zA-Z0-9_]", "_", table_name.lower().strip())
    clean_cols = [re.sub(r"[^a-zA-Z0-9_]", "_", c.strip().lower()) for c in df.columns]
    
    clean_df = df.copy()
    clean_df.columns = clean_cols

    col_defs = []
    for col in clean_cols:
        col_type_str = str(clean_df[col].dtype).lower()
        if "int" in col_type_str:
            sql_type = "BIGINT"
        elif "float" in col_type_str:
            sql_type = "NUMERIC"
        elif "datetime" in col_type_str:
            sql_type = "TIMESTAMP"
        elif "bool" in col_type_str:
            sql_type = "BOOLEAN"
        else:
            sql_type = "TEXT"
        col_defs.append(f'"{col}" {sql_type}')

    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Failed to connect to database.")
        
    try:
        cur = conn.cursor()
        cur.execute(f'DROP TABLE IF EXISTS "{clean_table}" CASCADE;')
        cur.execute(f'CREATE TABLE "{clean_table}" ({", ".join(col_defs)});')
        
        insert_cols = ", ".join([f'"{c}"' for c in clean_cols])
        insert_sql = f'INSERT INTO "{clean_table}" ({insert_cols}) VALUES %s'
        
        prepared_df = clean_df.astype(object).where(pd.notnull(clean_df), None)
        values = [tuple(x) for x in prepared_df.to_numpy()]
        
        execute_values(cur, insert_sql, values, page_size=2000)
        conn.commit()
        
        _SCHEMA_CACHE = None
        return len(values)
    finally:
        conn.close()