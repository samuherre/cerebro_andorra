"""Procesamiento del presupuesto de turismo (tramo Lago).

Este módulo lee el CSV crudo del presupuesto final de despeses de Andorra
Turisme, SAU (``estadistica_681``) del Departament d'Estadística d'Andorra,
normaliza los importes en euros (coma decimal catalana), lo transforma de
formato ancho a largo, le anota la gobernanza (linaje OBSERVADO) y escribe el
resultado en ``datos_procesados/``.

Imita el patrón ancho→largo de ``procesa_poblacion.py`` (v1) y reutiliza
``gobernanza.py`` tal cual para la validación "0 cifras sin fuente".

Sub-tarea 1.1: lectura del CSV de turismo, manejo de errores y normalización
de importes (coma decimal a punto, rango válido y nombre de partida).
Los mensajes de consola van en español, coherentes con el resto del proyecto.
"""

import pandas as pd

# --- Constantes de la fuente de turismo ------------------------------------

# Fuente oficial del dato de turismo (linaje OBSERVADO).
FUENTE_TURISMO = (
    "Departament d'Estadística d'Andorra (estadistica_681, Andorra Turisme SAU)"
)

# Prefijo común que antecede al nombre de la partida en la columna 'Descripció'.
PREFIJO_DESCRIPCION = "PRESSUPOST FINAL DE DESPESES. ANDORRA TURISME, SAU."

# Sufijos de 'Descripció' (normalizados en mayúsculas) de las partidas que se
# emiten a la salida. El resto de partidas del crudo se ignoran.
PARTIDA_FUNCIONAMENT = "DESPESES DE FUNCIONAMENT"
PARTIDA_TOTAL = "TOTAL PRESSUPOST DE DESPESES"

# Rango de años esperado en las columnas del CSV crudo.
ANIOS_ESPERADOS = [2020, 2021, 2022, 2023, 2024, 2025]

# Columnas no-año que deben existir en el crudo para poder procesarlo.
COLUMNAS_CLAVE = ["Codi", "Descripció"]

# Rango válido (inclusive) de un importe de presupuesto en euros (Req 3.2):
# de 0 a 999.999.999.999,99.
RANGO_VALOR = (0.0, 999_999_999_999.99)


def lee_turismo(ruta_entrada: str) -> pd.DataFrame:
    """Lee el CSV de turismo usando separador ``;`` y codificación UTF-8.

    Ante un archivo inexistente, ilegible, vacío o al que le falten una o más
    columnas esperadas (``Codi``, ``Descripció`` y los años de
    ``ANIOS_ESPERADOS``), registra un mensaje de error en español por consola
    indicando el archivo afectado y la causa, y aborta sin escribir ninguna
    salida propagando una excepción para que la orquestación finalice sin crear
    un archivo parcial (Req 3.1, 3.6).

    Args:
        ruta_entrada: Ruta al CSV crudo del presupuesto de turismo.

    Returns:
        DataFrame con el contenido del CSV leído.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta indicada.
        ValueError: Si el archivo está vacío o le faltan columnas esperadas.
        Exception: Si el archivo existe pero no puede leerse o parsearse.
    """
    try:
        df = pd.read_csv(ruta_entrada, sep=";", encoding="utf-8")
    except FileNotFoundError:
        print(
            f"[ERROR] No se encontró el archivo de turismo: '{ruta_entrada}'. "
            "Se aborta el procesamiento sin escribir salida."
        )
        raise
    except pd.errors.EmptyDataError:
        print(
            f"[ERROR] El archivo de turismo '{ruta_entrada}' está vacío. "
            "Se aborta el procesamiento sin escribir salida."
        )
        raise
    except Exception as error:
        print(
            f"[ERROR] No se pudo leer el archivo de turismo '{ruta_entrada}': "
            f"{error}. Se aborta el procesamiento sin escribir salida."
        )
        raise

    # Un CSV con cabecera pero sin filas de datos se considera vacío (Req 3.6).
    if df.empty:
        mensaje = (
            f"[ERROR] El archivo de turismo '{ruta_entrada}' no contiene filas "
            "de datos. Se aborta el procesamiento sin escribir salida."
        )
        print(mensaje)
        raise ValueError(mensaje)

    # Verificación de columnas esperadas: Codi, Descripció y los años (Req 3.6).
    columnas = set(df.columns)
    esperadas = COLUMNAS_CLAVE + [str(anio) for anio in ANIOS_ESPERADOS]
    faltantes = [
        columna
        for columna in esperadas
        if columna not in columnas and (
            # Admite columnas de año tipo int además de str.
            not (columna.isdigit() and int(columna) in columnas)
        )
    ]
    if faltantes:
        mensaje = (
            f"[ERROR] Al archivo de turismo '{ruta_entrada}' le faltan columnas "
            f"esperadas: {faltantes}. Se aborta el procesamiento sin escribir "
            "salida."
        )
        print(mensaje)
        raise ValueError(mensaje)

    print(
        f"[OK] Archivo de turismo leído: '{ruta_entrada}' "
        f"({len(df)} filas, {len(df.columns)} columnas)."
    )
    return df


def _a_euros(valor) -> float | None:
    """Normaliza un importe de presupuesto en euros a ``float``.

    Convierte la coma decimal catalana a punto (``'20867866,12'`` ->
    ``20867866.12``) y elimina separadores de miles si los hubiera (puntos en
    la parte entera o espacios). Devuelve ``None`` si el valor es vacío, no
    numérico o cae fuera de ``RANGO_VALOR``, para que ese registro pueda
    excluirse y registrarse (Req 3.2, 3.3).

    Args:
        valor: Valor crudo de la celda de importe (texto o número).

    Returns:
        El importe en euros como ``float`` dentro de ``RANGO_VALOR``, o
        ``None`` si no es válido.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None

    texto = str(valor).strip()
    if texto == "":
        return None

    # Eliminar espacios internos usados a veces como separador de miles.
    texto = texto.replace(" ", "")

    # Normalizar separadores decimales y de miles.
    #   - Con coma y punto presentes, la coma es el decimal y el punto el miles
    #     (convención catalana): '1.234.567,89' -> '1234567.89'.
    #   - Sólo con coma, es el separador decimal: '20867866,12' -> '20867866.12'.
    #   - Sólo con punto, se trata como decimal (el crudo no usa punto de miles
    #     en los valores enteros): '17435555' / '123.45'.
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        numero = float(texto)
    except (ValueError, TypeError):
        return None

    minimo, maximo = RANGO_VALOR
    if numero < minimo or numero > maximo:
        return None

    return numero


def _nombre_partida(descripcion: str) -> str:
    """Extrae el nombre de la partida desde la columna 'Descripció'.

    Elimina el prefijo común ``PREFIJO_DESCRIPCION`` y los espacios y puntos
    sobrantes, devolviendo el sufijo restante en mayúsculas para una
    comparación estable; por ejemplo
    ``"PRESSUPOST FINAL DE DESPESES. ANDORRA TURISME, SAU. DESPESES DE FUNCIONAMENT"``
    -> ``"DESPESES DE FUNCIONAMENT"``.

    Args:
        descripcion: Valor de la columna 'Descripció' de una fila.

    Returns:
        El nombre de la partida en mayúsculas, sin el prefijo común.
    """
    texto = str(descripcion).strip()
    if texto.upper().startswith(PREFIJO_DESCRIPCION):
        texto = texto[len(PREFIJO_DESCRIPCION):]
    # Limpia espacios y el punto que sigue al prefijo ("SAU. DESPESES...").
    return texto.strip().strip(".").strip().upper()

# --- Sub-tarea 1.2: transformación ancho→largo y anotación de gobernanza ----

import gobernanza

# Partidas que se emiten a la salida (sufijos de 'Descripció' en mayúsculas).
# El resto de partidas del crudo se ignoran para evitar series sin contexto.
PARTIDAS_EMITIDAS = (PARTIDA_FUNCIONAMENT, PARTIDA_TOTAL)


def normaliza_ancho_a_largo(df: pd.DataFrame) -> list[dict]:
    """Transforma el DataFrame de turismo de formato ancho a formato largo.

    El crudo tiene un registro por partida presupuestaria con los importes en
    columnas de año (2020..2025). Esta función emite **sólo** las partidas
    canónicas ``PARTIDA_FUNCIONAMENT`` y ``PARTIDA_TOTAL`` (identificadas por el
    sufijo de 'Descripció' mediante :func:`_nombre_partida`), produciendo un
    registro por cada combinación de (partida, año) con las claves ``periodo``
    (año, entero), ``partida`` (texto) y ``valor_eur`` (float >= 0).

    La comparación de partida es por igualdad exacta contra las partidas
    emitidas, de modo que la fila agregada alternativa
    ``TOTAL PRESSUPOST DE DESPESES (SENSE VARIACIÓ ...)`` no se confunde con el
    total ni se cuenta dos veces. Las demás partidas del crudo se ignoran.

    Los años con importe no numérico, vacío o fuera de ``RANGO_VALOR``
    (según :func:`_a_euros`) se excluyen de la salida y se registran por consola
    en español indicando el periodo y la causa (Req 3.2, 3.3). Si falta una
    columna de año esperada, ese periodo se omite y se avisa.

    Args:
        df: DataFrame leído por :func:`lee_turismo` (columnas Codi,
            Descripció, 2020..2025).

    Returns:
        Lista de diccionarios ``{"periodo": int, "partida": str,
        "valor_eur": float}``, uno por cada (partida emitida, año) válido.
    """
    if "Descripció" not in df.columns:
        print(
            "[ERROR] El archivo de turismo no contiene la columna 'Descripció'. "
            "No se puede normalizar; se devuelve lista vacía."
        )
        return []

    # Aviso de columnas de año faltantes (se omitirán al recorrer).
    faltantes = [
        anio
        for anio in ANIOS_ESPERADOS
        if str(anio) not in df.columns and anio not in df.columns
    ]
    if faltantes:
        print(
            "[AVISO] Faltan columnas de año esperadas en el archivo de turismo: "
            f"{faltantes}. Esos periodos se omitirán."
        )

    registros: list[dict] = []

    for indice, fila in df.iterrows():
        partida = _nombre_partida(fila["Descripció"])

        # Sólo se emiten las dos partidas canónicas; el resto se ignora.
        if partida not in PARTIDAS_EMITIDAS:
            continue

        for anio in ANIOS_ESPERADOS:
            # Localiza la columna del año, sea de tipo str o int.
            if str(anio) in df.columns:
                clave = str(anio)
            elif anio in df.columns:
                clave = anio
            else:
                # Ya avisado arriba; se omite este periodo.
                continue

            valor_eur = _a_euros(fila[clave])
            if valor_eur is None:
                print(
                    f"[ERROR] Partida '{partida}', periodo {anio}: importe "
                    f"inválido ('{fila[clave]}'); valor vacío, no numérico o "
                    "fuera del rango permitido. Se excluye ese registro."
                )
                continue

            registros.append(
                {
                    "periodo": int(anio),
                    "partida": partida,
                    "valor_eur": valor_eur,
                }
            )

    print(
        f"[OK] Normalización ancho a largo de turismo completada: "
        f"{len(registros)} registro(s) válidos generados "
        f"({len(PARTIDAS_EMITIDAS)} partidas × {len(ANIOS_ESPERADOS)} años)."
    )
    return registros


def anota_gobernanza(registros: list[dict], fecha_prueba: str) -> list[dict]:
    """Añade los metadatos de gobernanza a cada registro de turismo.

    A cada registro le adjunta ``fuente`` (=``FUENTE_TURISMO``), ``vigencia``
    (=periodo del registro, como texto), ``fecha_prueba`` y ``linaje`` con valor
    OBSERVADO, garantizando que ninguna cifra de presupuesto salga sin su
    procedencia (Req 3.4, 10.4). No altera las claves de dominio existentes del
    registro (``periodo``, ``partida``, ``valor_eur``); sólo agrega las de
    gobernanza.

    Args:
        registros: registros de turismo normalizados
            (``{"periodo", "partida", "valor_eur"}``).
        fecha_prueba: fecha (ISO) en que se verificó/procesó el dato.

    Returns:
        La lista de registros, cada uno enriquecido con ``fuente``,
        ``vigencia``, ``fecha_prueba`` y ``linaje`` = OBSERVADO.
    """
    for registro in registros:
        registro["fuente"] = FUENTE_TURISMO
        # La vigencia es el periodo (año) del propio registro, como texto.
        registro["vigencia"] = str(registro.get("periodo", ""))
        registro["fecha_prueba"] = fecha_prueba
        registro["linaje"] = gobernanza.LINAJE_OBSERVADO

    print(
        f"[OK] Gobernanza anotada en {len(registros)} registro(s) de turismo "
        f"(fuente OBSERVADO, fecha de prueba {fecha_prueba})."
    )
    return registros


# --- Sub-tarea 1.3: orquestación del script de turismo ---------------------
import datetime

# Ruta del CSV crudo del presupuesto de turismo, relativa a scripts/.
RUTA_ENTRADA = (
    "../datos_crudos/"
    "estadistica_681_turisme_pressupost_final_de_despeses_andorra_turisme,_sau.csv"
)

# Ruta de salida del CSV procesado, relativa a scripts/.
RUTA_SALIDA = "../datos_procesados/turismo.csv"

# Columnas de la tabla procesada turismo.csv, en orden: primero las de dominio
# (periodo, partida, valor_eur) y después las de gobernanza, coherentes con el
# patrón de poblacion_parroquia.csv de la v1 (design.md).
COLUMNAS_SALIDA = [
    "periodo",
    "partida",
    "valor_eur",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def procesa(fecha_prueba: str) -> None:
    """Orquesta el procesamiento completo del presupuesto de turismo.

    Lee el CSV crudo (``RUTA_ENTRADA``), lo normaliza de ancho a largo (sólo las
    partidas de funcionamiento y total), anota la gobernanza (linaje OBSERVADO),
    filtra los registros con gobernanza completa mediante
    :func:`gobernanza.filtra_registros_validos` y escribe el resultado en
    ``RUTA_SALIDA`` con separador ``;`` y UTF-8 vía :func:`gobernanza.escribe_csv`.

    Ante un archivo de entrada inexistente, ilegible, vacío o sin columnas
    esperadas, :func:`lee_turismo` lanza una excepción; aquí se captura para
    abortar limpiamente sin escribir ninguna salida parcial (Req 3.6). Las rutas
    son relativas a ``scripts/``, según la convención del repositorio
    (Req 3.4, 3.5, 3.6).

    Args:
        fecha_prueba: fecha (ISO) en que se verificó/procesó el dato.
    """
    print("[INICIO] Procesamiento del presupuesto de turismo.")

    # 1) Lectura del crudo. Si falla, abortar sin escribir salida (Req 3.6).
    try:
        df = lee_turismo(RUTA_ENTRADA)
    except Exception:
        print(
            "[ABORTADO] No se pudo leer el archivo de turismo; no se escribe "
            "ninguna salida."
        )
        return

    # 2) Normalización ancho→largo (sólo partidas emitidas, excluye inválidos).
    registros = normaliza_ancho_a_largo(df)

    # 3) Anotación de gobernanza (linaje OBSERVADO, Req 3.4).
    registros = anota_gobernanza(registros, fecha_prueba)

    # 4) Filtrado de registros con gobernanza completa (Req 3.5).
    registros_validos = gobernanza.filtra_registros_validos(registros, "turismo")

    # 5) Escritura segura en datos_procesados/ (separador ';', UTF-8).
    gobernanza.escribe_csv(registros_validos, RUTA_SALIDA, COLUMNAS_SALIDA)

    print(
        f"[FIN] Procesamiento de turismo completado: "
        f"{len(registros_validos)} registro(s) escritos en '{RUTA_SALIDA}'."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
