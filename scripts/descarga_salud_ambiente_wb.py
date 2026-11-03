"""Extractor ético de Salud, Educación, Conectividad, Energía y Medio Ambiente (Banco Mundial).

Reutiliza ``descarga_worldbank.descarga_indicador`` y ``ya_descargado`` para
descargar desde la API v2 del Banco Mundial (World Bank Open Data, licencia
CC BY 4.0) los indicadores sectoriales de Andorra (país ``AD``) hacia
``datos_crudos/worldbank_<codigo>.json``, sin modificar ``descarga_worldbank.INDICADORES``
para preservar intacto el contrato de macroeconomía.
"""

import descarga_worldbank

# Diccionario código -> (dominio, nombre legible, unidad)
INDICADORES_SECTORIALES = {
    # 1. Salud y bienestar
    "SP.DYN.LE00.IN": ("salud", "Esperanza de vida al nacer", "años"),
    "SH.XPD.CHEX.GD.ZS": ("salud", "Gasto corriente en salud (% del PIB)", "% del PIB"),
    "SH.XPD.CHEX.PC.CD": ("salud", "Gasto en salud per cápita", "US$"),
    "SP.DYN.IMRT.IN": ("salud", "Mortalidad infantil", "por 1.000 nacidos vivos"),
    "SH.MED.PHYS.ZS": ("salud", "Médicos por cada 1.000 habitantes", "por 1.000 hab."),
    # 2. Educación y conectividad digital
    "IT.NET.USER.ZS": (
        "educacion_conectividad",
        "Usuarios de Internet (% de la población)",
        "% de la población",
    ),
    "SE.XPD.TOTL.GD.ZS": (
        "educacion_conectividad",
        "Gasto público en educación (% del PIB)",
        "% del PIB",
    ),
    "SE.SEC.ENRR": (
        "educacion_conectividad",
        "Matriculación en educación secundaria",
        "% bruto",
    ),
    # 3. Energía, clima y medio ambiente
    "AG.LND.FRST.ZS": (
        "energia_ambiente",
        "Superficie forestal (% del territorio)",
        "% del territorio",
    ),
    "EG.FEC.RNEW.ZS": (
        "energia_ambiente",
        "Consumo de energía renovable",
        "% del consumo total",
    ),
    "EN.GHG.CO2.PC.CE.AR5": (
        "energia_ambiente",
        "Emisiones de CO2 per cápita",
        "t CO2e/hab.",
    ),
    "EN.ATM.PM25.MC.M3": (
        "energia_ambiente",
        "Exposición media a partículas PM2.5",
        "µg/m³",
    ),
}


def main() -> int:
    """Descarga los indicadores sectoriales de World Bank de forma idempotente."""
    print(
        "--- Descarga de Salud, Educación, Conectividad y Medio Ambiente (World Bank) ---"
    )
    descarga_worldbank.PAUSA_CORTESIA_S = 1
    fallidos = 0
    for codigo, (dominio, nombre, _) in INDICADORES_SECTORIALES.items():
        print(f"\n=== [{dominio}] {nombre} ({codigo}) ===")
        if descarga_worldbank.ya_descargado(codigo):
            print(
                f"Ya existe en disco: {descarga_worldbank.ruta_crudo(codigo)} (se omite)."
            )
            continue
        if not descarga_worldbank.descarga_indicador(codigo):
            fallidos += 1
    return fallidos


if __name__ == "__main__":
    raise SystemExit(main())
