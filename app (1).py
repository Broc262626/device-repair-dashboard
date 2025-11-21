
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Device Repair Dashboard", layout="wide")
st.title("Device Repair Dashboard")

CSV_FILE = "repairs.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=[
        "Server", "Parent fleet", "Fleet number", "Registration",
        "Issue", "Priority", "Comments", "Status"
    ])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

df = load_data()

st.header("Add New Device")
with st.form("add_device_form"):
    server = st.text_input("Server")
    parent_fleet = st.text_input("Parent fleet")
    fleet_num = st.text_input("Fleet number")
    registration = st.text_input("Registration")
    issue = st.text_area("Issue")
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    comments = st.text_area("Comments")
    status = st.selectbox("Status", ["Pending", "In Progress", "Waiting for Parts", "Completed"])

    submitted = st.form_submit_button("Add Device")

if submitted:
    new_row = {
        "Server": server,
        "Parent fleet": parent_fleet,
        "Fleet number": fleet_num,
        "Registration": registration,
        "Issue": issue,
        "Priority": priority,
        "Comments": comments,
        "Status": status
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.success("Device added successfully!")

st.header("Device List")

if not df.empty:
    delete_index = st.selectbox("Select a device to delete", ["None"] + list(df.index.astype(str)))
    if st.button("Delete Device") and delete_index != "None":
        df = df.drop(int(delete_index))
        df.reset_index(drop=True, inplace=True)
        save_data(df)
        st.success("Device deleted successfully!")

st.dataframe(df, use_container_width=True)
