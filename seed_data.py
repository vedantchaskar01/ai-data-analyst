import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SAMPLE_PRODUCTS = [
    # Electronics
    ("4K Gaming Monitor", "Electronics", 399.99, "2023-10-05"),
    ("Noise-Cancelling Headphones", "Electronics", 199.50, "2023-10-12"),
    ("Mechanical Keyboard", "Electronics", 89.00, "2023-10-18"),
    ("USB-C Hub Multiport", "Electronics", 39.99, "2023-10-25"),
    ("Smartwatch Series 5", "Electronics", 249.00, "2023-11-02"),
    ("Bluetooth Speaker", "Electronics", 59.99, "2023-11-15"),
    ("External SSD 1TB", "Electronics", 109.00, "2023-11-28"),
    
    # Kitchen & Dining
    ("Espresso Coffee Machine", "Kitchen", 280.00, "2023-10-08"),
    ("Air Fryer XL", "Kitchen", 89.95, "2023-10-19"),
    ("Professional Chef Knife Set", "Kitchen", 120.00, "2023-11-04"),
    ("High-Speed Blender", "Kitchen", 65.00, "2023-11-16"),
    ("Non-Stick Frying Pan", "Kitchen", 34.50, "2023-11-22"),
    ("Electric Glass Kettle", "Kitchen", 29.99, "2023-12-01"),
    ("Toaster 4-Slice", "Kitchen", 42.00, "2023-12-10"),

    # Home Office
    ("Ergonomic Mesh Chair", "Home Office", 220.00, "2023-10-10"),
    ("Motorized Standing Desk", "Home Office", 380.00, "2023-10-22"),
    ("LED Desk Lamp with Wireless Charger", "Home Office", 45.00, "2023-11-08"),
    ("Monitor Arm Mount", "Home Office", 49.99, "2023-11-19"),
    ("Faux Leather Desk Pad", "Home Office", 19.99, "2023-12-05"),
    ("Footrest Under Desk", "Home Office", 28.50, "2023-12-14"),

    # Fitness & Outdoor
    ("Adjustable Dumbbell Set", "Fitness", 185.00, "2023-10-14"),
    ("Non-Slip Yoga Mat", "Fitness", 25.00, "2023-10-29"),
    ("Resistance Bands Kit", "Fitness", 18.00, "2023-11-11"),
    ("Stainless Steel Water Bottle", "Fitness", 22.50, "2023-11-25"),
    ("Deep Tissue Foam Roller", "Fitness", 24.00, "2023-12-08"),
    ("Smart Jump Rope", "Fitness", 35.00, "2023-12-18"),

    # Books & Learning
    ("Data Science from Scratch", "Books", 38.00, "2023-10-16"),
    ("Designing Data-Intensive Applications", "Books", 48.50, "2023-11-07"),
    ("Python Cookbook", "Books", 42.00, "2023-11-21"),
    ("Hands-On Machine Learning", "Books", 55.00, "2023-12-12")
]

def seed_database():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()

        # Check existing count
        cur.execute("SELECT COUNT(*) FROM sales;")
        before_count = cur.fetchone()[0]
        print(f"Current rows in sales: {before_count}")

        insert_sql = """
            INSERT INTO sales (product_name, category, price, date_sold)
            VALUES (%s, %s, %s, %s);
        """
        cur.executemany(insert_sql, SAMPLE_PRODUCTS)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM sales;")
        after_count = cur.fetchone()[0]
        print(f"Added {len(SAMPLE_PRODUCTS)} rows. Total rows now: {after_count}")

        cur.close()
        conn.close()
        print("Database seeded successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_database()
