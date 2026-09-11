import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Database Connection
def get_connection():
    return sqlite3.connect("health_data.db")

# Setup Tables (if not present)
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT,
            weight REAL,
            bp_sys INTEGER,
            bp_dia INTEGER,
            heart_rate INTEGER,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()

st.title("🩺 Multi-User Health Tracker")

# 1. Profile Selection & Creation
st.subheader("Select Profile")
col_user, col_new = st.columns([2, 2])

with get_connection() as conn:
    users_df = pd.read_sql_query("SELECT id, name FROM users", conn)

user_names = users_df["name"].tolist() if not users_df.empty else []

with col_new:
    new_name = st.text_input("Add New User")
    if st.button("Add User"):
        if new_name.strip():
            try:
                with get_connection() as conn:
                    conn.cursor().execute("INSERT INTO users (name) VALUES (?)", (new_name.strip(),))
                    conn.commit()
                st.success(f"Added {new_name}!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("User already exists.")

selected_user = col_user.selectbox("User:", ["-- Select --"] + user_names)

if selected_user and selected_user != "-- Select --":
    user_id = int(users_df[users_df["name"] == selected_user]["id"].values[0])

    # 2. Log New Health Data
    st.subheader("Log New Health Data")
    with st.form("health_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        weight = f_col1.number_input("Weight (kg)", min_value=0.0, step=0.1)
        heart_rate = f_col1.number_input("Heart Rate (BPM)", min_value=0, step=1)
        
        bp_sys = f_col2.number_input("Systolic BP (Sys)", min_value=0, step=1)
        bp_dia = f_col2.number_input("Diastolic BP (Dia)", min_value=0, step=1)
        
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Log")

        if submitted:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with get_connection() as conn:
                conn.cursor().execute("""
                    INSERT INTO health_logs (user_id, timestamp, weight, bp_sys, bp_dia, heart_rate, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, now, weight, bp_sys, bp_dia, heart_rate, notes))
                conn.commit()
            st.success("Log saved successfully!")
            st.rerun()

    # 3. Health History
    st.subheader("Health History")
    with get_connection() as conn:
        logs_df = pd.read_sql_query("""
            SELECT timestamp AS Date, weight || ' kg' AS Weight, 
                   bp_sys || '/' || bp_dia AS [Blood Pressure], 
                   heart_rate || ' bpm' AS [Heart Rate], notes AS Notes
            FROM health_logs 
            WHERE user_id = ? 
            ORDER BY id DESC
        """, conn, params=(user_id,))
    
    st.dataframe(logs_df, use_container_width=True)