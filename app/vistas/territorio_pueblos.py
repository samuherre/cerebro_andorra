"""Vista "Territorio, Pueblos y Suelo (¿Qué hay en el suelo?)" de Cerebro Andorra.

Integra tres conjuntos gobernados (linaje OBSERVADO):
1. ``poblacion_poble.csv`` (``F15``): demografía oficial a escala de los 44
   pueblos (*pobles*) dentro de las 7 parròquies (2020-2025).
2. ``edificios_suelo.csv`` (``F17``): morfología constructiva, usos del suelo y
   número de plantas (``building:levels``) de los 1.144 edificios de OSM.
3. ``equipamientos_suelo.csv`` (``F18``): servicios, hoteles, comercios y
   equipamientos sobre el territorio.
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

if not hasattr(carga_datos, "carga_poblacion_poble"):
    importlib.reload(carga_datos)

_ID_FUENTE_POBLES = "F15"
_ID_FUENTE_EDIFICIOS = "F17"
_ID_FUENTE_EQUIP = "F18"


def _metadato_fila(fila: pd.Series, vigencia: "str | None" = None) -> dict:
    return {
        "fuente": fila.get("fuente"),
        "vigencia": str(vigencia if vigencia is not None else fila.get("vigencia", "")),
        "fecha_prueba": fila.get("fecha_prueba"),
    }


def _seccion_pobles() -> None:
    st.subheader("Los 44 Pueblos (*Pobles*) de Andorra")
    st.caption(
        "Unidad estadística oficial más pequeña dentro de cada parròquia "
        "(Departament d'Estadística d'Andorra, linaje OBSERVADO)."
    )

    if not hasattr(carga_datos, "carga_poblacion_poble"):
        importlib.reload(carga_datos)
    pobles = carga_datos.carga_poblacion_poble()
    if pobles is None or pobles.empty:
        st.info("No hay datos procesados de población por poble disponibles.")
        return

    df = pobles.copy()
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
    df["poblacion"] = pd.to_numeric(df["poblacion"], errors="coerce")
    df = df.dropna(subset=["anio", "poblacion"])

    anios = sorted(int(a) for a in df["anio"].unique())
    parroquias = ["Todas las parròquies"] + sorted(
        str(p) for p in df["parroquia"].dropna().unique()
    )

    with st.container(border=True):
        col_p, col_a = st.columns(2)
        with col_p:
            parroquia_sel = st.selectbox(
                "Filtrar por parròquia",
                options=parroquias,
                key="pobles_parroquia",
            )
        with col_a:
            anio_sel = st.selectbox(
                "Año de consulta",
                options=anios,
                index=len(anios) - 1,
                key="pobles_anio",
            )

    df_anio = df[df["anio"] == anio_sel].copy()
    if parroquia_sel != "Todas las parròquies":
        df_anio = df_anio[df_anio["parroquia"] == parroquia_sel]

    if df_anio.empty:
        st.info("No hay registros para la selección actual.")
        return

    df_anio = df_anio.sort_values("poblacion", ascending=False)
    fila_mayor = df_anio.iloc[0]
    fila_menor = df_anio.iloc[-1]

    # Cálculo de crecimiento 2020 -> anio_sel
    anio_base = min(anios)
    df_base = df[df["anio"] == anio_base][["poble", "parroquia", "poblacion"]].rename(
        columns={"poblacion": "pob_base"}
    )
    comparado = df_anio.merge(df_base, on=["poble", "parroquia"], how="left")
    comparado["var_pct"] = (
        (comparado["poblacion"] - comparado["pob_base"])
        / comparado["pob_base"].replace(0, pd.NA)
        * 100.0
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            componentes.cifra_gobernada(
                f"Núcleo más poblado: {fila_mayor['poble']} ({fila_mayor['parroquia']})",
                f"{int(fila_mayor['poblacion']):,}".replace(",", "."),
                _metadato_fila(fila_mayor, str(anio_sel)),
                fila_mayor.get("linaje"),
                id_fuente=_ID_FUENTE_POBLES,
            )
    with col2:
        with st.container(border=True):
            componentes.cifra_gobernada(
                f"Localidades (pobles) en selección ({anio_sel})",
                len(df_anio),
                _metadato_fila(fila_mayor, str(anio_sel)),
                fila_mayor.get("linaje"),
                id_fuente=_ID_FUENTE_POBLES,
            )
    with col3:
        with st.container(border=True):
            con_crecimiento = comparado.dropna(subset=["var_pct"]).sort_values(
                "var_pct", ascending=False
            )
            if not con_crecimiento.empty and anio_sel > anio_base:
                top_crec = con_crecimiento.iloc[0]
                componentes.cifra_gobernada(
                    f"Mayor expansión ({anio_base}-{anio_sel}): {top_crec['poble']}",
                    f"+{float(top_crec['var_pct']):.1f} %",
                    _metadato_fila(top_crec, f"{anio_base}-{anio_sel}"),
                    top_crec.get("linaje"),
                    id_fuente=_ID_FUENTE_POBLES,
                )
            else:
                componentes.cifra_gobernada(
                    f"Núcleo más pequeño: {fila_menor['poble']}",
                    f"{int(fila_menor['poblacion']):,}".replace(",", "."),
                    _metadato_fila(fila_menor, str(anio_sel)),
                    fila_menor.get("linaje"),
                    id_fuente=_ID_FUENTE_POBLES,
                )

    top_mostrar = df_anio.head(20).sort_values("poblacion", ascending=True)
    try:
        import plotly.express as px

        fig = px.bar(
            top_mostrar,
            x="poblacion",
            y="poble",
            color="parroquia",
            orientation="h",
            title=f"Población por poble ({anio_sel}) · Top localidades en la selección",
            labels={
                "poblacion": "Habitantes",
                "poble": "Poble (localidad)",
                "parroquia": "Parròquia",
            },
        )
        fig.update_layout(margin={"r": 20, "t": 45, "l": 10, "b": 10}, height=520)
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass

    with st.expander("Ver tabla completa de los pueblos y su variación interanual"):
        tabla_vista = comparado[
            ["poble", "parroquia", "pob_base", "poblacion", "var_pct"]
        ].copy()
        tabla_vista["var_pct"] = tabla_vista["var_pct"].apply(
            lambda v: f"{float(v):+.1f} %" if pd.notna(v) else "—"
        )
        st.dataframe(
            tabla_vista.rename(
                columns={
                    "poble": "Poble",
                    "parroquia": "Parròquia",
                    "pob_base": f"Población ({anio_base})",
                    "poblacion": f"Población ({anio_sel})",
                    "var_pct": f"Variación ({anio_base}-{anio_sel})",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


def _seccion_suelo_edificios() -> None:
    st.subheader("¿Qué hay en el suelo? Morfología de Edificios y Alturas")
    st.caption(
        "Análisis de los polígonos de edificación catastrados en OpenStreetMap "
        "(edificios_andorra.geojson, licencia ODbL, linaje OBSERVADO)."
    )

    if not hasattr(carga_datos, "carga_edificios_suelo"):
        importlib.reload(carga_datos)
    edif = carga_datos.carga_edificios_suelo()
    if edif is None or edif.empty:
        st.info("No hay datos procesados de morfología de edificios.")
        return

    df = edif.copy()
    df["num_edificios"] = pd.to_numeric(df["num_edificios"], errors="coerce")
    df["con_pisos_declarados"] = pd.to_numeric(
        df["con_pisos_declarados"], errors="coerce"
    )
    df["pisos_medios"] = pd.to_numeric(df["pisos_medios"], errors="coerce")
    df["pisos_maximos"] = pd.to_numeric(df["pisos_maximos"], errors="coerce")
    df = df.dropna(subset=["num_edificios"])

    fila_ref = df.iloc[0]
    total_edificios = int(df["num_edificios"].sum())
    total_con_altura = int(df["con_pisos_declarados"].sum())
    altura_max = int(df["pisos_maximos"].max())

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            componentes.cifra_gobernada(
                "Total de polígonos de edificios analizados",
                f"{total_edificios:,}".replace(",", "."),
                _metadato_fila(fila_ref),
                fila_ref.get("linaje"),
                id_fuente=_ID_FUENTE_EDIFICIOS,
            )
    with col2:
        with st.container(border=True):
            componentes.cifra_gobernada(
                "Edificios con altura declarada (building:levels)",
                total_con_altura,
                _metadato_fila(fila_ref),
                fila_ref.get("linaje"),
                id_fuente=_ID_FUENTE_EDIFICIOS,
            )
    with col3:
        with st.container(border=True):
            componentes.cifra_gobernada(
                "Altura máxima registrada (plantas sobre rasante)",
                f"{altura_max} plantas",
                _metadQh := _metadato_fila(fila_ref),
                fila_ref.get("linaje"),
                id_fuente=_ID_FUENTE_EDIFICIOS,
            )

    # Excluir "Edificación sin uso específico" en el gráfico detallado para ver usos tipificados
    especificos = df[df["categoria_osm"] != "Edificación sin uso específico"].copy()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if not especificos.empty:
            try:
                import plotly.express as px

                fig_usos = px.bar(
                    especificos.sort_values("num_edificios", ascending=True),
                    x="num_edificios",
                    y="categoria_osm",
                    color="uso_suelo",
                    orientation="h",
                    title="Edificios con tipología específica declarada",
                    labels={
                        "num_edificios": "Nº de edificios",
                        "categoria_osm": "Tipología",
                        "uso_suelo": "Uso del suelo",
                    },
                )
                fig_usos.update_layout(
                    margin={"r": 10, "t": 40, "l": 10, "b": 10}, height=400
                )
                st.plotly_chart(fig_usos, use_container_width=True)
            except Exception:
                pass

    with col_g2:
        con_pisos = df[df["pisos_maximos"] > 0].sort_values(
            "pisos_medios", ascending=True
        )
        if not con_pisos.empty:
            try:
                import plotly.express as px

                fig_alt = px.bar(
                    con_pisos,
                    x="pisos_medios",
                    y="categoria_osm",
                    color="uso_suelo",
                    orientation="h",
                    title="Altura media (nº de plantas) según tipología constructiva",
                    labels={
                        "pisos_medios": "Plantas medias",
                        "categoria_osm": "Tipología",
                        "uso_suelo": "Uso del suelo",
                    },
                )
                fig_alt.update_layout(
                    margin={"r": 10, "t": 40, "l": 10, "b": 10}, height=400
                )
                st.plotly_chart(fig_alt, use_container_width=True)
            except Exception:
                pass

    st.dataframe(
        df[
            [
                "uso_suelo",
                "categoria_osm",
                "num_edificios",
                "con_pisos_declarados",
                "pisos_medios",
                "pisos_maximos",
            ]
        ].rename(
            columns={
                "uso_suelo": "Uso del suelo",
                "categoria_osm": "Categoría constructiva",
                "num_edificios": "Nº edificios",
                "con_pisos_declarados": "Con nº plantas",
                "pisos_medios": "Plantas medias",
                "pisos_maximos": "Plantas máx.",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def render() -> None:
    """Renderiza la vista de Territorio, Pueblos y Suelo."""
    estilos.cabecera(
        "Territorio, Pueblos y Suelo",
        "Desagregación territorial en los 44 pueblos (pobles) de Andorra y "
        "radiografía de qué hay construido en el suelo (usos, tipologías y "
        "alturas de edificación).",
    )

    tab_pobles, tab_suelo = st.tabs(
        [
            "🏘️ Los 44 Pueblos (*Pobles*) de Andorra",
            "🏗️ ¿Qué hay en el suelo? (Edificios y Alturas)",
        ]
    )
    with tab_pobles:
        _seccion_pobles()
    with tab_suelo:
        _seccion_suelo_edificios()
