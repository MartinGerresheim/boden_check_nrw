import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from owslib.wfs import WebFeatureService

# --- KONFIGURATION & UI SETUP ---
st.set_page_config(page_title="Boden-Check NRW", page_icon="🚜", layout="centered")

st.title("🚜 Boden-Check NRW")
st.markdown("### Strategische Werkzeugwahl für Drainage-Projekte")
st.info("Dieses Tool nutzt Live-Daten des Geologischen Dienstes NRW.")

# --- SIDEBAR: ANTHROPOGENER FAKTOR ---
st.sidebar.header("Standort-Kontext")
baujahr_störung = st.sidebar.select_slider(
    "Zustand des Geländes (Baujahr/Eingriff)",
    options=["Altbau / Natürlich", "Bestand (10-30 J.)", "Neubau / Baustelle"],
    value="Altbau / Natürlich",
    help="Neubauten weisen oft starke Bodenverdichtungen durch Baumaschinen auf."
)

# Mapping der Störfaktoren
stör_faktor_map = {"Altbau / Natürlich": 1.0, "Bestand (10-30 J.)": 1.1, "Neubau / Baustelle": 1.3}
stör_faktor = stör_faktor_map[baujahr_störung]

# --- FUNKTIONEN ---
def get_soil_data(address):
    try:
        # 1. Geocoding
        geolocator = Nominatim(user_agent="boden_check_nrw_2026")
        location = geolocator.geocode(address + ", NRW")
        if not location: 
            return None, "Adresse nicht gefunden."
        
        lat, lon = location.latitude, location.longitude
        
        # 2. Die exakte URL, die das Geoportal NRW nutzt
        # Wir nutzen hier den OGC-Standard-Einstieg
        wfs_url = "https://www.wms.nrw.de/gd/bk050/wfs"
        
        wfs = WebFeatureService(url=wfs_url, version='2.0.0')
        
        # Layer-Name im WMS.NRW System
        layer_name = 'bk050:is_m_layer' 
        
        # 3. Abfrage
        response = wfs.getfeature(
            typename=layer_name,
            bbox=(lat-0.0005, lon-0.0005, lat+0.0005, lon+0.0005),
            outputFormat='json'
        )
        
        import json
        data = json.loads(response.read())
        
        if not data.get('features'):
            return None, "Keine Daten an diesem Punkt. (Evtl. versiegelte Fläche?)"
            
        return data['features'][0]['properties'], None
        
    except Exception as e:
        # Konstruktive Fehlermeldung
        return None, f"Verbindung zum NRW-Server fehlgeschlagen. Tipp: Später versuchen oder Bodenart manuell schätzen. (Details: {str(e)})"

# --- HAUPTPROGRAMM ---
address_input = st.text_input("Garten-Adresse eingeben:", placeholder="z.B. Königsallee 1, Düsseldorf")

if st.button("Analyse starten"):
    if address_input:
        with st.spinner("Analysiere Bodenschichten..."):
            props, error = get_soil_data(address_input)
            
            if error:
                st.error(error)
            else:
                # Extraktion der "Big Five" (vereinfacht für den Prototyp)
                bodenart = props.get('B_ART_OB', 'L') # Default Lehm falls unbekannt
                gw_stufe = props.get('GW_ST', '1')
                
                # --- MAPPING LOGIK ---
                if "L" in bodenart or "T" in bodenart:
                    basis_geraet = "Minibagger 1.5t - 1.8t"
                    klasse = "4-5"
                    basis_faktor = 1.5
                else:
                    basis_geraet = "Lochspaten / Handarbeit"
                    klasse = "3"
                    basis_faktor = 1.0
                
                finaler_faktor = round(basis_faktor * stör_faktor, 2)
                
                # --- AUSGABE ---
                st.success(f"### Empfohlenes Gerät: {basis_geraet}")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Bodenklasse", klasse)
                c2.metric("Erschwernis", f"x{finaler_faktor}")
                c3.metric("Grundwasser", "Fern" if gw_stufe == '1' else "Nah")
                
                # Detail-Tabelle
                st.write("#### Geologische Details (Rohdaten):")
                st.json({
                    "Bodenart (Code)": bodenart,
                    "Grundwasser-Stufe": gw_stufe,
                    "Beschreibung": props.get('BESCHREIBUNG', 'Keine Beschreibung verfügbar')
                })
                
                if stör_faktor > 1.0:
                    st.warning(f"Hinweis: Der Faktor wurde aufgrund der Auswahl '{baujahr_störung}' erhöht.")
    else:
        st.warning("Bitte geben Sie eine Adresse ein.")
