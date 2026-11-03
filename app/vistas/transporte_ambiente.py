"""Vista "Transporte, Energía y Medio Ambiente" de la App_Streamlit de Cerebro Andorra.

Reúne dos bloques gobernados (linaje OBSERVADO):
1. **Transporte y Movilidad Territorial** (``equipamientos_suelo.csv``, ``F18``):
   estaciones y paradas de autobús, teleféricos/remontes de montaña,
   aparcamientos públicos y estaciones de servicio/recarga por parròquia, más el
   mapa de nodos de transporte.
2. **Energía, Bosques y Emisiones** (``salud_educacion_ambiente.csv``, ``F19``):
   consumo de energía renovable, porcentaje de superficie forestal, emisiones de
   CO2 per cápita y exposición a partículas PM2.5 (Banco Mundial, CC BY 4.0).
"""

import importlib
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402
import componentes  # noqa: E402
import estilos  # noqa: E402

if not hasattr(carga_datos, "carga_equipamientos_suelo"):
    importlib.reload(carga_datos)

_ID_FUENTE_EQUIP = "F18"
_ID_FUENTE_WB_SECTORIAL = "F19"


def _metadato_fila(fila: pd.Series) -> dict:
    return {
        "fuente": fila.get("fuente"),
        "vigencia": str(fila.get("vigencia", "")),
        "fecha_prueba": fila.get("fecha_prueba"),
    }


def _formatea_valor(valor: float, unidad: str) -> str:
    u = str(unidad or "").strip()
    num_txt = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{num_txt} {u}".strip()


def _seccion_transporte() -> None:
    st.subheader("Infraestructura de Transporte y Movilidad por Parròquia")
    st.caption(
        "Nodos de transporte público, movilidad por cable (teleféricos/remontes), "
        "aparcamientos y estaciones de servicio (OpenStreetMap, licencia ODbL, linaje OBSERVADO)."
    )

    if not hasattr(carga_datos, "carga_equipamientos_suelo"):
        importlib.reload(carga_datos)
    equip = carga_datos.carga_equipamientos_suelo()
    if equip is None or equip.empty:
        st.info("No hay datos procesados de infraestructura de transporte.")
        return

    trans = equip[equip["dominio"] == "Transporte y movilidad"].copy()
    if trans.empty:
        st.info("No se encontraron registros de transporte en el inventario territorial.")
        return

    fila_ref = trans.iloc[0]
    total_nodos = len(trans)
    parroquias_cubiertas = int(trans["parroquia"].nunique())

    # Conteos por tipo principal
    por_tipo = trans["tipo_equipamiento"].value_counts()
    tipo_principal = str(por_tipo.index[0]) if not por_tipo.empty else "Transporte"
    cant_principal = int(por_tipo.iloc[0]) if not por_tipo.empty else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            componentes.cifra_gobernada(
                "Total de nodos de transporte registrados",
                total_nodos,
                _metadato_fila(fila_ref),
                fila_ref.get("linaje"),
                id_fuente=_ID_FUENTE_EQUIP,
            )
    with col2:
        with st.container(border=True):
            componentes.cifra_gobernada(
                f"Infraestructura principal: {tipo_principal}",
                cant_principal,
                _metadato_fila(fila_ref),
                fila_ref.get("linaje"),
                id_fuente=_ID_FUENTE_EQUIP,
            )
    with col3:
        with st.container(border=True):
            componentes.cifra_gobernada(
                "Parròquies con nodos georreferenciados",
                parroquias_cubiertas,
                _metadato_fila(fila_ref),
                fila_ref.get("linaje"),
                id_fuente=_ID_FUENTE_EQUIP,
            )

    col_graf, col_mapa = st.columns(2)
    with col_graf:
        resumen = (
            trans.groupby(["parroquia", "tipo_equipamiento"], as_index=False)
            .size()
            .rename(columns={"size": "cantidad"})
        )
        try:
            import plotly.express as px

            fig = px.bar(
                resumen,
                x="parroquia",
                y="cantidad",
                color="tipo_equipamiento",
                title="Dotación de transporte y movilidad por parròquia",
                labels={
                    "parroquia": "Parròquia",
                    "cantidad": "Nº de nodos",
                    "tipo_equipamiento": "Tipo",
                },
            )
            fig.update_layout(margin={"r": 10, "t": 40, "l": 10, "b": 10}, height=380)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.dataframe(resumen, use_container_width=True, hide_index=True)

    with col_mapa:
        st.markdown("**Mapa de nodos de movilidad y transporte**")
        trans_coords = trans.copy()
        trans_coords["lat"] = pd.to_numeric(trans_coords["lat"], errors="coerce")
        trans_coords["lon"] = pd.to_numeric(trans_coords["lon"], errors="coerce")
        trans_coords = trans_coords.dropna(subset=["lat", "lon"])
        if not trans_coords.empty:
            st.map(trans_coords[["lat", "lon"]], zoom=10)

    with st.expander("Explorar listado completo de nodos de transporte y movilidad"):
        st.dataframe(
            trans[["parroquia", "tipo_equipamiento", "nombre", "lat", "lon"]].rename(
                columns={
                    "parroquia": "Parròquia",
                    "tipo_equipamiento": "Tipo de infraestructura",
                    "nombre": "Nombre / Parada",
                    "lat": "Latitud",
                    "lon": "Longitud",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


def _seccion_energia_ambiente() -> None:
    st.subheader("Energía Renovable, Bosques, Emisiones y Calidad del Aire")
    st.caption(
        "Indicadores ambientales y energéticos oficiales para Andorra del Banco Mundial "
        "(World Bank Open Data, licencia CC BY 4.0, linaje OBSERVADO)."
    )

    if not hasattr(carga_datos, "carga_salud_ambiente"):
        importlib.reload(carga_datos)
    df = carga_datos.carga_salud_ambiente()
    if df is None or df.empty:
        st.info("No hay indicadores ambientales procesados en este momento.")
        return

    amb = df[df["dominio"] == "energia_ambiente"].copy()
    if amb.empty:
        st.info("No se encontraron indicadores en el dominio de energía y ambiente.")
        return

    amb["anio"] = pd.to_numeric(amb["anio"], errors="coerce")
    amb["valor"] = pd.to_numeric(amb["valor"], errors="coerce")
    amb = amb.dropna(subset=["anio", "valor"]).sort_values("anio")

    codigos = list(dict.fromkeys(amb["codigo"].tolist()))
    for inicio in range(0, len(codigos), 2):
        lote = codigos[inicio : inicio + 2]
        cols = st.columns(len(lote))
        for codigo, col in zip(lote, cols):
            filas_cod = amb[amb["codigo"] == codigo]
            ultima = filas_cod.iloc[-1]
            nombre = str(ultima.get("indicador", codigo))
            unidad = str(ultima.get("unidad", ""))
            anio_max = int(ultima["anio"])
            with col:
                with st.container(border=True):
                    componentes.cifra_gobernada(
                        f"{nombre} ({anio_max})",
                        _formatea_valor(ultima["valor"], unidad),
                        _metadato_fila(ultima),
                        ultima.get("linaje"),
                        id_fuente=_ID_FUENTE_WB_SECTORIAL,
                    )

    nombres_map = {
        str(amb[amb["codigo"] == c].iloc[-1]["indicador"]): c for c in codigos
    }
    elegido_nombre = st.selectbox(
        "Selecciona un indicador ambiental o energético para ver su serie histórica",
        options=list(nombres_map.keys()),
        key="sel_wb_energia_ambiente",
    )
    codigo_sel = nombres_map[elegido_nombre]
    serie = amb[amb["codigo"] == codigo_sel].sort_values("anio")
    unidad_sel = str(serie.iloc[-1].get("unidad", ""))

    try:
        import plotly.express as px

        fig = px.area(
            serie,
            x="anio",
            y="valor",
            markers=True,
            title=f"Evolución histórica: {elegido_nombre}",
            labels={"anio": "Año", "valor": f"Valor ({unidad_sel})"},
        )
        fig.update_layout(margin={"r": 10, "t": 40, "l": 10, "b": 10}, height=350)
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.dataframe(
            serie[["anio", "valor", "unidad", "fuente"]],
            use_container_width=True,
            hide_index=True,
        )


def render() -> None:
    """Renderiza la vista de Transporte, Energía y Medio Ambiente."""
    estilos.cabecera(
        "Transporte, Energía y Medio Ambiente",
        "Infraestructura de movilidad por parròquia, transición energética "
        "(energías renovables), cobertura forestal, emisiones de CO2 per cápita "
        "y calidad del aire del Principado de Andorra.",
    )

    tab_trans, tab_amb = st.tabs(
        [
            "🚌 Transporte y Movilidad Territorial",
            "🌲 Energía, Bosques y Clima",
        ]
    )
    with tab_trans:
        _seccion_transporte()
    with tab_amb:
        _seccion_energia_ambiente()
