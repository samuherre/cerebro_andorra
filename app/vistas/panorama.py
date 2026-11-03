"""Vista Panorama de la App_Streamlit de Cerebro Andorra (Versión Rediseñada).

Presenta un resumen ejecutivo del país con las dos cifras clave a partir de los datos
procesados:
1. Población total de Andorra del año más reciente.
2. Precio de venta medio en €/m² del periodo más reciente.

Todo preservando estrictamente la gobernanza mediante componentes.cifra_gobernada.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de módulos hermanos ------
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path
import componentes  # noqa: E402 - import tras ajustar sys.path


def _es_dataframe_vacio(datos) -> bool:
    """Indica si el argumento no es un DataFrame utilizable."""
    if datos is None:
        return True
    if not isinstance(datos, pd.DataFrame):
        return True
    return datos.empty


def _metadato_desde_fila(fila: pd.Series, vigencia) -> dict:
    """Construye el Metadato_Cifra a partir de una fila procesada."""
    return {
        "fuente": fila.get("fuente"),
        "vigencia": vigencia,
        "fecha_prueba": fila.get("fecha_prueba"),
    }


def _cifra_poblacion_total() -> None:
    """Renderiza la población total de Andorra del año más reciente dentro de una tarjeta."""
    poblacion = carga_datos.carga_poblacion()

    with st.container(border=True):
        st.markdown("####  Demografía Nacional")
        if _es_dataframe_vacio(poblacion):
            componentes.cifra_gobernada(
                "Población total de Andorra", None, None, None
            )
            return

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

        poblaciones = pd.to_numeric(
            filas_anio.get("poblacion"), errors="coerce"
        ).dropna()
        if poblaciones.empty:
            componentes._muestra_no_disponible(
                "Población total de Andorra",
                f"no hay valores de población utilizables para el año {anio_reciente}",
            )
            return

        poblacion_total = int(poblaciones.sum())
        metadato = _metadato_desde_fila(filas_anio.iloc[0], str(anio_reciente))
        linaje = filas_anio.iloc[0].get("linaje")

        componentes.cifra_gobernada(
            f"Población total de Andorra ({anio_reciente})",
            f"{poblacion_total:,}".replace(",", "."),
            metadato,
            linaje,
        )


def _cifra_precio_venta_medio() -> None:
    """Renderiza el precio de venta medio en €/m² dentro de una tarjeta."""
    precios = carga_datos.carga_precios()

    with st.container(border=True):
        st.markdown("#### Mercado Inmobiliario")
        if _es_dataframe_vacio(precios):
            componentes.cifra_gobernada(
                "Precio de venta medio (€/m²)", None, None, None
            )
            return

        ventas = pd.to_numeric(
            precios.get("precio_venta"), errors="coerce"
        ).dropna()
        if ventas.empty:
            componentes._muestra_no_disponible(
                "Precio de venta medio (€/m²)",
                "no hay precios de venta utilizables en los datos de vivienda",
            )
            return

        precio_medio = round(float(ventas.mean()), 2)
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
            f"Precio de venta medio (€/m²) ({vigencia})",
            f"{precio_medio:,.2f} €".replace(",", "@")
            .replace(".", ",")
            .replace("@", "."),
            metadato,
            linaje,
        )


def render() -> None:
    """Renderiza la Vista Panorama estilizada."""
    # Encabezado principal estilizado
    st.title("Panorama General")
    st.markdown(
        """
        > Resumen macro con los indicadores fundamentales del **Principado de Andorra**.  
        > *Toda cifra expuesta en este panel cuenta con su correspondiente trazabilidad, vigencia y linaje auditable.*
        """
    )
    st.divider()

    # Sección de KPIs Principales
    st.subheader("Indicadores Clave del País")
    
    columna_poblacion, columna_precio = st.columns(2)

    with columna_poblacion:
        _cifra_poblacion_total()

    with columna_precio:
        _cifra_precio_venta_medio()

    st.divider()

    # Bloque informativo visual sobre la gobernanza del proyecto
    with st.container(border=True):
        st.markdown("### Principios de Gobernanza de Datos")
        col_info1, col_info2, col_info3 = st.columns(3)

        with col_info1:
            st.markdown("**1. Cero Cifras Huérfanas**")
            st.caption("No existen datos sin su correspondiente fuente oficial asignada.")

        with col_info2:
            st.markdown("**2. Linaje Transparente**")
            st.caption("Distinción clara entre datos **OBSERVADOS** (directos) y **PROXY** (estimados).")

        with col_info3:
            st.markdown("**3. Auditoría a un Clic**")
            st.caption("Acceso directo a las fechas de prueba y detalles técnicos en cada metadato.")