import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text, inspect
from datetime import datetime

@st.cache_resource
def get_engine():
    try:
        user = st.secrets["postgres"]["user"]
        password = st.secrets["postgres"]["password"]
        host = st.secrets["postgres"]["host"]
        port = st.secrets["postgres"]["port"]
        database = st.secrets["postgres"]["database"]
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return create_engine(db_url, pool_pre_ping=True)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

ENGINE = get_engine()

def init_db():
    if not ENGINE: return
    inspector = inspect(ENGINE)
    with ENGINE.connect() as conn:
        conn.execute(text('''CREATE TABLE IF NOT EXISTS progress (
            id SERIAL PRIMARY KEY, date TEXT, child_name TEXT, discipline TEXT, 
            goal_area TEXT, status TEXT, notes TEXT, media_path TEXT, author TEXT,
            parent_note TEXT, parent_feedback TEXT)''')) 

        conn.execute(text('''CREATE TABLE IF NOT EXISTS session_plans (
            id SERIAL PRIMARY KEY, date TEXT, lead_staff TEXT, support_staff TEXT, 
            warm_up TEXT, learning_block TEXT, regulation_break TEXT, social_play TEXT, 
            closing_routine TEXT, materials_needed TEXT, internal_notes TEXT, author TEXT,
            staff_comments TEXT, supervision_notes TEXT)'''))

        conn.execute(text('''CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY, date TEXT, child_name TEXT, status TEXT, 
            logged_by TEXT, UNIQUE (date, child_name))'''))
        
        conn.execute(text("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, child_link TEXT)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS children (id SERIAL PRIMARY KEY, child_name TEXT UNIQUE, parent_username TEXT, date_of_birth TEXT)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS disciplines (name TEXT UNIQUE)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS goal_areas (name TEXT UNIQUE)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS invoices (id SERIAL PRIMARY KEY, date TEXT, child_name TEXT, item_desc TEXT, amount REAL, status TEXT, note TEXT)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS appointments (id SERIAL PRIMARY KEY, date TEXT, time TEXT, child_name TEXT, discipline TEXT, staff TEXT, cost REAL, status TEXT)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, date TEXT, type TEXT, target TEXT, content TEXT, author TEXT, status TEXT)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS library (id SERIAL PRIMARY KEY, child_name TEXT, title TEXT, link_url TEXT, category TEXT, added_by TEXT, date_added TEXT)"))
        
        conn.commit()
        
        # Migrations for existing DBs
        p_cols = [c['name'] for c in inspector.get_columns('progress')]
        if 'parent_note' not in p_cols:
            conn.execute(text("ALTER TABLE progress ADD COLUMN parent_note TEXT"))
            conn.execute(text("ALTER TABLE progress ADD COLUMN parent_feedback TEXT"))
            
        s_cols = [c['name'] for c in inspector.get_columns('session_plans')]
        if 'staff_comments' not in s_cols:
            conn.execute(text("ALTER TABLE session_plans ADD COLUMN staff_comments TEXT"))
            conn.execute(text("ALTER TABLE session_plans ADD COLUMN supervision_notes TEXT"))
        conn.commit()

def get_user(username, password):
    if not ENGINE: return None
    sql = text("SELECT * FROM users WHERE username = :user AND password = :pass")
    with ENGINE.connect() as conn:
        df = pd.read_sql(sql, conn, params={"user":username, "pass":password})
    return df.iloc[0].to_dict() if not df.empty else None

def get_data(table):
    if not ENGINE: return pd.DataFrame()
    with ENGINE.connect() as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)

def get_list_data(table):
    if not ENGINE: return pd.DataFrame()
    with ENGINE.connect() as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)

def save_progress(date, child, discipline, goal, status, notes, media, author, p_note):
    sql = text("""INSERT INTO progress (date, child_name, discipline, goal_area, status, notes, media_path, author, parent_note) 
                  VALUES (:d, :c, :dis, :g, :s, :n, :m, :a, :pn)""")
    with ENGINE.connect() as conn:
        conn.execute(sql, {"d":date, "c":child, "dis":discipline, "g":goal, "s":status, "n":notes, "m":media, "a":author, "pn":p_note})
        conn.commit()

def update_parent_feedback(pid, feedback):
    with ENGINE.connect() as conn:
        conn.execute(text("UPDATE progress SET parent_feedback = :f WHERE id = :id"), {"f":feedback, "id":pid})
        conn.commit()

def save_plan(date, lead, support, wu, lb, rb, sp, cr, mn, notes, author):
    sql = text("""INSERT INTO session_plans (date, lead_staff, support_staff, warm_up, learning_block, 
                  regulation_break, social_play, closing_routine, materials_needed, internal_notes, author, staff_comments, supervision_notes) 
                  VALUES (:d, :ls, :ss, :wu, :lb, :rb, :sp, :cr, :mn, :in, :a, '', '')""")
    with ENGINE.connect() as conn:
        conn.execute(sql, {"d":date, "ls":lead, "ss":support, "wu":wu, "lb":lb, "rb":rb, "sp":sp, "cr":cr, "mn":mn, "in":notes, "a":author})
        conn.commit()

def update_plan_extras(pid, comments, supervision):
    with ENGINE.connect() as conn:
        if comments:
            conn.execute(text("UPDATE session_plans SET staff_comments = COALESCE(staff_comments, '') || :c WHERE id = :id"), {"c": comments, "id": pid})
        if supervision:
            conn.execute(text("UPDATE session_plans SET supervision_notes = :s WHERE id = :id"), {"s": supervision, "id": pid})
        conn.commit()

def create_message(m_type, target, content, author):
    sql = text("INSERT INTO messages (date, type, target, content, author, status) VALUES (:d, :t, :tg, :c, :a, 'Active')")
    with ENGINE.connect() as conn:
        conn.execute(sql, {"d":str(datetime.now().date()), "t":m_type, "tg":target, "c":content, "a":author})
        conn.commit()

def get_messages(child_name):
    with ENGINE.connect() as conn:
        return pd.read_sql_query(text("SELECT * FROM messages WHERE (target = :c OR target = 'All') AND status='Active' ORDER BY id DESC"), conn, params={"c":child_name})

def add_library_link(child, title, url, cat, user):
    sql = text("INSERT INTO library (child_name, title, link_url, category, added_by, date_added) VALUES (:c, :t, :u, :cat, :a, :d)")
    with ENGINE.connect() as conn:
        conn.execute(sql, {"c":child, "t":title, "u":url, "cat":cat, "a":user, "d":str(datetime.now().date())})
        conn.commit()

def get_library(child_name):
    with ENGINE.connect() as conn:
        return pd.read_sql_query(text("SELECT * FROM library WHERE child_name = :c OR child_name = 'All'"), conn, params={"c":child_name})

def get_attendance_data(child_name=None):
    query = "SELECT * FROM attendance"
    params = {}
    if child_name:
        query += " WHERE child_name = :cn"
        params["cn"] = child_name
    query += " ORDER BY date DESC"
    with ENGINE.connect() as conn:
        return pd.read_sql_query(text(query), conn, params=params)
