import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

def ingest_superstore():
    csv_path = "Sample - Superstore.csv"
    if not os.path.exists(csv_path):
        print(f"File {csv_path} not found.")
        return

    df = pd.read_csv(csv_path, encoding="latin1")
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]

    df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
    df["ship_date"] = pd.to_datetime(df["ship_date"]).dt.date
    df["postal_code"] = df["postal_code"].fillna(0).astype(int).astype(str)

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS sales CASCADE;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS superstore_sales (
            row_id INT PRIMARY KEY,
            order_id VARCHAR(50),
            order_date DATE,
            ship_date DATE,
            ship_mode VARCHAR(50),
            customer_id VARCHAR(50),
            customer_name VARCHAR(100),
            segment VARCHAR(50),
            country VARCHAR(50),
            city VARCHAR(100),
            state VARCHAR(100),
            postal_code VARCHAR(20),
            region VARCHAR(50),
            product_id VARCHAR(50),
            category VARCHAR(50),
            sub_category VARCHAR(50),
            product_name VARCHAR(255),
            sales NUMERIC(12, 4),
            quantity INT,
            discount NUMERIC(6, 4),
            profit NUMERIC(12, 4)
        );
    """)

    cur.execute("TRUNCATE TABLE superstore_sales;")

    columns = list(df.columns)
    insert_sql = f"INSERT INTO superstore_sales ({', '.join(columns)}) VALUES %s"
    values = [tuple(x) for x in df.to_numpy()]

    execute_values(cur, insert_sql, values, page_size=2000)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_superstore_order_date ON superstore_sales(order_date);
        CREATE INDEX IF NOT EXISTS idx_superstore_category ON superstore_sales(category);
        CREATE INDEX IF NOT EXISTS idx_superstore_sub_cat ON superstore_sales(sub_category);
        CREATE INDEX IF NOT EXISTS idx_superstore_region ON superstore_sales(region);
        CREATE INDEX IF NOT EXISTS idx_superstore_customer ON superstore_sales(customer_name);
    """)

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM superstore_sales;")
    count = cur.fetchone()[0]
    print(f"Loaded {count} rows into superstore_sales.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    ingest_superstore()
