import streamlit as st
import requests
import pandas as pd
from geopy.geocoders import Nominatim
import io

def get_soil_data_nrw(address):
    try:
        # 1. Geocoding: Adresse in Koordinaten umwandeln
        geolocator = Nominatim(user_agent="nrw_soil_checker_2026")
        location = geolocator.geocode(address + ", NRW")
        if not location:
            return None, "Adresse in NRW nicht gefunden."
        
        lat, lon = location.latitude, location.longitude

        # 2. WMS Parameter vorbereiten (Wir simulieren einen GIS-Klick)
        # Wir definieren eine winzige Box (BBOX) um deine Koordinaten
        delta = 0.0001
        bbox = f"{lat-delta},{lon-delta},{lat+delta},{lon+delta}"
        
        url = "https://www.wms.nrw.de/gd/bk050"
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": "is_m_layer",
            "QUERY_LAYERS": "is_m_layer",
            "I": "50", "J": "50", # Simulation Klick in die Mitte eines 100x100 Bildes
            "WIDTH": "100", "HEIGHT": "100",
            "CRS": "EPSG:4326",
            "BBOX": bbox,
            "INFO_FORMAT": "text/html", # Der Server liefert nur HTML
            "WITH_GEOMETRY": "false"
        }

        # 3. Anfrage mit "Tarnung" (Header)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://www.geoportal.nrw/"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None, f"Server meldet Fehler: {response.status_code}"

        # 4. Daten-Extraktion (Aus HTML zu Tabelle)
        if "FeatureInfo" in response.text or "table" in response.text:
            # Wir füttern den HTML-String direkt in Pandas
            tables = pd.read_html(io.StringIO(response.text))
            if tables:
                df = tables[0]
                # Bereinigung: Falls die Tabelle Namen/Werte Spalten hat
                return df, None
        
        return None, "Keine Bodendaten an dieser exakten Position gefunden."

    except Exception as e:
        return None, f"Fehler bei der Abfrage: {str(e)}"

# --- Streamlit Interface ---
st.title("Profi-Bodencheck NRW")
st.write("Abfrage der Bodenkarte 1:50.000 via WMS-Schnittstelle")

user_address = st.text_input("Adresse eingeben (z.B. De-Greiff-Str. 195, Krefeld):")

if st.button("Daten abrufen"):
    with st.spinner("Frage Geologischen Dienst NRW ab..."):
        data, error = get_soil_data_nrw(user_address)
        
        if error:
            st.error(error)
        else:
            st.success("Daten erfolgreich empfangen!")
            st.dataframe(data) # Zeigt die extrahierte Tabelle an
