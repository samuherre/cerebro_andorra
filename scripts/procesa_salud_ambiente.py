"""Procesamiento de Salud, Educación, Conectividad, Energía y Medio Ambiente (tramo Lago).

Lee los archivos ``../datos_crudos/worldbank_<codigo>.json`` de los indicadores
sectoriales del Banco Mundial y genera la tabla gobernada
``../datos_procesados/salud_educacion_ambiente.csv`` (linaje OBSERVADO,
licencia CC BY 4.0).
"""

import datetime

import gobernanza
import procesa_economia
from descarga_salud_ambiente_wb import INDICADORES_SECTORIALES

FUENTE_WB_SECTORIAL = "Banco Mundial (World Bank Open Data, API v2)"
RUTA_SALIDA = "../datos_procesados/salud_educacion_ambiente.csv"

COLUMNAS_SALIDA = [
    "dominio",
    "indicador",
    "codigo",
    "anio",
    "valor",
    "unidad",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def procesa(fecha_prueba: str) -> None:
    """Procesa los JSON de salud, educación y ambiente del Banco Mundial."""
    print("[INICIO] Procesamiento de Salud, Educación y Medio Ambiente (World Bank).")
    registros: list[dict] = []

    for codigo, (dominio, nombre, unidad) in INDICADORES_SECTORIALES.items():
        observaciones = procesa_economia.lee_json_indicador(codigo)
        if observaciones is None:
            continue

        for obs in observaciones:
            if not isinstance(obs, dict):
                continue
            valor = obs.get("value")
            if valor is None:
                continue
            texto_anio = str(obs.get("date", "")).strip()
            if not texto_anio.isdigit():
                continue
            anio = int(texto_anio)
            try:
                valor_num = round(float(valor), 4)
            except (ValueError, TypeError):
                continue

            registros.append(
                {
                    "dominio": dominio,
                    "indicador": nombre,
                    "codigo": codigo,
                    "anio": anio,
                    "valor": valor_num,
                    "unidad": unidad,
                    "fuente": FUENTE_WB_SECTORIAL,
                    "vigencia": str(anio),
                    "fecha_prueba": fecha_prueba,
                    "linaje": gobernanza.LINAJE_OBSERVADO,
                }
            )

    validos = gobernanza.filtra_registros_validos(
        registros, "salud_educacion_ambiente"
    )
    gobernanza.escribe_csv(validos, RUTA_SALIDA, COLUMNAS_SALIDA)
    print(
        f"[FIN] Salud, Educación y Ambiente completados: {len(validos)} registros en '{RUTA_SALIDA}'."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
