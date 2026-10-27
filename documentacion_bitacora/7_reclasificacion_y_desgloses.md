# Bitácora 7 — Reclasificación de crudos mal etiquetados y desgloses de población

**Fecha de prueba:** 2026-10-26
**Tramo evaluado:** Lago / Procesamiento (normalización de crudos del Departament d'Estadística d'Andorra hacia `datos_procesados/`, linaje OBSERVADO)
**Scripts:** `scripts/procesa_indicadores_sociales.py` y `scripts/procesa_poblacion_desgloses.py`
**Requisitos relacionados:** 8.7 (entrada de bitácora con prefijo numérico que documente la reclasificación de un Crudo_MalEtiquetado y la incorporación de un Desglose_Poblacion)

## Objetivo

Dejar constancia de dos trabajos de la Parte 3 sobre crudos ya presentes en `datos_crudos/`: (1) la **reclasificación por contenido real** de dos crudos cuyo nombre de archivo engañaba sobre su contenido, y (2) la normalización de los **cinco desgloses de población** por parròquia de ancho a largo. En ambos casos el principio es el mismo: nombrar y gobernar el dato por lo que **realmente es**, sin inventar nada y sin tocar los crudos (fuente de verdad inmutable).

---

## Parte A — Reclasificación de crudos mal etiquetados

### Hallazgo: dos archivos cuyo nombre no coincide con su contenido

Al inspeccionar directamente los crudos (separador `;`, coma decimal catalana, columnas de año 2020–2025) se detectó que dos archivos oficiales estaban mal etiquetados en su nombre de fichero:

- **`oficial_820_transacciones_inmobiliarias.csv`** → el nombre sugiere "transacciones inmobiliarias", pero el contenido real son **tres umbrales de pobreza/ingresos** (`LLINDAR DE RISC DE POBRESA. 60%...`, `LLINDAR DE POBRESA. 50%...`, `LLINDAR DE POBRESA SEVERA. 40%...`), con importes en euros y coma decimal.
- **`oficial_810_indicadores_economicos.csv`** → el nombre sugiere "indicadores económicos", pero el contenido real es una única fila **`TAXA DE FECUNDITAT`** con valor decimal.

Estos dos crudos habían quedado como `excluido` en el inventario de la Parte 2 precisamente porque su nombre no permitía ubicarlos. La inspección por contenido permite ahora **reclasificarlos** y aprovecharlos.

### Decisión: nombrar por el contenido real, no por el archivo

Se crea `scripts/procesa_indicadores_sociales.py`, que lee cada crudo según su contenido real y los escribe renombrados por su significado (Indicador_Social_Reclasificado):

| Crudo mal etiquetado | Contenido real | Salida en `datos_procesados/` |
| --- | --- | --- |
| `oficial_820_transacciones_inmobiliarias.csv` | Umbrales de pobreza e ingresos (3 umbrales) | `umbrales_pobreza.csv` |
| `oficial_810_indicadores_economicos.csv` | Tasa de fecundidad | `tasa_fecundidad.csv` |

Los umbrales se reconocen **por el texto de `Descripció`** (palabras clave `RISC DE POBRESA`, `POBRESA SEVERA`, `POBRESA`) y no por el `Codi`: el código empieza por cero y algunos lectores de CSV lo interpretan como entero, perdiendo ese cero inicial. El orden de las reglas importa: "pobresa severa" se comprueba antes que "pobresa" para no confundir el umbral severo con el general.

### Coma decimal catalana

Los importes vienen con **coma como separador decimal** (`12153,39`). La función `_a_decimal(...)` convierte la coma a punto (`12153.39`) y devuelve `None` ante valores vacíos o no numéricos, de modo que la celda afectada se excluye y se registra sin inventar cifras.

### Gobernanza y crudos intactos

- Cada registro de salida lleva `fuente = "Departament d'Estadística d'Andorra"`, `vigencia` (= año), `fecha_prueba` (ISO `AAAA-MM-DD`) y `linaje = OBSERVADO`.
- Los dos indicadores se procesan de forma **independiente**: si uno falla (crudo ilegible o contenido que no casa lo esperado), el otro se procesa igualmente.
- Si el contenido de un crudo no casa lo esperado, se registra la **discrepancia** por consola en español y **no se muta** el archivo original.
- La escritura usa `gobernanza.escribe_csv` (separador `;`, UTF-8), que **rechaza** cualquier escritura dentro de `datos_crudos/`. Los crudos `oficial_820` y `oficial_810` quedan intactos; solo se leen.
- En el `Inventario_Fuentes`, `oficial_820` y `oficial_810` se anotan apuntando a su reclasificación (motivo real) conservando su `ID_Fuente`; `umbrales_pobreza.csv` y `tasa_fecundidad.csv` entran como `integrado`/OBSERVADO.

---

## Parte B — Desgloses de población por parròquia

### Hallazgo: cinco desgloses OBSERVADO en formato ancho con orden variable

El Departament d'Estadística d'Andorra publica cinco crudos de desglose de población por parròquia, todos en **formato ancho** (columnas `Codi;Descripció;2020..2025`, enteros):

| Dimensión | Archivo | Orden de los segmentos de `Descripció` |
| --- | --- | --- |
| `edad_5` | `estadistica_id1091_..._edat_(trams_5_anys).csv` | parròquia → categoría |
| `edad_1` | `estadistica_id1092_..._edat_(trams_1_any).csv` | parròquia → categoría |
| `sexo` | `estadistica_id1093_..._i_sexe.csv` | parròquia → categoría |
| `nacionalidad` | `estadistica_id1094_..._per_nacionalitat_i_parròquia.csv` | **categoría → parròquia (orden invertido)** |
| `lugar_nacimiento` | `estadistica_id1137_..._lloc_de_naixement.csv` | parròquia → categoría (capitalización tipo título) |

El hallazgo clave es que el **orden de los segmentos del patrón `CATEGORIA. PARRÒQUIA. SUBCATEGORIA` varía entre crudos**: la nacionalidad invierte el orden (la parròquia va en el segundo segmento), y el crudo de lugar de nacimiento viene en capitalización tipo título en vez de mayúsculas.

### Decisión: un parser configurable por dimensión

Se crea `scripts/procesa_poblacion_desgloses.py` con un **parser parametrizado por dimensión** (diseño P8), en vez de un patrón rígido único. `CONFIGURACION_DIMENSIONES` declara, por dimensión, el `archivo`, el `prefijo` a retirar, el `indice_parroquia` y el `indice_categoria` dentro de los segmentos. Así, la nacionalidad simplemente declara `indice_parroquia = 1`, `indice_categoria = 0` y el mismo código sirve para las cinco dimensiones.

El mapeo de la parròquia cruda a una de las **7 canónicas** se hace tras aplicar `.upper` sobre el segmento, lo que cubre tanto los crudos en mayúsculas como el de lugar de nacimiento en capitalización tipo título.

### Salida: una tabla larga única

Las cinco dimensiones se normalizan de ancho a largo y se concatenan en **un solo archivo** `datos_procesados/poblacion_desgloses.csv` con una columna `dimension` que permite filtrar (coherente con el formato largo canónico de `procesa_poblacion.py`). Se prefirió una tabla larga única frente a cinco CSV separados para reducir superficie (una sola carga, una sola entrada de inventario) y ganar cohesión. Columnas: `parroquia;dimension;categoria;anio;valor;fuente;vigencia;fecha_prueba;linaje`.

### Exclusiones sin inventar

Cada exclusión se registra por consola en español, sin fabricar cifras:

- Filas cuyo `Descripció` no casa el patrón de su dimensión o cuya parròquia no se reconoce entre las 7 canónicas: se omite la fila completa.
- Celdas cuyo valor está vacío, no es numérico, no es entero o es negativo: se omite ese (parròquia, categoría, año) concreto.
- Años esperados cuya columna falta en el crudo: se omite ese año y se avisa.
- Un desglose ausente o ilegible se omite **sin detener** los demás.

### Gobernanza y crudos intactos

Cada registro lleva `fuente = "Departament d'Estadística d'Andorra"`, `vigencia` (= año), `fecha_prueba` (ISO) y `linaje = OBSERVADO`. El resultado se filtra con `gobernanza.filtra_registros_validos` y se escribe con `gobernanza.escribe_csv`, que nunca escribe en `datos_crudos/`: los cinco crudos de desglose quedan intactos.

---

## Cómo ejecutarlo

Ambos procesadores forman parte del pipeline (`ejecuta_pipeline.py`) y también pueden ejecutarse de forma individual desde `scripts/`:

```powershell
python scripts/procesa_indicadores_sociales.py
python scripts/procesa_poblacion_desgloses.py
```

## Conclusión

Se recuperaron dos crudos antes excluidos reclasificándolos **por su contenido real** (umbrales de pobreza y tasa de fecundidad) en vez de por su nombre de archivo engañoso, y se integraron los **cinco desgloses de población** mediante un parser configurable que absorbe el orden variable de los segmentos (incluida la inversión de la nacionalidad). Todo con linaje OBSERVADO, conversión de la coma decimal catalana cuando aplica, exclusiones documentadas sin inventar cifras y los crudos originales intactos como fuente de verdad. Queda registrado aquí con prefijo numérico para la trazabilidad exigida por el proyecto.
