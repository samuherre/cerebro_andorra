"""Procesamiento del salario medio por sector de actividad (tramo Lago).

Este módulo lee el CSV crudo del salario medio mensual por sector de actividad
(nivel 1) del Departament d'Estadística d'Andorra (``oficial_2844``), toma para
cada sector el salario del periodo mensual más reciente con dato válido, le
anota la gobernanza (linaje OBSERVADO) y escribe el resultado en
``datos_procesados/salario_sector.csv``.

La fuente responde a la pregunta de usuario "¿En qué sectores trabaja la gente
y cuánto se gana en cada uno?": un registro por sector de actividad (comercio,
hostelería, construcción, sistema financiero, etc.) con su salario medio
mensual en euros.

Estructura del crudo (separador ``;``, UTF-8):
- Columna ``Codi``: código del indicador.
- Columna ``Descripció``: "SALARI MEDIÀ PER SECTOR D'ACTIVITAT (NIVELL 1). <LETRA>-<SECTOR>".
- Columnas de periodo mensual: ``2018/01`` .. ``2025/12`` con el salario (€).

El procesamiento normaliza de formato ancho a largo (un registro por sector),
quedándose con el último periodo que tenga un salario estrictamente positivo
(un 0 indica un sector sin asalariados ese mes, no un salario real). Los
sectores cuyo valor es siempre 0 o inválido se excluyen y se registran por
consola.

Imita el patrón de ``procesa_inversiones.py`` y reutiliza ``gobernanza.py``.
Mensajes de consola en español, coherentes con el resto del proyecto.
"""

import datetime

import pandas as pd

import gobernanza

# Fuente oficial del dato de salario por sector (linaje OBSERVADO).
FUENTE_EMPLEO = (
    "Departament d'Estadística d'Andorra "
    "(oficial_2844, salari medià per sector d'activitat)"
)

# Prefijo de la Descripció que precede al nombre del sector.
_PREFIJO_DESCR = "SALARI MEDIÀ PER SECTOR D'ACTIVITAT (NIVELL 1)."

# Rango admitido para el salario medio mensual (€), inclusive. Un valor fuera
# de este rango se considera inválido (error de origen).
RANGO_SALARIO = (1.0, 50_000.0)

# Nombres legibles en español para cada letra de sector (CAEA nivel 1). Permite
# mostrar el sector sin la jerga en catalán/mayúsculas del crudo.
_NOMBRE_SECTOR_ES = {
    "A": "Agricultura, ganadería, caza y silvicultura",
    "B": "Pesca",
    "C": "Industrias extractivas",
    "D": "Industrias manufactureras",
    "E": "Energía eléctrica, gas y agua",
    "F": "Construcción",
    "G": "Comercio",
    "H": "Hostelería",
    "I": "Transporte y comunicaciones",
    "J": "Sistema financiero",
    "K": "Actividades inmobiliarias y servicios a empresas",
    "L": "Administración pública y seguridad social",
    "M": "Educación",
    "N": "Actividades sanitarias, veterinarias y servicios sociales",
    "O": "Otras actividades sociales y servicios personales",
    "P": "Hogares que emplean personal doméstico",
    "Q": "Organismos extraterritoriales",
    "T": "Trabajo doméstico en la comunidad",
    "Z": "Declarante voluntario sin actividad",
}

# Ruta del CSV crudo, relativa a scripts/.
RUTA_ENTRADA = "../datos_crudos/oficial_2844_salario_sector.csv"

# Ruta de salida del CSV procesado, relativa a scripts/.
RUTA_SALIDA = "../datos_procesados/salario_sector.csv"

# Columnas de la tabla procesada salario_sector.csv, en orden.
COLUMNAS_SALIDA = [
    "sector",
    "letra_sector",
    "salario_medio",
    "es_total",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def lee_salario_sector(ruta_entrada: str) -> pd.DataFrame:
    """Lee el CSV de salario por sector (separador ``;``, UTF-8).

    Ante un archivo inexistente, ilegible o sin las columnas esperadas
    (``Descripció`` y al menos una columna de periodo mensual) registra un
    mensaje de error en español por consola y propaga una excepción para abortar
    sin escribir una salida parcial.

    Args:
        ruta_entrada: ruta al CSV crudo de salario por sector.

    Returns:
        DataFrame con el contenido del CSV leído.

    Raises:
        FileNotFoundError: si el archivo no existe.
        ValueError: si faltan columnas esperadas.
        Exception: si el archivo no puede leerse/parsearse.
    """
    try:
        df = pd.read_csv(ruta_entrada, sep=";", encoding="utf-8", dtype=str)
    except FileNotFoundError:
        print(
            f"[ERROR] No se encontró el archivo de salario por sector: "
            f"'{ruta_entrada}'. Se aborta el procesamiento sin escribir salida."
        )
        raise
    except Exception as error:  # noqa: BLE001
        print(
            f"[ERROR] No se pudo leer el archivo de salario por sector "
            f"'{ruta_entrada}': {error}. Se aborta sin escribir salida."
        )
        raise

    columnas = set(df.columns)
    faltantes: list[str] = []
    if "Descripció" not in columnas:
        faltantes.append("Descripció")
    periodos = [c for c in df.columns if _es_columna_periodo(c)]
    if not periodos:
        faltantes.append("al menos una columna de periodo (AAAA/MM)")

    if faltantes:
        mensaje = (
            f"[ERROR] El archivo de salario por sector '{ruta_entrada}' no "
            f"contiene las columnas esperadas: {faltantes}. Se aborta sin "
            "escribir salida."
        )
        print(mensaje)
        raise ValueError(mensaje)

    print(
        f"[OK] Archivo de salario por sector leído: '{ruta_entrada}' "
        f"({len(df)} filas, {len(df.columns)} columnas, "
        f"{len(periodos)} periodo(s))."
    )
    return df


def _es_columna_periodo(nombre: str) -> bool:
    """Indica si una cabecera de columna es un periodo mensual ``AAAA/MM``."""
    texto = str(nombre).strip()
    if len(texto) != 7 or texto[4] != "/":
        return False
    anio, mes = texto[:4], texto[5:]
    return anio.isdigit() and mes.isdigit()


def _a_salario(valor) -> float | None:
    """Convierte una celda al salario medio en euros (float) o ``None``.

    Acepta el formato decimal con coma del crudo ("1753,88"). Devuelve ``None``
    para celdas vacías, no numéricas, o fuera del rango admitido. Un ``0`` se
    trata como ``None`` (sector sin asalariados ese mes, no un salario real).

    Args:
        valor: valor crudo de la celda.

    Returns:
        El salario (``float``) si es válido y estrictamente positivo; ``None``
        en cualquier otro caso.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    if texto == "":
        return None
    # El crudo usa coma decimal; normalizar a punto.
    texto = texto.replace(".", "").replace(",", ".") if texto.count(",") else texto
    try:
        numero = float(texto)
    except (ValueError, TypeError):
        return None
    minimo, maximo = RANGO_SALARIO
    if numero < minimo or numero > maximo:
        return None
    return round(numero, 2)


def _sector_de_descripcion(descripcion: str) -> "tuple[str, str] | None":
    """Extrae ``(letra, nombre_es)`` del campo ``Descripció`` de una fila.

    De "SALARI MEDIÀ PER SECTOR D'ACTIVITAT (NIVELL 1). G-COMERÇ" devuelve
    ``("G", "Comercio")``. Para la fila "... TOTAL" devuelve
    ``("TOTAL", "Total (todos los sectores)")``.

    Args:
        descripcion: texto del campo ``Descripció``.

    Returns:
        Tupla ``(letra_sector, nombre_es)`` o ``None`` si no se reconoce.
    """
    if descripcion is None:
        return None
    texto = str(descripcion).strip()
    if _PREFIJO_DESCR not in texto:
        return None
    resto = texto.split(_PREFIJO_DESCR, 1)[1].strip()
    if resto.upper() == "TOTAL":
        return ("TOTAL", "Total (todos los sectores)")
    # Formato "<LETRA>-<NOMBRE CA>". Tomamos la letra antes del primer guion.
    if "-" in resto:
        letra = resto.split("-", 1)[0].strip().upper()
    else:
        letra = resto[:1].upper()
    nombre_es = _NOMBRE_SECTOR_ES.get(letra)
    if nombre_es is None:
        return None
    return (letra, nombre_es)


def normaliza_a_sectores(df: pd.DataFrame) -> list[dict]:
    """Transforma el DataFrame ancho en un registro por sector.

    Para cada fila (sector) toma el salario del periodo mensual más reciente
    con un valor válido y estrictamente positivo, y construye un registro con
    ``sector`` (nombre en español), ``letra_sector``, ``salario_medio``,
    ``es_total`` y ``vigencia`` (el periodo del dato, p. ej. "2025/12"). Los
    sectores sin ningún periodo con salario positivo (p. ej. Pesca, siempre 0)
    se excluyen y se registran por consola.

    Args:
        df: DataFrame leído por :func:`lee_salario_sector`.

    Returns:
        Lista de diccionarios, uno por sector con dato válido, sin gobernanza.
    """
    if "Descripció" not in df.columns or df.empty:
        print(
            "[AVISO] El archivo de salario por sector no tiene datos "
            "utilizables; se devuelve lista vacía."
        )
        return []

    # Periodos ordenados ascendentemente para localizar el más reciente.
    periodos = sorted([c for c in df.columns if _es_columna_periodo(c)])

    registros: list[dict] = []
    for _, fila in df.iterrows():
        info = _sector_de_descripcion(fila.get("Descripció"))
        if info is None:
            continue
        letra, nombre_es = info

        # Buscar el último periodo (más reciente) con salario válido positivo.
        salario = None
        vigencia = None
        for periodo in reversed(periodos):
            candidato = _a_salario(fila.get(periodo))
            if candidato is not None:
                salario = candidato
                vigencia = periodo
                break

        if salario is None:
            print(
                f"[AVISO] Sector '{nombre_es}' ({letra}) sin ningún salario "
                "válido en la serie; se excluye."
            )
            continue

        registros.append(
            {
                "sector": nombre_es,
                "letra_sector": letra,
                "salario_medio": salario,
                "es_total": "1" if letra == "TOTAL" else "0",
                "vigencia": vigencia,
            }
        )

    print(
        f"[OK] Normalización por sector completada: {len(registros)} "
        "sector(es) con salario válido."
    )
    return registros


def anota_gobernanza(registros: list[dict], fecha_prueba: str) -> list[dict]:
    """Añade los metadatos de gobernanza a cada registro de salario.

    A cada registro le adjunta ``fuente`` (=``FUENTE_EMPLEO``), conserva su
    ``vigencia`` (periodo del dato), ``fecha_prueba`` y ``linaje`` OBSERVADO.

    Args:
        registros: registros de salario por sector normalizados.
        fecha_prueba: fecha (ISO) en que se verificó/procesó el dato.

    Returns:
        La lista de registros enriquecida con la gobernanza.
    """
    for registro in registros:
        registro["fuente"] = FUENTE_EMPLEO
        registro["fecha_prueba"] = fecha_prueba
        registro["linaje"] = gobernanza.LINAJE_OBSERVADO

    print(
        f"[OK] Gobernanza anotada en {len(registros)} registro(s) de salario "
        f"por sector (fuente OBSERVADO, fecha de prueba {fecha_prueba})."
    )
    return registros


def procesa(fecha_prueba: str) -> None:
    """Orquesta el procesamiento completo del salario por sector.

    Lee el crudo, normaliza a un registro por sector (último periodo con dato),
    anota la gobernanza (OBSERVADO), filtra los registros válidos y escribe el
    resultado en ``RUTA_SALIDA`` con separador ``;`` y UTF-8. Ante un crudo
    inexistente o ilegible, aborta limpiamente sin escribir salida parcial.

    Args:
        fecha_prueba: fecha (ISO) en que se verificó/procesó el dato.
    """
    print("[INICIO] Procesamiento de salario por sector de actividad.")

    try:
        df = lee_salario_sector(RUTA_ENTRADA)
    except Exception:  # noqa: BLE001
        print(
            "[ABORTADO] No se pudo leer el archivo de salario por sector; no "
            "se escribe ninguna salida."
        )
        return

    registros = normaliza_a_sectores(df)
    registros = anota_gobernanza(registros, fecha_prueba)
    registros_validos = gobernanza.filtra_registros_validos(registros, "empleo")
    gobernanza.escribe_csv(registros_validos, RUTA_SALIDA, COLUMNAS_SALIDA)

    print(
        f"[FIN] Procesamiento de salario por sector completado: "
        f"{len(registros_validos)} registro(s) escritos en '{RUTA_SALIDA}'."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
