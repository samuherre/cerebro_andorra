"""Orquestador del pipeline de procesamiento de Cerebro Andorra.

Ejecuta en orden los pasos del Pipeline_Procesamiento sobre los datos
crudos ya verificados de ``datos_crudos/`` y escribe los resultados en
``datos_procesados/``:

1. ``procesa_poblacion``            → ``poblacion_parroquia.csv``
2. ``procesa_vivienda``             → ``precios_vivienda.csv``
3. ``procesa_turismo``              → ``turismo.csv``
4. ``procesa_inversiones``          → ``inversiones_inmobiliarias.csv``
5. ``procesa_poblacion_desgloses``  → ``poblacion_desgloses.csv``
6. ``procesa_indicadores_sociales`` → ``umbrales_pobreza.csv`` / ``tasa_fecundidad.csv``
7. ``procesa_economia``             → ``economia_worldbank.csv``
8. ``genera_inventario``            → ``inventario_fuentes.csv``

Los extractores de red (World Bank, límites de parròquia) NO forman parte de
este pipeline: se ejecutan aparte y bajo demanda. La descarga del GeoJSON de
límites tampoco forma parte de este pipeline.

Cada paso comparte la misma firma ``procesa(fecha_prueba: str) -> None`` y se
ejecuta con la fecha de prueba de hoy (ISO). Todos los pasos son obligatorios:
si alguno lanza una excepción, el orquestador lo registra por consola en
español, continúa con los pasos restantes y devuelve un código de salida
distinto de 0 (Req 3.4, 9.3).

Convención del repositorio: el script se ejecuta desde ``scripts/`` y los
módulos importados escriben con rutas relativas ``../datos_procesados``.
"""

import datetime
import sys

import genera_inventario
import procesa_economia
import procesa_indicadores_sociales
import procesa_inversiones
import procesa_poblacion
import procesa_poblacion_desgloses
import procesa_turismo
import procesa_vivienda


def main() -> int:
    """Ejecuta el pipeline completo e informa por consola en español.

    Fija ``fecha_prueba`` a hoy (ISO) y ejecuta ``procesa_poblacion``,
    ``procesa_vivienda`` y ``genera_inventario`` en ese orden. Cada paso se
    envuelve en ``try/except`` para que un fallo en un paso obligatorio no
    impida intentar los demás; el fallo se registra en español y marca el
    código de salida como distinto de 0.

    Returns:
        ``0`` si todos los pasos obligatorios finalizan sin excepción; un
        valor distinto de 0 (el número de pasos fallidos) en caso contrario.
    """
    fecha_prueba = datetime.date.today().isoformat()

    print("=" * 60)
    print(f"[pipeline] Inicio del pipeline. Fecha de prueba: {fecha_prueba}.")
    print("=" * 60)

    # Pasos obligatorios del pipeline, en orden de ejecución. Cada entrada es
    # (nombre legible, función procesa del módulo correspondiente).
    pasos = [
        ("Procesamiento de población por parròquia", procesa_poblacion.procesa),
        ("Procesamiento de precios de vivienda", procesa_vivienda.procesa),
        ("Procesamiento de presupuesto de turismo", procesa_turismo.procesa),
        ("Procesamiento de inversiones inmobiliarias", procesa_inversiones.procesa),
        ("Procesamiento de desgloses de población", procesa_poblacion_desgloses.procesa),
        ("Procesamiento de indicadores sociales", procesa_indicadores_sociales.procesa),
        ("Procesamiento de economía (World Bank)", procesa_economia.procesa),
        ("Generación del inventario de fuentes", genera_inventario.procesa),
    ]

    pasos_fallidos = 0
    for numero, (nombre, funcion_procesa) in enumerate(pasos, start=1):
        print(f"\n[pipeline] Paso {numero}/{len(pasos)}: {nombre}...")
        try:
            funcion_procesa(fecha_prueba)
            print(f"[pipeline] Paso {numero}/{len(pasos)} completado: {nombre}.")
        except Exception as error:
            pasos_fallidos += 1
            print(
                f"[pipeline] ERROR en el paso {numero}/{len(pasos)} "
                f"({nombre}): {error}. Se continúa con los pasos restantes."
            )

    print("\n" + "=" * 60)
    if pasos_fallidos == 0:
        print(
            f"[pipeline] Pipeline finalizado correctamente: "
            f"{len(pasos)}/{len(pasos)} paso(s) completado(s)."
        )
    else:
        print(
            f"[pipeline] Pipeline finalizado con errores: "
            f"{pasos_fallidos} de {len(pasos)} paso(s) obligatorio(s) "
            "fallaron. Revise los mensajes anteriores."
        )
    print("=" * 60)

    return pasos_fallidos


if __name__ == "__main__":
    sys.exit(main())
