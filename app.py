
import time
import re
import pprint
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Print configuration
pp = pprint.PrettyPrinter(indent=4)

# Page configuration
st.set_page_config(page_title="Når kommer våren?",
                   page_icon="⛅",
                   layout="centered", # wide, centered, or sidebar
                   initial_sidebar_state="auto", # auto, expanded, collapsed
                   menu_items={
                       "Get Help": "https://alv.no/",
                       "Report a bug": "mailto:hakon@alv.no",
                       "About": ("This is a simple app to predict the arrival of spring in Norway. ")
                   }
)

# Get closest location ID that compares the current_loction to the dataframe
def get_closest_location_id(current_location, df):
    closest_distance = None
    closest_id = None

    for _, row in df.iterrows():
        location = (row['latitude'], row['longitude'])
        distance = great_circle(current_location, location).miles

        if closest_distance is None or distance < closest_distance:
            closest_distance = distance
            closest_id = row["id"]

    return closest_id

# Get date from day of year
def day_of_year_to_date(day_of_year, year):
    return pd.to_datetime(f"{year}-01-01") + pd.DateOffset(days=day_of_year-1)

def date_to_date_norwegian(date_of_spring):
        english_to_norwegian_months_mapping = {
            "January": "Januar",
            "February": "Februar",
            "March": "Mars",
            "April": "April",
            "May": "Mai",
            "June": "Juni",
            "July": "Juli",
            "August": "August",
            "September": "September",
            "October": "Oktober",
            "November": "November",
            "December": "Desember"
        }

        # Replace date_of_spring with Norwegian month names
        for english, norwegian in english_to_norwegian_months_mapping.items():
            date_of_spring = date_of_spring.replace(english, norwegian)
        
        # Convert day of month from (01, 02, 03, ..) to (1, 2, 3, ..)
        day_of_month = str(int(date_of_spring.split(".")[0]))
        added_date_text = date_of_spring.split(".")[1]
        date_of_spring = day_of_month + "." + added_date_text
        
        return date_of_spring

# Load prediction data with caching
@st.cache_data
def load_data():
    df_predictions = pd.read_json("data/predictions.json")
    return df_predictions
df_predictions = load_data()

# Front Page Title
st.title("⛅ Når kommer våren? ⛅")
st.write(("Velkommen til vår lille app for å forutsi når våren kommer til Norge på forskjellige lokasjoner. "))
st.divider()

# Choose location in Norway
st.header("🌍 Velg lokasjon i Norge")
st.markdown("""
    <style>
    input[type=text] {
        color: #061838;
    }
    input[type=text]:focus {
        caret-color: #061838;
        background-color: lightyellow;
    }
    </style>
    """, unsafe_allow_html=True
)

# Get location input from user
location_input = st.text_input("Skriv inn lokasjonen i **Norge** du ønsker å sjekke her (og trykk enter):")
geolocator = Nominatim(user_agent="streamlit_app")
if location_input:
    with st.spinner("Processing ..."):
        while True:
            
            # Get location data from geopy API
            try:
                location = geolocator.geocode(location_input, exactly_one=True, language="en", namedetails=True, addressdetails=True)
            except ValueError or GeocoderUnavailable or GeocoderTimedOut:
                time.sleep(1)
                continue
            
            # Sleep for 1 second to avoid geocoding API rate limits
            time.sleep(1)
            
            # If location is in Norway
            if location and location.raw["address"]["country_code"] == "no":
                api_location = (location.latitude, location.longitude)
                api_location_name = location.raw["name"]
                print(f"API location name: {api_location_name}")
                print(f"API location: {api_location}")
            
                # Get matching data if input equals prediction data
                df_predictions_lower = df_predictions.copy()
                location_input_lower = location_input.lower()
                df_predictions_lower["name"] = df_predictions["name"].str.lower()
                matching_rows = df_predictions_lower[df_predictions_lower["name"] == location_input_lower]
                
                # Use location from predictions if name is found in data
                if not matching_rows.empty:
                    map_latitude = matching_rows["latitude"].values[0]
                    map_longitude = matching_rows["longitude"].values[0]
                    map_location = (map_latitude, map_longitude)
                    
                # Use location from API if name is not found
                else:
                    map_location = api_location
                
                # Display map with location
                location_data = {"location":  map_location,
                                 "latitude":  map_location[0],
                                 "longitude": map_location[1]}
                df = pd.DataFrame.from_dict(location_data, orient="columns")
                st.map(df)
                break
            
            # If location is not in Norway
            elif location and location.raw["address"]["country_code"] != "no":
                st.write("Lokasjon ikke funnet i Norge. Prøv igjen.")
                break
            
            # If location is not found
            else:
                st.write("Lokasjon ikke funnet.")
                break

# Display predictions for the closest location
#st.header("📅 Prediksjoner for våren nær din lokasjon")
try:
    # Location is in Norway
    if location and location.raw["address"]["country_code"] == "no":
        
        # Get dataframe containing nearest location that is predicted spring for
        current_location = (location.latitude, location.longitude)
        closest_id = get_closest_location_id(current_location, df_predictions)
        df_output = df_predictions[df_predictions["id"] == closest_id]
        
        # Log prediction information
        pred_location_name = df_output["name"].values[0]
        pred_latitude = df_output["latitude"].values[0]
        pred_longitude = df_output["longitude"].values[0]
        pred_location = (pred_latitude, pred_longitude)
        print(f"Predicted location name: {pred_location_name}")
        print(f"Predicted location: {pred_location}")
        
        # Extract prediction values
        year = df_output["year"].values[0]
        spring_start = df_output["spring_start"].values[0]
        sprint_start_lower = df_output["spring_start_lower"].values[0]
        sprint_start_upper = df_output["spring_start_upper"].values[0]
        
        # Get date from day of year
        date_of_spring_start = day_of_year_to_date(spring_start, year).strftime("%d. %B %Y")
        date_of_spring_start_lower = day_of_year_to_date(sprint_start_lower, year).strftime("%d. %B %Y")
        date_of_spring_start_upper = day_of_year_to_date(sprint_start_upper, year).strftime("%d. %B %Y")
        
        # Transform to Norwegian date format
        date_of_spring_start = date_to_date_norwegian(date_of_spring_start)
        date_of_spring_start_lower_without_year = re.sub(r' \b\d{4}\b', '', date_to_date_norwegian(date_of_spring_start_lower))
        date_of_spring_start_upper_without_year = re.sub(r' \b\d{4}\b', '', date_to_date_norwegian(date_of_spring_start_upper))
        
        # Display date for spring arrival
        st.header(f"🌸 Vårens ankomst: {date_of_spring_start}")
        st.write("Helt sikkerhet vil våren komme mellom {} og {}.".format(date_of_spring_start_lower_without_year, date_of_spring_start_upper_without_year))
except NameError:
    st.write("Du har ikke skrevet inn noen lokasjon ovenfor!")
    pass

st.divider()