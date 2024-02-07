
import time
import pprint
import pandas as pd
import streamlit as st
from geopy.geocoders import Photon
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
                       "About": ("This is a simple app to predict the arrival of spring in Norway. " 
                                 "It is based on the work of the Norwegian Meteorological Institute.")
                   }
)

# Load prediction data with caching
@st.cache_data
def load_data():
    df_predictions = pd.read_json("data/predictions.json")
    return df_predictions
df_predictions = load_data()

# Front Page Title
st.title("⛅ Når kommer våren? ⛅")
st.write(("Velkommen til vår lille app for å forutsi når våren kommer til Norge på forskjellige lokasjoner. " 
         "Vi tar ikke noe ansvar for at prediksjonene er riktige, men håper at det kan skape en dialog rundt "
         "utfordringer med analyse av værdata. Vi har basert oss på data fra Meteorologisk institutt. Hvis du "
         "er uenig i prediksjonen for ditt område, send gjerne inn en klage til hei@alv.no."))
st.divider()

# Choose location in Norway
st.header("🌍 Velg lokasjon i Norge")
geolocator = Photon(user_agent="streamlit_app")
st.markdown("""
    <style>
    input[type=text] {
        color: #061838;
    }
    </style>
    """, unsafe_allow_html=True
)

# Get location input from user
location_input = st.text_input("Skriv inn lokasjonen i **Norge** du ønsker å sjekke her:")
if location_input:
    while True:
        
        # Get location data from geopy API
        try:
            location = geolocator.geocode(location_input)
        except ValueError or GeocoderUnavailable or GeocoderTimedOut:
            continue
        
        # Sleep for 1 second to avoid geocoding API rate limits
        time.sleep(1)
        
        # If location is in Norway
        if location and location.raw["properties"]["countrycode"] == "NO":
            st.write(f"Latitude: {location.latitude}, Longitude: {location.longitude}")
            location_data = {"location": location,
                             "latitude": location.latitude,
                             "longitude": location.longitude}
            df = pd.DataFrame.from_dict(location_data, orient="columns")
            st.map(df)
            break
        
        # If location is not in Norway
        elif location and location.raw["properties"]["countrycode"] != "NO":
            st.write("Lokasjon ikke funnet i Norge. Prøv igjen.")
            break
        
        # If location is not found
        else:
            st.write("Lokasjon ikke funnet.")
            break

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

def day_of_year_to_date(day_of_year, year):
    return pd.to_datetime(f"{year}-01-01") + pd.DateOffset(days=day_of_year-1)

# Display predictions for the closest location
#st.header("📅 Prediksjoner for våren nær din lokasjon")
try:
    if location and location.raw["properties"]["countrycode"] == "NO":
        current_location = (location.latitude, location.longitude)
        closest_id = get_closest_location_id(current_location, df_predictions)
        df_output = df_predictions[df_predictions["id"] == closest_id]
        year = df_output["year"].values[0]
        spring_start = df_output["spring_start"].values[0]
        
        date_of_spring = day_of_year_to_date(spring_start, year).strftime("%d. %B %Y")

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
            
        # Display date for spring arrival
        st.header(f"🌸 Vårens ankomst: {date_of_spring}")
except NameError:
    st.write("Du har ikke skrevet inn noen lokasjon ovenfor!")
    pass

st.divider()