"""Vista Mapa (Vista_Mapa) de la App_Streamlit de Cerebro Andorra.

Vista geoespacial que representa un indicador por parròquia sobre el mapa de
Andorra (coropletas) a partir del GeoJSON de límites de las 7 parròquies. El
usuario puede elegir entre dos indicadores: población total (OBSERVADO) o
precio de venta en €/m² (PROXY, procedente del scraping de Indomio).

Este módulo implementa, por ahora, las dos piezas de datos sobre las que se
apoyará el render (tarea 10.1):

- ``MAPA_NOMBRES_GEOJSON``: mapa de los nombres de parròquia tal como vienen en
  el GeoJSON de OpenStreetMap (catalán, con variantes de grafía) a los siete
  nombres canónicos del proyecto.
- ``mapea_nombre_parroquia(nombre_geojson)``: función **total** que devuelve el
  nombre canónico de una parròquia a partir del nombre del GeoJSON, manejando
  de forma explícita y segura cualquier nombre que no esté en el mapa directo
  (Req 1.1).
- ``tabla_indicador(indicador)``: construye la tabla parròquia→valor del
  indicador seleccionado (población del año máximo, o precio de venta PROXY)
  con su gobernanza, reutilizando ``carga_datos`` (Req 1.2).

El ``render()`` del coropletas con Plotly y el Plan B por centroides se
implementan en la tarea 10.2; aquí el módulo queda importable y válido, sin
``render()``.

Como este módulo vive en ``app/vistas/`` y reutiliza los módulos transversales
``carga_datos.py`` y ``componentes.py`` (ubicados en ``app/``), se añade la
carpeta ``app/`` al ``sys.path`` resolviéndola de forma relativa a este archivo
(mismo patrón que ``vivienda.py`` y ``panorama.py``), sin convertir ``app/`` en
un paquete.

Textos de interfaz y mensajes de consola en español, coherentes con el resto
del proyecto.
"""

import sys
import unicodedata
from pathlib import Path

import pandas as pd

# --- Resolución de la ruta a app/ y reutilización de módulos transversales --
# parents[1] sube desde app/vistas/mapa.py hasta app/; desde ahí se importan los
# módulos transversales de carga de datos y de componentes de UI sin convertir
# app/ en un paquete.
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path
import componentes  # noqa: E402 - import tras ajustar sys.path (uso en 10.2)

# --- Parròquies canónicas --------------------------------------------------
# Las siete parròquies de Andorra con la grafía canónica del proyecto (idéntica
# a la de datos_procesados/poblacion_parroquia.csv y precios_vivienda.csv). El
# orden es el administrativo habitual y se usa para una presentación estable.
PARROQUIES_CANONICAS = [
    "Andorra la Vella",
    "Canillo",
    "Encamp",
    "Escaldes-Engordany",
    "La Massana",
    "Ordino",
    "Sant Julià de Lòria",
]

# --- Mapeo de nombres del GeoJSON a nombres canónicos ----------------------
# El GeoJSON de límites proviene de OpenStreetMap y puede traer el nombre de la
# parròquia en catalán con variantes de grafía (apóstrofes, acentos, guiones o
# formas abreviadas). Este mapa traduce esas variantes conocidas al nombre
# canónico del proyecto. Las claves se comparan de forma tolerante (ver
# ``_normaliza``), por lo que basta con registrar las variantes de contenido,
# no todas las combinaciones de mayúsculas/acentos.
MAPA_NOMBRES_GEOJSON = {
    # Andorra la Vella
    "Andorra la Vella": "Andorra la Vella",
    "Andorra-la-Vella": "Andorra la Vella",
    # Canillo
    "Canillo": "Canillo",
    # Encamp
    "Encamp": "Encamp",
    # Escaldes-Engordany (variantes con guion o con espacio)
    "Escaldes-Engordany": "Escaldes-Engordany",
    "Escaldes Engordany": "Escaldes-Engordany",
    "Les Escaldes": "Escaldes-Engordany",
    # La Massana (con y sin artículo)
    "La Massana": "La Massana",
    "Massana": "La Massana",
    # Ordino
    "Ordino": "Ordino",
    # Sant Julià de Lòria (variantes de acento y de apóstrofe/forma)
    "Sant Julià de Lòria": "Sant Julià de Lòria",
    "Sant Julia de Loria": "Sant Julià de Lòria",
    "Sant Julià de Loria": "Sant Julià de Lòria",
}

# --- Indicadores seleccionables --------------------------------------------
# Etiqueta visible en la interfaz -> clave interna del indicador. La clave
# interna es la que recibe ``tabla_indicador`` (Req 1.2).
INDICADORES = {
    "Población total": "poblacion",
    "Precio de venta (€/m²)": "precio_venta",
}


def _normaliza(texto: str) -> str:
    """Normaliza un nombre para compararlo de forma tolerante.

    Pasa a minúsculas, elimina acentos (descomposición Unicode) y comprime los
    espacios, de modo que variantes como "Sant Julià de Lòria", "SANT JULIA DE
    LORIA" o "  Sant   Julia  de Loria " se consideren equivalentes. No altera
    el resultado canónico: sólo sirve para emparejar claves de
    ``MAPA_NOMBRES_GEOJSON``.

    Args:
        texto: nombre de parròquia tal como viene en el GeoJSON.

    Returns:
        Cadena normalizada (minúsculas, sin acentos, espacios comprimidos).
    """
    sin_acentos = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(caracter)
    )
    return " ".join(sin_acentos.lower().split())


# Índice auxiliar: nombre normalizado -> nombre canónico, derivado de
# MAPA_NOMBRES_GEOJSON para permitir el emparejamiento tolerante a grafía.
_INDICE_NORMALIZADO = {
    _normaliza(variante): canonico for variante, canonico in MAPA_NOMBRES_GEOJSON.items()
}


def mapea_nombre_parroquia(nombre_geojson: str) -> "str | None":
    """Devuelve el nombre canónico de la parròquia a partir del nombre del GeoJSON.

    El mapeo es **total** respecto a las siete parròquies: cualquier grafía
    conocida de las parròquies de Andorra (con o sin acentos, con guion o
    espacio, en mayúsculas o minúsculas) se resuelve a su nombre canónico. El
    emparejamiento se hace primero de forma exacta contra
    ``MAPA_NOMBRES_GEOJSON`` y, si no hay coincidencia directa, de forma
    tolerante a grafía mediante ``_normaliza`` (Req 1.1).

    Cualquier entrada que no corresponda a ninguna de las siete parròquies
    (``None``, cadena vacía o un nombre desconocido) se maneja de forma
    explícita y segura devolviendo ``None``, para que la vista pueda decidir qué
    hacer con ese polígono sin romperse.

    Args:
        nombre_geojson: nombre de la parròquia tal como aparece en el GeoJSON.

    Returns:
        El nombre canónico de la parròquia (uno de ``PARROQUIES_CANONICAS``), o
        ``None`` si el nombre no corresponde a ninguna de las siete parròquies.
    """
    if nombre_geojson is None:
        return None

    # Coincidencia exacta con el mapa declarado (caso más común y barato).
    directo = MAPA_NOMBRES_GEOJSON.get(nombre_geojson)
    if directo is not None:
        return directo

    # Coincidencia tolerante a grafía (acentos, mayúsculas, espacios, guion).
    clave = _normaliza(nombre_geojson)
    if clave == "":
        return None
    return _INDICE_NORMALIZADO.get(clave)


def _fila_a_metadato(fila: "pd.Series") -> dict:
    """Construye el Metadato_Cifra (fuente/vigencia/fecha_prueba) de una fila.

    Reúne los tres campos de gobernanza presentes en una fila de datos
    procesados. Si alguno falta, se deja como ``None`` para que
    ``cifra_gobernada`` trate la cifra como no disponible por metadato
    incompleto en la tarea 10.2.

    Args:
        fila: registro (``pd.Series``) de un dato procesado.

    Returns:
        Diccionario con las claves ``fuente``, ``vigencia`` y ``fecha_prueba``.
    """
    return {
        "fuente": fila.get("fuente"),
        "vigencia": fila.get("vigencia"),
        "fecha_prueba": fila.get("fecha_prueba"),
    }


def _fila_vacia_parroquia(parroquia: str) -> dict:
    """Devuelve una fila de tabla de indicador para una parròquia sin dato.

    Cuando una parròquia canónica no aparece en los datos procesados (o su valor
    no es utilizable), su entrada en la tabla del indicador conserva el nombre
    de la parròquia pero deja el ``valor`` y la gobernanza en ``None``. La vista
    (tarea 10.2) representará esas parròquies con un estilo distinto (Req 1.6).

    Args:
        parroquia: nombre canónico de la parròquia sin dato.

    Returns:
        Diccionario con el esquema de la tabla de indicador y valores ``None``.
    """
    return {
        "parroquia": parroquia,
        "valor": None,
        "fuente": None,
        "vigencia": None,
        "fecha_prueba": None,
        "linaje": None,
    }


def _tabla_poblacion() -> "pd.DataFrame":
    """Construye la tabla parròquia→población total del año más reciente.

    Carga la población procesada (OBSERVADO), identifica el año máximo
    disponible y toma, por cada parròquia canónica, su población de ese año con
    su Metadato_Cifra y su linaje. Las parròquies sin registro para el año
    máximo (o sin año identificable en los datos) quedan con ``valor=None`` y
    gobernanza ``None`` (Req 1.2, 1.6).

    Returns:
        ``DataFrame`` con una fila por parròquia canónica y las columnas
        ``parroquia``, ``valor``, ``fuente``, ``vigencia``, ``fecha_prueba`` y
        ``linaje``.
    """
    poblacion = carga_datos.carga_poblacion()

    # Sin datos de población: todas las parròquies quedan sin valor.
    if poblacion is None or poblacion.empty or "parroquia" not in poblacion.columns:
        return pd.DataFrame(
            [_fila_vacia_parroquia(parroquia) for parroquia in PARROQUIES_CANONICAS]
        )

    # Identificar el año más reciente. Si no hay ningún año utilizable, no se
    # puede fijar un valor por parròquia: todas quedan sin dato.
    anios = pd.to_numeric(poblacion.get("anio"), errors="coerce").dropna()
    if anios.empty:
        return pd.DataFrame(
            [_fila_vacia_parroquia(parroquia) for parroquia in PARROQUIES_CANONICAS]
        )

    anio_reciente = int(anios.max())
    filas_anio = poblacion[
        pd.to_numeric(poblacion["anio"], errors="coerce") == anio_reciente
    ]

    # Indexar por parròquia para localizar cada registro de forma directa.
    por_parroquia = {
        str(fila["parroquia"]).strip(): fila for _, fila in filas_anio.iterrows()
    }

    filas = []
    for parroquia in PARROQUIES_CANONICAS:
        fila = por_parroquia.get(parroquia)
        if fila is None:
            filas.append(_fila_vacia_parroquia(parroquia))
            continue

        valor = pd.to_numeric(pd.Series([fila.get("poblacion")]), errors="coerce").iloc[0]
        if pd.isna(valor):
            # Hay registro pero el valor no es utilizable: parròquia sin dato.
            filas.append(_fila_vacia_parroquia(parroquia))
            continue

        metadato = _fila_a_metadato(fila)
        filas.append(
            {
                "parroquia": parroquia,
                "valor": int(valor),
                "fuente": metadato["fuente"],
                # La vigencia de la cifra es el año más reciente mostrado.
                "vigencia": str(anio_reciente),
                "fecha_prueba": metadato["fecha_prueba"],
                "linaje": fila.get("linaje"),
            }
        )

    return pd.DataFrame(filas)


def _tabla_precio_venta() -> "pd.DataFrame":
    """Construye la tabla parròquia→precio de venta en €/m² (PROXY).

    Carga los precios de vivienda procesados (una fila por parròquia, linaje
    PROXY de Indomio) y toma, por cada parròquia canónica, su ``precio_venta``
    con su Metadato_Cifra y su linaje. Las parròquies ausentes o sin precio
    utilizable quedan con ``valor=None`` y gobernanza ``None`` (Req 1.2, 1.6,
    1.7).

    Returns:
        ``DataFrame`` con una fila por parròquia canónica y las columnas
        ``parroquia``, ``valor``, ``fuente``, ``vigencia``, ``fecha_prueba`` y
        ``linaje``.
    """
    precios = carga_datos.carga_precios()

    if precios is None or precios.empty or "parroquia" not in precios.columns:
        return pd.DataFrame(
            [_fila_vacia_parroquia(parroquia) for parroquia in PARROQUIES_CANONICAS]
        )

    por_parroquia = {
        str(fila["parroquia"]).strip(): fila for _, fila in precios.iterrows()
    }

    filas = []
    for parroquia in PARROQUIES_CANONICAS:
        fila = por_parroquia.get(parroquia)
        if fila is None:
            filas.append(_fila_vacia_parroquia(parroquia))
            continue

        valor = pd.to_numeric(
            pd.Series([fila.get("precio_venta")]), errors="coerce"
        ).iloc[0]
        if pd.isna(valor):
            filas.append(_fila_vacia_parroquia(parroquia))
            continue

        metadato = _fila_a_metadato(fila)
        filas.append(
            {
                "parroquia": parroquia,
                "valor": float(valor),
                "fuente": metadato["fuente"],
                "vigencia": metadato["vigencia"],
                "fecha_prueba": metadato["fecha_prueba"],
                "linaje": fila.get("linaje"),
            }
        )

    return pd.DataFrame(filas)


def tabla_indicador(indicador: str) -> "pd.DataFrame | None":
    """Construye la tabla parròquia→valor del indicador seleccionado con gobernanza.

    Recibe la **clave interna** del indicador (``"poblacion"`` o
    ``"precio_venta"``, los valores de ``INDICADORES``) y devuelve una tabla con
    una fila por parròquia canónica y las columnas ``parroquia``, ``valor``,
    ``fuente``, ``vigencia``, ``fecha_prueba`` y ``linaje``:

    - ``"poblacion"`` → población total del año más reciente (OBSERVADO).
    - ``"precio_venta"`` → precio de venta en €/m² de Indomio (PROXY).

    Las parròquies que falten en los datos, o cuyo valor no sea utilizable,
    aparecen en la tabla con ``valor=None`` y gobernanza ``None``, para que la
    vista las represente con un estilo distinto sin perder las demás (Req 1.6).

    Args:
        indicador: clave interna del indicador (``"poblacion"`` o
            ``"precio_venta"``).

    Returns:
        Un ``DataFrame`` con la tabla del indicador, o ``None`` si la clave de
        indicador no es reconocida.
    """
    if indicador == "poblacion":
        return _tabla_poblacion()
    if indicador == "precio_venta":
        return _tabla_precio_venta()

    # Indicador no reconocido: se maneja de forma explícita devolviendo None
    # para que la vista (10.2) muestre el mensaje correspondiente.
    print(
        f"[mapa] Indicador no reconocido: '{indicador}'. "
        f"Valores admitidos: {sorted(set(INDICADORES.values()))}."
    )
    return None


# --- Datos para la presentación y el Plan B --------------------------------
# ID_Fuente estable de cada indicador en el Inventario_Fuentes
# (datos_procesados/inventario_fuentes.csv). Permite ofrecer el
# Detalle_Gobernanza a un clic (Req 5.5): la población por parròquia es F01 y
# los precios de oferta de Indomio (PROXY) son F02.
ID_FUENTE_INDICADOR = {
    "poblacion": "F01",
    "precio_venta": "F02",
}

# Nombres de columna del GeoJSON donde suele venir el nombre de la parròquia.
# El GeoJSON de OpenStreetMap expone el nombre bajo varias claves habituales
# ("name", "name:ca", etc.); se prueban en orden hasta encontrar una que mapee a
# una parròquia canónica (Req 1.1).
_CLAVES_NOMBRE_GEOJSON = ("name", "name:ca", "NOM", "nom", "NAME", "parroquia")

# Plan B (Req 1.5): centroides aproximados (lat, lon) de las 7 parròquies de
# Andorra. Se usan sólo cuando no hay GeoJSON de límites disponible, para
# degradar a una representación por puntos con st.map (un punto por parròquia)
# sin interrumpir la vista. Son coordenadas aproximadas del núcleo de cada
# parròquia, suficientes para situar los marcadores sobre el mapa.
CENTROIDES_PARROQUIES = {
    "Andorra la Vella": (42.5063, 1.5218),
    "Canillo": (42.5676, 1.5976),
    "Encamp": (42.5361, 1.5836),
    "Escaldes-Engordany": (42.5100, 1.5389),
    "La Massana": (42.5448, 1.5146),
    "Ordino": (42.5557, 1.5331),
    "Sant Julià de Lòria": (42.4637, 1.4914),
}


def _etiqueta_indicador(clave_interna: str) -> str:
    """Devuelve la etiqueta visible de un indicador a partir de su clave interna.

    Invierte el diccionario ``INDICADORES`` (etiqueta visible → clave interna)
    para recuperar el rótulo que ve el usuario (p. ej. ``"poblacion"`` →
    ``"Población total"``). Si la clave no se reconoce, se devuelve la propia
    clave como alternativa segura.

    Args:
        clave_interna: clave interna del indicador (``"poblacion"`` o
            ``"precio_venta"``).

    Returns:
        La etiqueta visible del indicador.
    """
    for etiqueta, clave in INDICADORES.items():
        if clave == clave_interna:
            return etiqueta
    return clave_interna


def _nombre_canonico_feature(feature: dict) -> "str | None":
    """Extrae el nombre canónico de la parròquia de una feature del GeoJSON.

    Recorre las claves de nombre habituales de las propiedades de la feature
    (``name``, ``name:ca``, etc.) y devuelve el primer nombre que
    ``mapea_nombre_parroquia`` resuelva a una de las 7 parròquies canónicas. Si
    ninguna propiedad corresponde a una parròquia conocida, devuelve ``None``
    (Req 1.1).

    Args:
        feature: una feature del GeoJSON (``dict`` con clave ``properties``).

    Returns:
        El nombre canónico de la parròquia, o ``None`` si no se reconoce.
    """
    propiedades = feature.get("properties") if isinstance(feature, dict) else None
    if not isinstance(propiedades, dict):
        return None

    for clave in _CLAVES_NOMBRE_GEOJSON:
        if clave in propiedades:
            canonico = mapea_nombre_parroquia(propiedades.get(clave))
            if canonico is not None:
                return canonico
    return None


def _tiene_geometria_poligono(feature: dict) -> bool:
    """Indica si una feature del GeoJSON tiene geometría de polígono no vacía.

    El Plan_A_Mapa sólo tiene sentido sobre polígonos reales. Esta función
    comprueba que la ``geometry`` de la feature sea de tipo ``Polygon`` o
    ``MultiPolygon`` y que sus ``coordinates`` no estén vacías, para distinguir
    una parròquia con contorno dibujable de una feature sin geometría utilizable
    (p. ej. un punto o una geometría vacía) (Req 6.6, 6.7).

    Args:
        feature: una feature del GeoJSON (``dict`` con clave ``geometry``).

    Returns:
        ``True`` si la geometría es un polígono (simple o múltiple) con
        coordenadas no vacías; ``False`` en cualquier otro caso.
    """
    if not isinstance(feature, dict):
        return False

    geometria = feature.get("geometry")
    if not isinstance(geometria, dict):
        return False

    if geometria.get("type") not in ("Polygon", "MultiPolygon"):
        return False

    coordenadas = geometria.get("coordinates")
    return isinstance(coordenadas, list) and len(coordenadas) > 0


def valida_7_parroquies_canonicas(geojson: dict) -> bool:
    """Valida que el GeoJSON cubra exactamente las 7 parròquies con polígono.

    Devuelve ``True`` si y sólo si el GeoJSON contiene, entre sus features, las
    siete parròquies canónicas (ni más ni menos, sin duplicados) y cada una con
    geometría de polígono no vacía. Es la condición que activa el Plan_A_Mapa:
    si no se cumple (faltan parròquies, hay nombres no reconocidos como únicos
    o alguna geometría no es un polígono válido), la vista debe recurrir al
    Plan_B_Mapa (Req 6.6, 6.7).

    Args:
        geojson: GeoJSON de límites de parròquies (``dict``).

    Returns:
        ``True`` si hay exactamente las 7 parròquies canónicas con geometría de
        polígono válida; ``False`` en cualquier otro caso.
    """
    if not isinstance(geojson, dict):
        return False

    features = geojson.get("features")
    if not isinstance(features, list):
        return False

    parroquies_con_poligono = set()
    for feature in features:
        canonico = _nombre_canonico_feature(feature)
        if canonico is None:
            continue
        if not _tiene_geometria_poligono(feature):
            continue
        parroquies_con_poligono.add(canonico)

    # Deben estar las 7 parròquies canónicas, cada una con polígono válido.
    return parroquies_con_poligono == set(PARROQUIES_CANONICAS)


def _prepara_geojson_canonico(geojson: dict) -> "tuple[dict, str] | None":
    """Añade a cada feature una propiedad con el nombre canónico de la parròquia.

    Devuelve una copia del GeoJSON en la que cada feature de una parròquia
    reconocida (y con geometría de polígono no vacía) lleva en ``properties``
    una clave estable (``_parroquia_canonica``) con su nombre canónico, junto al
    nombre de esa clave para usarlo como ``featureidkey`` en el coropletas. Las
    features que no corresponden a ninguna parròquia, o que no tienen geometría
    de polígono, se descartan.

    El Plan_A_Mapa exige las 7 parròquies con geometría válida: si tras filtrar
    no se obtienen exactamente las 7 parròquies canónicas, devuelve ``None`` para
    que la vista active el Plan_B_Mapa en lugar de dibujar un coropletas parcial
    (Req 6.6, 6.7).

    Args:
        geojson: GeoJSON de límites de parròquies (``dict``).

    Returns:
        Una tupla ``(geojson_canonico, clave_id)``, o ``None`` si el GeoJSON no
        contiene exactamente las 7 parròquies con geometría de polígono válida.
    """
    if not isinstance(geojson, dict):
        return None

    features = geojson.get("features")
    if not isinstance(features, list) or not features:
        return None

    # Gate del Plan A: sólo se prepara el coropletas si están las 7 parròquies
    # con geometría de polígono válida; en caso contrario, Plan B (Req 6.6, 6.7).
    if not valida_7_parroquies_canonicas(geojson):
        return None

    clave_id = "_parroquia_canonica"
    features_canonicas = []
    for feature in features:
        canonico = _nombre_canonico_feature(feature)
        if canonico is None:
            # Feature que no corresponde a ninguna de las 7 parròquies: se omite
            # para no introducir polígonos ajenos en el coropletas.
            continue
        if not _tiene_geometria_poligono(feature):
            # Feature de una parròquia pero sin geometría de polígono utilizable:
            # se omite para no romper el dibujo del coropletas.
            continue
        propiedades = dict(feature.get("properties") or {})
        propiedades[clave_id] = canonico
        features_canonicas.append({**feature, "properties": propiedades})

    if not features_canonicas:
        return None

    geojson_canonico = {**geojson, "features": features_canonicas}
    return geojson_canonico, clave_id


def _dibuja_coropletas(tabla: "pd.DataFrame", geojson: dict, clave_interna: str) -> bool:
    """Dibuja el coropletas con Plotly Express sobre el GeoJSON de parròquies.

    Colorea cada parròquia según el valor del indicador (``color_continuous_scale``
    con ``range_color`` para la leyenda de rango) usando el estilo
    ``open-street-map`` (sin token) y ``use_container_width=True`` para que sea
    usable en móvil (Req 1.1, 1.2, 1.3). Las parròquies sin dato (``valor`` None)
    conservan su polígono pero con un color neutro distinto, para que se
    distingan de las coloreadas sin perderlas (Req 1.6).

    Args:
        tabla: tabla parròquia→valor del indicador con su gobernanza.
        geojson: GeoJSON de límites de parròquies (``dict``).
        clave_interna: clave interna del indicador seleccionado.

    Returns:
        ``True`` si el coropletas se dibujó; ``False`` si el GeoJSON no contenía
        las 7 parròquies con geometría de polígono válida (la vista activará el
        Plan B).
    """
    # Import perezoso: plotly sólo se necesita en tiempo de ejecución para
    # dibujar el mapa. Así el módulo sigue siendo importable aunque plotly no
    # esté instalado (py_compile/validación), y la vista degrada con un mensaje
    # en español si la dependencia falta (Req 1.5).
    try:
        import plotly.express as px
    except Exception as error:  # noqa: BLE001 - degradación segura en la app
        import streamlit as st

        st.warning(
            "No se pudo cargar la librería de mapas (plotly). Se muestra la "
            "representación alternativa por puntos."
        )
        print(f"[mapa] No se pudo importar plotly: {error}.")
        return False

    import streamlit as st

    preparado = _prepara_geojson_canonico(geojson)
    if preparado is None:
        # El GeoJSON existe pero no contiene los límites de las parròquies: se
        # trata como ausencia de límites administrativos y se activa el Plan B.
        return False

    geojson_canonico, clave_id = preparado

    etiqueta = _etiqueta_indicador(clave_interna)
    datos = tabla.copy()
    datos["valor_color"] = pd.to_numeric(datos["valor"], errors="coerce")

    # Rango de la leyenda de color a partir de las parròquies con dato. Si no
    # hubiera ningún valor, se usa un rango trivial para no romper el dibujo.
    valores = datos["valor_color"].dropna()
    if not valores.empty:
        rango_color = (float(valores.min()), float(valores.max()))
    else:
        rango_color = (0.0, 1.0)

    figura = px.choropleth_mapbox(
        datos,
        geojson=geojson_canonico,
        locations="parroquia",
        featureidkey=f"properties.{clave_id}",
        color="valor_color",
        color_continuous_scale="Viridis",
        range_color=rango_color,
        mapbox_style="open-street-map",  # Estilo libre, sin token de Mapbox.
        center={"lat": 42.5063, "lon": 1.5218},
        zoom=9.5,
        opacity=0.65,
        labels={"valor_color": etiqueta},
        hover_name="parroquia",
    )
    # Las parròquies sin dato (valor NaN) se pintan con un color neutro distinto
    # del gradiente, conservando su polígono (Req 1.6).
    figura.update_coloraxes(colorbar_title_text=etiqueta)
    figura.update_traces(marker_line_width=0.8, marker_line_color="white")
    figura.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.plotly_chart(figura, use_container_width=True)
    st.caption(
        "Las parròquies sin dato del indicador seleccionado se muestran sin "
        "color de relleno del gradiente, conservando su contorno."
    )
    return True


def _plan_b_por_centroides(tabla: "pd.DataFrame", clave_interna: str) -> None:
    """Plan B: representa las parròquies por puntos (centroides) con ``st.map``.

    Se activa cuando no hay GeoJSON de límites disponible o no puede leerse
    (Req 1.5). Dibuja un marcador por parròquia en su centroide aproximado,
    dimensionando el punto según el valor del indicador para transmitir la
    magnitud sin coropletas. Deja constancia (comentario y texto en la vista) de
    que es la representación degradada por puntos y de que el coropletas quedó
    pendiente.

    Args:
        tabla: tabla parròquia→valor del indicador con su gobernanza.
        clave_interna: clave interna del indicador seleccionado.
    """
    import streamlit as st

    st.info(
        "Plan B activo: no hay límites administrativos (GeoJSON) disponibles, "
        "así que el mapa se representa por puntos sobre los centroides "
        "aproximados de las 7 parròquies en lugar de un coropletas."
    )

    datos = tabla.copy()
    datos["valor_color"] = pd.to_numeric(datos["valor"], errors="coerce")

    filas_mapa = []
    for _, fila in datos.iterrows():
        centroide = CENTROIDES_PARROQUIES.get(str(fila["parroquia"]))
        if centroide is None:
            continue
        lat, lon = centroide
        filas_mapa.append(
            {
                "parroquia": fila["parroquia"],
                "lat": lat,
                "lon": lon,
                "valor": fila["valor_color"],
            }
        )

    if not filas_mapa:
        st.warning(
            "No hay centroides de parròquia disponibles para la representación "
            "alternativa."
        )
        return

    mapa_df = pd.DataFrame(filas_mapa)

    # Dimensionar el punto según el indicador (las parròquies sin dato usan un
    # tamaño mínimo fijo para seguir siendo visibles, Req 1.6). st.map espera un
    # tamaño en metros; se escala el valor a un rango de radios legible.
    valores = mapa_df["valor"].dropna()
    if not valores.empty and float(valores.max()) > 0:
        maximo = float(valores.max())
        mapa_df["size"] = mapa_df["valor"].apply(
            lambda v: 300 + 1200 * (float(v) / maximo)
            if pd.notna(v) and maximo > 0
            else 200
        )
    else:
        mapa_df["size"] = 400

    try:
        # Firma moderna de st.map (admite size); si la versión de Streamlit no
        # la soporta, se degrada a un mapa de puntos sin tamaño variable.
        st.map(mapa_df, latitude="lat", longitude="lon", size="size")
    except TypeError:
        st.map(mapa_df[["lat", "lon"]])

    st.caption(
        f"Tamaño del punto proporcional a «{_etiqueta_indicador(clave_interna)}» "
        "por parròquia. El coropletas por polígono queda pendiente hasta "
        "disponer del GeoJSON de límites."
    )


def _detalle_parroquia(tabla: "pd.DataFrame", clave_interna: str) -> None:
    """Muestra el detalle gobernado de una parròquia seleccionada.

    Ofrece un selector para elegir una de las 7 parròquies y, para la elegida,
    muestra su nombre, el valor del indicador, su Metadato_Cifra y su
    Etiqueta_Linaje mediante ``componentes.cifra_gobernada`` (con el ID_Fuente
    del indicador para el Detalle_Gobernanza a un clic). Para el precio de venta
    de Indomio el linaje es PROXY (Req 1.4, 1.7); si la parròquia no tiene dato,
    ``cifra_gobernada`` muestra "Dato no disponible" sin romper la vista (Req
    1.6).

    Args:
        tabla: tabla parròquia→valor del indicador con su gobernanza.
        clave_interna: clave interna del indicador seleccionado.
    """
    import streamlit as st

    st.subheader("Detalle de una parròquia")
    parroquia = st.selectbox(
        "Selecciona una parròquia para ver su cifra gobernada",
        options=list(tabla["parroquia"]),
        key="mapa_detalle_parroquia",
    )

    filas = tabla[tabla["parroquia"] == parroquia]
    if filas.empty:
        componentes.cifra_gobernada(parroquia, None, None, None)
        return

    fila = filas.iloc[0]
    etiqueta = f"{parroquia} · {_etiqueta_indicador(clave_interna)}"

    valor = fila.get("valor")
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        # Parròquia sin dato del indicador: se muestra como no disponible.
        componentes.cifra_gobernada(etiqueta, None, None, None)
        return

    metadato = {
        "fuente": fila.get("fuente"),
        "vigencia": fila.get("vigencia"),
        "fecha_prueba": fila.get("fecha_prueba"),
    }
    linaje = fila.get("linaje")
    id_fuente = ID_FUENTE_INDICADOR.get(clave_interna)

    # Formatear el valor: el precio de venta en €/m² con dos decimales; la
    # población como entero con separador de miles.
    if clave_interna == "precio_venta":
        valor_mostrado = f"{float(valor):,.2f}".replace(",", ".")
    else:
        valor_mostrado = f"{int(valor):,}".replace(",", ".")

    componentes.cifra_gobernada(etiqueta, valor_mostrado, metadato, linaje, id_fuente)


def render() -> None:
    """Renderiza la Vista_Mapa completa.

    Dibuja el coropletas de las 7 parròquies coloreadas por el indicador
    seleccionable (población total u€/m² de venta) con Plotly Express, estilo
    ``open-street-map`` (sin token), leyenda de rango de color y
    ``use_container_width=True`` (Req 1.1, 1.2, 1.3). Las parròquies sin dato se
    dibujan con un estilo distinto conservando las demás (Req 1.6). Al
    seleccionar una parròquia muestra su nombre, valor, Metadato_Cifra y linaje
    (PROXY para el precio de Indomio) vía ``cifra_gobernada`` (Req 1.4, 1.7).

    Si el GeoJSON de límites falta o no puede leerse, muestra un mensaje en
    español sin interrumpir la vista y activa el Plan B con ``st.map`` por
    centroides de las parròquies (Req 1.5).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    import streamlit as st

    st.title("Mapa del territorio")
    st.write(
        "Indicador por parròquia sobre el mapa de Andorra. Cada cifra conserva "
        "su fuente, vigencia, fecha de prueba y etiqueta de linaje."
    )

    # Selector del indicador: se muestran las etiquetas visibles de INDICADORES
    # y se traduce la elección a su clave interna para tabla_indicador (Req 1.2).
    etiqueta_sel = st.selectbox(
        "Indicador a representar",
        options=list(INDICADORES.keys()),
        key="mapa_indicador",
    )
    clave_interna = INDICADORES[etiqueta_sel]

    tabla = tabla_indicador(clave_interna)
    if tabla is None or tabla.empty:
        st.warning(
            "No hay datos disponibles para el indicador seleccionado. No se "
            "puede dibujar el mapa."
        )
        return

    geojson = carga_datos.carga_geojson_parroquies()

    if geojson is None:
        # GeoJSON ausente o ilegible: mensaje en español + Plan B por centroides,
        # sin interrumpir la vista (Req 1.5).
        st.warning(
            "No se encontró o no se pudo leer el archivo geoespacial de límites "
            "de las parròquies (GeoJSON). Se activa la representación "
            "alternativa por puntos."
        )
        _plan_b_por_centroides(tabla, clave_interna)
    else:
        # Hay GeoJSON: intentar el Plan A. El coropletas sólo se dibuja si están
        # las 7 parròquies con geometría de polígono válida; si no, se degrada
        # al Plan B por centroides (Req 6.6, 6.7).
        dibujado = _dibuja_coropletas(tabla, geojson, clave_interna)
        if not dibujado:
            st.warning(
                "El archivo geoespacial no contiene las 7 parròquies con "
                "geometría de polígono válida. Se activa la representación "
                "alternativa por puntos (Plan B)."
            )
            _plan_b_por_centroides(tabla, clave_interna)

    _detalle_parroquia(tabla, clave_interna)
