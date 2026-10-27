"""Módulo transversal de gobernanza de datos de Cerebro Andorra.

Concentra la lógica de gobernanza (metadatos de cifra, etiquetas de linaje y
validación) para que los procesadores de población, vivienda e inventario la
reutilicen. Cumple el principio rector del proyecto:
"0 cifras sin fuente, sin vigencia y sin fecha de prueba".

Mensajes de consola en español, coherentes con el resto del proyecto.
"""

import csv
import os

# --- Etiquetas de linaje permitidas ---------------------------------------
# Clasificación de gobernanza de un dato según su linaje y fiabilidad.
LINAJE_OBSERVADO = "OBSERVADO"  # dato oficial, censo o transacción real
LINAJE_ESTIMADO = "ESTIMADO"    # calibración o consenso del sector
LINAJE_PROXY = "PROXY"          # dato de mercado dinámico extraído de la web

# Conjunto de linajes válidos para validación rápida de pertenencia.
LINAJES_VALIDOS = {LINAJE_OBSERVADO, LINAJE_ESTIMADO, LINAJE_PROXY}

# --- Estados de dataset permitidos (inventario de fuentes) -----------------
ESTADOS_VALIDOS = {"integrado", "candidato", "caído", "excluido"}


def construye_metadato(fuente: str, vigencia: str, fecha_prueba: str) -> dict:
    """Construye el Metadato_Cifra con los tres campos obligatorios.

    Devuelve un diccionario con la fuente del dato, su vigencia (año o periodo
    al que corresponde) y la fecha de prueba (fecha en que se verificó o
    extrajo). No valida el contenido: la validación se realiza con
    ``metadato_completo``.

    Args:
        fuente: origen del dato (institución o portal).
        vigencia: año o periodo al que corresponde la cifra.
        fecha_prueba: fecha (ISO) en que se verificó o extrajo el dato.

    Returns:
        dict con las claves ``fuente``, ``vigencia`` y ``fecha_prueba``.
    """
    return {
        "fuente": fuente,
        "vigencia": vigencia,
        "fecha_prueba": fecha_prueba,
    }


def metadato_completo(registro: dict) -> bool:
    """Indica si un registro tiene el metadato de gobernanza completo.

    Un registro se considera completo cuando sus tres campos obligatorios
    (``fuente``, ``vigencia`` y ``fecha_prueba``) están presentes y no vacíos,
    y su ``linaje`` pertenece a ``LINAJES_VALIDOS`` (OBSERVADO/ESTIMADO/PROXY).

    Args:
        registro: diccionario que representa una cifra con sus metadatos.

    Returns:
        True si el metadato está completo y el linaje es válido; False en caso
        contrario.
    """
    if not isinstance(registro, dict):
        return False

    # Los tres campos obligatorios deben estar presentes y no vacíos.
    for campo in ("fuente", "vigencia", "fecha_prueba"):
        valor = registro.get(campo)
        if valor is None:
            return False
        if str(valor).strip() == "":
            return False

    # El linaje debe pertenecer al conjunto de linajes válidos.
    if registro.get("linaje") not in LINAJES_VALIDOS:
        return False

    return True


def _motivo_exclusion(registro: dict) -> str:
    """Determina, en español, por qué un registro no supera la gobernanza.

    Se usa para dejar constancia en la bitácora del motivo concreto de cada
    exclusión. Devuelve la primera causa detectada siguiendo el orden de los
    campos obligatorios y, por último, la validez del linaje.

    Args:
        registro: diccionario que representa una cifra con sus metadatos.

    Returns:
        Cadena en español describiendo el motivo de la exclusión.
    """
    if not isinstance(registro, dict):
        return "el registro no es un diccionario válido"

    etiquetas = {
        "fuente": "fuente",
        "vigencia": "vigencia",
        "fecha_prueba": "fecha de prueba",
    }
    for campo, etiqueta in etiquetas.items():
        valor = registro.get(campo)
        if valor is None or str(valor).strip() == "":
            return f"falta el campo obligatorio '{etiqueta}'"

    linaje = registro.get("linaje")
    if linaje not in LINAJES_VALIDOS:
        if linaje is None or str(linaje).strip() == "":
            return "falta la etiqueta de linaje (OBSERVADO/ESTIMADO/PROXY)"
        return (
            f"la etiqueta de linaje '{linaje}' no es válida "
            "(debe ser OBSERVADO, ESTIMADO o PROXY)"
        )

    return "motivo desconocido"


def filtra_registros_validos(registros: list[dict], contexto: str) -> list[dict]:
    """Filtra una colección conservando sólo los registros bien gobernados.

    Conserva únicamente los registros cuyo metadato de gobernanza está completo
    y cuyo linaje es válido (según ``metadato_completo``). Por cada registro
    excluido registra en la bitácora, mediante un mensaje en español por
    consola, el contexto y el motivo concreto de la exclusión, sin alterar los
    registros válidos restantes (Req 3.3, 3.5, 7.3).

    Args:
        registros: colección de registros (dicts) candidatos a la salida.
        contexto: descripción del origen de los registros (p. ej. "población")
            para identificar en la bitácora dónde se produjo la exclusión.

    Returns:
        Lista con los registros que superan la validación de gobernanza, en el
        mismo orden en que aparecían en la entrada.
    """
    validos: list[dict] = []
    excluidos = 0

    for indice, registro in enumerate(registros):
        if metadato_completo(registro):
            validos.append(registro)
        else:
            excluidos += 1
            motivo = _motivo_exclusion(registro)
            print(
                f"[gobernanza:{contexto}] Registro #{indice} excluido: {motivo}."
            )

    if excluidos:
        print(
            f"[gobernanza:{contexto}] Se excluyeron {excluidos} registro(s) sin "
            f"gobernanza completa; se conservaron {len(validos)}."
        )

    return validos


class EscrituraEnCrudosError(Exception):
    """Se lanza al intentar escribir dentro de ``datos_crudos/``.

    Los datos crudos son la fuente de verdad del proyecto y deben quedar
    intactos; cualquier intento de escritura sobre ellos se rechaza (Req 1.4,
    9.3).
    """


def _es_ruta_en_crudos(ruta_salida: str) -> bool:
    """Indica si ``ruta_salida`` cae dentro de un directorio ``datos_crudos``.

    Normaliza la ruta a absoluta y comprueba, componente a componente, si
    alguno de los directorios del recorrido es ``datos_crudos``. De este modo
    detecta tanto rutas relativas (``../datos_crudos/x.csv``) como absolutas,
    sin depender del separador de la plataforma.

    Args:
        ruta_salida: ruta del archivo CSV que se pretende escribir.

    Returns:
        True si la ruta apunta a algún nivel dentro de ``datos_crudos/``.
    """
    ruta_absoluta = os.path.abspath(ruta_salida)
    # El último componente es el propio archivo; el resto son directorios.
    directorio = os.path.dirname(ruta_absoluta)
    partes = directorio.replace("\\", "/").split("/")
    return "datos_crudos" in partes


def escribe_csv(
    registros: list[dict], ruta_salida: str, columnas: list[str]
) -> None:
    """Escribe una colección de registros en un CSV de forma segura.

    Garantiza las convenciones de datos del proyecto: separador ``;`` y
    codificación UTF-8. Crea el directorio de salida de forma idempotente con
    ``os.makedirs(exist_ok=True)`` antes de escribir (Req 1.5) y nunca escribe
    dentro de ``datos_crudos/``, que debe permanecer intacto como fuente de
    verdad (Req 1.4, 9.3). Cada registro aporta sus valores según ``columnas``;
    las claves ausentes se escriben como cadena vacía.

    Args:
        registros: colección de registros (dicts) a volcar en el CSV.
        ruta_salida: ruta del archivo CSV de destino.
        columnas: nombres de las columnas y su orden en la cabecera.

    Raises:
        EscrituraEnCrudosError: si la ruta de salida apunta a ``datos_crudos/``.
    """
    # Protección de la fuente de verdad: jamás escribir sobre los crudos.
    if _es_ruta_en_crudos(ruta_salida):
        mensaje = (
            f"[gobernanza] Escritura rechazada: la ruta '{ruta_salida}' está "
            "dentro de 'datos_crudos/', que debe permanecer intacto como "
            "fuente de verdad."
        )
        print(mensaje)
        raise EscrituraEnCrudosError(mensaje)

    # Crear el directorio de salida de forma idempotente antes de escribir.
    directorio = os.path.dirname(os.path.abspath(ruta_salida))
    os.makedirs(directorio, exist_ok=True)

    with open(ruta_salida, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas,
            delimiter=";",
            extrasaction="ignore",
            restval="",
        )
        escritor.writeheader()
        for registro in registros:
            escritor.writerow(registro)

    print(
        f"[gobernanza] Escritos {len(registros)} registro(s) en "
        f"'{ruta_salida}' (separador ';', UTF-8)."
    )
