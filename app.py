import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# ---------------- DATABASE ----------------
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# Tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT,
    quantity INTEGER,
    status TEXT,
    location TEXT,
    date_added TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER,
    issue TEXT,
    status TEXT,
    date_reported TEXT
)
""")

conn.commit()

# ---------------- SAMPLE DATA (RUN ONCE) ----------------
def insert_sample_data():
    cursor.execute("SELECT COUNT(*) FROM assets")
    if cursor.fetchone()[0] == 0:
        data = [
            ("Desktop Computer","IT",15,"Working","Lab 1"),
            ("Keyboard","IT",2,"Working","Lab 1"),
            ("Mouse","IT",1,"Working","Lab 2"),
            ("Monitor","IT",8,"Working","Lab 1"),
            ("Printer","IT",1,"Not Working","Lab 1"),
            ("Scanner","IT",3,"Working","Lab 2"),
            ("UPS","IT",4,"Working","Lab 1"),
            ("Ceiling Fan","Electrical",6,"Working","Lab 1"),
            ("LED Light","Electrical",1,"Working","Lab 2"),
            ("Air Conditioner","Electrical",2,"Working","Lab 1"),
            ("Chair","Furniture",25,"Working","Lab 1"),
            ("Table","Furniture",12,"Working","Lab 2"),
            ("Projector Table","Furniture",1,"Working","Lab 1")
        ]
        for d in data:
            cursor.execute("""
            INSERT INTO assets (name, category, quantity, status, location, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (d[0], d[1], d[2], d[3], d[4], str(datetime.now())))
        conn.commit()

insert_sample_data()

# ---------------- EMAIL ----------------
def send_email(msg_text):
    try:
        sender = "your_email@gmail.com"
        password = "your_app_password"
        receiver = "receiver@gmail.com"

        msg = MIMEText(msg_text)
        msg['Subject'] = "Lab Alert 🚨"
        msg['From'] = sender
        msg['To'] = receiver

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except:
        pass

# ---------------- LOGIN ----------------
users = {
    "admin": {"password": "123", "role": "admin"},
    "hod": {"password": "123", "role": "hod"},
    "principal": {"password": "123", "role": "principal"}
}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == p:
            st.session_state.login = True
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

role = st.session_state.role

# ---------------- MENU ----------------
if role == "admin":
    menu = ["Dashboard","Add Asset","View Assets","Maintenance"]
elif role == "hod":
    menu = ["Dashboard","View Assets","Maintenance"]
else:
    menu = ["Dashboard"]

choice = st.sidebar.selectbox("Menu", menu)

if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

st.title("💻 IT Lab Stock Management")

# ---------------- DASHBOARD ----------------
if choice == "Dashboard":
    df = pd.read_sql("SELECT * FROM assets", conn)

    if not df.empty:
        st.subheader("📊 Dashboard")

        col1,col2,col3 = st.columns(3)
        col1.metric("Total", len(df))
        col2.metric("Working", len(df[df["status"]=="Working"]))
        col3.metric("Not Working", len(df[df["status"]=="Not Working"]))

        # Blink CSS
        st.markdown("""
        <style>
        @keyframes blink {50% {opacity:0;}}
        .blink {color:red; animation: blink 1s infinite;}
        </style>
        """, unsafe_allow_html=True)

        for _,row in df.iterrows():
            if row["quantity"] < 2:
                st.markdown(f"<p class='blink'>⚠️ Low Stock: {row['name']}</p>", unsafe_allow_html=True)
                send_email(f"Low Stock Alert: {row['name']}")

        fig,ax = plt.subplots()
        df["category"].value_counts().plot(kind="bar", ax=ax)
        st.pyplot(fig)

# ---------------- ADD ----------------
elif choice == "Add Asset" and role=="admin":
    st.subheader("➕ Add Asset")
    name = st.text_input("Name")
    cat = st.selectbox("Category",["IT","Electrical","Furniture"])
    qty = st.number_input("Quantity",1)
    status = st.selectbox("Status",["Working","Not Working"])
    loc = st.text_input("Location")

    if st.button("Add"):
        cursor.execute("""
        INSERT INTO assets (name,category,quantity,status,location,date_added)
        VALUES (?,?,?,?,?,?)
        """,(name,cat,qty,status,loc,str(datetime.now())))
        conn.commit()
        st.success("Added")

# ---------------- VIEW ----------------
elif choice == "View Assets":
    df = pd.read_sql("SELECT * FROM assets", conn)
    st.dataframe(df)

    if role=="admin":
        st.subheader("Update")
        i = st.number_input("ID",1)
        ns = st.selectbox("Status",["Working","Not Working"])
        nq = st.number_input("Qty",0)

        if st.button("Update"):
            cursor.execute("UPDATE assets SET status=?,quantity=? WHERE id=?",(ns,nq,i))
            conn.commit()
            st.success("Updated")

        st.subheader("Delete")
        d = st.number_input("Delete ID",1)

        if st.button("Delete"):
            cursor.execute("DELETE FROM assets WHERE id=?",(d,))
            conn.commit()
            st.success("Deleted")

# ---------------- MAINTENANCE ----------------
elif choice == "Maintenance":
    df = pd.read_sql("SELECT * FROM assets", conn)

    if role=="hod":
        st.subheader("📢 Complaint")
        aid = st.selectbox("Asset ID", df["id"])
        issue = st.text_input("Issue")

        if st.button("Submit"):
            cursor.execute("""
            INSERT INTO maintenance (asset_id,issue,status,date_reported)
            VALUES (?,?,?,?)
            """,(aid,issue,"Pending",str(datetime.now())))
            conn.commit()
            send_email(f"Complaint for Asset {aid}: {issue}")
            st.success("Sent")

    st.subheader("📋 Records")
    mdf = pd.read_sql("SELECT * FROM maintenance", conn)
    st.dataframe(mdf)

    if role=="admin":
        mid = st.number_input("Maintenance ID",1)
        stat = st.selectbox("Status",["Pending","Completed"])

        if st.button("Update"):
            cursor.execute("UPDATE maintenance SET status=? WHERE id=?",(stat,mid))
            conn.commit()
            st.success("Updated")
