
import streamlit as st
import pandas as pd
import os, json, hashlib, secrets, datetime
import plotly.express as px

BASE_DIR = os.path.dirname(__file__)
REPAIRS_CSV = os.path.join(BASE_DIR, "repairs.csv")
USERS_JSON = os.path.join(BASE_DIR, "users.json")
LOGS_CSV = os.path.join(BASE_DIR, "logs.csv")

# ---- Utilities ----
def load_repairs():
    if os.path.exists(REPAIRS_CSV):
        return pd.read_csv(REPAIRS_CSV, dtype=str).fillna("")
    cols = ["Server","Parent fleet","Fleet number","Issue","Priority","Tech Support check","Status"]
    return pd.DataFrame(columns=cols)

def save_repairs(df):
    df.to_csv(REPAIRS_CSV, index=False)

def load_users():
    if os.path.exists(USERS_JSON):
        with open(USERS_JSON,"r") as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_JSON,"w") as f:
        json.dump(users, f, indent=2)

def log_action(user, action, details=""):
    timestamp = datetime.datetime.utcnow().isoformat()
    entry = {"timestamp":timestamp,"user":user,"action":action,"details":details}
    if os.path.exists(LOGS_CSV):
        df = pd.read_csv(LOGS_CSV, dtype=str)
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    else:
        df = pd.DataFrame([entry])
    df.to_csv(LOGS_CSV, index=False)

def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

# ---- Session init ----
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = "readonly"
if "theme_dark" not in st.session_state:
    st.session_state.theme_dark = False

# ---- App UI ----
st.set_page_config(page_title="Multi-Page Repair Dashboard", layout="wide")

# Sidebar: Login / Theme toggle / Navigation
st.sidebar.title("Access & Navigation")
users = load_users()

if st.session_state.user is None:
    st.sidebar.subheader("Login")
    selected_user = st.sidebar.selectbox("Username", ["(choose)"] + [u["username"] for u in users])
    pwd = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Log in"):
        if selected_user == "(choose)":
            st.sidebar.error("Choose a username")
        else:
            user_record = next((u for u in users if u["username"]==selected_user), None)
            if user_record and hash_password(pwd, user_record["salt"]) == user_record["password_hash"]:
                st.session_state.user = selected_user
                st.session_state.role = "admin" if selected_user=="admin" else "readonly"
                log_action(st.session_state.user, "login", "successful")
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid credentials")
else:
    st.sidebar.markdown(f"**Logged in:** {st.session_state.user} ({st.session_state.role})")
    if st.sidebar.button("Log out"):
        log_action(st.session_state.user, "logout", "")
        st.session_state.user = None
        st.session_state.role = "readonly"
        st.experimental_rerun()

st.sidebar.markdown("---")
st.session_state.theme_dark = st.sidebar.checkbox("Dark mode", value=st.session_state.theme_dark)
if st.session_state.theme_dark:
    st.markdown(
        """<style>
        .main { background-color: #0e1117; color: #EEF2FF; }
        .stButton>button { background-color:#2b2b2b; color:white; }
        </style>""", unsafe_allow_html=True
    )

# Navigation
page = st.sidebar.radio("Go to", ["Dashboard","Add/Edit Devices","Admin settings","Analytics","Reports/Logs"])

# Load data
df = load_repairs()

# Priority highlighting util (full cell)
def style_priority(df_local):
    def _style(row):
        priority = str(row["Priority"])
        styles = [""]*len(row)
        if priority == "1":
            color = "background-color: #2ecc71; color: black; font-weight: bold;"
        elif priority == "2":
            color = "background-color: #f39c12; color: black; font-weight: bold;"
        elif priority == "3":
            color = "background-color: #e74c3c; color: white; font-weight: bold;"
        else:
            color = ""
        idx = list(df_local.columns).index("Priority")
        styles[idx] = color
        return styles
    return df_local.style.apply(lambda r: _style(r), axis=1)

# --- PAGE: Dashboard ---
if page == "Dashboard":
    st.title("Dashboard — Overview")
    st.markdown("Split view: visual dashboard on top, device table below.")
    # Top visuals
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.subheader("By Status (circle)")
        status_counts = df["Status"].value_counts()
        if not status_counts.empty:
            fig = px.pie(values=status_counts.values, names=status_counts.index, title="Status Distribution", hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data")
    with col2:
        st.subheader("By Parent fleet (circle)")
        fleet_counts = df["Parent fleet"].value_counts()
        if not fleet_counts.empty:
            fig2 = px.pie(values=fleet_counts.values, names=fleet_counts.index, title="Parent Fleet Distribution", hole=0.3)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data")
    with col3:
        st.subheader("Priority counts")
        pri_counts = df["Priority"].value_counts().reindex(["1","2","3"]).fillna(0)
        fig3 = px.bar(x=pri_counts.index, y=pri_counts.values, labels={"x":"Priority","y":"Count"}, title="Priorities")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.subheader("Device Table")
    st.dataframe(style_priority(df), use_container_width=True)

# --- PAGE: Add/Edit Devices ---
elif page == "Add/Edit Devices":
    st.title("Add / Edit Devices")
    if st.session_state.role != "admin":
        st.info("Read-only users cannot add or edit. Log in as admin to modify data.")

    with st.expander("Add New Device"):
        if st.session_state.role == "admin":
            with st.form("add_form"):
                server = st.text_input("Server")
                parent = st.text_input("Parent fleet")
                fleet = st.text_input("Fleet number")
                issue = st.text_area("Issue", height=150)
                priority = st.selectbox("Priority", ["1","2","3"])
                tech = st.selectbox("Tech Support check", ["Yes","No"])
                status = st.selectbox("Status", ["New","Incomplete","waiting materials","Complete"])
                submitted = st.form_submit_button("Add Device")
                if submitted:
                    new_row = {"Server":server,"Parent fleet":parent,"Fleet number":fleet,"Issue":issue,
                               "Priority":priority,"Tech Support check":tech,"Status":status}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_repairs(df)
                    log_action(st.session_state.user or "anonymous","add", json.dumps(new_row))
                    st.success("Device added")
        else:
            st.write("Admin only")

    st.markdown("---")
    st.subheader("Edit existing record")
    if len(df) == 0:
        st.info("No records to edit")
    else:
        if st.session_state.role == "admin":
            row_idx = st.number_input("Row index to edit", min_value=0, max_value=max(0,len(df)-1), step=1)
            if st.button("Load record"):
                st.session_state.edit_row = df.loc[int(row_idx)].to_dict()
                st.session_state.edit_index = int(row_idx)
                st.experimental_rerun()
            if "edit_row" in st.session_state:
                er = st.session_state.edit_row
                with st.form("edit_form"):
                    u_server = st.text_input("Server", er["Server"])
                    u_parent = st.text_input("Parent fleet", er["Parent fleet"])
                    u_fleet = st.text_input("Fleet number", er["Fleet number"])
                    u_issue = st.text_area("Issue", er["Issue"], height=150)
                    u_priority = st.selectbox("Priority", ["1","2","3"], index=["1","2","3"].index(str(er["Priority"])))
                    u_tech = st.selectbox("Tech Support check", ["Yes","No"], index=["Yes","No"].index(er["Tech Support check"]))
                    u_status = st.selectbox("Status", ["New","Incomplete","waiting materials","Complete"], index=["New","Incomplete","waiting materials","Complete"].index(er["Status"]))
                    saved = st.form_submit_button("Save changes")
                    if saved:
                        df.loc[st.session_state.edit_index] = [u_server,u_parent,u_fleet,u_issue,u_priority,u_tech,u_status]
                        save_repairs(df)
                        log_action(st.session_state.user,"edit", f"row {st.session_state.edit_index}")
                        del st.session_state.edit_row
                        del st.session_state.edit_index
                        st.success("Saved changes")
        else:
            st.write("Admin only - please login")

    st.markdown("---")
    st.subheader("Delete record (Admin only)")
    if st.session_state.role == "admin" and len(df)>0:
        del_idx = st.number_input("Row index to delete", min_value=0, max_value=len(df)-1, step=1, key="del_idx")
        if st.button("Delete record"):
            rec = df.loc[int(del_idx)].to_dict()
            df = df.drop(int(del_idx)).reset_index(drop=True)
            save_repairs(df)
            log_action(st.session_state.user,"delete", json.dumps(rec))
            st.success("Deleted")
    elif st.session_state.role != "admin":
        st.write("Login as admin to delete")

# --- PAGE: Admin settings ---
elif page == "Admin settings":
    st.title("Admin settings")
    if st.session_state.role != "admin":
        st.info("Only admin can manage users. Log in as admin.")
    else:
        st.subheader("Manage users")
        users = load_users()
        st.write("Existing users:")
        st.write([u["username"] for u in users])
        with st.expander("Add new user"):
            with st.form("add_user_form"):
                uname = st.text_input("Username")
                pwd = st.text_input("Password")
                submit_user = st.form_submit_button("Create user")
                if submit_user:
                    salt = secrets.token_hex(8)
                    pwd_hash = hash_password(pwd, salt)
                    users.append({"username":uname,"salt":salt,"password_hash":pwd_hash})
                    save_users(users)
                    log_action(st.session_state.user,"create_user", uname)
                    st.success("User created")

        st.markdown("---")
        with st.expander("Delete user"):
            del_user = st.selectbox("Select user to delete", [u["username"] for u in users if u["username"]!="admin"])
            if st.button("Delete user"):
                users = [u for u in users if u["username"]!=del_user]
                save_users(users)
                log_action(st.session_state.user,"delete_user",del_user)
                st.success("Deleted user")

# --- PAGE: Analytics ---
elif page == "Analytics":
    st.title("Analytics")
    st.subheader("Priority breakdown")
    pri_counts = df["Priority"].value_counts().reindex(["1","2","3"]).fillna(0)
    fig = px.pie(names=pri_counts.index, values=pri_counts.values, title="Priority distribution", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Status over Parent fleet")
    if not df.empty:
        pivot = df.pivot_table(index="Parent fleet", columns="Status", aggfunc="size", fill_value=0)
        st.dataframe(pivot)
        st.bar_chart(df["Parent fleet"].value_counts())

# --- PAGE: Reports/Logs ---
elif page == "Reports/Logs":
    st.title("Reports & Logs")
    st.subheader("Action logs")
    if os.path.exists(LOGS_CSV):
        logs_df = pd.read_csv(LOGS_CSV, dtype=str).fillna("")
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.info("No logs yet")

    st.markdown("---")
    st.subheader("Export current data")
    st.download_button("Download repairs.csv", data=open(REPAIRS_CSV,"rb"), file_name="repairs.csv")
