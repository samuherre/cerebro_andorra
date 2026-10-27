"""Procesamiento de los desgloses de población por parròquia (tramo Lago).

Este módulo normaliza los cinco desgloses OBSERVADO de población por parròquia
(edad en tramos de 5 y de 1 año, sexo, nacionalidad y lugar de nacimiento) del
Departament d'Estadística d'Andorra, que existen en ``datos_crudos/`` en formato
ancho (años 2020–2025 en columnas), hacia una tabla larga única
``poblacion_desgloses.csv`` en ``datos_procesados/``, con gobernanza completa
(linaje OBSERVADO).

El orden de los segmentos del patrón ``CATEGORIA. PARRÒQUIA. SUBCATEGORIA`` de la
columna ``Descripció`` varía entre crudos (p. ej. nacionalidad invierte el orden
a categoría→parròquia), por lo que se usa un parser configurable por dimensión
(design.md, P8 y H6).

Sub-tarea 1.1: lectura de crudos y parser configurable por dimensión.
Reutiliza ``NOMBRES_CANONICOS`` y el estilo de ``_a_poblacion_entera`` de
``procesa_poblacion.py``. Los mensajes de consola van en español, coherentes con
el resto del proyecto.
"""

import pandas as pd

# Fuente oficial de los desgloses de población (linaje OBSERVADO).
FUENTE_DESGLOSES = "Departament d'Estadística d'Andorra"

# Rango de años esperado en las columnas de cada crudo (Req 1.2).
ANIOS_ESPERADOS = [2020, 2021, 2022, 2023, 2024, 2025]

# Ruta de salida del CSV procesado, relativa a scripts/.
RUTA_SALIDA = "../datos_procesados/poblacion_desgloses.csv"

# Columnas de la tabla procesada poblacion_desgloses.csv, en orden (design.md,
# Req 1.4).
COLUMNAS_SALIDA = [
    "parroquia",
    "dimension",
    "categoria",
    "anio",
    "valor",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]

# Columnas mínimas que debe contener cada crudo de desglose para procesarse
# (Req 1.10): el código, la descripción y las columnas de año esperadas.
COLUMNAS_ESPERADAS = ["Codi", "Descripció"] + [str(anio) for anio in ANIOS_ESPERADOS]

# Mapa de nombres crudos (en mayúsculas) al nombre canónico de cada parròquia,
# tal como se define en el glosario de requisitos. Reutiliza la convención de
# ``procesa_poblacion.py``: la clave es el nombre crudo en MAYÚSCULAS, de modo
# que la búsqueda se hace tras aplicar ``.upper()`` sobre el segmento extraído.
# Esto cubre tanto los crudos en mayúsculas (edad, sexo, nacionalidad) como el
# de lugar de nacimiento, que viene en capitalización tipo título.
NOMBRES_CANONICOS = {
    "CANILLO": "Canillo",
    "ENCAMP": "Encamp",
    "ORDINO": "Ordino",
    "LA MASSANA": "La Massana",
    "ANDORRA LA VELLA": "Andorra la Vella",
    "SANT JULIÀ DE LÒRIA": "Sant Julià de Lòria",
    "ESCALDES-ENGORDANY": "Escaldes-Engordany",
}

# Separador de segmentos dentro de 'Descripció' una vez retirado el prefijo de
# la dimensión. Cada dimensión declara su prefijo, el índice del segmento de la
# parròquia y el índice del segmento de la categoría, para soportar el orden
# variable del patrón CATEGORIA/PARRÒQUIA/SUBCATEGORIA (design.md, H6 y P8).
SEPARADOR_SEGMENTOS = ". "

CONFIGURACION_DIMENSIONES: dict[str, dict] = {
    "edad_5": {
        "archivo": (
            "../datos_crudos/estadistica_id1091_població_població_per_parròquia_"
            "i_edat_(trams_5_anys).csv"
        ),
        "prefijo": "POBLACIÓ PER PARRÒQUIA I EDAT (TRAMS 5 ANYS).",
        "indice_parroquia": 0,
        "indice_categoria": 1,
    },
    "edad_1": {
        "archivo": (
            "../datos_crudos/estadistica_id1092_població_població_per_parròquia_"
            "i_edat_(trams_1_any).csv"
        ),
        "prefijo": "POBLACIÓ PER PARRÒQUIA I EDAT (TRAMS 1 ANY).",
        "indice_parroquia": 0,
        "indice_categoria": 1,
    },
    "sexo": {
        "archivo": (
            "../datos_crudos/estadistica_id1093_població_població_per_parròquia_"
            "i_sexe.csv"
        ),
        "prefijo": "POBLACIÓ PER PARRÒQUIA I SEXE.",
        "indice_parroquia": 0,
        "indice_categoria": 1,
    },
    # La nacionalidad invierte el orden: el patrón es CATEGORIA. PARRÒQUIA, por
    # lo que la parròquia va en el segundo segmento y la categoría en el primero.
    "nacionalidad": {
        "archivo": (
            "../datos_crudos/estadistica_id1094_població_població_per_"
            "nacionalitat_i_parròquia.csv"
        ),
        "prefijo": "POBLACIÓ PER NACIONALITAT I PARRÒQUIA.",
        "indice_parroquia": 1,
        "indice_categoria": 0,
    },
    # El crudo de lugar de nacimiento viene en capitalización tipo título; el
    # mapeo a parròquia canónica se hace tras aplicar .upper() (Req 1.3).
    "lugar_nacimiento": {
        "archivo": (
            "../datos_crudos/estadistica_id1137_població_població_per_parròquia_"
            "i_lloc_de_naixement.csv"
        ),
        "prefijo": "Població per parròquia i lloc de naixement.",
        "indice_parroquia": 0,
        "indice_categoria": 1,
    },
}


def lee_crudo(ruta_entrada: str) -> pd.DataFrame | None:
    """Lee un crudo de desglose usando separador ``;`` y codificación UTF-8.

    Devuelve ``None`` (y registra por consola en español la causa y el nombre del
    archivo afectado) cuando el crudo no puede procesarse, de modo que el
    desglose se omita sin detener los demás (Req 1.10). Los casos cubiertos son:

    - el archivo no existe en la ruta indicada;
    - el archivo existe pero no puede leerse o parsearse;
    - el archivo está vacío (sin filas de datos);
    - le falta una o más de las columnas esperadas (``Codi``, ``Descripció`` y
      las columnas de año 2020–2025).

    Args:
        ruta_entrada: ruta al CSV crudo del desglose, relativa a ``scripts/``.

    Returns:
        El DataFrame con el contenido del crudo, o ``None`` si no puede
        procesarse por cualquiera de las causas anteriores.
    """
    try:
        df = pd.read_csv(ruta_entrada, sep=";", encoding="utf-8")
    except FileNotFoundError:
        print(
            f"[ERROR] No se encontró el crudo de desglose: '{ruta_entrada}'. "
            "Se omite este desglose."
        )
        return None
    except Exception as error:
        print(
            f"[ERROR] No se pudo leer el crudo de desglose '{ruta_entrada}': "
            f"{error}. Se omite este desglose."
        )
        return None

    # Crudo vacío: no hay filas de datos que normalizar.
    if df.empty:
        print(
            f"[ERROR] El crudo de desglose '{ruta_entrada}' está vacío "
            "(sin filas de datos). Se omite este desglose."
        )
        return None

    # Verificación de columnas esperadas (Codi, Descripció y años 2020–2025).
    faltantes = [columna for columna in COLUMNAS_ESPERADAS if columna not in df.columns]
    if faltantes:
        print(
            f"[ERROR] Al crudo de desglose '{ruta_entrada}' le faltan columnas "
            f"esperadas: {faltantes}. Se omite este desglose."
        )
        return None

    print(
        f"[OK] Crudo de desglose leído: '{ruta_entrada}' "
        f"({len(df)} filas, {len(df.columns)} columnas)."
    )
    return df


def segmenta_descripcion(descripcion: str, prefijo: str) -> list[str] | None:
    """Divide la columna 'Descripció' en segmentos tras retirar el prefijo.

    Elimina el prefijo de la dimensión (p. ej.
    ``"POBLACIÓ PER PARRÒQUIA I SEXE."``) y divide el resto por el separador
    ``". "`` (``SEPARADOR_SEGMENTOS``), devolviendo la lista de segmentos. El
    patrón esperado es ``CATEGORIA. PARRÒQUIA. SUBCATEGORIA``, que tras quitar el
    prefijo deja al menos dos segmentos (parròquia y categoría, en el orden que
    indique la configuración de la dimensión).

    Devuelve ``None`` si la descripción no casa el patrón —es decir, si no
    empieza por el prefijo o si, una vez retirado, no quedan al menos dos
    segmentos no vacíos—, para que la fila se omita y se registre aguas arriba
    (Req 1.8).

    Args:
        descripcion: valor de la columna 'Descripció' de una fila.
        prefijo: prefijo de la dimensión a retirar antes de segmentar.

    Returns:
        La lista de segmentos (ya sin espacios sobrantes) o ``None`` si la
        descripción no casa el patrón esperado.
    """
    if descripcion is None:
        return None

    texto = str(descripcion).strip()

    # El patrón exige que la descripción comience por el prefijo de la dimensión
    # (comparación insensible a mayúsculas por robustez entre crudos).
    prefijo_limpio = prefijo.strip()
    if not texto.upper().startswith(prefijo_limpio.upper()):
        return None

    resto = texto[len(prefijo_limpio):].strip()
    if resto == "":
        return None

    # División por ". " y limpieza de espacios en cada segmento. Se descartan los
    # segmentos vacíos que pudieran surgir de puntos finales u otros artefactos.
    segmentos = [
        segmento.strip()
        for segmento in resto.split(SEPARADOR_SEGMENTOS)
        if segmento.strip() != ""
    ]

    # El patrón CATEGORIA/PARRÒQUIA requiere al menos dos segmentos (parròquia y
    # categoría). Si no los hay, la fila no casa el patrón.
    if len(segmentos) < 2:
        return None

    return segmentos


def _a_poblacion_entera(valor) -> int | None:
    """Convierte un valor de población a entero no negativo.

    Replica el estilo de ``procesa_poblacion._a_poblacion_entera``: devuelve
    ``None`` si el valor es vacío, no numérico, no entero o negativo, para que la
    celda afectada pueda excluirse y registrarse (Req 1.7).

    Args:
        valor: valor crudo de la celda de población.

    Returns:
        El entero de población (>= 0) o ``None`` si no es válido.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    if texto == "":
        return None
    try:
        # Se admite "4422" y "4422.0"; se rechaza texto no numérico.
        numero = float(texto.replace(",", ""))
    except (ValueError, TypeError):
        return None
    if numero < 0:
        return None
    if numero != int(numero):
        # Un decimal no entero (p. ej. 4422.5) no es una población válida.
        return None
    return int(numero)


# --- Sub-tarea 1.2: extracción parròquia/categoría y transformación ---------


def extrae_parroquia_categoria(
    descripcion: str, config: dict
) -> "tuple[str, str] | None":
    """Extrae la parròquia canónica y la categoría de la dimensión.

    Segmenta la columna 'Descripció' con :func:`segmenta_descripcion` (usando el
    prefijo de la dimensión declarado en ``config``) y aplica los índices
    ``indice_parroquia`` e ``indice_categoria`` para localizar cada segmento,
    soportando así el orden variable del patrón ``CATEGORIA. PARRÒQUIA.
    SUBCATEGORIA`` entre crudos (la nacionalidad invierte el orden, H6/P8).

    El segmento de la parròquia se mapea a su nombre canónico a través de
    ``NOMBRES_CANONICOS`` tras aplicar ``.upper()``, de modo que cada fila queda
    asignada a exactamente una de las 7 parròquies (Req 1.3). La categoría se
    devuelve tal cual aparece en el crudo, limpiando sólo los espacios sobrantes.

    Devuelve ``None`` (para que la fila se omita y se registre aguas arriba,
    Req 1.8) cuando:

    - la descripción no casa el patrón (``segmenta_descripcion`` devuelve
      ``None``);
    - los índices configurados caen fuera de la lista de segmentos;
    - el segmento de categoría queda vacío;
    - la parròquia cruda no se reconoce entre las 7 canónicas (Req 1.3).

    Args:
        descripcion: valor de la columna 'Descripció' de una fila.
        config: configuración de la dimensión (``prefijo``, ``indice_parroquia``
            e ``indice_categoria``).

    Returns:
        La tupla ``(parroquia_canonica, categoria)`` o ``None`` si la parròquia
        no se reconoce o el patrón no casa.
    """
    segmentos = segmenta_descripcion(descripcion, config["prefijo"])
    if segmentos is None:
        return None

    indice_parroquia = config["indice_parroquia"]
    indice_categoria = config["indice_categoria"]

    # Los índices configurados deben existir en la lista de segmentos; si no, la
    # fila no casa el patrón esperado de su dimensión (Req 1.8).
    if indice_parroquia >= len(segmentos) or indice_categoria >= len(segmentos):
        return None

    segmento_parroquia = segmentos[indice_parroquia].strip()
    categoria = segmentos[indice_categoria].strip()

    # Una categoría vacía no describe ninguna subcategoría válida.
    if categoria == "":
        return None

    # Mapeo a parròquia canónica tras .upper(): cubre tanto los crudos en
    # mayúsculas como el de lugar de nacimiento (capitalización tipo título).
    parroquia_canonica = NOMBRES_CANONICOS.get(segmento_parroquia.upper())
    if parroquia_canonica is None:
        return None

    return parroquia_canonica, categoria


def normaliza_dimension(
    df: pd.DataFrame, dimension: str, config: dict
) -> list[dict]:
    """Transforma un desglose de población de formato ancho a largo.

    Recorre el DataFrame leído por :func:`lee_crudo` y, por cada fila, extrae la
    parròquia canónica y la categoría con :func:`extrae_parroquia_categoria`.
    Para cada año presente dentro del rango esperado (``ANIOS_ESPERADOS``) emite
    un registro ``{"parroquia", "dimension", "categoria", "anio", "valor"}`` con
    ``valor`` entero ``>= 0`` (Req 1.2, 1.4).

    Exclusiones, cada una registrada por consola en español sin inventar cifras:

    - filas cuyo contenido de 'Descripció' no casa el patrón o cuya parròquia no
      se reconoce: se omite la fila completa (Req 1.8);
    - celdas cuyo valor está vacío, no es numérico, no es entero o es negativo:
      se omite ese (parròquia, categoría, año) concreto y se identifica en el
      mensaje de advertencia (Req 1.7);
    - años esperados cuya columna falta en el crudo: se omite ese año y se avisa.

    Args:
        df: DataFrame del crudo del desglose (columnas ``Codi``, ``Descripció``
            y años 2020–2025).
        dimension: clave de la dimensión (``edad_5``, ``edad_1``, ``sexo``,
            ``nacionalidad`` o ``lugar_nacimiento``), que se escribe en la
            columna ``dimension``.
        config: configuración de la dimensión (prefijo e índices de segmento).

    Returns:
        Lista de registros en formato largo, uno por (parròquia, categoría, año)
        válido.
    """
    if "Descripció" not in df.columns:
        print(
            f"[ERROR] El crudo de la dimensión '{dimension}' no contiene la "
            "columna 'Descripció'. No se puede normalizar; se devuelve lista "
            "vacía."
        )
        return []

    # Columnas de año presentes en el DataFrame (respetando el rango esperado).
    anios_presentes = [
        anio for anio in ANIOS_ESPERADOS
        if str(anio) in df.columns or anio in df.columns
    ]
    faltantes = [anio for anio in ANIOS_ESPERADOS if anio not in anios_presentes]
    if faltantes:
        print(
            f"[AVISO] Dimensión '{dimension}': faltan columnas de año "
            f"esperadas {faltantes}. Esos años se omitirán."
        )

    registros: list[dict] = []
    filas_sin_patron = 0
    celdas_invalidas = 0

    for indice, fila in df.iterrows():
        resultado = extrae_parroquia_categoria(fila["Descripció"], config)
        if resultado is None:
            # La fila no casa el patrón o la parròquia no se reconoce (Req 1.8).
            filas_sin_patron += 1
            print(
                f"[AVISO] Dimensión '{dimension}', fila {indice}: contenido de "
                f"'Descripció' no reconocido ('{fila['Descripció']}'). Se omite "
                "la fila."
            )
            continue

        parroquia_canonica, categoria = resultado

        for anio in anios_presentes:
            # Localiza la columna del año, sea de tipo str o int.
            clave = str(anio) if str(anio) in df.columns else anio

            valor = _a_poblacion_entera(fila[clave])
            if valor is None:
                # Celda inválida: se identifica parròquia, categoría y año (Req 1.7).
                celdas_invalidas += 1
                print(
                    f"[AVISO] Dimensión '{dimension}' ({parroquia_canonica}, "
                    f"categoría '{categoria}', año {anio}): valor inválido "
                    f"('{fila[clave]}'). Se excluye ese registro."
                )
                continue

            registros.append(
                {
                    "parroquia": parroquia_canonica,
                    "dimension": dimension,
                    "categoria": categoria,
                    "anio": int(anio),
                    "valor": valor,
                }
            )

    print(
        f"[OK] Dimensión '{dimension}' normalizada: {len(registros)} registro(s) "
        f"válidos, {filas_sin_patron} fila(s) sin patrón y {celdas_invalidas} "
        "celda(s) inválida(s) excluidas."
    )
    return registros


# --- Sub-tarea 1.3: anotación de gobernanza y orquestación de las 5 dimensiones ---
import datetime

import gobernanza


def anota_gobernanza(registros: list[dict], fecha_prueba: str) -> list[dict]:
    """Añade los metadatos de gobernanza a cada registro de desglose.

    A cada registro producido por :func:`normaliza_dimension` (que contiene
    ``parroquia``, ``dimension``, ``categoria``, ``anio`` y ``valor``) le
    adjunta ``fuente`` (=``FUENTE_DESGLOSES``), ``vigencia`` (=año del registro,
    como texto), ``fecha_prueba`` (ISO ``AAAA-MM-DD``) y ``linaje`` con valor
    OBSERVADO, garantizando que ninguna cifra salga sin su procedencia (Req 1.6).
    No altera las claves existentes del registro; sólo agrega las de gobernanza.

    Args:
        registros: registros de desglose normalizados (``{"parroquia",
            "dimension", "categoria", "anio", "valor"}``).
        fecha_prueba: fecha (ISO ``AAAA-MM-DD``) en que se verificó/procesó el
            dato.

    Returns:
        La lista de registros, cada uno enriquecido con ``fuente``,
        ``vigencia``, ``fecha_prueba`` y ``linaje`` = OBSERVADO.
    """
    for registro in registros:
        registro["fuente"] = FUENTE_DESGLOSES
        # La vigencia es el año del propio registro, expresado como texto.
        registro["vigencia"] = str(registro.get("anio", ""))
        registro["fecha_prueba"] = fecha_prueba
        registro["linaje"] = gobernanza.LINAJE_OBSERVADO

    print(
        f"[OK] Gobernanza anotada en {len(registros)} registro(s) de desgloses "
        f"(fuente OBSERVADO, fecha de prueba {fecha_prueba})."
    )
    return registros


def procesa(fecha_prueba: str) -> None:
    """Orquesta el procesamiento completo de los 5 desgloses de población.

    Recorre ``CONFIGURACION_DIMENSIONES`` y, por cada dimensión, lee su crudo
    con :func:`lee_crudo`, lo normaliza de ancho a largo con
    :func:`normaliza_dimension`, le anota la gobernanza (linaje OBSERVADO) y
    acumula sus registros. Un desglose ausente o ilegible (``lee_crudo``
    devuelve ``None``) se omite sin detener los demás (Req 1.10). Finalmente
    concatena las dimensiones procesadas, filtra los registros con gobernanza
    completa con ``gobernanza.filtra_registros_validos`` y escribe el resultado
    en ``RUTA_SALIDA`` con ``gobernanza.escribe_csv`` (separador ``;``, UTF-8,
    creando el directorio de salida de forma idempotente; Req 1.5, 1.6, 1.9).

    Las rutas son relativas a ``scripts/`` según la convención del repositorio;
    ``gobernanza.escribe_csv`` rechaza cualquier escritura dentro de
    ``datos_crudos/``, que permanece intacto como fuente de verdad (Req 1.9).

    Args:
        fecha_prueba: fecha (ISO ``AAAA-MM-DD``) en que se verificó/procesó el
            dato.
    """
    print("[INICIO] Procesamiento de los desgloses de población por parròquia.")

    registros_totales: list[dict] = []
    dimensiones_procesadas = 0
    dimensiones_omitidas = 0

    for dimension, config in CONFIGURACION_DIMENSIONES.items():
        print(f"[PASO] Procesando desglose '{dimension}'...")

        # 1) Lectura del crudo. Si falla, se omite este desglose (Req 1.10).
        df = lee_crudo(config["archivo"])
        if df is None:
            dimensiones_omitidas += 1
            print(
                f"[OMITIDO] Desglose '{dimension}' omitido; se continúa con los "
                "demás."
            )
            continue

        # 2) Normalización ancho→largo (Req 1.2, 1.7, 1.8).
        registros = normaliza_dimension(df, dimension, config)

        # 3) Anotación de gobernanza (linaje OBSERVADO, Req 1.6).
        registros = anota_gobernanza(registros, fecha_prueba)

        # 4) Acumulación para concatenar las 5 dimensiones.
        registros_totales.extend(registros)
        dimensiones_procesadas += 1

    print(
        f"[RESUMEN] Desgloses procesados: {dimensiones_procesadas}; omitidos: "
        f"{dimensiones_omitidas}. Total de registros acumulados: "
        f"{len(registros_totales)}."
    )

    # 5) Filtrado de registros con gobernanza completa (Req 1.6).
    registros_validos = gobernanza.filtra_registros_validos(
        registros_totales, "poblacion_desgloses"
    )

    # 6) Escritura segura en datos_procesados/ (Req 1.5, 1.9).
    gobernanza.escribe_csv(registros_validos, RUTA_SALIDA, COLUMNAS_SALIDA)

    print(
        f"[FIN] Procesamiento de desgloses completado: "
        f"{len(registros_validos)} registro(s) escritos en '{RUTA_SALIDA}'."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
