import streamlit as st
from views.database import init_db, get_user
from views import tracker, planner, dashboard, admin_tools, billing, schedule, library, communication

init_db()
st.set_page_config(page_title="TILP Connect", layout="wide", page_icon="🧩")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 TILP Connect Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Log In"):
        user = get_user(u, p)
        if user:
            st.session_state.update({"logged_in": True, "role": user["role"].lower(), "username": user["username"], "child_link": user.get("child_link", "")})
            st.rerun()
        else: st.error("Invalid credentials")
else:
    role = st.session_state["role"]
    pages = {}
    if role == "admin":
        pages = {"🔑 Admin": admin_tools.show_page, "📢 Comms": communication.show_page, "🗓️ Schedule": schedule.show_page, "💳 Billing": billing.show_page, "📂 Library": library.show_page, "📊 Dashboard": dashboard.show_page}
    elif role in ["ot", "slp", "bc", "ece", "assistant", "staff", "therapist"]:
        pages = {"📊 Dashboard": dashboard.show_page, "📝 Tracker": tracker.show_page, "📅 Planner": planner.show_page, "📢 Comms": communication.show_page, "📂 Library": library.show_page}
    elif role == "parent":
        pages = {"📊 My Dashboard": dashboard.show_page, "🗓️ Appts": schedule.show_page, "📂 Files": library.show_page, "💳 Billing": billing.show_page}

    sel = st.sidebar.radio("Navigation", list(pages.keys()))
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    pages[sel]()
