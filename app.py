
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Device Repair Dashboard", layout="wide")

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

# --- LOGIN SYSTEM ---
st.sidebar.title("Login")
role = st.sidebar.selectbox("Select role", ["Read-Only", "Admin"])
password = st.sidebar.text_input("Password", type="password")
is_admin = (role == "Admin" and password == "admin123")

st.title("Device Repair Dashboard")

# FULL CELL PRIORITY HIGHLIGHTING
def highlight_priority(row):
    styles = [""] * len(row)
    if row["Priority"] == "1":
        styles[row.index.get_loc("Priority")] = "background-color: red; color: white; font-weight: bold;"
    elif row["Priority"] == "2":
        styles[row.index.get_loc("Priority")] = "background-color: orange; color: black; font-weight: bold;"
    elif row["Priority"] == "3":
        styles[row.index.get_loc("Priority")] = "background-color: green; color: white; font-weight: bold;"
    return styles

# FILTERS
st.sidebar.header("Filters")
issue_filter = st.sidebar.text_input("Filter by Issue (contains)")
comments_filter = st.sidebar.text_input("Filter by Comments (contains)")

filtered_df = df.copy()

if issue_filter:
    filtered_df = filtered_df[filtered_df["Issue"].str.contains(issue_filter, case=False, na=False)]
if comments_filter:
    filtered_df = filtered_df[filtered_df["Comments"].str.contains(comments_filter, case=False, na=False)]

# ADMIN ADD FORM
if is_admin:
    st.header("Add New Device")
    with st.form("add_device_form"):
        server = st.text_input("Server")
        parent_fleet = st.text_input("Parent fleet")
        fleet_num = st.text_input("Fleet number")
        registration = st.text_input("Registration")
        issue = st.text_area("Issue")
        priority = st.selectbox("Priority", ["1", "2", "3"])
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
else:
    st.info("Read-only mode: Login as admin to add or delete records.")

# TABLE
st.header("Device List")
st.dataframe(filtered_df.style.apply(highlight_priority, axis=1), use_container_width=True)

# DELETE HIDDEN
if is_admin:
    with st.expander("Delete a Device (Admin Only)"):
        delete_index = st.selectbox("Select a device to delete", ["None"] + list(df.index.astype(str)))
        if st.button("Confirm Delete"):
            if delete_index != "None":
                df = df.drop(int(delete_index))
                df.reset_index(drop=True, inplace=True)
                save_data(df)
                st.success("Device deleted successfully!")

# ANALYTICS
st.header("Analytics Dashboard")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Devices by Priority")
    st.bar_chart(df["Priority"].value_counts())

with col2:
    st.subheader("Devices by Status")
    st.bar_chart(df["Status"].value_counts())
