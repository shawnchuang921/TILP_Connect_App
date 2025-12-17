# views/admin_tools.py (FINAL VERSION - Fixed upsert_child arguments)
import streamlit as st
# FIXED: Using relative import (dot) since database.py is in the same folder
from .database import get_list_data, upsert_user, delete_user, upsert_child, delete_child, upsert_list_item, delete_list_item 
import pandas as pd
from datetime import date

def show_page():
    # Only Admin should see this page, checked in app.py
    st.title("🔑 Admin Management Tools")
    st.info("Manage User Accounts, Child Profiles, and Custom List Options.")

    tab1, tab2, tab3 = st.tabs(["👤 User Accounts", "👨‍👩‍👧‍👦 Child Profiles", "📝 Custom Lists"])

    # --- TAB 1: USER ACCOUNTS ---
    with tab1:
        st.header("Staff and Parent Logins")
        df_users = get_list_data("users")
        st.dataframe(df_users, use_container_width=True)

        with st.form("user_form"):
            st.subheader("Add / Edit / Delete User")
            col1, col2 = st.columns(2)
            username = col1.text_input("Username (must be unique)", help="Used as the Login ID")
            password = col2.text_input("Password (Leave blank to keep existing password for edit)", type="password")
            
            col3, col4 = st.columns(2)
            role = col3.selectbox("Role", ["admin", "OT", "SLP", "BC", "ECE", "Assistant", "parent"])
            
            child_link = "All"
            
            # Parent Link logic
            if role == "parent":
                children_df = get_list_data("children")
                # Filter children not currently assigned to a parent or already assigned to this username
                assigned_children = children_df[
                    (children_df["parent_username"] == "None") | 
                    (children_df["parent_username"] == username)
                ]["child_name"].tolist()
                
                # Add the child they are already linked to, if any
                current_link = df_users[df_users['username'] == username]['child_link'].iloc[0] if username in df_users['username'].values and df_users[df_users['username'] == username]['child_link'].iloc[0] != 'All' else 'None'
                
                available_children = ["None"] + sorted(list(set(assigned_children)))

                # If the user is editing an existing parent, ensure their current child is selected by default
                default_index = available_children.index(current_link) if current_link in available_children else 0
                
                child_link = col4.selectbox("Link to Child (for Parents)", available_children, index=default_index)
            else:
                col4.write("Child Link: All (Staff Role)")
            
            col5, col6 = st.columns(2)

            if col5.form_submit_button("💾 Save User Account"):
                if username:
                    # If editing, we try to grab the old user record to keep the password if not provided
                    old_user = df_users[df_users['username'] == username]
                    current_password = old_user['password'].iloc[0] if not old_user.empty else None
                    
                    final_password = password if password else current_password
                    final_child_link = child_link if role == "parent" and child_link != "None" else "All"
                    
                    upsert_user(username, final_password, role, final_child_link)
                    
                    # Update child's parent_username in children table if linked
                    if final_child_link != "All":
                        # FIX 1: Added third argument (Date of Birth) to upsert_child
                        # The Admin tool does not manage DOB here, so we pass a blank string.
                        upsert_child(final_child_link, username, "") 

                    st.success(f"User '{username}' ({role}) saved successfully.")
                    st.rerun()
                else:
                    st.error("Username is required.")
                
            if col6.form_submit_button("🗑️ Delete User"):
                if username and username != st.session_state["username"]: # Prevent deleting logged-in user
                    # Unlink child before deleting user
                    current_link = df_users[df_users['username'] == username]['child_link'].iloc[0] if username in df_users['username'].values else 'All'
                    if current_link != 'All':
                        # FIX 2: Added third argument (Date of Birth) to upsert_child
                        upsert_child(current_link, "None", "") 
                        
                    delete_user(username)
                    st.warning(f"User '{username}' deleted.")
                    st.rerun()
                else:
                    st.error("Cannot delete yourself or username is blank.")

    # --- TAB 2: CHILD PROFILES ---
    with tab2:
        st.header("Client Child Profiles")
        df_children = get_list_data("children")
        st.dataframe(df_children, use_container_width=True)

        with st.form("child_form"):
            st.subheader("Add / Edit / Delete Child Profile")
            col1, col2 = st.columns(2)
            
            child_name = col1.text_input("Child Name (ID)", help="Must be unique.")
            
            existing_dob = df_children[df_children['child_name'] == child_name]['date_of_birth'].iloc[0] if child_name in df_children['child_name'].values else date.today().isoformat()
            dob = col2.date_input("Date of Birth (Optional)", value=pd.to_datetime(existing_dob) if pd.notna(existing_dob) and existing_dob != "" else date.today())
            
            # Get list of users with role 'parent' and ensure they are unassigned
            parent_df = df_users[df_users["role"] == "parent"]
            unassigned_parents = parent_df[parent_df["child_link"].isin(["All", "None"])]["username"].tolist()
            
            # Find current assigned parent
            current_parent = df_children[df_children['child_name'] == child_name]['parent_username'].iloc[0] if child_name in df_children['child_name'].values else 'None'

            # Combine current parent with unassigned parents for the list
            parent_list = ["None/Unassigned"] + sorted(list(set(unassigned_parents + [current_parent])))
            
            default_index = parent_list.index(current_parent) if current_parent in parent_list else 0
            parent_link = st.selectbox("Assign Parent Login ID", parent_list, index=default_index)
            
            col3, col4 = st.columns(2)
            
            if col3.form_submit_button("💾 Save Child Profile"):
                if child_name:
                    final_parent = parent_link if parent_link != "None/Unassigned" else "None"
                    
                    # 1. Update/Insert Child record (This section already calls upsert_child correctly with 3 arguments)
                    upsert_child(child_name, final_parent, dob.isoformat())
                    
                    # 2. Update the newly assigned parent's user record (if one was selected)
                    if final_parent != "None":
                        # We don't change the password here, just the link
                        upsert_user(final_parent, None, "parent", child_name) 
                        st.success(f"Child '{child_name}' saved and linked to parent '{final_parent}'.")
                    else:
                         st.success(f"Child '{child_name}' saved (no parent assigned).")
                    st.rerun()
                else:
                    st.error("Child Name is required.")
                    
            if col4.form_submit_button("🗑️ Delete Child"):
                if child_name:
                    delete_child(child_name)
                    st.warning(f"Child '{child_name}' deleted. Parent link removed.")
                    st.rerun()

    # --- TAB 3: CUSTOM LISTS ---
    with tab3:
        st.header("Manage Goal Areas and Disciplines")
        
        col_list_1, col_list_2 = st.columns(2)
        
        # Discipline Management
        with col_list_1:
            st.subheader("Disciplines")
            df_d = get_list_data("disciplines")
            st.dataframe(df_d, use_container_width=True)
            
            d_name = st.text_input("Discipline Name (Add/Delete)")
            col_d1, col_d2 = st.columns(2)
            
            if col_d1.button("➕ Add Discipline"):
                if d_name:
                    upsert_list_item("disciplines", d_name)
                    st.success(f"Discipline '{d_name}' added.")
                    st.rerun()
            
            if col_d2.button("🗑️ Delete Discipline"):
                if d_name:
                    delete_list_item("disciplines", d_name)
                    st.warning(f"Discipline '{d_name}' deleted.")
                    st.rerun()

        # Goal Area Management
        with col_list_2:
            st.subheader("Goal Areas")
            df_g = get_list_data("goal_areas")
            st.dataframe(df_g, use_container_width=True)
            
            g_name = st.text_input("Goal Area Name (Add/Delete)")
            col_g1, col_g2 = st.columns(2)

            if col_g1.button("➕ Add Goal Area"):
                if g_name:
                    upsert_list_item("goal_areas", g_name)
                    st.success(f"Goal Area '{g_name}' added.")
                    st.rerun()
                    
            if col_g2.button("🗑️ Delete Goal Area"):
                if g_name:
                    delete_list_item("goal_areas", g_name)
                    st.warning(f"Goal Area '{g_name}' deleted.")
                    st.rerun()
