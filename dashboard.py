import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ================= CONFIG =================
st.set_page_config(layout="wide")

# ================= AUTH =================
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    r"F:\Python\Projects\credentials.json", scope)

client = gspread.authorize(creds)

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    sheet = client.open_by_key("1KMgtEmIBAQ2kxn0qDrBvkbica3zzlWReBqlqMLX-zNw").worksheet("Master")

    data = sheet.get_all_values()

    headers = data[0]
    rows = data[1:]

    # Fix duplicate columns
    new_headers = []
    seen = {}

    for col in headers:
        col = str(col).strip()
        if col in seen:
            seen[col] += 1
            col = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
        new_headers.append(col)

    df = pd.DataFrame(rows, columns=new_headers)

    return df

df = load_data()

if df.empty:
    st.error("No data found")
    st.stop()

# ================= FIND COLUMNS =================
def find_col(keyword):
    for col in df.columns:
        if keyword.lower() in col.lower():
            return col
    return None

batch_col   = find_col("batch")
mentor_col  = find_col("mentor")
channel_col = find_col("channel")
region_col  = find_col("region")

# ================= STATUS =================
def get_status(row):
    row_str = str(row)
    if "Drop" in row_str:
        return "Drop"
    elif "Fail" in row_str:
        return "Fail"
    elif "Redo" in row_str:
        return "Redo"
    elif "Pass" in row_str:
        return "Pass"
    return "Other"

df["Final_Status"] = df.apply(get_status, axis=1)

# ================= TITLE =================
st.title("📊 Training Dashboard")

# ================= FILTERS =================
col1, col2, col3, col4 = st.columns(4)

with col1:
    batch = st.selectbox("Batch", ["All"] + sorted(df[batch_col].unique())) if batch_col else "All"

with col2:
    mentor = st.selectbox("Mentor", ["All"] + sorted(df[mentor_col].unique())) if mentor_col else "All"

with col3:
    channel = st.selectbox("Channel", ["All"] + sorted(df[channel_col].unique())) if channel_col else "All"

with col4:
    region = st.selectbox("Region", ["All"] + sorted(df[region_col].unique())) if region_col else "All"

# ================= FILTER =================
filtered_df = df.copy()

if batch_col and batch != "All":
    filtered_df = filtered_df[filtered_df[batch_col] == batch]

if mentor_col and mentor != "All":
    filtered_df = filtered_df[filtered_df[mentor_col] == mentor]

if channel_col and channel != "All":
    filtered_df = filtered_df[filtered_df[channel_col] == channel]

if region_col and region != "All":
    filtered_df = filtered_df[filtered_df[region_col] == region]

# ================= KPIs =================
st.subheader("📊 Summary")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total", len(filtered_df))
k2.metric("Pass", len(filtered_df[filtered_df["Final_Status"] == "Pass"]))
k3.metric("Fail", len(filtered_df[filtered_df["Final_Status"] == "Fail"]))
k4.metric("Redo", len(filtered_df[filtered_df["Final_Status"] == "Redo"]))
k5.metric("Drop", len(filtered_df[filtered_df["Final_Status"] == "Drop"]))

# ================= PIE =================
st.subheader("📊 Status Distribution")
fig = px.pie(filtered_df, names="Final_Status")
st.plotly_chart(fig, width="stretch")

# ================= MENTOR =================
if mentor_col:
    st.subheader("👨‍🏫 Mentor Performance")

    mentor_chart = filtered_df.groupby([mentor_col, "Final_Status"]).size().reset_index(name="Count")

    fig2 = px.bar(mentor_chart, x=mentor_col, y="Count", color="Final_Status")
    st.plotly_chart(fig2, width="stretch")

# ================= TABLE =================
st.subheader("📋 Data")
st.dataframe(filtered_df, width="stretch")