import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------- DATABASE ----------------
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables
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

# ---------------- UI ----------------
st.set_page_config(page_title="Smart Infrastructure Management", layout="wide")
st.title("🏗️ Smart Infrastructure & Asset Management System")

menu = ["Dashboard", "Add Asset", "View Assets", "Maintenance"]
choice = st.sidebar.selectbox("Menu", menu)

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

        st.subheader("Category Distribution")
        fig, ax = plt.subplots()
        df["category"].value_counts().plot(kind="bar", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("No data available")

# ---------------- ADD ASSET ----------------
elif choice == "Add Asset":
    st.subheader("➕ Add New Asset")

    name = st.text_input("Asset Name")
    category = st.selectbox("Category", ["IT", "Electrical", "Furniture"])
    quantity = st.number_input("Quantity", min_value=1)
    status = st.selectbox("Status", ["Working", "Not Working"])
    location = st.text_input("Location")

    if st.button("Add Asset"):
        cursor.execute("""
        INSERT INTO assets (name, category, quantity, status, location, date_added)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, quantity, status, location, str(datetime.now())))
        conn.commit()
        st.success("Asset Added Successfully!")

# ---------------- VIEW ASSETS ----------------
elif choice == "View Assets":
    st.subheader("📋 Asset List")

    df = pd.read_sql("SELECT * FROM assets", conn)

    if not df.empty:
        for i, row in df.iterrows():
            if row["quantity"] < 2:
                st.warning(f"Low Stock: {row['name']}")

        st.dataframe(df)

        st.subheader("✏️ Update Asset")
        id_update = st.number_input("Enter Asset ID to Update", min_value=1)

        new_status = st.selectbox("New Status", ["Working", "Not Working"])
        new_quantity = st.number_input("New Quantity", min_value=0)

        if st.button("Update"):
            cursor.execute("""
            UPDATE assets SET status=?, quantity=? WHERE id=?
            """, (new_status, new_quantity, id_update))
            conn.commit()
            st.success("Updated Successfully!")

        st.subheader("🗑️ Delete Asset")
        id_delete = st.number_input("Enter Asset ID to Delete", min_value=1)

        if st.button("Delete"):
            cursor.execute("DELETE FROM assets WHERE id=?", (id_delete,))
            conn.commit()
            st.success("Deleted Successfully!")

    else:
        st.warning("No assets found")

# ---------------- MAINTENANCE ----------------
elif choice == "Maintenance":
    st.subheader("🛠️ Maintenance")

    df = pd.read_sql("SELECT * FROM assets", conn)

    if not df.empty:
        asset_ids = df["id"].tolist()

        asset_id = st.selectbox("Select Asset ID", asset_ids)
        issue = st.text_input("Issue Description")

        if st.button("Report Issue"):
            cursor.execute("""
            INSERT INTO maintenance (asset_id, issue, status, date_reported)
            VALUES (?, ?, ?, ?)
            """, (asset_id, issue, "Pending", str(datetime.now())))
            conn.commit()
            st.success("Issue Reported!")

        st.subheader("📋 Maintenance Records")
        mdf = pd.read_sql("SELECT * FROM maintenance", conn)
        st.dataframe(mdf)

        update_id = st.number_input("Enter Maintenance ID", min_value=1)
        new_status = st.selectbox("Update Status", ["Pending", "Completed"])

        if st.button("Update Maintenance"):
            cursor.execute("""
            UPDATE maintenance SET status=? WHERE id=?
            """, (new_status, update_id))
            conn.commit()
            st.success("Maintenance Updated!")

    else:
        st.warning("Add assets first!")
