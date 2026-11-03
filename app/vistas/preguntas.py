"""Vista "Andorra en preguntas" de la App_Streamlit de Cerebro Andorra (Versión Rediseñada).

Esta vista está redactada en tono FAQ orientado a usuario final: cada
Pregunta_Usuario se plantea como un enunciado en lenguaje natural terminado en
``?`` y, cuando el lago tiene datos, se responde con una respuesta visual y una
cifra gobernada; cuando no los tiene, la pregunta queda declarada como pendiente
con un motivo real no vacío (Req 7.1, 7.6, 7.7).
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
import estilos  # noqa: E402 - import tras ajustar sys.path

_TEXTO_OFERTA_PROXY = (
    "Precio de oferta de anuncios de Indomio (linaje PROXY): no es una "
    "transacción real."
)

_CLAVES_POBLACION = ("poblac", "798")
_CLAVES_PRECIOS = ("precios_vivienda", "indomio")
_CLAVES_TURISMO = ("turismo", "681")
_CLAVES_ECONOMIA = ("economia_worldbank", "world bank", "banco mundial")
_CLAVES_EMPLEO = ("salario_sector", "2844", "sector d'activitat")
_CLAVES_INVERSIONES = ("inversiones_inmobiliarias", "2729", "inversions")

_PARTIDA_TOTAL_TURISMO = "TOTAL PRESSUPOST DE DESPESES"

_CODIGO_PIB = "NY.GDP.MKTP.CD"
_CLAVE_INDICADOR_PIB = "pib"

_PENDIENTES_BASE = [
    {
        "pregunta": "¿Cómo se reparten las inversiones inmobiliarias por parròquia?",
        "motivo": (
            "El total nacional de inversiones inmobiliarias sí está integrado "
            "(ver «¿Cuántas inversiones inmobiliarias hay?»), pero la fuente "
            "oficial no publica el desglose por parròquia con licencia clara; "
            "ese nivel de detalle queda pendiente y no se inventa una cifra."
        ),
    },
    {
        "pregunta": "¿Qué tan segura es cada parròquia?",
        "motivo": (
            "No se encontró una fuente abierta y de licencia clara de seguridad o "
            "criminalidad por parròquia en Andorra; se documentó el intento en la "
            "bitácora y la pregunta queda pendiente sin inventar datos."
        ),
    },
]


def _euros_es(valor: float) -> str:
    """Formatea un importe en euros con separador de miles en estilo español."""
    return (
        f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        + " €"
    )


def _es_dataframe_vacio(datos) -> bool:
    """Indica si el argumento no es un DataFrame utilizable."""
    if datos is None:
        return True
    if not isinstance(datos, pd.DataFrame):
        return True
    return datos.empty


def _id_fuente_por_nombre(inventario, *claves: str) -> "str | None":
    """Resuelve el ID_Fuente de una fuente buscando subcadenas en su ``nombre``."""
    if _es_dataframe_vacio(inventario):
        return None
    if "nombre" not in inventario.columns or "id_fuente" not in inventario.columns:
        return None

    claves_norm = [clave.lower() for clave in claves]
    for _, fila in inventario.iterrows():
        nombre = str(fila.get("nombre", "")).lower()
        if any(clave in nombre for clave in claves_norm):
            id_fuente = fila.get("id_fuente")
            if id_fuente is None or str(id_fuente).strip() == "":
                return None
            return str(id_fuente).strip()
    return None


def _metadato_desde_fila(fila: "pd.Series", vigencia) -> dict:
    """Construye el Metadato_Cifra a partir de una fila procesada."""
    return {
        "fuente": fila.get("fuente"),
        "vigencia": vigencia,
        "fecha_prueba": fila.get("fecha_prueba"),
    }


def _respuesta_gobernada(respuesta: "dict | None") -> bool:
    """Indica si una respuesta trae Metadato_Cifra y Etiqueta_Linaje completos."""
    if not isinstance(respuesta, dict):
        return False

    linaje = respuesta.get("linaje")
    if linaje is None or str(linaje).strip() == "":
        return False

    metadato = respuesta.get("metadato")
    if not isinstance(metadato, dict):
        return False

    for clave in ("fuente", "vigencia", "fecha_prueba"):
        valor = metadato.get(clave)
        if valor is None or str(valor).strip() == "":
            return False

    return True


def _respuesta_poblacion(inventario) -> "dict | None":
    """Construye la respuesta a "¿cuánta gente vive en Andorra?"."""
    poblacion = carga_datos.carga_poblacion()
    if _es_dataframe_vacio(poblacion):
        return None

    anios = pd.to_numeric(poblacion.get("anio"), errors="coerce").dropna()
    if anios.empty:
        return None

    anio_reciente = int(anios.max())
    filas_anio = poblacion[
        pd.to_numeric(poblacion["anio"], errors="coerce") == anio_reciente
    ]
    poblaciones = pd.to_numeric(
        filas_anio.get("poblacion"), errors="coerce"
    ).dropna()
    if poblaciones.empty:
        return None

    poblacion_total = int(poblaciones.sum())
    fila_ref = filas_anio.iloc[0]

    return {
        "pregunta": "¿Cuánta gente vive en Andorra?",
        "etiqueta": f"Población total de Andorra ({anio_reciente})",
        "valor": f"{poblacion_total:,}".replace(",", "."),
        "metadato": _metadato_desde_fila(fila_ref, str(anio_reciente)),
        "linaje": fila_ref.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, *_CLAVES_POBLACION),
        "nota": "Suma de la población de las 7 parròquies del año más reciente.",
    }


def _respuesta_precio_m2(inventario) -> "dict | None":
    """Construye la respuesta a "¿cuánto vale el metro cuadrado?"."""
    precios = carga_datos.carga_precios()
    if _es_dataframe_vacio(precios):
        return None

    ventas = pd.to_numeric(precios.get("precio_venta"), errors="coerce").dropna()
    if ventas.empty:
        return None

    fila_ref = precios.iloc[0]
    vigencia = fila_ref.get("vigencia")
    if vigencia is None or str(vigencia).strip() == "":
        return None

    precio_medio = round(float(ventas.mean()), 2)

    return {
        "pregunta": "¿Cuánto vale el metro cuadrado en Andorra?",
        "etiqueta": f"Precio de venta medio en €/m² ({vigencia})",
        "valor": f"{precio_medio:.2f}",
        "metadato": _metadato_desde_fila(fila_ref, vigencia),
        "linaje": fila_ref.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, *_CLAVES_PRECIOS),
        "nota": _TEXTO_OFERTA_PROXY,
    }


def _respuesta_turismo(inventario) -> "dict | None":
    """Construye la respuesta a "¿cuánto pesa el turismo?"."""
    turismo = carga_datos.carga_turismo()
    if _es_dataframe_vacio(turismo):
        return None
    if "partida" not in turismo.columns:
        return None

    totales = turismo[
        turismo["partida"].astype(str).str.strip().str.upper()
        == _PARTIDA_TOTAL_TURISMO
    ]
    if totales.empty:
        return None

    periodos = pd.to_numeric(totales.get("periodo"), errors="coerce").dropna()
    if periodos.empty:
        return None

    periodo_reciente = int(periodos.max())
    filas_periodo = totales[
        pd.to_numeric(totales["periodo"], errors="coerce") == periodo_reciente
    ]
    valores = pd.to_numeric(
        filas_periodo.get("valor_eur"), errors="coerce"
    ).dropna()
    if valores.empty:
        return None

    total_eur = float(valores.iloc[0])
    fila_ref = filas_periodo.iloc[0]

    return {
        "pregunta": "¿Cuánto pesa el turismo en el presupuesto?",
        "etiqueta": f"Total del presupuesto de turismo en € ({periodo_reciente})",
        "valor": f"{total_eur:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
        "metadato": _metadato_desde_fila(fila_ref, str(periodo_reciente)),
        "linaje": fila_ref.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, *_CLAVES_TURISMO),
        "nota": (
            "Partida «TOTAL PRESSUPOST DE DESPESES» de Andorra Turisme, SAU del "
            "periodo más reciente."
        ),
    }


def _respuesta_economia(inventario) -> "dict | None":
    """Construye la respuesta a "¿cómo evoluciona la economía de Andorra?"."""
    economia = carga_datos.carga_economia()
    if _es_dataframe_vacio(economia):
        return None

    mascara = pd.Series(False, index=economia.index)
    if "codigo" in economia.columns:
        mascara = mascara | (
            economia["codigo"].astype(str).str.strip().str.upper()
            == _CODIGO_PIB.upper()
        )
    if "indicador" in economia.columns:
        mascara = mascara | economia["indicador"].astype(str).str.lower().str.contains(
            _CLAVE_INDICADOR_PIB, na=False
        )

    pib = economia[mascara]
    if pib.empty:
        return None

    anios = pd.to_numeric(pib.get("anio"), errors="coerce")
    valores = pd.to_numeric(pib.get("valor"), errors="coerce")
    pib_valido = pib[anios.notna() & valores.notna()]
    if pib_valido.empty:
        return None

    anios_validos = pd.to_numeric(pib_valido["anio"], errors="coerce")
    anio_reciente = int(anios_validos.max())
    fila_ref = pib_valido[anios_validos == anio_reciente].iloc[0]
    valor_pib = float(pd.to_numeric(fila_ref.get("valor"), errors="coerce"))
    unidad = str(fila_ref.get("unidad", "")).strip()

    valor_formateado = (
        f"{valor_pib:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    if unidad:
        valor_formateado = f"{valor_formateado} {unidad}"

    etiqueta_unidad = f" ({unidad})" if unidad else ""

    return {
        "pregunta": "¿Cómo evoluciona la economía de Andorra?",
        "etiqueta": f"PIB de Andorra{etiqueta_unidad} ({anio_reciente})",
        "valor": valor_formateado,
        "metadato": _metadato_desde_fila(fila_ref, str(anio_reciente)),
        "linaje": fila_ref.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, *_CLAVES_ECONOMIA),
        "nota": (
            "Producto Interior Bruto más reciente publicado por el Banco Mundial "
            "(World Bank Open Data) para Andorra."
        ),
    }


def _respuesta_empleo(inventario) -> "dict | None":
    """Construye la respuesta a "¿en qué sectores trabaja la gente?"."""
    salario = carga_datos.carga_salario_sector()
    if _es_dataframe_vacio(salario):
        return None
    if "sector" not in salario.columns or "salario_medio" not in salario.columns:
        return None

    datos = salario.copy()
    datos["salario_medio"] = pd.to_numeric(
        datos["salario_medio"], errors="coerce"
    )
    datos = datos.dropna(subset=["salario_medio"])
    if datos.empty:
        return None

    es_total = datos.get("es_total").astype(str).str.strip() == "1"
    sectores = datos[~es_total]
    if sectores.empty:
        return None

    # Sector mejor pagado como titular de la respuesta.
    fila_top = sectores.loc[sectores["salario_medio"].idxmax()]
    fila_ref = datos.iloc[0]
    vigencia = fila_ref.get("vigencia")
    if vigencia is None or str(vigencia).strip() == "":
        return None

    n_sectores = int(sectores["sector"].nunique())

    return {
        "pregunta": "¿En qué sectores trabaja la gente y cuánto se gana?",
        "etiqueta": (
            f"Sector mejor pagado: {fila_top['sector']} ({vigencia})"
        ),
        "valor": _euros_es(float(fila_top["salario_medio"])),
        "metadato": _metadato_desde_fila(fila_ref, vigencia),
        "linaje": fila_ref.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, *_CLAVES_EMPLEO),
        "nota": (
            f"Salario medio mensual por sector de actividad en {n_sectores} "
            "sectores (CAEA nivel 1). El detalle completo está en la vista "
            "Economía."
        ),
    }


def _respuesta_inversiones(inventario) -> "dict | None":
    """Construye la respuesta a "¿cuántas inversiones inmobiliarias hay?"."""
    inversiones = carga_datos.carga_inversiones()
    if _es_dataframe_vacio(inversiones):
        return None
    if "anio" not in inversiones.columns or "num_inversiones" not in inversiones.columns:
        return None

    anios = pd.to_numeric(inversiones["anio"], errors="coerce").dropna()
    if anios.empty:
        return None

    anio_reciente = int(anios.max())
    filas = inversiones[
        pd.to_numeric(inversiones["anio"], errors="coerce") == anio_reciente
    ]
    nums = pd.to_numeric(filas.get("num_inversiones"), errors="coerce").dropna()
    if nums.empty:
        return None

    num = int(nums.iloc[0])
    fila_ref = filas.iloc[0]

    return {
        "pregunta": "¿Cuántas inversiones inmobiliarias hay?",
        "etiqueta": f"Inversiones inmobiliarias ({anio_reciente})",
        "valor": f"{num:,}".replace(",", "."),
        "metadato": _metadato_desde_fila(fila_ref, str(anio_reciente)),
        "linaje": fila_ref.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, *_CLAVES_INVERSIONES),
        "nota": (
            "Número de inversiones inmobiliarias oficiales registradas en "
            "Andorra el año más reciente (dato nacional, no desglosado por "
            "parròquia)."
        ),
    }


def _respuesta_poble(inventario) -> "dict | None":
    """Construye la respuesta a "¿cuál es el pueblo (poble) más poblado?"."""
    pobles = carga_datos.carga_poblacion_poble()
    if _es_dataframe_vacio(pobles):
        return None
    anios = pd.to_numeric(pobles.get("anio"), errors="coerce").dropna()
    if anios.empty:
        return None
    anio_max = int(anios.max())
    sub = pobles[pd.to_numeric(pobles["anio"], errors="coerce") == anio_max].copy()
    sub["poblacion"] = pd.to_numeric(sub.get("poblacion"), errors="coerce")
    sub = sub.dropna(subset=["poblacion"]).sort_values("poblacion", ascending=False)
    if sub.empty:
        return None
    top = sub.iloc[0]
    return {
        "pregunta": "¿Cuál es el pueblo (poble) más poblado de Andorra?",
        "etiqueta": f"{top['poble']} ({top['parroquia']}) en {anio_max}",
        "valor": f"{int(top['poblacion']):,}".replace(",", "."),
        "metadato": _metadato_desde_fila(top, str(anio_max)),
        "linaje": top.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, "poblacion_poble", "1096"),
        "nota": (
            f"Entre los {len(sub)} pueblos (pobles) oficiales de Andorra, "
            f"{top['poble']} concentra la mayor población en {anio_max}."
        ),
    }


def _respuesta_salud_esperanza(inventario) -> "dict | None":
    """Construye la respuesta a "¿cuál es la esperanza de vida y el estado de salud?"."""
    df = carga_datos.carga_salud_ambiente()
    if _es_dataframe_vacio(df):
        return None
    sub = df[df["codigo"].isin(["SP.DYN.LE00.IN", "SH.XPD.CHEX.GD.ZS"])].copy()
    if sub.empty:
        return None
    sub["anio"] = pd.to_numeric(sub.get("anio"), errors="coerce")
    sub["valor"] = pd.to_numeric(sub.get("valor"), errors="coerce")
    sub = sub.dropna(subset=["anio", "valor"]).sort_values("anio")
    if sub.empty:
        return None
    fila = sub.iloc[-1]
    anio_max = int(fila["anio"])
    unidad = str(fila.get("unidad", "")).strip()
    return {
        "pregunta": "¿Cómo están los indicadores de salud en Andorra?",
        "etiqueta": f"{fila['indicador']} ({anio_max})",
        "valor": f"{float(fila['valor']):.2f} {unidad}".strip(),
        "metadato": _metadato_desde_fila(fila, str(anio_max)),
        "linaje": fila.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, "salud_educacion_ambiente"),
        "nota": "Indicador oficial de salud publicado por el Banco Mundial para Andorra.",
    }


def _respuesta_energia_bosques(inventario) -> "dict | None":
    """Construye la respuesta sobre energía renovable y bosques en Andorra."""
    df = carga_datos.carga_salud_ambiente()
    if _es_dataframe_vacio(df):
        return None
    sub = df[df["dominio"] == "energia_ambiente"].copy()
    if sub.empty:
        return None
    sub["anio"] = pd.to_numeric(sub.get("anio"), errors="coerce")
    sub["valor"] = pd.to_numeric(sub.get("valor"), errors="coerce")
    sub = sub.dropna(subset=["anio", "valor"]).sort_values("anio")
    if sub.empty:
        return None
    fila = sub.iloc[-1]
    anio_max = int(fila["anio"])
    unidad = str(fila.get("unidad", "")).strip()
    return {
        "pregunta": "¿Cómo está Andorra en energía renovable, bosques y medio ambiente?",
        "etiqueta": f"{fila['indicador']} ({anio_max})",
        "valor": f"{float(fila['valor']):.2f} {unidad}".strip(),
        "metadato": _metadato_desde_fila(fila, str(anio_max)),
        "linaje": fila.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, "salud_educacion_ambiente"),
        "nota": "Ver serie completa de energía renovable, bosques y CO2 en «Transporte y ambiente».",
    }


def _respuesta_suelo_edificios(inventario) -> "dict | None":
    """Construye la respuesta a "¿qué hay construido en el suelo?"."""
    edif = carga_datos.carga_edificios_suelo()
    if _es_dataframe_vacio(edif):
        return None
    nums = pd.to_numeric(edif.get("num_edificios"), errors="coerce").dropna()
    if nums.empty:
        return None
    total = int(nums.sum())
    fila = edif.iloc[0]
    return {
        "pregunta": "¿Qué hay construido en el suelo y qué equipamientos existen?",
        "etiqueta": f"Polígonos de edificios catastrados ({fila.get('vigencia')})",
        "valor": f"{total:,}".replace(",", "."),
        "metadato": _metadato_desde_fila(fila, str(fila.get("vigencia", "2026"))),
        "linaje": fila.get("linaje"),
        "id_fuente": _id_fuente_por_nombre(inventario, "edificios_suelo"),
        "nota": (
            "Huella edificada clasificada por tipología constructiva, número de "
            "plantas y nodos de transporte, salud y educación (OpenStreetMap, ODbL)."
        ),
    }


def _evalua_preguntas(inventario) -> "tuple[list, list]":
    """Clasifica las Pregunta_Usuario en respondidas y pendientes."""
    candidatas = [
        (
            "¿Cuánta gente vive en Andorra?",
            _respuesta_poblacion,
            "No hay datos procesados de población disponibles en este momento.",
        ),
        (
            "¿Cuánto vale el metro cuadrado en Andorra?",
            _respuesta_precio_m2,
            "No hay datos procesados de precios de vivienda disponibles en este momento.",
        ),
        (
            "¿Cuánto pesa el turismo en el presupuesto?",
            _respuesta_turismo,
            "No hay datos procesados de turismo disponibles en este momento.",
        ),
        (
            "¿Cómo evoluciona la economía de Andorra?",
            _respuesta_economia,
            "Todavía no hay ningún indicador económico real integrado en el lago "
            "(la descarga del Banco Mundial es un extractor bajo demanda).",
        ),
        (
            "¿En qué sectores trabaja la gente y cuánto se gana?",
            _respuesta_empleo,
            "No se han integrado datos oficiales de salario o empleo por "
            "sectores; no existen datos procesados que respondan a esta pregunta.",
        ),
        (
            "¿Cuántas inversiones inmobiliarias hay?",
            _respuesta_inversiones,
            "No hay datos procesados de inversiones inmobiliarias disponibles "
            "en este momento.",
        ),
        (
            "¿Cuál es el pueblo (poble) más poblado de Andorra?",
            _respuesta_poble,
            "No hay datos procesados de población por poble disponibles.",
        ),
        (
            "¿Cómo están los indicadores de salud en Andorra?",
            _respuesta_salud_esperanza,
            "No hay datos procesados de salud disponibles en este momento.",
        ),
        (
            "¿Cómo está Andorra en energía renovable, bosques y medio ambiente?",
            _respuesta_energia_bosques,
            "No hay datos procesados de energía y medio ambiente disponibles.",
        ),
        (
            "¿Qué hay construido en el suelo y qué equipamientos existen?",
            _respuesta_suelo_edificios,
            "No hay datos procesados de edificios y suelo disponibles.",
        ),
    ]

    respondidas: list = []
    pendientes: list = []

    for pregunta, constructor, motivo_indisponible in candidatas:
        respuesta = constructor(inventario)
        if respuesta is None or not _respuesta_gobernada(respuesta):
            pendientes.append({"pregunta": pregunta, "motivo": motivo_indisponible})
        else:
            respondidas.append(respuesta)

    pendientes.extend(_PENDIENTES_BASE)
    return respondidas, pendientes


def preguntas_respondidas() -> list:
    """Devuelve las Pregunta_Respondida con su cifra, metadato, linaje e id_fuente."""
    inventario = carga_datos.carga_inventario()
    respondidas, _ = _evalua_preguntas(inventario)
    return respondidas


def preguntas_pendientes() -> list:
    """Devuelve las Pregunta_Pendiente, cada una con un motivo no vacío."""
    inventario = carga_datos.carga_inventario()
    _, pendientes = _evalua_preguntas(inventario)
    normalizadas = []
    for item in pendientes:
        motivo = str(item.get("motivo", "")).strip()
        if not motivo:
            motivo = "Pendiente: no hay datos disponibles para responder."
        normalizadas.append({"pregunta": item.get("pregunta", ""), "motivo": motivo})
    return normalizadas


def _muestra_respondidas(respondidas: list) -> None:
    """Renderiza las Pregunta_Respondida con su cifra gobernada dentro de tarjetas."""
    st.subheader("Preguntas resueltas por el lago")

    for respuesta in respondidas:
        with st.container(border=True):
            st.markdown(f"### {respuesta['pregunta']}")
            nota = respuesta.get("nota")
            if nota:
                st.caption(nota)
            componentes.cifra_gobernada(
                respuesta["etiqueta"],
                respuesta["valor"],
                respuesta["metadato"],
                respuesta["linaje"],
                id_fuente=respuesta.get("id_fuente"),
            )


def _muestra_pendientes(pendientes: list) -> None:
    """Renderiza la lista de Pregunta_Pendiente con su motivo en cajas de información."""
    st.subheader("Preguntas pendientes y límites actuales")

    if not pendientes:
        st.caption("No hay preguntas pendientes declaradas.")
        return

    for item in pendientes:
        with st.container(border=True):
            st.markdown(f"#### {item['pregunta']}")
            st.info(f"**Motivo:** {item['motivo']}")


def render() -> None:
    """Renderiza la Vista_Preguntas completa estilizada."""
    estilos.cabecera(
        "Andorra en preguntas",
        "Resolvemos las dudas más habituales sobre Andorra con cifras vivas "
        "del lago de datos. Cada respuesta incluye su trazabilidad; lo que aún "
        "no podemos responder lo declaramos con transparencia.",
    )

    inventario = carga_datos.carga_inventario()
    respondidas, pendientes = _evalua_preguntas(inventario)

    if respondidas:
        _muestra_respondidas(respondidas)
    else:
        st.warning(
            "⚠️ No hay ninguna pregunta respondible en este momento: no se "
            "pudieron cargar los datos procesados necesarios."
        )

    st.divider()
    _muestra_pendientes(pendientes)