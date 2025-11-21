
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Device Repair Dashboard", layout="wide")

st.title("Device Repair Dashboard")

@st.cache_data
def load_data():
    return pd.read_csv("repairs.csv")

df = load_data()

st.sidebar.header("Filters")
status_filter = st.sidebar.multiselect("Status", df["Status"].unique())
priority_filter = st.sidebar.multiselect("Priority", df["Priority"].unique())

filtered_df = df.copy()
if status_filter:
    filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]
if priority_filter:
    filtered_df = filtered_df[filtered_df["Priority"].isin(priority_filter)]

st.dataframe(filtered_df, use_container_width=True)
