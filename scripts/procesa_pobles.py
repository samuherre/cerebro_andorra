"""Procesamiento de población por poble (localidad/pueblo) de Andorra (tramo Lago).

Lee ``../datos_crudos/estadistica_id1096_població_població_per_poble.csv``
(formato ancho 2020-2025) y normaliza los 44 pueblos de Andorra a formato largo
en ``../datos_procesados/poblacion_poble.csv``, vinculando cada pueblo con su
parròquia canónica y anotando gobernanza completa (linaje OBSERVADO).
"""

import datetime
import re

import pandas as pd

import gobernanza
from procesa_poblacion import NOMBRES_CANONICOS

FUENTE_POBLES = "Departament d'Estadística d'Andorra (sig.govern.ad, id1096)"
RUTA_ENTRADA = "../datos_crudos/estadistica_id1096_població_població_per_poble.csv"
RUTA_SALIDA = "../datos_procesados/poblacion_poble.csv"

ANIOS_ESPERADOS = [2020, 2021, 2022, 2023, 2024, 2025]
COLUMNAS_SALIDA = [
    "poble",
    "parroquia",
    "anio",
    "poblacion",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]

# Expresión regular para extraer poble y parròquia de:
# "POBLACIÓ PER POBLE. <POBLE>. (<PARRÒQUIA>)"
_PATRON_POBLE = re.compile(
    r"^POBLACI[ÓO]\s+PER\s+POBLE\.\s*(.+?)\.\s*\((.+?)\)\s*$",
    re.IGNORECASE,
)


def extrae_poble_parroquia(descripcion: str) -> "tuple[str, str] | None":
    """Extrae el nombre del pueblo (en formato título) y la parròquia canónica."""
    if descripcion is None:
        return None
    coincidencia = _PATRON_POBLE.match(str(descripcion).strip())
    if not coincidencia:
        return None

    poble_crudo = coincidencia.group(1).strip()
    parroquia_cruda = coincidencia.group(2).strip().upper()
    mapa_parroquias = {
        **NOMBRES_CANONICOS,
        "SANT JULIÀ": "Sant Julià de Lòria",
        "SANT JULIA": "Sant Julià de Lòria",
    }
    parroquia_canonica = mapa_parroquias.get(parroquia_cruda)
    if not poble_crudo or parroquia_canonica is None:
        return None

    # Normalización legible del nombre del pueblo (conservando artículos catalanes)
    poble_limpio = " ".join(poble_crudo.split()).title()
    for art_mayus, art_minus in (
        (" D'", " d'"),
        (" De ", " de "),
        (" La ", " la "),
        (" El ", " el "),
        (" Els ", " els "),
        (" Les ", " les "),
    ):
        poble_limpio = poble_limpio.replace(art_mayus, art_minus)

    return poble_limpio, parroquia_canonica


def _a_entero(valor) -> "int | None":
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    try:
        numero = float(texto.replace(",", ""))
    except (ValueError, TypeError):
        return None
    if numero < 0 or numero != int(numero):
        return None
    return int(numero)


def procesa(fecha_prueba: str) -> None:
    """Lee el crudo de población por poble, lo normaliza y escribe el CSV gobernado."""
    print("[INICIO] Procesamiento de población por poble (localidades).")
    try:
        df = pd.read_csv(RUTA_ENTRADA, sep=";", encoding="utf-8")
    except Exception as error:
        print(f"[ERROR] No se pudo leer '{RUTA_ENTRADA}': {error}.")
        gobernanza.escribe_csv([], RUTA_SALIDA, COLUMNAS_SALIDA)
        return

    registros: list[dict] = []
    for indice, fila in df.iterrows():
        extraido = extrae_poble_parroquia(fila.get("Descripció"))
        if extraido is None:
            print(
                f"[AVISO] Fila {indice} omitida en pobles: descripción no reconocida "
                f"('{fila.get('Descripció')}')."
            )
            continue

        poble, parroquia = extraido
        for anio in ANIOS_ESPERADOS:
            col = str(anio) if str(anio) in df.columns else anio
            if col not in df.columns:
                continue
            poblacion = _a_entero(fila[col])
            if poblacion is None:
                continue
            registros.append(
                {
                    "poble": poble,
                    "parroquia": parroquia,
                    "anio": int(anio),
                    "poblacion": poblacion,
                    "fuente": FUENTE_POBLES,
                    "vigencia": str(anio),
                    "fecha_prueba": fecha_prueba,
                    "linaje": gobernanza.LINAJE_OBSERVADO,
                }
            )

    validos = gobernanza.filtra_registros_validos(registros, "poblacion_poble")
    gobernanza.escribe_csv(validos, RUTA_SALIDA, COLUMNAS_SALIDA)
    print(
        f"[FIN] Población por poble completada: {len(validos)} registros en '{RUTA_SALIDA}'."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
