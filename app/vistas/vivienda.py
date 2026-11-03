"""Vista de Vivienda/Mercado inmobiliario de la App_Streamlit de Cerebro Andorra.

Presenta los precios de venta y de alquiler en €/m² de las 7 parròquies a partir
de los datos procesados de Indomio, mostrando cada cifra exclusivamente a través
de ``cifra_gobernada`` para garantizar el principio rector del proyecto ("0
cifras sin fuente, sin vigencia y sin fecha de prueba"). Los precios de Indomio
llevan la Etiqueta_Linaje PROXY, que ``cifra_gobernada`` distingue visualmente
con un badge de color propio (Req 7.1, 7.2, 7.3).

La actividad inmobiliaria oficial se representa con las inversiones
inmobiliarias registradas por año (linaje OBSERVADO, fuente oficial), que sí
están integradas en el lago. El dataset ``oficial_820`` sigue excluido (su
contenido real son umbrales de pobreza, reclasificados aparte); el recuento de
transacciones de compraventa desglosado por parròquia no existe con licencia
abierta y queda documentado como límite (Req 7.4, 7.5).

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
import estilos  # noqa: E402 - import tras ajustar sys.path

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


def _muestra_inversiones_oficiales() -> None:
    """Muestra las inversiones inmobiliarias oficiales (linaje OBSERVADO).

    Sustituye al antiguo indicador de "Dato no disponible": en vez de declarar
    ausente la actividad inmobiliaria oficial, muestra el número de inversiones
    inmobiliarias registradas por año (fuente oficial, OBSERVADO) con su cifra
    gobernada y su serie, y aclara el límite real: no hay desglose por parròquia
    ni un recuento de transacciones de compraventa con licencia abierta.
    """
    st.subheader("Actividad inmobiliaria oficial")
    st.caption(
        "Inversiones inmobiliarias registradas en Andorra por año (datos "
        "oficiales, linaje OBSERVADO)."
    )

    inversiones = carga_datos.carga_inversiones()
    if inversiones is None or inversiones.empty:
        with st.container(border=True):
            st.warning("Inversiones inmobiliarias oficiales: Dato no disponible")
            st.caption(
                "Motivo: no se pudieron cargar los datos procesados de "
                "inversiones inmobiliarias."
            )
        return

    datos = inversiones.copy()
    datos["anio"] = pd.to_numeric(datos.get("anio"), errors="coerce")
    datos["num_inversiones"] = pd.to_numeric(
        datos.get("num_inversiones"), errors="coerce"
    )
    datos = datos.dropna(subset=["anio", "num_inversiones"]).sort_values("anio")
    if datos.empty:
        with st.container(border=True):
            st.warning("Inversiones inmobiliarias oficiales: Dato no disponible")
            st.caption("Motivo: no hay registros de inversiones utilizables.")
        return

    # Cifra gobernada del año más reciente + serie histórica.
    fila = datos.iloc[-1]
    anio = int(fila["anio"])
    with st.container(border=True):
        componentes.cifra_gobernada(
            f"Inversiones inmobiliarias registradas ({anio})",
            int(fila["num_inversiones"]),
            {
                "fuente": fila.get("fuente"),
                "vigencia": str(anio),
                "fecha_prueba": fila.get("fecha_prueba"),
            },
            fila.get("linaje"),
            id_fuente="F04",
        )

        try:
            import plotly.express as px

            figura = px.bar(
                datos,
                x="anio",
                y="num_inversiones",
                labels={"anio": "Año", "num_inversiones": "Nº de inversiones"},
                text="num_inversiones",
            )
            figura.update_traces(textposition="outside")
            figura.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0})
            st.plotly_chart(figura, use_container_width=True)
        except Exception as error:  # noqa: BLE001 - degradación segura
            print(f"[vivienda] No se pudo importar plotly: {error}.")

    st.info(
        "Límite actual: la fuente oficial publica el total nacional de "
        "inversiones, no el número de transacciones de compraventa desglosado "
        "por parròquia. Ese nivel de detalle queda pendiente y se documenta en "
        "la bitácora, sin inventar cifras."
    )


def render() -> None:
    """Renderiza la Vista_Vivienda completa."""
    estilos.cabecera(
        "Vivienda y mercado inmobiliario",
        "Precios de oferta de venta y alquiler por m² (linaje PROXY, de "
        "Indomio) y la actividad inmobiliaria oficial de Andorra.",
    )

    precios = carga_datos.carga_precios()
    if precios is None or precios.empty:
        st.warning(
            "Precios de vivienda: Dato no disponible. No se pudieron cargar los "
            "datos procesados de precios."
        )
    else:
        _muestra_precios(precios)

    st.divider()
    _muestra_inversiones_oficiales()