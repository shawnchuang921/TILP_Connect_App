import streamlit as st
from .database import create_message, get_list_data

def show_page():
    st.title("📢 Communication Hub")
    with st.form("comm_form", clear_on_submit=True):
        m_type = st.selectbox("Type", ["Announcement", "To-Do List"])
        target = st.selectbox("Recipient", ["All"] + get_list_data("children")["child_name"].tolist())
        content = st.text_area("Message")
        if st.form_submit_button("Send"):
            create_message(m_type, target, content, st.session_state["username"])
            st.success("Sent!")
