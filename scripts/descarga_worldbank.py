"""Extractor ético de economía de World Bank Open Data (tramo Lago).

Este módulo descarga desde la API v2 del Banco Mundial (World Bank Open Data)
los indicadores macroeconómicos reales para Andorra (país ``AD``) y guarda,
por indicador, el JSON crudo tal cual en ``datos_crudos/worldbank_<codigo>.json``.

Junto a ``descarga_limites_parroquias.py``, es uno de los únicos scripts del
proyecto que escriben en ``datos_crudos/``, y lo hacen solamente para CREAR
archivos nuevos, sin modificar, sobrescribir ni eliminar ninguno de los crudos
existentes (que son la fuente de verdad, P2).

La API v2 del Banco Mundial devuelve, por indicador, un array JSON de dos
elementos ``[metadata, observaciones]``. Este extractor NO interpreta ni
transforma el contenido: guarda el JSON crudo completo para que
``procesa_economia.py`` lo normalice aguas abajo (linaje OBSERVADO).

Convenciones de acceso ético a fuentes externas (Req 4.1-4.4, 4.8):
- Se envía un header ``User-Agent`` de navegador real para evitar bloqueos.
- Se aplica una pausa de cortesía con ``time.sleep()`` (>= 12 s) ANTES de cada
  petición, para no superar el límite de ~5 peticiones/minuto de la fuente.
- Se manejan explícitamente los códigos 200 / 429 / 406 / otros y se registra
  el resultado por consola en español.
- Ante un 429 se reintenta hasta 3 veces respetando ``Retry-After`` (o
  esperando al menos 60 s); nunca se guarda una descarga parcial.
- Ante un 406, otro código de error o un error de red, se documenta el hallazgo
  en la bitácora en lugar de forzar el acceso, y no se guarda nada.

Si el JSON del indicador ya existe en disco, el extractor NO vuelve a
descargarlo (idempotencia y cortesía con la fuente, Req 4.8). Este script NO
forma parte del pipeline de procesamiento (P6): se ejecuta aparte y bajo
demanda.

Licencia de la fuente: CC BY 4.0 (atribución). Fuente a citar: *Banco Mundial
(World Bank Open Data, API v2)*.

Los mensajes de consola van en español, coherentes con el resto del proyecto.
"""

import json
import os
import time

import requests

# Plantilla de URL de la API v2 del Banco Mundial para Andorra (país "AD").
# El marcador {codigo} se sustituye por el código del indicador; se pide JSON y
# el rango de años 2015–2024 (Req 4.1).
URL_PLANTILLA = (
    "https://api.worldbank.org/v2/country/AD/indicator/"
    "{codigo}?format=json&date=2015:2024"
)

# Indicadores a integrar (código World Bank -> (nombre, unidad)). Todos reales
# para Andorra. Esta estructura (dict código -> tupla (nombre, unidad)) la
# importa ``procesa_economia.py`` tal cual; se mantiene carácter a carácter para
# que coincida con su fallback local (Req 4.5).
INDICADORES = {
    "NY.GDP.MKTP.CD": ("PIB (US$ corrientes)", "US$"),
    "FP.CPI.TOTL.ZG": ("Inflación, IPC", "% anual"),
    "NY.GDP.PCAP.CD": ("PIB per cápita", "US$"),
    "SP.POP.TOTL": ("Población total", "personas"),
}

# User-Agent de navegador real para identificarnos ante el servidor y evitar
# bloqueos anti-bot (403/406) (Req 4.1).
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Pausa de cortesía (en segundos) ANTES de cada petición. >= 12 s garantiza no
# superar el límite de ~5 peticiones/minuto de la fuente (Req 4.1, 4.2).
PAUSA_CORTESIA_S = 12

# Número máximo de reintentos ante un HTTP 429 (Req 4.3).
MAX_REINTENTOS_429 = 3

# Tiempo máximo de espera de la respuesta HTTP, en segundos (Req 4.1).
TIMEOUT_HTTP_S = 30

# Espera mínima (en segundos) entre reintentos tras un HTTP 429 cuando la
# fuente no indica un ``Retry-After`` utilizable (Req 4.3).
ESPERA_MINIMA_429_S = 60

# Ruta de la bitácora donde se documenta la descarga, su licencia y los
# eventuales bloqueos, relativa a la carpeta scripts/.
RUTA_BITACORA = "../documentacion_bitacora/6_descarga_worldbank.md"


def ruta_crudo(codigo: str) -> str:
    """Devuelve la ruta del JSON crudo de un indicador, relativa a scripts/.

    Args:
        codigo: código del indicador World Bank (p. ej. ``NY.GDP.MKTP.CD``).

    Returns:
        Ruta ``../datos_crudos/worldbank_<codigo>.json``.
    """
    return f"../datos_crudos/worldbank_{codigo}.json"


def ya_descargado(codigo: str) -> bool:
    """Indica si el JSON crudo del indicador ya existe en disco.

    Base de la idempotencia (Req 4.8): si el archivo ya existe, el extractor no
    vuelve a descargarlo, por cortesía con la fuente. Un archivo ausente
    devuelve ``False`` para que se intente la descarga.

    Args:
        codigo: código del indicador World Bank (p. ej. ``NY.GDP.MKTP.CD``).

    Returns:
        ``True`` si ``worldbank_<codigo>.json`` ya existe; ``False`` en otro caso.
    """
    return os.path.isfile(ruta_crudo(codigo))


def _documenta_bloqueo_bitacora(motivo: str) -> None:
    """Registra en la bitácora un bloqueo o fallo de la descarga de un indicador.

    Deja constancia del hallazgo (p. ej. un 429 agotado, un 406 o un error de
    red) en lugar de forzar el acceso, coherente con las convenciones del
    proyecto. No interrumpe la ejecución si la bitácora no puede escribirse.

    Args:
        motivo: descripción en español del bloqueo o fallo observado.
    """
    entrada = (
        "\n## Hallazgo de descarga ({})\n\n"
        "- Fuente: Banco Mundial (World Bank Open Data, API v2).\n"
        "- Licencia: CC BY 4.0 (atribución).\n"
        "- Linaje: OBSERVADO (organismo internacional oficial).\n"
        "- Resultado: {}\n"
        "- Decisión: no se fuerza el acceso; no se guarda ninguna descarga "
        "parcial. El procesamiento de economía tolera la ausencia del JSON.\n"
    ).format(time.strftime("%Y-%m-%d %H:%M:%S"), motivo)
    try:
        os.makedirs(os.path.dirname(RUTA_BITACORA), exist_ok=True)
        # Se añade al final para conservar el histórico de intentos.
        with open(RUTA_BITACORA, "a", encoding="utf-8") as bitacora:
            bitacora.write(entrada)
        print(f"   Hallazgo documentado en la bitácora: {RUTA_BITACORA}")
    except OSError as err:
        print(f"   Aviso: no se pudo escribir en la bitácora ({err}).")


def descarga_indicador(codigo: str) -> bool:
    """Descarga el JSON crudo de un indicador de World Bank (Peticion_Etica).

    Realiza una petición ``GET`` a ``URL_PLANTILLA`` con las cabeceras
    ``User-Agent`` de navegador real y ``Accept: application/json``, aplicando
    la pausa de cortesía ``PAUSA_CORTESIA_S`` (>= 12 s) ANTES de la petición y
    un ``timeout`` de ``TIMEOUT_HTTP_S`` segundos (Req 4.1).

    Maneja explícitamente los códigos y registra en español el HTTP recibido:

    - 200: valida que el contenido sea JSON, crea el directorio de salida de
      forma idempotente (``os.makedirs(..., exist_ok=True)``), guarda el JSON
      crudo en ``datos_crudos/worldbank_<codigo>.json`` y devuelve ``True``.
    - 429: reintenta hasta ``MAX_REINTENTOS_429`` veces, respetando el tiempo
      indicado en ``Retry-After`` o esperando al menos ``ESPERA_MINIMA_429_S``
      (60 s) entre reintentos (Req 4.3); nunca guarda una descarga parcial.
    - 406, otro código de error o error de red: registra el hallazgo en la
      bitácora, no guarda nada y devuelve ``False`` (Req 4.4).

    Nunca modifica, sobrescribe ni elimina otros archivos de ``datos_crudos/``:
    solo crea el archivo nuevo del indicador (P2).

    Args:
        codigo: código del indicador World Bank (p. ej. ``NY.GDP.MKTP.CD``).

    Returns:
        ``True`` solo si se guardó el JSON crudo; ``False`` en cualquier otro
        caso (bloqueo, error de red o contenido no JSON).
    """
    url = URL_PLANTILLA.format(codigo=codigo)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    for intento in range(1, MAX_REINTENTOS_429 + 1):
        # Pausa de cortesía ANTES de cada petición para respetar el límite de
        # tasa de la fuente (~5 peticiones/minuto) (Req 4.1, 4.2).
        print(
            f"Pausa de cortesía de {PAUSA_CORTESIA_S} segundos antes de "
            f"consultar World Bank para el indicador «{codigo}»..."
        )
        time.sleep(PAUSA_CORTESIA_S)

        print(f"Descargando indicador «{codigo}» desde World Bank: {url}")
        try:
            respuesta = requests.get(
                url,
                headers=headers,
                timeout=TIMEOUT_HTTP_S,
            )
        except requests.exceptions.RequestException as err:
            motivo = (
                f"Error de red al contactar World Bank para «{codigo}» "
                f"({url}): {err}"
            )
            print(f"   ✖ {motivo}")
            _documenta_bloqueo_bitacora(motivo)
            return False

        codigo_http = respuesta.status_code
        print(
            f"   Código HTTP recibido de World Bank («{codigo}»): {codigo_http}"
        )

        if codigo_http == 200:
            # Se valida que el contenido sea JSON antes de guardar nada.
            try:
                datos = respuesta.json()
            except ValueError as err:
                motivo = (
                    f"Respuesta 200 para «{codigo}» pero el contenido no es "
                    f"JSON válido: {err}"
                )
                print(f"   ✖ {motivo}")
                _documenta_bloqueo_bitacora(motivo)
                return False

            ruta_salida = ruta_crudo(codigo)
            # Creación idempotente del directorio de salida; solo se crea el
            # archivo nuevo del indicador, sin tocar otros crudos (P2).
            os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
            with open(ruta_salida, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False)
            print(
                f"   ✓ Indicador «{codigo}» guardado en: {ruta_salida}"
            )
            return True

        if codigo_http == 429:
            # Límite de peticiones: respeta Retry-After si viene; si no, espera
            # al menos ESPERA_MINIMA_429_S (60 s) antes de reintentar (Req 4.3).
            espera = ESPERA_MINIMA_429_S
            cabecera_retry = respuesta.headers.get("Retry-After")
            if cabecera_retry is not None:
                try:
                    espera = max(ESPERA_MINIMA_429_S, int(cabecera_retry))
                except (TypeError, ValueError):
                    espera = ESPERA_MINIMA_429_S
            if intento < MAX_REINTENTOS_429:
                print(
                    f"   ⚠ Límite de peticiones (HTTP 429) para «{codigo}». "
                    f"Reintento {intento} de {MAX_REINTENTOS_429 - 1}; "
                    f"espera de {espera} segundos."
                )
                time.sleep(espera)
                continue
            motivo = (
                f"Límite de peticiones (HTTP 429) para «{codigo}» tras "
                f"{MAX_REINTENTOS_429} intentos. No se guarda descarga parcial."
            )
            print(f"   ⚠ {motivo}")
            _documenta_bloqueo_bitacora(motivo)
            return False

        if codigo_http == 406:
            motivo = (
                f"Error HTTP 406 (No Aceptable) para «{codigo}» ({url}). No se "
                "guarda nada."
            )
            print(f"   ✖ {motivo}")
            _documenta_bloqueo_bitacora(motivo)
            return False

        # Cualquier otro código se maneja como error explícito.
        motivo = (
            f"Error al descargar «{codigo}» desde World Bank (código HTTP "
            f"{codigo_http}). No se guarda nada."
        )
        print(f"   ✖ {motivo}")
        _documenta_bloqueo_bitacora(motivo)
        return False

    return False


def main() -> int:
    """Orquesta la descarga ética e idempotente de los indicadores de World Bank.

    Recorre ``INDICADORES`` y, para cada código:

    - Si el JSON ya existe, informa y lo omite (idempotencia, Req 4.8).
    - Si no existe, intenta la descarga ética con ``descarga_indicador``,
      aplicando la pausa de cortesía entre indicadores.

    Este script NO forma parte del pipeline de procesamiento (P6): se ejecuta
    aparte y bajo demanda. Nunca modifica otros crudos.

    Devuelve ``0`` si todos los indicadores quedan disponibles (recién
    descargados o previos) y un código ``!= 0`` igual al número de indicadores
    que no se pudieron obtener.
    """
    print("--- Descarga ética de economía (World Bank Open Data, API v2) ---")
    print(
        "Fuente: Banco Mundial (World Bank Open Data, API v2). "
        "Licencia: CC BY 4.0 (atribución). Linaje: OBSERVADO."
    )

    fallidos = 0
    for codigo in INDICADORES:
        print(f"\n=== Indicador «{codigo}» ===")
        if ya_descargado(codigo):
            print(
                f"El JSON del indicador «{codigo}» ya existe; no se vuelve a "
                f"descargar (idempotencia): {ruta_crudo(codigo)}"
            )
            continue

        if not descarga_indicador(codigo):
            print(
                f"No se pudo obtener el indicador «{codigo}». El procesamiento "
                "de economía tolerará su ausencia."
            )
            fallidos += 1

    if fallidos == 0:
        print(
            "\nDescarga finalizada correctamente: todos los indicadores "
            "disponibles (descargados o previos)."
        )
    else:
        print(
            f"\nDescarga finalizada con {fallidos} indicador(es) no "
            "disponible(s). Se documentaron los hallazgos en la bitácora."
        )
    return fallidos


if __name__ == "__main__":
    raise SystemExit(main())
