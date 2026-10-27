# Cerebro Andorra · Parte 2 · Visualización

Sistema de ingeniería de datos y analítica territorial del Principado de Andorra,
construido bajo una arquitectura lakehouse. Reúne, limpia y prepara indicadores
clave (población, vivienda, turismo e inversiones) y los presenta en una
aplicación web con el principio rector **"0 cifras sin fuente, sin vigencia y sin
fecha de prueba"**.

## Integrantes del grupo

> **TODO:** reemplazar por los nombres reales de los integrantes antes de la
> entrega. No inventar personas; dejar el marcador hasta confirmarlos.

- [Nombres del grupo]

Los nombres también se muestran de forma visible en la barra lateral de la app
(`app/streamlit_app.py`, variable `_EQUIPO`).

## Enlace al repositorio

> **TODO:** reemplazar el marcador por la URL real del repositorio.

- Repositorio: [URL del repositorio]

> **Nota (Req 9.6 / 9.7):** el enlace al repositorio forma parte de la entrega.
> Si al revisarlo el enlace no es accesible o apunta a una ubicación inexistente,
> se debe indicar de forma visible junto a este apartado un mensaje de error que
> señale que el enlace no es válido, conservando el resto del contenido del
> README. La comprobación de accesibilidad del enlace es manual.

## Enlace al Despliegue público

> **TODO:** reemplazar el marcador por la URL pública real una vez publicada la
> app en Streamlit Community Cloud.

- Despliegue público (Streamlit Community Cloud): [URL de Streamlit Community Cloud]

El despliegue usa únicamente servicios y llaves gratuitos, sin tarjeta de crédito
y sin servicios de pago (Req 8.1, 8.9). El punto de entrada es
`app/streamlit_app.py` y las dependencias están fijadas en `requirements.txt`.

## Decisión de qué datos mostrar

El sistema integra **cuatro fuentes** en el lago de datos, elegidas por responder
a las preguntas de la Entrega 1 (cuánta gente vive aquí, cuánto vale el metro
cuadrado, cuánto pesa el turismo, cómo se mueve la inversión inmobiliaria) y por
tener un linaje de datos auditable. Cada dato se clasifica según la taxonomía de
gobernanza del proyecto: **OBSERVADO** (oficial / censo / transacción real),
**ESTIMADO** (consenso del sector) o **PROXY** (dato de mercado dinámico de la web,
que representa oferta y no transacción real).

| Fuente | Dominio | Linaje | Por qué se muestra |
|--------|---------|--------|--------------------|
| Población por parròquia (Departament d'Estadística, `estadistica_id798`) | Población | OBSERVADO | Cifra base del territorio; alimenta el mapa y la vista de población. |
| Precios de vivienda (scraping de Indomio) | Mercado inmobiliario | **PROXY** | Aporta granularidad geográfica de precios; se muestra siempre como precio de oferta, no como transacción real. |
| Presupuesto de turismo (`estadistica_681`, Andorra Turisme SAU) | Turismo | OBSERVADO | Mide el peso del turismo (gasto de funcionamiento y total del presupuesto). |
| Inversiones inmobiliarias (`estadistica_2729`) | Economía / inmobiliario | OBSERVADO | Serie oficial del número de inversiones por año; cuarta fuente integrada. |

Criterio de selección: se priorizan fuentes **oficiales (OBSERVADO)** y se admite
una fuente **PROXY** (Indomio) únicamente para ganar granularidad de precios por
zona, dejando su naturaleza de oferta siempre explícita. Las cifras que no pueden
sostenerse con fuente, vigencia y fecha de prueba no se muestran.

## Evaluación de si los datos se pueden usar

Se revisó la procedencia y condiciones de uso de cada fuente antes de integrarla:

- **API y portal del Departament d'Estadística d'Andorra (`sig.govern.ad`)** —
  datos públicos oficiales de estadística (población, turismo, inversiones). Son
  datos de interés público publicados por la administración; se usan como
  OBSERVADO citando la fuente, la vigencia y la fecha de prueba de cada cifra.
  El texto literal de la licencia de cada dataset se registra en el
  `Diccionario_Datos` (Excel en `contexto/`).
- **OpenStreetMap vía Overpass API (límites de parròquia, GeoJSON)** — publicado
  bajo **ODbL (Open Database License)**, que permite el uso y la redistribución
  con **atribución** y manteniendo la misma licencia para las bases derivadas. El
  mapa atribuye a OpenStreetMap. La descarga se hace de forma ética (ver
  `Bitacora_Herramientas` y la bitácora de descarga).
- **Indomio (scraping web)** — se trata como **PROXY**: precios de **oferta**
  publicados en anuncios, no transacciones cerradas. No se publican anuncios
  individuales ni datos de personas; solo se usan agregados por zona como señal de
  mercado, y la app etiqueta esos precios como PROXY/oferta de forma visible. Se
  documenta el origen y la fecha de extracción; ante medidas anti-bot se registra
  el hallazgo en la bitácora en lugar de forzar el acceso.

Conclusión: las cuatro fuentes son utilizables para el fin del proyecto siempre que
se respete la atribución (OSM/ODbL), se cite la fuente oficial (Estadística) y se
mantenga el etiquetado PROXY de Indomio. Las condiciones literales por fuente
quedan en el `Diccionario_Datos`.

## Cómo se protegieron los datos

- **Agregación por zona, nunca individuos:** todo dato relativo a personas se
  presenta agregado por parròquia o zona, con valores que representan a dos o más
  personas. No se exponen registros ni atributos individuales identificables
  (Req 10.6).
- **Principio "0 cifras sin fuente, vigencia ni fecha de prueba":** cada cifra de
  la app lleva su `Metadato_Cifra` (fuente, vigencia y fecha de prueba) y su
  `Etiqueta_Linaje` (OBSERVADO / ESTIMADO / PROXY). Las cifras que no cumplen se
  omiten y se registra el motivo en la bitácora (Req 10.1–10.5).
- **Sin PII en el repositorio:** no se versiona ningún dato de personas
  identificables ni credenciales. Los precios de Indomio se usan como agregados de
  oferta, no como anuncios individuales.
- **Compuerta de acceso opcional y secreta:** si se activa la `Compuerta_Acceso`,
  la clave se compara contra un valor almacenado en el servidor mediante
  `st.secrets` o variable de entorno. La clave **nunca** se escribe en un archivo
  versionado: `.streamlit/secrets.toml` queda fuera del repositorio (`.gitignore`).
  Si la clave apareciera en cualquier archivo versionado, el sistema se considera
  no conforme (Req 8.7, 8.8).
- **Crudos inmutables:** el pipeline nunca escribe en `datos_crudos/`; solo lee de
  ahí y escribe en `datos_procesados/`, preservando la fuente de verdad.

## Compuerta de acceso (opcional)

La `Compuerta_Acceso` es **opcional** y está **desactivada por defecto**. Si no se
configura ninguna clave, la app arranca con normalidad y no pide nada. Solo cuando
existe una clave configurada en el servidor, la app pide esa clave antes de mostrar
el contenido.

Puntos clave de gobernanza (Req 8.7, 8.8):

- La clave se compara **siempre en el servidor**, nunca en el cliente. La
  implementación usa una comparación de tiempo constante (`hmac.compare_digest`).
- La clave se lee de `st.secrets` o, como alternativa en local, de la variable de
  entorno `CLAVE_ACCESO`. No se escribe ni se guarda la clave introducida por el
  usuario.
- La clave **nunca** se versiona. El archivo `.streamlit/secrets.toml` está incluido
  en `.gitignore`, por lo que no llega al repositorio. Si la clave apareciera en
  cualquier archivo versionado, el sistema se considera **no conforme**.

### Cómo activarla

**En local** — crea el archivo `.streamlit/secrets.toml` (ignorado por git) con un
valor claramente propio (no reutilices el ejemplo):

```toml
# .streamlit/secrets.toml  (NO versionar: está en .gitignore)
CLAVE_ACCESO = "CAMBIA_ESTA_CLAVE"
```

O bien, usando una variable de entorno (PowerShell):

```powershell
$env:CLAVE_ACCESO = "CAMBIA_ESTA_CLAVE"
streamlit run app/streamlit_app.py
```

**En Streamlit Community Cloud** — configura el secreto desde la UI (ver la sección
de despliegue), nunca en un archivo del repositorio.

### Cómo se compara en el código

La comparación vive en `app/streamlit_app.py` (función `compuerta_acceso`). En
esencia:

```python
import hmac, os
import streamlit as st

# La clave se lee del servidor: st.secrets o variable de entorno.
clave_esperada = st.secrets.get("CLAVE_ACCESO") or os.environ.get("CLAVE_ACCESO")

if clave_esperada:  # compuerta activa solo si hay clave configurada
    introducida = st.text_input("Clave de acceso", type="password")
    if introducida and hmac.compare_digest(str(introducida), str(clave_esperada)):
        ...  # acceso concedido
    else:
        st.stop()  # sin clave válida no se muestra la app
# si clave_esperada es None, la compuerta está desactivada y la app sigue normal
```

## Despliegue en Streamlit Community Cloud

El `Despliegue_Publico` se publica en **Streamlit Community Cloud**, que es
**gratuito y no requiere tarjeta de crédito** (Req 8.1, 8.9, 11.1). Pasos:

1. **Repositorio público en GitHub.** Sube el proyecto a un repositorio público (o
   da acceso a Streamlit Cloud al repositorio privado). Asegúrate de que
   `.gitignore` excluye `.streamlit/secrets.toml` para no filtrar la clave.
2. **Archivo de entrada.** El punto de entrada de la app es
   `app/streamlit_app.py`. Se indica tal cual en el campo *Main file path* al crear
   la app en Streamlit Cloud.
3. **Dependencias.** Streamlit Cloud instala automáticamente las dependencias
   fijadas en `requirements.txt` (todas con versión exacta `==`, sin rangos
   abiertos — Req 11.2). No hace falta configurar nada extra.
4. **Crear la app.** En <https://share.streamlit.io> → *New app* → selecciona el
   repositorio, la rama y escribe `app/streamlit_app.py` como *Main file path*.
   Pulsa *Deploy*. La app queda publicada en una URL pública.
5. **Configurar los Secrets (solo si activas la compuerta).** En la UI de la app:
   *Settings* → *Secrets*, y añade la clave en formato TOML (NO en el repositorio):

   ```toml
   CLAVE_ACCESO = "CAMBIA_ESTA_CLAVE"
   ```

   Streamlit Cloud inyecta esos valores en `st.secrets` en tiempo de ejecución. Al
   guardarlos, la app se reinicia y la compuerta queda activa. Si no configuras
   ningún secreto, la compuerta permanece desactivada y la app es pública.
6. **Verificar.** Abre la URL pública y comprueba que la pantalla inicial carga
   (HTTP 200) y que los nombres del grupo son visibles en la barra lateral
   (Req 8.2, 8.3). Copia esa URL al apartado *Enlace al Despliegue público* de este
   README.

## Herramienta de visualización seleccionada

**Streamlit + Plotly Express.**

- **Streamlit** como framework de la aplicación web: permite construir las vistas
  (Panorama, Población, Vivienda, Fuentes, Mapa, Preguntas y Economía) con el
  patrón "cifra + metadato + linaje" de forma directa (`st.metric`, `st.caption`,
  `st.expander`/`st.popover` para el detalle de gobernanza a un clic) y se despliega
  gratis en Streamlit Community Cloud. Es responsive en móvil con
  `use_container_width=True`.
- **Plotly Express** para el mapa de coropletas por parròquia, usando el estilo
  `open-street-map` **sin token** ni servicio de pago. Dibuja el coropletas por
  polígono de forma declarativa, con leyenda y escala de color automáticas, y se
  integra de forma nativa con Streamlit.

La justificación completa frente a las alternativas probadas está en
`Bitacora_Herramientas`.

## Bitacora_Herramientas

Se probaron al menos dos herramientas sobre los **mismos datos** en cada tramo con
decisión no trivial: el **Mapa** (coropletas por parròquia) y las **Vistas**
(framework de UI). Para cada herramienta se documentan los seis elementos exigidos.

### Tramo Mapa — datos: GeoJSON de límites de las 7 parròquies + tabla de indicador por parròquia

#### Opción A · Plotly Express (`choropleth_map` / `choropleth_mapbox`) — SELECCIONADA

1. **Qué requirió para empezar:** instalar `plotly` (una sola dependencia). Es
   usable sin token usando el estilo de mapa base `open-street-map` /
   `carto-positron`.
2. **Licencia:** MIT (Plotly). Los tiles base son de OpenStreetMap (ODbL, con
   atribución).
3. **Dónde quedan los datos al publicar:** el GeoJSON y la tabla de indicador se
   sirven desde el propio repositorio en Streamlit Community Cloud; el render del
   mapa ocurre en el cliente. No se envían datos a un servicio de terceros ni se
   requiere cuenta de mapas.
4. **Qué resolvió:** coropletas por polígono de forma declarativa
   (`choropleth_map(geojson=..., locations=..., color=...)`), leyenda y escala de
   color automáticas (`color_continuous_scale`, `range_color`), interactividad de
   hover y buen comportamiento responsive con `use_container_width=True`.
5. **Qué no resolvió:** devolver el clic de selección de una parròquia requiere
   configurar `st.plotly_chart(on_select=...)`; es un paso extra pero no bloqueante.
6. **Por qué quedó seleccionada:** menor número de dependencias, integración nativa
   con Streamlit, leyenda/escala automáticas y curva de aprendizaje baja (API
   declarativa tipo pandas). Cubre el coropletas sin token ni servicios de pago.

#### Opción B · pydeck / Folium — NO seleccionada

1. **Qué requirió para empezar:** `pydeck` viene incluido con Streamlit
   (`st.pydeck_chart`); **Folium** requiere dependencias extra (`folium` +
   `streamlit-folium`).
2. **Licencia:** MIT (pydeck) / BSD (Folium), más ODbL de los tiles de OSM.
3. **Dónde quedan los datos al publicar:** igual que Plotly, los datos se sirven
   desde el repositorio; sin embargo, algunos estilos de pydeck piden un token de
   Mapbox (se evitaría usando estilos libres).
4. **Qué resolvió:** pydeck dibuja el coropletas con `GeoJsonLayer`; Folium ofrece
   `Choropleth` cómodo y tooltips de selección vía `streamlit-folium`.
5. **Qué no resolvió:** pydeck es más verboso (capas manuales, leyenda manual);
   Folium añade una dependencia y una capa HTML extra, y algunos estilos de pydeck
   arrastran la necesidad de token de pago.
6. **Por qué no quedó seleccionada:** dependencias adicionales
   (`streamlit-folium`) o verbosidad de las capas (pydeck) frente a la solución de
   una sola dependencia de Plotly. Quedan documentadas como alternativa válida por
   si se necesita en una iteración futura.

> **Plan B del mapa:** si no se consigue el GeoJSON de límites administrativos
> (p. ej. bloqueo de Overpass), la `Vista_Mapa` degrada a una representación por
> puntos/centroides de las 7 parròquies con `st.map`, sin dependencias
> adicionales, dejando constancia en la bitácora.

### Tramo Vistas — datos: cifras procesadas en `datos_procesados/` (decisión reafirmada de la v1)

#### Opción A · Streamlit — SELECCIONADA

1. **Qué requirió para empezar:** instalar `streamlit`; sin build ni servidor
   propio, se ejecuta con `streamlit run app/streamlit_app.py`.
2. **Licencia:** Apache 2.0.
3. **Dónde quedan los datos al publicar:** la app y los CSV procesados viven en el
   repositorio y se despliegan en Streamlit Community Cloud (gratis, sin tarjeta);
   el estado se mantiene en el servidor de la sesión, sin terceros de pago.
4. **Qué resolvió:** patrón directo "cifra + metadato + linaje" con
   `st.metric`/`st.caption`, detalle de gobernanza a un clic con
   `st.expander`/`st.popover`, navegación por vistas, cacheo con `st.cache_data` y
   responsive móvil con `use_container_width=True`.
5. **Qué no resolvió:** menos control fino del layout y del routing que un
   framework web completo; suficiente para el alcance del proyecto.
6. **Por qué quedó seleccionada:** velocidad de prototipado, despliegue gratuito
   sencillo y encaje natural con el patrón de gobernanza de cifras. Se reutiliza en
   todas las vistas nuevas sin introducir un segundo framework de UI.

#### Opción B · Dash — NO seleccionada

1. **Qué requirió para empezar:** instalar `dash` (sobre Flask/React); exige
   definir callbacks y layout de forma más explícita.
2. **Licencia:** MIT.
3. **Dónde quedan los datos al publicar:** requeriría un hosting con servidor
   Flask; el despliegue gratuito sin tarjeta es menos inmediato que en Streamlit
   Community Cloud.
4. **Qué resolvió:** mayor control del layout y de la interactividad por callbacks;
   buena integración con Plotly.
5. **Qué no resolvió:** más código repetitivo (callbacks, ids) para el patrón
   simple "cifra + metadato + linaje"; despliegue gratuito menos directo.
6. **Por qué no quedó seleccionada:** sobredimensionado para el alcance; Streamlit
   logra el mismo resultado con menos fricción y mejor ruta de despliegue gratuito.
   La comparación se revisó en la Parte 2 y la decisión de la v1 sigue vigente.

## Bitacora_IA

Se usó asistencia de IA de forma acotada y verificando siempre contra los datos y
los requisitos. Resumen honesto:

- **Aciertos:**
  - Acelerar el andamiaje de los procesadores nuevos (turismo, inversiones)
    reutilizando el patrón ancho→largo ya existente, en lugar de reinventarlo.
  - Redactar y organizar documentación (este README, bitácoras y comentarios) en
    español de forma consistente.
  - Proponer la comparación estructurada de herramientas de mapa y de UI sobre los
    mismos datos.
- **Errores / límites detectados:**
  - La IA asumió inicialmente que `edificios_andorra.geojson` servía para el
    coropletas por parròquia; la inspección directa del archivo mostró que solo
    contiene edificios, no límites administrativos. Se corrigió añadiendo un
    extractor ético del GeoJSON de límites y un Plan B.
  - Hubo que ajustar manualmente la normalización de la coma decimal y los rangos
    de validación para que coincidieran con el dato real.
- **Criterio de uso:** la IA no decide la gobernanza de los datos ni inventa
  cifras; toda cifra proviene de `datos_procesados/` y se verifica con su fuente,
  vigencia y fecha de prueba.

## Reflexión sobre datos

Trabajar con fuentes oficiales de un país pequeño como Andorra mostró lo valioso de
separar con rigor lo **observado** de lo que es solo **proxy**. La tentación de
presentar los precios de oferta de Indomio como "el precio real" habría sido un
error de gobernanza; etiquetarlos siempre como PROXY mantiene honesta la lectura.
El principio "0 cifras sin fuente, sin vigencia y sin fecha de prueba" obligó a
renunciar a cifras atractivas pero no trazables, y eso mejoró la calidad del
conjunto: es preferible mostrar menos indicadores bien sostenidos que muchos sin
linaje. Las preguntas que el lago aún no puede responder quedan declaradas como
pendientes con su motivo, en lugar de rellenarse con estimaciones no fundamentadas.

## Reflexión sobre seguridad

La principal superficie de riesgo no es técnica sino de **privacidad y
procedencia**: evitar exponer datos de personas y evitar filtrar secretos en el
repositorio. Por eso todo dato de personas se agrega por parròquia (nunca
individuos) y la clave de la `Compuerta_Acceso` opcional vive solo en el servidor
(`st.secrets` / variable de entorno), con `.streamlit/secrets.toml` excluido del
control de versiones: una clave versionada se considera, por diseño, una no
conformidad. En el acceso a fuentes externas se actúa de forma ética (User-Agent de
navegador real, pausas de cortesía y respeto de los límites de tasa), y ante
bloqueos anti-bot se documenta el hallazgo en lugar de forzar el acceso. Mantener
los datos crudos inmutables también protege la integridad de la fuente de verdad.
