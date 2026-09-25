import os
import json
import re
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import extract_schema, execute_safe_query

load_dotenv()

MODEL_NAME = "gemini-3.1-flash-lite"
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client

def generate_sql(question: str, schema: dict) -> str:
    client = get_client()
    prompt = f"""You are an expert PostgreSQL database analyst.
Generate a valid, highly efficient PostgreSQL query to answer the user's question.
Rules:
1. ONLY return the raw SQL query string.
2. Do NOT wrap the query in markdown, code blocks (no ```sql), or explanations.
3. Only use tables and columns present in the schema.

Schema:
{schema}

User Question:
{question}
"""
    config = types.GenerateContentConfig(
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config
    )
    sql = response.text.strip()
    sql = re.sub(r"^```(?:sql)?", "", sql, flags=re.IGNORECASE).strip()
    sql = re.sub(r"```$", "", sql).strip()
    return sql

def heuristic_chart_analysis(question: str, data: list) -> dict:
    if not data:
        return {"insight": "No data found for this question.", "chart_type": "None", "title": ""}
    
    first_row = data[0]
    keys = list(first_row.keys())
    
    if len(data) == 1 and len(keys) == 1:
        val = first_row[keys[0]]
        return {
            "insight": f"{keys[0].replace('_', ' ').title()}: {val}",
            "chart_type": "Metric",
            "x_col": keys[0],
            "y_col": keys[0],
            "title": keys[0].replace("_", " ").title()
        }
    
    numeric_cols = []
    string_cols = []
    for k in keys:
        val = first_row[k]
        try:
            float(val)
            numeric_cols.append(k)
        except (ValueError, TypeError):
            string_cols.append(k)
            
    if string_cols and numeric_cols:
        x = string_cols[0]
        y = numeric_cols[0]
        chart_type = "Line" if any(w in x.lower() for w in ["date", "time", "month", "year", "day"]) else "Bar"
        return {
            "insight": f"Breakdown of {y.replace('_', ' ')} by {x.replace('_', ' ')}.",
            "chart_type": chart_type,
            "x_col": x,
            "y_col": y,
            "title": f"{y.replace('_', ' ').title()} by {x.replace('_', ' ').title()}"
        }
        
    return {
        "insight": "Displaying query results.",
        "chart_type": "None",
        "title": ""
    }

def generate_insights(question: str, data: list) -> dict:
    if not data:
        return {"insight": "No matching records found in the database.", "chart_type": "None", "title": ""}
    
    sample_data = data[:15]
    client = get_client()
    prompt = f"""You are a business intelligence analyst.
Analyze the following data that answers the user's question.
Provide a concise 1-sentence business insight and recommend visualization settings.

Available chart types: 'Bar', 'Line', 'Pie', 'Metric' (if only 1 aggregate value), or 'None'.

Output valid JSON ONLY with this exact structure:
{{
    "insight": "1-sentence business takeaway.",
    "chart_type": "Bar|Line|Pie|Metric|None",
    "x_col": "column_name_for_x_axis_or_null",
    "y_col": "column_name_for_y_axis_or_null",
    "title": "Short descriptive chart title"
}}

User Question: {question}
Data Sample: {sample_data}
"""
    config = types.GenerateContentConfig(
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config
        )
        raw_text = response.text.strip()
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return heuristic_chart_analysis(question, data)
    except Exception:
        return heuristic_chart_analysis(question, data)

def ask_database(question: str):
    start_time = time.time()
    schema = extract_schema()
    if not schema:
        return None

    max_retries = 2
    current_prompt = question
    sql = ""
    results = None

    for attempt in range(max_retries):
        try:
            sql = generate_sql(current_prompt, schema)
            results = execute_safe_query(sql)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                current_prompt = f"Previous SQL: {sql}\nFailed with error: {e}\nFix the query. User question: {question}"
            else:
                return {
                    "sql": sql,
                    "data": [],
                    "analysis": {"insight": f"Query execution failed: {e}", "chart_type": "None"},
                    "time_taken": round(time.time() - start_time, 2)
                }

    if results is None:
        results = []

    try:
        analysis = generate_insights(question, results)
    except Exception:
        analysis = heuristic_chart_analysis(question, results)

    time_taken = round(time.time() - start_time, 2)
    return {
        "sql": sql,
        "data": results,
        "analysis": analysis,
        "time_taken": time_taken
    }
