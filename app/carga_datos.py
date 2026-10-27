"""Carga cacheada de los datos procesados de Cerebro Andorra.

Este módulo centraliza la lectura de ``datos_procesados/`` para la App_Streamlit.
Todas las funciones de carga están cacheadas con ``@st.cache_data`` para que la
lectura de disco ocurra una sola vez por sesión, y devuelven ``None`` cuando el
archivo no existe o no puede leerse, de modo que las vistas puedan mostrar el
indicador de "Dato no disponible" sin interrumpir la carga (Req 5.4, 6.5, 7.5,
8.4).

La ruta a ``datos_procesados/`` se resuelve de forma relativa al propio archivo
mediante ``Path(__file__).resolve().parents[1] / "datos_procesados"``, para que
la app funcione con independencia del directorio de trabajo desde el que se
lance (``streamlit run app/streamlit_app.py`` desde la raíz del repositorio).

Convención de los CSV del proyecto: separador ``;`` y codificación UTF-8.

Mensajes de consola en español, coherentes con el resto del proyecto.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Resolución de rutas ---------------------------------------------------
# El directorio de datos procesados es hermano de 'app/' dentro del repositorio.
# parents[1] sube desde app/carga_datos.py hasta la raíz del proyecto.
DIR_PROCESADOS = Path(__file__).resolve().parents[1] / "datos_procesados"

# El GeoJSON de límites de parròquies vive en datos_crudos/ (no en procesados):
# es la fuente geoespacial tal cual se descarga, no un dato transformado.
DIR_CRUDOS = Path(__file__).resolve().parents[1] / "datos_crudos"

# Nombres de los archivos procesados que consume la app.
ARCHIVO_POBLACION = "poblacion_parroquia.csv"
ARCHIVO_PRECIOS = "precios_vivienda.csv"
ARCHIVO_INVENTARIO = "inventario_fuentes.csv"
ARCHIVO_TURISMO = "turismo.csv"
ARCHIVO_INVERSIONES = "inversiones_inmobiliarias.csv"

# Archivos procesados de la Parte 3 (enriquecimiento):
# - desgloses de población (tabla larga con la columna 'dimension'),
# - indicadores sociales reclasificados (umbrales de pobreza, fecundidad),
# - economía del Banco Mundial (World Bank).
ARCHIVO_DESGLOSES = "poblacion_desgloses.csv"
ARCHIVO_UMBRALES = "umbrales_pobreza.csv"
ARCHIVO_FECUNDIDAD = "tasa_fecundidad.csv"
ARCHIVO_ECONOMIA = "economia_worldbank.csv"

# Nombre del GeoJSON de límites de las 7 parròquies dentro de datos_crudos/.
ARCHIVO_GEOJSON_PARROQUIES = "parroquias_andorra.geojson"


def _lee_csv_procesado(nombre_archivo: str) -> "pd.DataFrame | None":
    """Lee un CSV de ``datos_procesados/`` devolviendo ``None`` ante fallos.

    Resuelve la ruta del archivo dentro de ``DIR_PROCESADOS`` y lo lee con el
    separador ``;`` y codificación UTF-8 propios del proyecto. Si el archivo no
    existe o no puede leerse por cualquier motivo, registra un mensaje en
    español por consola y devuelve ``None`` en lugar de propagar la excepción,
    para que las vistas muestren "Dato no disponible" sin romper la carga.

    Args:
        nombre_archivo: nombre del CSV dentro de ``datos_procesados/``.

    Returns:
        Un ``DataFrame`` con el contenido del archivo, o ``None`` si el archivo
        no existe o no puede leerse.
    """
    ruta = DIR_PROCESADOS / nombre_archivo

    if not ruta.exists():
        print(
            f"[carga_datos] Dato no disponible: no se encontró el archivo "
            f"'{ruta}'."
        )
        return None

    try:
        return pd.read_csv(ruta, sep=";", encoding="utf-8")
    except Exception as error:  # noqa: BLE001 - degradación segura en la app
        print(
            f"[carga_datos] Dato no disponible: no se pudo leer '{ruta}': "
            f"{error}."
        )
        return None


@st.cache_data
def carga_poblacion() -> "pd.DataFrame | None":
    """Carga la tabla de población por parròquia desde datos procesados.

    Lee ``datos_procesados/poblacion_parroquia.csv`` (separador ``;``, UTF-8).

    Returns:
        Un ``DataFrame`` con la población por parròquia y año, o ``None`` si el
        archivo no existe o no puede leerse (Req 6.5).
    """
    return _lee_csv_procesado(ARCHIVO_POBLACION)


@st.cache_data
def carga_precios() -> "pd.DataFrame | None":
    """Carga la tabla de precios de vivienda desde datos procesados.

    Lee ``datos_procesados/precios_vivienda.csv`` (separador ``;``, UTF-8).

    Returns:
        Un ``DataFrame`` con los precios de vivienda por parròquia, o ``None``
        si el archivo no existe o no puede leerse (Req 5.4, 7.5).
    """
    return _lee_csv_procesado(ARCHIVO_PRECIOS)


@st.cache_data
def carga_inventario() -> "pd.DataFrame | None":
    """Carga el Inventario_Fuentes desde datos procesados.

    Lee ``datos_procesados/inventario_fuentes.csv`` (separador ``;``, UTF-8).

    Returns:
        Un ``DataFrame`` con el inventario de fuentes, o ``None`` si el archivo
        no existe o no puede leerse (Req 8.4).
    """
    return _lee_csv_procesado(ARCHIVO_INVENTARIO)


@st.cache_data
def carga_turismo() -> "pd.DataFrame | None":
    """Carga la tabla de presupuesto de turismo desde datos procesados.

    Lee ``datos_procesados/turismo.csv`` (separador ``;``, UTF-8).

    Returns:
        Un ``DataFrame`` con el presupuesto de turismo por año y partida, o
        ``None`` si el archivo no existe o no puede leerse, para que la vista
        muestre el mensaje de ausencia sin interrumpirse (Req 3.8).
    """
    return _lee_csv_procesado(ARCHIVO_TURISMO)


@st.cache_data
def carga_inversiones() -> "pd.DataFrame | None":
    """Carga la tabla de inversiones inmobiliarias desde datos procesados.

    Lee ``datos_procesados/inversiones_inmobiliarias.csv`` (separador ``;``,
    UTF-8).

    Returns:
        Un ``DataFrame`` con el número de inversiones inmobiliarias por año, o
        ``None`` si el archivo no existe o no puede leerse, para que la vista
        muestre el mensaje de ausencia sin interrumpirse (Req 4.8).
    """
    return _lee_csv_procesado(ARCHIVO_INVERSIONES)


# --- Parte 3: desgloses de población --------------------------------------
# La tabla de desgloses es una única tabla larga con la columna 'dimension'
# que distingue cada desglose (edad_5, edad_1, sexo, nacionalidad,
# lugar_nacimiento). Las cargas por dimensión filtran esa tabla y devuelven
# None cuando el desglose falta (archivo ausente/ilegible) o cuando el filtro
# queda sin filas, para permitir el comportamiento de ausencia por desglose
# sin romper la vista (Req 2.6).


@st.cache_data
def carga_poblacion_desgloses() -> "pd.DataFrame | None":
    """Carga la tabla larga de desgloses de población desde datos procesados.

    Lee ``datos_procesados/poblacion_desgloses.csv`` (separador ``;``, UTF-8).
    Es la tabla base de la que derivan las cargas por dimensión.

    Returns:
        Un ``DataFrame`` con los desgloses de población (columna ``dimension``
        por desglose), o ``None`` si el archivo no existe o no puede leerse
        (Req 2.6).
    """
    return _lee_csv_procesado(ARCHIVO_DESGLOSES)


def _filtra_dimension(dimensiones: "list[str]") -> "pd.DataFrame | None":
    """Filtra la tabla de desgloses a una o varias dimensiones.

    Reutiliza ``carga_poblacion_desgloses()`` como tabla base y selecciona las
    filas cuya columna ``dimension`` está en ``dimensiones``.

    Args:
        dimensiones: lista de valores admitidos para la columna ``dimension``.

    Returns:
        Un ``DataFrame`` con las filas del desglose, o ``None`` si la tabla
        base falta/es ilegible, no tiene la columna ``dimension`` o el filtro
        queda sin filas (Req 2.6).
    """
    base = carga_poblacion_desgloses()

    if base is None or "dimension" not in base.columns:
        return None

    filtrado = base[base["dimension"].isin(dimensiones)]

    if filtrado.empty:
        print(
            f"[carga_datos] Dato no disponible: el desglose "
            f"{dimensiones} no tiene filas en '{ARCHIVO_DESGLOSES}'."
        )
        return None

    return filtrado


@st.cache_data
def carga_poblacion_edad() -> "pd.DataFrame | None":
    """Carga el desglose de población por edad (tramos de 5 años o de 1 año).

    Filtra ``carga_poblacion_desgloses()`` a ``dimension`` en
    ``('edad_5', 'edad_1')``.

    Returns:
        Un ``DataFrame`` con el desglose por edad, o ``None`` si el desglose
        falta o no tiene filas (Req 2.6).
    """
    return _filtra_dimension(["edad_5", "edad_1"])


@st.cache_data
def carga_poblacion_sexo() -> "pd.DataFrame | None":
    """Carga el desglose de población por sexo.

    Filtra ``carga_poblacion_desgloses()`` a ``dimension == 'sexo'``.

    Returns:
        Un ``DataFrame`` con el desglose por sexo, o ``None`` si el desglose
        falta o no tiene filas (Req 2.6).
    """
    return _filtra_dimension(["sexo"])


@st.cache_data
def carga_poblacion_nacionalidad() -> "pd.DataFrame | None":
    """Carga el desglose de población por nacionalidad.

    Filtra ``carga_poblacion_desgloses()`` a ``dimension == 'nacionalidad'``.

    Returns:
        Un ``DataFrame`` con el desglose por nacionalidad, o ``None`` si el
        desglose falta o no tiene filas (Req 2.6).
    """
    return _filtra_dimension(["nacionalidad"])


@st.cache_data
def carga_poblacion_lugar_nacimiento() -> "pd.DataFrame | None":
    """Carga el desglose de población por lugar de nacimiento.

    Filtra ``carga_poblacion_desgloses()`` a
    ``dimension == 'lugar_nacimiento'``.

    Returns:
        Un ``DataFrame`` con el desglose por lugar de nacimiento, o ``None`` si
        el desglose falta o no tiene filas (Req 2.6).
    """
    return _filtra_dimension(["lugar_nacimiento"])


# --- Parte 3: indicadores sociales y economía -----------------------------


@st.cache_data
def carga_umbrales_pobreza() -> "pd.DataFrame | None":
    """Carga la tabla de umbrales de pobreza desde datos procesados.

    Lee ``datos_procesados/umbrales_pobreza.csv`` (separador ``;``, UTF-8).

    Returns:
        Un ``DataFrame`` con los umbrales de pobreza por indicador y año, o
        ``None`` si el archivo no existe o no puede leerse (Req 3.5).
    """
    return _lee_csv_procesado(ARCHIVO_UMBRALES)


@st.cache_data
def carga_tasa_fecundidad() -> "pd.DataFrame | None":
    """Carga la tabla de tasa de fecundidad desde datos procesados.

    Lee ``datos_procesados/tasa_fecundidad.csv`` (separador ``;``, UTF-8).

    Returns:
        Un ``DataFrame`` con la tasa de fecundidad por año, o ``None`` si el
        archivo no existe o no puede leerse (Req 3.5).
    """
    return _lee_csv_procesado(ARCHIVO_FECUNDIDAD)


@st.cache_data
def carga_economia() -> "pd.DataFrame | None":
    """Carga la tabla de economía del Banco Mundial desde datos procesados.

    Lee ``datos_procesados/economia_worldbank.csv`` (separador ``;``, UTF-8).

    Returns:
        Un ``DataFrame`` con los indicadores económicos (PIB, IPC, PIB per
        cápita...), o ``None`` si el archivo no existe o no puede leerse, para
        que la Vista_Economia muestre la ausencia de fuente económica real sin
        interrumpirse (Req 5.3, 5.4, 5.5).
    """
    return _lee_csv_procesado(ARCHIVO_ECONOMIA)


@st.cache_data
def carga_geojson_parroquies() -> "dict | None":
    """Carga el GeoJSON de límites de las 7 parròquies desde datos crudos.

    Lee ``datos_crudos/parroquias_andorra.geojson`` y lo devuelve como ``dict``
    GeoJSON. Si el archivo no existe o no puede leerse/parsearse por cualquier
    motivo, registra un mensaje en español por consola y devuelve ``None`` en
    lugar de propagar la excepción, para que la Vista_Mapa muestre el mensaje
    de ausencia sin interrumpirse (Req 1.5).

    Returns:
        Un ``dict`` con el contenido del GeoJSON, o ``None`` si el archivo no
        existe o no puede leerse/parsearse.
    """
    ruta = DIR_CRUDOS / ARCHIVO_GEOJSON_PARROQUIES

    if not ruta.exists():
        print(
            f"[carga_datos] Dato no disponible: no se encontró el archivo "
            f"geoespacial '{ruta}'."
        )
        return None

    try:
        with open(ruta, encoding="utf-8") as archivo:
            return json.load(archivo)
    except Exception as error:  # noqa: BLE001 - degradación segura en la app
        print(
            f"[carga_datos] Dato no disponible: no se pudo leer o parsear "
            f"'{ruta}': {error}."
        )
        return None
