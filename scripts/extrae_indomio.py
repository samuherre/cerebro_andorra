import os
from bs4 import BeautifulSoup
import requests

# Directorio de salida para los datos crudos
OUTPUT_DIR = "../datos_crudos"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extraer_precios_indomio():
  # URL pública del mercado inmobiliario de Andorra en Indomio
  url = "https://www.indomio.es/en/mercado-inmobiliario/andorra/andorra-provincia/"

  # Headers mejorados para imitar a un navegador real y evitar el bloqueo 403
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
      ),
      "Connection": "keep-alive",
  }

  print(
      "Conectando con Indomio simulando ser un navegador web legítimo..."
  )
  response = requests.get(url, headers=headers)

  print(f"Código de estado HTTP recibido: {response.status_code}")

  if response.status_code != 200:
    print(
        f"El sitio web sigue bloqueando la petición automatizada (Código:"
        f" {response.status_code})."
    )
    print(
        "Esto es un hallazgo excelente para la bitácora: Las medidas anti-bot"
        " de los portales inmobiliarios dificultan el scraping directo."
    )
    return

  # Parsear el HTML de la página si el acceso fue exitoso
  soup = BeautifulSoup(response.text, "html.parser")
  print("¡Conexión exitosa a Indomio!")

  archivo_salida = os.path.join(OUTPUT_DIR, "indomio_mercado_inmobiliario.html")
  with open(archivo_salida, "w", encoding="utf-8") as f:
    f.write(response.text)

  print(f"Archivo espejo guardado correctamente en: {archivo_salida}")


if __name__ == "__main__":
  extraer_precios_indomio()