import os
import re
import pandas as pd
from decimal import Decimal
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import io

from database import extract_schema, execute_safe_query, import_dataframe_to_db
from llm import ask_database

app = FastAPI(title="AI-Powered Natural-Language Data Analyst API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_database_info():
    info = {"tables": {}, "total_records": 0}
    try:
        rows = execute_safe_query("SELECT relname AS table_name, n_live_tup AS row_count FROM pg_stat_user_tables ORDER BY relname;")
        if rows:
            for r in rows:
                t_name = r["table_name"]
                t_count = int(r.get("row_count", 0))
                info["tables"][t_name] = t_count
                info["total_records"] += t_count
    except Exception as e:
        print(f"Error getting db info: {e}")
    return info

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: float(v) if isinstance(v, Decimal) else v for k, v in obj.items()}
    return obj

class QueryRequest(BaseModel):
    query: str

@app.get("/api/db-info")
def get_db_info():
    db_name = os.getenv("DB_NAME", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    db_info = get_database_info()
    schema = extract_schema()
    
    return {
        "db_name": db_name,
        "db_host": db_host,
        "db_port": db_port,
        "db_info": db_info,
        "schema": schema
    }

@app.post("/api/import")
async def import_csv(file: UploadFile = File(...), table_name: str = Form(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents), encoding="latin1")
        
        # Format table name to be safe
        safe_table_name = re.sub(r"[^a-zA-Z0-9_]", "_", table_name.lower())
        
        rows_loaded = import_dataframe_to_db(df, safe_table_name)
        
        # Refresh schema cache by extracting it (it refreshes internal cache in database.py if implemented, else just re-fetches)
        extract_schema(force_refresh=True)
        
        return {"success": True, "message": f"Imported {rows_loaded:,} rows into '{safe_table_name}'", "rows_loaded": rows_loaded, "table_name": safe_table_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
def run_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    query_res = ask_database(req.query.strip())
    
    if query_res:
        query_res["data"] = convert_decimals(query_res.get("data", []))
        return query_res
    else:
        raise HTTPException(status_code=500, detail="Query execution failed. Check backend connectivity or schema.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
