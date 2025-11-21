import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Device Repair Dashboard", layout="wide")

# ---------- Load or create data ----------
import os

DATA_FILE = "repairs.csv"

# Load data directly (no caching)
if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE)
else:
    data = pd.DataFrame(columns=[
        "Device", "Serial", "Customer", "Technician",
        "Status", "Issue", "Cost",
        "Checked_in", "Updated"
    ])

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

    # Add the new repair to the dataframe
    data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)

    # Save to CSV
    data.to_csv(DATA_FILE, index=False)

    # Show success message and refresh the app
    st.success("✔ Repair job added successfully!")
    st.experimental_rerun()  # <- This reloads the app immediately with the new data


# ---------- View Repairs ----------
elif mode == "View Repairs":
    st.title("📋 All Repair Jobs")
    st.write("Use the filters below to quickly find devices:")

    if len(data) == 0:
        st.info("No repair jobs yet.")
    else:
        # --- Filters ---
        col1, col2, col3 = st.columns(3)

        with col1:
            technician_filter = st.multiselect(
                "Filter by Technician",
                options=data["Technician"].unique(),
                default=data["Technician"].unique()
            )

        with col2:
            status_filter = st.multiselect(
                "Filter by Status",
                options=data["Status"].unique(),
                default=data["Status"].unique()
            )

        with col3:
            device_filter = st.text_input("Search by Device Name")

        # --- Apply filters ---
        filtered_data = data[
            (data["Technician"].isin(technician_filter)) &
            (data["Status"].isin(status_filter)) &
            (data["Device"].str.contains(device_filter, case=False, na=False))
        ]

        # --- Display table sorted by latest check-in ---
        st.dataframe(filtered_data.sort_values(by="Checked_in", ascending=False))

# ---------- Analytics ----------
# --- Filters ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    technician_filter = st.multiselect(
        "Filter by Technician",
        options=data["Technician"].unique(),
        default=data["Technician"].unique()
    )

with col2:
    status_filter = st.multiselect(
        "Filter by Status",
        options=data["Status"].unique(),
        default=data["Status"].unique()
    )

with col3:
    device_filter = st.text_input("Search by Device Name")

with col4:
    # Ensure Checked_in is datetime
    data['Checked_in'] = pd.to_datetime(data['Checked_in'], errors='coerce')
    start_date, end_date = st.date_input(
        "Filter by Check-in Date",
        value=[data['Checked_in'].min(), data['Checked_in'].max()]
    )

