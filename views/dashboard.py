import streamlit as st
from .database import get_data, get_attendance_data, get_messages, update_parent_feedback

def show_page():
    role = st.session_state["role"]
    child = st.session_state["child_link"]
    st.title("📊 Dashboard")

    # Messages
    msgs = get_messages(child if role == "parent" else "All")
    if not msgs.empty:
        for _, m in msgs.iterrows():
            st.info(f"📢 {m['type']}: {m['content']} (by {m['author']})")

    # Progress
    df = get_data("progress")
    if role == "parent": df = df[df['child_name'] == child]
    
    for _, row in df.sort_values('id', ascending=False).iterrows():
        with st.container(border=True):
            st.write(f"### {row['discipline']} - {row['status']}")
            st.write(f"**Note:** {row['parent_note']}")
            if role == "parent":
                with st.form(f"fb_{row['id']}", clear_on_submit=True):
                    fb = st.text_area("Feedback/Questions")
                    if st.form_submit_button("Send"):
                        update_parent_feedback(row['id'], fb)
                        st.rerun()
            elif row['parent_feedback']:
                st.warning(f"Parent Feedback: {row['parent_feedback']}")
