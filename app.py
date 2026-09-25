import os
import re
from decimal import Decimal
import pandas as pd
import altair as alt
import streamlit as st
import importlib
import database
import llm
importlib.reload(database)
importlib.reload(llm)
from database import extract_schema, execute_safe_query, import_dataframe_to_db
from llm import ask_database

st.set_page_config(
    page_title="Universal AI Data Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 22px;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 22px;
    }

    .top-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
    }

    .top-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #047857;
    }

    .badge-dot {
        width: 7px;
        height: 7px;
        background-color: #10b981;
        border-radius: 50%;
    }

    .section-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 10px;
    }

    .kpi-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #334155;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .hero-metric-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 24px;
        text-align: center;
        margin-bottom: 16px;
    }

    .hero-metric-val {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.02em;
    }

    .hero-metric-lbl {
        font-size: 0.8125rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }

    .insight-callout {
        background-color: #f8fafc;
        border-left: 3px solid #0f172a;
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        margin-bottom: 16px;
        font-size: 0.95rem;
        color: #1e293b;
        font-weight: 500;
    }

    .execution-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #64748b;
        margin-bottom: 12px;
    }

    .stTextArea textarea {
        font-size: 0.9rem;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
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
    except Exception:
        pass
    return info

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: float(v) if isinstance(v, Decimal) else v for k, v in obj.items()}
    return obj

def generate_dynamic_prompts(table_name: str, columns_list: list):
    prompts = []
    numeric_cols = []
    date_cols = []
    categorical_cols = []

    for col_str in columns_list:
        raw_name = col_str.split(" (")[0]
        raw_type = col_str.split(" (")[1].replace(")", "").lower() if " (" in col_str else "text"
        
        if any(t in raw_type for t in ["int", "numeric", "real", "double", "float"]) and not raw_name.endswith("_id"):
            numeric_cols.append(raw_name)
        elif any(t in raw_type for t in ["date", "time", "timestamp"]):
            date_cols.append(raw_name)
        elif any(t in raw_type for t in ["char", "text", "varchar"]) and not raw_name.endswith("_id"):
            categorical_cols.append(raw_name)

    if categorical_cols and numeric_cols:
        prompts.append(f"Top 5 {categorical_cols[0]} by total {numeric_cols[0]}")
    if date_cols and numeric_cols:
        prompts.append(f"Monthly trend of {numeric_cols[0]} over time")
    if numeric_cols:
        prompts.append(f"Average and total {numeric_cols[0]} across {table_name}")
    if categorical_cols:
        prompts.append(f"Count of records grouped by {categorical_cols[0]}")
    
    prompts.append(f"Show first 10 rows of {table_name}")
    return prompts[:4]

db_name = os.getenv("DB_NAME", "postgres")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")

db_info = get_database_info()
schema = extract_schema()
table_names = list(schema.keys()) if schema else []

if "history" not in st.session_state:
    st.session_state.history = []

if "active_result" not in st.session_state:
    st.session_state.active_result = None

with st.sidebar:
    st.markdown("### Universal Data Ingestion")
    uploaded_file = st.file_uploader("Upload any CSV dataset", type=["csv"])
    
    if uploaded_file is not None:
        custom_tbl_name = re.sub(r"[^a-zA-Z0-9_]", "_", os.path.splitext(uploaded_file.name)[0].lower())
        table_input = st.text_input("Destination Table Name", value=custom_tbl_name)
        
        if st.button("Import to PostgreSQL", type="primary", width="stretch"):
            with st.spinner("Parsing and importing dataset..."):
                try:
                    df_up = pd.read_csv(uploaded_file, encoding="latin1")
                    rows_loaded = import_dataframe_to_db(df_up, table_input)
                    extract_schema(force_refresh=True)
                    get_database_info.clear()
                    st.success(f"Imported {rows_loaded:,} rows into '{table_input}'")
                    st.rerun()
                except Exception as err:
                    st.error(f"Import error: {err}")

    st.markdown("---")
    st.markdown("### Database Cluster")
    st.caption(f"{db_name} @ {db_host}:{db_port}")

    if st.button("Sync Schema Cache", width="stretch"):
        extract_schema(force_refresh=True)
        get_database_info.clear()
        st.rerun()

    st.markdown("### Schema Catalog")
    if schema:
        for t_name, t_meta in schema.items():
            col_count = len(t_meta.get("columns", []))
            with st.expander(f"{t_name} ({col_count} cols)"):
                for col_entry in t_meta.get("columns", []):
                    st.caption(f"• {col_entry}")
    else:
        st.caption("No public tables identified.")

    st.markdown("---")
    if st.button("Clear Conversation", width="stretch"):
        st.session_state.history = []
        st.session_state.active_result = None
        st.rerun()

st.markdown(f"""
<div class="top-header">
    <div>
        <h1 class="top-title">Universal Natural-Language Data Analyst</h1>
        <div style="font-size:0.85rem; color:#64748b; margin-top:3px;">Ask questions about any dataset in plain English. Powered by PostgreSQL and Gemini.</div>
    </div>
    <div class="top-badge">
        <span class="badge-dot"></span>
        <span>Connected: {db_name}</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([4, 6], gap="medium")

with col_left:
    st.markdown('<div class="section-label">Data Source & Query Console</div>', unsafe_allow_html=True)
    
    selected_table = st.selectbox(
        "Active Table",
        table_names if table_names else ["No tables found"],
        key="active_table_select"
    )

    suggested_run = None
    if selected_table and selected_table in schema:
        cols_meta = schema[selected_table].get("columns", [])
        row_estimate = db_info.get("tables", {}).get(selected_table, 0)
        
        st.markdown(f"""
        <div style="margin-bottom: 12px;">
            <span class="kpi-chip">{len(cols_meta)} Columns</span>
            <span class="kpi-chip">{row_estimate:,} Records</span>
            <span class="kpi-chip">PostgreSQL Ready</span>
        </div>
        """, unsafe_allow_html=True)

        dynamic_suggestions = generate_dynamic_prompts(selected_table, cols_meta)
        
        st.markdown("<div style='font-size:0.75rem; font-weight:600; color:#64748b; margin-bottom:6px;'>Dynamic Suggestions for this Dataset:</div>", unsafe_allow_html=True)
        for s_idx, prompt_sug in enumerate(dynamic_suggestions):
            if st.button(prompt_sug, key=f"sug_{s_idx}", width="stretch"):
                suggested_run = prompt_sug

    query_input = st.text_area(
        "Ask a question in plain English:",
        value=suggested_run if suggested_run else "",
        placeholder="e.g. Which categories had the highest performance?",
        height=100
    )

    run_submitted = st.button("Run Analysis", type="primary", width="stretch")

    if st.session_state.history:
        st.markdown("---")
        st.markdown('<div class="section-label">Recent Questions</div>', unsafe_allow_html=True)
        for h_idx, past_item in enumerate(reversed(st.session_state.history[-5:])):
            q_label = past_item.get("question", "")
            if st.button(q_label, key=f"hist_btn_{h_idx}", width="stretch"):
                st.session_state.active_result = past_item
                st.rerun()

def render_chart_output(df: pd.DataFrame, analysis: dict):
    chart_type = analysis.get("chart_type", "None")
    x_col = analysis.get("x_col")
    y_col = analysis.get("y_col")
    title = analysis.get("title", "")

    numeric_df = df.copy()
    for col in numeric_df.columns:
        try:
            numeric_df[col] = pd.to_numeric(numeric_df[col])
        except Exception:
            pass

    if chart_type == "Metric" or (len(numeric_df) == 1 and len(numeric_df.columns) == 1):
        target_col = y_col if y_col in numeric_df.columns else numeric_df.columns[0]
        raw_val = numeric_df[target_col].iloc[0]
        try:
            val_str = f"{float(raw_val):,.2f}" if isinstance(raw_val, (int, float)) else str(raw_val)
        except Exception:
            val_str = str(raw_val)
        lbl_str = title if title else target_col.replace("_", " ").title()
        st.markdown(f"""
        <div class="hero-metric-box">
            <div class="hero-metric-lbl">{lbl_str}</div>
            <div class="hero-metric-val">{val_str}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    if not x_col or x_col not in numeric_df.columns:
        x_col = numeric_df.columns[0]
    if not y_col or y_col not in numeric_df.columns:
        candidates = [c for c in numeric_df.columns if c != x_col and pd.api.types.is_numeric_dtype(numeric_df[c])]
        y_col = candidates[0] if candidates else (numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0])

    if chart_type == "Bar":
        try:
            chart = alt.Chart(numeric_df).mark_bar(color="#0f172a", cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                x=alt.X(f"{x_col}:N", title=x_col.replace("_", " ").title(), sort="-y"),
                y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title()),
                tooltip=[x_col, y_col]
            ).properties(title=title, height=360)
            st.altair_chart(chart, width="stretch")
        except Exception:
            st.bar_chart(numeric_df.set_index(x_col)[y_col])

    elif chart_type == "Line":
        try:
            chart = alt.Chart(numeric_df).mark_line(point=True, strokeWidth=2.5, color="#2563eb").encode(
                x=alt.X(f"{x_col}:N", title=x_col.replace("_", " ").title()),
                y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title()),
                tooltip=[x_col, y_col]
            ).properties(title=title, height=360)
            st.altair_chart(chart, width="stretch")
        except Exception:
            st.line_chart(numeric_df.set_index(x_col)[y_col])

    elif chart_type == "Pie":
        try:
            chart = alt.Chart(numeric_df).mark_arc(innerRadius=35).encode(
                theta=alt.Theta(f"{y_col}:Q"),
                color=alt.Color(f"{x_col}:N", scale=alt.Scale(scheme="tableau10")),
                tooltip=[x_col, y_col]
            ).properties(title=title, height=360)
            st.altair_chart(chart, width="stretch")
        except Exception:
            st.dataframe(numeric_df, width="stretch")
    else:
        st.dataframe(numeric_df, width="stretch")

with col_right:
    st.markdown('<div class="section-label">Analytics Canvas</div>', unsafe_allow_html=True)

    if run_submitted and query_input.strip():
        with st.spinner("Synthesizing SQL and querying database..."):
            query_res = ask_database(query_input.strip())
        
        if query_res:
            res_obj = {
                "question": query_input.strip(),
                "sql": query_res.get("sql", ""),
                "data": convert_decimals(query_res.get("data", [])),
                "analysis": query_res.get("analysis") or {},
                "time_taken": query_res.get("time_taken", 0)
            }
            st.session_state.active_result = res_obj
            st.session_state.history.append(res_obj)
        else:
            st.error("Query execution failed. Check backend connectivity.")

    active = st.session_state.active_result

    if active:
        q_text = active.get("question", "")
        summary = active.get("analysis", {}).get("insight", "")
        duration = active.get("time_taken", 0)
        data_rows = active.get("data", [])
        sql_stmt = active.get("sql", "")
        analysis_dict = active.get("analysis", {})

        st.markdown(f"**Inquiry:** {q_text}")
        if summary:
            st.markdown(f'<div class="insight-callout">{summary}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="execution-tag">COMPLETED IN {duration}s • {len(data_rows)} ROWS RETURNED</div>', unsafe_allow_html=True)

        if data_rows:
            df_out = pd.DataFrame(data_rows)
            t_chart, t_grid, t_sql = st.tabs(["Visualization", "Data Table", "SQL Statement"])

            with t_chart:
                render_chart_output(df_out, analysis_dict)

            with t_grid:
                st.dataframe(df_out, width="stretch")
                csv_file = df_out.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Export CSV",
                    data=csv_file,
                    file_name="query_export.csv",
                    mime="text/csv",
                    key=f"exp_{abs(hash(sql_stmt))}"
                )

            with t_sql:
                st.code(sql_stmt, language="sql")
        else:
            st.info("Query returned no matching records.")
            if sql_stmt:
                st.code(sql_stmt, language="sql")

    else:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px; padding:30px; text-align:center;">
            <div style="font-weight:600; color:#334155; font-size:1.05rem;">Universal Analytics Canvas Ready</div>
            <div style="color:#64748b; font-size:0.875rem; margin-top:6px; max-width:440px; margin-left:auto; margin-right:auto;">
                Ask any question about your data on the left, click a dynamic suggestion, or upload any new dataset in the sidebar.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if selected_table and selected_table in schema:
            st.markdown(f"<div style='margin-top:20px; font-size:0.8rem; font-weight:700; color:#64748b; text-transform:uppercase;'>Live Preview: {selected_table}</div>", unsafe_allow_html=True)
            samples = schema[selected_table].get("sample_rows", [])
            if samples:
                st.dataframe(pd.DataFrame(convert_decimals(samples)), width="stretch")
