import streamlit as st
import pandas as pd
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# -------------------------------
# Sidebar: Authentication
# -------------------------------
st.sidebar.title("Login")
user_email = st.sidebar.text_input("Enter your email")

# Role mapping (replace with secrets later)
users_roles = {
    "paudie@example.com": "admin",
    "rob@example.com": "leader",
    "rep1@example.com": "rep",
    "rep2@example.com": "rep",
    "leadgen1@example.com": "leadgen",
    "leadgen2@example.com": "leadgen"
}

user_role = users_roles.get(user_email)
if user_role:
    st.sidebar.success(f"Logged in as {user_email} ({user_role})")
else:
    st.sidebar.warning("Unknown user - read-only access")
    user_role = "readonly"

# -------------------------------
# Google Sheets Integration (Placeholder)
# -------------------------------
if "service_account" in st.secrets:
    sa_info = json.loads(st.secrets["service_account"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        sa_info, scopes=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    )
    gc = gspread.authorize(credentials)
    # Example placeholders for sheets
    # leadgen_sheet = gc.open("SalesDashboard").worksheet("LeadGen")
    # sales_sheet = gc.open("SalesDashboard").worksheet("Sales")
else:
    st.warning("Google Sheets not connected. Add your service account to Streamlit secrets.")

# -------------------------------
# Initialize DataFrames (In-memory for demo)
# -------------------------------
if "leadgen_df" not in st.session_state:
    st.session_state.leadgen_df = pd.DataFrame(columns=[
        "Week", "Date Range", "Sector", "Agent", "Leads Generated",
        "Leads Contacted", "Appointments Booked", "Spend"
    ])

if "sales_df" not in st.session_state:
    st.session_state.sales_df = pd.DataFrame(columns=[
        "Week", "Date Range", "Sector", "Rep", "Appointments Sat",
        "Proposals Issued", "Sales Closed"
    ])

# -------------------------------
# Lead Generation Form
# -------------------------------
st.header("Lead Generation Input")

if user_role in ["admin", "leader", "leadgen"]:
    with st.form("lead_gen_form"):
        week_num = st.number_input("Week Number", min_value=1, max_value=52, step=1)
        date_range = st.text_input("Date Range (e.g., 18-24 Nov)")
        sector = st.selectbox("Sector", ["Domestic", "Commercial", "Agri"])
        total_leads = st.number_input("Total Leads Generated", min_value=0)
        total_contacted = st.number_input("Total Leads Contacted", min_value=0)
        appointments_booked = st.number_input("Appointments Booked", min_value=0)
        spend = st.number_input("Total Lead Generation Spend", min_value=0.0)
        agent_name = st.text_input("Lead Gen Agent Name (Optional)")
        submitted = st.form_submit_button("Submit Lead Data")
        
        if submitted:
            new_row = {
                "Week": week_num,
                "Date Range": date_range,
                "Sector": sector,
                "Agent": agent_name if agent_name else "Total",
                "Leads Generated": total_leads,
                "Leads Contacted": total_contacted,
                "Appointments Booked": appointments_booked,
                "Spend": spend
            }
            st.session_state.leadgen_df = pd.concat(
                [st.session_state.leadgen_df, pd.DataFrame([new_row])], ignore_index=True
            )
            st.success("Lead Generation data submitted!")

# -------------------------------
# Sales Rep Form
# -------------------------------
st.header("Sales Rep Input")

if user_role in ["admin", "leader", "rep"]:
    with st.form("sales_form"):
        rep_name = st.text_input("Rep Name")
        week_num_sales = st.number_input("Week Number", min_value=1, max_value=52, step=1, key="week_sales")
        date_range_sales = st.text_input("Date Range")
        sector_sales = st.selectbox("Sector", ["Domestic", "Commercial", "Agri"], key="sector_sales")
        appointments_sat = st.number_input("Appointments Sat", min_value=0)
        proposals_issued = st.number_input("Proposals Issued", min_value=0)
        sales_closed = st.number_input("Sales Closed", min_value=0)
        submitted_sales = st.form_submit_button("Submit Sales Data")
        
        if submitted_sales:
            new_row = {
                "Week": week_num_sales,
                "Date Range": date_range_sales,
                "Sector": sector_sales,
                "Rep": rep_name,
                "Appointments Sat": appointments_sat,
                "Proposals Issued": proposals_issued,
                "Sales Closed": sales_closed
            }
            st.session_state.sales_df = pd.concat(
                [st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True
            )
            st.success("Sales Rep data submitted!")

# -------------------------------
# Calculated Metrics
# -------------------------------
st.header("Calculated Metrics")

def calculate_metrics():
    metrics = {}
    # Leadgen metrics
    df = st.session_state.leadgen_df
    if not df.empty:
        grouped = df.groupby("Sector").sum(numeric_only=True)
        metrics['lead_to_appointment'] = (grouped["Appointments Booked"] / grouped["Leads Generated"]).fillna(0)
        metrics['cost_per_lead'] = (grouped["Spend"] / grouped["Leads Generated"]).fillna(0)
        metrics['cost_per_appointment'] = (grouped["Spend"] / grouped["Appointments Booked"]).fillna(0)
    else:
        metrics['lead_to_appointment'] = pd.Series()
        metrics['cost_per_lead'] = pd.Series()
        metrics['cost_per_appointment'] = pd.Series()
    return metrics

metrics = calculate_metrics()

st.subheader("Lead Generation Metrics")
st.write(metrics['lead_to_appointment'].to_frame("Lead → Appointment Rate"))
st.write(metrics['cost_per_lead'].to_frame("Cost per Lead"))
st.write(metrics['cost_per_appointment'].to_frame("Cost per Appointment"))

# Sales metrics
st.subheader("Sales Metrics")
df_sales = st.session_state.sales_df
if not df_sales.empty:
    sales_grouped = df_sales.groupby("Rep").sum(numeric_only=True)
    sales_grouped["Appointment → Proposal %"] = (sales_grouped["Proposals Issued"] / sales_grouped["Appointments Sat"]).fillna(0) * 100
    sales_grouped["Proposal → Sale %"] = (sales_grouped["Sales Closed"] / sales_grouped["Proposals Issued"]).fillna(0) * 100
    sales_grouped["Appointment → Sale %"] = (sales_grouped["Sales Closed"] / sales_grouped["Appointments Sat"]).fillna(0) * 100
    st.write(sales_grouped)

# -------------------------------
# Alerts / Flags
# -------------------------------
st.header("Alerts / Flags")

# Domestic appointment target
domestic = st.session_state.sales_df[st.session_state.sales_df["Sector"]=="Domestic"]
total_domestic_appointments = domestic["Appointments Sat"].sum() if not domestic.empty else 0

if total_domestic_appointments >= 70:
    st.success(f"Domestic Appointments: {total_domestic_appointments} ✅")
elif total_domestic_appointments >= 55:
    st.warning(f"Domestic Appointments: {total_domestic_appointments} ⚠️")
else:
    st.error(f"Domestic Appointments: {total_domestic_appointments} ❌")

# Lead to appointment flag
if not st.session_state.leadgen_df.empty:
    for sector, rate in metrics['lead_to_appointment'].items():
        if rate < 0.2:
            st.warning(f"Lead to Appointment rate for {sector} is below 20%: {rate:.2f}")

# Rep activity flag
for _, row in df_sales.iterrows():
    if row["Appointments Sat"] < 8:
        st.warning(f"{row['Rep']} has fewer than 8 appointments ({row['Appointments Sat']})")

# Rep performance flag
for _, row in df_sales.iterrows():
    appt_to_sale = row["Sales Closed"] / row["Appointments Sat"] if row["Appointments Sat"] > 0 else 0
    if appt_to_sale < 0.2:
        st.warning(f"{row['Rep']} Appointment → Sale below 20% ({appt_to_sale:.2f})")

# -------------------------------
# Rolling 4-Week Trends
# -------------------------------
st.header("Rolling 4-Week Trends")

def rolling_trends(df, column, label):
    if not df.empty:
        last_4_weeks = df.groupby("Week")[column].sum().tail(4)
        st.line_chart(last_4_weeks, height=200, use_container_width=True)
        st.markdown(f"**{label} (last 4 weeks)**")

rolling_trends(st.session_state.leadgen_df, "Leads Generated", "Leads Generated")
rolling_trends(st.session_state.leadgen_df, "Appointments Booked", "Appointments Booked")
rolling_trends(st.session_state.sales_df, "Appointments Sat", "Appointments Sat")
rolling_trends(st.session_state.sales_df, "Proposals Issued", "Proposals Issued")
rolling_trends(st.session_state.sales_df, "Sales Closed", "Sales Closed")
