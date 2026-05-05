import requests
from owslib.wfs import WebFeatureService
import json

# TEST-SETUP: Geologischer Dienst NRW, Krefeld
LAT, LON = 51.346, 6.585 

targets = [
    {"name": "Ziel A (GeoServer)", "url": "https://www.geoserver.nrw.de/geoserver/gd/wfs", "layer": "gd:bk050_bodeneinheiten", "type": "WFS"},
    {"name": "Ziel B (Legacy)", "url": "https://www.wms.nrw.de/gd/bk050/wfs", "layer": "bk050:is_m_layer", "type": "WFS"},
    {"name": "Ziel C (GetFeatureInfo)", "url": "https://www.wms.nrw.de/gd/bk050", "type": "WMS_INFO"}
]

print(f"--- STARTE DIAGNOSE FÜR KOORDINATEN: {LAT}, {LON} ---\n")

for t in targets:
    print(f"Prüfe {t['name']}...")
    try:
        if t["type"] == "WMS_INFO":
            params = {
                "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
                "LAYERS": "is_m_layer", "QUERY_LAYERS": "is_m_layer",
                "I": 50, "J": 50, "WIDTH": 100, "HEIGHT": 100, "CRS": "EPSG:4326",
                "BBOX": f"{LAT-0.001},{LON-0.001},{LAT+0.001},{LON+0.001}",
                "INFO_FORMAT": "application/json"
            }
            r = requests.get(t["url"], params=params, timeout=15)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                print("ERFOLG: Daten empfangen.")
                print(json.dumps(r.json(), indent=2)[:500] + "...")
        else:
            wfs = WebFeatureService(url=t["url"], version='2.0.0')
            print(f"Verbindung steht: {wfs.identification.title}")
            feat = wfs.getfeature(typename=t["layer"], bbox=(LAT-0.001, LON-0.001, LAT+0.001, LON+0.001), outputFormat='json')
            print("ERFOLG: WFS-Daten geladen.")
    except Exception as e:
        print(f"FEHLER: {e}")
    print("-" * 30)
