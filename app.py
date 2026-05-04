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
        # 1. Geocoding: Adresse in Koordinaten (Lat, Lon) wandeln
        geolocator = Nominatim(user_agent="boden_check_nrw_pro")
        location = geolocator.geocode(address + ", NRW")
        if not location: 
            return None, "Adresse konnte nicht gefunden werden. Bitte genauer eingeben."
        
        lat, lon = location.latitude, location.longitude
        
        # 2. WFS-Verbindung zum neuen GeoServer NRW
        # Wir nutzen den stabilsten Einstiegspunkt
        wfs_url = "https://www.geoserver.nrw.de/geoserver/gd/wfs"
        wfs = WebFeatureService(url=wfs_url, version='2.0.0')
        
        # Der Layer für die Bodenkarte 1:50.000 (BK50)
        layer_name = 'gd:bk050_bodeneinheiten'
        
        # 3. Die "Punkt-Abfrage": Wir bauen ein winziges Fenster (BBox) um unsere Koordinate
        # Der Server liefert uns dann die Daten für diesen "Piekser"
        try:
            response = wfs.getfeature(
                typename=layer_name,
                bbox=(lat-0.0001, lon-0.0001, lat+0.0001, lon+0.0001),
                outputFormat='application/json'
            )
            
            import json
            data = json.loads(response.read())
        except:
            # Falls JSON fehlschlägt, versuchen wir das Standardformat (GML)
            return None, "Der Server antwortet gerade nicht im richtigen Datenformat. Später erneut versuchen."

        # 4. Daten-Extraktion
        if not data.get('features') or len(data['features']) == 0:
            return None, "An dieser Stelle liegen keine Bodendaten vor (evtl. bebautes/versiegeltes Gebiet)."
            
        # Wir nehmen das erste Feature, das an diesem Punkt gefunden wurde
        props = data['features'][0]['properties']
        return props, None
        
    except Exception as e:
        return None, f"Fehler bei der Datenabfrage: {str(e)}"

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
