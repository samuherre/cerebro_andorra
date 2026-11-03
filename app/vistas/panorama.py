"""Vista Panorama de la App_Streamlit de Cerebro Andorra (Versión Rediseñada).

Presenta un resumen ejecutivo del país con las cifras clave a partir de los datos
procesados y un modelo urbano 3D interactivo de la capital (Andorra la Vella y
Escaldes-Engordany), preservando estrictamente la gobernanza mediante
``componentes.cifra_gobernada``.
"""

import importlib
import re
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
import estilos  # noqa: E402 - import tras ajustar sys.path

if not hasattr(carga_datos, "carga_geojson_edificios"):
    importlib.reload(carga_datos)


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
        st.markdown("#### Demografía Nacional")
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


@st.cache_data
def _prepara_geojson_3d_capital() -> "dict | None":
    """Prepara los polígonos de edificación de la capital con elevación 3D y color."""
    if not hasattr(carga_datos, "carga_geojson_edificios"):
        return None
    raw = carga_datos.carga_geojson_edificios()
    if not isinstance(raw, dict) or not raw.get("features"):
        return None

    features_3d = []
    for feat in raw.get("features", []):
        geom = feat.get("geometry") or {}
        if geom.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        props = dict(feat.get("properties") or {})
        b_tag = str(props.get("building") or "yes").strip().lower()
        amenity = str(props.get("amenity") or "").strip().lower()
        tourism = str(props.get("tourism") or "").strip().lower()
        nombre = (
            props.get("name:es")
            or props.get("name")
            or props.get("name:ca")
            or ""
        )

        # Clasificación por grupo funcional y color RGBA para el mapa 3D
        if b_tag in ("government", "public", "civic") or amenity in (
            "townhall",
            "courthouse",
            "police",
            "Embassy",
        ):
            grupo = "Institucional y Gobierno"
            color = [245, 158, 11, 230]  # Ámbar / Dorado
            pisos_def = 5.0
        elif (
            b_tag in ("commercial", "retail", "office", "hotel", "supermarket")
            or tourism in ("hotel", "hostel", "apartment")
        ):
            grupo = "Comercial, Hotelero y Oficinas"
            color = [14, 165, 233, 220]  # Azul cian brillante
            pisos_def = 6.0
        elif (
            b_tag in ("hospital", "school", "university", "college", "church", "cathedral", "chapel", "sports_centre", "stadium")
            or amenity in ("hospital", "clinic", "school", "university", "place_of_worship")
        ):
            grupo = "Salud, Educación y Cultura"
            color = [16, 185, 129, 225]  # Verde esmeralda
            pisos_def = 4.5
        else:
            grupo = "Residencial y Tejido Urbano"
            color = [99, 102, 241, 185]  # Índigo urbano
            pisos_def = 4.0

        # Lectura de niveles (building:levels)
        niv_raw = props.get("building:levels")
        pisos_obs = None
        if niv_raw is not None:
            m = re.search(r"(\d+(?:\.\d+)?)", str(niv_raw))
            if m:
                val = float(m.group(1))
                if 1.0 <= val <= 30.0:
                    pisos_obs = val

        if pisos_obs is not None:
            altura_m = round(pisos_obs * 3.6, 1)
            pisos_txt = f"{int(pisos_obs)} plantas observadas ({altura_m} m)"
        else:
            altura_m = round(pisos_def * 3.5, 1)
            pisos_txt = f"~{int(pisos_def)} plantas base ({altura_m} m)"

        nombre_mostrar = str(nombre).strip() if str(nombre).strip() else f"Edificio ({grupo})"

        features_3d.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "nombre_mostrar": nombre_mostrar,
                    "grupo": grupo,
                    "altura_m": altura_m,
                    "pisos_txt": pisos_txt,
                    "color_fill": color,
                },
            }
        )

    return {"type": "FeatureCollection", "features": features_3d}


def _bloque_mapa_3d_capital() -> None:
    """Renderiza el visor 3D interactivo de Andorra la Vella (Capital)."""
    if not hasattr(st, "pydeck_chart"):
        return

    geojson_3d = _prepara_geojson_3d_capital()
    if not geojson_3d or not geojson_3d.get("features"):
        return

    st.subheader("🏙️ Gemelo Digital 3D: Andorra la Vella (Capital) y Valle Central")
    st.caption(
        "Modelo tridimensional interactivo de los **1.144 edificios catastrados** en el "
        "núcleo urbano de la capital (**Andorra la Vella** y **Escaldes-Engordany**). "
        "Mantén presionado `Ctrl + clic izquierdo` (o clic derecho) y arrastra para "
        "inclinar y rotar la cámara 3D. Fuente: OpenStreetMap (`F17`, licencia ODbL, linaje `OBSERVADO`)."
    )

    camaras = {
        "🏛️ Centro Histórico e Institucional (Andorra la Vella)": {
            "lat": 42.5068,
            "lon": 1.5218,
            "zoom": 15.5,
            "pitch": 58,
            "bearing": -22,
        },
        "🛍️ Eje Comercial Meritxell – Vivand (Escaldes-Engordany)": {
            "lat": 42.5088,
            "lon": 1.5345,
            "zoom": 15.3,
            "pitch": 58,
            "bearing": 28,
        },
        "🏔️ Vista Panorámica del Valle de la Capital (Completa)": {
            "lat": 42.5078,
            "lon": 1.5275,
            "zoom": 14.3,
            "pitch": 55,
            "bearing": -15,
        },
    }

    estilos_mapa = {
        "Modo Noche 3D (Alto Contraste)": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        "Modo Día 3D (Claro)": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        "Modo Callejero Detallado": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    }

    col_cam, col_est = st.columns([2, 1])
    with col_cam:
        cam_sel = st.selectbox(
            "Enfoque de cámara 3D sobre la capital",
            options=list(camaras.keys()),
            key="panorama_camara_3d",
        )
    with col_est:
        est_sel = st.selectbox(
            "Estilo cartográfico base",
            options=list(estilos_mapa.keys()),
            key="panorama_estilo_3d",
        )

    cfg_cam = camaras[cam_sel]

    try:
        import pydeck as pdk

        capa_edificios = pdk.Layer(
            "GeoJsonLayer",
            data=geojson_3d,
            opacity=0.88,
            stroked=True,
            filled=True,
            extruded=True,
            wireframe=True,
            get_elevation="properties.altura_m",
            elevation_scale=1.2,
            get_fill_color="properties.color_fill",
            get_line_color=[255, 255, 255, 90],
            pickable=True,
            auto_highlight=True,
        )

        vista_3d = pdk.ViewState(
            latitude=cfg_cam["lat"],
            longitude=cfg_cam["lon"],
            zoom=cfg_cam["zoom"],
            pitch=cfg_cam["pitch"],
            bearing=cfg_cam["bearing"],
            min_zoom=11,
            max_zoom=18,
        )

        tooltip = {
            "html": (
                "<b>{nombre_mostrar}</b><br/>"
                "Uso: {grupo}<br/>"
                "Altura: {pisos_txt}<br/>"
                "<span style='font-size:11px;opacity:0.85;'>Fuente: F17 · OpenStreetMap (OBSERVADO)</span>"
            ),
            "style": {
                "backgroundColor": "#0f172a",
                "color": "#f8fafc",
                "fontSize": "12px",
                "borderRadius": "6px",
                "padding": "8px 10px",
            },
        }

        deck = pdk.Deck(
            layers=[capa_edificios],
            initial_view_state=vista_3d,
            map_style=estilos_mapa[est_sel],
            tooltip=tooltip,
        )

        st.pydeck_chart(deck, use_container_width=True, height=500)

        st.markdown(
            "🟨 **Institucional y Gobierno** &nbsp;|&nbsp; "
            "🟦 **Comercial, Hotelero y Oficinas** &nbsp;|&nbsp; "
            "🟩 **Salud, Educación y Cultura** &nbsp;|&nbsp; "
            "🟪 **Residencial y Tejido Urbano** "
            "— *Elevación proporcional a `building:levels` (plantas sobre rasante, fuente `F17`).*"
        )
    except Exception as error:  # noqa: BLE001
        st.info(f"Visor 3D no disponible en este entorno ({error}).")


def render() -> None:
    """Renderiza la Vista Panorama estilizada."""
    estilos.cabecera(
        "Panorama general",
        "Resumen macro con los indicadores fundamentales del Principado de "
        "Andorra y gemelo urbano 3D de su capital. Toda cifra cuenta con su "
        "trazabilidad, vigencia y linaje auditable.",
    )

    # Sección de KPIs Principales
    st.subheader("Indicadores Clave del País")

    columna_poblacion, columna_precio = st.columns(2)

    with columna_poblacion:
        _cifra_poblacion_total()

    with columna_precio:
        _cifra_precio_venta_medio()

    # Segunda fila de resumen multisectorial (Territorio, Salud/Educación, Ambiente/Transporte)
    pobles = (
        carga_datos.carga_poblacion_poble()
        if hasattr(carga_datos, "carga_poblacion_poble")
        else None
    )
    edif = (
        carga_datos.carga_edificios_suelo()
        if hasattr(carga_datos, "carga_edificios_suelo")
        else None
    )
    salud_amb = (
        carga_datos.carga_salud_ambiente()
        if hasattr(carga_datos, "carga_salud_ambiente")
        else None
    )

    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        with st.container(border=True):
            st.markdown("#### 🏘️ Pueblos (*Pobles*)")
            if not _es_dataframe_vacio(pobles):
                anios_p = pd.to_numeric(pobles.get("anio"), errors="coerce").dropna()
                if not anios_p.empty:
                    a_max = int(anios_p.max())
                    sub_p = pobles[pd.to_numeric(pobles["anio"], errors="coerce") == a_max]
                    f_p = sub_p.iloc[0]
                    componentes.cifra_gobernada(
                        f"Localidades (pobles) censadas ({a_max})",
                        len(sub_p),
                        _metadato_desde_fila(f_p, str(a_max)),
                        f_p.get("linaje"),
                        id_fuente="F15",
                    )
            else:
                st.caption("Ejecuta el pipeline para ver los 44 pueblos.")

    with col_t2:
        with st.container(border=True):
            st.markdown("#### 🏗️ Huella Urbana y Suelo")
            if not _es_dataframe_vacio(edif):
                nums_e = pd.to_numeric(edif.get("num_edificios"), errors="coerce").dropna()
                f_e = edif.iloc[0]
                vig_e = str(f_e.get("vigencia", "2026"))
                componentes.cifra_gobernada(
                    f"Edificios catastrados ({vig_e})",
                    f"{int(nums_e.sum()):,}".replace(",", "."),
                    _metadato_desde_fila(f_e, vig_e),
                    f_e.get("linaje"),
                    id_fuente="F17",
                )
            else:
                st.caption("Ejecuta el pipeline para ver el catastro de edificios.")

    with col_t3:
        with st.container(border=True):
            st.markdown("#### 🌲 Salud, Energía y Clima")
            if not _es_dataframe_vacio(salud_amb):
                s_valid = salud_amb.copy()
                s_valid["anio"] = pd.to_numeric(s_valid.get("anio"), errors="coerce")
                s_valid["valor"] = pd.to_numeric(s_valid.get("valor"), errors="coerce")
                s_valid = s_valid.dropna(subset=["anio", "valor"]).sort_values("anio")
                if not s_valid.empty:
                    f_s = s_valid.iloc[-1]
                    a_s = int(f_s["anio"])
                    u_s = str(f_s.get("unidad", "")).strip()
                    componentes.cifra_gobernada(
                        f"{f_s['indicador']} ({a_s})",
                        f"{float(f_s['valor']):.2f} {u_s}".strip(),
                        _metadato_desde_fila(f_s, str(a_s)),
                        f_s.get("linaje"),
                        id_fuente="F19",
                    )
            else:
                st.caption("Indicadores sectoriales de salud y medio ambiente.")

    st.divider()

    # Mapa 3D de la capital de Andorra (Andorra la Vella y Escaldes-Engordany)
    _bloque_mapa_3d_capital()

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
