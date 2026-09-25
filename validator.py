import sqlglot
from sqlglot import exp

def sanitize_query(sql_query: str) -> str:
    try:
        parsed = sqlglot.parse_one(sql_query, read="postgres")
        if not isinstance(parsed, exp.Select):
            raise ValueError(f"Blocked: Only SELECT queries allowed. Got {parsed.key.upper()}")
        if not parsed.args.get("limit"):
            parsed = parsed.limit(100)
        return parsed.sql(dialect="postgres")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"SQL parsing error: {e}")
