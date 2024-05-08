import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import folium_static
import pygame

# Load data
@st.cache
def load_data():
    df = pd.read_excel(r'C:\streamlitDashboard\requests.xlsx')
    return df

# Set page configuration to wide
st.set_page_config(layout="wide")

# Load data
df = load_data()

# Add Filters
st.sidebar.title('Filters')
selected_city = st.sidebar.selectbox('Select City', ['All'] + sorted(df['CITY'].unique(), key=str))
selected_vehicle_type = st.sidebar.selectbox('Select Vehicle Type', ['All'] + sorted(df['VEHICLETYPE'].astype(str).unique()))
selected_date_from = st.sidebar.date_input('Select Date From')
selected_date_to = st.sidebar.date_input('Select Date To')
selected_driver = st.sidebar.selectbox('Select Driver', ['All'] + sorted(df['DRIVER'].astype(str).unique()))
selected_trip_type = st.sidebar.selectbox('Select Trip Type', ['All'] + sorted(df['TRIPTYPE'].astype(str).unique()))
selected_rider = st.sidebar.selectbox('Select Rider', ['All'] + sorted(df['Rider Mobile Number'].astype(str).unique()))
selected_country = st.sidebar.selectbox('Select Country', ['All'] + sorted(df['COUNTRY'].astype(str).unique()))

# Convert selected dates to Pandas datetime objects
selected_date_from = pd.Timestamp(selected_date_from)
selected_date_to = pd.Timestamp(selected_date_to)

# Apply Filters
filtered_df = df[
    ((df['CITY'] == selected_city) | (selected_city == 'All')) &
    ((df['VEHICLETYPE'] == selected_vehicle_type) | (selected_vehicle_type == 'All')) &
    ((df['Date'] >= selected_date_from) & (df['Date'] <= selected_date_to)) &
    ((df['DRIVER'] == selected_driver) | (selected_driver == 'All')) &
    ((df['TRIPTYPE'] == selected_trip_type) | (selected_trip_type == 'All')) &
    ((df['Rider Mobile Number'].astype(str) == selected_rider) | (selected_rider == 'All')) &
    ((df['COUNTRY'] == selected_country) | (selected_country == 'All'))
]

# Drop rows with NaN values in Latitude and Longitude columns
filtered_df = filtered_df.dropna(subset=['Latitude', 'Longitude'])

# Calculate KPIs for filtered data
total_requests = len(filtered_df)
total_trips = filtered_df[filtered_df['Category'] == 'Trips'].shape[0]
driver_cancellations = filtered_df[filtered_df['Category'] == 'Driver Cancellation'].shape[0]
rider_cancellations = filtered_df[filtered_df['Category'] == 'Rider Cancellation'].shape[0]
no_driver_found = filtered_df[filtered_df['Category'] == 'No Drivers Found'].shape[0]
timeouts = filtered_df[filtered_df['Category'] == 'Timeout'].shape[0]

# Check if total_trips is zero to avoid division by zero
if total_trips == 0:
    fulfillment_rate = 0
    acceptance_rate = 0
    driver_canc_rate = 0
else:
    fulfillment_rate = round((total_trips * 100) / (total_trips + driver_cancellations + rider_cancellations), 2)
    acceptance_rate = round((total_trips * 100) / (total_trips + driver_cancellations + rider_cancellations + timeouts), 2)
    driver_canc_rate = round((driver_cancellations * 100) / (total_trips + driver_cancellations + rider_cancellations + timeouts), 2)

# Title of the dashboard
st.title('Requests Dashboard')

# KPIs Section
st.write('## KPIs')

# Define KPIs
kpi_data = {
    'Total Requests': total_requests,
    'Total Trips': total_trips,
    'Driver Cancellations': driver_cancellations,
    'Rider Cancellations': rider_cancellations,
    'Timeouts': timeouts,
    'No Driver Found Cases': no_driver_found,
    'Fulfillment Rate (%)': fulfillment_rate,
    'Acceptance Rate (%)': acceptance_rate,
    'Driver Cancellation Rate (%)': driver_canc_rate
}

# CSS styles for the box
box_style = """
    background-color: #007bff;
    color: white;
    padding: 30px;
    border-radius: 5px;
    margin-bottom: 10px;
    font-size: 22px;
"""

# Arrange KPIs in a 3x3 grid
col1, col2, col3 = st.columns(3)

# Display KPIs in each column with styled boxes
with col1:
    for kpi_name, kpi_value in kpi_data.items():
        if kpi_name in ['Total Requests', 'Total Trips', 'Driver Cancellations']:
            st.markdown(f'<div style="{box_style}">{kpi_name}: {kpi_value}</div>', unsafe_allow_html=True)

with col2:
    for kpi_name, kpi_value in kpi_data.items():
        if kpi_name in ['Rider Cancellations', 'Timeouts', 'No Driver Found Cases']:
            st.markdown(f'<div style="{box_style}">{kpi_name}: {kpi_value}</div>', unsafe_allow_html=True)

with col3:
    for kpi_name, kpi_value in kpi_data.items():
        if kpi_name in ['Fulfillment Rate (%)', 'Acceptance Rate (%)', 'Driver Cancellation Rate (%)']:
            st.markdown(f'<div style="{box_style}">{kpi_name}: {kpi_value}</div>', unsafe_allow_html=True)


# Display filtered data
st.write('## Filtered Raw Data')
# Display the DataFrame without styling
st.write(filtered_df)

# Data Visualization
st.write('## Data Visualization')

# Aggregate data by vehicle type and date
request_count_by_date = filtered_df.groupby(['VEHICLETYPE', 'Date']).size().reset_index(name='count')

# Create a line chart using Altair with smooth lines
chart1 = alt.Chart(request_count_by_date).mark_line(interpolate='basis').encode(
    x=alt.X('Date:T', axis=alt.Axis(format='%Y-%m-%d'), title='Date'),
    y=alt.Y('count:Q', axis=alt.Axis(title='Request Count')),
    color='VEHICLETYPE:N',
    tooltip=['Date', 'count']
).properties(
    width=1400,
    height=400,
    title='Request Count by Vehicle Type Over Time'
).interactive()

# Render the chart
st.altair_chart(chart1)

# Aggregate data by Category and Hour
request_count_by_hour = filtered_df.groupby(['Category', 'Hour']).size().reset_index(name='count')

# Create a line chart using Altair with smooth lines
chart2 = alt.Chart(request_count_by_hour).mark_line(interpolate='basis').encode(
    x=alt.X('Hour:O', title='Hour'),
    y=alt.Y('count:Q', axis=alt.Axis(title='Request Count')),
    color='Category:N',
    tooltip=['Hour', 'count']
).properties(
    width=1400,
    height=400,
    title='Request Count by Category Over Hour'
).interactive()

# Render the chart
st.altair_chart(chart2)

# Display map chart of requests
st.write('## Heat Map of Requests')

# Filter out rows with missing latitude or longitude values
filtered_df = filtered_df.dropna(subset=['Latitude', 'Longitude'])

# Rename columns to match expected names for latitude and longitude
filtered_df = filtered_df.rename(columns={'Latitude': 'LAT', 'Longitude': 'LON'})

# Display map with points representing requests
st.map(filtered_df)

# Display filtered data
st.write('## Driver Data Table')

# Filter out 'No Drivers Found' from the total requests
filtered_df = filtered_df[filtered_df['Category'] != 'No Drivers Found']

# Calculate total requests per driver
driver_requests = filtered_df.groupby('DRIVER').size().reset_index(name='Total Requests')

# Filter out 'Trips' from the filtered DataFrame
filtered_df_trips = filtered_df[filtered_df['Category'] == 'Trips']

# Group data by driver and calculate total trips
driver_trips = filtered_df_trips.groupby('DRIVER').size().reset_index(name='Total Trips')

# Merge total requests and total trips tables on DRIVER column
driver_kpis = pd.merge(driver_requests, driver_trips, on='DRIVER', how='left')

# Filter out 'Driver Cancellation' from the filtered DataFrame
filtered_df_driver_cancellations = filtered_df[filtered_df['Category'] == 'Driver Cancellation']

# Group data by driver and calculate total driver cancellations
driver_cancellations = filtered_df_driver_cancellations.groupby('DRIVER').size().reset_index(name='Driver Cancellation')

# Merge total requests, total trips, and total driver cancellations tables on DRIVER column
driver_kpis = pd.merge(driver_kpis, driver_cancellations, on='DRIVER', how='left')

# Filter out 'Rider Cancellation' from the filtered DataFrame
filtered_df_rider_cancellations = filtered_df[filtered_df['Category'] == 'Rider Cancellation']

# Group data by driver and calculate total rider cancellations
rider_cancellations = filtered_df_rider_cancellations.groupby('DRIVER').size().reset_index(name='Rider Cancellation')

# Merge total requests, total trips, and total rider cancellations tables on DRIVER column
driver_kpis = pd.merge(driver_kpis, rider_cancellations, on='DRIVER', how='left')

# Filter out 'Timeouts' from the filtered DataFrame
filtered_df_timeouts = filtered_df[filtered_df['Category'] == 'Timeout']

# Group data by driver and calculate total timeouts
timeouts = filtered_df_timeouts.groupby('DRIVER').size().reset_index(name='Timeout')

# Merge total requests, total trips, and total timeouts tables on DRIVER column
driver_kpis = pd.merge(driver_kpis, timeouts, on='DRIVER', how='left')

# Fill NaN values with 0
driver_kpis.fillna(0, inplace=True)

# Calculate Fulfillment Rate
driver_kpis['Fulfillment Rate (%)'] = (driver_kpis['Total Trips'] / (driver_kpis['Total Trips'] + driver_kpis['Driver Cancellation'] + driver_kpis['Rider Cancellation'])) * 100

# Calculate Acceptance Rate
driver_kpis['Acceptance Rate (%)'] = (driver_kpis['Total Trips'] / (driver_kpis['Total Trips'] + driver_kpis['Driver Cancellation'] + driver_kpis['Rider Cancellation']+ driver_kpis['Timeout'])) * 100

# Calculate Driver Cancellation Rate
driver_kpis['Driver Cancellation Rate (%)'] = (driver_kpis['Driver Cancellation'] / (driver_kpis['Total Requests'])) * 100

# Calculate Rider Cancellation Rate
driver_kpis['Rider Cancellation (%)'] = (driver_kpis['Rider Cancellation'] / (driver_kpis['Total Requests'])) * 100

# Calculate Timeout Rate
driver_kpis['Timeout Rate (%)'] = (driver_kpis['Timeout'] / (driver_kpis['Total Requests'])) * 100

# Display the table
st.write(driver_kpis)





