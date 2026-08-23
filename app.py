import streamlit as st
import pandas as pd
from llm import ask_database

st.set_page_config(page_title="Universal Data Analyst", layout="wide")
st.title("Universal AI Data Analyst 🤖")
st.write("Ask questions about your PostgreSQL database in plain English.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg and msg["sql"]:
            st.code(msg["sql"], language="sql")
        if "data" in msg and len(msg["data"]) > 0:
            df = pd.DataFrame(msg["data"])
            st.dataframe(df)
            if msg.get("chart") == "Bar":
                st.bar_chart(df.set_index(df.columns[0]))
            elif msg.get("chart") == "Line":
                st.line_chart(df.set_index(df.columns[0]))

if prompt := st.chat_input("Ask a question about the database..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            res = ask_database(prompt)
            if not res:
                st.error("Failed to get an answer from the database.")
            else:
                sql_query = res.get("sql", "")
                data_list = res.get("data", [])
                analysis = res.get("analysis") or {}
                
                insight = analysis.get("insight", "Here is your data.")
                chart_type = analysis.get("chart_type", "None")
                
                st.markdown(insight)
                st.code(sql_query, language="sql")
                
                if len(data_list) > 0:
                    df = pd.DataFrame(data_list)
                    st.dataframe(df)
                    if chart_type == "Bar":
                        st.bar_chart(df.set_index(df.columns[0]))
                    elif chart_type == "Line":
                        st.line_chart(df.set_index(df.columns[0]))
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": insight,
                    "sql": sql_query,
                    "data": data_list,
                    "chart": chart_type
                })
