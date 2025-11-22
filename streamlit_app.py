import streamlit as st
import pandas as pd
import json
import yaml
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------------
# Authentication / Roles
# -------------------------------

# Example roles (replace with secrets/auth file later)
auth_config = {
    "users": ["paudie@example.com", "rob@example.com", "rep1@example.com"],
    "roles": ["admin", "leader", "rep"]
}

# Simple login simulation
st.sidebar.title("Login")
user_email = st.sidebar.text_input("Enter your email")
user_role = None
if user_email in auth_config["users"]:
    user_role = auth_config["roles"][auth_config["users"].index(user_email)]
    st.sidebar.success(f"Logged in as {user_email} ({user_role})")
else:
    st.sidebar.warning("Unknown user, limited access")

# -------------------------------
# Connect to Google Sheets
# -------------------------------

if "service_account" in st.secrets:
    sa_info = json.loads(st.secrets["service_account"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        sa_info, scopes=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    )
    gc = gspread.authorize(credentials)
    # Placeholder: open your sheet
    # sheet = gc.open("SalesDashboard").sheet1
else:
    st.warning("Google Sheets not connected (add secrets)")

# -------------------------------
# Dashboard Layout
# -------------------------------

st.title("Weekly Sales & Lead Dashboard")

# -------------------------------
# Weekly Lead Generation Input
# -------------------------------
st.header("Lead Generation Input (Weekly)")

if user_role in ["admin", "leader"]:
    with st.form("lead_gen_form"):
        week_num = st.number_input("Week Number", min_value=1, max_value=52, step=1)
        date_range = st.text_input("Date Range (e.g., 18-24 Nov)")
        sector = st.selectbox("Sector", ["Domestic", "Commercial"])
        total_leads = st.number_input("Total Leads Generated", min_value=0)
        total_contacted = st.number_input("Total Leads Contacted", min_value=0)
        appointments_booked = st.number_input("Appointments Booked", min_value=0)
        spend = st.number_input("Total Lead Generation Spend", min_value=0.0)
        submitted = st.form_submit_button("Submit Lead Data")
        if submitted:
            st.success("Lead data submitted!")

# -------------------------------
# Weekly Sales Input
# -------------------------------
st.header("Sales Input (Weekly)")

if user_role in ["admin", "leader", "rep"]:
    with st.form("sales_form"):
        rep_name = st.text_input("Rep Name")
        week_num = st.number_input("Week Number", min_value=1, max_value=52, step=1, key="week_sales")
        date_range = st.text_input("Date Range")
        sector = st.selectbox("Sector", ["Domestic", "Commercial"], key="sales_sector")
        appointments_sat = st.number_input("Appointments Sat", min_value=0)
        proposals_issued = st.number_input("Proposals Issued", min_value=0)
        sales_closed = st.number_input("Sales Closed", min_value=0)
        submitted_sales = st.form_submit_button("Submit Sales Data")
        if submitted_sales:
            st.success("Sales data submitted!")

# -------------------------------
# Calculated Metrics (Placeholder)
# -------------------------------

st.header("Calculated Metrics")

st.markdown("- **Lead to Appointment Conversion:** TBD")
st.markdown("- **Appointment to Sale Conversion:** TBD")
st.markdown("- **Cost per Acquisition:** TBD")

# -------------------------------
# Alerts / Flags
# -------------------------------

st.header("Alerts / Flags")

st.markdown("- **Domestic Appointments < 70:** Red/Amber/Green")
st.markdown("- **Lead to Appointment < 20%:** Highlight")
st.markdown("- **Rep Activity < 8 appointments:** Highlight")
st.markdown("- **Rep Performance < 20% Appointment to Sale:** Highlight")
