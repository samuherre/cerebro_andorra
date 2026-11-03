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
# OpenStreetMap publica sus datos bajo la Open Database License (ODbL), con
# texto literal verificado y atribución a los colaboradores de OSM.
LICENCIA_OSM = "ODbL (OpenStreetMap contributors)"
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


def _gob(arch, preg):
    """Devuelve las 4 filas de gobernanza comunes (fuente/vigencia/fecha/linaje)."""
    return [
        [arch, "fuente", "(anotado)", "Origen oficial del dato",
         "Texto", "texto", "Departament d'Estadística d'Andorra", "No", "Texto de la fuente", CLAS,
         "Se anota en el procesamiento (gobernanza)", preg],
        [arch, "vigencia", "(anotado)", "Periodo/año al que corresponde la cifra",
         "Texto", "año", "2024", "No", "Año o periodo", CLAS,
         "Se anota como el periodo del propio registro", preg],
        [arch, "fecha_prueba", "(anotado)", "Fecha real en que se verificó/procesó el dato",
         "Fecha", "AAAA-MM-DD", "2026-11-02", "No", "Fecha ISO", CLAS,
         "Se anota en el procesamiento con la fecha real de ejecución", preg],
        [arch, "linaje", "(anotado)", "Clasificación de gobernanza del dato",
         "Texto", "etiqueta", "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", CLAS,
         "Se etiqueta según el origen del dato", preg],
    ]


def _campos_poble():
    arch = "datos_procesados/poblacion_poble.csv"
    preg = "¿Cuánta gente vive en cada poble (localidad) y cómo evoluciona?"
    return [
        [arch, "poble", "Descripció", "Poble (localidad) de Andorra",
         "Texto", "nombre", "Aldosa", "No", "Nombre del poble", CLAS,
         "Se extrae del crudo de población por poble (id1096)", preg],
        [arch, "parroquia", "(derivado)", "Parròquia a la que pertenece el poble",
         "Texto", "nombre", "Canillo", "No", "Una de las 7 parròquies", CLAS,
         "Se asigna el nombre canónico de la parròquia", preg],
        [arch, "anio", "(año en cabecera)", "Año al que corresponde la población del poble",
         "Entero", "año", "2020", "No", "2020 a 2025", CLAS,
         "Transformación ancho→largo: cada columna de año pasa a fila", preg],
        [arch, "poblacion", "(valor de la celda)", "Número de habitantes del poble en el año",
         "Entero", "personas", "189", "No", "≥ 0", CLAS,
         "Se valida que sea entero no negativo", preg],
    ] + _gob(arch, preg)


def _campos_cruces_sexo():
    arch = "datos_procesados/poblacion_cruces_sexo.csv"
    preg = "¿Cómo se cruza la población por sexo con la edad, nacionalidad y origen?"
    return [
        [arch, "dimension", "(derivado)", "Cruce de sexo con otra dimensión",
         "Texto", "etiqueta", "sexo_edad_5", "No", "sexo_edad_5 / sexo_nacionalidad / sexo_lugar_nacimiento", CLAS,
         "Se asigna según el crudo de cruce procesado (id1098/1104/1138)", preg],
        [arch, "sexo", "Descripció", "Sexo del cruce",
         "Texto", "etiqueta", "HOME", "No", "HOME / DONA", CLAS,
         "Se extrae del patrón de la descripción del crudo", preg],
        [arch, "categoria", "Descripció", "Categoría de la otra dimensión (edad, nacionalidad u origen)",
         "Texto", "etiqueta", "00-04 ANYS", "No", "Depende de la dimensión", CLAS,
         "Se extrae del patrón de la descripción del crudo", preg],
        [arch, "anio", "(año en cabecera)", "Año al que corresponde el cruce",
         "Entero", "año", "2020", "No", "2020 a 2025", CLAS,
         "Transformación ancho→largo: cada columna de año pasa a fila", preg],
        [arch, "valor", "(valor de la celda)", "Número de personas del cruce",
         "Entero", "personas", "1315", "No", "≥ 0", CLAS,
         "Se valida que sea entero no negativo", preg],
    ] + _gob(arch, preg)


def _campos_edificios_suelo():
    arch = "datos_procesados/edificios_suelo.csv"
    preg = "¿Cómo es la morfología de edificación del territorio (usos y alturas)?"
    return [
        [arch, "uso_suelo", "(derivado de OSM)", "Uso del suelo / categoría de la huella edificada",
         "Texto", "texto", "Huella edificada general", "No", "Texto del uso", CLAS,
         "Se agrupa a partir de las etiquetas de edificio de OpenStreetMap", preg],
        [arch, "categoria_osm", "building/amenity (OSM)", "Categoría original de OpenStreetMap",
         "Texto", "texto", "Edificación sin uso específico", "No", "Texto de la categoría OSM", CLAS,
         "Se toma de las etiquetas del edificio en OSM", preg],
        [arch, "num_edificios", "(conteo)", "Número de edificios de esa categoría",
         "Entero", "edificios", "949", "No", "≥ 0", CLAS,
         "Se cuenta el número de polígonos de edificio por categoría", preg],
        [arch, "con_pisos_declarados", "(conteo)", "Edificios con número de plantas declarado en OSM",
         "Entero", "edificios", "133", "No", "≥ 0", CLAS,
         "Se cuentan los edificios con la etiqueta de plantas (building:levels)", preg],
        [arch, "pisos_medios", "(cálculo)", "Media de plantas de los edificios con dato",
         "Decimal", "plantas", "4.97", "Sí", "≥ 0", CLAS,
         "Media de building:levels entre los edificios que lo declaran", preg],
        [arch, "pisos_maximos", "(cálculo)", "Máximo de plantas declarado en la categoría",
         "Entero", "plantas", "9", "Sí", "≥ 0", CLAS,
         "Máximo de building:levels en la categoría", preg],
    ] + _gob(arch, preg)


def _campos_equipamientos():
    arch = "datos_procesados/equipamientos_suelo.csv"
    preg = "¿Qué equipamientos y servicios hay en cada parròquia y dónde están?"
    return [
        [arch, "parroquia", "(derivado)", "Parròquia donde se ubica el equipamiento",
         "Texto", "nombre", "Andorra la Vella", "No", "Una de las 7 parròquies", CLAS,
         "Se asigna por la ubicación del punto OSM", preg],
        [arch, "dominio", "(derivado)", "Dominio temático del equipamiento",
         "Texto", "texto", "Turismo y servicios", "No", "Texto del dominio", CLAS,
         "Se agrupa el tipo de equipamiento en un dominio temático", preg],
        [arch, "tipo_equipamiento", "amenity/tourism (OSM)", "Tipo de equipamiento o servicio",
         "Texto", "texto", "Hotel / alojamiento", "No", "Texto del tipo", CLAS,
         "Se deriva de las etiquetas de OpenStreetMap", preg],
        [arch, "nombre", "name (OSM)", "Nombre público del equipamiento (no es un dato de personas)",
         "Texto", "texto", "Hôtel Mercure Andorra", "Sí", "Texto del nombre", CLAS,
         "Se toma el nombre público del punto en OSM (establecimiento, no persona)", preg],
        [arch, "lat", "(OSM)", "Latitud del equipamiento",
         "Decimal", "grados", "42.50792", "No", "Coordenada WGS84", CLAS,
         "Coordenada del punto público en OSM", preg],
        [arch, "lon", "(OSM)", "Longitud del equipamiento",
         "Decimal", "grados", "1.527106", "No", "Coordenada WGS84", CLAS,
         "Coordenada del punto público en OSM", preg],
    ] + _gob(arch, preg)


def _campos_salud_educacion():
    arch = "datos_procesados/salud_educacion_ambiente.csv"
    preg = "¿Cómo están la salud, la educación y el ambiente en Andorra?"
    return [
        [arch, "dominio", "(derivado)", "Dominio del indicador (salud, educación o ambiente)",
         "Texto", "texto", "salud", "No", "salud / educacion / ambiente", CLAS,
         "Se asigna según el indicador del Banco Mundial", preg],
        [arch, "indicador", "indicator.value (WB)", "Nombre del indicador",
         "Texto", "texto", "Esperanza de vida al nacer", "No", "Texto del indicador", CLAS,
         "Se toma del catálogo de indicadores del Banco Mundial", preg],
        [arch, "codigo", "(código WB)", "Código del indicador en la API del Banco Mundial",
         "Texto", "código", "SP.DYN.LE00.IN", "No", "Código WB", CLAS,
         "Se toma del nombre del JSON descargado", preg],
        [arch, "anio", "date (WB)", "Año de la observación",
         "Entero", "año", "2024", "No", "Año", CLAS,
         "Se toma del campo 'date' de la observación", preg],
        [arch, "valor", "value (WB)", "Valor del indicador en ese año",
         "Decimal", "según indicador", "84.188", "Sí", "Depende del indicador", CLAS,
         "Se omiten las observaciones con valor nulo (no se inventan)", preg],
        [arch, "unidad", "(catálogo WB)", "Unidad de medida del indicador",
         "Texto", "texto", "años", "No", "Texto de la unidad", CLAS,
         "Se toma del catálogo de indicadores del Banco Mundial", preg],
    ] + _gob(arch, preg)


def _campos_turismo():
    arch = "datos_procesados/turismo.csv"
    return [
        [arch, "periodo", "Any / període", "Año al que corresponde la partida de turismo",
         "Texto", "año", "2024", "No", "2020 a 2025", CLAS,
         "Se normaliza el año a texto", "¿Cómo evoluciona el presupuesto de turismo en el tiempo?"],
        [arch, "partida", "Concepte", "Partida o concepto de gasto de Andorra Turisme SAU",
         "Texto", "texto", "DESPESES DE FUNCIONAMENT", "No", "Texto del concepto", CLAS,
         "Se conserva el nombre del concepto tal como viene de la fuente", "¿En qué se reparte el gasto de turismo?"],
        [arch, "valor_eur", "Import (€)", "Importe en euros de la partida de turismo",
         "Decimal", "€", "17378555.0", "No", "≥ 0", CLAS,
         "Se convierte el importe a número decimal", "¿Cuánto gasta Andorra en turismo por año?"],
        [arch, "fuente", "(anotado)", "Origen oficial del dato de turismo",
         "Texto", "texto", "Departament d'Estadística d'Andorra (estadistica_681, Andorra Turisme SAU)", "No", "Texto de la fuente", CLAS,
         "Se anota en el procesamiento (gobernanza)", "¿De dónde viene la cifra de turismo? (trazabilidad)"],
        [arch, "vigencia", "(anotado)", "Año al que corresponde la cifra de turismo",
         "Texto", "año", "2024", "No", "2020 a 2025", CLAS,
         "Se anota como el año del propio registro", "¿A qué periodo corresponde la cifra?"],
        [arch, "fecha_prueba", "(anotado)", "Fecha real en que se verificó/procesó el dato",
         "Fecha", "AAAA-MM-DD", "2026-11-02", "No", "Fecha ISO", CLAS,
         "Se anota en el procesamiento con la fecha real de ejecución", "¿Cuándo se comprobó la cifra? (frescura)"],
        [arch, "linaje", "(anotado)", "Clasificación de gobernanza del dato",
         "Texto", "etiqueta", "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", CLAS,
         "Se etiqueta como OBSERVADO por ser dato oficial de ejecución presupuestaria", "¿Qué fiabilidad tiene la cifra?"],
    ]


def _campos_inversiones():
    arch = "datos_procesados/inversiones_inmobiliarias.csv"
    return [
        [arch, "anio", "Any", "Año al que corresponde el número de inversiones",
         "Entero", "año", "2024", "No", "2020 a 2025", CLAS,
         "Se normaliza el año a entero", "¿Cómo evoluciona la inversión inmobiliaria en el tiempo?"],
        [arch, "num_inversiones", "Nombre d'inversions immobiliàries", "Número de inversiones inmobiliarias registradas en el año",
         "Entero", "inversiones", "501", "No", "≥ 0", CLAS,
         "Se valida que sea entero no negativo", "¿Cuánta inversión inmobiliaria hay por año?"],
        [arch, "fuente", "(anotado)", "Origen oficial del dato de inversiones",
         "Texto", "texto", "Departament d'Estadística d'Andorra (estadistica_2729, inversions immobiliàries)", "No", "Texto de la fuente", CLAS,
         "Se anota en el procesamiento (gobernanza)", "¿De dónde viene la cifra de inversiones? (trazabilidad)"],
        [arch, "vigencia", "(anotado)", "Año al que corresponde la cifra de inversiones",
         "Texto", "año", "2024", "No", "2020 a 2025", CLAS,
         "Se anota como el año del propio registro", "¿A qué periodo corresponde la cifra?"],
        [arch, "fecha_prueba", "(anotado)", "Fecha real en que se verificó/procesó el dato",
         "Fecha", "AAAA-MM-DD", "2026-11-02", "No", "Fecha ISO", CLAS,
         "Se anota en el procesamiento con la fecha real de ejecución", "¿Cuándo se comprobó la cifra? (frescura)"],
        [arch, "linaje", "(anotado)", "Clasificación de gobernanza del dato",
         "Texto", "etiqueta", "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", CLAS,
         "Se etiqueta como OBSERVADO por ser dato oficial de registro", "¿Qué fiabilidad tiene la cifra?"],
    ]


def _campos_empleo():
    arch = "datos_procesados/salario_sector.csv"
    preg = "¿En qué sectores trabaja la gente y cuánto se gana en cada uno?"
    return [
        [arch, "sector", "Descripció", "Sector de actividad (CAEA nivel 1) en español",
         "Texto", "texto", "Hostelería", "No", "Uno de los sectores de actividad", CLAS,
         "Se extrae de 'SALARI MEDIÀ PER SECTOR D'ACTIVITAT (NIVELL 1). <LETRA>-<SECTOR>' y se traduce a español", preg],
        [arch, "letra_sector", "(código CAEA)", "Letra del sector de actividad (CAEA nivel 1)",
         "Texto", "código", "H", "No", "A..T o TOTAL", CLAS,
         "Se toma la letra anterior al guion de la Descripció", preg],
        [arch, "salario_medio", "(valor del periodo)", "Salario medio mensual del sector en euros (último mes con dato)",
         "Decimal", "€/mes", "1835.41", "No", "> 0 y ≤ 50000", CLAS,
         "Se toma el último periodo mensual con salario positivo; se descartan los ceros (sector sin asalariados)", preg],
        [arch, "es_total", "(derivado)", "Marca si la fila es el total de todos los sectores",
         "Texto", "0/1", "0", "No", "0 o 1", CLAS,
         "Se asigna 1 a la fila TOTAL y 0 al resto de sectores", preg],
        [arch, "fuente", "(anotado)", "Origen oficial del salario por sector",
         "Texto", "texto", "Departament d'Estadística d'Andorra", "No", "Texto de la fuente", CLAS,
         "Se anota en el procesamiento (gobernanza)", preg],
        [arch, "vigencia", "(anotado)", "Periodo mensual al que corresponde el salario",
         "Texto", "AAAA/MM", "2025/12", "No", "2018/01 a 2025/12", CLAS,
         "Se anota como el periodo del dato más reciente del sector", preg],
        [arch, "fecha_prueba", "(anotado)", "Fecha real en que se verificó/procesó el salario",
         "Fecha", "AAAA-MM-DD", "2026-11-02", "No", "Fecha ISO", CLAS,
         "Se anota en el procesamiento con la fecha real de ejecución", preg],
        [arch, "linaje", "(anotado)", "Clasificación de gobernanza del salario",
         "Texto", "etiqueta", "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", CLAS,
         "Se etiqueta como OBSERVADO por ser dato oficial del Departament d'Estadística", preg],
    ]


# (id_fuente, csv_para_fecha, licencia_literal, generador_de_campos)
# Los ID_Fuente coinciden EXACTAMENTE con los del Inventario_Fuentes
# (datos_procesados/inventario_fuentes.csv) para que cada cifra de la app lleve
# a su ficha del diccionario con el mismo ID (trazabilidad cifra -> ficha):
#   F03 = turismo.csv, F04 = inversiones_inmobiliarias.csv,
#   F10 = poblacion_desgloses.csv, F11 = umbrales_pobreza.csv,
#   F12 = tasa_fecundidad.csv, F13 = economia_worldbank.csv,
#   F14 = salario_sector.csv.
FUENTES_NUEVAS = [
    ("F03", "turismo.csv", LICENCIA_ESTADISTICA, _campos_turismo),
    ("F04", "inversiones_inmobiliarias.csv", LICENCIA_ESTADISTICA, _campos_inversiones),
    ("F10", "poblacion_desgloses.csv", LICENCIA_ESTADISTICA, _campos_desgloses),
    ("F11", "umbrales_pobreza.csv", LICENCIA_ESTADISTICA, _campos_pobreza),
    ("F12", "tasa_fecundidad.csv", LICENCIA_ESTADISTICA, _campos_fecundidad),
    ("F13", "economia_worldbank.csv", LICENCIA_WORLDBANK, _campos_economia),
    ("F14", "salario_sector.csv", LICENCIA_ESTADISTICA, _campos_empleo),
    # Fuentes nuevas de la ultima parte (territorio/pueblos, suelo y bienestar).
    ("F15", "poblacion_poble.csv", LICENCIA_ESTADISTICA, _campos_poble),
    ("F16", "poblacion_cruces_sexo.csv", LICENCIA_ESTADISTICA, _campos_cruces_sexo),
    ("F17", "edificios_suelo.csv", LICENCIA_OSM, _campos_edificios_suelo),
    ("F18", "equipamientos_suelo.csv", LICENCIA_OSM, _campos_equipamientos),
    ("F19", "salud_educacion_ambiente.csv", LICENCIA_WORLDBANK, _campos_salud_educacion),
]

# ID_Fuente que gestiona este script. Se eliminan sus filas previas antes de
# reinsertarlas para que el script sea idempotente (volver a ejecutarlo no
# duplica entradas). Se incluyen tambien los ID obsoletos F30/F31 (turismo e
# inversiones quedaron con esos ID en una version anterior del diccionario, pero
# en el inventario son F03/F04): al estar aqui, sus filas antiguas se eliminan y
# se reescriben con el ID correcto, alineando diccionario e inventario.
IDS_GESTIONADOS = {
    "F03", "F04", "F10", "F11", "F12", "F13", "F14",
    "F15", "F16", "F17", "F18", "F19", "F30", "F31",
}


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


def _elimina_filas_gestionadas(ws):
    """Borra las filas cuyas entradas pertenecen a los ID_Fuente gestionados.

    Hace el script idempotente: antes de reinsertar los campos de F10..F14 se
    eliminan sus filas previas (identificadas por el ID_Fuente en la columna 1),
    de modo que volver a ejecutarlo no duplique entradas en el diccionario.
    """
    filas_a_borrar = [
        r
        for r in range(5, ws.max_row + 1)
        if str(ws.cell(row=r, column=1).value or "").strip() in IDS_GESTIONADOS
    ]
    # Borrar de abajo hacia arriba para no desplazar los índices pendientes.
    for r in sorted(filas_a_borrar, reverse=True):
        ws.delete_rows(r, 1)
    if filas_a_borrar:
        print(
            f"[OK] Eliminadas {len(filas_a_borrar)} fila(s) previa(s) de "
            "ID_Fuente gestionados para evitar duplicados."
        )


def main():
    wb = openpyxl.load_workbook(RUTA_XLSX)
    ws = wb[HOJA]

    _asegura_cabeceras_nuevas(ws)
    _elimina_filas_gestionadas(ws)

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
