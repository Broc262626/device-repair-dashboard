
import streamlit as st
import pandas as pd
import bcrypt
import altair as alt
import os
import json

st.set_page_config(page_title="Device Repair Dashboard", layout="wide")

DATA_FILE = "repairs.csv"
USER_FILE = "users.json"

def load_repairs():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            "Server",
            "Parent Fleet",
            "Fleet Number",
            "Issue",
            "Priority",
            "Tech Support Comment",
            "Status"
        ])
        df.to_csv(DATA_FILE, index=False)
    return pd.read_csv(DATA_FILE)

def save_repairs(df):
    df.to_csv(DATA_FILE, index=False)

def load_users():
    if not os.path.exists(USER_FILE):
        admin_pw = bcrypt.hashpw("admin".encode(), bcrypt.gensalt()).decode()
        with open(USER_FILE, "w") as f:
            json.dump({"admin": {"password": admin_pw, "role": "admin"}}, f, indent=4)
    with open(USER_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Log In", use_container_width=True):
        if username in users and bcrypt.checkpw(password.encode(), users[username]["password"].encode()):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

role = users[st.session_state.user]["role"]
df = load_repairs()

st.sidebar.title("Navigation")
menu = ["Dashboard", "Manage Devices"]
if role == "admin":
    menu.append("Admin Panel")

page = st.sidebar.radio("Go to:", menu)

def priority_color(val):
    colors = {
        "1": "background-color: #ff4d4d; color: white;",
        "2": "background-color: #ffa64d; color: black;",
        "3": "background-color: #4dff88; color: black;"
    }
    return colors.get(str(val), "")

if page == "Dashboard":
    st.title("📊 Analytics Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Status Distribution")
        if len(df) > 0:
            chart = alt.Chart(df).mark_arc().encode(
                theta="count()",
                color="Status"
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No data yet.")

    with col2:
        st.subheader("Parent Fleet Distribution")
        if len(df) > 0:
            chart2 = alt.Chart(df).mark_arc().encode(
                theta="count()",
                color="Parent Fleet"
            )
            st.altair_chart(chart2, use_container_width=True)
        else:
            st.info("No data yet.")

elif page == "Manage Devices":
    st.title("🛠 Manage Devices")

    st.subheader("Add New Device")
    with st.form("add_device"):
        a = st.text_input("Server")
        b = st.text_input("Parent Fleet")
        c = st.text_input("Fleet Number")
        d = st.text_area("Issue")
        e = st.selectbox("Priority", ["1","2","3"])
        f = st.text_area("Tech Support Comment")
        g = st.selectbox("Status", ["New", "Incomplete", "Waiting Materials", "Complete"])

        if st.form_submit_button("Add Device"):
            df.loc[len(df)] = [a,b,c,d,e,f,g]
            save_repairs(df)
            st.success("Added successfully.")
            st.rerun()

    st.subheader("All Devices")
    if len(df) > 0:
        st.dataframe(df.style.applymap(priority_color, subset=["Priority"]), use_container_width=True)
    else:
        st.info("No devices yet.")

    if role == "admin" and len(df) > 0:
        st.subheader("Delete Device")
        delete_row = st.number_input("Row number", min_value=0, max_value=len(df)-1, step=1)
        if st.button("Delete Selected Row", type="primary"):
            df = df.drop(delete_row).reset_index(drop=True)
            save_repairs(df)
            st.success("Deleted.")
            st.rerun()

elif page == "Admin Panel" and role == "admin":
    st.title("🔧 Admin Panel – User Management")

    st.subheader("Create New User")
    with st.form("create_user"):
        new_user = st.text_input("New Username")
        new_pw = st.text_input("New Password", type="password")
        new_role = st.selectbox("Role", ["admin","readonly"])
        create = st.form_submit_button("Create User")

        if create:
            hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
            users[new_user] = {"password": hashed, "role": new_role}
            save_users(users)
            st.success("User created.")
            st.rerun()

    st.subheader("Existing Users")
    st.write(users)

    del_user = st.text_input("Delete Username")
    if st.button("Delete User"):
        if del_user in users:
            del users[del_user]
            save_users(users)
            st.success("User deleted.")
            st.rerun()
        else:
            st.error("User not found.")
