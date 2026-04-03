import streamlit as st
import sqlite3
import openai
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI SQL Assistant", page_icon="🤖", layout="wide")

st.title("🤖 Natural Language to SQL Query Generator")
st.markdown("*Ask business questions in plain English - get data instantly!*")

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        openai.api_key = api_key
        st.success("✓ API Key set")
    
    st.markdown("---")
    st.header("📊 Database Info")
    
    def get_connection():
        """Create a new database connection for each request"""
        return sqlite3.connect('sales_database.db', check_same_thread=False)
    
    conn = get_connection()
    sales_count = pd.read_sql_query("SELECT COUNT(*) as count FROM sales", conn)
    st.metric("Sales Records", sales_count['count'].iloc[0])
    conn.close()
    
    st.markdown("---")
    st.header("📝 Sample Questions")
    st.markdown("- Show me top 10 customers by revenue")
    st.markdown("- What is total sales by product category?")
    st.markdown("- Which city has the most orders?")

def get_schema(conn):
    schema = "DATABASE SCHEMA:\n"
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    for _, table in tables.iterrows():
        table_name = table['name']
        columns = pd.read_sql_query(f"PRAGMA table_info({table_name})", conn)
        schema += f"\n{table_name}: " + ", ".join(columns['name'].tolist())
    return schema

def generate_sql(question, schema):
    prompt = f"""Convert to SQLite SQL:
{schema}
Question: {question}
SQL:"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.3
    )
    sql = response.choices[0].message.content
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

question = st.text_area("💬 Your Question:", height=100, placeholder="Example: Show me top 10 customers by revenue")

if st.button("🔍 Generate & Execute", type="primary"):
    if not api_key:
        st.error("Please enter your OpenAI API key")
    elif question:
        with st.spinner("Generating SQL..."):
            conn = get_connection()
            schema = get_schema(conn)
            sql = generate_sql(question, schema)
            st.code(sql, language="sql")
            try:
                result = pd.read_sql_query(sql, conn)
                st.success(f"✅ {len(result)} rows returned")
                st.dataframe(result)
                csv = result.to_csv(index=False)
                st.download_button("📥 Download CSV", csv, "results.csv")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                conn.close()
