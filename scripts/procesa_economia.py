"""Procesamiento de economía World Bank (tramo Lago).

Este módulo lee los JSON crudos de la API v2 del Banco Mundial (World Bank Open
Data) descargados por ``descarga_worldbank.py`` en ``datos_crudos/`` (archivos
``worldbank_<codigo>.json``), los normaliza a tabla larga (un registro por
indicador y año), les anota la gobernanza (linaje OBSERVADO) y escribe el
resultado en ``datos_procesados/economia_worldbank.csv``.

La API v2 devuelve, por indicador, un array JSON de dos elementos:
``[metadata, observaciones]``. Cada observación tiene al menos ``date`` (año) y
``value`` (cifra o ``null``). Las observaciones con ``value`` nulo se **omiten**
(no se inventan datos, Req 4.5, 4.6).

Sub-tarea 3.1: lectura del JSON por indicador y normalización a tabla larga.

Reutiliza ``gobernanza.py`` tal cual e imita el estilo de los demás
procesadores (``procesa_poblacion.py``). Los mensajes de consola van en
español, coherentes con el resto del proyecto. Nunca escribe en
``datos_crudos/``.
"""

import datetime
import json
import os

import gobernanza

# --- Dependencia tolerante de descarga_worldbank.INDICADORES ---------------
# El extractor de red ``descarga_worldbank.py`` (tarea 5.1) es opcional y puede
# no existir todavía. Se importa de forma tolerante; si no está disponible, se
# usa un diccionario local equivalente como fallback (mismo contenido que el
# definido en el design.md para ``descarga_worldbank.INDICADORES``). Cada
# entrada mapea el código del indicador a una tupla ``(nombre, unidad)``.
_INDICADORES_FALLBACK = {
    "NY.GDP.MKTP.CD": ("PIB (US$ corrientes)", "US$"),
    "FP.CPI.TOTL.ZG": ("Inflación, IPC", "% anual"),
    "NY.GDP.PCAP.CD": ("PIB per cápita", "US$"),
    "SP.POP.TOTL": ("Población total", "personas"),
}

try:
    import descarga_worldbank  # type: ignore

    INDICADORES = descarga_worldbank.INDICADORES
except Exception:
    # El extractor de red aún no existe o no pudo importarse; se usa el
    # diccionario local como fuente de nombres y unidades de los indicadores.
    print(
        "[AVISO] No se pudo importar 'descarga_worldbank'; se usan los nombres "
        "y unidades de indicadores definidos localmente como respaldo."
    )
    INDICADORES = _INDICADORES_FALLBACK

# Ruta de salida del CSV procesado, relativa a scripts/.
RUTA_SALIDA = "../datos_procesados/economia_worldbank.csv"

# Fuente oficial del dato económico (linaje OBSERVADO) y su licencia literal.
FUENTE_WB = "Banco Mundial (World Bank Open Data, API v2)"
LICENCIA_WB = "CC BY 4.0"

# Columnas de la tabla procesada economia_worldbank.csv, en orden (design.md).
COLUMNAS_SALIDA = [
    "indicador",
    "codigo",
    "anio",
    "valor",
    "unidad",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def _ruta_crudo(codigo: str) -> str:
    """Devuelve la ruta del JSON crudo de un indicador, relativa a scripts/.

    Args:
        codigo: código del indicador World Bank (p. ej. ``NY.GDP.MKTP.CD``).

    Returns:
        Ruta ``../datos_crudos/worldbank_<codigo>.json``.
    """
    return f"../datos_crudos/worldbank_{codigo}.json"


def lee_json_indicador(codigo: str) -> "list | None":
    """Lee ``worldbank_<codigo>.json`` y devuelve la lista de observaciones.

    La API v2 del Banco Mundial devuelve, por indicador, un array JSON de dos
    elementos ``[metadata, observaciones]``. Esta función devuelve el **segundo**
    elemento (la lista de observaciones).

    Devuelve ``None`` —registrando la causa en español por consola— si el
    archivo no existe, no puede leerse o parsearse, o su estructura no es la
    esperada (no es un array de al menos dos elementos, o el segundo elemento no
    es una lista). Nunca modifica el crudo.

    Args:
        codigo: código del indicador World Bank (p. ej. ``NY.GDP.MKTP.CD``).

    Returns:
        La lista de observaciones (2º elemento del array) o ``None`` si falta,
        es ilegible o la estructura es inesperada.
    """
    ruta = _ruta_crudo(codigo)

    if not os.path.exists(ruta):
        print(
            f"[AVISO] No se encontró el JSON del indicador '{codigo}': "
            f"'{ruta}'. Se omite este indicador."
        )
        return None

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = json.load(archivo)
    except Exception as error:
        print(
            f"[ERROR] No se pudo leer o parsear el JSON del indicador "
            f"'{codigo}' ('{ruta}'): {error}. Se omite este indicador."
        )
        return None

    # La estructura esperada es un array de dos elementos [metadata, obs].
    if not isinstance(contenido, list) or len(contenido) < 2:
        print(
            f"[ERROR] El JSON del indicador '{codigo}' ('{ruta}') no tiene la "
            "estructura esperada (array de dos elementos). Se omite este "
            "indicador."
        )
        return None

    observaciones = contenido[1]
    if not isinstance(observaciones, list):
        print(
            f"[ERROR] El segundo elemento del JSON del indicador '{codigo}' "
            f"('{ruta}') no es una lista de observaciones. Se omite este "
            "indicador."
        )
        return None

    print(
        f"[OK] JSON del indicador '{codigo}' leído: {len(observaciones)} "
        "observación(es) encontradas."
    )
    return observaciones


def normaliza_indicador(
    observaciones: list, codigo: str, fecha_prueba: str
) -> list[dict]:
    """Normaliza las observaciones de un indicador a filas de tabla larga.

    Produce una fila por observación con ``value`` **no nulo**: las
    observaciones cuyo ``value`` es ``null``/``None`` se **omiten** (no se
    inventan datos, Req 4.5, 4.6) y se registran por consola en español. Para
    cada fila emitida se toman ``indicador`` y ``unidad`` de ``INDICADORES`` (de
    ``descarga_worldbank`` o del respaldo local), se usa el año de la
    observación como ``anio`` y como ``vigencia``, y se anota la gobernanza con
    ``fuente=FUENTE_WB``, la ``fecha_prueba`` recibida y ``linaje`` OBSERVADO.

    Las observaciones sin año legible, o con un año no numérico, se omiten y se
    registran. Si el código no está en ``INDICADORES``, el ``indicador`` y la
    ``unidad`` quedan como cadena vacía (el registro podrá excluirlo la
    gobernanza aguas abajo si procede).

    Args:
        observaciones: lista de observaciones (2º elemento del array de la API).
        codigo: código del indicador World Bank (p. ej. ``NY.GDP.MKTP.CD``).
        fecha_prueba: fecha (ISO ``AAAA-MM-DD``) en que se verificó el dato.

    Returns:
        Lista de diccionarios, uno por observación válida, con las claves de
        ``COLUMNAS_SALIDA``.
    """
    if not isinstance(observaciones, list):
        print(
            f"[ERROR] Las observaciones del indicador '{codigo}' no son una "
            "lista; no se puede normalizar. Se devuelve lista vacía."
        )
        return []

    # Nombre y unidad del indicador según el diccionario de indicadores.
    nombre, unidad = INDICADORES.get(codigo, ("", ""))
    if codigo not in INDICADORES:
        print(
            f"[AVISO] El código '{codigo}' no está en INDICADORES; su nombre y "
            "unidad quedarán vacíos."
        )

    registros: list[dict] = []
    omitidas_nulas = 0

    for indice, observacion in enumerate(observaciones):
        if not isinstance(observacion, dict):
            print(
                f"[ERROR] Observación #{indice} del indicador '{codigo}' no es "
                "un objeto válido. Se omite."
            )
            continue

        valor = observacion.get("value")
        # Las observaciones con value nulo se OMITEN (no se inventan datos).
        if valor is None:
            omitidas_nulas += 1
            continue

        # El año viene en 'date' como texto; debe ser un entero.
        texto_anio = str(observacion.get("date", "")).strip()
        if texto_anio == "":
            print(
                f"[ERROR] Observación #{indice} del indicador '{codigo}' sin "
                "año ('date'). Se omite."
            )
            continue
        try:
            anio = int(texto_anio)
        except (ValueError, TypeError):
            print(
                f"[ERROR] Observación #{indice} del indicador '{codigo}' con "
                f"año no numérico ('{texto_anio}'). Se omite."
            )
            continue

        registros.append(
            {
                "indicador": nombre,
                "codigo": codigo,
                "anio": anio,
                "valor": valor,
                "unidad": unidad,
                "fuente": FUENTE_WB,
                "vigencia": str(anio),
                "fecha_prueba": fecha_prueba,
                "linaje": gobernanza.LINAJE_OBSERVADO,
            }
        )

    if omitidas_nulas:
        print(
            f"[AVISO] Indicador '{codigo}': se omitieron {omitidas_nulas} "
            "observación(es) con valor nulo (no se inventan datos)."
        )
    print(
        f"[OK] Indicador '{codigo}' normalizado: {len(registros)} registro(s) "
        "con valor no nulo."
    )
    return registros


def procesa(fecha_prueba: str) -> None:
    """Orquesta el procesamiento de economía World Bank, tolerante a ausencia.

    Recorre los indicadores definidos en ``INDICADORES`` y, para cada código,
    intenta leer su JSON crudo (``worldbank_<codigo>.json``) con
    :func:`lee_json_indicador`. Los indicadores cuyo JSON falta, es ilegible o
    tiene una estructura inesperada se **omiten** (``lee_json_indicador``
    devuelve ``None``), sin detener el procesamiento del resto. Las
    observaciones de los JSON presentes se normalizan con
    :func:`normaliza_indicador` y se concatenan en una sola tabla larga.

    La colección resultante se filtra con
    ``gobernanza.filtra_registros_validos`` y se escribe en ``RUTA_SALIDA`` con
    ``gobernanza.escribe_csv`` (separador ``;``, UTF-8). Si no hay ningún JSON
    presente (o ninguna observación válida), se escribe igualmente el CSV con
    **solo la cabecera** (``COLUMNAS_SALIDA``), de modo que la vista de economía
    pueda mostrar la ausencia de fuente económica real sin inventar datos
    (Req 4.6, 5.3).

    Las rutas son relativas a ``scripts/``, según la convención del
    repositorio; nunca se escribe ni se modifica nada en ``datos_crudos/``.

    Args:
        fecha_prueba: fecha (ISO ``AAAA-MM-DD``) en que se verificó el dato.
    """
    print("[INICIO] Procesamiento de economía (World Bank).")

    registros: list[dict] = []
    indicadores_presentes = 0

    # 1) Recorrer los indicadores conocidos; omitir los JSON ausentes/ilegibles.
    for codigo in INDICADORES:
        observaciones = lee_json_indicador(codigo)
        if observaciones is None:
            # Ausencia tolerada: el extractor de red es opcional (fuera del
            # pipeline). Se omite este indicador y se continúa con los demás.
            continue

        indicadores_presentes += 1
        registros.extend(
            normaliza_indicador(observaciones, codigo, fecha_prueba)
        )

    if indicadores_presentes == 0:
        print(
            "[AVISO] No se encontró ningún JSON de World Bank en "
            "'datos_crudos/'. Se escribirá la tabla de economía vacía (solo "
            "cabecera); la vista mostrará la ausencia de fuente económica real."
        )

    # 2) Filtrado de registros con gobernanza completa (linaje OBSERVADO).
    registros_validos = gobernanza.filtra_registros_validos(
        registros, "economia"
    )

    # 3) Escritura segura en datos_procesados/. Con lista vacía,
    #    gobernanza.escribe_csv escribe solo la cabecera (Req 4.6, 5.3).
    gobernanza.escribe_csv(registros_validos, RUTA_SALIDA, COLUMNAS_SALIDA)

    print(
        f"[FIN] Procesamiento de economía completado: "
        f"{len(registros_validos)} registro(s) escritos en '{RUTA_SALIDA}' "
        f"({indicadores_presentes} indicador(es) presentes)."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
