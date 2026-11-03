"""Vista de Vivienda/Mercado inmobiliario de la App_Streamlit de Cerebro Andorra.

Presenta los precios de venta y de alquiler en €/m² de las 7 parròquies a partir
de los datos procesados de Indomio, mostrando cada cifra exclusivamente a través
de ``cifra_gobernada`` para garantizar el principio rector del proyecto ("0
cifras sin fuente, sin vigencia y sin fecha de prueba"). Los precios de Indomio
llevan la Etiqueta_Linaje PROXY, que ``cifra_gobernada`` distingue visualmente
con un badge de color propio (Req 7.1, 7.2, 7.3).

Las transacciones inmobiliarias oficiales (linaje OBSERVADO) no se procesan en
v1 —el dataset ``oficial_820`` quedó excluido por no coincidir su contenido con
el nombre del archivo—, de modo que la vista muestra un indicador de "Dato no
disponible" para las transacciones oficiales (Req 7.4, 7.5).

La app se lanza desde la raíz del repositorio (``streamlit run
app/streamlit_app.py``); como este módulo vive en ``app/vistas/`` se añade la
carpeta ``app/`` al ``sys.path`` (parents[1]) para poder importar los módulos
transversales ``componentes`` y ``carga_datos`` sin convertir ``app/`` en un
paquete.

Textos de interfaz y mensajes de consola en español, coherentes con el resto del
proyecto.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de módulos transversales --
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path
import componentes  # noqa: E402 - import tras ajustar sys.path

# Etiqueta de linaje de los precios de Indomio
_LINAJE_PRECIOS = "PROXY"

# Orden canónico de las 7 parròquies de Andorra para una presentación estable.
_PARROQUIES = [
    "Andorra la Vella",
    "Canillo",
    "Encamp",
    "Escaldes-Engordany",
    "La Massana",
    "Ordino",
    "Sant Julià de Lòria",
]


def _valor_o_none(fila: "pd.Series", columna: str):
    """Devuelve el valor de una columna, o ``None`` si está ausente/NaN."""
    if columna not in fila.index:
        return None
    valor = fila[columna]
    if valor is None or pd.isna(valor):
        return None
    return valor


def _metadato_de_fila(fila: "pd.Series") -> "dict | None":
    """Construye el Metadato_Cifra de una fila de precios, o ``None``."""
    campos = ("fuente", "vigencia", "fecha_prueba")
    if not all(campo in fila.index for campo in campos):
        return None
    return {campo: fila[campo] for campo in campos}


def _linaje_de_fila(fila: "pd.Series") -> "str | None":
    """Devuelve la Etiqueta_Linaje del registro, o ``None`` si no la tiene."""
    valor = _valor_o_none(fila, "linaje")
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _muestra_precios(precios: "pd.DataFrame") -> None:
    """Renderiza el precio de venta y de alquiler de cada una de las 7 parròquies."""
    st.subheader(" Precios de vivienda por parròquia (€/m²)")
    st.caption(
        "Precios de oferta extraídos de Indomio (linaje PROXY): representan "
        "anuncios, no transacciones reales."
    )

    # Indexar por parròquia para localizar cada registro de forma directa.
    por_parroquia = {}
    if "parroquia" in precios.columns:
        for _, fila in precios.iterrows():
            por_parroquia[str(fila["parroquia"]).strip()] = fila

    # Presentación continua estilizada por parròquia
    for parroquia in _PARROQUIES:
        with st.container(border=True):
            st.markdown(f"### {parroquia}")
            fila = por_parroquia.get(parroquia)

            if fila is None:
                columna_venta, columna_alquiler = st.columns(2)
                with columna_venta:
                    componentes.cifra_gobernada(
                        "Precio de venta (€/m²)", None, None, None
                    )
                with columna_alquiler:
                    componentes.cifra_gobernada(
                        "Precio de alquiler (€/m²)", None, None, None
                    )
                continue

            metadato = _metadato_de_fila(fila)
            linaje = _linaje_de_fila(fila)

            columna_venta, columna_alquiler = st.columns(2)
            with columna_venta:
                componentes.cifra_gobernada(
                    "Precio de venta (€/m²)",
                    _valor_o_none(fila, "precio_venta"),
                    metadato,
                    linaje,
                )
            with columna_alquiler:
                componentes.cifra_gobernada(
                    "Precio de alquiler (€/m²)",
                    _valor_o_none(fila, "precio_alquiler"),
                    metadato,
                    linaje,
                )


def _muestra_transacciones_oficiales() -> None:
    """Muestra el indicador de "Dato no disponible" para transacciones oficiales."""
    st.subheader(" Transacciones inmobiliarias oficiales")
    with st.container(border=True):
        st.warning("Transacciones oficiales: Dato no disponible")
        st.caption(
            "Motivo: no existen datos procesados de transacciones inmobiliarias "
            "oficiales (linaje OBSERVADO) en esta versión (dataset `oficial_820` excluido)."
        )


def render() -> None:
    """Renderiza la Vista_Vivienda completa."""
    st.title("Vivienda y Mercado Inmobiliario")
    st.markdown(
        """
        > Análisis de precios de oferta de venta y alquiler por m² en el Principado de Andorra.  
        > *Los valores expuestos cuentan con linaje **PROXY** al provenir de fuentes de mercado (Indomio).*
        """
    )
    st.divider()

    precios = carga_datos.carga_precios()
    if precios is None or precios.empty:
        st.warning(
            "Precios de vivienda: Dato no disponible. No se pudieron cargar los "
            "datos procesados de precios."
        )
    else:
        _muestra_precios(precios)

    st.divider()
    _muestra_transacciones_oficiales()