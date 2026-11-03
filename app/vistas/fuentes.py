"""Vista_Fuentes de la App_Streamlit de Cerebro Andorra (Versión Rediseñada).

Esta vista materializa el Requisito 8 ("Vista Fuentes y Método"): presenta el
Inventario_Fuentes como una tabla auditable con, por cada dataset, su nombre,
su fuente, su Etiqueta_Linaje y su Estado_Dataset, y muestra el motivo cuando
un dataset está en estado ``excluido`` o ``caído`` (Req 8.1, 8.2, 8.3).
"""

import sys
from pathlib import Path

import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de la carga de datos ------
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path
import estilos  # noqa: E402 - import tras ajustar sys.path

# Columnas del Inventario_Fuentes que la vista muestra
_COLUMNAS_INVENTARIO = ["nombre", "fuente", "linaje", "estado", "motivo"]

# Rótulos legibles para el encabezado de la tabla
_ETIQUETAS_COLUMNAS = {
    "nombre": "Nombre",
    "fuente": "Fuente",
    "linaje": "Linaje",
    "estado": "Estado",
    "motivo": "Motivo",
}


def render() -> None:
    """Renderiza la Vista_Fuentes estilizada con resumen métrico e inventario."""
    estilos.cabecera(
        "Fuentes y método",
        "Inventario auditable de los datasets del proyecto con su linaje de "
        "gobernanza y su estado de integración. Los datasets excluidos o "
        "caídos detallan su motivo.",
    )

    inventario = carga_datos.carga_inventario()

    # Degradación segura si falta el inventario (Req 8.4)
    if inventario is None or inventario.empty:
        st.warning(
            "⚠️ Inventario no disponible: no se encontró el Inventario_Fuentes o no pudo leerse."
        )
        return

    # --- Resumen ejecutivo en tarjetas (KPIs rápidos) ------------------------
    total_datasets = len(inventario)
    if "estado" in inventario.columns:
        estados = inventario["estado"].str.lower().fillna("")
        integrados = (estados == "integrado").sum()
        excluidos = (estados == "excluido").sum()
        caidos = (estados == "caído").sum() + (estados == "caido").sum()
    else:
        integrados = total_datasets
        excluidos = 0
        caidos = 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.metric("Total Datasets", total_datasets)
    with col2:
        with st.container(border=True):
            st.metric("Integrados", integrados)
    with col3:
        with st.container(border=True):
            st.metric("Excluidos", excluidos)
    with col4:
        with st.container(border=True):
            st.metric("Caídos / Error", caidos)

    st.markdown("---")

    # --- Tabla interactiva del inventario ------------------------------------
    st.subheader("Inventario de Datasets Auditables")
    st.caption("Usa la barra de búsqueda o haz clic en los encabezados de la tabla para ordenar las filas.")

    columnas_presentes = [
        columna for columna in _COLUMNAS_INVENTARIO if columna in inventario.columns
    ]
    tabla = inventario[columnas_presentes].rename(columns=_ETIQUETAS_COLUMNAS)

    with st.container(border=True):
        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Estado": st.column_config.TextColumn("Estado", help="Estado de integración en la v1"),
                "Linaje": st.column_config.TextColumn("Linaje", help="Etiqueta OBSERVADO o PROXY"),
            },
        )

    # --- Bloque desplegable de metodología -----------------------------------
    with st.expander("Detalles de Metodología de Gobernanza"):
        st.markdown(
            """
            * **OBSERVADO:** Datos provenientes directamente de fuentes oficiales públicas sin transformaciones ni inferencias destructivas.
            * **PROXY:** Datos derivados de fuentes de mercado u estimaciones (ej. anuncios de oferta).
            * **Excluidos:** Datasets cuya calidad o incoherencia formal impiden su integración en la versión vigente.
            """
        )