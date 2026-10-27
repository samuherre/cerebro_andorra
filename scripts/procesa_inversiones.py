"""Procesamiento de inversiones inmobiliarias (tramo Lago).

Este módulo lee el CSV crudo del número de inversiones inmobiliarias del
Departament d'Estadística d'Andorra (``estadistica_2729``), lo normaliza de
formato ancho a largo (un registro por año), le anota la gobernanza (linaje
OBSERVADO) y escribe el resultado en ``datos_procesados/``.

La fuente tiene una sola fila (``Nombre d'inversions immobiliàries``) con el
número de inversiones por año en columnas (2020..2025). El procesamiento
produce un registro por año, con el número de inversiones como entero ``>= 0``
y ``<= 999_999``.

Sub-tarea 2.1: lectura del CSV de inversiones con manejo de errores y
conversión del valor a entero no negativo acotado.

Imita el patrón ancho→largo de ``procesa_poblacion.py`` y reutiliza
``gobernanza.py`` tal cual. Los mensajes de consola van en español, coherentes
con el resto del proyecto.
"""

import pandas as pd

# Fuente oficial del dato de inversiones inmobiliarias (linaje OBSERVADO).
FUENTE_INVERSIONES = (
    "Departament d'Estadística d'Andorra "
    "(estadistica_2729, inversions immobiliàries)"
)

# Rango de años esperado en las columnas del CSV crudo (Req 4.1, 4.2).
ANIOS_ESPERADOS = [2020, 2021, 2022, 2023, 2024, 2025]

# Rango admitido para el número de inversiones (entero, inclusive) (Req 4.2, 4.6).
RANGO_NUM = (0, 999_999)


def lee_inversiones(ruta_entrada: str) -> pd.DataFrame:
    """Lee el CSV de inversiones usando separador ``;`` y codificación UTF-8.

    Ante un archivo inexistente, ilegible o sin las columnas esperadas
    (``Descripció`` y al menos una columna de año), registra un mensaje de error
    en español por consola indicando la ruta afectada y la causa, y aborta sin
    escribir ninguna salida propagando una excepción para que la orquestación
    finalice sin crear un archivo parcial (Req 4.1, 4.5).

    Args:
        ruta_entrada: ruta al CSV crudo de inversiones inmobiliarias.

    Returns:
        DataFrame con el contenido del CSV leído.

    Raises:
        FileNotFoundError: si el archivo no existe en la ruta indicada.
        ValueError: si el archivo existe pero le faltan columnas esperadas.
        Exception: si el archivo existe pero no puede leerse o parsearse.
    """
    try:
        df = pd.read_csv(ruta_entrada, sep=";", encoding="utf-8")
    except FileNotFoundError:
        print(
            f"[ERROR] No se encontró el archivo de inversiones: "
            f"'{ruta_entrada}'. Se aborta el procesamiento sin escribir salida."
        )
        raise
    except Exception as error:
        print(
            f"[ERROR] No se pudo leer el archivo de inversiones "
            f"'{ruta_entrada}': {error}. Se aborta el procesamiento sin "
            "escribir salida."
        )
        raise

    # Validación de columnas esperadas: debe existir 'Descripció' y al menos
    # una columna de año del rango esperado (Req 4.5).
    columnas = set(df.columns)
    faltantes: list[str] = []
    if "Descripció" not in columnas:
        faltantes.append("Descripció")

    anios_presentes = [
        anio for anio in ANIOS_ESPERADOS
        if str(anio) in columnas or anio in columnas
    ]
    if not anios_presentes:
        faltantes.append("al menos una columna de año (2020..2025)")

    if faltantes:
        mensaje = (
            f"[ERROR] El archivo de inversiones '{ruta_entrada}' no contiene "
            f"las columnas esperadas: {faltantes}. Se aborta el procesamiento "
            "sin escribir salida."
        )
        print(mensaje)
        raise ValueError(mensaje)

    print(
        f"[OK] Archivo de inversiones leído: '{ruta_entrada}' "
        f"({len(df)} filas, {len(df.columns)} columnas)."
    )
    return df


def _a_entero_no_negativo(valor) -> int | None:
    """Convierte un valor al número de inversiones como entero no negativo.

    Devuelve ``None`` si el valor es vacío, no numérico, no entero, negativo o
    superior a ``999_999``, para que ese año pueda excluirse de la salida y
    registrarse por consola (Req 4.6).

    Args:
        valor: valor crudo de la celda de número de inversiones.

    Returns:
        El entero de inversiones (``0 <= n <= 999_999``) o ``None`` si no es
        un valor válido.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    if texto == "":
        return None
    try:
        # Se admite "322" y "322.0"; se rechaza texto no numérico. Primero se
        # intenta la conversión directa para que un decimal real como "3.5" se
        # interprete como no entero (y se rechace), en lugar de confundir el
        # punto con un separador de miles.
        numero = float(texto)
    except (ValueError, TypeError):
        # Reintento tolerando separadores de miles ("1.234" o "1,234").
        try:
            numero = float(texto.replace(".", "").replace(",", ""))
        except (ValueError, TypeError):
            return None
    if numero != int(numero):
        # Un decimal no entero (p. ej. 322.5) no es un número de inversiones
        # válido.
        return None
    numero = int(numero)
    minimo, maximo = RANGO_NUM
    if numero < minimo or numero > maximo:
        return None
    return numero


# --- Sub-tarea 2.2: transformación ancho→largo y anotación de gobernanza ----
import gobernanza


def normaliza_ancho_a_largo(df: pd.DataFrame) -> list[dict]:
    """Transforma el DataFrame de formato ancho a formato largo.

    La fuente de inversiones tiene una sola fila (``Nombre d'inversions
    immobiliàries``) con el número de inversiones por año en columnas
    (2020..2025). Esta función produce un registro por año con las claves
    ``anio`` (entero) y ``num_inversiones`` (entero ``>= 0`` y ``<= 999_999``).

    Los años cuyo valor es inválido (vacío, no numérico, no entero, negativo o
    superior a ``999_999``) se excluyen de la salida y se registran por consola
    en español, identificando la fila y el valor rechazado, sin interrumpir el
    procesamiento de los años restantes (Req 4.2, 4.6).

    Args:
        df: DataFrame leído por :func:`lee_inversiones` (columnas Codi,
            Descripció, 2020..2025).

    Returns:
        Lista de diccionarios ``{"anio": int, "num_inversiones": int}``, uno por
        cada año con valor válido.
    """
    if "Descripció" not in df.columns:
        print(
            "[ERROR] El archivo de inversiones no contiene la columna "
            "'Descripció'. No se puede normalizar; se devuelve lista vacía."
        )
        return []

    if df.empty:
        print(
            "[AVISO] El archivo de inversiones no contiene filas de datos; "
            "se devuelve lista vacía."
        )
        return []

    # Columnas de año presentes en el DataFrame (respetando el rango esperado).
    columnas_presentes = [
        anio for anio in ANIOS_ESPERADOS
        if str(anio) in df.columns or anio in df.columns
    ]
    faltantes = [anio for anio in ANIOS_ESPERADOS if anio not in columnas_presentes]
    if faltantes:
        print(
            "[AVISO] Faltan columnas de año esperadas en el archivo de "
            f"inversiones: {faltantes}. Esas columnas se omitirán."
        )

    registros: list[dict] = []

    # La fuente tiene una sola fila con el número de inversiones; se procesa esa
    # fila (si hubiera más, se procesan todas para no perder datos).
    for indice, fila in df.iterrows():
        for anio in ANIOS_ESPERADOS:
            # Localiza la columna del año, sea de tipo str o int.
            if str(anio) in df.columns:
                clave = str(anio)
            elif anio in df.columns:
                clave = anio
            else:
                continue

            valor_crudo = fila[clave]
            num_inversiones = _a_entero_no_negativo(valor_crudo)
            if num_inversiones is None:
                print(
                    f"[ERROR] Fila {indice} (año {anio}): número de inversiones "
                    f"inválido ('{valor_crudo}'). Se excluye ese registro."
                )
                continue

            registros.append(
                {
                    "anio": int(anio),
                    "num_inversiones": num_inversiones,
                }
            )

    print(
        f"[OK] Normalización ancho a largo completada: {len(registros)} "
        "registro(s) válidos generados."
    )
    return registros


def anota_gobernanza(registros: list[dict], fecha_prueba: str) -> list[dict]:
    """Añade los metadatos de gobernanza a cada registro de inversiones.

    A cada registro le adjunta ``fuente`` (=``FUENTE_INVERSIONES``),
    ``vigencia`` (=año del registro, como texto), ``fecha_prueba`` y ``linaje``
    con valor OBSERVADO, garantizando que ninguna cifra de inversiones salga sin
    su procedencia (Req 4.4, 10.4). No altera las claves de dominio existentes
    (``anio``, ``num_inversiones``); sólo agrega las de gobernanza.

    Args:
        registros: registros de inversiones normalizados
            (``{"anio", "num_inversiones"}``).
        fecha_prueba: fecha (ISO) en que se verificó/procesó el dato.

    Returns:
        La lista de registros, cada uno enriquecido con ``fuente``,
        ``vigencia``, ``fecha_prueba`` y ``linaje`` = OBSERVADO.
    """
    for registro in registros:
        registro["fuente"] = FUENTE_INVERSIONES
        # La vigencia es el año del propio registro, expresado como texto.
        registro["vigencia"] = str(registro.get("anio", ""))
        registro["fecha_prueba"] = fecha_prueba
        registro["linaje"] = gobernanza.LINAJE_OBSERVADO

    print(
        f"[OK] Gobernanza anotada en {len(registros)} registro(s) de "
        f"inversiones (fuente OBSERVADO, fecha de prueba {fecha_prueba})."
    )
    return registros

# --- Sub-tarea 2.3: orquestación del procesamiento de inversiones ----------
import datetime

# Ruta del CSV crudo de inversiones inmobiliarias, relativa a scripts/.
RUTA_ENTRADA = (
    "../datos_crudos/"
    "estadistica_2729_immobiliàries_nombre_d'inversions_immobiliàries.csv"
)

# Ruta de salida del CSV procesado, relativa a scripts/.
RUTA_SALIDA = "../datos_procesados/inversiones_inmobiliarias.csv"

# Columnas de la tabla procesada inversiones_inmobiliarias.csv, en orden.
COLUMNAS_SALIDA = [
    "anio",
    "num_inversiones",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def procesa(fecha_prueba: str) -> None:
    """Orquesta el procesamiento completo de las inversiones inmobiliarias.

    Lee el CSV crudo (``RUTA_ENTRADA``), lo normaliza de formato ancho a largo
    (un registro por año), anota la gobernanza (linaje OBSERVADO), filtra los
    registros con gobernanza completa y escribe el resultado en ``RUTA_SALIDA``
    con separador ``;`` y UTF-8.

    Ante un archivo de entrada inexistente o ilegible, :func:`lee_inversiones`
    lanza una excepción; aquí se captura para abortar limpiamente sin escribir
    salida parcial (Req 4.5). Las rutas son relativas a ``scripts/``, según la
    convención del repositorio (Req 4.3).

    Args:
        fecha_prueba: fecha (ISO) en que se verificó/procesó el dato.
    """
    print("[INICIO] Procesamiento de inversiones inmobiliarias.")

    # 1) Lectura del crudo. Si falla, abortar sin escribir salida (Req 4.5).
    try:
        df = lee_inversiones(RUTA_ENTRADA)
    except Exception:
        print(
            "[ABORTADO] No se pudo leer el archivo de inversiones; no se "
            "escribe ninguna salida."
        )
        return

    # 2) Normalización ancho→largo (excluye años inválidos, Req 4.2/4.6).
    registros = normaliza_ancho_a_largo(df)

    # 3) Anotación de gobernanza (linaje OBSERVADO, Req 4.4).
    registros = anota_gobernanza(registros, fecha_prueba)

    # 4) Filtrado de registros con gobernanza completa (Req 4.3).
    registros_validos = gobernanza.filtra_registros_validos(
        registros, "inversiones"
    )

    # 5) Escritura segura en datos_procesados/ (Req 4.3).
    gobernanza.escribe_csv(registros_validos, RUTA_SALIDA, COLUMNAS_SALIDA)

    print(
        f"[FIN] Procesamiento de inversiones completado: "
        f"{len(registros_validos)} registro(s) escritos en '{RUTA_SALIDA}'."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
