"""Extractor ético del GeoJSON de límites de las 7 parròquies (tramo Fuentes).

Este módulo descarga desde la API de Overpass (OpenStreetMap) las relaciones
administrativas (``boundary=administrative``) correspondientes a las 7
parròquies de Andorra y guarda el resultado como
``datos_crudos/parroquias_andorra.geojson``.

Es el ÚNICO script del proyecto que escribe en ``datos_crudos/``, y lo hace
solamente para CREAR este archivo nuevo, sin modificar, sobrescribir ni
eliminar ninguno de los crudos existentes (que son la fuente de verdad).

La orquestación (``descarga``) intenta hasta 3 endpoints mirror de Overpass y,
si ninguno produce las 7 parròquies válidas, recurre al fallback de Nominatim
(una consulta de polígono por parròquia). La respuesta de Overpass con
``out geom`` NO es un GeoJSON: se convierte a un ``FeatureCollection`` y se
valida que tenga exactamente 7 polígonos no vacíos antes de usarse. Solo se
guarda el GeoJSON si supera ``valida_7_parroquies`` (Req 6.4).

Convenciones de acceso ético a fuentes externas (Req 6.1, 6.8, 8.8):
- Se envía un header ``User-Agent`` de navegador real para evitar bloqueos.
- Se aplica una pausa de cortesía con ``time.sleep()`` antes de cada petición.
- Se manejan explícitamente los códigos 200 / 429 / 406 / otros y se registra el
  resultado por consola en español.
- Si se agotan los 3 endpoints y el fallback sin obtener las 7 parròquies
  válidas, se documenta en la bitácora los endpoints probados y los códigos
  recibidos SIN guardar un GeoJSON inventado, y se devuelve ``False`` para que
  la Vista_Mapa active su Plan B (representación por centroides).

Si el archivo ya existe con las 7 parròquies de geometría válida, el extractor
NO vuelve a descargar (idempotencia y cortesía con la fuente, Req 6.5). Este
script NO forma parte del pipeline de procesamiento: se ejecuta aparte y bajo
demanda.

Los mensajes de consola van en español, coherentes con el resto del proyecto.
"""

import json
import os
import time

import requests

# Endpoints mirror de la API de Overpass (OpenStreetMap). Se prueban en orden
# (hasta 3 en total) ante un 406 u otro error, antes de recurrir al fallback de
# Nominatim (Req 6.3, diseño H3).
URLS_OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Endpoint primario de Overpass, conservado por compatibilidad con llamadas
# previas; coincide con el primer mirror de ``URLS_OVERPASS``.
URL_OVERPASS = URLS_OVERPASS[0]

# Endpoint de búsqueda de Nominatim (OpenStreetMap), usado como fallback para
# obtener el polígono de cada parròquia (diseño H2).
URL_NOMINATIM = "https://nominatim.openstreetmap.org/search"

# Nombres canónicos de las 7 parròquies de Andorra (fallback Nominatim: una
# consulta por parròquia).
PARROQUIES_CANONICAS = [
    "Canillo",
    "Encamp",
    "Ordino",
    "La Massana",
    "Andorra la Vella",
    "Sant Julià de Lòria",
    "Escaldes-Engordany",
]

# Ruta de salida del GeoJSON de límites, relativa a la carpeta scripts/.
RUTA_SALIDA_GEOJSON = "../datos_crudos/parroquias_andorra.geojson"

# Ruta de la bitácora donde se documenta la descarga y sus bloqueos.
RUTA_BITACORA = "../documentacion_bitacora/5_descarga_limites_parroquias.md"

# User-Agent de navegador real para identificarnos ante el servidor y evitar
# bloqueos anti-bot (403/406) (Req 6.1).
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Pausa de cortesía (en segundos) antes de cada consulta a Overpass. >= 12 s
# garantiza no superar el límite de 5 peticiones/minuto de la fuente (Req 6.1,
# 6.2). Nominatim exige una pausa distinta (>= 1 s/petición).
PAUSA_OVERPASS_S = 12

# Pausa de cortesía (en segundos) entre consultas a Nominatim: la fuente exige
# respetar >= 1 petición por segundo (diseño H2).
PAUSA_NOMINATIM_S = 1

# Compatibilidad con el nombre previo de la pausa de Overpass.
PAUSA_CORTESIA_S = PAUSA_OVERPASS_S

# Número máximo de reintentos ante un HTTP 429 por endpoint (Req 6.2).
MAX_REINTENTOS_429 = 3

# Tiempo máximo de espera de la respuesta HTTP, en segundos (Req 6.1).
TIMEOUT_HTTP_S = 30


def ya_descargado(ruta: str) -> bool:
    """Indica si ya existe un GeoJSON de parròquies VÁLIDO en disco.

    Devuelve ``True`` solo cuando el archivo existe y contiene exactamente 7
    features de parròquia con geometría de polígono válida (Req 6.5). En ese
    caso NO se vuelve a descargar, por idempotencia y cortesía con la fuente.

    Un archivo ausente, ilegible, no-JSON o que no supere ``valida_7_parroquies``
    devuelve ``False`` para que la orquestación intente obtenerlo de nuevo.
    """
    return _lee_geojson_valido(ruta) is not None


def construye_consulta_overpass() -> str:
    """Devuelve la consulta Overpass QL de los límites de parròquia de Andorra.

    Selecciona las relaciones administrativas (``boundary=administrative``) de
    Andorra con ``admin_level=7`` (el nivel de las parròquies en OSM). Son los 7
    límites de parròquia: Canillo, Encamp, Ordino, La Massana, Andorra la Vella,
    Sant Julià de Lòria y Escaldes-Engordany. Se pide la salida en formato
    GeoJSON directamente (``out:json`` con geometrías) para que la Vista_Mapa la
    consuma como coropletas.
    """
    return (
        "[out:json][timeout:90];\n"
        '// Área de Andorra (código ISO3166-1 "AD").\n'
        'area["ISO3166-1"="AD"][admin_level=2]->.andorra;\n'
        "// Las 7 parròquies son relaciones administrativas de admin_level 7.\n"
        'relation["boundary"="administrative"]["admin_level"="7"](area.andorra);\n'
        "out geom;"
    )


def descarga_overpass(url: str) -> "dict | None":
    """Descarga los límites de parròquia desde un mirror de Overpass.

    Realiza la Peticion_Etica que corrige el HTTP 406 del intento original
    (diseño H3): usa ``POST`` enviando la consulta en el cuerpo (``data=consulta``)
    con las cabeceras ``Accept: application/json`` y
    ``Content-Type: application/x-www-form-urlencoded``, además del
    ``User-Agent`` de navegador real. Aplica la pausa de cortesía
    ``PAUSA_OVERPASS_S`` (>= 12 s) antes de consultar y un ``timeout`` de
    ``TIMEOUT_HTTP_S`` segundos (Req 6.1).

    Maneja explícitamente los códigos y registra en español el HTTP recibido:

    - 200: devuelve el objeto JSON ya parseado.
    - 429: reintenta hasta ``MAX_REINTENTOS_429`` veces, esperando el tiempo
      indicado por la respuesta (``Retry-After``) o al menos ``PAUSA_OVERPASS_S``
      segundos entre reintentos (Req 6.2); si no obtiene 200, devuelve ``None``.
    - 406 u otro código distinto de 200: registra el código y devuelve ``None``
      para que el orquestador pruebe el siguiente endpoint (Req 6.3).

    Devuelve ``None`` ante cualquier fallo (error de red, código no 200 o
    contenido no JSON). No escribe en disco: solo descarga y parsea.
    """
    consulta = construye_consulta_overpass()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    for intento in range(1, MAX_REINTENTOS_429 + 1):
        # Pausa de cortesía ANTES de cada petición para respetar el límite de
        # tasa de la fuente (<= 5 peticiones/minuto).
        print(
            f"Pausa de cortesía de {PAUSA_OVERPASS_S} segundos antes de "
            f"consultar Overpass ({url})..."
        )
        time.sleep(PAUSA_OVERPASS_S)

        print(f"Descargando límites de parròquia desde Overpass: {url}")
        try:
            respuesta = requests.post(
                url,
                data=consulta,
                headers=headers,
                timeout=TIMEOUT_HTTP_S,
            )
        except requests.exceptions.RequestException as err:
            print(f"   ✖ Error de red al contactar Overpass ({url}): {err}")
            return None

        codigo = respuesta.status_code
        print(f"   Código HTTP recibido de Overpass ({url}): {codigo}")

        if codigo == 200:
            try:
                return respuesta.json()
            except ValueError as err:
                print(
                    "   ✖ Respuesta 200 pero el contenido no es JSON válido: "
                    f"{err}"
                )
                return None

        if codigo == 429:
            # Límite de peticiones: respeta Retry-After si viene, si no espera
            # al menos la pausa de cortesía antes de reintentar (Req 6.2).
            espera = PAUSA_OVERPASS_S
            cabecera_retry = respuesta.headers.get("Retry-After")
            if cabecera_retry is not None:
                try:
                    espera = max(PAUSA_OVERPASS_S, int(cabecera_retry))
                except (TypeError, ValueError):
                    espera = PAUSA_OVERPASS_S
            if intento < MAX_REINTENTOS_429:
                print(
                    f"   ⚠ Límite de peticiones (HTTP 429) en {url}. "
                    f"Reintento {intento} de {MAX_REINTENTOS_429 - 1}; "
                    f"espera de {espera} segundos."
                )
                time.sleep(espera)
                continue
            print(
                f"   ⚠ Límite de peticiones (HTTP 429) en {url} tras "
                f"{MAX_REINTENTOS_429} intentos. Se abandona este endpoint."
            )
            return None

        if codigo == 406:
            print(
                f"   ✖ Error HTTP 406 (No Aceptable) en {url}. Se probará el "
                "siguiente endpoint alternativo."
            )
            return None

        # Cualquier otro código se maneja como error explícito.
        print(
            f"   ✖ Error al descargar desde Overpass {url} (código HTTP "
            f"{codigo}). Se probará el siguiente endpoint alternativo."
        )
        return None

    return None


def descarga_nominatim_parroquia(parroquia: str) -> "dict | None":
    """Descarga el polígono GeoJSON de una parròquia desde Nominatim (OSM).

    Fallback del Plan A del mapa (diseño H2). Realiza la Peticion_Etica contra
    ``URL_NOMINATIM`` con los parámetros ``q='<parroquia>, Andorra'``,
    ``format=json``, ``polygon_geojson=1`` y ``limit=1``, enviando el
    ``User-Agent`` de navegador real y respetando la pausa de cortesía que la
    fuente exige (``PAUSA_NOMINATIM_S`` >= 1 s por petición) ANTES de consultar,
    con un ``timeout`` de ``TIMEOUT_HTTP_S`` (30 s) (Req 6.3).

    Del primer resultado extrae el campo ``geojson`` y devuelve el objeto
    GeoJSON de geometría (``Polygon`` o ``MultiPolygon``). Devuelve ``None`` si
    hay error de red, el código no es 200, el contenido no es JSON, no hay
    resultados o el resultado no trae un ``geojson`` de polígono válido.
    Registra por consola en español el código HTTP recibido. No escribe en
    disco.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    params = {
        "q": f"{parroquia}, Andorra",
        "format": "json",
        "polygon_geojson": 1,
        "limit": 1,
    }

    # Pausa de cortesía ANTES de la petición: Nominatim exige >= 1 petición por
    # segundo (diseño H2, Req 6.3).
    print(
        f"Pausa de cortesía de {PAUSA_NOMINATIM_S} s antes de consultar "
        f"Nominatim para «{parroquia}»..."
    )
    time.sleep(PAUSA_NOMINATIM_S)

    print(f"Descargando límite de «{parroquia}» desde Nominatim.")
    try:
        respuesta = requests.get(
            URL_NOMINATIM,
            params=params,
            headers=headers,
            timeout=TIMEOUT_HTTP_S,
        )
    except requests.exceptions.RequestException as err:
        print(f"   ✖ Error de red al contactar Nominatim («{parroquia}»): {err}")
        return None

    codigo = respuesta.status_code
    print(f"   Código HTTP recibido de Nominatim («{parroquia}»): {codigo}")

    if codigo != 200:
        print(
            f"   ✖ Nominatim devolvió HTTP {codigo} para «{parroquia}»; no se "
            "obtiene el polígono."
        )
        return None

    try:
        resultados = respuesta.json()
    except ValueError as err:
        print(
            f"   ✖ Respuesta 200 de Nominatim para «{parroquia}» pero el "
            f"contenido no es JSON válido: {err}"
        )
        return None

    if not isinstance(resultados, list) or not resultados:
        print(f"   ✖ Nominatim no devolvió resultados para «{parroquia}».")
        return None

    geojson = resultados[0].get("geojson") if isinstance(resultados[0], dict) else None
    if not isinstance(geojson, dict) or geojson.get("type") not in (
        "Polygon",
        "MultiPolygon",
    ):
        print(
            f"   ✖ El resultado de Nominatim para «{parroquia}» no trae un "
            "polígono (Polygon/MultiPolygon)."
        )
        return None

    if not geojson.get("coordinates"):
        print(
            f"   ✖ El polígono de «{parroquia}» en Nominatim no tiene "
            "coordenadas."
        )
        return None

    print(f"   ✓ Polígono de «{parroquia}» obtenido de Nominatim.")
    return geojson


def construye_featurecollection_nominatim() -> "dict | None":
    """Construye el ``FeatureCollection`` de las 7 parròquies vía Nominatim.

    Itera ``PARROQUIES_CANONICAS`` consultando ``descarga_nominatim_parroquia``
    para cada una y acumula un ``Feature`` por parròquia con su geometría de
    polígono y la propiedad ``name`` (nombre canónico). Solo devuelve el
    ``FeatureCollection`` si consigue EXACTAMENTE 7 polígonos no vacíos; en caso
    contrario registra en español cuántos se obtuvieron y devuelve ``None`` para
    que el orquestador documente el bloqueo sin guardar un GeoJSON incompleto
    (Req 6.3, 6.4).
    """
    features = []
    for parroquia in PARROQUIES_CANONICAS:
        geometria = descarga_nominatim_parroquia(parroquia)
        if geometria is None:
            print(
                f"   ⚠ No se obtuvo el polígono de «{parroquia}» desde "
                "Nominatim."
            )
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"name": parroquia},
                "geometry": geometria,
            }
        )

    if len(features) != len(PARROQUIES_CANONICAS):
        print(
            "   ✖ Nominatim solo devolvió "
            f"{len(features)} de {len(PARROQUIES_CANONICAS)} polígonos de "
            "parròquia; no se construye el FeatureCollection (Req 6.4)."
        )
        return None

    print(
        f"   ✓ FeatureCollection de Nominatim con las "
        f"{len(features)} parròquies construido."
    )
    return {"type": "FeatureCollection", "features": features}


def _overpass_a_featurecollection(overpass_json: dict) -> "dict | None":
    """Convierte la respuesta de Overpass (``out geom``) a un ``FeatureCollection``.

    La salida de Overpass con ``out geom;`` NO es un GeoJSON: es el formato
    propio de Overpass, con una lista ``elements`` donde cada relación
    administrativa trae sus miembros (``members``) con la geometría (``geometry``)
    de cada *way* como lista de puntos ``{"lat": ..., "lon": ...}``.

    Esta función arma, para cada relación de parròquia, un ``Feature`` cuya
    geometría es un ``MultiPolygon`` compuesto por los anillos de sus *ways* con
    rol ``outer`` (o, en su defecto, todos los *ways* con geometría). Las
    coordenadas se emiten en orden GeoJSON ``[lon, lat]``. La propiedad ``name``
    se resuelve al nombre canónico vía ``mapea_nombre_parroquia`` para que la
    Vista_Mapa la consuma; si el nombre no mapea, se conserva el nombre crudo de
    las etiquetas (``tags``).

    Devuelve el ``FeatureCollection`` resultante (sin forzar que tenga 7
    features: de eso se encarga ``valida_7_parroquies``), o ``None`` si la
    estructura no es la esperada o no se pudo extraer ninguna geometría.
    """
    # Import local para no crear dependencia de arranque con el paquete de la
    # app; mapea_nombre_parroquia es una función total que tolera cualquier
    # entrada.
    try:
        from app.vistas.mapa import mapea_nombre_parroquia
    except Exception:  # pragma: no cover - defensa ante layout de import
        mapea_nombre_parroquia = None  # type: ignore[assignment]

    if not isinstance(overpass_json, dict):
        return None
    elementos = overpass_json.get("elements")
    if not isinstance(elementos, list):
        return None

    features = []
    for elemento in elementos:
        if not isinstance(elemento, dict) or elemento.get("type") != "relation":
            continue

        miembros = elemento.get("members")
        if not isinstance(miembros, list):
            continue

        # Anillos de los ways con rol "outer"; si no hay ningún rol "outer"
        # etiquetado, se toman todos los ways con geometría como respaldo.
        anillos_outer = []
        anillos_todos = []
        for miembro in miembros:
            if not isinstance(miembro, dict) or miembro.get("type") != "way":
                continue
            geometria = miembro.get("geometry")
            if not isinstance(geometria, list) or not geometria:
                continue
            puntos = [
                [punto["lon"], punto["lat"]]
                for punto in geometria
                if isinstance(punto, dict)
                and "lon" in punto
                and "lat" in punto
            ]
            if len(puntos) < 3:
                continue
            # Cierra el anillo si no viene cerrado (GeoJSON exige primer=último).
            if puntos[0] != puntos[-1]:
                puntos.append(puntos[0])
            anillos_todos.append(puntos)
            if miembro.get("role") == "outer":
                anillos_outer.append(puntos)

        anillos = anillos_outer if anillos_outer else anillos_todos
        if not anillos:
            continue

        # Cada anillo exterior se modela como un polígono independiente del
        # MultiPolygon (sin resolver huecos: suficiente para validar y pintar).
        coordenadas = [[anillo] for anillo in anillos]

        tags = elemento.get("tags")
        nombre_crudo = tags.get("name") if isinstance(tags, dict) else None
        nombre = None
        if mapea_nombre_parroquia is not None and nombre_crudo is not None:
            nombre = mapea_nombre_parroquia(nombre_crudo)
        if nombre is None:
            nombre = nombre_crudo

        features.append(
            {
                "type": "Feature",
                "properties": {"name": nombre},
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": coordenadas,
                },
            }
        )

    if not features:
        print(
            "   ✖ No se pudo convertir la respuesta de Overpass a polígonos "
            "GeoJSON (sin geometrías utilizables)."
        )
        return None

    return {"type": "FeatureCollection", "features": features}


def valida_7_parroquies(geojson: dict) -> bool:
    """Valida que un GeoJSON contenga los 7 límites de parròquia válidos.

    Devuelve ``True`` si y solo si el objeto es un ``FeatureCollection`` con
    exactamente 7 features, cada una con una geometría de tipo ``Polygon`` o
    ``MultiPolygon`` cuyas coordenadas no están vacías (Req 6.4). Cualquier otra
    estructura (tipo inesperado, número distinto de 7, geometría ausente, no
    poligonal o sin coordenadas) devuelve ``False``.
    """
    if not isinstance(geojson, dict):
        return False
    if geojson.get("type") != "FeatureCollection":
        return False

    features = geojson.get("features")
    if not isinstance(features, list) or len(features) != 7:
        return False

    for feature in features:
        if not isinstance(feature, dict):
            return False
        geometria = feature.get("geometry")
        if not isinstance(geometria, dict):
            return False
        if geometria.get("type") not in ("Polygon", "MultiPolygon"):
            return False
        if not geometria.get("coordinates"):
            return False

    return True


def _documenta_bloqueo_bitacora(motivo: str) -> None:
    """Registra en la bitácora un bloqueo o fallo de la descarga del GeoJSON.

    Deja constancia del hallazgo (p. ej. un 429 o un error de red) en lugar de
    forzar el acceso, coherente con las convenciones del proyecto. No interrumpe
    la ejecución si la bitácora no puede escribirse.
    """
    entrada = (
        "\n## Hallazgo de descarga ({})\n\n"
        "- Fuente: Overpass API (OpenStreetMap), límites de parròquia.\n"
        "- Resultado: {}\n"
        "- Decisión: no se fuerza el acceso; la Vista_Mapa usa el Plan B "
        "(representación por centroides).\n"
    ).format(time.strftime("%Y-%m-%d %H:%M:%S"), motivo)
    try:
        os.makedirs(os.path.dirname(RUTA_BITACORA), exist_ok=True)
        # Se añade al final para conservar el histórico de intentos.
        with open(RUTA_BITACORA, "a", encoding="utf-8") as bitacora:
            bitacora.write(entrada)
        print(f"   Hallazgo documentado en la bitácora: {RUTA_BITACORA}")
    except OSError as err:
        print(f"   Aviso: no se pudo escribir en la bitácora ({err}).")


def _lee_geojson_valido(ruta: str) -> "dict | None":
    """Lee un GeoJSON de disco y lo devuelve solo si valida las 7 parròquies.

    Sirve de base a la idempotencia (Req 6.5): si el archivo ya existe y
    contiene exactamente 7 features con geometría de polígono válida, se
    devuelve el objeto para omitir una nueva descarga. Devuelve ``None`` si el
    archivo no existe, no puede leerse, no es JSON o no supera
    ``valida_7_parroquies``.
    """
    if not os.path.isfile(ruta):
        return None
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            geojson = json.load(archivo)
    except (OSError, ValueError) as err:
        print(
            f"   ⚠ El GeoJSON existente en {ruta} no se pudo leer o no es JSON "
            f"válido ({err}); se intentará descargar de nuevo."
        )
        return None
    if not valida_7_parroquies(geojson):
        print(
            f"   ⚠ El GeoJSON existente en {ruta} no contiene las 7 parròquies "
            "con geometría válida; se intentará descargar de nuevo."
        )
        return None
    return geojson


def _guarda_geojson(geojson: dict, ruta_salida: str) -> None:
    """Escribe el ``FeatureCollection`` validado en ``ruta_salida``.

    Crea el directorio de salida de forma idempotente con
    ``os.makedirs(..., exist_ok=True)`` y escribe en UTF-8. Es el único punto
    que crea el archivo nuevo en ``datos_crudos/``; nunca toca otros ficheros
    (Req 6.4, 8.8).
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(geojson, archivo, ensure_ascii=False)


def descarga(ruta_salida: str) -> bool:
    """Orquesta la obtención ética del GeoJSON de límites de parròquia.

    Flujo (diseño H2/H3):

    1. **Idempotencia (Req 6.5):** si ``ruta_salida`` ya existe y contiene las 7
       parròquies con geometría válida, no se re-descarga y se devuelve
       ``True`` conservando el archivo (y el resto de ``datos_crudos/``) intacto.
    2. **Overpass (hasta 3 endpoints, Req 6.3):** se prueba cada mirror de
       ``URLS_OVERPASS`` con la Peticion_Etica corregida (POST + cabeceras que
       arreglan el 406). La respuesta de Overpass (``out geom``) no es GeoJSON,
       así que se convierte con ``_overpass_a_featurecollection``; si el
       resultado valida las 7 parròquies, se usa.
    3. **Fallback Nominatim (Req 6.3, 6.4):** si ningún endpoint de Overpass
       produjo 7 polígonos válidos, se intenta
       ``construye_featurecollection_nominatim``.
    4. **Guardado (Req 6.4):** solo se guarda el GeoJSON si ``valida_7_parroquies``
       es ``True``. Jamás se guarda un GeoJSON inventado o incompleto.
    5. **Bloqueo total (Req 6.8):** si tras agotar los 3 endpoints y el fallback
       no se consiguen las 7 parròquies, se documenta en la bitácora los
       endpoints probados y los códigos observados, NO se guarda nada y se
       devuelve ``False`` para que la Vista_Mapa active su Plan B.

    Nunca sobrescribe ni elimina otros archivos de ``datos_crudos/``: solo crea
    el archivo nuevo ``ruta_salida`` (Req 6.4, 8.8).
    """
    # 1. Idempotencia: si ya hay un GeoJSON válido, no se re-descarga (Req 6.5).
    if _lee_geojson_valido(ruta_salida) is not None:
        print(
            f"   ✓ El GeoJSON de parròquies ya existe y es válido: {ruta_salida}. "
            "No se vuelve a descargar (idempotencia)."
        )
        return True

    # Traza de endpoints probados y su resultado, para documentar un eventual
    # bloqueo total en la bitácora (Req 6.8).
    endpoints_probados = []

    # 2. Overpass: hasta 3 endpoints mirror. La respuesta no es GeoJSON, se
    #    convierte y se valida; el primero que dé 7 parròquies válidas se usa.
    for url in URLS_OVERPASS[:3]:
        overpass_json = descarga_overpass(url)
        if overpass_json is None:
            endpoints_probados.append(
                f"Overpass {url}: sin respuesta utilizable (ver código HTTP "
                "registrado por consola)"
            )
            continue

        geojson = _overpass_a_featurecollection(overpass_json)
        if geojson is not None and valida_7_parroquies(geojson):
            _guarda_geojson(geojson, ruta_salida)
            print(
                f"   ✓ GeoJSON de las 7 parròquies obtenido de Overpass ({url}) "
                f"y guardado en: {ruta_salida}"
            )
            return True

        endpoints_probados.append(
            f"Overpass {url}: respondió pero no se obtuvieron 7 polígonos de "
            "parròquia válidos"
        )
        print(
            f"   ⚠ El endpoint Overpass {url} no produjo las 7 parròquies "
            "válidas; se prueba el siguiente."
        )

    # 3. Fallback Nominatim (una consulta por parròquia).
    print(
        "   ⚠ Ningún endpoint de Overpass produjo las 7 parròquies; se recurre "
        "al fallback de Nominatim."
    )
    geojson_nominatim = construye_featurecollection_nominatim()
    if geojson_nominatim is not None and valida_7_parroquies(geojson_nominatim):
        _guarda_geojson(geojson_nominatim, ruta_salida)
        print(
            f"   ✓ GeoJSON de las 7 parròquies obtenido de Nominatim y guardado "
            f"en: {ruta_salida}"
        )
        return True

    endpoints_probados.append(
        f"Nominatim {URL_NOMINATIM}: no se obtuvieron las 7 parròquies con "
        "geometría válida"
    )

    # 5. Bloqueo total: se documenta en la bitácora y NO se guarda nada (Req 6.8).
    motivo = (
        "Agotados los endpoints sin obtener las 7 parròquies con geometría "
        "válida. Endpoints probados y resultado:\n"
        + "\n".join(f"  - {detalle}" for detalle in endpoints_probados)
    )
    print(f"   ✖ {motivo}")
    _documenta_bloqueo_bitacora(motivo)
    return False


def main() -> int:
    """Orquesta la descarga ética e idempotente del GeoJSON de parròquies.

    - Si el archivo ya existe, informa y termina sin descargar (idempotencia).
    - Si no existe, intenta la descarga ética.

    Devuelve ``0`` si hay GeoJSON disponible (recién descargado o previo) y un
    código ``!= 0`` si no se pudo obtener (la Vista_Mapa usará el Plan B).
    """
    print("--- Descarga ética de límites de parròquia (OpenStreetMap) ---")

    if ya_descargado(RUTA_SALIDA_GEOJSON):
        print(
            "El GeoJSON de parròquies ya existe y es válido (7 parròquies); no "
            f"se vuelve a descargar: {RUTA_SALIDA_GEOJSON}"
        )
        return 0

    # ``descarga`` reaplica la comprobación de idempotencia y orquesta la cadena
    # Overpass -> Nominatim, guardando solo si valida las 7 parròquies.
    exito = descarga(RUTA_SALIDA_GEOJSON)
    if exito:
        print("Descarga finalizada correctamente.")
        return 0

    print(
        "No se pudo obtener el GeoJSON de parròquies. La Vista_Mapa activará su "
        "Plan B (representación por centroides)."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
