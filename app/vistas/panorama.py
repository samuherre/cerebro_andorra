"""Vista Panorama de la App_Streamlit de Cerebro Andorra.

Presenta un resumen del país con dos cifras clave a partir de los datos
procesados:

1. La población total de Andorra del año más reciente disponible, con la
   etiqueta del año al que corresponde (Req 5.1).
2. El precio de venta medio en euros por metro cuadrado del año más reciente
   presente en los datos de vivienda, redondeado a dos decimales y con la
   etiqueta del año (Req 5.2).

Ambas cifras se muestran exclusivamente a través de ``componentes.cifra_gobernada``,
de modo que el principio rector —"0 cifras sin fuente, sin vigencia y sin fecha
de prueba"— y la presentación del Metadato_Cifra y la Etiqueta_Linaje quedan
garantizados en un único punto (Req 5.3).

Si un dato no está disponible (DataFrame ``None`` o vacío) o no tiene un año
identificable, se muestra el indicador de "Dato no disponible" con el motivo
correspondiente sin interrumpir la carga del resto de la vista (Req 5.4, 5.5).

Como este módulo vive en ``app/vistas/`` y reutiliza los módulos hermanos
``carga_datos.py`` y ``componentes.py`` (ubicados en ``app/``), se añade la
carpeta ``app/`` al ``sys.path`` resolviéndola de forma relativa a este archivo.

Mensajes de consola y textos de interfaz en español, coherentes con el resto
del proyecto.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de módulos hermanos ------
# parents[1] sube desde app/vistas/panorama.py hasta app/; desde ahí se importan
# carga_datos y componentes sin necesidad de convertir app/ en un paquete.
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path
import componentes  # noqa: E402 - import tras ajustar sys.path


def _es_dataframe_vacio(datos) -> bool:
    """Indica si el argumento no es un DataFrame utilizable.

    Considera "vacío" tanto el caso ``None`` (archivo inexistente o ilegible,
    Req 5.4) como el de un DataFrame sin filas.

    Args:
        datos: valor devuelto por una función de carga (``DataFrame`` o ``None``).

    Returns:
        True si no hay datos utilizables; False si es un DataFrame con filas.
    """
    if datos is None:
        return True
    if not isinstance(datos, pd.DataFrame):
        return True
    return datos.empty


def _metadato_desde_fila(fila: pd.Series, vigencia) -> dict:
    """Construye el Metadato_Cifra a partir de una fila procesada.

    Reconstruye el diccionario ``fuente``/``vigencia``/``fecha_prueba`` que
    espera ``componentes.cifra_gobernada`` a partir de las columnas de una fila
    de datos procesados. La ``vigencia`` se pasa de forma explícita porque para
    la población corresponde al año más reciente calculado.

    Args:
        fila: una fila (``pd.Series``) de los datos procesados con las columnas
            ``fuente`` y ``fecha_prueba``.
        vigencia: valor de vigencia a mostrar (año o periodo).

    Returns:
        dict con las claves ``fuente``, ``vigencia`` y ``fecha_prueba``.
    """
    return {
        "fuente": fila.get("fuente"),
        "vigencia": vigencia,
        "fecha_prueba": fila.get("fecha_prueba"),
    }


def _cifra_poblacion_total() -> None:
    """Renderiza la población total de Andorra del año más reciente.

    Carga los datos de población, identifica el año máximo disponible, suma la
    población de todas las parròquies de ese año y muestra la cifra con su
    Metadato_Cifra y su Etiqueta_Linaje mediante ``cifra_gobernada``. La
    etiqueta incluye el año al que corresponde la cifra (Req 5.1, 5.3).

    Si no hay datos (Req 5.4) o no se puede identificar un año (Req 5.5),
    delega en ``cifra_gobernada`` con ``valor=None`` para mostrar el indicador
    de "Dato no disponible" con el motivo, sin interrumpir la carga.
    """
    poblacion = carga_datos.carga_poblacion()

    if _es_dataframe_vacio(poblacion):
        # No hay datos procesados de población (Req 5.4).
        componentes.cifra_gobernada(
            "Población total de Andorra", None, None, None
        )
        return

    # Identificar el año más reciente. Si la columna no existe o no tiene
    # ningún valor numérico, no hay año identificable (Req 5.5).
    anios = pd.to_numeric(poblacion.get("anio"), errors="coerce").dropna()
    if anios.empty:
        componentes._muestra_no_disponible(
            "Población total de Andorra",
            "no se pudo identificar el año más reciente en los datos de población",
        )
        return

    anio_reciente = int(anios.max())
    filas_anio = poblacion[
        pd.to_numeric(poblacion["anio"], errors="coerce") == anio_reciente
    ]

    # Sumar la población del año más reciente ignorando valores no numéricos.
    poblaciones = pd.to_numeric(filas_anio.get("poblacion"), errors="coerce").dropna()
    if poblaciones.empty:
        componentes._muestra_no_disponible(
            "Población total de Andorra",
            f"no hay valores de población utilizables para el año {anio_reciente}",
        )
        return

    poblacion_total = int(poblaciones.sum())

    # El metadato se toma de la primera fila del año (todas comparten fuente y
    # fecha de prueba); la vigencia es el año más reciente.
    metadato = _metadato_desde_fila(filas_anio.iloc[0], str(anio_reciente))
    linaje = filas_anio.iloc[0].get("linaje")

    componentes.cifra_gobernada(
        f"Población total de Andorra ({anio_reciente})",
        f"{poblacion_total:,}".replace(",", "."),
        metadato,
        linaje,
    )


def _cifra_precio_venta_medio() -> None:
    """Renderiza el precio de venta medio en €/m² del año más reciente.

    Carga los datos de precios de vivienda (una extracción, un único periodo),
    calcula la media de ``precio_venta`` sobre las parròquies con valor
    disponible, la redondea a dos decimales y la muestra con su Metadato_Cifra
    y su Etiqueta_Linaje PROXY mediante ``cifra_gobernada``. La etiqueta incluye
    el periodo de vigencia (Req 5.2, 5.3).

    Si no hay datos (Req 5.4) o no hay ningún precio de venta utilizable /
    periodo identificable (Req 5.5), muestra el indicador de "Dato no
    disponible" con el motivo, sin interrumpir la carga.
    """
    precios = carga_datos.carga_precios()

    if _es_dataframe_vacio(precios):
        # No hay datos procesados de vivienda (Req 5.4).
        componentes.cifra_gobernada(
            "Precio de venta medio (€/m²)", None, None, None
        )
        return

    # Precio de venta medio ignorando ausentes/vacíos (Req 2.6, 5.2).
    ventas = pd.to_numeric(precios.get("precio_venta"), errors="coerce").dropna()
    if ventas.empty:
        componentes._muestra_no_disponible(
            "Precio de venta medio (€/m²)",
            "no hay precios de venta utilizables en los datos de vivienda",
        )
        return

    precio_medio = round(float(ventas.mean()), 2)

    # La vigencia (periodo de la extracción) es común a todas las filas; se toma
    # de la primera fila. Si no existe, no hay año/periodo identificable (5.5).
    fila_ref = precios.iloc[0]
    vigencia = fila_ref.get("vigencia")
    if vigencia is None or str(vigencia).strip() == "":
        componentes._muestra_no_disponible(
            "Precio de venta medio (€/m²)",
            "no se pudo identificar el periodo de vigencia de los precios de vivienda",
        )
        return

    metadato = _metadato_desde_fila(fila_ref, vigencia)
    linaje = fila_ref.get("linaje")

    componentes.cifra_gobernada(
        f"Precio de venta medio en €/m² ({vigencia})",
        f"{precio_medio:.2f}",
        metadato,
        linaje,
    )


def render() -> None:
    """Renderiza la Vista Panorama completa.

    Punto de entrada que ``streamlit_app.py`` invoca para pintar la vista.
    Muestra el título, una breve descripción y las dos cifras clave del país
    (población total y precio de venta medio), cada una con su gobernanza. Un
    fallo de datos en una cifra no interrumpe la presentación de la otra
    (Req 5.4, 5.5).
    """
    st.title("Panorama de Andorra")
    st.write(
        "Resumen del país con las cifras clave más recientes. Toda cifra se "
        "muestra con su fuente, vigencia, fecha de prueba y etiqueta de linaje."
    )

    columna_poblacion, columna_precio = st.columns(2)

    with columna_poblacion:
        _cifra_poblacion_total()

    with columna_precio:
        _cifra_precio_venta_medio()
