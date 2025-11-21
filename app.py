
import streamlit as st
import pandas as pd
import os
import hashlib, binascii, secrets
import plotly.express as px

st.set_page_config(page_title="Repair Dashboard (Multi-page)", layout="wide")

DATA_DIR = "."
REPAIRS_FILE = os.path.join(DATA_DIR, "repairs.csv")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")

# ---------- Password utilities ----------
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_bytes(16)
    else:
        salt = binascii.unhexlify(salt)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return binascii.hexlify(salt).decode(), binascii.hexlify(dk).decode()

def verify_password(stored_salt_hex, stored_hash_hex, provided_password):
    salt = binascii.unhexlify(stored_salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 200000)
    return binascii.hexlify(dk).decode() == stored_hash_hex

# ---------- Data helpers ----------
@st.cache_data
def load_repairs():
    if os.path.exists(REPAIRS_FILE):
        return pd.read_csv(REPAIRS_FILE)
    return pd.DataFrame(columns=[
        "Server","Parent fleet","Fleet number","Issue","Priority","Tech Support check","Status"
    ])

def save_repairs(df):
    df.to_csv(REPAIRS_FILE, index=False)

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE, dtype=str).fillna("")
    return pd.DataFrame(columns=["username","salt","pw_hash","role"])

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

# ---------- Session / Auth ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

st.sidebar.title("Account")

users = load_users()

if not st.session_state.logged_in:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Log in"):
        user_row = users[users["username"] == username]
        if user_row.shape[0] == 1:
            row = user_row.iloc[0]
            if verify_password(row["salt"], row["pw_hash"], password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = row["role"]
                st.sidebar.success(f"Logged in as {username} ({row['role']})")
            else:
                st.sidebar.error("Incorrect username or password")
        else:
            st.sidebar.error("Incorrect username or password")
    st.sidebar.markdown("---")
    st.sidebar.info("If you don't have an account ask an Admin to create one.")
else:
    st.sidebar.write(f"User: **{st.session_state.username}**")
    st.sidebar.write(f"Role: **{st.session_state.role}**")
    if st.sidebar.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.experimental_rerun()

# ---------- Navigation ----------
st.sidebar.title("Navigation")
pages = ["Dashboard","Manage Devices","Analytics"]
if st.session_state.logged_in and st.session_state.role == "Admin":
    pages.append("User Management")
page = st.sidebar.radio("Go to", pages)

# ---------- Load data ----------
df = load_repairs()
users = load_users()

# ---------- Helpers ----------
def highlight_priority_full(row):
    styles = [""] * len(row)
    if str(row.get("Priority","")) == "1":
        styles[row.index.get_loc("Priority")] = "background-color: green; color: white; font-weight: bold;"
    elif str(row.get("Priority","")) == "2":
        styles[row.index.get_loc("Priority")] = "background-color: orange; color: black; font-weight: bold;"
    elif str(row.get("Priority","")) == "3":
        styles[row.index.get_loc("Priority")] = "background-color: red; color: white; font-weight: bold;"
    return styles

# ---------- Pages ----------
if page == "Dashboard":
    st.title("Device Repair — Dashboard")
    st.markdown("Quick view and filters")
    col1, col2 = st.columns([3,1])
    with col2:
        st.header("Filters")
        parent_filter = st.selectbox("Parent fleet", options=["All"] + sorted(df["Parent fleet"].dropna().unique().tolist()))
        status_filter = st.selectbox("Status", options=["All"] + sorted(df["Status"].dropna().unique().tolist()))
        priority_filter = st.selectbox("Priority", options=["All","1","2","3"])
    filtered = df.copy()
    if parent_filter and parent_filter != "All":
        filtered = filtered[filtered["Parent fleet"] == parent_filter]
    if status_filter and status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]
    if priority_filter and priority_filter != "All":
        filtered = filtered[filtered["Priority"] == priority_filter]
    st.dataframe(filtered.style.apply(highlight_priority_full, axis=1), use_container_width=True)

elif page == "Manage Devices":
    st.title("Manage Devices")
    if not st.session_state.logged_in or st.session_state.role != "Admin":
        st.warning("Manage Devices is available to Admin users only.")
    # Add new device
    st.subheader("Add New Device")
    with st.form("add_device"):
        server = st.text_input("Server")
        parent_fleet = st.text_input("Parent fleet")
        fleet_number = st.text_input("Fleet number")
        issue = st.text_area("Issue", height=120)
        priority = st.selectbox("Priority", ["1","2","3"])
        tech = st.selectbox("Tech Support check", ["Yes","No"])
        status = st.selectbox("Status", ["New","Incomplete","waiting materials","Complete"])
        submitted = st.form_submit_button("Add device")
    if submitted:
        new = {"Server":server,"Parent fleet":parent_fleet,"Fleet number":fleet_number,
               "Issue":issue,"Priority":priority,"Tech Support check":tech,"Status":status}
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        save_repairs(df)
        st.success("Added device.")
        st.experimental_rerun()
    # List and edit existing
    st.subheader("Existing Devices")
    for i in range(len(df)):
        row = df.iloc[i]
        with st.expander(f"{row['Server']} — {row['Issue'][:60]}"):
            st.write("**Server:**", row["Server"])
            st.write("**Parent fleet:**", row["Parent fleet"])
            st.write("**Fleet number:**", row["Fleet number"])
            st.write("**Issue:**", row["Issue"])
            st.write("**Priority:**", row["Priority"])
            st.write("**Tech Support check:**", row["Tech Support check"])
            st.write("**Status:**", row["Status"])
            if st.session_state.logged_in and st.session_state.role == "Admin":
                col1, col2 = st.columns(2)
                with col1:
                    ns = st.text_input("Server", value=row["Server"], key=f"ns_{i}")
                    npf = st.text_input("Parent fleet", value=row["Parent fleet"], key=f"npf_{i}")
                    nf = st.text_input("Fleet number", value=row["Fleet number"], key=f"nf_{i}")
                with col2:
                    ni = st.text_area("Issue", value=row["Issue"], key=f"ni_{i}", height=120)
                    nprio = st.selectbox("Priority", ["1","2","3"], index=["1","2","3"].index(str(row["Priority"])), key=f"nprio_{i}")
                    ntech = st.selectbox("Tech Support check", ["Yes","No"], index=["Yes","No"].index(row["Tech Support check"]), key=f"ntech_{i}")
                    nstat = st.selectbox("Status", ["New","Incomplete","waiting materials","Complete"], index=["New","Incomplete","waiting materials","Complete"].index(row["Status"]), key=f"nstat_{i}")
                if st.button("Save changes", key=f"save_{i}"):
                    df.loc[i] = [ns, npf, nf, ni, nprio, ntech, nstat]
                    save_repairs(df)
                    st.success("Saved.")
                    st.experimental_rerun()
                if st.button("Delete device", key=f"del_{i}"):
                    df = df.drop(i).reset_index(drop=True)
                    save_repairs(df)
                    st.warning("Deleted.")
                    st.experimental_rerun()

elif page == "Analytics":
    st.title("Analytics")
    st.markdown("Visual summaries — circle charts as requested")
    # Status donut
    st.subheader("Status distribution")
    status_counts = df["Status"].value_counts()
    if not status_counts.empty:
        fig = px.pie(values=status_counts.values, names=status_counts.index, hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to show.")
    # Parent fleet donut
    st.subheader("Parent fleet distribution")
    fleet_counts = df["Parent fleet"].value_counts()
    if not fleet_counts.empty:
        fig2 = px.pie(values=fleet_counts.values, names=fleet_counts.index, hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data to show.")
    # Priority bar
    st.subheader("Priority counts")
    pr = df["Priority"].value_counts().reindex(["1","2","3"]).fillna(0)
    fig3 = px.bar(x=pr.index, y=pr.values, labels={"x":"Priority","y":"Count"})
    st.plotly_chart(fig3, use_container_width=True)

elif page == "User Management":
    st.title("User Management (Admin)")
    if not st.session_state.logged_in or st.session_state.role != "Admin":
        st.warning("User Management is Admin only.")
    else:
        st.subheader("Existing users")
        st.write(users[["username","role"]])
        st.subheader("Create new user")
        with st.form("create_user"):
            uname = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            role_sel = st.selectbox("Role", ["Admin","Read-only"])
            created = st.form_submit_button("Create user")
        if created:
            if uname.strip() == "" or pwd.strip() == "":
                st.error("Provide both username and password.")
            elif uname in users["username"].values:
                st.error("User already exists.")
            else:
                salt_hex, hash_hex = hash_password(pwd)
                users = users.append({"username":uname,"salt":salt_hex,"pw_hash":hash_hex,"role":role_sel}, ignore_index=True)
                save_users(users)
                st.success("User created.")
                st.experimental_rerun()
        st.subheader("Delete a user")
        del_user = st.selectbox("Select user to delete", options=users["username"].tolist())
        if st.button("Delete user"):
            if del_user == st.session_state.username:
                st.error("You cannot delete yourself while logged in.")
            else:
                users = users[users["username"] != del_user].reset_index(drop=True)
                save_users(users)
                st.success("Deleted user.")
                st.experimental_rerun()
