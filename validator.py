import sqlglot
from sqlglot import exp

def sanitize_query(sql_query: str) -> str:
    try:
        parsed = sqlglot.parse_one(sql_query, read="postgres")
        if not isinstance(parsed, exp.Select):
            raise ValueError(f"Blocked: Only SELECT allowed. Got {parsed.key.upper()}")
        if not parsed.args.get("limit"):
            parsed = parsed.limit(100)
        return parsed.sql(dialect="postgres")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"Bad SQL: {e}")

if __name__ == "__main__":
    test_queries = [
        "SELECT product_name, price FROM sales ORDER BY price DESC",
        "SELECT * FROM sales LIMIT 5",
        "DELETE FROM sales WHERE id = 1",
        "DROP TABLE sales"
    ]
    for q in test_queries:
        print(f"Q: {q}")
        try:
            safe_q = sanitize_query(q)
            print(f"Ok: {safe_q}")
        except ValueError as e:
            print(f"Err: {e}")
        print("---")
