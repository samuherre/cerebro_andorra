# Bitácora 3 — Comparación tramo Vistas: Streamlit vs Dash

**Fecha de prueba:** 2026-09-27
**Tramo evaluado:** Vistas / Presentación (panel que muestra los indicadores procesados desde `datos_procesados/`)
**Requisitos relacionados:** 5.1 (vista de población por parròquia), 6.1 (vista de precios de vivienda), 7.1 (vista de indicadores con su metadato), 8.1 (visualización del linaje de gobernanza en cada cifra)

## Objetivo

El enunciado del curso exige probar **al menos 2 herramientas sobre los mismos datos** en cada tramo con decisión no trivial, y justificar la elección en la bitácora. Aquí se documenta la comparación entre **Streamlit** y **Dash (Plotly)** para el tramo de Vistas, dejando constancia de que la decisión fue evaluada y no asumida.

## Datos usados (los mismos para ambas herramientas)

Ambas herramientas se contrastaron sobre los **mismos datos procesados** generados por el tramo de Lago/Procesamiento (ver bitácora 2), sin volver a tocar los crudos (fuente de verdad inmutable):

- Población por parròquia en formato largo (resultado de la transformación ancho→largo, sin la fila `TOTAL`).
- Precios de vivienda de Indomio ya limpios (precio numérico y variación separados), marcados con linaje PROXY.
- Indicadores con su metadato de gobernanza asociado (`fuente`, `vigencia`, `fecha_prueba`, `linaje` ∈ {OBSERVADO, ESTIMADO, PROXY}).

El objetivo era comprobar cuál de las dos herramientas resuelve mejor el patrón repetido en las 4 vistas de v1: **cifra + metadato + linaje**.

## Criterios y resultado de la comparación

| Criterio | Streamlit | Dash (Plotly) |
|----------|-----------|---------------|
| Rapidez para prototipar 4 vistas | Muy alta (script lineal) | Media (callbacks explícitos) |
| Componentes de cifra + metadato | Trivial (`st.metric`, `st.caption`) | Requiere más composición manual |
| Coste / ejecución local | Gratis, `streamlit run` local | Gratis, pero más configuración |
| Curva de aprendizaje | Baja | Media (modelo de callbacks) |

## Decisión: Streamlit

Se elige **Streamlit**, herramienta ya adoptada en el steering del proyecto. Se registra la comparación con Dash para dejar constancia de que la decisión fue **evaluada y no asumida**. Los motivos:

- **Velocidad de prototipado:** el modelo de script lineal de Streamlit permite montar las 4 vistas de v1 mucho más rápido que el modelo de callbacks explícitos de Dash.
- **Patrón "cifra + metadato + linaje":** con `st.metric` (cifra) y `st.caption` (metadato/linaje) el patrón se resuelve de forma trivial, mientras que en Dash exige más composición manual de componentes.
- **Coste y ejecución local:** ambas son gratuitas, pero Streamlit se lanza directamente con `streamlit run` con menos configuración.
- **Curva de aprendizaje:** baja en Streamlit frente a la curva media que impone el modelo de callbacks de Dash, coherente con el perfil del equipo.

Estas ventajas son suficientes para las 4 vistas de v1 (población, precios, indicadores y visualización de linaje), que no requieren la interactividad avanzada donde Dash empezaría a compensar.

## Dash como candidato futuro

Se deja **Dash (Plotly) documentado como candidato** para cuando las vistas necesiten interactividad más compleja (filtros encadenados, callbacks entre múltiples gráficos, aplicaciones multipágina con estado). En ese escenario su modelo de callbacks aportaría control fino que hoy no es necesario. La reevaluación quedaría registrada en una nueva entrada de bitácora cuando el alcance lo justifique.

## Conclusión

Se elige **Streamlit** para el tramo de Vistas de la v1. La comparación con Dash queda registrada aquí para trazabilidad de la decisión metodológica exigida por el curso.
