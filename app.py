
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Repair Dashboard", layout="wide")

CSV_FILE = "repairs.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=[
        "Server", "Parent fleet", "Fleet number", "Issue",
        "Priority", "Tech Support check", "Status"
    ])

df = load_data()

st.title("Device Repair Dashboard")

def highlight_priority(row):
    styles = [""] * len(row)
    priority = str(row["Priority"])
    idx = row.index.get_loc("Priority")

    if priority == "1":
        styles[idx] = "background-color: green; color: white; font-weight: bold;"
    elif priority == "2":
        styles[idx] = "background-color: orange; color: black; font-weight: bold;"
    elif priority == "3":
        styles[idx] = "background-color: red; color: white; font-weight: bold;"
    return styles

st.header("Device Table")
st.dataframe(df.style.apply(highlight_priority, axis=1), use_container_width=True)

st.header("Visual Dashboard")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Status Distribution")
    status_counts = df["Status"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%')
    ax.axis('equal')
    st.pyplot(fig)

with col2:
    st.subheader("Parent Fleet Distribution")
    fleet_counts = df["Parent fleet"].value_counts()
    fig2, ax2 = plt.subplots()
    ax2.pie(fleet_counts, labels=fleet_counts.index, autopct='%1.1f%%')
    ax2.axis('equal')
    st.pyplot(fig2)
