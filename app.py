import streamlit as st
import requests
import pandas as pd
from geopy.geocoders import Nominatim

def get_soil_data_final(address):
    try:
        # 1. Geocoding
        geolocator = Nominatim(user_agent="bodencheck_nrw_2026")
        location = geolocator.geocode(address + ", NRW")
        if not location:
            return None, "Adresse nicht gefunden."
        
        lat, lon = location.latitude, location.longitude
        
        # 2. Die funktionierende URL aus deinem Test
        url = "https://www.wms.nrw.de/gd/bk050"
        
        # Parameter für die Abfrage (GetFeatureInfo)
        # Wir nutzen 'is_m_layer', da dieser im Test funktioniert hat
        params = {
            "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
            "LAYERS": "is_m_layer", "QUERY_LAYERS": "is_m_layer",
            "I": 50, "J": 50, "WIDTH": 100, "HEIGHT": 100, "CRS": "EPSG:4326",
            "BBOX": f"{lat-0.001},{lon-0.001},{lat+0.001},{lon+0.001}",
            "INFO_FORMAT": "text/html" # Wir holen HTML, da JSON nicht unterstützt wird
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if "Boden" not in response.text and "bk050" not in response.text:
            return None, "Keine Bodendaten an dieser Position gefunden."

        # 3. HTML-Tabelle in Daten umwandeln
        # Wir nutzen pandas, um die Tabelle aus dem HTML-Text zu ziehen
        tables = pd.read_html(response.text)
        if tables:
            df = tables[0] # Die erste Tabelle enthält die Daten
            # Wir wandeln die Tabelle in ein Wörterbuch um (Spalte 0 = Name, Spalte 1 = Wert)
            data_dict = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
            return data_dict, None
        
        return None, "Daten konnten nicht gelesen werden."

    except Exception as e:
        return None, f"Technischer Fehler: {str(e)}"

# --- STREAMLIT UI ---
st.title("Bodencheck NRW - Finaler Zugriff")
addr = st.text_input("Adresse in NRW eingeben:", "De-Greiff-Straße 195, Krefeld")

if st.button("Boden analysieren"):
    data, error = get_soil_data_final(addr)
    if error:
        st.error(error)
    else:
        st.success("Daten erfolgreich vom GD NRW empfangen!")
        st.table(pd.DataFrame(data.items(), columns=["Eigenschaft", "Wert"]))
