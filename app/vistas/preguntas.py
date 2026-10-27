"""Vista "Andorra en preguntas" de la App_Streamlit de Cerebro Andorra.

Esta vista está redactada en tono FAQ orientado a usuario final: cada
Pregunta_Usuario se plantea como un enunciado en lenguaje natural terminado en
``?`` y, cuando el lago tiene datos, se responde con una respuesta visual y una
cifra gobernada; cuando no los tiene, la pregunta queda declarada como pendiente
con un motivo real no vacío (Req 7.1, 7.6, 7.7). Cada respuesta se muestra
exclusivamente a través de ``componentes.cifra_gobernada`` para garantizar el
principio rector del proyecto —"0 cifras sin fuente, sin vigencia y sin fecha de
prueba"— acompañada de su Metadato_Cifra y su Etiqueta_Linaje (Req 7.2), con el
Detalle_Gobernanza a un clic a partir del ``id_fuente`` resuelto desde el
Inventario_Fuentes.

Las Pregunta_Usuario que esta vista intenta responder son:

1. ¿Cuánta gente vive en Andorra? → población total del año más reciente
   (linaje OBSERVADO, fuente F01).
2. ¿Cuánto vale el metro cuadrado? → precio de venta medio en €/m² de los
   anuncios de Indomio (linaje PROXY, fuente F02), señalando que es precio de
   oferta y no transacción real (Req 7.3).
3. ¿Cuánto pesa el turismo? → total del presupuesto de despeses de turismo del
   año más reciente (linaje OBSERVADO, fuente F03).
4. ¿Cómo evoluciona la economía? → PIB más reciente del Banco Mundial
   (linaje OBSERVADO, fuente F13) si el extractor de economía ya llenó el lago;
   si no hay dato económico integrado, cae a pendiente (Req 7.4).
5. ¿Cuánta gente trabaja y en qué sectores? → pendiente mientras no haya una
   fuente de empleo integrada en el lago (Req 7.4, 7.7).

Como refuerzo del principio rector, si la respuesta construida para una pregunta
carece de Metadato_Cifra o de Etiqueta_Linaje, esa pregunta se trata como
pendiente y no se muestra su cifra (Req 7.6). Si los datos procesados necesarios
para una pregunta no están disponibles, esa pregunta —y sólo esa— se reclasifica
como pendiente con un motivo de indisponibilidad, conservando inalteradas las
respuestas de las demás y sin interrumpir la carga de la vista (Req 7.7).

Como este módulo vive en ``app/vistas/`` y reutiliza los módulos hermanos
``carga_datos.py`` y ``componentes.py`` (ubicados en ``app/``), se añade la
carpeta ``app/`` al ``sys.path`` resolviéndola de forma relativa a este archivo
(parents[1]).

Textos de interfaz y mensajes de consola en español, coherentes con el resto
del proyecto.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de módulos hermanos ------
# parents[1] sube desde app/vistas/preguntas.py hasta app/; desde ahí se
# importan carga_datos y componentes sin convertir app/ en un paquete.
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path
import componentes  # noqa: E402 - import tras ajustar sys.path

# Texto de oferta que acompaña al precio €/m² PROXY de Indomio: deja claro que
# es precio de anuncio y no transacción real (Req 2.2, coherente con Req 7.2).
_TEXTO_OFERTA_PROXY = (
    "Precio de oferta de anuncios de Indomio (linaje PROXY): no es una "
    "transacción real."
)

# Subcadenas identificadoras del `nombre` de cada fuente en el Inventario_Fuentes
# para resolver el ID_Fuente real por dominio (población, precios, turismo). Se
# busca por subcadena porque el `nombre` del inventario no coincide carácter a
# carácter con el campo `fuente` de los datos procesados.
_CLAVES_POBLACION = ("poblac", "798")
_CLAVES_PRECIOS = ("precios_vivienda", "indomio")
_CLAVES_TURISMO = ("turismo", "681")
_CLAVES_ECONOMIA = ("economia_worldbank", "world bank", "banco mundial")

# Partida del presupuesto de turismo que representa el total de despeses.
_PARTIDA_TOTAL_TURISMO = "TOTAL PRESSUPOST DE DESPESES"

# Códigos/etiquetas del indicador de PIB dentro de economia_worldbank.csv. El
# extractor de World Bank etiqueta el PIB con el código oficial NY.GDP.MKTP.CD y
# un `indicador` que contiene "PIB"; se admite cualquiera de las dos señales.
_CODIGO_PIB = "NY.GDP.MKTP.CD"
_CLAVE_INDICADOR_PIB = "pib"

# Pregunta_Pendiente base: preguntas reales del alcance del proyecto que el lago
# todavía no responde porque no hay fuente abierta y de licencia clara. Cada una
# lleva un motivo no vacío que explica con honestidad el límite del sistema
# (Req 7.7). La pregunta de empleo se trata aparte en ``_respuesta_empleo`` para
# que pase a respondida en cuanto se integre una fuente de empleo real.
_PENDIENTES_BASE = [
    {
        "pregunta": "¿Cuántas transacciones inmobiliarias hay por parròquia?",
        "motivo": (
            "No se encontró una fuente abierta y de licencia clara con el número "
            "de transacciones inmobiliarias desglosado por parròquia en Andorra; "
            "se documentó el intento en la bitácora y no se inventa una cifra."
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


def _es_dataframe_vacio(datos) -> bool:
    """Indica si el argumento no es un DataFrame utilizable.

    Considera "vacío" tanto el caso ``None`` (archivo inexistente o ilegible)
    como el de un DataFrame sin filas, de modo que la pregunta dependiente de
    esos datos se reclasifique como pendiente por indisponibilidad (Req 2.5).

    Args:
        datos: valor devuelto por una función de carga (``DataFrame`` o ``None``).

    Returns:
        True si no hay datos utilizables; False si es un DataFrame con filas.
    """
    if datos is None:
        return True
    if not isinstance(datos, pd.DataFrame):
        return True
    return datos.empty


def _id_fuente_por_nombre(inventario, *claves: str) -> "str | None":
    """Resuelve el ID_Fuente de una fuente buscando subcadenas en su ``nombre``.

    Recorre el Inventario_Fuentes y devuelve el ``id_fuente`` de la primera fila
    cuyo campo ``nombre`` contiene (sin distinguir mayúsculas) alguna de las
    ``claves`` indicadas. Permite pasar el ``id_fuente`` real al
    Detalle_Gobernanza de cada cifra (Req 5.5) sin fijar los IDs por constante,
    de modo que la vista siga el inventario como fuente de verdad.

    Args:
        inventario: ``DataFrame`` del Inventario_Fuentes, o ``None`` si no se
            pudo cargar.
        *claves: subcadenas a buscar en el campo ``nombre`` del inventario.

    Returns:
        El ``id_fuente`` de la primera fila coincidente, o ``None`` si el
        inventario no está disponible o ninguna fila coincide.
    """
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
    """Construye el Metadato_Cifra a partir de una fila procesada.

    Reconstruye el diccionario ``fuente``/``vigencia``/``fecha_prueba`` que
    espera ``componentes.cifra_gobernada``. La ``vigencia`` se pasa de forma
    explícita porque suele corresponder al año/periodo calculado para la cifra.

    Args:
        fila: una fila (``pd.Series``) de datos procesados con las columnas
            ``fuente`` y ``fecha_prueba``.
        vigencia: valor de vigencia a mostrar (año o periodo).

    Returns:
        dict con las claves ``fuente``, ``vigencia`` y ``fecha_prueba``.
    """
    return {
        "fuente": fila.get("fuente"),
        "vigencia": vigencia,
        "fecha_prueba": fila.get("fecha_prueba"),
    }


def _respuesta_gobernada(respuesta: "dict | None") -> bool:
    """Indica si una respuesta trae Metadato_Cifra y Etiqueta_Linaje completos.

    Refuerza el principio rector en la propia vista: una Pregunta_Usuario sólo
    puede considerarse respondida si su respuesta incluye un ``metadato`` con
    ``fuente``, ``vigencia`` y ``fecha_prueba`` no vacíos y un ``linaje`` no
    vacío. En caso contrario la pregunta debe tratarse como pendiente y no
    mostrarse (Req 7.6). La validación final de gobernanza la sigue haciendo
    ``componentes.cifra_gobernada`` al renderizar; esta comprobación evita
    además clasificar como respondida una pregunta cuya cifra se omitiría.

    Args:
        respuesta: diccionario de respuesta construido por un ``_respuesta_*``,
            o ``None``.

    Returns:
        True si la respuesta tiene metadato y linaje completos; False en caso
        contrario.
    """
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
    """Construye la respuesta a "¿cuánta gente vive en Andorra?".

    Carga la población por parròquia, identifica el año más reciente, suma la
    población de ese año y arma un diccionario con la cifra gobernada
    (OBSERVADO) y su ``id_fuente`` (F01). Si los datos no están disponibles o no
    hay año/valores utilizables, devuelve ``None`` para que la pregunta se
    reclasifique como pendiente (Req 2.5).

    Args:
        inventario: ``DataFrame`` del Inventario_Fuentes, o ``None``.

    Returns:
        dict con la respuesta lista para ``cifra_gobernada``, o ``None`` si los
        datos no permiten responder.
    """
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
    """Construye la respuesta a "¿cuánto vale el metro cuadrado?".

    Carga los precios de vivienda de Indomio, calcula el precio de venta medio
    en €/m² sobre las parròquies con valor, lo redondea a dos decimales y arma
    un diccionario con la cifra gobernada (PROXY) y su ``id_fuente`` (F02),
    incluyendo el texto de que es precio de oferta y no transacción real
    (Req 2.2). Si no hay datos, precios utilizables o periodo de vigencia,
    devuelve ``None`` para reclasificar la pregunta como pendiente (Req 2.5).

    Args:
        inventario: ``DataFrame`` del Inventario_Fuentes, o ``None``.

    Returns:
        dict con la respuesta lista para ``cifra_gobernada``, o ``None`` si los
        datos no permiten responder.
    """
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
    """Construye la respuesta a "¿cuánto pesa el turismo?".

    Carga el presupuesto de turismo, filtra la partida del total de despeses,
    identifica el periodo más reciente y arma un diccionario con el importe
    total gobernado (OBSERVADO) y su ``id_fuente`` (F03). Si los datos no están
    disponibles o no hay un total utilizable para un periodo identificable,
    devuelve ``None`` para reclasificar la pregunta como pendiente (Req 2.5).

    Args:
        inventario: ``DataFrame`` del Inventario_Fuentes, o ``None``.

    Returns:
        dict con la respuesta lista para ``cifra_gobernada``, o ``None`` si los
        datos no permiten responder.
    """
    turismo = carga_datos.carga_turismo()
    if _es_dataframe_vacio(turismo):
        return None
    if "partida" not in turismo.columns:
        return None

    # Quedarse sólo con la fila del total del presupuesto de despeses.
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
    """Construye la respuesta a "¿cómo evoluciona la economía de Andorra?".

    Carga ``economia_worldbank.csv``, selecciona el indicador de PIB (por el
    código oficial ``NY.GDP.MKTP.CD`` o porque su ``indicador`` contiene "PIB"),
    toma el año más reciente con valor y arma un diccionario con la cifra
    gobernada (OBSERVADO) y su ``id_fuente`` (F13) resuelto desde el inventario
    (Req 7.4). Si el extractor de economía aún no ha llenado el lago (archivo
    vacío con sólo cabecera), no hay indicador de PIB o no hay un año/valor
    utilizable, devuelve ``None`` para que la pregunta caiga a pendiente con su
    motivo (Req 7.7).

    Args:
        inventario: ``DataFrame`` del Inventario_Fuentes, o ``None``.

    Returns:
        dict con la respuesta lista para ``cifra_gobernada``, o ``None`` si los
        datos no permiten responder.
    """
    economia = carga_datos.carga_economia()
    if _es_dataframe_vacio(economia):
        return None

    # Localizar el indicador de PIB por código oficial o por el texto del
    # nombre del indicador, tolerando que falte alguna de las dos columnas.
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

    # Formato con separador de miles en punto (convención europea) y dos
    # decimales; se añade la unidad cuando está disponible.
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
    """Construye la respuesta a "¿cuánta gente trabaja y en qué sectores?".

    De momento devuelve siempre ``None`` porque no hay ninguna fuente de empleo
    por sectores integrada en el lago: ``_evalua_preguntas`` la reclasifica
    entonces como Pregunta_Pendiente con un motivo real (Req 7.4, 7.7). Se deja
    como función explícita —en lugar de una entrada fija en ``_PENDIENTES_BASE``—
    para que la pregunta pase a respondida de forma automática en cuanto exista
    una Fuente_Oficial_Nueva de empleo, sin tocar el resto de la vista.

    Args:
        inventario: ``DataFrame`` del Inventario_Fuentes, o ``None``.

    Returns:
        ``None`` mientras no haya una fuente de empleo integrada.
    """
    # No hay fuente de empleo por sectores integrada todavía; la pregunta cae a
    # pendiente con el motivo de indisponibilidad definido en _evalua_preguntas.
    return None


def _evalua_preguntas(inventario) -> "tuple[list, list]":
    """Clasifica las Pregunta_Usuario en respondidas y pendientes.

    Intenta construir la respuesta de cada pregunta candidata con datos vivos
    del lago (población, precio €/m², turismo, economía y empleo). Cada pregunta
    cuya respuesta pueda armarse y además tenga Metadato_Cifra y Etiqueta_Linaje
    se añade a las respondidas; cada pregunta cuyos datos no estén disponibles, o
    cuya respuesta carezca de gobernanza completa, se añade a las pendientes con
    un motivo real no vacío, sin afectar a las demás (Req 7.6, 7.7). A las
    pendientes así reclasificadas se suman las pendientes base (preguntas sin
    fuente abierta, como seguridad o transacciones por parròquia), cada una con
    su motivo no vacío (Req 7.7).

    Args:
        inventario: ``DataFrame`` del Inventario_Fuentes, o ``None``.

    Returns:
        Una tupla ``(respondidas, pendientes)`` de listas de diccionarios.
    """
    # Cada entrada asocia una Pregunta_Usuario con su constructor de respuesta y
    # el motivo a usar si sus datos no están disponibles o su respuesta no está
    # gobernada (Req 7.6, 7.7).
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
            "¿Cuánta gente trabaja y en qué sectores?",
            _respuesta_empleo,
            "No se ha integrado ninguna fuente oficial de empleo por sectores; "
            "no existen datos procesados que respondan a esta pregunta.",
        ),
    ]

    respondidas: list = []
    pendientes: list = []

    for pregunta, constructor, motivo_indisponible in candidatas:
        respuesta = constructor(inventario)
        if respuesta is None or not _respuesta_gobernada(respuesta):
            # Sólo esta pregunta se reclasifica como pendiente —por ausencia de
            # datos o por respuesta sin gobernanza—; las demás se evalúan igual
            # (Req 7.6, 7.7).
            pendientes.append({"pregunta": pregunta, "motivo": motivo_indisponible})
        else:
            respondidas.append(respuesta)

    # Añadir las pendientes base (preguntas sin fuente abierta de licencia clara).
    pendientes.extend(_PENDIENTES_BASE)

    return respondidas, pendientes


def preguntas_respondidas() -> list:
    """Devuelve las Pregunta_Respondida con su cifra, metadato, linaje e id_fuente.

    Construye, a partir de los datos procesados y del Inventario_Fuentes, la
    lista de Pregunta_Usuario que el lago puede responder con al menos una cifra
    gobernada (población total OBSERVADO, precio €/m² PROXY, total del
    presupuesto de turismo OBSERVADO y PIB del Banco Mundial OBSERVADO cuando el
    extractor de economía ya llenó el lago). Cada elemento incluye la
    ``etiqueta``, el ``valor``, el ``metadato``, el ``linaje`` y el ``id_fuente``
    listos para ``componentes.cifra_gobernada`` (Req 7.1, 7.2). Las preguntas
    cuyos datos no estén disponibles o cuya respuesta carezca de gobernanza se
    omiten de esta lista por reclasificarse como pendientes (Req 7.6, 7.7).

    Returns:
        Lista de diccionarios de respuesta (posiblemente vacía si ningún dato
        está disponible).
    """
    inventario = carga_datos.carga_inventario()
    respondidas, _ = _evalua_preguntas(inventario)
    return respondidas


def preguntas_pendientes() -> list:
    """Devuelve las Pregunta_Pendiente, cada una con un motivo no vacío.

    Reúne las Pregunta_Usuario que el lago no responde: tanto las pendientes
    base sin fuente abierta (seguridad y transacciones por parròquia) como las
    que se reclasifican por indisponibilidad de sus datos procesados o por falta
    de gobernanza de su respuesta (Req 7.6, 7.7). Cada elemento tiene las claves
    ``pregunta`` y ``motivo``, con ``motivo`` garantizado no vacío (longitud
    mínima de 1 carácter).

    Returns:
        Lista de diccionarios ``{"pregunta": str, "motivo": str}``.
    """
    inventario = carga_datos.carga_inventario()
    _, pendientes = _evalua_preguntas(inventario)
    # Garantizar que ningún motivo quede vacío (Req 2.4): si por cualquier
    # motivo llegara vacío, se sustituye por un texto genérico no vacío.
    normalizadas = []
    for item in pendientes:
        motivo = str(item.get("motivo", "")).strip()
        if not motivo:
            motivo = "Pendiente: no hay datos disponibles para responder."
        normalizadas.append({"pregunta": item.get("pregunta", ""), "motivo": motivo})
    return normalizadas


def _muestra_respondidas(respondidas: list) -> None:
    """Renderiza las Pregunta_Respondida con su cifra gobernada y detalle.

    Para cada pregunta respondida muestra el enunciado en lenguaje natural, una
    nota aclaratoria y la cifra a través de ``componentes.cifra_gobernada``,
    pasando el ``id_fuente`` para que el Detalle_Gobernanza quede disponible a un
    clic (Req 7.1, 7.2). El enunciado es un texto terminado en '?', coherente
    con el tono FAQ "Andorra en preguntas".

    Args:
        respondidas: lista de diccionarios de respuesta.
    """
    st.subheader("Preguntas que ya responde el lago")

    for respuesta in respondidas:
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
    """Renderiza la lista de Pregunta_Pendiente con su motivo.

    Muestra cada pregunta pendiente junto con el texto de motivo que explica por
    qué el lago aún no la responde, de forma honesta sobre los límites del
    sistema (Req 7.7).

    Args:
        pendientes: lista de diccionarios ``{"pregunta", "motivo"}``.
    """
    st.subheader("Preguntas que todavía no responde el lago")

    if not pendientes:
        st.caption("No hay preguntas pendientes declaradas.")
        return

    for item in pendientes:
        st.markdown(f"**{item['pregunta']}**")
        st.caption(f"Motivo: {item['motivo']}")


def render() -> None:
    """Renderiza la Vista_Preguntas completa en tono FAQ "Andorra en preguntas".

    Presenta las Pregunta_Respondida con su cifra gobernada (Metadato_Cifra,
    Etiqueta_Linaje y Detalle_Gobernanza a un clic) y, a continuación, la lista
    de Pregunta_Pendiente con su motivo (Req 7.1, 7.2, 7.7). Cada enunciado es
    una pregunta en lenguaje natural terminada en '?'. Si los datos de una
    pregunta no están disponibles o su respuesta carece de gobernanza, esa
    pregunta se reclasifica como pendiente y las demás se conservan, sin
    interrumpir la carga de la vista (Req 7.6, 7.7).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.title("Andorra en preguntas")
    st.write(
        "Resolvemos las dudas más habituales sobre Andorra con cifras vivas del "
        "lago, cada una con su fuente y su fecha de prueba. Lo que todavía no "
        "podemos responder lo decimos con honestidad y explicamos por qué."
    )

    inventario = carga_datos.carga_inventario()
    respondidas, pendientes = _evalua_preguntas(inventario)

    if respondidas:
        _muestra_respondidas(respondidas)
    else:
        st.warning(
            "No hay ninguna pregunta respondible en este momento: no se "
            "pudieron cargar los datos procesados necesarios."
        )

    _muestra_pendientes(pendientes)
