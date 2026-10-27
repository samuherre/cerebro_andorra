"""Procesamiento de población por parròquia (tramo Lago).

Este módulo lee el CSV crudo de población por parròquia del Departament
d'Estadística d'Andorra, lo normaliza de formato ancho a largo, le anota la
gobernanza (linaje OBSERVADO) y escribe el resultado en ``datos_procesados/``.

Sub-tarea 2.1: lectura del CSV de población con manejo de errores.
Sub-tarea 2.2: transformación de formato ancho (años en columnas) a largo
(un registro por parròquia y año).
Los mensajes de consola van en español, coherentes con el resto del proyecto.
"""

import pandas as pd

# Fuente oficial del dato de población (linaje OBSERVADO).
FUENTE_POBLACION = "Departament d'Estadística d'Andorra (estadistica_id798)"

# Prefijo que antecede al nombre de la parròquia en la columna 'Descripció'.
PREFIJO_DESCRIPCION = "POBLACIÓ PER PARRÒQUIA."

# Sufijo exacto de la fila agregada que NO representa una parròquia concreta.
SUFIJO_TOTAL = "TOTAL"

# Rango de años esperado en las columnas del CSV crudo (Req 1.2).
ANIOS_ESPERADOS = [2020, 2021, 2022, 2023, 2024, 2025]

# Mapa de nombres crudos (en mayúsculas) al nombre canónico de cada parròquia,
# tal como se define en el glosario de requisitos. Permite normalizar la
# capitalización sin perder los signos diacríticos catalanes.
NOMBRES_CANONICOS = {
    "CANILLO": "Canillo",
    "ENCAMP": "Encamp",
    "ORDINO": "Ordino",
    "LA MASSANA": "La Massana",
    "ANDORRA LA VELLA": "Andorra la Vella",
    "SANT JULIÀ DE LÒRIA": "Sant Julià de Lòria",
    "ESCALDES-ENGORDANY": "Escaldes-Engordany",
}


def lee_poblacion(ruta_entrada: str) -> pd.DataFrame:
    """Lee el CSV de población usando separador ``;`` y codificación UTF-8.

    Ante un archivo inexistente o ilegible, registra un mensaje de error en
    español por consola indicando el archivo afectado y aborta sin escribir
    ninguna salida, propagando la excepción para que la orquestación finalice
    sin crear un archivo parcial (Req 1.1, 1.6, 9.3).

    Args:
        ruta_entrada: Ruta al CSV crudo de población por parròquia.

    Returns:
        DataFrame con el contenido del CSV leído.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta indicada.
        Exception: Si el archivo existe pero no puede leerse o parsearse.
    """
    try:
        df = pd.read_csv(ruta_entrada, sep=";", encoding="utf-8")
    except FileNotFoundError:
        print(
            f"[ERROR] No se encontró el archivo de población: '{ruta_entrada}'. "
            "Se aborta el procesamiento sin escribir salida."
        )
        raise
    except Exception as error:
        print(
            f"[ERROR] No se pudo leer el archivo de población '{ruta_entrada}': "
            f"{error}. Se aborta el procesamiento sin escribir salida."
        )
        raise

    print(
        f"[OK] Archivo de población leído: '{ruta_entrada}' "
        f"({len(df)} filas, {len(df.columns)} columnas)."
    )
    return df

def _extrae_nombre_parroquia(descripcion: str) -> str:
    """Extrae el nombre de la parròquia desde la columna 'Descripció'.

    Elimina el prefijo ``POBLACIÓ PER PARRÒQUIA.`` y los espacios sobrantes.
    Devuelve el sufijo restante en mayúsculas (tal como viene en el crudo);
    por ejemplo ``"POBLACIÓ PER PARRÒQUIA. CANILLO"`` -> ``"CANILLO"``.

    Args:
        descripcion: Valor de la columna 'Descripció' de una fila.

    Returns:
        El nombre crudo de la parròquia (o "TOTAL" para la fila agregada).
    """
    texto = str(descripcion).strip()
    if texto.upper().startswith(PREFIJO_DESCRIPCION):
        texto = texto[len(PREFIJO_DESCRIPCION):]
    return texto.strip()


def _a_poblacion_entera(valor) -> int | None:
    """Convierte un valor de población a entero no negativo.

    Devuelve ``None`` si el valor es vacío, no numérico o negativo, para que
    la fila afectada pueda excluirse y registrarse (Req 1.7).

    Args:
        valor: Valor crudo de la celda de población.

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
        # Un decimal no entero (p.ej. 4422.5) no es una población válida.
        return None
    return int(numero)


def normaliza_ancho_a_largo(df: pd.DataFrame) -> list[dict]:
    """Transforma el DataFrame de formato ancho a formato largo.

    El crudo tiene un registro por parròquia con las poblaciones en columnas de
    año (2020..2025). Esta función produce un registro por cada combinación de
    (parròquia, año), con las claves ``parroquia`` (nombre canónico), ``anio``
    (entero) y ``poblacion`` (entero >= 0).

    La fila cuyo sufijo de 'Descripció' es exactamente ``TOTAL`` se excluye de
    la salida pero se conserva en memoria (no se devuelve) para la posterior
    verificación de la propiedad "suma de parròquies = total" (Req 1.2).

    Las filas con población no numérica, negativa, vacía o con columnas de año
    faltantes se excluyen de la salida y se registran por consola en español
    indicando la fila afectada (Req 1.7).

    Args:
        df: DataFrame leído por :func:`lee_poblacion` (columnas Codi,
            Descripció, 2020..2025).

    Returns:
        Lista de diccionarios ``{"parroquia": str, "anio": int,
        "poblacion": int}``, uno por cada (parròquia, año) válido.
    """
    if "Descripció" not in df.columns:
        print(
            "[ERROR] El archivo de población no contiene la columna "
            "'Descripció'. No se puede normalizar; se devuelve lista vacía."
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
            f"población: {faltantes}. Esas columnas se omitirán."
        )

    registros: list[dict] = []
    fila_total: dict | None = None  # Se conserva en memoria para verificación.

    for indice, fila in df.iterrows():
        nombre_crudo = _extrae_nombre_parroquia(fila["Descripció"])

        # La fila TOTAL se aparta: se conserva en memoria y no se emite.
        if nombre_crudo.upper() == SUFIJO_TOTAL:
            fila_total = fila.to_dict()
            continue

        nombre_canonico = NOMBRES_CANONICOS.get(nombre_crudo.upper())
        if nombre_canonico is None:
            print(
                f"[ERROR] Fila {indice}: parròquia no reconocida "
                f"('{nombre_crudo}'). Se excluye de la salida."
            )
            continue

        for anio in ANIOS_ESPERADOS:
            # Localiza la columna del año, sea de tipo str o int.
            if str(anio) in df.columns:
                clave = str(anio)
            elif anio in df.columns:
                clave = anio
            else:
                print(
                    f"[ERROR] Fila {indice} ({nombre_canonico}): falta la "
                    f"columna del año {anio}. Se excluye ese registro."
                )
                continue

            poblacion = _a_poblacion_entera(fila[clave])
            if poblacion is None:
                print(
                    f"[ERROR] Fila {indice} ({nombre_canonico}, año {anio}): "
                    f"población inválida ('{fila[clave]}'). Se excluye ese "
                    "registro."
                )
                continue

            registros.append(
                {
                    "parroquia": nombre_canonico,
                    "anio": int(anio),
                    "poblacion": poblacion,
                }
            )

    if fila_total is None:
        print(
            "[AVISO] No se encontró la fila TOTAL en el archivo de población; "
            "no se podrá verificar la suma de parròquies contra el total."
        )

    print(
        f"[OK] Normalización ancho a largo completada: {len(registros)} "
        "registros válidos generados."
    )
    return registros


# --- Sub-tarea 2.3: anotación de gobernanza y orquestación -----------------
import datetime

import gobernanza

# Ruta del CSV crudo de población por parròquia, relativa a scripts/.
RUTA_ENTRADA = "../datos_crudos/estadistica_id798_població_població_per_parròquia.csv"

# Ruta de salida del CSV procesado, relativa a scripts/.
RUTA_SALIDA = "../datos_procesados/poblacion_parroquia.csv"

# Columnas de la tabla procesada poblacion_parroquia.csv, en orden (design.md).
COLUMNAS_SALIDA = [
    "parroquia",
    "anio",
    "poblacion",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def anota_gobernanza(registros: list[dict], fecha_prueba: str) -> list[dict]:
    """Añade los metadatos de gobernanza a cada registro de población.

    A cada registro le adjunta ``fuente`` (=``FUENTE_POBLACION``), ``vigencia``
    (=año del registro, como texto), ``fecha_prueba`` y ``linaje`` con valor
    OBSERVADO, garantizando que ninguna cifra de población salga sin su
    procedencia (Req 3.4). No altera las claves existentes del registro
    (``parroquia``, ``anio``, ``poblacion``); sólo agrega las de gobernanza.

    Args:
        registros: registros de población normalizados
            (``{"parroquia", "anio", "poblacion"}``).
        fecha_prueba: fecha (ISO) en que se verificó/procesó el dato.

    Returns:
        La lista de registros, cada uno enriquecido con ``fuente``,
        ``vigencia``, ``fecha_prueba`` y ``linaje`` = OBSERVADO.
    """
    for registro in registros:
        registro["fuente"] = FUENTE_POBLACION
        # La vigencia es el año del propio registro, expresado como texto.
        registro["vigencia"] = str(registro.get("anio", ""))
        registro["fecha_prueba"] = fecha_prueba
        registro["linaje"] = gobernanza.LINAJE_OBSERVADO

    print(
        f"[OK] Gobernanza anotada en {len(registros)} registro(s) de población "
        f"(fuente OBSERVADO, fecha de prueba {fecha_prueba})."
    )
    return registros


def procesa(fecha_prueba: str) -> None:
    """Orquesta el procesamiento completo de la población por parròquia.

    Lee el CSV crudo (``RUTA_ENTRADA``), lo normaliza de ancho a largo, anota la
    gobernanza (linaje OBSERVADO), filtra los registros con gobernanza completa
    y escribe el resultado en ``RUTA_SALIDA`` con separador ``;`` y UTF-8.

    Ante un archivo de entrada inexistente o ilegible, :func:`lee_poblacion`
    lanza una excepción; aquí se captura para abortar limpiamente sin escribir
    salida parcial (Req 1.6). Las rutas son relativas a ``scripts/``, según la
    convención del repositorio (Req 1.1, 1.2, 1.4, 3.4).

    Args:
        fecha_prueba: fecha (ISO) en que se verificó/procesó el dato.
    """
    print("[INICIO] Procesamiento de población por parròquia.")

    # 1) Lectura del crudo. Si falla, abortar sin escribir salida (Req 1.6).
    try:
        df = lee_poblacion(RUTA_ENTRADA)
    except Exception:
        print(
            "[ABORTADO] No se pudo leer el archivo de población; no se escribe "
            "ninguna salida."
        )
        return

    # 2) Normalización ancho→largo (excluye TOTAL y filas inválidas, Req 1.2/1.7).
    registros = normaliza_ancho_a_largo(df)

    # 3) Anotación de gobernanza (linaje OBSERVADO, Req 3.4).
    registros = anota_gobernanza(registros, fecha_prueba)

    # 4) Filtrado de registros con gobernanza completa (Req 3.5).
    registros_validos = gobernanza.filtra_registros_validos(registros, "poblacion")

    # 5) Escritura segura en datos_procesados/ (Req 1.4, 1.5).
    gobernanza.escribe_csv(registros_validos, RUTA_SALIDA, COLUMNAS_SALIDA)

    print(
        f"[FIN] Procesamiento de población completado: "
        f"{len(registros_validos)} registro(s) escritos en '{RUTA_SALIDA}'."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
