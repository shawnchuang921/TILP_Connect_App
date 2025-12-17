# views/dashboard.py (BULLETPROOF VERSION - Handles case sensitivity)
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from .database import get_list_data, get_data, upsert_attendance, get_attendance_data, delete_attendance

def render_attendance_overview(is_ece=False):
    """Component to show attendance with optional ECE controls."""
    st.subheader("🗓️ Attendance Overview")
    
    col_start, col_end = st.columns(2)
    start_date = col_start.date_input("Filter Start Date", value=datetime.now().date() - timedelta(days=7), key="filter_start")
    end_date = col_end.date_input("Filter End Date", value=datetime.now().date(), key="filter_end")
    
    all_att = get_attendance_data()
    if not all_att.empty:
        all_att['date'] = pd.to_datetime(all_att['date'])
        filtered_df = all_att[
            (all_att['date'].dt.date >= start_date) & 
            (all_att['date'].dt.date <= end_date)
        ].sort_values(by=['date', 'child_name'], ascending=[False, True])

        if filtered_df.empty:
            st.info("No records found for this range.")
        else:
            if not is_ece:
                display_df = filtered_df[['date', 'child_name', 'status', 'logged_by']].copy()
                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                for _, row in filtered_df.iterrows():
                    rec_id = row['id']
                    date_str = row['date'].strftime('%Y-%m-%d')
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{date_str}** | {row['child_name']} : `{row['status']}`")
                    with c2:
                        col_e, col_d = st.columns(2)
                        if col_e.button("✏️", key=f"ed_{rec_id}"):
                            st.session_state.edit_attendance_data = row.to_dict()
                            st.rerun()
                        if col_d.button("🗑️", key=f"del_{rec_id}"):
                            delete_attendance(rec_id)
                            st.rerun()
                    st.divider()

def show_ece_logging_tool():
    """Form for ECE logging with robust date handling."""
    st.subheader("📝 Daily Attendance Logging (ECE Only)")
    logged_by = st.session_state.get('username', 'Unknown')
    is_edit = 'edit_attendance_data' in st.session_state and st.session_state.edit_attendance_data is not None
    edit_data = st.session_state.get('edit_attendance_data', {})

    if is_edit:
        raw_date = edit_data['date']
        if isinstance(raw_date, str):
            default_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
        elif hasattr(raw_date, 'date'):
            default_date = raw_date.date()
        else:
            default_date = raw_date
    else:
        default_date = datetime.now().date()

    current_date = st.date_input("Log Date", value=default_date)
    children_df = get_list_data("children")
    children_list = children_df['child_name'].tolist() if not children_df.empty else []

    with st.form("ece_logging_form"):
        attendance_options = ["Present", "Absent", "Late", "Cancelled"]
        records = {}
        target_children = [edit_data['child_name']] if is_edit else children_list
        for name in target_children:
            idx = 0
            if is_edit and edit_data['status'] in attendance_options:
                idx = attendance_options.index(edit_data['status'])
            records[name] = st.selectbox(f"Status for {name}", attendance_options, index=idx)

        if st.form_submit_button("Save Changes" if is_edit else "Save Attendance", type="primary"):
            for name, status in records.items():
                upsert_attendance(current_date.strftime('%Y-%m-%d'), name, status, logged_by)
            st.session_state.edit_attendance_data = None
            st.rerun()
    
    if is_edit and st.button("Cancel"):
        st.session_state.edit_attendance_data = None
        st.rerun()

def show_staff_dashboard(role):
    """Unified Dashboard for all clinical staff."""
    st.title(f"📊 {role.upper()} Dashboard")
    tab1, tab2, tab3 = st.tabs(["📋 Progress Notes", "🗓️ Attendance", "📅 Session Plans"])
    
    with tab1:
        st.header("Recent Clinical Progress")
        df_prog = get_data("progress")
        if not df_prog.empty:
            st.dataframe(df_prog[['date', 'child_name', 'discipline', 'status', 'notes', 'author']].sort_values(by='date', ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No progress notes yet.")

    with tab2:
        if role.lower() == 'ece':
            show_ece_logging_tool()
            st.divider()
        render_attendance_overview(is_ece=(role.lower() == 'ece'))

    with tab3:
        st.header("Daily Session Plans")
        df_plans = get_data("session_plans")
        if not df_plans.empty:
            st.dataframe(df_plans.sort_values(by='date', ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No session plans found.")

def show_parent_dashboard(child_name):
    st.title(f"👋 Parent Dashboard: {child_name}")
    att = get_attendance_data(child_name=child_name)
    if not att.empty:
        st.metric("Latest Status", att.iloc[0]['status'], delta=att.iloc[0]['date'])
    st.divider()
    prog = get_data("progress")
    if not prog.empty:
        child_prog = prog[prog['child_name'] == child_name]
        st.dataframe(child_prog[['date', 'discipline', 'status', 'notes']].sort_values(by='date', ascending=False), use_container_width=True, hide_index=True)

def show_page():
    if not st.session_state.get('logged_in', False):
        st.error("Please log in.")
        return
        
    # Standardize role for comparison
    role = str(st.session_state.get('role', '')).lower().strip()
    
    if role == 'parent':
        show_parent_dashboard(st.session_state.get('child_link', ''))
    else:
        # This will now catch "Admin", "admin", "ECE", "ece", etc.
        show_staff_dashboard(st.session_state.get('role', 'staff'))
