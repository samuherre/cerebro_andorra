"""Generación del Inventario_Fuentes de Cerebro Andorra (tramo Catálogo).

Cataloga cada dataset del proyecto con su nombre, fuente, etiqueta de linaje
(OBSERVADO/ESTIMADO/PROXY) y estado (integrado/candidato/caído/excluido),
además del motivo cuando corresponde. El catálogo es una lista declarativa en
este propio módulo (no se descubre dinámicamente en v1), lo que hace el
inventario reproducible y auditable (Req 4).

Convenciones del repositorio: el script se ejecuta desde ``scripts/`` y escribe
con la ruta relativa ``../datos_procesados``; nunca escribe en
``datos_crudos/``. Todos los mensajes de consola van en español.
"""

import csv
import os

import gobernanza
from procesa_inversiones import FUENTE_INVERSIONES
from procesa_turismo import FUENTE_TURISMO

# Ruta de salida del inventario (relativa a la carpeta scripts/).
RUTA_SALIDA_INVENTARIO = "../datos_procesados/inventario_fuentes.csv"

# Columnas EXTENDIDAS del inventario: a las columnas de la Parte 2
# (``id_fuente``, ``nombre``, ``fuente``, ``vigencia``, ``fecha_prueba``,
# ``linaje``, ``estado``, ``motivo``) se añade al final ``licencia`` (texto de
# licencia literal de la fuente) para la Parte 3 (Req 4.9, 8.4, 8.5). El orden
# es el de escritura en la cabecera del CSV; ``licencia`` va al final para no
# alterar la posición de las columnas previas.
COLUMNAS_INVENTARIO = [
    "id_fuente",
    "nombre",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
    "estado",
    "motivo",
    "licencia",
]

# Fuentes canónicas reutilizadas en varios registros del catálogo.
FUENTE_ESTADISTICA = "Departament d'Estadística d'Andorra (sig.govern.ad)"
FUENTE_INDOMIO = "Indomio (scraping, precios de oferta)"
FUENTE_OSM = "OpenStreetMap vía Overpass API"
# Fuente oficial de la economía World Bank (debe coincidir con
# ``procesa_economia.FUENTE_WB`` para que la vista resuelva el id_fuente).
FUENTE_WORLDBANK = "Banco Mundial (World Bank Open Data, API v2)"

# Textos de licencia literal por fuente (Req 4.9, 8.4, 8.5).
LICENCIA_ESTADISTICA = "Departament d'Estadística d'Andorra"
LICENCIA_INDOMIO = ""
LICENCIA_OSM = "ODbL (OpenStreetMap contributors)"
LICENCIA_WORLDBANK = "CC BY 4.0"

# Vigencia (periodo cubierto) de las fuentes nuevas de la Parte 3.
VIGENCIA_DESGLOSES = "2020-2025"
VIGENCIA_SOCIALES = "2020-2025"
VIGENCIA_WORLDBANK = "2015-2024"

# Vigencia (periodo cubierto) de las fuentes OBSERVADO nuevas: ambos crudos
# traen las columnas de año 2020..2025 (ver procesa_turismo/procesa_inversiones).
VIGENCIA_TURISMO = "2020-2025"
VIGENCIA_INVERSIONES = "2020-2025"

# Formato del ID_Fuente: la letra 'F' seguida de exactamente dos dígitos,
# soportando de F01 a F99 (hasta 99 fuentes) (Req 5.1).
PRIMER_ID = 1
ULTIMO_ID = 99


def clave_fuente(registro: dict) -> str:
    """Devuelve la clave lógica estable de una fuente dentro del catálogo.

    La clave se deriva del ``nombre`` del dataset (no de su posición en la
    lista), de modo que una misma fuente produce siempre la misma clave entre
    ejecuciones. Esto es la base para conservar su ``id_fuente`` idéntico
    carácter a carácter aunque cambien sus demás atributos (Req 5.2).

    El ``nombre`` se normaliza quitando espacios sobrantes de los extremos para
    evitar que diferencias triviales de formato generen claves distintas.

    Args:
        registro: entrada del catálogo (o fila del inventario) con ``nombre``.

    Returns:
        Clave lógica estable (el nombre normalizado) de la fuente.
    """
    nombre = registro.get("nombre", "")
    return str(nombre).strip()


def carga_ids_existentes(ruta_inventario: str) -> dict:
    """Lee el inventario previo y devuelve el mapa ``clave -> id_fuente``.

    Si el inventario ``ruta_inventario`` ya existe, se lee (separador ``;``,
    UTF-8) y se construye un mapa de clave lógica de fuente a ``id_fuente`` con
    los IDs ya asignados, para conservarlos idénticos en la nueva ejecución
    (Req 5.2). Sólo se consideran filas con un ``id_fuente`` no vacío. Si el
    archivo no existe, o no puede leerse, o carece de las columnas necesarias,
    se devuelve un mapa vacío ``{}`` (primera ejecución o inventario ilegible),
    registrando el hallazgo en la bitácora.

    Args:
        ruta_inventario: ruta del CSV de inventario previo.

    Returns:
        Mapa ``clave_fuente -> id_fuente`` de los IDs ya asignados; ``{}`` si no
        hay inventario previo utilizable.
    """
    if not os.path.exists(ruta_inventario):
        print(
            f"[inventario] No existe inventario previo en '{ruta_inventario}'; "
            "se asignarán ID_Fuente nuevos desde cero."
        )
        return {}

    ids_previos: dict = {}
    try:
        with open(ruta_inventario, "r", encoding="utf-8", newline="") as archivo:
            lector = csv.DictReader(archivo, delimiter=";")
            if lector.fieldnames is None or "id_fuente" not in lector.fieldnames:
                print(
                    f"[inventario] El inventario previo '{ruta_inventario}' no "
                    "tiene la columna 'id_fuente'; se ignora y se reasignan IDs."
                )
                return {}
            for fila in lector:
                id_fuente = (fila.get("id_fuente") or "").strip()
                if not id_fuente:
                    continue
                clave = clave_fuente(fila)
                # La primera aparición de una clave fija su ID (se conserva).
                ids_previos.setdefault(clave, id_fuente)
    except OSError as error:
        print(
            f"[inventario] No se pudo leer el inventario previo "
            f"'{ruta_inventario}': {error}. Se reasignan IDs desde cero."
        )
        return {}

    print(
        f"[inventario] Cargados {len(ids_previos)} ID_Fuente previo(s) desde "
        f"'{ruta_inventario}' para conservarlos."
    )
    return ids_previos


def siguiente_id_libre(ids_usados: set[str]) -> str:
    """Calcula el menor ``F##`` no presente en ``ids_usados`` (F01..F99).

    Recorre los números del 1 al 99 y devuelve el primero cuyo ID formateado
    (``f"F{n:02d}"``) no esté ya en uso. Garantiza unicidad y soporta hasta 99
    fuentes (Req 5.1). Los IDs liberados no se reutilizan dentro de una misma
    pasada porque el conjunto ``ids_usados`` debe actualizarse por el llamador
    tras cada asignación.

    Args:
        ids_usados: conjunto de ID_Fuente ya ocupados (``F01``..``F99``).

    Returns:
        El menor ID_Fuente libre con formato ``F##``.

    Raises:
        ValueError: si ya se agotaron los 99 identificadores posibles.
    """
    for numero in range(PRIMER_ID, ULTIMO_ID + 1):
        candidato = f"F{numero:02d}"
        if candidato not in ids_usados:
            return candidato

    raise ValueError(
        "No quedan ID_Fuente libres: se agotó el rango F01..F99 (99 fuentes)."
    )


def asigna_ids(catalogo: list[dict], ids_previos: dict) -> list[dict]:
    """Asigna un ``id_fuente`` estable a cada entrada del catálogo.

    Para cada entrada reutiliza el ID previo cuando su clave lógica ya existe en
    ``ids_previos`` (conservación carácter a carácter entre ejecuciones, Req
    5.2); para las claves nuevas asigna el siguiente ``F##`` libre con
    ``siguiente_id_libre`` (Req 5.1). Los IDs ya en uso —tanto los heredados
    como los recién asignados— se acumulan en el conjunto de ocupados, de modo
    que un ID liberado en el pasado no se reutiliza para una fuente distinta.

    No muta las entradas originales: devuelve copias con la clave ``id_fuente``
    añadida.

    Args:
        catalogo: lista de entradas (dicts) del inventario a identificar.
        ids_previos: mapa ``clave -> id_fuente`` de ejecuciones anteriores.

    Returns:
        Nueva lista de entradas, cada una con su ``id_fuente`` asignado.
    """
    # IDs ocupados = todos los previamente asignados (aunque su fuente ya no
    # esté en el catálogo), para no reutilizar IDs liberados (Req 5.1).
    ids_usados: set[str] = {
        str(id_fuente).strip()
        for id_fuente in ids_previos.values()
        if str(id_fuente).strip()
    }

    resultado: list[dict] = []
    for registro in catalogo:
        entrada = dict(registro)
        clave = clave_fuente(entrada)

        if clave in ids_previos and str(ids_previos[clave]).strip():
            # Fuente ya inventariada: se conserva su ID exacto (Req 5.2).
            entrada["id_fuente"] = str(ids_previos[clave]).strip()
        else:
            # Fuente nueva: se asigna el siguiente F## libre (Req 5.1).
            nuevo_id = siguiente_id_libre(ids_usados)
            entrada["id_fuente"] = nuevo_id
            ids_usados.add(nuevo_id)

        resultado.append(entrada)

    return resultado


def construye_inventario(
    fecha_prueba: str, ids_previos: dict | None = None
) -> list[dict]:
    """Devuelve el catálogo declarativo de datasets del proyecto (Parte 3).

    Extiende el catálogo de la Parte 2 (población, vivienda, turismo,
    inversiones, excluidos y candidatos) con las cuatro fuentes nuevas de la
    Parte 3 —desgloses de población (``poblacion_desgloses.csv``), umbrales de
    pobreza (``umbrales_pobreza.csv``, reclasificado desde ``oficial_820``),
    tasa de fecundidad (``tasa_fecundidad.csv``, reclasificado desde
    ``oficial_810``) y economía del Banco Mundial
    (``economia_worldbank.csv``)— como ``integrado`` con linaje OBSERVADO. Las
    dos entradas ``oficial_820``/``oficial_810`` se conservan ``excluido`` pero
    su ``motivo`` apunta ahora a su reclasificación, manteniendo su
    ``id_fuente`` (la clave lógica es el ``nombre``, que no cambia). Cada
    entrada lleva además la columna ``licencia`` con el texto de licencia
    literal de la fuente (World Bank ``CC BY 4.0``; Estadística Andorra; OSM
    ``ODbL``) (Req 4.9, 8.4, 8.5). Cada entrada ``integrado`` lleva ``nombre``,
    ``fuente``, ``vigencia``, ``fecha_prueba``, ``linaje`` y ``estado`` no
    vacíos (Req 5.3).

    Antes de devolver el catálogo, cada registro se valida: su ``linaje`` debe
    pertenecer a ``gobernanza.LINAJES_VALIDOS`` y su ``estado`` a
    ``gobernanza.ESTADOS_VALIDOS``. Cualquier dataset con linaje inválido (o con
    estado no clasificable en los cuatro válidos) se omite del inventario y se
    registra en la bitácora, en español, indicando su ``id_fuente`` y el motivo
    del rechazo (Req 4.7, 5.4). Para poder reportar el ``id_fuente`` de las
    entradas rechazadas, los IDs se asignan sobre el catálogo completo antes de
    filtrar.

    Args:
        fecha_prueba: fecha (ISO) de verificación/generación del inventario.
            Se usa como ``fecha_prueba`` de las entradas integradas (Req 5.3).
        ids_previos: mapa ``clave -> id_fuente`` de ejecuciones anteriores para
            conservar los IDs estables (Req 5.2). Si es ``None``, se cargan del
            inventario previo con ``carga_ids_existentes``.

    Returns:
        Lista de registros (dicts) válidos que componen el Inventario_Fuentes,
        cada uno ya con su ``id_fuente`` estable asignado.
    """
    # Catálogo declarativo: un registro por dataset catalogado (Req 4.1).
    # Las entradas 'integrado' llevan vigencia y fecha_prueba no vacíos (Req 5.3).
    catalogo = [
        # --- Integrados v1: población por parròquia y precios de vivienda ---
        {
            "nombre": "estadistica_id798_població_població_per_parròquia.csv",
            "fuente": FUENTE_ESTADISTICA,
            "vigencia": "2024",
            "fecha_prueba": fecha_prueba,
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "integrado",
            "motivo": "",
            "licencia": LICENCIA_ESTADISTICA,
        },
        {
            "nombre": "precios_vivienda_indomio.csv",
            "fuente": FUENTE_INDOMIO,
            "vigencia": "2025",
            "fecha_prueba": fecha_prueba,
            "linaje": gobernanza.LINAJE_PROXY,
            "estado": "integrado",
            "motivo": "",
            "licencia": LICENCIA_INDOMIO,
        },
        # --- Integrados Parte 2: turismo e inversiones (OBSERVADO) ----------
        {
            "nombre": "turismo.csv",
            "fuente": FUENTE_TURISMO,
            "vigencia": VIGENCIA_TURISMO,
            "fecha_prueba": fecha_prueba,
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "integrado",
            "motivo": "",
            "licencia": LICENCIA_ESTADISTICA,
        },
        {
            "nombre": "inversiones_inmobiliarias.csv",
            "fuente": FUENTE_INVERSIONES,
            "vigencia": VIGENCIA_INVERSIONES,
            "fecha_prueba": fecha_prueba,
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "integrado",
            "motivo": "",
            "licencia": LICENCIA_ESTADISTICA,
        },
        # --- Integrados Parte 3: desgloses, sociales y economía (OBSERVADO) -
        {
            "nombre": "poblacion_desgloses.csv",
            "fuente": FUENTE_ESTADISTICA,
            "vigencia": VIGENCIA_DESGLOSES,
            "fecha_prueba": fecha_prueba,
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "integrado",
            "motivo": "",
            "licencia": LICENCIA_ESTADISTICA,
        },
        {
            "nombre": "umbrales_pobreza.csv",
            "fuente": FUENTE_ESTADISTICA,
            "vigencia": VIGENCIA_SOCIALES,
            "fecha_prueba": fecha_prueba,
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "integrado",
            "motivo": (
                "Reclasificado desde oficial_820 (contenido real: umbrales "
                "de pobreza)"
            ),
            "licencia": LICENCIA_ESTADISTICA,
        },
        {
            "nombre": "tasa_fecundidad.csv",
            "fuente": FUENTE_ESTADISTICA,
            "vigencia": VIGENCIA_SOCIALES,
            "fecha_prueba": fecha_prueba,
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "integrado",
            "motivo": (
                "Reclasificado desde oficial_810 (contenido real: tasa de "
                "fecundidad)"
            ),
            "licencia": LICENCIA_ESTADISTICA,
        },
        {
            "nombre": "economia_worldbank.csv",
            "fuente": FUENTE_WORLDBANK,
            "vigencia": VIGENCIA_WORLDBANK,
            "fecha_prueba": fecha_prueba,
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "integrado",
            "motivo": "",
            "licencia": LICENCIA_WORLDBANK,
        },
        # --- Reclasificados: crudos mal etiquetados (contenido real) --------
        # Se conserva el id_fuente (la clave lógica es el 'nombre', que no
        # cambia) y se anota el motivo apuntando a su reclasificación (Req 8.2).
        {
            "nombre": "oficial_820_transacciones_inmobiliarias.csv",
            "fuente": FUENTE_ESTADISTICA,
            "vigencia": "",
            "fecha_prueba": "",
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "excluido",
            "motivo": (
                "El contenido no coincide con el nombre del archivo: "
                "reclasificado como umbrales de pobreza en umbrales_pobreza.csv"
            ),
            "licencia": LICENCIA_ESTADISTICA,
        },
        {
            "nombre": "oficial_810_indicadores_economicos.csv",
            "fuente": FUENTE_ESTADISTICA,
            "vigencia": "",
            "fecha_prueba": "",
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "excluido",
            "motivo": (
                "El contenido no coincide con el nombre del archivo: "
                "reclasificado como tasa de fecundidad en tasa_fecundidad.csv"
            ),
            "licencia": LICENCIA_ESTADISTICA,
        },
        # --- Candidatos: catalogados pero no procesados todavía -------------
        {
            "nombre": "estadistica_id1091..1138 (edad/sexo/nacionalidad)",
            "fuente": FUENTE_ESTADISTICA,
            "vigencia": "",
            "fecha_prueba": "",
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "candidato",
            "motivo": "Catalogado pero no procesado todavía",
            "licencia": LICENCIA_ESTADISTICA,
        },
        {
            "nombre": "edificios_andorra.geojson",
            "fuente": FUENTE_OSM,
            "vigencia": "",
            "fecha_prueba": "",
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "candidato",
            "motivo": "Capa de detalle urbano fuera de alcance de la Parte 2",
            "licencia": LICENCIA_OSM,
        },
        {
            "nombre": "parroquias_andorra.geojson",
            "fuente": FUENTE_OSM,
            "vigencia": "",
            "fecha_prueba": "",
            "linaje": gobernanza.LINAJE_OBSERVADO,
            "estado": "candidato",
            "motivo": "Límites de las 7 parròquies para la Vista_Mapa",
            "licencia": LICENCIA_OSM,
        },
    ]

    # Los IDs se asignan sobre el catálogo COMPLETO (antes de validar) para
    # poder reportar el id_fuente de las entradas que se rechacen (Req 5.4).
    if ids_previos is None:
        ids_previos = carga_ids_existentes(RUTA_SALIDA_INVENTARIO)
    catalogo = asigna_ids(catalogo, ids_previos)

    inventario: list[dict] = []
    for indice, registro in enumerate(catalogo):
        id_fuente = registro.get("id_fuente", f"#{indice}")
        nombre = registro.get("nombre", f"#{indice}")
        linaje = registro.get("linaje")
        estado = registro.get("estado")

        # El linaje debe ser una etiqueta válida (OBSERVADO/ESTIMADO/PROXY).
        if linaje not in gobernanza.LINAJES_VALIDOS:
            print(
                f"[inventario] Fuente '{id_fuente}' ('{nombre}') omitida del "
                f"inventario: la etiqueta de linaje '{linaje}' no es válida "
                "(debe ser OBSERVADO, ESTIMADO o PROXY)."
            )
            continue

        # El estado debe ser uno de los cuatro estados válidos (Req 4.7).
        if estado not in gobernanza.ESTADOS_VALIDOS:
            print(
                f"[inventario] Fuente '{id_fuente}' ('{nombre}') omitida del "
                f"inventario: el estado '{estado}' no es clasificable en los "
                "cuatro estados válidos (integrado, candidato, caído, excluido)."
            )
            continue

        inventario.append(registro)

    print(
        f"[inventario] Catálogo construido: {len(inventario)} dataset(s) "
        f"clasificado(s) de {len(catalogo)} candidato(s)."
    )
    return inventario


def procesa(fecha_prueba: str) -> None:
    """Construye el inventario con IDs estables y lo escribe en procesados/.

    Orquesta la generación del Inventario_Fuentes extendido: carga los IDs
    previos del inventario existente con ``carga_ids_existentes`` (para
    conservarlos carácter a carácter, Req 5.2), construye el catálogo con
    ``construye_inventario`` asignando los ``id_fuente`` estables con
    ``asigna_ids`` (Req 5.1), y escribe
    ``../datos_procesados/inventario_fuentes.csv`` con las columnas extendidas
    (``COLUMNAS_INVENTARIO``) mediante ``gobernanza.escribe_csv`` (separador
    ``;``, UTF-8, creación idempotente del directorio y rechazo de escritura en
    ``datos_crudos/``) (Req 5.3).

    Args:
        fecha_prueba: fecha (ISO) de verificación/generación del inventario.
    """
    # Cargar los IDs previos para conservarlos estables entre ejecuciones.
    ids_previos = carga_ids_existentes(RUTA_SALIDA_INVENTARIO)
    inventario = construye_inventario(fecha_prueba, ids_previos)
    gobernanza.escribe_csv(inventario, RUTA_SALIDA_INVENTARIO, COLUMNAS_INVENTARIO)
    print(
        f"[inventario] Inventario de fuentes escrito en "
        f"'{RUTA_SALIDA_INVENTARIO}' con {len(inventario)} fuente(s) y "
        "ID_Fuente estable."
    )


if __name__ == "__main__":
    import datetime

    # Fecha de prueba por defecto: hoy en formato ISO.
    procesa(datetime.date.today().isoformat())
