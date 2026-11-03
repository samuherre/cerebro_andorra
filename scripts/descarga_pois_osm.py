"""Extractor ético de Puntos de Interés (Transporte, Salud, Educación y Servicios) en OSM.

Consulta la API de Overpass (con mirrors de respaldo) para extraer en el
Principado de Andorra (bounding box 42.42,1.40,42.66,1.79) los nodos y recintos de:
- Transporte y movilidad (paradas de autobús, estaciones, teleféricos/remontes,
  aparcamientos, gasolineras, puntos de recarga).
- Salud y emergencias (hospitales, clínicas, farmacias, médicos, bomberos, policía).
- Educación y cultura (colegios, institutos, universidades, bibliotecas, museos).

Guarda el resultado crudo en ``../datos_crudos/pois_osm_andorra.json`` (licencia ODbL).
"""

import json
import os
import time

import requests

RUTA_SALIDA = "../datos_crudos/pois_osm_andorra.json"
MIRRORS_OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]

# Bounding box de Andorra: sur=42.42, oeste=1.40, norte=42.66, este=1.79
CONSULTA_OVERPASS = """[out:json][timeout:45][bbox:42.42,1.40,42.66,1.79];
(
  node["highway"="bus_stop"];
  nwr["amenity"~"bus_station|fuel|charging_station|parking|hospital|clinic|doctors|pharmacy|dentist|fire_station|police|school|college|university|library|townhall|courthouse|place_of_worship|recycling"];
  nwr["aerialway"];
  nwr["tourism"~"museum|hotel|guest_house"];
);
out center tags;
"""

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}


def main() -> int:
    if os.path.isfile(RUTA_SALIDA):
        print(f"El archivo '{RUTA_SALIDA}' ya existe; se omite descarga (idempotencia).")
        return 0

    for url in MIRRORS_OVERPASS:
        print(f"Consultando mirror de Overpass: {url} ...")
        try:
            resp = requests.post(
                url,
                data={"data": CONSULTA_OVERPASS},
                headers=HEADERS,
                timeout=45,
            )
            if resp.status_code == 200:
                datos = resp.json()
                os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
                with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
                    json.dump(datos, f, ensure_ascii=False)
                print(
                    f"[OK] Guardado '{RUTA_SALIDA}' con {len(datos.get('elements', []))} elementos."
                )
                return 0
            print(f"  [AVISO] HTTP {resp.status_code} desde {url}.")
        except Exception as err:
            print(f"  [AVISO] Error en {url}: {err}.")
        time.sleep(2)

    print(
        "No se pudo descargar desde ningún mirror de Overpass; el pipeline usará edificios_andorra.geojson."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
