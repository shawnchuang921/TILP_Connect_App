import streamlit as st
from .database import add_library_link, get_library, get_list_data

def show_page():
    st.title("📂 Library")
    role = st.session_state["role"]
    child = st.session_state["child_link"]
    
    if role != "parent":
        with st.form("lib_form", clear_on_submit=True):
            target = st.selectbox("Target", ["All"] + get_list_data("children")["child_name"].tolist())
            t = st.text_input("Title")
            u = st.text_input("URL")
            cat = st.selectbox("Category", ["Homework", "Reports", "Videos"])
            if st.form_submit_button("Add"):
                add_library_link(target, t, u, cat, st.session_state["username"])
                st.rerun()

    df = get_library(child if role == "parent" else "All")
    for cat in df['category'].unique():
        st.subheader(cat)
        for _, r in df[df['category'] == cat].iterrows():
            st.markdown(f"🔗 [{r['title']}]({r['link_url']})")
