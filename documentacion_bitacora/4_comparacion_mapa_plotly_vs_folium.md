# Bitácora 4 — Comparación tramo Mapa: Plotly Express vs Folium/pydeck

**Fecha de prueba:** 2026-09-27
**Tramo evaluado:** Mapa / Visualización geoespacial (coropletas por parròquia con un indicador seleccionable y su gobernanza)
**Requisitos relacionados:** 1.1 (coropletas de las 7 parròquies con indicador seleccionable y su gobernanza), 11.5 y 11.7 (acceso ético a la fuente del GeoJSON de límites)

## Objetivo

El enunciado del curso exige probar **al menos 2 herramientas sobre los mismos datos** en cada tramo con decisión no trivial, y justificar la elección en la bitácora. En la Parte 2 el tramo con decisión nueva es el **Mapa**: dibujar un coropletas por parròquia a partir de un GeoJSON de límites administrativos. Aquí se documenta la comparación entre **Plotly Express** y **Folium/pydeck**, dejando constancia de que la decisión fue evaluada y no asumida.

## Datos usados (los mismos para ambas herramientas)

Ambas herramientas se probaron sobre el **mismo** par de insumos, sin tocar los crudos (fuente de verdad inmutable):

- `datos_crudos/parroquias_andorra.geojson` — límites administrativos de las **7 parròquies** de Andorra (`admin_level=7`, `boundary=administrative`) descargados de OpenStreetMap vía Overpass, licencia **ODbL** con atribución. Ver bitácora 5 para el detalle de la descarga ética.
- La **misma** tabla de indicador por parròquia (parròquia → valor + gobernanza): población total del año máximo (OBSERVADO) o precio de venta €/m² (PROXY), según el indicador seleccionable.

El objetivo era comprobar cuál de las herramientas resuelve mejor el patrón de la `Vista_Mapa`: **coropletas por polígono + leyenda de color + selección de parròquia + cifra gobernada**, sin introducir servicios de pago ni tokens.

## Hallazgo previo sobre el GeoJSON disponible

Antes de comparar herramientas se verificó el contenido real de `datos_crudos/edificios_andorra.geojson` (el único GeoJSON heredado): es un `FeatureCollection` de **edificios individuales** de OpenStreetMap (polígonos con `building`, `name`, `name:ca`), licencia ODbL. **No contiene límites administrativos de parròquia**: no hay campo de parròquia, ni `admin_level`, ni `boundary`.

Conclusión del hallazgo: ese archivo **no sirve** para un coropletas por parròquia, porque un coropletas necesita un polígono por cada una de las 7 parròquies y el archivo sólo tiene edificios. Por eso la Parte 2 incorpora un GeoJSON nuevo de límites (`parroquias_andorra.geojson`) y `edificios_andorra.geojson` queda en el inventario como `candidato` (capa de detalle urbano para una futura iteración), no como base del mapa.

## Criterios y resultado de la comparación

| Criterio | Plotly Express (`choropleth_map`) | Folium / pydeck |
|----------|-----------------------------------|-----------------|
| Qué requiere para empezar | Sólo `plotly`; estilo `open-street-map` usable sin token | Folium requiere `folium` + `streamlit-folium` (dependencia extra); pydeck viene con Streamlit (`st.pydeck_chart`) |
| Licencia | MIT (Plotly) | BSD (Folium) / MIT (pydeck) + ODbL de los tiles OSM |
| ¿Token/servicio de pago? | No: `open-street-map` no pide token de Mapbox | No en teoría, pero varios estilos de pydeck piden token Mapbox; se evitarían usando estilos libres |
| Coropletas por polígono GeoJSON | Nativo y declarativo: `choropleth_map(geojson=..., locations=..., color=...)` | pydeck `GeoJsonLayer` (más verboso, por capas); Folium `Choropleth` (cómodo pero añade capa HTML) |
| Integración con Streamlit | `st.plotly_chart` nativo; hover/leyenda nativos | pydeck nativo; Folium sólo vía `streamlit-folium` |
| Leyenda y escala de color | Automática y configurable (`color_continuous_scale`, `range_color`) | Manual en pydeck; automática en Folium |
| Selección de parròquia | `hover`/`click` con `customdata`; captura con `st.plotly_chart(on_select=...)` | Folium soporta tooltips; captura de clic vía `streamlit-folium` |
| Curva de aprendizaje del equipo | Baja (API declarativa tipo pandas) | Media (pydeck por capas; Folium por objetos) |
| Responsive / móvil | Buena con `use_container_width=True` | pydeck buena; Folium aceptable |

## Decisión (Parte 2): Plotly Express con estilo `open-street-map`

Se elige **Plotly Express** (`choropleth_map` con estilo `open-street-map`, sin token) para la `Vista_Mapa`. Los motivos:

- **Una sola dependencia:** basta con `plotly` (ya fijado en `requirements.txt`), sin necesidad de `streamlit-folium`. Menos superficie de dependencias que mantener.
- **Sin token ni servicio de pago:** el estilo `open-street-map` renderiza el mapa base sin token de Mapbox, coherente con el principio de ejecución local y gratuita del proyecto.
- **Coropletas declarativo:** `choropleth_map(geojson=..., locations=..., color=...)` resuelve el coloreado por polígono de forma directa, con leyenda y escala de color automáticas (`color_continuous_scale`, `range_color`).
- **Integración nativa con Streamlit:** `st.plotly_chart(..., use_container_width=True)` ofrece hover, leyenda y buen comportamiento responsive en móvil sin trabajo extra.

## Por qué NO Folium/pydeck (alternativa registrada)

Ambas se probaron sobre los mismos datos y se descartan, dejándolas documentadas como alternativa:

- **Folium** resuelve bien el coropletas (`Choropleth`) y los tooltips, pero su integración con Streamlit exige la **dependencia extra** `streamlit-folium`, y renderiza como una capa HTML incrustada en lugar de un gráfico nativo.
- **pydeck** está disponible de serie en Streamlit (`st.pydeck_chart`), pero dibujar el coropletas con `GeoJsonLayer` es **más verboso** (configuración por capas y de la leyenda manual), y varios de sus estilos de mapa base **piden token de Mapbox**, lo que contradice el requisito de no usar servicios de pago ni credenciales.

Para el alcance de la Parte 2 (coropletas de 7 polígonos con un indicador seleccionable), la ventaja de Plotly Express en simplicidad y sin token es decisiva. Folium/pydeck quedan como candidatos para una futura iteración con interactividad geoespacial más compleja (capas múltiples, animaciones, detalle urbano por edificio).

## Plan B (documentado)

Si no se consigue el GeoJSON de límites administrativos (p. ej. bloqueo de Overpass; ver bitácora 5), la `Vista_Mapa` **degrada** a una representación por **puntos/centroides** de las 7 parròquies con `st.map` (un marcador por parròquia según el indicador), sin dependencias adicionales. En ambos casos cada parròquia conserva su **cifra gobernada** (valor + metadato + linaje), y se deja constancia en la bitácora de que el coropletas quedó pendiente.

## Conclusión

Se elige **Plotly Express** (`open-street-map`, sin token) para el tramo Mapa de la Parte 2. La comparación con **Folium/pydeck** sobre los mismos datos de parròquia queda registrada aquí para trazabilidad de la decisión metodológica exigida por el curso.
