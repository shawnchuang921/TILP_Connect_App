# app.py (Standardized Version)
import streamlit as st
from views.database import init_db, get_user
from views import tracker, planner, dashboard, admin_tools 

# Initialize Database
init_db()

# Page Configuration
st.set_page_config(page_title="TILP Connect", layout="wide", page_icon="🧩")

# --- DATABASE AUTHENTICATION ---
def login_screen():
    st.title("🔐 TILP Connect Login")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Log In"):
            user_data = get_user(username, password)
            
            if user_data:
                st.session_state["logged_in"] = True
                # Standardizing keys to ensure dashboard.py can find them
                st.session_state["role"] = str(user_data["role"])
                st.session_state["username"] = user_data["username"]
                st.session_state["child_link"] = user_data.get("child_link", "")
                st.success(f"Welcome, {user_data['username']}!")
                st.rerun()
            else:
                st.error("Incorrect username or password")

def main():
    # Check Login Status
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_screen()
        return

    # --- SIDEBAR NAVIGATION ---
    # Retrieve role and force to lowercase for reliable comparison
    user_role = str(st.session_state.get("role", "")).lower()
    username = st.session_state.get("username", "User")
    
    st.sidebar.title(f"👤 {username.capitalize()}")
    st.sidebar.markdown(f"**Role:** {user_role.upper()}")
    
    # Define available pages based on Role
    pages = {}
    
    # 1. Admin Tools (Admin Only)
    if user_role == "admin":
        pages["🔑 Admin Tools"] = admin_tools.show_page
    
    # 2. Staff Tools (Admin + All Therapist/Staff roles)
    # We use a lowercase list to match our lowercase user_role
    staff_roles = ["admin", "ot", "slp", "bc", "ece", "assistant", "staff", "therapist"]
    if user_role in staff_roles:
        pages["📝 Progress Tracker"] = tracker.show_page
        pages["📅 Daily Planner"] = planner.show_page
    
    # 3. Dashboard (Available to everyone, but view changes inside dashboard.py)
    if user_role == "parent":
        child_name = st.session_state.get("child_link", "My Child")
        pages[f"📊 My Child's Dashboard"] = dashboard.show_page
    else:
        pages["📊 Dashboard & Reports"] = dashboard.show_page

    # Sidebar selection
    selection = st.sidebar.radio("Go to:", list(pages.keys()))
    
    st.sidebar.divider()
    if st.sidebar.button("Log Out"):
        st.session_state.clear()
        st.rerun()

    # Display Selected Page
    try:
        pages[selection]()
    except Exception as e:
        st.error(f"Error loading page: {e}")

if __name__ == "__main__":
    main()
