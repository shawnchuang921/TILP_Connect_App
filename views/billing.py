# views/billing.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from .database import ENGINE, get_list_data

# --- DATABASE HELPERS ---
def create_invoice(date, child, item, amount, status, note):
    sql = text("INSERT INTO invoices (date, child_name, item_desc, amount, status, note) VALUES (:d, :c, :i, :a, :s, :n)")
    with ENGINE.connect() as conn:
        conn.execute(sql, {"d": str(date), "c": child, "i": item, "a": amount, "s": status, "n": note})
        conn.commit()

def update_invoice_status(inv_id, new_status):
    with ENGINE.connect() as conn:
        conn.execute(text("UPDATE invoices SET status = :s WHERE id = :id"), {"s": new_status, "id": inv_id})
        conn.commit()

def delete_invoice(inv_id):
    with ENGINE.connect() as conn:
        conn.execute(text("DELETE FROM invoices WHERE id = :id"), {"id": inv_id})
        conn.commit()

# --- MAIN PAGE ---
def show_page():
    st.title("💳 Billing & Invoices")
    role = st.session_state.get('role', '')
    child_link = st.session_state.get('child_link')

    # ADMIN VIEW: Create Invoices
    if role == "admin":
        with st.expander("➕ Generate New Invoice"):
            with st.form("billing_form", clear_on_submit=True):
                c_df = get_list_data("children")
                children = c_df['child_name'].tolist() if not c_df.empty else []
                
                col1, col2 = st.columns(2)
                inv_date = col1.date_input("Invoice Date")
                child = col1.selectbox("Child Name", children)
                item = col2.text_input("Service Description", placeholder="e.g., Speech Therapy - Nov")
                amount = col2.number_input("Amount ($)", min_value=0.0, step=10.0)
                status = st.selectbox("Status", ["Unpaid", "Paid", "Pending", "Overdue"])
                note = st.text_area("Internal Note")
                
                if st.form_submit_button("Create Invoice"):
                    create_invoice(inv_date, child, item, amount, status, note)
                    st.success("Invoice generated successfully.")
                    st.rerun()

    st.divider()

    # VIEWING LOGIC
    with ENGINE.connect() as conn:
        if role == "parent":
            df = pd.read_sql(text("SELECT * FROM invoices WHERE child_name = :c ORDER BY date DESC"), conn, params={"c": child_link})
        else:
            df = pd.read_sql(text("SELECT * FROM invoices ORDER BY date DESC"), conn)

    if not df.empty:
        st.subheader("Transaction History")
        
        # Financial Summary for Admin
        if role == "admin":
            total_unpaid = df[df['status'] != 'Paid']['amount'].sum()
            st.metric("Total Outstanding Balance", f"${total_unpaid:,.2f}")

        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**{row['item_desc']}**")
                c1.caption(f"Date: {row['date']} | Child: {row['child_name']}")
                
                color = "green" if row['status'] == "Paid" else "red"
                c2.markdown(f"### ${row['amount']:.2f}")
                c2.markdown(f":{color}[**Status: {row['status']}**]")
                
                if role == "admin":
                    new_stat = c3.selectbox("Change Status", ["Unpaid", "Paid", "Pending", "Overdue"], key=f"stat_{row['id']}")
                    if c3.button("Update", key=f"upd_{row['id']}"):
                        update_invoice_status(row['id'], new_stat)
                        st.rerun()
                    if c3.button("🗑️", key=f"del_{row['id']}"):
                        delete_invoice(row['id'])
                        st.rerun()
    else:
        st.info("No billing records found.")
