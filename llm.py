import os
from google import genai
from database import extract_schema, execute_safe_query

def generate_sql(question: str, schema: dict) -> str:
    client = genai.Client()
    prompt = f"""
You are a PostgreSQL expert.
Write a SQL query to answer the user's question based on the schema.
Return ONLY the raw SQL query. Do not wrap it in markdown (no ```sql).

Schema:
{schema}

Question:
{question}
"""
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt
    )
    return response.text.strip().replace('```sql', '').replace('```', '').strip()

def ask_database(question: str):
    schema = extract_schema()
    if not schema:
        print("db error")
        return None
    
    max_retries = 3
    current_question = question

    for attempt in range(max_retries):
        sql = generate_sql(current_question, schema)
        print(f"gen sql: {sql}")
        try:
            results = execute_safe_query(sql)
            print("results:")
            for r in results:
                print(r)
            return results
        except Exception as e:
            print(f"err: {e}")
            current_question = f"My last question was: {question}. Your SQL was: {sql}. It failed with error: {e}. Fix the SQL and return ONLY the raw SQL string."
            print("retrying...")
    
    print("max retries hit")
    return None

if __name__ == "__main__":
    q = "What are the names and prices of all electronics?"
    print(f"Q: {q}")
    ask_database(q)
