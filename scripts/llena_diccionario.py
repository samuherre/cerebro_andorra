"""Rellena las 3 hojas del diccionario de datos del Taller (Entrega 1).

Toma la información ya recopilada en el proyecto Cerebro Andorra (scripts de
extracción, procesadores, bitácoras y datos crudos/procesados) y la vuelca en
las hojas '1. Fuentes', '2. Diccionario' y '3. Bitácora IA' del archivo
Diccionario_de_datos_TallerDatos.xlsx, escribiendo a partir de la fila 5 para
respetar la fila de ejemplo (gris) de cada hoja.

Se ejecuta desde la carpeta scripts/ con ruta relativa al archivo en la raíz.
"""

import openpyxl

RUTA_XLSX = "../Diccionario_de_datos_TallerDatos.xlsx"

# --- Hoja 1: Fuentes --------------------------------------------------------
# Columnas: ID fuente, Nombre, Entidad, Tipo de publicador, URL, Formato,
# Cómo se obtiene, Licencia, ¿Personas?, Cobertura, Periodo, Frecuencia,
# Fecha probada, Estado, Cómo la encontraron, Observaciones
FUENTES = [
    [
        "F01",
        "Població per parròquia (banc de dades d'Estadística)",
        "Departament d'Estadística d'Andorra",
        "Entidad pública",
        "https://sig.govern.ad/Sigdde.Public/Inici",
        "CSV",
        "Descarga directa",
        "no declara",
        "No",
        "Nacional (7 parròquies)",
        "2020 a 2025",
        "Anual",
        "2026-09-27",
        "Integrada al lago",
        "Búsqueda propia + confirmación con IA de la fuente oficial",
        "Formato ancho (un año por columna); incluye fila TOTAL que se excluye. Linaje OBSERVADO.",
    ],
    [
        "F02",
        "Precios de vivienda €/m² por parròquia (Indomio)",
        "Indomio.es",
        "Empresa privada",
        "https://www.indomio.es/en/mercado-inmobiliario/andorra/andorra-provincia/",
        "Página web",
        "Bloquea scripts o pide sesión",
        "no declara",
        "No",
        "Nacional (7 parròquies) + barrios de Andorra la Vella",
        "Captura de agosto-septiembre 2026",
        "Mensual",
        "2026-09-27",
        "Integrada al lago",
        "Sugerida por la IA como portal con desglose por zona; confirmada abriendo el sitio",
        "Datos de oferta (anuncios), no de transacción real. Linaje PROXY. Bloqueo anti-bot documentado.",
    ],
    [
        "F03",
        "Edificios de Andorra (geometría OSM)",
        "OpenStreetMap / Overpass API",
        "Plataforma colaborativa",
        "https://overpass-api.de/api/interpreter",
        "GeoJSON",
        "API sin llave",
        "ODbL",
        "No",
        "Andorra la Vella (área de prueba)",
        "Extracción puntual 2026-09",
        "No se sabe",
        "2026-09-27",
        "Candidata",
        "Query Overpass propia; primer intento dio 406 hasta añadir User-Agent",
        "Vista geoespacial fuera de alcance v1. Pocos edificios con building:levels.",
    ],
    [
        "F04",
        "Transacciones inmobiliarias oficiales (idDivision 820)",
        "Departament d'Estadística d'Andorra",
        "Entidad pública",
        "https://sig.govern.ad/Sigdde.Public/estadistiquesdades/api/data",
        "CSV",
        "API sin llave",
        "no declara",
        "No",
        "Nacional",
        "2020 a 2025 (solicitado)",
        "Trimestral",
        "2026-09-27",
        "Descartada",
        "Descarga automatizada desde la API oficial",
        "El contenido descargado no coincide con el nombre/tema del archivo; excluida del lago.",
    ],
    [
        "F05",
        "Indicadores económicos oficiales (idDivision 810)",
        "Departament d'Estadística d'Andorra",
        "Entidad pública",
        "https://sig.govern.ad/Sigdde.Public/estadistiquesdades/api/data",
        "CSV",
        "API sin llave",
        "no declara",
        "No",
        "Nacional",
        "2020 a 2025 (solicitado)",
        "Trimestral",
        "2026-09-27",
        "Descartada",
        "Descarga automatizada desde la API oficial",
        "El contenido descargado no coincide con el nombre/tema del archivo; excluida del lago.",
    ],
    [
        "F06",
        "AGIA — informe semestral de precios inmobiliarios",
        "Col·legi d'Agents i Gestors Immobiliaris d'Andorra",
        "Academia u ONG",
        "https://www.agia.ad/",
        "PDF",
        "Solo PDF o página",
        "no declara",
        "No",
        "Nacional (por parròquia)",
        "Informe semestral",
        "Semestral",
        "2026-09-27",
        "Candidata",
        "Citada por la IA como la fuente sectorial más fiable para calibrar Indomio",
        "Precio de operaciones reales (linaje ESTIMADO). Útil para calibrar el PROXY de Indomio.",
    ],
]

# --- Hoja 2: Diccionario ----------------------------------------------------
# Columnas: ID fuente, Archivo/tabla, Nombre del campo, Nombre original,
# Qué significa, Tipo de dato, Unidad, Ejemplo, ¿Vacío?, Valores/rango,
# Clasificación, Transformación, Pregunta del sistema
DICCIONARIO = [
    # poblacion_parroquia.csv (F01)
    ["F01", "datos_procesados/poblacion_parroquia.csv", "parroquia", "Descripció",
     "Nombre de la parròquia a la que corresponde la cifra de población",
     "Texto", "nombre", "Canillo", "No",
     "Una de las 7 parròquies", "Pública",
     "Se quita el prefijo 'POBLACIÓ PER PARRÒQUIA.' y se normaliza a nombre canónico; se excluye la fila TOTAL",
     "¿Cómo se distribuye la población entre las parròquies?"],
    ["F01", "datos_procesados/poblacion_parroquia.csv", "anio", "(año en cabecera)",
     "Año al que corresponde la cifra de población",
     "Entero", "año", "2025", "No",
     "2020 a 2025", "Pública",
     "Transformación ancho→largo: cada columna de año pasa a ser una fila",
     "¿Cómo evoluciona la población por parròquia en el tiempo?"],
    ["F01", "datos_procesados/poblacion_parroquia.csv", "poblacion", "(valor de la celda de año)",
     "Número de habitantes de la parròquia en ese año",
     "Entero", "personas", "6457", "No",
     "≥ 0", "Pública",
     "Se valida que sea entero no negativo; se descartan celdas vacías o no numéricas",
     "¿Cuántos habitantes tiene cada parròquia?"],
    ["F01", "datos_procesados/poblacion_parroquia.csv", "fuente", "(anotado)",
     "Origen oficial del dato de población", "Texto", "texto",
     "Departament d'Estadística d'Andorra (estadistica_id798)", "No",
     "Texto de la fuente", "Pública",
     "Se anota en el procesamiento (gobernanza): 0 cifras sin fuente",
     "¿De dónde viene cada cifra? (trazabilidad)"],
    ["F01", "datos_procesados/poblacion_parroquia.csv", "vigencia", "(anotado)",
     "Año o periodo al que corresponde la cifra", "Texto", "año", "2025", "No",
     "2020 a 2025", "Pública", "Se anota como el año del propio registro",
     "¿A qué periodo corresponde la cifra?"],
    ["F01", "datos_procesados/poblacion_parroquia.csv", "fecha_prueba", "(anotado)",
     "Fecha en que se verificó/procesó el dato", "Fecha", "AAAA-MM-DD",
     "2026-09-27", "No", "Fecha ISO", "Pública",
     "Se anota en el procesamiento con la fecha de ejecución",
     "¿Cuándo se comprobó la cifra? (frescura)"],
    ["F01", "datos_procesados/poblacion_parroquia.csv", "linaje", "(anotado)",
     "Clasificación de gobernanza según linaje del dato", "Texto", "etiqueta",
     "OBSERVADO", "No", "OBSERVADO / ESTIMADO / PROXY", "Pública",
     "Se etiqueta como OBSERVADO por ser dato oficial de censo",
     "¿Qué fiabilidad tiene la cifra? (observado vs estimado vs proxy)"],
    # precios_vivienda.csv (F02)
    ["F02", "datos_procesados/precios_vivienda.csv", "parroquia", "Municipalities",
     "Parròquia a la que corresponde el precio de vivienda", "Texto", "nombre",
     "Andorra la Vella", "No", "Una de las 7 parròquies", "Pública",
     "Se mapea el municipio de Indomio al nombre canónico (p.ej. 'Sant Julia de Loria'→'Sant Julià de Lòria')",
     "¿Cómo varían los precios de vivienda entre parròquies?"],
    ["F02", "datos_procesados/precios_vivienda.csv", "precio_venta", "Sale €/m²",
     "Precio de oferta de venta por metro cuadrado", "Decimal", "€/m²", "7115.0",
     "Sí", "≥ 0", "Pública",
     "Se separa la celda '7,115(+14.8%)': se quita la coma de miles y se toma el número",
     "¿Cuánto cuesta comprar vivienda por parròquia?"],
    ["F02", "datos_procesados/precios_vivienda.csv", "var_venta", "Sale €/m² (paréntesis)",
     "Variación interanual del precio de venta", "Decimal", "%", "14.8", "Sí",
     "Positiva o negativa", "Pública",
     "Se extrae el porcentaje entre paréntesis de la celda de venta, con su signo",
     "¿Suben o bajan los precios de venta y cuánto?"],
    ["F02", "datos_procesados/precios_vivienda.csv", "precio_alquiler", "Rent €/m²",
     "Precio de oferta de alquiler por metro cuadrado al mes", "Decimal", "€/m²/mes",
     "24.66", "Sí", "≥ 0", "Pública",
     "Se separa la celda '24.66(+2.0%)' en precio y variación",
     "¿Cuánto cuesta alquilar vivienda por parròquia?"],
    ["F02", "datos_procesados/precios_vivienda.csv", "var_alquiler", "Rent €/m² (paréntesis)",
     "Variación interanual del precio de alquiler", "Decimal", "%", "-14.6", "Sí",
     "Positiva o negativa", "Pública",
     "Se extrae el porcentaje entre paréntesis de la celda de alquiler, con su signo",
     "¿Suben o bajan los alquileres y cuánto?"],
    ["F02", "datos_procesados/precios_vivienda.csv", "fuente", "(anotado)",
     "Origen del dato de precios", "Texto", "texto",
     "Indomio (scraping, precios de oferta)", "No", "Texto de la fuente", "Pública",
     "Se anota en el procesamiento (gobernanza)",
     "¿De dónde viene el precio? (trazabilidad)"],
    ["F02", "datos_procesados/precios_vivienda.csv", "vigencia", "(anotado)",
     "Periodo de la extracción del precio", "Texto", "año", "2026", "No",
     "Año de la extracción", "Pública", "Se anota como el año de fecha_prueba",
     "¿A qué periodo corresponde el precio?"],
    ["F02", "datos_procesados/precios_vivienda.csv", "fecha_prueba", "(anotado)",
     "Fecha en que se extrajo/verificó el precio", "Fecha", "AAAA-MM-DD",
     "2026-09-27", "No", "Fecha ISO", "Pública",
     "Se anota con la fecha de ejecución del scraping/procesamiento",
     "¿Cuándo se capturó el precio? (frescura)"],
    ["F02", "datos_procesados/precios_vivienda.csv", "linaje", "(anotado)",
     "Clasificación de gobernanza del dato", "Texto", "etiqueta", "PROXY", "No",
     "OBSERVADO / ESTIMADO / PROXY", "Pública",
     "Se etiqueta como PROXY por ser precio de oferta de anuncios, no de transacción",
     "¿Qué fiabilidad tiene el precio? (es oferta, no cierre real)"],
]

# --- Hoja 3: Bitácora IA ----------------------------------------------------
# Columnas: #, Herramienta de IA, Qué le encargaron, Qué respondió,
# Cómo lo comprobaron, Resultado, ID fuente, Qué aprendieron
BITACORA = [
    ["1", "Kiro / asistente IA",
     "Encontrar la fuente oficial de población y vivienda por parròquia de Andorra",
     "Señaló el Departament d'Estadística (banc de dades, sig.govern.ad) con CSV parametrizable por tema/fecha",
     "Se descargó el CSV de población por parròquia y se abrió: separador ';', años 2020-2025 y fila TOTAL",
     "Correcto", "F01",
     "La fuente oficial existe y da CSV; el formato es ancho y trae una fila TOTAL que hay que excluir."],
    ["2", "Kiro / asistente IA",
     "Conseguir precio de vivienda por zona/barrio en Andorra",
     "Propuso portales inmobiliarios (Indomio, Idealista, Fotocasa) y a AGIA como fuente sectorial",
     "Se abrió Indomio y se hizo scraping con requests+BeautifulSoup enviando User-Agent de navegador",
     "Parcial", "F02",
     "Indomio da desglose por parròquia (y barrios solo en Andorra la Vella) pero es dato de oferta (PROXY), no transacción."],
    ["3", "Kiro / asistente IA",
     "Obtener la geometría de edificios sin depender del catastro oficial",
     "Recomendó OpenStreetMap vía Overpass API (query por área) y Geofabrik como extracto",
     "Se lanzó la query Overpass; devolvió 406 hasta añadir un User-Agent de navegador, luego respondió",
     "Parcial", "F03",
     "Overpass funciona sin llave pero exige User-Agent; pocos edificios tienen altura (building:levels)."],
    ["4", "Kiro / asistente IA",
     "Descargar transacciones inmobiliarias e indicadores económicos oficiales por API",
     "Indicó los idDivision 820 (transacciones) y 810 (económicos) del endpoint de datos de sig.govern.ad",
     "Se descargaron ambos CSV y se inspeccionó su contenido frente al nombre/tema esperado",
     "Incorrecto", "F04",
     "El contenido descargado no coincide con el nombre del archivo; ambos se descartaron del lago."],
    ["5", "Kiro / asistente IA",
     "Elegir motor de procesamiento del lago (pandas vs DuckDB) sobre los mismos crudos",
     "Comparó ambos: pandas más idiomático para melt() y limpieza de celdas; DuckDB mejor solo a gran volumen",
     "Se probaron los dos sobre el CSV de población y las celdas '7,115(+14.8%)' de Indomio",
     "Correcto", "F01",
     "Para decenas de filas gana pandas; DuckDB queda documentado como candidato si el lago crece."],
    ["6", "Kiro / asistente IA",
     "Elegir herramienta de vistas (Streamlit vs Dash) para el patrón cifra+metadato+linaje",
     "Comparó ambas: Streamlit resuelve st.metric/st.caption de forma trivial; Dash exige más composición",
     "Se prototiparon las 4 vistas sobre los mismos datos procesados",
     "Correcto", "F01",
     "Streamlit es más rápido para v1; Dash queda como candidato si se necesita interactividad avanzada."],
]


def escribe_hoja(ws, filas, fila_inicial=5):
    """Escribe una lista de filas en la hoja a partir de fila_inicial."""
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            ws.cell(row=fila_inicial + i, column=j + 1, value=valor)


def main():
    wb = openpyxl.load_workbook(RUTA_XLSX)

    # La fila 4 de cada hoja es el ejemplo (Medellín/Wikipedia), ajeno a este
    # proyecto (Andorra). El enunciado permite borrarla y el Resumen no la
    # cuenta, así que se limpia para dejar el diccionario coherente.
    for nombre_hoja, num_cols in [
        ("1. Fuentes", 16),
        ("2. Diccionario", 13),
        ("3. Bitácora IA", 8),
    ]:
        hoja = wb[nombre_hoja]
        for col in range(1, num_cols + 1):
            hoja.cell(row=4, column=col).value = None

    escribe_hoja(wb["1. Fuentes"], FUENTES)
    escribe_hoja(wb["2. Diccionario"], DICCIONARIO)
    escribe_hoja(wb["3. Bitácora IA"], BITACORA)

    wb.save(RUTA_XLSX)
    print(
        f"[OK] Diccionario rellenado: {len(FUENTES)} fuentes, "
        f"{len(DICCIONARIO)} campos, {len(BITACORA)} encargos a la IA."
    )


if __name__ == "__main__":
    main()
