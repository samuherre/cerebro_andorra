"""Actualiza el Diccionario de Datos (Excel de contexto/) con los campos nuevos de la Parte 3.

Añade exactamente una entrada por cada campo realmente integrado en el lago por las
fuentes nuevas de la Parte 3 (enriquecimiento):

- poblacion_desgloses.csv  (desgloses de población por parròquia)
- umbrales_pobreza.csv      (reclasificación del crudo mal etiquetado 820)
- tasa_fecundidad.csv       (reclasificación del crudo mal etiquetado 810)
- economia_worldbank.csv    (economía del Banco Mundial)

Cada entrada lleva su fecha real de prueba en ISO (AAAA-MM-DD), tomada del propio CSV
procesado, y el texto de licencia literal de la fuente. Toda entrada que carezca de
fecha real de prueba o de texto literal de licencia se marca como INCOMPLETA con una
indicación visible, conservando el resto de los datos de la entrada (Requisitos 8.4, 8.5).

Se ejecuta desde la carpeta scripts/ con ruta relativa al Excel en contexto/.
No modifica datos_crudos/ ni toca los CSV procesados (solo los lee).
"""

import copy
import csv
import os

import openpyxl

RUTA_XLSX = "../contexto/Diccionario_de_datos_TallerDatos_unido_Andorra (1).xlsx"
HOJA = "2. Diccionario"
RUTA_PROCESADOS = "../datos_procesados"

# Texto que marca de forma visible una celda incompleta (Req 8.5).
MARCA_INCOMPLETA = "INCOMPLETA: "

# Licencias tal como deben copiarse de forma literal. Si una fuente no tiene texto
# literal disponible, su valor es None y la entrada se marcará como INCOMPLETA.
LICENCIA_WORLDBANK = "CC BY 4.0"
# El Departament d'Estadística d'Andorra no publica un texto de licencia literal
# verificado en el proyecto, así que se deja sin texto literal (se marca INCOMPLETA).
LICENCIA_ESTADISTICA = None

# Clasificación de acceso usada por el resto de la hoja.
CLAS = "Pública"


def _lee_fecha_prueba(nombre_csv):
    """Devuelve la fecha_prueba real (ISO) de la primera fila de datos del CSV procesado.

    Devuelve None si el archivo no existe, está vacío (solo cabecera) o no trae la
    columna fecha_prueba: en ese caso el campo no está realmente integrado con fecha
    real y debe marcarse como INCOMPLETA.
    """
    ruta = os.path.join(RUTA_PROCESADOS, nombre_csv)
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8", newline="") as fh:
            lector = csv.DictReader(fh, delimiter=";")
            for fila in lector:
                valor = (fila.get("fecha_prueba") or "").strip()
                return valor or None
    except (OSError, UnicodeDecodeError, csv.Error):
        return None
    return None


# Definición de los campos por fuente nueva. Cada entrada es un dict con los metadatos
# del campo que irá al diccionario. Las columnas de fecha y licencia se resuelven abajo.
# Estructura de columnas de la hoja "2. Diccionario":
#  C1 ID fuente | C2 Archivo/tabla | C3 Campo en el lago | C4 Nombre original
#  C5 Qué significa | C6 Tipo | C7 Unidad | C8 Ejemplo | C9 ¿Vacío? | C10 Rango
#  C11 Clasificación | C12 Transformación | C13 Pregunta del sistema
#  [NUEVAS] C14 Fecha de prueba (AAAA-MM-DD) | C15 Licencia (texto literal)


def _campos_desgloses():
    arch = "datos_procesados/poblacion_desgloses.csv"
    preg = "¿Cómo se compone la población de cada parròquia (edad, sexo, nacionalidad, origen)?"
    return [
        [arch, "parroquia", "Descripció", "Parròquia a la que corresponde el desglose de población",
         "Texto", "nombre", "Canillo", "No", "Una de las 7 parròquies", CLAS,
         "Se extrae del patrón 'CATEGORIA. PARRÒQUIA. SUBCATEGORIA' y se normaliza a nombre canónico", preg],
        [arch, "dimension", "(derivado del archivo)", "Dimensión del desglose de población",
         "Texto", "etiqueta", "edad_5", "No", "edad_5 / edad_1 / sexo / nacionalidad / lugar_nacimiento", CLAS,
         "Se asigna según el crudo de desglose procesado", preg],
        [arch, "categoria", "Descripció", "Categoría dentro de la dimensión (tramo, sexo, nacionalidad u origen)",
         "Texto", "etiqueta", "DE 00-04 ANYS", "No", "Depende de la dimensión", CLAS,
         "Se extrae del patrón 'CATEGORIA. PARRÒQUIA. SUBCATEGORIA'", preg],
        [arch, "anio", "(año en cabecera)", "Año al que corresponde la cifra del desglose",
         "Entero", "año", "2025", "No", "2020 a 2025", CLAS,
         "Transformación ancho→largo: cada columna de año pasa a ser una fila", preg],
        [arch, "valor", "(valor de la celda de año)", "Número de personas del desglose en esa parròquia y año",
         "Entero", "personas", "150", "No", "≥ 0", CLAS,
         "Se valida que sea entero no negativo; se descartan celdas vacías o no numéricas", preg],
        [arch, "fuente", "(anotado)", "Origen oficial del desglose de población",
         "Texto", "texto", "Departament d'Estadística d'Andorra", "No", "Texto de la fuente", CLAS,
         "Se anota en el procesamiento (gobernanza)", preg],
        [arch, "vigencia", "(anotado)", "Año al que corresponde la cifra del desglose",
         "Texto", "año", "2025", "No", "2020 a 2025", CLAS,
         "Se anota como el año del propio registro", preg],
        [arch, "fecha_prueba", "(anotado)", "Fecha real en que se verificó/procesó el desglose",
         "Fecha", "AAAA-MM-DD", "2026-10-26", "No", "Fecha ISO", CLAS,
         "Se anota en el procesamiento con la fecha real de ejecución", preg],
        [arch, "linaje", "(anotado)", "Clasificación de gobernanza del desglose",
         "Texto", "etiqueta", "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", CLAS,
         "Se etiqueta como OBSERVADO por ser dato oficial de censo", preg],
    ]


def _campos_pobreza():
    arch = "datos_procesados/umbrales_pobreza.csv"
    preg = "¿Cuáles son los umbrales de pobreza e ingresos en Andorra?"
    return [
        [arch, "indicador", "(contenido real del crudo 820)", "Umbral de pobreza o ingresos (reclasificado del crudo mal etiquetado 820)",
         "Texto", "texto", "LLINDAR DE RISC DE POBRESA (60%)", "No", "Texto del umbral", CLAS,
         "Se reclasifica el crudo 'transacciones' según su contenido real (umbrales de pobreza/ingresos)", preg],
        [arch, "anio", "(año)", "Año al que corresponde el umbral",
         "Entero", "año", "2021", "No", "2020 a 2025", CLAS,
         "Se conservan solo los años dentro de 2020–2025", preg],
        [arch, "valor_eur", "(importe)", "Importe del umbral en euros",
         "Decimal", "€", "12153.39", "No", "≥ 0", CLAS,
         "Se convierte el separador decimal de coma catalana a punto", preg],
        [arch, "fuente", "(anotado)", "Origen oficial del umbral",
         "Texto", "texto", "Departament d'Estadística d'Andorra", "No", "Texto de la fuente", CLAS,
         "Se anota en el procesamiento (gobernanza)", preg],
        [arch, "vigencia", "(anotado)", "Año al que corresponde el umbral",
         "Texto", "año", "2021", "No", "2020 a 2025", CLAS,
         "Se anota como el año del propio registro", preg],
        [arch, "fecha_prueba", "(anotado)", "Fecha real en que se verificó/procesó el umbral",
         "Fecha", "AAAA-MM-DD", "2026-10-26", "No", "Fecha ISO", CLAS,
         "Se anota en el procesamiento con la fecha real de ejecución", preg],
        [arch, "linaje", "(anotado)", "Clasificación de gobernanza del umbral",
         "Texto", "etiqueta", "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", CLAS,
         "Se etiqueta como OBSERVADO por ser dato oficial", preg],
    ]


def _campos_fecundidad():
    arch = "datos_procesados/tasa_fecundidad.csv"
    preg = "¿Cómo evoluciona la tasa de fecundidad en Andorra?"
    return [
        [arch, "indicador", "(contenido real del crudo 810)", "Indicador de fecundidad (reclasificado del crudo mal etiquetado 810)",
         "Texto", "texto", "Tasa de fecundidad", "No", "Tasa de fecundidad", CLAS,
         "Se reclasifica el crudo 'indicadores económicos' según su contenido real (tasa de fecundidad)", preg],
        [arch, "anio", "(año)", "Año al que corresponde la tasa",
         "Entero", "año", "2022", "No", "2020 a 2025", CLAS,
         "Se conservan solo los años dentro de 2020–2025", preg],
        [arch, "valor", "(valor)", "Valor de la tasa de fecundidad",
         "Decimal", "tasa", "26.47959", "No", "≥ 0", CLAS,
         "Se convierte el separador decimal de coma catalana a punto", preg],
        [arch, "fuente", "(anotado)", "Origen oficial de la tasa",
         "Texto", "texto", "Departament d'Estadística d'Andorra", "No", "Texto de la fuente", CLAS,
         "Se anota en el procesamiento (gobernanza)", preg],
        [arch, "vigencia", "(anotado)", "Año al que corresponde la tasa",
         "Texto", "año", "2022", "No", "2020 a 2025", CLAS,
         "Se anota como el año del propio registro", preg],
        [arch, "fecha_prueba", "(anotado)", "Fecha real en que se verificó/procesó la tasa",
         "Fecha", "AAAA-MM-DD", "2026-10-26", "No", "Fecha ISO", CLAS,
         "Se anota en el procesamiento con la fecha real de ejecución", preg],
        [arch, "linaje", "(anotado)", "Clasificación de gobernanza de la tasa",
         "Texto", "etiqueta", "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", CLAS,
         "Se etiqueta como OBSERVADO por ser dato oficial", preg],
    ]


def _campos_economia():
    arch = "datos_procesados/economia_worldbank.csv"
    preg = "¿Cómo evolucionan los indicadores macroeconómicos de Andorra (PIB, IPC)?"
    return [
        [arch, "indicador", "indicator.value", "Nombre del indicador macroeconómico del Banco Mundial",
         "Texto", "texto", "PIB (US$ a precios actuales)", "No", "Texto del indicador", CLAS,
         "Se toma del catálogo de indicadores de la descarga World Bank", preg],
        [arch, "codigo", "(código WB)", "Código del indicador en la API del Banco Mundial",
         "Texto", "código", "NY.GDP.MKTP.CD", "No", "Código WB", CLAS,
         "Se toma del nombre del JSON descargado", preg],
        [arch, "anio", "date", "Año de la observación",
         "Entero", "año", "2024", "No", "Año", CLAS,
         "Se toma del campo 'date' de la observación", preg],
        [arch, "valor", "value", "Valor del indicador en ese año",
         "Decimal", "según indicador", "4044000000.0", "Sí", "Depende del indicador", CLAS,
         "Se omiten las observaciones con valor nulo (no se inventan)", preg],
        [arch, "unidad", "(catálogo WB)", "Unidad de medida del indicador",
         "Texto", "texto", "US$ a precios actuales", "No", "Texto de la unidad", CLAS,
         "Se toma del catálogo de indicadores de la descarga World Bank", preg],
        [arch, "fuente", "(anotado)", "Origen del indicador económico",
         "Texto", "texto", "Banco Mundial (World Bank Open Data, API v2)", "No", "Texto de la fuente", CLAS,
         "Se anota en el procesamiento (gobernanza)", preg],
        [arch, "vigencia", "(anotado)", "Año al que corresponde el indicador",
         "Texto", "año", "2024", "No", "Año", CLAS,
         "Se anota como el año del propio registro", preg],
        [arch, "fecha_prueba", "(anotado)", "Fecha real en que se verificó/descargó el indicador",
         "Fecha", "AAAA-MM-DD", "(sin descarga)", "No", "Fecha ISO", CLAS,
         "Se anotaría en la descarga; el JSON de World Bank no se descargó en esta entrega", preg],
        [arch, "linaje", "(anotado)", "Clasificación de gobernanza del indicador",
         "Texto", "etiqueta", "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", CLAS,
         "Se etiqueta como OBSERVADO por ser dato oficial del Banco Mundial", preg],
    ]


# (id_fuente, csv_para_fecha, licencia_literal, generador_de_campos)
# Los ID_Fuente coinciden con los del Inventario_Fuentes (datos_procesados/inventario_fuentes.csv):
#   F10 = poblacion_desgloses.csv, F11 = umbrales_pobreza.csv,
#   F12 = tasa_fecundidad.csv, F13 = economia_worldbank.csv.
FUENTES_NUEVAS = [
    ("F10", "poblacion_desgloses.csv", LICENCIA_ESTADISTICA, _campos_desgloses),
    ("F11", "umbrales_pobreza.csv", LICENCIA_ESTADISTICA, _campos_pobreza),
    ("F12", "tasa_fecundidad.csv", LICENCIA_ESTADISTICA, _campos_fecundidad),
    ("F13", "economia_worldbank.csv", LICENCIA_WORLDBANK, _campos_economia),
]


def _ultima_fila_con_datos(ws):
    """Devuelve el número de la última fila (>=5) que tiene datos en la hoja."""
    ultima = 4
    for r in range(5, ws.max_row + 1):
        if any(ws.cell(row=r, column=c).value is not None for c in range(1, 14)):
            ultima = r
    return ultima


def _asegura_cabeceras_nuevas(ws):
    """Añade las cabeceras de las columnas 14 (fecha) y 15 (licencia) copiando el estilo."""
    estilo = ws.cell(row=3, column=13)
    titulos = {
        14: "Fecha de prueba (AAAA-MM-DD)",
        15: "Licencia (texto literal)",
    }
    for col, titulo in titulos.items():
        celda = ws.cell(row=3, column=col)
        celda.value = titulo
        celda.font = copy.copy(estilo.font)
        celda.fill = copy.copy(estilo.fill)
        celda.alignment = copy.copy(estilo.alignment)
        celda.border = copy.copy(estilo.border)
    ws.column_dimensions["N"].width = 26
    ws.column_dimensions["O"].width = 34


def main():
    wb = openpyxl.load_workbook(RUTA_XLSX)
    ws = wb[HOJA]

    _asegura_cabeceras_nuevas(ws)

    fila = _ultima_fila_con_datos(ws) + 1
    total = 0
    incompletas = 0

    for id_fuente, csv_fecha, licencia_literal, generador in FUENTES_NUEVAS:
        fecha_real = _lee_fecha_prueba(csv_fecha)

        # Celda de fecha: real o marcada como incompleta de forma visible.
        if fecha_real:
            valor_fecha = fecha_real
            fecha_incompleta = False
        else:
            valor_fecha = MARCA_INCOMPLETA + "sin fecha real de prueba (fuente no descargada)"
            fecha_incompleta = True

        # Celda de licencia: texto literal o marcada como incompleta de forma visible.
        if licencia_literal:
            valor_licencia = licencia_literal
            licencia_incompleta = False
        else:
            valor_licencia = MARCA_INCOMPLETA + "falta texto literal de licencia de la fuente"
            licencia_incompleta = True

        for campo in generador():
            ws.cell(row=fila, column=1, value=id_fuente)
            for j, valor in enumerate(campo):  # columnas 2..13
                ws.cell(row=fila, column=2 + j, value=valor)
            ws.cell(row=fila, column=14, value=valor_fecha)
            ws.cell(row=fila, column=15, value=valor_licencia)
            fila += 1
            total += 1
            if fecha_incompleta or licencia_incompleta:
                incompletas += 1

    wb.save(RUTA_XLSX)
    print(f"[OK] Diccionario actualizado: {total} campos nuevos escritos "
          f"({incompletas} marcados como INCOMPLETA por falta de fecha real o licencia literal).")

    # Verificación de integridad: se reabre el archivo tras guardarlo.
    wb2 = openpyxl.load_workbook(RUTA_XLSX)
    ws2 = wb2[HOJA]
    ultima = _ultima_fila_con_datos(ws2)
    print(f"[OK] Reapertura correcta. Hojas: {wb2.sheetnames}. "
          f"Ultima fila con datos en '{HOJA}': {ultima}.")


if __name__ == "__main__":
    main()
