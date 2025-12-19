# views/admin_tools.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from .database import (
    ENGINE, 
    get_list_data, 
    get_data
)

# --- DATABASE HELPER FUNCTIONS (Specific to Admin) ---
def upsert_user(username, password, role, child_link):
    with ENGINE.connect() as conn:
        result = conn.execute(text("SELECT username FROM users WHERE username = :u"), {"u": username}).fetchone()
        if result:
            if password:
                sql = text("UPDATE users SET password=:p, role=:r, child_link=:c WHERE username=:u")
                conn.execute(sql, {"u": username, "p": password, "r": role, "c": child_link})
            else:
                sql = text("UPDATE users SET role=:r, child_link=:c WHERE username=:u")
                conn.execute(sql, {"u": username, "r": role, "c": child_link})
        else:
            conn.execute(text("INSERT INTO users (username, password, role, child_link) VALUES (:u, :p, :r, :c)"), 
                         {"u": username, "p": password, "r": role, "c": child_link})
        conn.commit()

def delete_user(username):
    with ENGINE.connect() as conn:
        conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": username})
        conn.commit()

def upsert_child(cn, pu, dob):
    with ENGINE.connect() as conn:
        conn.execute(text("""
            INSERT INTO children (child_name, parent_username, date_of_birth) 
            VALUES (:cn, :pu, :dob) 
            ON CONFLICT (child_name) 
            DO UPDATE SET parent_username=EXCLUDED.parent_username, date_of_birth=EXCLUDED.date_of_birth
        """), {"cn": cn, "pu": pu, "dob": dob})
        conn.commit()

def delete_child(cn):
    with ENGINE.connect() as conn:
        conn.execute(text("DELETE FROM children WHERE child_name = :cn"), {"cn": cn})
        conn.commit()

def upsert_list_item(table, item):
    with ENGINE.connect() as conn:
        conn.execute(text(f"INSERT INTO {table} (name) VALUES (:n) ON CONFLICT (name) DO NOTHING"), {"n": item})
        conn.commit()

def delete_list_item(table, item):
    with ENGINE.connect() as conn:
        conn.execute(text(f"DELETE FROM {table} WHERE name = :n"), {"n": item})
        conn.commit()

# --- MAIN PAGE VIEW ---
def show_page():
    st.title("🔑 Admin Control Panel")
    
    tab1, tab2, tab3 = st.tabs(["👤 User Management", "👶 Child Profiles", "⚙️ App Lists"])

    # --- TAB 1: USER MANAGEMENT ---
    with tab1:
        st.subheader("Manage Users & Permissions")
        
        with st.expander("➕ Add / Update User"):
            with st.form("user_form", clear_on_submit=True):
                u = st.text_input("Username")
                p = st.text_input("Password (leave blank to keep current if updating)")
                r = st.selectbox("Role", ["admin", "ot", "slp", "bc", "ece", "assistant", "staff", "parent"])
                
                # Fetch children for parent linking
                c_df = get_list_data("children")
                c_list = ["None"] + (c_df['child_name'].tolist() if not c_df.empty else [])
                cl = st.selectbox("Link to Child (Parents only)", c_list)
                
                if st.form_submit_button("Save User"):
                    if u:
                        link_val = cl if cl != "None" else ""
                        upsert_user(u, p, r, link_val)
                        st.success(f"User {u} saved!")
                        st.rerun()

        # Display Users Table
        users_df = get_data("users")
        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True)
            user_to_del = st.selectbox("Select User to Remove", users_df['username'].tolist())
            if st.button("Delete Selected User"):
                delete_user(user_to_del)
                st.rerun()

    # --- TAB 2: CHILD PROFILES ---
    with tab2:
        st.subheader("Child Directory")
        with st.form("child_form", clear_on_submit=True):
            cn = st.text_input("Child Name")
            pu = st.text_input("Parent Username (must match a User)")
            dob = st.text_input("Date of Birth (YYYY-MM-DD)")
            if st.form_submit_button("Add/Update Child"):
                upsert_child(cn, pu, dob)
                st.success("Child profile updated.")
                st.rerun()
        
        children_df = get_list_data("children")
        if not children_df.empty:
            st.dataframe(children_df, use_container_width=True)
            c_del = st.selectbox("Remove Child Profile", children_df['child_name'].tolist())
            if st.button("Delete Child Profile"):
                delete_child(c_del)
                st.rerun()

    # --- TAB 3: APP LISTS (Disciplines/Goal Areas) ---
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Disciplines")
            new_disc = st.text_input("Add Discipline (e.g., Physiotherapy)")
            if st.button("Add Discipline"):
                upsert_list_item("disciplines", new_disc)
                st.rerun()
            
            d_df = get_list_data("disciplines")
            if not d_df.empty:
                d_sel = st.selectbox("Remove Discipline", d_df['name'].tolist())
                if st.button("Delete Discipline"):
                    delete_list_item("disciplines", d_sel)
                    st.rerun()

        with col2:
            st.subheader("Goal Areas")
            new_goal = st.text_input("Add Goal Area (e.g., Fine Motor)")
            if st.button("Add Goal Area"):
                upsert_list_item("goal_areas", new_goal)
                st.rerun()
                
            g_df = get_list_data("goal_areas")
            if not g_df.empty:
                g_sel = st.selectbox("Remove Goal Area", g_df['name'].tolist())
                if st.button("Delete Goal Area"):
                    delete_list_item("goal_areas", g_sel)
                    st.rerun()
