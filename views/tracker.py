import streamlit as st
from datetime import date
from .database import get_list_data, save_progress, get_data

def show_page():
    st.title("📝 Progress Tracker")
    user = st.session_state["username"]
    
    with st.form("tracker_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Date", date.today())
        child = c1.selectbox("Child", get_list_data("children")["child_name"].tolist())
        disc = c2.selectbox("Discipline", get_list_data("disciplines")["name"].tolist())
        goal = c1.selectbox("Goal Area", get_list_data("goal_areas")["name"].tolist())
        stat = c2.selectbox("Status", ["Progressing", "Mastered", "Emerging", "Regression", "Not Observed"])
        
        clin = st.text_area("🔒 Clinical Notes (Internal)")
        p_note = st.text_area("👨‍👩‍👧 Note to Parents")
        media = st.text_input("Media URL")
        
        if st.form_submit_button("Save Entry"):
            save_progress(dt, child, disc, goal, stat, clin, media, user, p_note)
            st.success("Saved and cleared!")

    st.divider()
    df = get_data("progress").sort_values('id', ascending=False)
    if not df.empty:
        st.subheader("Recent History")
        st.dataframe(df.head(10), use_container_width=True)
