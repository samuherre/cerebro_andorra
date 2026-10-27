import os
import time
import requests

# URLs base de la API oficial de Andorra
BASE_URL = "https://sig.govern.ad/Sigdde.Public/estadistiquesdades/api"

# Directorio de salida para los datos crudos
OUTPUT_DIR = "../datos_crudos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lista selectiva de los indicadores maestros que SÍ le importan a tu panel
# (Aquí definimos explícitamente qué queremos descargar para no saturar el disco)
INDICADORES_MAESTROS = [
    {
        "idDivision": 798,
        "nombre": "poblacion_total",
        "descripcion": "Población total histórica",
    },
    {
        "idDivision": 820,
        "nombre": "transacciones_inmobiliarias",
        "descripcion": "Estadística de transacciones inmobiliarias",
    },
    {
        "idDivision": 850,
        "nombre": "turismo_visitantes",
        "descripcion": "Entrada de visitantes y vehículos por frontera",
    },
    {
        "idDivision": 810,
        "nombre": "indicadores_economicos",
        "descripcion": "Indicadores macroeconómicos y empleo",
    },
]


def descargar_indicador_clave(
    id_division, nombre_archivo_base, start_date="2020", end_date="2025"
):
  """Descarga de forma individual un indicador oficial específico asegurando

  el respeto a las restricciones de la API.
  """
  url_data = f"{BASE_URL}/data"
  params_data = {
      "idDivision": id_division,
      "startDate": start_date,
      "endDate": end_date,
      "file": "csv",
      "language": "ca",
  }

  print(
      f"Descargando indicador ID {id_division} ({nombre_archivo_base})..."
  )
  response_data = requests.get(url_data, params=params_data)

  if response_data.status_code == 200:
    nombre_archivo = os.path.join(
        OUTPUT_DIR, f"oficial_{id_division}_{nombre_archivo_base}.csv"
    )
    with open(nombre_archivo, "wb") as f:
      f.write(response_data.content)
    print(f"   ✓ Guardado exitosamente en: {nombre_archivo}")
    return True
  elif response_data.status_code == 429:
    print("   ⚠ Límite de peticiones alcanzado (429). Esperando...")
    time.sleep(30)
    return False
  else:
    print(
        f"   ✖ Error al descargar ID {id_division} (Código:"
        f" {response_data.status_code}). Es posible que el ID de prueba deba"
        " ajustarse."
    )
    return False


if __name__ == "__main__":
  print("--- Iniciando ingesta selectiva y limpia para el Lakehouse ---")

  for indicador in INDICADORES_MAESTROS:
    exito = descargar_indicador_clave(
        id_division=indicador["idDivision"],
        nombre_archivo_base=indicador["nombre"],
        start_date="2020",
        end_date="2025",
    )

    # Pausa de cortesía obligatoria para cumplir la regla de 5 peticiones por minuto
    print(
        "Pausa de cortesía de 12 segundos para respetar el límite de la API..."
    )
    time.sleep(12)

  print(
      "\n¡Proceso selectivo finalizado! Revisa tu carpeta 'datos_crudos/'."
      " Deberías tener exactamente los archivos clave."
  )