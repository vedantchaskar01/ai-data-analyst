import streamlit as st
import pandas as pd
import altair as alt
from decimal import Decimal
from llm import ask_database
from database import extract_schema

st.set_page_config(
    page_title="Universal AI Data Analyst",
    page_icon="🤖",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .latency-badge {
        font-size: 0.8rem;
        color: #059669;
        font-weight: 600;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown("**Model:** `gemini-3.1-flash-lite` ⚡")
    st.markdown("**Status:** Free Tier Active")
    
    if st.button("🔄 Refresh Database Schema"):
        with st.spinner("Refreshing schema cache..."):
            extract_schema(force_refresh=True)
            st.success("Schema cache updated!")

    st.divider()
    st.subheader("📚 Available Tables")
    schema = extract_schema()
    if schema:
        for tbl, details in schema.items():
            with st.expander(f"📁 {tbl} ({len(details['columns'])} cols)"):
                for col in details["columns"]:
                    st.caption(f"• {col}")
    else:
        st.warning("No database tables found or connection error.")

    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

st.title("Universal AI Data Analyst 🤖")
st.caption("Ask questions about your PostgreSQL database in plain English — now powered by gemini-3.1-flash-lite.")

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: float(v) if isinstance(v, Decimal) else v for k, v in obj.items()}
    return obj

def render_chart(df: pd.DataFrame, analysis: dict):
    chart_type = analysis.get("chart_type", "None")
    x_col = analysis.get("x_col")
    y_col = analysis.get("y_col")
    title = analysis.get("title", "")

    # Clean DataFrame: ensure numeric conversions
    numeric_df = df.copy()
    for col in numeric_df.columns:
        try:
            numeric_df[col] = pd.to_numeric(numeric_df[col])
        except Exception:
            pass

    # Metric KPI Card
    if chart_type == "Metric" or (len(numeric_df) == 1 and len(numeric_df.columns) == 1):
        col_name = y_col if y_col in numeric_df.columns else numeric_df.columns[0]
        raw_val = numeric_df[col_name].iloc[0]
        try:
            val_display = f"{float(raw_val):,.2f}" if isinstance(raw_val, (int, float)) else str(raw_val)
        except Exception:
            val_display = str(raw_val)
        label_display = title if title else col_name.replace('_', ' ').title()
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">{label_display}</div>
            <div class="metric-value">{val_display}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Fallback column detection if not provided
    if not x_col or x_col not in numeric_df.columns:
        x_col = numeric_df.columns[0]
    if not y_col or y_col not in numeric_df.columns:
        # Find first numeric column different from x_col
        candidate_y = [c for c in numeric_df.columns if c != x_col and pd.api.types.is_numeric_dtype(numeric_df[c])]
        y_col = candidate_y[0] if candidate_y else (numeric_df.columns[1] if len(numeric_df.columns) > 1 else numeric_df.columns[0])

    if chart_type == "Bar":
        try:
            chart = alt.Chart(numeric_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X(f"{x_col}:N", title=x_col.replace('_', ' ').title(), sort='-y'),
                y=alt.Y(f"{y_col}:Q", title=y_col.replace('_', ' ').title()),
                color=alt.Color(f"{x_col}:N", legend=None, scale=alt.Scale(scheme='tableau10')),
                tooltip=[x_col, y_col]
            ).properties(title=title, height=350)
            st.altair_chart(chart, use_container_width=True)
        except Exception as e:
            st.bar_chart(numeric_df.set_index(x_col)[y_col])

    elif chart_type == "Line":
        try:
            chart = alt.Chart(numeric_df).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X(f"{x_col}:N", title=x_col.replace('_', ' ').title()),
                y=alt.Y(f"{y_col}:Q", title=y_col.replace('_', ' ').title()),
                tooltip=[x_col, y_col]
            ).properties(title=title, height=350)
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            st.line_chart(numeric_df.set_index(x_col)[y_col])

    elif chart_type == "Pie":
        try:
            chart = alt.Chart(numeric_df).mark_arc(innerRadius=35).encode(
                theta=alt.Theta(f"{y_col}:Q"),
                color=alt.Color(f"{x_col}:N", scale=alt.Scale(scheme='tableau10')),
                tooltip=[x_col, y_col]
            ).properties(title=title, height=350)
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            st.dataframe(numeric_df)
    else:
        st.info("No visualization required for this query result.")

def display_assistant_response(insight, time_taken, data_list, sql_query, analysis):
    if insight:
        st.markdown(insight)
    if time_taken:
        st.markdown(f"<div class='latency-badge'>⚡ Executed in {time_taken}s</div>", unsafe_allow_html=True)

    if len(data_list) > 0:
        df = pd.DataFrame(convert_decimals(data_list))
        chart_type = analysis.get("chart_type", "None") if analysis else "None"
        
        if chart_type != "None":
            t1, t2, t3 = st.tabs(["📊 Visualization", "📋 Data Table", "🔍 SQL Query"])
            with t1:
                render_chart(df, analysis or {})
            with t2:
                st.dataframe(df, use_container_width=True)
            with t3:
                st.code(sql_query, language="sql")
        else:
            t1, t2 = st.tabs(["📋 Data Table", "🔍 SQL Query"])
            with t1:
                st.dataframe(df, use_container_width=True)
            with t2:
                st.code(sql_query, language="sql")
    elif sql_query:
        st.code(sql_query, language="sql")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            display_assistant_response(
                msg.get("content", ""),
                msg.get("time_taken"),
                msg.get("data", []),
                msg.get("sql", ""),
                msg.get("analysis", {})
            )

# Chat input
if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing question & querying PostgreSQL..."):
            res = ask_database(prompt)

        if not res:
            st.error("Failed to connect or retrieve data from the database.")
        else:
            sql_query = res.get("sql", "")
            data_list = convert_decimals(res.get("data", []))
            analysis = res.get("analysis") or {}
            time_taken = res.get("time_taken", 0)
            insight = analysis.get("insight", "Here is your data.")

            display_assistant_response(insight, time_taken, data_list, sql_query, analysis)

            st.session_state.messages.append({
                "role": "assistant",
                "content": insight,
                "sql": sql_query,
                "data": data_list,
                "analysis": analysis,
                "time_taken": time_taken
            })
