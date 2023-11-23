# Equipo 4

import os
import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
import pydeck as pdk

# SETTING PAGE CONFIG TO WIDE MODE AND ADDING A TITLE AND FAVICON
st.set_page_config(layout="wide", page_title="SF Incidents Dashboard", page_icon=":oncoming_police_car:")

# LOAD DATA ONCE
@st.cache_resource
def load_data():
    path = "Police_Department_Incident_Reports__2018_to_Present.csv.zip"
    if not os.path.isfile(path):
        path = f"https://github.com/marisa-valencia/DataAnalysisAdanClass/blob/main//{path}"

    data = pd.read_csv(
        path,
        nrows=100000,  # adjust as needed
        usecols=["Incident Datetime", "Latitude", "Longitude"],  # adjust as needed
        parse_dates=["Incident Datetime"],
    )

    # Drop rows with missing values in "Latitude" and "Longitude" columns
    #data.dropna(subset=['Latitude', 'Longitude'], inplace=True)

    return data


# FUNCTION FOR INCIDENT MAPS
def map(data, Latitude, Longitude, zoom):
    st.write(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": Latitude,
                "longitude": Longitude,
                "zoom": zoom,
                "pitch": 50,
            },
            layers=[
                pdk.Layer(
                    "HexagonLayer",
                    data=data,
                    get_position=["Longitude", "Latitude"],
                    radius=100,
                    elevation_scale=4,
                    elevation_range=[0, 1000],
                    pickable=True,
                    extruded=True,
                ),
            ],
        )
    )

# FILTER DATA FOR A SPECIFIC HOUR, CACHE
@st.cache_data
def filterdata(df, hour_selected):
    df.dropna(subset=['Latitude'], inplace=True)
    df.dropna(subset=['Longitude'], inplace=True)
    return df[df["Incident Datetime"].dt.hour == hour_selected]


# CALCULATE MIDPOINT FOR GIVEN SET OF DATA
@st.cache_data
def mpoint(lat, lon):
    lat_numeric = pd.to_numeric(lat, errors="coerce")
    lon_numeric = pd.to_numeric(lon, errors="coerce")

    # Check if there are valid numeric values
    if not np.isnan(lat_numeric).all() and not np.isnan(lon_numeric).all():
        lat_avg = np.nanmean(lat_numeric)
        lon_avg = np.nanmean(lon_numeric)
        return (lat_avg, lon_avg)
    else:
        # Return a default location if no valid values are found
        return (37.7749, -122.4194)  # Default to San Francisco's coordinates


# FILTER DATA BY HOUR
@st.cache_data
def histdata(df, hr):
    filtered = df[
        (df["Incident Datetime"].dt.hour >= hr) & (df["Incident Datetime"].dt.hour < (hr + 1))
    ]

    hist = np.histogram(filtered["Incident Datetime"].dt.minute, bins=60, range=(0, 60))[0]

    return pd.DataFrame({"minute": range(60), "incidents": hist})

# STREAMLIT APP LAYOUT
data = load_data()

# LAYING OUT THE TOP SECTION OF THE APP
row1_1, row1_2 = st.columns((2, 3))

# SEE IF THERE'S A QUERY PARAM IN THE URL (e.g. ?incident_hour=2)
# THIS ALLOWS YOU TO PASS A STATEFUL URL TO SOMEONE WITH A SPECIFIC HOUR SELECTED,
# E.G. https://share.streamlit.io/streamlit/demo-sf-incidents/main?incident_hour=2
if not st.session_state.get("url_synced", False):
    try:
        incident_hour = int(st.experimental_get_query_params()["incident_hour"][0])
        st.session_state["incident_hour"] = incident_hour
        st.session_state["url_synced"] = True
    except KeyError:
        pass

# IF THE SLIDER CHANGES, UPDATE THE QUERY PARAM
def update_query_params():
    hour_selected = st.session_state["incident_hour"]
    st.experimental_set_query_params(incident_hour=hour_selected)

with row1_1:
    st.title("San Francisco's Incidents")
    hour_selected = st.slider(
        "Select hour of incident", 0, 23, key="incident_hour", on_change=update_query_params,
    )

with row1_2:
    st.write(
        """
    ##
    Exploring incidents in San Francisco over time.
    By adjusting the slider on the left, you can examine distinct time intervals, allowing you to investigate patterns and trends in reported incidents.
    """
    )

# LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS
row2_1, row2_2 = st.columns((6, 7))  # Increase the width of the map column

# SETTING THE ZOOM LOCATIONS FOR THE MAP
sf_midpoint = mpoint(data["Latitude"], data["Longitude"])
zoom_level = 12

with row2_1:
    st.write(
        f"""**All incidents in SF from {hour_selected}:00 to {(hour_selected + 1) % 24}:00**"""
    )
    #map(data, sf_midpoint[0], sf_midpoint[1], 11)
    map(filterdata(data, hour_selected), sf_midpoint[0], sf_midpoint[1], 11)

# Additional maps for specific locations can be added here using the 'map' function.

# CALCULATING DATA FOR THE HISTOGRAM
chart_data = histdata(data, hour_selected)

# LAYING OUT THE HISTOGRAM SECTION
with row2_2:
    st.write(
        f"""**Breakdown of incidents per minute between {hour_selected}:00 and {(hour_selected + 1) % 24}:00**"""
    )

    st.altair_chart(
        alt.Chart(chart_data)
        .mark_area(
            interpolate="step-after",
        )
        .encode(
            x=alt.X("minute:Q", scale=alt.Scale(nice=False)),
            y=alt.Y("incidents:Q"),
            tooltip=["minute", "incidents"],
        )
        .configure_mark(opacity=0.2, color="red"),
        use_container_width=True,
    )
