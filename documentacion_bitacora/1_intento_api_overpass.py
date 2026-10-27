import requests
import json
import os

# Asegurarnos de que la carpeta exista
if not os.path.exists('datos_crudos'):
    os.makedirs('datos_crudos')

query = """[out:json][timeout:90];
area["name"="Andorra la Vella"]->.andorra;
(
  way["building"](area.andorra);
  relation["building"](area.andorra);
);
out geom;"""

print("Descargando geometría de los edificios desde Overpass API...")

# Agregamos un User-Agent para identificarnos ante el servidor y evitar el bloqueo 406
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

try:
    r = requests.get(
        "https://overpass-api.de/api/interpreter",
        params={"data": query},
        headers=headers
    )
    
    r.raise_for_status() 
    
    data = r.json()
    
    ruta_archivo = "datos_crudos/edificios_andorra.json"
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"¡Éxito! El archivo se ha guardado correctamente en: {ruta_archivo}")

except requests.exceptions.HTTPError as err:
    print(f"Error HTTP: {err}")
    print("Detalle del servidor:", r.text)
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")