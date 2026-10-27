"""Reclasificación de los dos crudos oficiales mal etiquetados (tramo Lago).

Dos crudos del Departament d'Estadística d'Andorra llevan un nombre de archivo
que no corresponde con su contenido real:

- ``oficial_820_transacciones_inmobiliarias.csv`` **no** contiene transacciones
  inmobiliarias: contiene los tres umbrales de pobreza e ingresos (llindar de
  risc de pobresa, de pobresa y de pobresa severa), con importes en euros y
  coma decimal catalana. Se reclasifica como "Umbrales de pobreza e ingresos"
  → ``umbrales_pobreza.csv``.
- ``oficial_810_indicadores_economicos.csv`` **no** contiene indicadores
  económicos: contiene una única fila de tasa de fecundidad (TAXA DE
  FECUNDITAT) con valor decimal. Se reclasifica como "Tasa de fecundidad"
  → ``tasa_fecundidad.csv``.

Este módulo los lee según su contenido real, convierte la coma decimal catalana
a punto, les anota la gobernanza (linaje OBSERVADO) y escribe cada indicador en
``datos_procesados/``. Los crudos originales nunca se modifican ni se eliminan:
son la fuente de verdad del proyecto (Req 3.6, 3.7).

Sub-tarea 2.1: conversión de la coma decimal y normalización de los dos
indicadores. Los mensajes de consola van en español, coherentes con el resto
del proyecto.
"""

import datetime

import pandas as pd

import gobernanza

# --- Rutas de entrada (crudos mal etiquetados) y salida --------------------
# Relativas a scripts/, según la convención del repositorio.
RUTA_POBREZA = "../datos_crudos/oficial_820_transacciones_inmobiliarias.csv"
RUTA_FECUNDIDAD = "../datos_crudos/oficial_810_indicadores_economicos.csv"
RUTA_SALIDA_POBREZA = "../datos_procesados/umbrales_pobreza.csv"
RUTA_SALIDA_FECUNDIDAD = "../datos_procesados/tasa_fecundidad.csv"

# Fuente oficial común de ambos indicadores (linaje OBSERVADO).
FUENTE_SOCIAL = "Departament d'Estadística d'Andorra"

# Rango de años esperado en las columnas de los crudos (Req 3.1, 3.2).
ANIOS_ESPERADOS = [2020, 2021, 2022, 2023, 2024, 2025]

# Nombre canónico del indicador de fecundidad en el lago (contenido real).
INDICADOR_FECUNDIDAD = "Tasa de fecundidad"

# Texto que debe aparecer en la fila del crudo de fecundidad para confirmar que
# su contenido real es la tasa de fecundidad y no indicadores económicos.
MARCADOR_FECUNDIDAD = "FECUNDITAT"

# Reglas de reconocimiento de cada umbral de pobreza a partir del texto de la
# columna 'Descripció'. Se empareja por contenido (no por 'Codi') para no
# depender del tipo con que se lea el código: el 'Codi' empieza por cero y
# algunos lectores de CSV lo interpretan como entero, perdiendo ese cero
# inicial. Cada entrada define las palabras clave (en mayúsculas) que deben
# aparecer en la descripción y el nombre canónico del Indicador_Social_
# Reclasificado, nombrado por su significado real y no por el nombre engañoso
# del archivo ("transacciones inmobiliarias").
REGLAS_UMBRALES_POBREZA = [
    (("RISC DE POBRESA",), "LLINDAR DE RISC DE POBRESA (60%)"),
    (("POBRESA SEVERA",), "LLINDAR DE POBRESA SEVERA (40%)"),
    (("POBRESA",), "LLINDAR DE POBRESA (50%)"),
]


def _clasifica_umbral_pobreza(descripcion: str) -> "str | None":
    """Devuelve el nombre canónico del umbral de pobreza, o ``None``.

    Empareja el texto de 'Descripció' con las palabras clave de
    ``REGLAS_UMBRALES_POBREZA``. El orden de las reglas importa: "POBRESA
    SEVERA" se comprueba antes que "POBRESA" para no confundir el umbral severo
    con el general.

    Args:
        descripcion: valor de la columna 'Descripció' de una fila.

    Returns:
        El nombre canónico del umbral o ``None`` si no se reconoce.
    """
    texto = str(descripcion).upper()
    for claves, nombre in REGLAS_UMBRALES_POBREZA:
        if all(clave in texto for clave in claves):
            return nombre
    return None

# Columnas de salida de cada indicador reclasificado, en orden (design.md).
COLUMNAS_POBREZA = [
    "indicador",
    "anio",
    "valor_eur",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]
COLUMNAS_FECUNDIDAD = [
    "indicador",
    "anio",
    "valor",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def _a_decimal(valor) -> "float | None":
    """Convierte un valor con coma decimal catalana a ``float``.

    Transforma el separador decimal de coma a punto (``'12153,39'`` ->
    ``12153.39``). Devuelve ``None`` si el valor está vacío, ausente o no es
    numérico, para que la celda afectada pueda excluirse y registrarse sin
    inventar datos (Req 3.1, 3.2).

    Args:
        valor: valor crudo de la celda (texto, número o ausente).

    Returns:
        El importe como ``float`` o ``None`` si no es un número válido.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    if texto == "":
        return None
    # La coma catalana es el separador decimal; se normaliza a punto.
    texto = texto.replace(",", ".")
    try:
        return float(texto)
    except (ValueError, TypeError):
        return None


def _columna_del_anio(df: pd.DataFrame, anio: int):
    """Localiza la clave de la columna de un año, sea de tipo ``str`` o ``int``.

    Args:
        df: DataFrame leído del crudo.
        anio: año buscado (entero).

    Returns:
        La clave de columna presente en el DataFrame, o ``None`` si falta.
    """
    if str(anio) in df.columns:
        return str(anio)
    if anio in df.columns:
        return anio
    return None


def normaliza_pobreza(df: pd.DataFrame, fecha_prueba: str) -> list[dict]:
    """Normaliza el crudo de umbrales de pobreza a formato largo gobernado.

    Produce un registro por cada combinación de (umbral de pobreza, año), con
    las claves ``indicador`` (nombre canónico del umbral), ``anio`` (entero),
    ``valor_eur`` (importe decimal con la coma catalana convertida a punto) y
    los metadatos de gobernanza (``fuente``, ``vigencia``, ``fecha_prueba`` y
    ``linaje`` = OBSERVADO). Conserva únicamente los años dentro de
    ``ANIOS_ESPERADOS`` (2020–2025) (Req 3.1, 3.3).

    Si el contenido del crudo no casa lo esperado (faltan columnas clave o
    ninguna fila corresponde a un umbral de pobreza conocido), no muta el
    archivo original y registra por consola en español la discrepancia
    detectada, devolviendo una lista vacía (Req 3.6, 3.7).

    Args:
        df: DataFrame leído del Crudo_MalEtiquetado_Pobreza (columnas Codi,
            Descripció, 2020..2025).
        fecha_prueba: fecha (ISO ``AAAA-MM-DD``) en que se verificó el dato.

    Returns:
        Lista de registros (dicts) de umbrales de pobreza gobernados.
    """
    if df is None or "Descripció" not in df.columns:
        print(
            "[DISCREPANCIA] El crudo de umbrales de pobreza no tiene la columna "
            "esperada ('Descripció'). No se reclasifica y el archivo original "
            "queda intacto."
        )
        return []

    registros: list[dict] = []
    umbrales_reconocidos = 0

    for indice, fila in df.iterrows():
        descripcion = str(fila.get("Descripció", "")).strip()
        indicador = _clasifica_umbral_pobreza(descripcion)
        if indicador is None:
            # Fila que no corresponde a un umbral de pobreza conocido: se
            # registra la discrepancia sin tocar el crudo (Req 3.6).
            print(
                f"[DISCREPANCIA] Fila {indice}: la descripción "
                f"('{descripcion}') no corresponde a un umbral de pobreza "
                f"conocido. Se omite esa fila."
            )
            continue

        umbrales_reconocidos += 1

        for anio in ANIOS_ESPERADOS:
            clave = _columna_del_anio(df, anio)
            if clave is None:
                print(
                    f"[AVISO] Falta la columna del año {anio} en el crudo de "
                    f"umbrales de pobreza; se omite ese registro de "
                    f"'{indicador}'."
                )
                continue

            valor_eur = _a_decimal(fila[clave])
            if valor_eur is None:
                print(
                    f"[DISCREPANCIA] '{indicador}' año {anio}: importe inválido "
                    f"('{fila[clave]}'). Se excluye ese registro."
                )
                continue

            registros.append(
                {
                    "indicador": indicador,
                    "anio": int(anio),
                    "valor_eur": valor_eur,
                    "fuente": FUENTE_SOCIAL,
                    "vigencia": str(int(anio)),
                    "fecha_prueba": fecha_prueba,
                    "linaje": gobernanza.LINAJE_OBSERVADO,
                }
            )

    if umbrales_reconocidos == 0:
        print(
            "[DISCREPANCIA] El crudo de umbrales de pobreza no contiene ninguna "
            "fila de umbral reconocida; el contenido no casa lo esperado. El "
            "archivo original queda intacto."
        )
        return []

    print(
        f"[OK] Umbrales de pobreza reclasificados: {len(registros)} registro(s) "
        f"de {umbrales_reconocidos} umbral(es), linaje OBSERVADO."
    )
    return registros


def normaliza_fecundidad(df: pd.DataFrame, fecha_prueba: str) -> list[dict]:
    """Normaliza el crudo de tasa de fecundidad a formato largo gobernado.

    Produce un registro por cada año, con las claves ``indicador`` (siempre
    ``'Tasa de fecundidad'``), ``anio`` (entero), ``valor`` (tasa decimal con la
    coma catalana convertida a punto) y los metadatos de gobernanza (``fuente``,
    ``vigencia``, ``fecha_prueba`` y ``linaje`` = OBSERVADO). Conserva
    únicamente los años dentro de ``ANIOS_ESPERADOS`` (2020–2025) (Req 3.2,
    3.3).

    Si el contenido no casa lo esperado (faltan columnas clave o ninguna fila
    corresponde a la tasa de fecundidad), no muta el archivo original y registra
    por consola en español la discrepancia detectada, devolviendo una lista
    vacía (Req 3.6, 3.7).

    Args:
        df: DataFrame leído del Crudo_MalEtiquetado_Fecundidad (columnas Codi,
            Descripció, 2020..2025).
        fecha_prueba: fecha (ISO ``AAAA-MM-DD``) en que se verificó el dato.

    Returns:
        Lista de registros (dicts) de tasa de fecundidad gobernados.
    """
    if df is None or "Descripció" not in df.columns:
        print(
            "[DISCREPANCIA] El crudo de tasa de fecundidad no tiene la columna "
            "esperada ('Descripció'). No se reclasifica y el archivo original "
            "queda intacto."
        )
        return []

    # Localiza la fila cuyo contenido real es la tasa de fecundidad.
    fila_fecundidad = None
    for _, fila in df.iterrows():
        descripcion = str(fila.get("Descripció", "")).upper()
        if MARCADOR_FECUNDIDAD in descripcion:
            fila_fecundidad = fila
            break

    if fila_fecundidad is None:
        print(
            "[DISCREPANCIA] El crudo de tasa de fecundidad no contiene ninguna "
            "fila de fecundidad (TAXA DE FECUNDITAT); el contenido no casa lo "
            "esperado. El archivo original queda intacto."
        )
        return []

    registros: list[dict] = []

    for anio in ANIOS_ESPERADOS:
        clave = _columna_del_anio(df, anio)
        if clave is None:
            print(
                f"[AVISO] Falta la columna del año {anio} en el crudo de tasa "
                f"de fecundidad; se omite ese registro."
            )
            continue

        valor = _a_decimal(fila_fecundidad[clave])
        if valor is None:
            print(
                f"[DISCREPANCIA] Tasa de fecundidad año {anio}: valor inválido "
                f"('{fila_fecundidad[clave]}'). Se excluye ese registro."
            )
            continue

        registros.append(
            {
                "indicador": INDICADOR_FECUNDIDAD,
                "anio": int(anio),
                "valor": valor,
                "fuente": FUENTE_SOCIAL,
                "vigencia": str(int(anio)),
                "fecha_prueba": fecha_prueba,
                "linaje": gobernanza.LINAJE_OBSERVADO,
            }
        )

    print(
        f"[OK] Tasa de fecundidad reclasificada: {len(registros)} registro(s), "
        f"linaje OBSERVADO."
    )
    return registros


def _procesa_indicador(
    ruta_entrada: str,
    ruta_salida: str,
    normalizador,
    columnas: list[str],
    contexto: str,
    fecha_prueba: str,
) -> None:
    """Procesa un indicador social de extremo a extremo, de forma aislada.

    Lee el crudo según su contenido real, lo normaliza con ``normalizador``,
    filtra los registros con gobernanza completa y escribe el CSV de salida.
    Cualquier fallo (lectura ilegible del crudo, contenido que no casa) se
    captura y registra en español sin propagarse, de modo que el fallo de un
    indicador no impida el procesamiento del otro (Req 3.3, 3.4). Nunca modifica
    ni elimina los crudos: sólo los lee (Req 3.7).

    Args:
        ruta_entrada: ruta del crudo mal etiquetado a leer.
        ruta_salida: ruta del CSV reclasificado a escribir en procesados/.
        normalizador: función ``normaliza_*`` que produce la lista de registros.
        columnas: columnas de salida en orden para el CSV.
        contexto: etiqueta corta del indicador para la bitácora de gobernanza.
        fecha_prueba: fecha (ISO ``AAAA-MM-DD``) en que se verificó el dato.
    """
    print(f"[INICIO] Reclasificación de '{contexto}'.")

    # 1) Lectura del crudo. El fallo de uno no debe detener el otro (Req 3.4):
    #    se captura aquí y no se propaga. Sólo se lee; nunca se escribe sobre el
    #    crudo original (Req 3.7).
    try:
        df = pd.read_csv(ruta_entrada, sep=";", encoding="utf-8")
    except Exception as error:
        print(
            f"[ERROR] No se pudo leer el crudo de '{contexto}' "
            f"('{ruta_entrada}'): {error}. Se omite este indicador y se "
            f"continúa con el resto; el crudo original queda intacto."
        )
        return

    print(f"[OK] Leído crudo de '{contexto}': {len(df)} fila(s).")

    # 2) Normalización según el contenido real del crudo (coma decimal → punto,
    #    gobernanza OBSERVADO). Si el contenido no casa, devuelve lista vacía.
    registros = normalizador(df, fecha_prueba)

    # 3) Filtrado de registros con gobernanza completa (Req 3.3).
    registros_validos = gobernanza.filtra_registros_validos(registros, contexto)

    # 4) Escritura segura en datos_procesados/ (nunca en datos_crudos/, Req 3.7).
    gobernanza.escribe_csv(registros_validos, ruta_salida, columnas)

    print(
        f"[FIN] '{contexto}': {len(registros_validos)} registro(s) escritos en "
        f"'{ruta_salida}'."
    )


def procesa(fecha_prueba: str) -> None:
    """Orquesta la reclasificación independiente de los dos indicadores sociales.

    Lee ambos crudos mal etiquetados y los reclasifica de forma **aislada**: el
    fallo de uno (crudo ilegible o contenido que no casa) no impide el
    procesamiento del otro (Req 3.3, 3.4). Cada indicador se normaliza, se filtra
    con :func:`gobernanza.filtra_registros_validos` y se escribe con
    :func:`gobernanza.escribe_csv` en su CSV de salida
    (``RUTA_SALIDA_POBREZA`` y ``RUTA_SALIDA_FECUNDIDAD``). Los crudos originales
    nunca se modifican ni se eliminan: sólo se leen (Req 3.7). Las rutas son
    relativas a ``scripts/``, según la convención del repositorio.

    Args:
        fecha_prueba: fecha (ISO ``AAAA-MM-DD``) en que se verificó el dato.
    """
    print("[INICIO] Reclasificación de los indicadores sociales mal etiquetados.")

    # Umbrales de pobreza (Crudo_MalEtiquetado_Pobreza → umbrales_pobreza.csv).
    _procesa_indicador(
        RUTA_POBREZA,
        RUTA_SALIDA_POBREZA,
        normaliza_pobreza,
        COLUMNAS_POBREZA,
        "umbrales_pobreza",
        fecha_prueba,
    )

    # Tasa de fecundidad (Crudo_MalEtiquetado_Fecundidad → tasa_fecundidad.csv).
    # Se procesa aparte del anterior: aunque el de pobreza falle, este se ejecuta.
    _procesa_indicador(
        RUTA_FECUNDIDAD,
        RUTA_SALIDA_FECUNDIDAD,
        normaliza_fecundidad,
        COLUMNAS_FECUNDIDAD,
        "tasa_fecundidad",
        fecha_prueba,
    )

    print("[FIN] Reclasificación de indicadores sociales completada.")


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
