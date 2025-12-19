import streamlit as st
import pandas as pd
from datetime import date, timedelta
from .database import get_data, save_plan, update_plan_extras

def show_page():
    st.title("📅 Daily Planner")
    user = st.session_state["username"]
    role = st.session_state["role"]

    with st.expander("➕ Create Plan"):
        with st.form("plan_form", clear_on_submit=True):
            dt = st.date_input("Date", date.today())
            lead = st.text_input("Lead", value=user)
            wu = st.text_area("Warm Up")
            lb = st.text_area("Learning Block")
            sp = st.text_area("Social Play")
            mn = st.text_area("Materials")
            if st.form_submit_button("Publish"):
                save_plan(dt, lead, "Team", wu, lb, "", sp, "", mn, "", user)
                st.rerun()

    st.divider()
    c1, c2 = st.columns(2)
    start = c1.date_input("From", date.today() - timedelta(days=2))
    end = c2.date_input("To", date.today() + timedelta(days=7))

    df = get_data("session_plans")
    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date']).dt.date
        filtered = df[(df['date_dt'] >= start) & (df['date_dt'] <= end)].sort_values('date_dt')
        
        for _, row in filtered.iterrows():
            with st.expander(f"🗓️ {row['date']} | Lead: {row['lead_staff']}"):
                st.write(f"**Warm Up:** {row['warm_up']}")
                st.write(f"**Learning:** {row['learning_block']}")
                st.write(f"**Materials:** {row['materials_needed']}")
                
                if row['staff_comments']: st.info(f"Comments: {row['staff_comments']}")
                with st.form(f"comm_{row['id']}", clear_on_submit=True):
                    c_text = st.text_input("Add comment")
                    if st.form_submit_button("Post"):
                        update_plan_extras(row['id'], f"\n{user}: {c_text}", None)
                        st.rerun()

                st.divider()
                if row['supervision_notes']: st.warning(f"Supervision: {row['supervision_notes']}")
                if role in ['admin', 'bc', 'ot', 'slp']:
                    if st.checkbox("✍️ Add Supervision", key=f"chk_{row['id']}"):
                        sup = st.text_area("Notes", key=f"area_{row['id']}")
                        if st.button("Save Report", key=f"btn_{row['id']}"):
                            update_plan_extras(row['id'], None, f"[{user.upper()}]: {sup}")
                            st.rerun()
