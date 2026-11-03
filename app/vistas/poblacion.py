"""Vista Gente/Población de la App_Streamlit de Cerebro Andorra (Versión Estilizada)."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de módulos ---------------
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos
import estilos
from componentes import cifra_gobernada

ANIO_MIN = 2020
ANIO_MAX = 2025
_ID_FUENTE_DESGLOSES = "F10"
_ID_FUENTE_UMBRALES = "F11"
_ID_FUENTE_FECUNDIDAD = "F12"
_ARCHIVO_UMBRALES = "umbrales_pobreza.csv"
_ARCHIVO_FECUNDIDAD = "tasa_fecundidad.csv"
_TOP_N_NACIONALIDAD = 8
_ETIQUETA_OTROS = "Otros"
_CATEGORIA_ALTRES = "ALTRES NACIONALITATS"

# Paleta y estilo UI consistente para gráficos
THEME_PLOTLY = {
    "background": "rgba(0,0,0,0)",
    "paper_bg": "rgba(0,0,0,0)",
    "font_color": "#E0E6ED",
    "grid_color": "#2A2F3D",
    "primary": "#3B82F6",
    "secondary": "#10B981",
    "accent": "#F59E0B",
    "accent_female": "#EC4899",
    "purple": "#8B5CF6",
}


def _aplicar_estilo_grafico(figura, titulo, xaxis="", yaxis=""):
    """Aplica una plantilla estética oscura y limpia a las figuras de Plotly."""
    figura.update_layout(
        title=dict(text=titulo, font=dict(size=16, color="#FFFFFF")),
        xaxis_title=xaxis,
        yaxis_title=yaxis,
        paper_bgcolor=THEME_PLOTLY["paper_bg"],
        plot_bgcolor=THEME_PLOTLY["background"],
        font=dict(color=THEME_PLOTLY["font_color"], family="sans-serif"),
        margin=dict(l=20, r=20, t=50, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor=THEME_PLOTLY["grid_color"],
            zerolinecolor=THEME_PLOTLY["grid_color"],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=THEME_PLOTLY["grid_color"],
            zerolinecolor=THEME_PLOTLY["grid_color"],
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(color=THEME_PLOTLY["font_color"])
        ),
    )
    return figura


def _construye_metadato(fila: "pd.Series") -> "dict | None":
    campos = ("fuente", "vigencia", "fecha_prueba")
    if not all(campo in fila.index for campo in campos):
        return None
    return {campo: fila[campo] for campo in campos}


def _linaje_de_fila(fila: "pd.Series") -> "str | None":
    if "linaje" not in fila.index:
        return None
    valor = fila["linaje"]
    if valor is None or pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto or None


def _anios_disponibles(df: "pd.DataFrame") -> "list[int]":
    return sorted(
        int(a)
        for a in pd.to_numeric(df["anio"], errors="coerce").dropna().unique()
        if ANIO_MIN <= int(a) <= ANIO_MAX
    )


def _filtra_seleccion(
    df: "pd.DataFrame | None", parroquia: str, anio: int
) -> "pd.DataFrame | None":
    if df is None or df.empty:
        return None
    if "parroquia" not in df.columns or "anio" not in df.columns:
        return None
    seleccion = df[
        (df["parroquia"] == parroquia)
        & (pd.to_numeric(df["anio"], errors="coerce") == anio)
    ]
    return None if seleccion.empty else seleccion


def _plotly():
    try:
        import plotly.graph_objects as go
        return go
    except Exception:
        return None


def _ordena_tramos_edad(categorias: "list[str]") -> "list[str]":
    import re

    def clave(etiqueta: str) -> int:
        numeros = re.findall(r"\d+", str(etiqueta))
        return int(numeros[0]) if numeros else 10**6

    return sorted(categorias, key=clave)


# --- Secciones Visuales ---------------------------------------------------


def _piramide_edad_sexo(parroquia: str, anio: int) -> None:
    st.markdown("### Pirámide Demográfica y Reparto por Sexo")
    st.caption(
        "Perfil por tramos de edad y distribución HOME / DONA (linaje OBSERVADO)."
    )

    go = _plotly()
    edad = _filtra_seleccion(carga_datos.carga_poblacion_edad(), parroquia, anio)

    if edad is not None and "dimension" in edad.columns:
        edad = edad[edad["dimension"] == "edad_5"]
        if edad.empty:
            edad = None

    if edad is None:
        st.info(f"Sin datos de edad para {parroquia} en {anio}.")
    else:
        tramos = _ordena_tramos_edad(list(edad["categoria"].unique()))
        valores_por_tramo = {
            str(fila["categoria"]): pd.to_numeric(
                fila["valor"], errors="coerce"
            )
            for _, fila in edad.iterrows()
        }
        valores = [valores_por_tramo.get(t) for t in tramos]

        if go is not None:
            figura = go.Figure()
            figura.add_trace(
                go.Bar(
                    y=tramos,
                    x=valores,
                    orientation="h",
                    name="Población",
                    marker_color=THEME_PLOTLY["primary"],
                    marker_line_width=0,
                )
            )
            _aplicar_estilo_grafico(
                figura,
                f"Tramo de edad · {parroquia} · {anio}",
                "Personas",
                "Tramo de edad",
            )
            figura.update_layout(bargap=0.2)
            st.plotly_chart(figura, use_container_width=True)
        else:
            st.dataframe(
                pd.DataFrame(
                    {"Tramo de edad": tramos, "Población": valores}
                ),
                use_container_width=True,
            )

    st.markdown("---")
    sexo = _filtra_seleccion(
        carga_datos.carga_poblacion_sexo(), parroquia, anio
    )
    if sexo is None:
        st.info(f"Sin datos de sexo para {parroquia} en {anio}.")
        return

    fila_home = sexo[sexo["categoria"] == "HOME"]
    fila_dona = sexo[sexo["categoria"] == "DONA"]
    valor_home = (
        pd.to_numeric(fila_home.iloc[0]["valor"], errors="coerce")
        if not fila_home.empty
        else None
    )
    valor_dona = (
        pd.to_numeric(fila_dona.iloc[0]["valor"], errors="coerce")
        if not fila_dona.empty
        else None
    )

    if go is not None and valor_home is not None and valor_dona is not None:
        figura_sexo = go.Figure()
        figura_sexo.add_trace(
            go.Bar(
                y=["Sexo"],
                x=[-int(valor_home)],
                orientation="h",
                name="Hombres (HOME)",
                marker_color=THEME_PLOTLY["primary"],
                customdata=[int(valor_home)],
                hovertemplate="%{customdata} hombres<extra></extra>",
            )
        )
        figura_sexo.add_trace(
            go.Bar(
                y=["Sexo"],
                x=[int(valor_dona)],
                orientation="h",
                name="Mujeres (DONA)",
                marker_color=THEME_PLOTLY["accent_female"],
                hovertemplate="%{x} mujeres<extra></extra>",
            )
        )
        _aplicar_estilo_grafico(
            figura_sexo,
            f"Reparto por sexo · {parroquia} · {anio}",
            "Hombres (Izq) vs Mujeres (Der)",
            "",
        )
        figura_sexo.update_layout(barmode="relative", height=220)
        st.plotly_chart(figura_sexo, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            f = None if fila_home.empty else fila_home.iloc[0]
            cifra_gobernada(
                f"Hombres (HOME) · {parroquia} · {anio}",
                None
                if (valor_home is None or pd.isna(valor_home))
                else int(valor_home),
                None if f is None else _construye_metadato(f),
                None if f is None else _linaje_de_fila(f),
                id_fuente=_ID_FUENTE_DESGLOSES,
            )
    with col2:
        with st.container(border=True):
            f = None if fila_dona.empty else fila_dona.iloc[0]
            cifra_gobernada(
                f"Mujeres (DONA) · {parroquia} · {anio}",
                None
                if (valor_dona is None or pd.isna(valor_dona))
                else int(valor_dona),
                None if f is None else _construye_metadato(f),
                None if f is None else _linaje_de_fila(f),
                id_fuente=_ID_FUENTE_DESGLOSES,
            )


def _composicion_nacionalidad(parroquia: str, anio: int) -> None:
    st.markdown("### Composición por Nacionalidad")

    nac = _filtra_seleccion(
        carga_datos.carga_poblacion_nacionalidad(), parroquia, anio
    )
    if nac is None:
        st.info(f"Sin datos de nacionalidad para {parroquia} en {anio}.")
        return

    nac = nac.copy()
    nac["valor_num"] = pd.to_numeric(nac["valor"], errors="coerce")
    nac = nac.dropna(subset=["valor_num"])
    if nac.empty:
        st.info(f"Sin cifras de nacionalidad para {parroquia} en {anio}.")
        return

    residuo_crudo = nac[nac["categoria"] == _CATEGORIA_ALTRES][
        "valor_num"
    ].sum()
    individuales = nac[nac["categoria"] != _CATEGORIA_ALTRES].sort_values(
        "valor_num", ascending=False
    )

    top = individuales.head(_TOP_N_NACIONALIDAD)
    resto = individuales.iloc[_TOP_N_NACIONALIDAD:]["valor_num"].sum()
    otros = float(resto) + float(residuo_crudo)

    etiquetas = [str(c) for c in top["categoria"].tolist()]
    valores = [int(v) for v in top["valor_num"].tolist()]
    if otros > 0:
        etiquetas.append(_ETIQUETA_OTROS)
        valores.append(int(round(otros)))

    go = _plotly()
    if go is not None:
        figura = go.Figure(
            go.Bar(
                x=valores,
                y=etiquetas,
                orientation="h",
                marker_color=THEME_PLOTLY["secondary"],
            )
        )
        _aplicar_estilo_grafico(
            figura,
            f"Principales nacionalidades · {parroquia} · {anio}",
            "Personas",
            "",
        )
        figura.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(figura, use_container_width=True)
    else:
        st.dataframe(
            pd.DataFrame({"Nacionalidad": etiquetas, "Población": valores}),
            use_container_width=True,
        )

    fila_top = top.iloc[0]
    with st.container(border=True):
        cifra_gobernada(
            f"Nacionalidad mayoritaria ({fila_top['categoria']}) · {parroquia} · {anio}",
            int(fila_top["valor_num"]),
            _construye_metadato(fila_top),
            _linaje_de_fila(fila_top),
            id_fuente=_ID_FUENTE_DESGLOSES,
        )


def _distribucion_lugar_nacimiento(parroquia: str, anio: int) -> None:
    st.markdown("### Lugar de Nacimiento")

    lugar = _filtra_seleccion(
        carga_datos.carga_poblacion_lugar_nacimiento(), parroquia, anio
    )
    if lugar is None:
        st.info(f"Sin datos de lugar de nacimiento para {parroquia} en {anio}.")
        return

    lugar = lugar.copy()
    lugar["valor_num"] = pd.to_numeric(lugar["valor"], errors="coerce")
    lugar = lugar.dropna(subset=["valor_num"]).sort_values(
        "valor_num", ascending=False
    )
    if lugar.empty:
        st.info(
            f"Sin cifras de lugar de nacimiento para {parroquia} en {anio}."
        )
        return

    etiquetas = [str(c) for c in lugar["categoria"].tolist()]
    valores = [int(v) for v in lugar["valor_num"].tolist()]

    go = _plotly()
    if go is not None:
        figura = go.Figure(
            go.Bar(
                x=etiquetas,
                y=valores,
                marker_color=THEME_PLOTLY["purple"],
            )
        )
        _aplicar_estilo_grafico(
            figura,
            f"Lugar de origen · {parroquia} · {anio}",
            "País / Región",
            "Personas",
        )
        st.plotly_chart(figura, use_container_width=True)
    else:
        st.dataframe(
            pd.DataFrame(
                {"Lugar de nacimiento": etiquetas, "Población": valores}
            ),
            use_container_width=True,
        )

    fila_top = lugar.iloc[0]
    with st.container(border=True):
        cifra_gobernada(
            f"Lugar de nacimiento mayoritario ({fila_top['categoria']}) · {parroquia} · {anio}",
            int(fila_top["valor_num"]),
            _construye_metadato(fila_top),
            _linaje_de_fila(fila_top),
            id_fuente=_ID_FUENTE_DESGLOSES,
        )


def _bloque_poblacion_total(anio: int) -> None:
    st.subheader(f"Población Total por Parròquia ({anio})")
    df = carga_datos.carga_poblacion()
    if df is None or df.empty:
        st.warning("Datos de población no disponibles.")
        return

    df_anio = df[pd.to_numeric(df["anio"], errors="coerce") == anio]
    if df_anio.empty:
        st.warning(f"No hay cifras para {anio}.")
        return

    columnas = st.columns(3)
    for i, fila_tupla in enumerate(df_anio.itertuples(index=False)):
        fila = pd.Series(fila_tupla._asdict())
        poblacion = pd.to_numeric(fila.get("poblacion"), errors="coerce")
        with columnas[i % 3]:
            with st.container(border=True):
                cifra_gobernada(
                    etiqueta=str(fila["parroquia"]),
                    valor=None if pd.isna(poblacion) else int(poblacion),
                    metadato=_construye_metadato(fila),
                    linaje=_linaje_de_fila(fila),
                    id_fuente="F01",
                )


def _bloque_social() -> None:
    st.subheader("Indicadores Sociales de Andorra")
    st.caption(
        "Umbrales de pobreza y tasa de fecundidad oficial (linaje OBSERVADO)."
    )

    col_pobreza, col_fecundidad = st.columns(2)

    with col_pobreza:
        st.markdown("**Umbrales de pobreza (€ anuales)**")
        umbrales = carga_datos.carga_umbrales_pobreza()
        if umbrales is None or umbrales.empty:
            st.info("Sin datos de umbrales de pobreza.")
        else:
            id_umbrales = _ID_FUENTE_UMBRALES
            umbrales = umbrales.copy()
            umbrales["_valor_num"] = pd.to_numeric(
                umbrales["valor_eur"], errors="coerce"
            )
            indicadores = sorted(
                str(i) for i in umbrales["indicador"].dropna().unique()
            )
            for nombre_umbral in indicadores:
                grupo = umbrales[umbrales["indicador"] == nombre_umbral]
                grupo_num = grupo.copy()
                grupo_num["_anio_num"] = pd.to_numeric(
                    grupo_num["anio"], errors="coerce"
                )
                fila = grupo_num.sort_values("_anio_num").iloc[-1]
                valor = fila["_valor_num"]
                anio = pd.to_numeric(fila.get("anio"), errors="coerce")
                etiqueta_anio = "" if pd.isna(anio) else f" · {int(anio)}"
                with st.container(border=True):
                    cifra_gobernada(
                        f"{nombre_umbral}{etiqueta_anio}",
                        None
                        if pd.isna(valor)
                        else f"{float(valor):,.2f} €",
                        _construye_metadato(fila),
                        _linaje_de_fila(fila),
                        id_fuente=id_umbrales,
                    )

    with col_fecundidad:
        st.markdown("**Tasa de fecundidad**")
        fecundidad = carga_datos.carga_tasa_fecundidad()
        if fecundidad is None or fecundidad.empty:
            st.info("Sin datos de tasa de fecundidad.")
        else:
            id_fecundidad = _ID_FUENTE_FECUNDIDAD
            fecundidad = fecundidad.copy()
            fecundidad["_valor_num"] = pd.to_numeric(
                fecundidad["valor"], errors="coerce"
            )
            fecundidad["_anio_num"] = pd.to_numeric(
                fecundidad["anio"], errors="coerce"
            )
            fila = fecundidad.sort_values("_anio_num").iloc[-1]
            valor = fila["_valor_num"]
            anio = pd.to_numeric(fila.get("anio"), errors="coerce")
            etiqueta_anio = "" if pd.isna(anio) else f" · {int(anio)}"
            nombre_indicador = str(
                fila.get("indicador", "Tasa de fecundidad")
            )
            with st.container(border=True):
                cifra_gobernada(
                    f"{nombre_indicador}{etiqueta_anio}",
                    None if pd.isna(valor) else round(float(valor), 2),
                    _construye_metadato(fila),
                    _linaje_de_fila(fila),
                    id_fuente=id_fecundidad,
                )


# --- Función Principal (Render) --------------------------------------------


def render() -> None:
    estilos.cabecera(
        "Gente y población",
        "Demografía oficial del Departament d'Estadística d'Andorra, con "
        "linaje y gobernanza auditable en cada cifra.",
    )

    desgloses = carga_datos.carga_poblacion_desgloses()
    df_para_anios = (
        desgloses if desgloses is not None else carga_datos.carga_poblacion()
    )

    if (
        df_para_anios is None
        or df_para_anios.empty
        or "anio" not in df_para_anios.columns
    ):
        st.warning("Datos de población no disponibles.")
        return

    anios = _anios_disponibles(df_para_anios)
    if not anios:
        st.warning("No hay años en el rango en los datos procesados.")
        return

    if desgloses is not None and "parroquia" in desgloses.columns:
        parroquias = sorted(
            str(p) for p in desgloses["parroquia"].dropna().unique()
        )
    else:
        pob = carga_datos.carga_poblacion()
        parroquias = (
            sorted(str(p) for p in pob["parroquia"].dropna().unique())
            if pob is not None and "parroquia" in pob.columns
            else []
        )

    # Filtros superiores en contenedor
    with st.container(border=True):
        col_parroquia, col_anio = st.columns(2)
        with col_anio:
            anio_sel = st.selectbox(
                "Año de consulta",
                options=anios,
                index=anios.index(max(anios)),
            )
        with col_parroquia:
            parroquia_sel = (
                st.selectbox(
                    "Parròquia",
                    options=parroquias,
                )
                if parroquias
                else None
            )

    st.markdown("---")

    # Organización en pestañas para limpiar el layout vertical
    tab_totales, tab_desgloses, tab_social = st.tabs(
        [
            " Totales por Parròquia",
            f" Desgloses ({parroquia_sel or 'General'})",
            " Indicadores Sociales",
        ]
    )

    with tab_totales:
        _bloque_poblacion_total(anio_sel)

    with tab_desgloses:
        if parroquia_sel is None:
            st.info("No hay parròquies disponibles.")
        else:
            _piramide_edad_sexo(parroquia_sel, anio_sel)
            st.markdown("---")
            _composicion_nacionalidad(parroquia_sel, anio_sel)
            st.markdown("---")
            _distribucion_lugar_nacimiento(parroquia_sel, anio_sel)

    with tab_social:
        _bloque_social()