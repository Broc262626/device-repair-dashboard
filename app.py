
import streamlit as st
import pandas as pd
import json, hashlib, time
from datetime import datetime

st.set_page_config(page_title="Device Dashboard", layout="wide")

def load_users():
    with open("users.json") as f:
        return json.load(f)

def hash_pw(p, salt):
    return hashlib.sha256((p+salt).encode()).hexdigest()

def login_page():
    st.title("Login")
    users = load_users()
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in users:
            if hash_pw(p, users[u]["salt"]) == users[u]["password_hash"]:
                st.session_state.user = u
                st.rerun()
        st.error("Invalid credentials")

if "user" not in st.session_state:
    login_page()
    st.stop()

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard","Add/Edit Devices","Admin settings","Analytics","Reports/Logs"])

df = pd.read_csv("repairs.csv")

if page=="Dashboard":
    st.title("Dashboard")
    st.metric("Total Devices", len(df))
    st.dataframe(df)

elif page=="Add/Edit Devices":
    st.title("Add / Edit Devices")
    with st.form("add"):
        s = st.text_input("Server")
        pf = st.text_input("Parent fleet")
        fn = st.text_input("Fleet number")
        issue = st.text_area("Issue")
        pr = st.selectbox("Priority",[1,2,3])
        tech = st.selectbox("Tech Support check",["Yes","No"])
        stt = st.selectbox("Status",["New","Incomplete","waiting materials","Complete"])
        if st.form_submit_button("Add"):
            df.loc[len(df)] = [s,pf,fn,issue,pr,tech,stt]
            df.to_csv("repairs.csv",index=False)
            st.success("Added")
            time.sleep(0.2)
            st.rerun()

elif page=="Admin settings":
    st.title("Admin Settings")
    st.write("Manage users coming soon.")

elif page=="Analytics":
    st.title("Analytics")
    st.write("Charts coming soon.")

elif page=="Reports/Logs":
    st.title("Logs")
    st.write(pd.read_csv("logs.csv"))
