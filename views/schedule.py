# views/schedule.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from .database import ENGINE, get_list_data

# --- DATABASE HELPERS ---
def create_appointment(date, time, child, discipline, staff, cost, status):
    sql = text("INSERT INTO appointments (date, time, child_name, discipline, staff, cost, status) VALUES (:d, :t, :c, :dis, :st, :co, :stat)")
    with ENGINE.connect() as conn:
        conn.execute(sql, {"d": str(date), "t": str(time), "c": child, "dis": discipline, "st": staff, "co": cost, "stat": status})
        conn.commit()

def delete_appointment(appt_id):
    with ENGINE.connect() as conn:
        conn.execute(text("DELETE FROM appointments WHERE id = :id"), {"id": appt_id})
        conn.commit()

# --- MAIN PAGE ---
def show_page():
    st.title("🗓️ Schedule & Appointments")
    role = st.session_state.get('role', '')
    child_link = st.session_state.get('child_link')

    if role == "admin":
        with st.expander("➕ Schedule New Session"):
            with st.form("schedule_form", clear_on_submit=True):
                c_df = get_list_data("children")
                d_df = get_list_data("disciplines")
                
                col1, col2 = st.columns(2)
                s_date = col1.date_input("Date")
                s_time = col1.time_input("Time")
                child = col1.selectbox("Child", c_df['child_name'].tolist() if not c_df.empty else [])
                
                disc = col2.selectbox("Discipline", d_df['name'].tolist() if not d_df.empty else [])
                staff = col2.text_input("Assign Staff Member")
                cost = col2.number_input("Session Cost ($)", value=120.0)
                status = st.selectbox("Status", ["Scheduled", "Completed", "Cancelled", "No-Show"])
                
                if st.form_submit_button("Book Appointment"):
                    create_appointment(s_date, s_time, child, disc, staff, cost, status)
                    st.success("Session booked!")
                    st.rerun()

    st.divider()

    # VIEWING LOGIC
    with ENGINE.connect() as conn:
        if role == "parent":
            df = pd.read_sql(text("SELECT * FROM appointments WHERE child_name = :c ORDER BY date ASC, time ASC"), conn, params={"c": child_link})
        else:
            df = pd.read_sql(text("SELECT * FROM appointments ORDER BY date ASC, time ASC"), conn)

    if not df.empty:
        st.subheader("Upcoming Sessions")
        
        # Create a clean calendar-like view
        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                
                c1.markdown(f"### 🕒 {row['time']}")
                c1.write(f"**Date:** {row['date']}")
                
                c2.write(f"**Child:** {row['child_name']}")
                c2.write(f"**Specialist:** {row['staff']} ({row['discipline']})")
                
                status_color = "green" if row['status'] == "Completed" else "blue"
                if row['status'] == "Cancelled": status_color = "red"
                
                c3.markdown(f":{status_color}[**{row['status']}**]")
                if role == "admin":
                    if c3.button("Delete", key=f"del_apt_{row['id']}"):
                        delete_appointment(row['id'])
                        st.rerun()
    else:
        st.info("No appointments scheduled.")
