import streamlit as st
import pandas as pd
import requests
import datetime
import plotly.express as px

# Configure page layout
st.set_page_config(page_title="Data Center Time Series", layout="wide")

@st.cache_data(ttl=3600)
def load_data():
    """Fetch the latest release parquet file from the GitHub API."""
    repo_url = "https://api.github.com/repos/JesusASantillanMinila/data_centers_time_series/releases/latest"
    try:
        response = requests.get(repo_url)
        response.raise_for_status()
        data = response.json()
        
        # Locate the parquet asset URL
        download_url = next(
            (asset["browser_download_url"] for asset in data.get("assets", []) 
             if asset["name"].endswith(".parquet")), 
            None
        )
        
        if not download_url:
            st.error("No parquet file found in the latest release.")
            st.stop()
            
        df = pd.read_parquet(download_url)
        df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
        return df
        
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

df = load_data()

# Dashboard Title
st.title("Data Centers Time Series Dashboard")

# Define default filter values
default_state = "Illinois" 
default_county = "Cook"
default_start_date = datetime.date(2025, 1, 1)

# Top row filters
col1, col2, col3 = st.columns(3)

with col1:
    state_list = sorted(df['STATE_NAME'].dropna().unique())
    start_index_state = state_list.index(default_state) if default_state in state_list else 0
    selected_state = st.selectbox("Select State", state_list, index=start_index_state)

with col2:
    county_list = sorted(df[df['STATE_NAME'] == selected_state]['COUNTY_NAME'].dropna().unique())
    start_index_county = county_list.index(default_county) if default_county in county_list else 0
    selected_county = st.selectbox("Select County", county_list, index=start_index_county)

with col3:
    min_date = df['snapshot_date'].min().date()
    max_date = df['snapshot_date'].max().date()
    
    # Ensure default start date is within valid bounds
    safe_start_date = max(min_date, min(default_start_date, max_date))
    
    selected_dates = st.date_input(
        "Select Date Range", 
        value=(safe_start_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# Handle single vs. range date selections
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_dt, end_dt = selected_dates
elif isinstance(selected_dates, tuple) and len(selected_dates) == 1:
    start_dt, end_dt = selected_dates[0], max_date
else:
    start_dt, end_dt = selected_dates, max_date

# Filter DataFrame based on selections
mask = (
    (df['STATE_NAME'] == selected_state) &
    (df['COUNTY_NAME'] == selected_county) &
    (df['snapshot_date'].dt.date >= start_dt) &
    (df['snapshot_date'].dt.date <= end_dt)
)
filtered_df = df[mask]

# Visualization
if not filtered_df.empty:
    plot_df = filtered_df.sort_values('snapshot_date')
    
    fig = px.line(
        plot_df, 
        x='snapshot_date', 
        y='total_data_center_count', 
        title=f"Total Data Centers in {selected_county} County, {selected_state}",
        markers=True,
        labels={'snapshot_date': 'Date', 'total_data_center_count': 'Total Data Centers'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Show raw filtered data
    with st.expander("View Raw Data"):
        st.dataframe(filtered_df, use_container_width=True)
else:
    st.warning("No data found for the selected filter combination.")