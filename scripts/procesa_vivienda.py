"""Procesamiento y limpieza de precios de vivienda de Indomio (linaje PROXY).

Tramo Lago del pipeline: lee el CSV crudo de precios de oferta obtenido por
scraping de Indomio, separa el valor del precio de su variación interanual y
prepara los registros gobernados para la app.

Convenciones del proyecto:
- Se ejecuta desde la carpeta ``scripts/`` y usa rutas relativas.
- Nunca escribe dentro de ``datos_crudos/`` (los crudos son la fuente de verdad).
- Todos los mensajes de consola van en español.

Este módulo implementa por ahora la lectura del CSV y el patrón de parseo
(sub-tarea 3.1). El parseo de celdas, la normalización y la orquestación se
implementan en sub-tareas posteriores.
"""

import re

import pandas as pd

# Fuente y linaje de este dominio. Los precios de Indomio son datos de mercado
# extraídos de anuncios (precios de oferta), por lo que su linaje es PROXY.
FUENTE_VIVIENDA = "Indomio (scraping, precios de oferta)"

# Nombres de columna esperados en el CSV crudo de Indomio.
COLUMNAS_ESPERADAS = ["Municipalities", "Sale €/m²", "Rent €/m²"]

# El CSV crudo de Indomio viene codificado en Windows-1252 (cp1252): el símbolo
# del euro se guarda como 0x80 y el superíndice dos como 0xB2. Leerlo con esta
# codificación hace que los nombres de columna coincidan exactamente con
# "Sale €/m²" y "Rent €/m²".
CODIFICACION_VIVIENDA = "cp1252"

# Captura "7,115(+14.8%)" -> precio="7,115", variacion="+14.8"
PATRON_PRECIO = re.compile(r"^\s*([\d.,]+)\s*\(\s*([+-]?\d+(?:\.\d+)?)\s*%\s*\)\s*$")


def lee_precios(ruta_entrada: str) -> pd.DataFrame:
    """Lee el CSV de precios de Indomio usando separador de tabulador.

    Verifica que estén presentes las columnas ``Municipalities``, ``Sale €/m²``
    y ``Rent €/m²``. Si el archivo no existe, no puede leerse o le faltan
    columnas esperadas, registra la causa en español por consola y devuelve
    ``None`` para que el orquestador aborte sin escribir una salida parcial
    (Req 2.1, 2.2, 9.3).

    Args:
        ruta_entrada: Ruta al CSV crudo de precios de vivienda.

    Returns:
        El ``DataFrame`` leído si la lectura y la verificación tienen éxito;
        ``None`` en caso de error.
    """
    try:
        df = pd.read_csv(
            ruta_entrada,
            sep="\t",
            encoding=CODIFICACION_VIVIENDA,
        )
    except FileNotFoundError:
        print(
            f"ERROR: no se encontró el archivo de precios de vivienda "
            f"'{ruta_entrada}'. Se aborta sin escribir salida."
        )
        return None
    except Exception as error:
        print(
            f"ERROR: no se pudo leer el archivo de precios de vivienda "
            f"'{ruta_entrada}': {error}. Se aborta sin escribir salida."
        )
        return None

    columnas_faltantes = [
        columna for columna in COLUMNAS_ESPERADAS if columna not in df.columns
    ]
    if columnas_faltantes:
        print(
            f"ERROR: al archivo de precios de vivienda '{ruta_entrada}' le "
            f"faltan columnas esperadas: {', '.join(columnas_faltantes)}. "
            f"Se aborta sin escribir salida."
        )
        return None

    print(
        f"OK: se leyó el archivo de precios de vivienda '{ruta_entrada}' "
        f"con {len(df)} filas."
    )
    return df


def parsea_celda_precio(celda) -> tuple[float | None, float | None]:
    """Separa el valor de precio y su variación interanual de una celda.

    Las celdas de Indomio combinan el precio €/m² y su variación porcentual en
    una sola cadena, por ejemplo ``"7,115(+14.8%)"``. La coma actúa como
    separador de miles, por lo que se elimina antes de convertir el precio a
    ``float`` (``"7,115"`` -> ``7115.0``). La variación se devuelve como
    ``float`` conservando el signo (``"+14.8"`` -> ``14.8``, ``"-3.2"`` ->
    ``-3.2``).

    Si la celda es ``None``, está vacía o no coincide con el formato esperado,
    devuelve ``(None, None)`` para que la normalización pueda marcar el precio
    como ausente sin abortar el resto del procesamiento (Req 2.3, 2.6).

    Args:
        celda: Contenido de la celda de precio tal como viene del CSV crudo.

    Returns:
        Una tupla ``(precio, variacion)`` de ``float`` si la celda casa con el
        patrón; ``(None, None)`` en caso contrario.
    """
    if celda is None:
        return (None, None)

    coincidencia = PATRON_PRECIO.match(str(celda))
    if coincidencia is None:
        return (None, None)

    texto_precio, texto_variacion = coincidencia.group(1), coincidencia.group(2)

    # La coma es separador de miles: se elimina antes de convertir a float.
    precio = float(texto_precio.replace(",", ""))
    variacion = float(texto_variacion)
    return (precio, variacion)


import datetime

import gobernanza

# Rutas relativas asumiendo ejecución desde la carpeta ``scripts/`` (convención
# del repositorio: los crudos son la fuente de verdad y las salidas van a
# ``datos_procesados/``).
RUTA_ENTRADA = "../datos_crudos/precios_vivienda_indomio.csv"
RUTA_SALIDA = "../datos_procesados/precios_vivienda.csv"

# Mapeo del nombre de municipio de Indomio al nombre canónico de parròquia, de
# modo que población y vivienda compartan la misma clave de parròquia en la app.
# La mayoría de nombres ya coinciden; sólo "Sant Julia de Loria" necesita
# normalizarse a su forma con diacríticos catalanes.
MAPEO_PARROQUIA = {
    "Andorra la Vella": "Andorra la Vella",
    "Canillo": "Canillo",
    "Encamp": "Encamp",
    "Escaldes-Engordany": "Escaldes-Engordany",
    "La Massana": "La Massana",
    "Ordino": "Ordino",
    "Sant Julia de Loria": "Sant Julià de Lòria",
}

# Orden de columnas de la tabla procesada precios_vivienda.csv (ver design.md).
COLUMNAS_SALIDA = [
    "parroquia",
    "precio_venta",
    "var_venta",
    "precio_alquiler",
    "var_alquiler",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def _mapea_parroquia(municipio: str) -> str:
    """Devuelve el nombre canónico de parròquia para un municipio de Indomio.

    Si el municipio no está en ``MAPEO_PARROQUIA`` se devuelve tal cual,
    conservando el valor original para no perder el registro (Req 2.4).
    """
    return MAPEO_PARROQUIA.get(municipio, municipio)


def normaliza_precios(df, fecha_prueba: str) -> list[dict]:
    """Normaliza el DataFrame de Indomio a un registro por parròquia.

    Por cada fila del crudo produce un registro con el nombre canónico de
    parròquia, el precio y la variación de venta y de alquiler ya separados
    (mediante ``parsea_celda_precio``) y los metadatos de gobernanza con
    ``linaje`` = PROXY (Req 2.4, 2.5).

    Cuando una celda de precio no casa con el patrón esperado, el valor de
    precio (y su variación) del registro se marcan como ausentes dejándolos
    vacíos, pero la fila se conserva y se registra en un mensaje de consola en
    español la parròquia y la columna afectadas (Req 2.6).

    La ``vigencia`` es el periodo de la extracción: se toma el año de
    ``fecha_prueba`` (formato ISO ``AAAA-MM-DD``); si no puede interpretarse,
    se usa la propia ``fecha_prueba`` como periodo.

    Args:
        df: DataFrame leído por ``lee_precios``.
        fecha_prueba: fecha (ISO) en que se extrajo/verificó el dato.

    Returns:
        Lista de registros (dicts) con las columnas de ``COLUMNAS_SALIDA``.
    """
    # La vigencia es el periodo de extracción: usamos el año de fecha_prueba.
    vigencia = fecha_prueba.split("-")[0] if fecha_prueba else ""
    if not vigencia:
        vigencia = fecha_prueba

    registros: list[dict] = []
    for _, fila in df.iterrows():
        municipio = str(fila["Municipalities"]).strip()
        parroquia = _mapea_parroquia(municipio)

        precio_venta, var_venta = parsea_celda_precio(fila["Sale €/m²"])
        if precio_venta is None:
            print(
                f"AVISO: la celda de precio de venta de la parròquia "
                f"'{parroquia}' (columna 'Sale €/m²') no casa con el formato "
                f"esperado; se marca el precio como ausente."
            )

        precio_alquiler, var_alquiler = parsea_celda_precio(fila["Rent €/m²"])
        if precio_alquiler is None:
            print(
                f"AVISO: la celda de precio de alquiler de la parròquia "
                f"'{parroquia}' (columna 'Rent €/m²') no casa con el formato "
                f"esperado; se marca el precio como ausente."
            )

        # Los valores ausentes (None) se emiten como cadena vacía en el CSV.
        registros.append(
            {
                "parroquia": parroquia,
                "precio_venta": "" if precio_venta is None else precio_venta,
                "var_venta": "" if var_venta is None else var_venta,
                "precio_alquiler": (
                    "" if precio_alquiler is None else precio_alquiler
                ),
                "var_alquiler": "" if var_alquiler is None else var_alquiler,
                "fuente": FUENTE_VIVIENDA,
                "vigencia": vigencia,
                "fecha_prueba": fecha_prueba,
                "linaje": gobernanza.LINAJE_PROXY,
            }
        )

    return registros


def procesa(fecha_prueba: str) -> None:
    """Orquesta la lectura, normalización, gobernanza y escritura de precios.

    Lee el CSV crudo de Indomio, normaliza los precios a un registro por
    parròquia con linaje PROXY, filtra los registros que superan la gobernanza
    y escribe el resultado en ``../datos_procesados/precios_vivienda.csv``
    (Req 2.4, 2.5). Si la lectura falla (``lee_precios`` devuelve ``None``),
    aborta limpiamente sin escribir ninguna salida parcial (Req 2.2).

    Args:
        fecha_prueba: fecha (ISO) en que se extrajo/verificó el dato.
    """
    df = lee_precios(RUTA_ENTRADA)
    if df is None:
        print(
            "ERROR: no se pudo leer el archivo de precios de vivienda; "
            "se aborta el procesamiento sin escribir salida."
        )
        return

    registros = normaliza_precios(df, fecha_prueba)
    registros_validos = gobernanza.filtra_registros_validos(registros, "vivienda")

    gobernanza.escribe_csv(registros_validos, RUTA_SALIDA, COLUMNAS_SALIDA)
    print(
        f"OK: procesamiento de precios de vivienda finalizado con "
        f"{len(registros_validos)} registro(s)."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
