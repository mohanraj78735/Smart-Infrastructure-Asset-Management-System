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

# ---------------- EMAIL FUNCTION ----------------
def send_email(message):
    try:
        sender = "your_email@gmail.com"
        password = "your_app_password"
        receiver = "receiver_email@gmail.com"

        msg = MIMEText(message)
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

# ---------------- LOGIN SYSTEM ----------------
users = {
    "admin": {"password": "123", "role": "admin"},
    "hod": {"password": "123", "role": "hod"},
    "principal": {"password": "123", "role": "principal"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = users[username]["role"]
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# ---------------- ROLE ----------------
role = st.session_state.role

# ---------------- MENU ----------------
if role == "admin":
    menu = ["Dashboard", "Add Asset", "View Assets", "Maintenance"]
elif role == "hod":
    menu = ["Dashboard", "View Assets", "Maintenance"]
else:
    menu = ["Dashboard"]

choice = st.sidebar.selectbox("Menu", menu)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.title("💻 IT Lab Stock Management System")

# ---------------- DASHBOARD ----------------
if choice == "Dashboard":
    st.subheader("📊 Dashboard")

    df = pd.read_sql("SELECT * FROM assets", conn)

    if not df.empty:
        total = len(df)
        working = len(df[df["status"] == "Working"])
        not_working = len(df[df["status"] == "Not Working"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Assets", total)
        col2.metric("Working", working)
        col3.metric("Not Working", not_working)

        # BLINK ALERT
        st.markdown("""
        <style>
        @keyframes blink {50% {opacity: 0;}}
        .blink {color:red; animation: blink 1s infinite;}
        </style>
        """, unsafe_allow_html=True)

        for i, row in df.iterrows():
            if row["quantity"] < 2:
                st.markdown(f"<p class='blink'>⚠️ Low Stock: {row['name']}</p>", unsafe_allow_html=True)
                send_email(f"Low Stock Alert: {row['name']}")

        fig, ax = plt.subplots()
        df["category"].value_counts().plot(kind="bar", ax=ax)
        st.pyplot(fig)

    else:
        st.warning("No Data")

# ---------------- ADD ASSET ----------------
elif choice == "Add Asset" and role == "admin":
    st.subheader("➕ Add Asset")

    name = st.text_input("Name")
    category = st.selectbox("Category", ["IT", "Electrical", "Furniture"])
    quantity = st.number_input("Quantity", min_value=1)
    status = st.selectbox("Status", ["Working", "Not Working"])
    location = st.text_input("Location")

    if st.button("Add"):
        cursor.execute("""
        INSERT INTO assets (name, category, quantity, status, location, date_added)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, quantity, status, location, str(datetime.now())))
        conn.commit()
        st.success("Added Successfully")

# ---------------- VIEW ASSETS ----------------
elif choice == "View Assets":
    st.subheader("📋 Assets")

    df = pd.read_sql("SELECT * FROM assets", conn)

    if not df.empty:
        st.dataframe(df)

        if role == "admin":
            st.subheader("✏️ Update")
            id_update = st.number_input("ID", min_value=1)
            new_status = st.selectbox("Status", ["Working", "Not Working"])
            new_qty = st.number_input("Quantity", min_value=0)

            if st.button("Update"):
                cursor.execute("UPDATE assets SET status=?, quantity=? WHERE id=?",
                               (new_status, new_qty, id_update))
                conn.commit()
                st.success("Updated")

            st.subheader("🗑️ Delete")
            id_del = st.number_input("Delete ID", min_value=1)

            if st.button("Delete"):
                cursor.execute("DELETE FROM assets WHERE id=?", (id_del,))
                conn.commit()
                st.success("Deleted")

# ---------------- MAINTENANCE ----------------
elif choice == "Maintenance":
    st.subheader("🛠️ Maintenance")

    df = pd.read_sql("SELECT * FROM assets", conn)

    if not df.empty:
        asset_ids = df["id"].tolist()

        if role == "hod":
            st.subheader("📢 Raise Complaint")
            asset_id = st.selectbox("Asset ID", asset_ids)
            issue = st.text_input("Issue")

            if st.button("Submit"):
                cursor.execute("""
                INSERT INTO maintenance (asset_id, issue, status, date_reported)
                VALUES (?, ?, ?, ?)
                """, (asset_id, issue, "Pending", str(datetime.now())))
                conn.commit()
                send_email(f"Complaint for Asset {asset_id}: {issue}")
                st.success("Complaint Sent")

        st.subheader("📋 Records")
        mdf = pd.read_sql("SELECT * FROM maintenance", conn)
        st.dataframe(mdf)

        if role == "admin":
            mid = st.number_input("Maintenance ID", min_value=1)
            new_status = st.selectbox("Update Status", ["Pending", "Completed"])

            if st.button("Update Status"):
                cursor.execute("UPDATE maintenance SET status=? WHERE id=?",
                               (new_status, mid))
                conn.commit()
                st.success("Updated")
