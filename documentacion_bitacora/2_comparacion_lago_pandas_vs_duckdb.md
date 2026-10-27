# Bitácora 2 — Comparación tramo Lago/Procesamiento: pandas vs DuckDB

**Fecha de prueba:** 2026-09-27
**Tramo evaluado:** Lago / Procesamiento (limpieza y normalización de datos crudos hacia `datos_procesados/`)
**Requisitos relacionados:** 1.1 (lectura y transformación de población por parròquia), 2.1 (lectura y limpieza de precios de vivienda de Indomio)

## Objetivo

El enunciado del curso exige probar **al menos 2 herramientas sobre los mismos datos** en cada tramo con decisión no trivial, y justificar la elección en la bitácora. Aquí se documenta la comparación entre **pandas** y **DuckDB** para el tramo de procesamiento, dejando constancia de que la decisión fue evaluada y no asumida.

## Datos usados (los mismos para ambas herramientas)

Ambas herramientas se probaron sobre los **mismos** archivos crudos, sin modificarlos (los crudos son fuente de verdad inmutable):

- `datos_crudos/estadistica_id798_població_població_per_parròquia.csv` — población por parròquia en formato ancho (una columna por año), separador `;`, codificación UTF-8. Requiere transformación ancho→largo y exclusión de la fila `TOTAL`.
- `datos_crudos/precios_vivienda_indomio.csv` — precios de vivienda (PROXY), separador tabulador. Contiene celdas "sucias" que combinan valor y variación interanual, p. ej. `7,115(+14.8%)`, que hay que separar en precio numérico (7115) y variación (+14.8).

## Criterios y resultado de la comparación

| Criterio | pandas | DuckDB |
|----------|--------|--------|
| Facilidad para la transformación ancho→largo | Directa con `melt()` | Requiere `UNPIVOT` (SQL), menos idiomático para el equipo |
| Parseo de celdas sucias `7,115(+14.8%)` | Natural con `str`/`re` por celda | Menos ergonómico; regex en SQL más verboso |
| Rendimiento en este volumen | Sobrado (decenas de filas) | Sobrado; su ventaja aparece en millones de filas |
| Gestión de memoria | Carga todo en RAM; irrelevante aquí (datos diminutos) | Motor columnar con spilling a disco; ventaja sólo en grandes volúmenes |
| Curva de aprendizaje del equipo | Ya conocido (steering usa Python/CSV) | Añade SQL analítico; curva extra |
| Integración con Streamlit | Nativa (`st.dataframe`, `st.cache_data`) | Requiere convertir a DataFrame igualmente |

## Decisión (v1): pandas

Para el volumen de esta feature (decenas de filas) las ventajas de DuckDB en gestión de memoria y rendimiento **no se materializan**. En cambio, pandas ofrece:

- `melt()` para la transformación ancho→largo de la población de forma directa.
- Manipulación de strings y expresiones regulares por celda más natural para limpiar las celdas de Indomio del tipo `7,115(+14.8%)`.
- Integración nativa con Streamlit (`st.dataframe`, `st.cache_data`), que es el tramo de Vistas de esta misma feature.
- Menor curva de aprendizaje, coherente con el steering del proyecto (Python 3 + CSV).

## DuckDB como candidato futuro

Se deja **DuckDB documentado como candidato** para cuando el lago crezca: desgloses por edad, sexo y nacionalidad, y series históricas largas. En ese escenario, su motor columnar y su gestión de memoria con *spilling* a disco sí aportarían ventaja frente a cargar todo en RAM con pandas. La reevaluación quedaría registrada en una nueva entrada de bitácora cuando el volumen lo justifique.

## Conclusión

Se elige **pandas** para el tramo Lago/Procesamiento de la v1. La comparación con DuckDB queda registrada aquí para trazabilidad de la decisión metodológica exigida por el curso.
