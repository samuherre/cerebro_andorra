"""Vista "Salud, Educación y Conectividad" de la App_Streamlit de Cerebro Andorra.

Integra dos fuentes gobernadas (linaje OBSERVADO):
1. ``salud_educacion_ambiente.csv`` (Banco Mundial, CC BY 4.0, ``F19``):
   - Esperanza de vida al nacer, gasto en salud (% PIB y per cápita),
     mortalidad infantil y densidad médica.
   - Penetración de Internet (% población), gasto público en educación (% PIB) y
     matriculación secundaria.
2. ``equipamientos_suelo.csv`` (OpenStreetMap vía Overpass, ODbL, ``F18``):
   - Infraestructura sanitaria, de emergencias, educativa y cultural sobre el
     territorio por parròquia.
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

if not hasattr(carga_datos, "carga_salud_ambiente"):
    importlib.reload(carga_datos)

_ID_FUENTE_WB_SECTORIAL = "F19"
_ID_FUENTE_EQUIP = "F18"


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


def _bloque_dominio_wb(df: pd.DataFrame, dominio: str, titulo: str, subtitulo: str) -> None:
    st.subheader(titulo)
    st.caption(subtitulo)

    sub = df[df["dominio"] == dominio].copy()
    if sub.empty:
        st.info("No hay indicadores disponibles para esta sección.")
        return

    sub["anio"] = pd.to_numeric(sub["anio"], errors="coerce")
    sub["valor"] = pd.to_numeric(sub["valor"], errors="coerce")
    sub = sub.dropna(subset=["anio", "valor"]).sort_values("anio")

    codigos = list(dict.fromkeys(sub["codigo"].tolist()))
    # Tarjetas resumen del último año disponible por indicador
    for inicio in range(0, len(codigos), 3):
        lote = codigos[inicio : inicio + 3]
        cols = st.columns(len(lote))
        for codigo, col in zip(lote, cols):
            filas_cod = sub[sub["codigo"] == codigo]
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

    # Selector de serie histórica para explorar la evolución
    nombres_map = {
        str(sub[sub["codigo"] == c].iloc[-1]["indicador"]): c for c in codigos
    }
    elegido_nombre = st.selectbox(
        f"Explorar serie histórica ({titulo})",
        options=list(nombres_map.keys()),
        key=f"sel_wb_{dominio}",
    )
    codigo_sel = nombres_map[elegido_nombre]
    serie = sub[sub["codigo"] == codigo_sel].sort_values("anio")
    unidad_sel = str(serie.iloc[-1].get("unidad", ""))

    try:
        import plotly.express as px

        fig = px.line(
            serie,
            x="anio",
            y="valor",
            markers=True,
            title=f"Evolución histórica: {elegido_nombre}",
            labels={"anio": "Año", "valor": f"Valor ({unidad_sel})"},
        )
        fig.update_layout(margin={"r": 10, "t": 40, "l": 10, "b": 10}, height=340)
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.dataframe(
            serie[["anio", "valor", "unidad", "fuente"]],
            use_container_width=True,
            hide_index=True,
        )


def _bloque_equipamientos_salud_educacion() -> None:
    st.subheader("Infraestructura Sanitaria, Educativa y Cultural en el Territorio")
    st.caption(
        "Equipamientos georreferenciados en OpenStreetMap (licencia ODbL, linaje OBSERVADO)."
    )

    if not hasattr(carga_datos, "carga_equipamientos_suelo"):
        importlib.reload(carga_datos)
    equip = carga_datos.carga_equipamientos_suelo()
    if equip is None or equip.empty:
        st.info("No hay datos de equipamientos territoriales procesados.")
        return

    sub = equip[
        equip["dominio"].isin(["Salud y emergencias", "Educación y cultura"])
    ].copy()
    if sub.empty:
        st.info("No se encontraron equipamientos sanitarios o educativos.")
        return

    fila_ref = sub.iloc[0]
    total_salud = int((sub["dominio"] == "Salud y emergencias").sum())
    total_edu = int((sub["dominio"] == "Educación y cultura").sum())

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            componentes.cifra_gobernada(
                "Equipamientos de Salud y Emergencias registrados",
                total_salud,
                _metadato_fila(fila_ref),
                fila_ref.get("linaje"),
                id_fuente=_ID_FUENTE_EQUIP,
            )
    with col2:
        with st.container(border=True):
            componentes.cifra_gobernada(
                "Equipamientos de Educación, Cultura y Civismo registrados",
                total_edu,
                _metadato_fila(fila_ref),
                fila_ref.get("linaje"),
                id_fuente=_ID_FUENTE_EQUIP,
            )

    resumen = (
        sub.groupby(["dominio", "tipo_equipamiento"], as_index=False)
        .size()
        .rename(columns={"size": "cantidad"})
        .sort_values("cantidad", ascending=True)
    )
    try:
        import plotly.express as px

        fig = px.bar(
            resumen,
            x="cantidad",
            y="tipo_equipamiento",
            color="dominio",
            orientation="h",
            title="Dotación de equipamientos sanitarios, educativos y cívicos por tipo",
            labels={
                "cantidad": "Nº de instalaciones",
                "tipo_equipamiento": "Tipo de equipamiento",
                "dominio": "Dominio",
            },
        )
        fig.update_layout(margin={"r": 20, "t": 40, "l": 10, "b": 10}, height=380)
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass

    with st.expander("Ver listado detallado de centros y su ubicación por parròquia"):
        st.dataframe(
            sub[["parroquia", "dominio", "tipo_equipamiento", "nombre"]].rename(
                columns={
                    "parroquia": "Parròquia",
                    "dominio": "Dominio",
                    "tipo_equipamiento": "Tipo",
                    "nombre": "Nombre / Identificador",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


def render() -> None:
    """Renderiza la vista completa de Salud, Educación y Conectividad."""
    estilos.cabecera(
        "Salud, Educación y Conectividad",
        "Indicadores de esperanza de vida, inversión sanitaria, penetración de "
        "Internet, gasto educativo y dotación de centros en el territorio de "
        "Andorra, todos con trazabilidad y linaje OBSERVADO.",
    )

    if not hasattr(carga_datos, "carga_salud_ambiente"):
        importlib.reload(carga_datos)
    df = carga_datos.carga_salud_ambiente()
    if df is None or df.empty:
        st.warning(
            "Todavía no se han cargado los indicadores sectoriales del Banco Mundial "
            "(salud_educacion_ambiente.csv)."
        )
    else:
        tab_salud, tab_edu, tab_centros = st.tabs(
            [
                "🏥 Salud y Demografía Vital",
                "🎓 Educación y Conectividad Digital",
                "📍 Centros Sanitarios y Educativos en Mapa",
            ]
        )
        with tab_salud:
            _bloque_dominio_wb(
                df,
                "salud",
                "Salud Pública y Esperanza de Vida",
                "Serie oficial del Banco Mundial (World Bank Open Data, licencia CC BY 4.0).",
            )
        with tab_edu:
            _bloque_dominio_wb(
                df,
                "educacion_conectividad",
                "Educación y Conectividad Digital",
                "Acceso a Internet, gasto público en educación y escolarización en Andorra.",
            )
        with tab_centros:
            _bloque_equipamientos_salud_educacion()
            return

    st.divider()
    _bloque_equipamientos_salud_educacion()
