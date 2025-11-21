import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Device Repair Dashboard", layout="wide")

# ---------- Load or create data ----------
@st.cache_data
def load_data():
    try:
        return pd.read_csv("repairs.csv")
    except:
        return pd.DataFrame(columns=[
            "Device", "Serial", "Customer", "Technician",
            "Status", "Issue", "Cost",
            "Checked_in", "Updated"
        ])

data = load_data()

# ---------- Sidebar ----------
st.sidebar.title("📱 Device Repair Dashboard")
mode = st.sidebar.radio("Choose an action", [
    "Add New Repair",
    "View Repairs",
    "Analytics"
])

# ---------- Add New Repair ----------
if mode == "Add New Repair":
    st.title("➕ Add New Repair Job")

    with st.form("add_repair"):
        col1, col2 = st.columns(2)
        with col1:
            device = st.text_input("Device Name / Model")
            serial = st.text_input("Serial / IMEI")
            customer = st.text_input("Customer Name")

        with col2:
            technician = st.text_input("Technician")
            status = st.selectbox("Status", ["Pending", "In Progress", "Waiting for Parts", "Completed"])
            cost = st.number_input("Estimated Cost", min_value=0.0)

        issue = st.text_area("Describe the issue")

        submitted = st.form_submit_button("Save")

    if submitted:
        new_row = {
            "Device": device,
            "Serial": serial,
            "Customer": customer,
            "Technician": technician,
            "Status": status,
            "Issue": issue,
            "Cost": cost,
            "Checked_in": datetime.now(),
            "Updated": datetime.now()
        }

        data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
        data.to_csv("repairs.csv", index=False)
        st.success("✔ Repair job added successfully!")

# ---------- View Repairs ----------
elif mode == "View Repairs":
    st.title("📋 All Repair Jobs")
    st.write("Below is your current list of devices under repair:")

    if len(data) == 0:
        st.info("No repair jobs yet.")
    else:
        st.dataframe(data)

# ---------- Analytics ----------
elif mode == "Analytics":
    st.title("📊 Repair Analytics")

    total_repairs = len(data)
    completed_repairs = len(data[data["Status"] == "Completed"])
    waiting_repairs = len(data[data["Status"] == "Waiting for Parts"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Repairs", total_repairs)
    col2.metric("Completed", completed_repairs)
    col3.metric("Waiting for Parts", waiting_repairs)
