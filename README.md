# Cerebro Andorra

Sistema de ingenieria de datos y analitica territorial del Principado de Andorra,
construido bajo una arquitectura lakehouse para la materia de Gestion y Gobernanza
de Datos. Reune, limpia y prepara indicadores clave (poblacion y sus desgloses,
vivienda, turismo, inversiones, indicadores sociales y macroeconomia) y los
presenta en una aplicacion web con el principio rector
**"0 cifras sin fuente, sin vigencia y sin fecha de prueba"**.

El proyecto se desarrollo en tres partes incrementales sobre el mismo lago de
datos y la misma app, sin romper lo anterior:

- **Parte 1 - Web (base):** pipeline minimo (poblacion por parroquia y precios de
  vivienda de Indomio) e app Streamlit con cuatro vistas (Panorama, Poblacion,
  Vivienda, Fuentes y Metodo).
- **Parte 2 - Visualizacion:** mapa coropletas por parroquia, vista de preguntas,
  dos fuentes oficiales mas (turismo e inversiones), identificadores de fuente
  estables (F01, F02...), diseno responsive, etiquetado PROXY visible, despliegue
  publico y este README con bitacoras.
- **Parte 3 - Enriquecimiento:** desgloses de poblacion (edad, sexo, nacionalidad,
  lugar de nacimiento), reclasificacion de dos crudos mal etiquetados, economia
  real del Banco Mundial, fix del mapa (Plan A con GeoJSON real) y reorientacion
  de la vista de preguntas a tono de usuario final ("Andorra en preguntas").

## Integrantes del grupo

- Daniel Zapata
- Samuel Herrera
- Tomas Londono

Los nombres tambien se muestran de forma visible en la barra lateral de la app
(`app/streamlit_app.py`, variable `_EQUIPO`).

## Enlace al repositorio

> Reemplazar el marcador por la URL real del repositorio una vez publicado.

- Repositorio: [URL del repositorio]

## Enlace al despliegue publico

> Reemplazar el marcador por la URL publica real una vez publicada la app en
> Streamlit Community Cloud.

- Despliegue publico (Streamlit Community Cloud): [URL de Streamlit Community Cloud]

El despliegue usa unicamente servicios y llaves gratuitos, sin tarjeta de credito
y sin servicios de pago. El punto de entrada es `app/streamlit_app.py` y las
dependencias estan fijadas en `requirements.txt`.

## Como ejecutar el proyecto

Desde la raiz del repositorio:

```powershell
# 1. Instalar dependencias (una vez)
pip install -r requirements.txt

# 2. Ejecutar el pipeline de procesamiento (desde scripts/)
cd scripts
python ejecuta_pipeline.py
cd ..

# 3. Levantar la app
streamlit run app/streamlit_app.py
```

Extractores de red (opcionales, fuera del pipeline, bajo demanda):

```powershell
# Economia real del Banco Mundial -> datos_crudos/worldbank_<codigo>.json
python scripts/descarga_worldbank.py

# GeoJSON de limites de parroquia -> datos_crudos/parroquias_andorra.geojson
python scripts/descarga_limites_parroquias.py
```

Tras descargar los crudos de red, vuelve a correr el pipeline para que
`economia_worldbank.csv` y el mapa tomen los datos reales.

## Estructura del repositorio

```
cerebro_andorra/
|- datos_crudos/          # Datos sin procesar (fuente de verdad inmutable)
|- datos_procesados/      # CSV limpios y gobernados generados por el pipeline
|- scripts/               # Pipeline de extraccion y procesamiento (Python)
|- app/                   # App Streamlit: streamlit_app.py + vistas/ + componentes
|- documentacion_bitacora/# Bitacora del proyecto: intentos, hallazgos y decisiones
|- contexto/              # Enunciados, diccionario de datos y material del taller
|- README.md
`- requirements.txt       # Dependencias fijadas con == (reproducible)
```

## Decision de que datos mostrar

El sistema integra fuentes al lago eligiendolas por responder a las preguntas de
la Entrega 1 (cuanta gente vive aqui, como se compone la poblacion, cuanto vale el
metro cuadrado, cuanto pesa el turismo, como se mueve la inversion inmobiliaria,
como evoluciona la economia) y por tener un linaje auditable. Cada dato se
clasifica segun la taxonomia de gobernanza: **OBSERVADO** (oficial / censo /
transaccion real), **ESTIMADO** (consenso del sector) o **PROXY** (dato de mercado
dinamico de la web, que representa oferta y no transaccion real).

| Fuente | Dominio | Linaje | Por que se muestra |
|--------|---------|--------|--------------------|
| Poblacion por parroquia (Departament d'Estadistica, `estadistica_id798`) | Poblacion | OBSERVADO | Cifra base del territorio; alimenta el mapa y la vista de poblacion. |
| Desgloses de poblacion (edad, sexo, nacionalidad, lugar de nacimiento) | Poblacion | OBSERVADO | Composicion demografica por parroquia; piramide, nacionalidad y origen. |
| Precios de vivienda (scraping de Indomio) | Mercado inmobiliario | **PROXY** | Granularidad de precios por zona; siempre como precio de oferta, no transaccion. |
| Presupuesto de turismo (`estadistica_681`, Andorra Turisme SAU) | Turismo | OBSERVADO | Mide el peso del turismo (gasto de funcionamiento y total del presupuesto). |
| Inversiones inmobiliarias (`estadistica_2729`) | Economia / inmobiliario | OBSERVADO | Serie oficial del numero de inversiones por ano. |
| Umbrales de pobreza (reclasificado de `oficial_820`) | Social | OBSERVADO | El crudo "transacciones" contenia en realidad umbrales de pobreza e ingresos. |
| Tasa de fecundidad (reclasificado de `oficial_810`) | Demografia | OBSERVADO | El crudo "indicadores economicos" contenia en realidad la tasa de fecundidad. |
| Economia (Banco Mundial, World Bank Open Data API v2) | Macroeconomia | OBSERVADO | PIB, PIB per capita y poblacion total a escala pais, con licencia clara. |

Criterio de seleccion: se priorizan fuentes **oficiales (OBSERVADO)** y se admite
una fuente **PROXY** (Indomio) unicamente para ganar granularidad de precios por
zona, dejando su naturaleza de oferta siempre explicita. Las cifras que no pueden
sostenerse con fuente, vigencia y fecha de prueba no se muestran.

## Evaluacion de si los datos se pueden usar

Se reviso la procedencia y condiciones de uso de cada fuente antes de integrarla:

- **Departament d'Estadistica d'Andorra (`sig.govern.ad`)** - datos publicos
  oficiales (poblacion y desgloses, turismo, inversiones, indicadores sociales).
  Se usan como OBSERVADO citando fuente, vigencia y fecha de prueba de cada cifra.
  El texto literal de la licencia de cada dataset se registra en el diccionario de
  datos (Excel en `contexto/`).
- **Banco Mundial (World Bank Open Data, API v2)** - indicadores macroeconomicos de
  Andorra con licencia clara **CC BY 4.0** (atribucion) y sin autenticacion. Se
  integra como OBSERVADO citando al Banco Mundial.
- **OpenStreetMap via Overpass / Nominatim (limites de parroquia, GeoJSON)** -
  publicado bajo **ODbL (Open Database License)**, que permite uso y
  redistribucion con **atribucion** y misma licencia para las bases derivadas. El
  mapa atribuye a OpenStreetMap. La descarga se hace de forma etica.
- **Indomio (scraping web)** - se trata como **PROXY**: precios de **oferta**
  publicados en anuncios, no transacciones cerradas. No se publican anuncios
  individuales ni datos de personas; solo agregados por zona como senal de mercado,
  etiquetados como PROXY/oferta de forma visible.

Conclusion: las fuentes son utilizables para el fin del proyecto siempre que se
respete la atribucion (OSM/ODbL, World Bank CC BY 4.0), se cite la fuente oficial
(Estadistica) y se mantenga el etiquetado PROXY de Indomio. Las condiciones
literales por fuente quedan en el diccionario de datos.

## Como se protegieron los datos

- **Agregacion por zona, nunca individuos:** todo dato relativo a personas se
  presenta agregado por parroquia o zona. No se exponen registros ni atributos
  individuales identificables.
- **Principio "0 cifras sin fuente, vigencia ni fecha de prueba":** cada cifra de
  la app lleva su metadato (fuente, vigencia y fecha de prueba) y su etiqueta de
  linaje (OBSERVADO / ESTIMADO / PROXY). Las cifras que no cumplen se omiten y se
  registra el motivo en la bitacora.
- **Sin PII en el repositorio:** no se versiona ningun dato de personas
  identificables ni credenciales. Los precios de Indomio se usan como agregados de
  oferta, no como anuncios individuales.
- **Compuerta de acceso opcional y secreta:** si se activa la compuerta, la clave
  se compara contra un valor almacenado en el servidor mediante `st.secrets` o
  variable de entorno. La clave **nunca** se escribe en un archivo versionado:
  `.streamlit/secrets.toml` queda fuera del repositorio (`.gitignore`). Una clave
  versionada se considera, por diseno, una no conformidad.
- **Crudos inmutables:** el pipeline nunca escribe en `datos_crudos/`; solo lee de
  ahi y escribe en `datos_procesados/`, preservando la fuente de verdad. Solo los
  extractores de red escriben en `datos_crudos/`, y unicamente creando archivos
  nuevos.

## Compuerta de acceso (opcional)

La compuerta de acceso es **opcional** y esta **desactivada por defecto**. Si no se
configura ninguna clave, la app arranca con normalidad y no pide nada. Solo cuando
existe una clave configurada en el servidor, la app pide esa clave antes de mostrar
el contenido.

Puntos clave de gobernanza:

- La clave se compara **siempre en el servidor**, nunca en el cliente, con una
  comparacion de tiempo constante (`hmac.compare_digest`).
- La clave se lee de `st.secrets` o, como alternativa en local, de la variable de
  entorno `CLAVE_ACCESO`. No se guarda la clave introducida por el usuario.
- La clave **nunca** se versiona. `.streamlit/secrets.toml` esta en `.gitignore`.

### Como activarla

**En local** - crea `.streamlit/secrets.toml` (ignorado por git) con un valor
propio:

```toml
# .streamlit/secrets.toml  (NO versionar: esta en .gitignore)
CLAVE_ACCESO = "CAMBIA_ESTA_CLAVE"
```

O con una variable de entorno (PowerShell):

```powershell
$env:CLAVE_ACCESO = "CAMBIA_ESTA_CLAVE"
streamlit run app/streamlit_app.py
```

**En Streamlit Community Cloud** - configura el secreto desde la UI (Settings ->
Secrets), nunca en un archivo del repositorio.

## Despliegue en Streamlit Community Cloud

El despliegue publico se hace en **Streamlit Community Cloud**, que es **gratuito y
no requiere tarjeta de credito**. Pasos:

1. **Repositorio en GitHub.** Sube el proyecto. Asegurate de que `.gitignore`
   excluye `.streamlit/secrets.toml` para no filtrar la clave.
2. **Archivo de entrada.** El punto de entrada es `app/streamlit_app.py` (campo
   *Main file path*).
3. **Dependencias.** Streamlit Cloud instala automaticamente las de
   `requirements.txt` (todas con version exacta `==`, sin rangos abiertos).
4. **Crear la app.** En <https://share.streamlit.io> -> *New app* -> selecciona
   repositorio, rama y escribe `app/streamlit_app.py` como *Main file path* ->
   *Deploy*.
5. **Secrets (solo si activas la compuerta).** En *Settings* -> *Secrets*, anade la
   clave en TOML (nunca en el repositorio).
6. **Verificar.** Abre la URL publica y comprueba que la pantalla inicial carga y
   que los nombres del grupo son visibles en la barra lateral. Copia esa URL al
   apartado *Enlace al despliegue publico* de este README.

## Herramientas de visualizacion seleccionadas

**Streamlit + Plotly Express.**

- **Streamlit** como framework de la aplicacion web: construye las vistas
  (Panorama, Poblacion, Vivienda, Fuentes, Mapa, Preguntas y Economia) con el
  patron "cifra + metadato + linaje" de forma directa (`st.metric`, `st.caption`,
  `st.expander`/`st.popover` para el detalle de gobernanza a un clic) y se despliega
  gratis en Streamlit Community Cloud. Es responsive en movil con
  `use_container_width=True`.
- **Plotly Express / Graph Objects** para el mapa de coropletas por parroquia (estilo
  `open-street-map` **sin token**), la piramide de poblacion, las composiciones por
  nacionalidad y origen, y las series de economia.

La justificacion completa frente a las alternativas probadas esta en la bitacora de
herramientas (`documentacion_bitacora/`).

## Hallazgos por parte

Resumen honesto de lo aprendido en cada parte. El detalle vive en
`documentacion_bitacora/`.

### Parte 1 - Web (base del lago)

- Se construyo un pipeline minimo que lee solo crudos verificados y escribe en
  `datos_procesados/`, sin tocar `datos_crudos/`. La normalizacion ancho->largo de
  la poblacion (7 parroquias x 6 anos = 42 registros, excluyendo la fila "TOTAL")
  se convirtio en el patron canonico reutilizado despues por todos los dominios.
- Los precios de Indomio llegan con el valor y la variacion interanual pegados en
  una misma celda (`7,115(+14.8%)`); hubo que separarlos y limpiar la coma de
  miles. Se etiquetan como PROXY desde el origen.
- Se eligio **pandas** frente a DuckDB para el tramo de procesamiento: con decenas
  de filas la gestion de memoria columnar de DuckDB no aporta ventaja y pandas
  integra de forma nativa con Streamlit.

### Parte 2 - Visualizacion

- **El GeoJSON heredado no servia para el mapa:** `edificios_andorra.geojson`
  contiene edificios individuales de OSM, no limites administrativos de parroquia.
  Se documento el hallazgo y se penso un extractor dedicado del GeoJSON de limites,
  con un Plan B por centroides mientras tanto.
- Se integraron **turismo** e **inversiones** como tercera y cuarta fuentes
  OBSERVADO, llevando el inventario a cuatro fuentes con **ID estable** (F01..F09)
  que no cambia entre ejecuciones.
- Se eligio **Streamlit** frente a Dash para las vistas: menos codigo repetitivo
  para el patron "cifra + metadato + linaje" y despliegue gratuito mas directo.
- Se reafirmo el etiquetado **PROXY** visible para Indomio y el diseno responsive
  en movil.

### Parte 3 - Enriquecimiento

- **Desgloses de poblacion con orden variable:** los cinco crudos de desglose vienen
  en formato ancho, pero el orden de los segmentos del patron
  `CATEGORIA. PARROQUIA. SUBCATEGORIA` cambia entre archivos (la nacionalidad
  invierte el orden a categoria->parroquia). Se resolvio con un parser configurable
  por dimension en vez de un patron rigido. Resultado: 5.964 registros gobernados
  en una tabla larga unica.
- **Dos crudos mal etiquetados por su nombre:** `oficial_820_transacciones_...`
  contenia en realidad umbrales de pobreza e ingresos, y
  `oficial_810_indicadores_economicos` contenia la tasa de fecundidad. Se
  reclasificaron por su contenido real (reconocidos por el texto de `Descripcio`,
  no por el `Codi`, que empieza por cero y algunos lectores truncan) y se convirtio
  la coma decimal catalana a punto.
- **El HTTP 406 del mapa era culpa nuestra, no un bloqueo:** la peticion a Overpass
  hacia `GET` sin cabecera `Accept`. El fix fue `POST` con `Accept: application/json`
  y `Content-Type: application/x-www-form-urlencoded`, mas una cadena de hasta 3
  mirrors. En la ejecucion real los mirrors de Overpass dieron 406/timeout, pero el
  **fallback Nominatim** devolvio los poligonos reales de las 7 parroquias (ODbL),
  activando el Plan A (coropletas) del mapa.
- **Economia real del Banco Mundial:** el extractor etico (`descarga_worldbank.py`)
  trajo PIB, PIB per capita y poblacion total (HTTP 200, licencia CC BY 4.0). El
  indice de precios (IPC) viene todo nulo para Andorra en la API, asi que se omite
  sin inventar cifras (30 registros reales de 3 indicadores).
- La vista de preguntas se reorientó a tono de usuario final ("Andorra en
  preguntas"); las preguntas sin fuente abierta y de licencia clara (transacciones
  y seguridad por parroquia) quedan declaradas como pendientes con su motivo.

## Bitacora de IA

Se uso asistencia de IA de forma acotada y verificando siempre contra los datos y
los requisitos. Resumen honesto:

- **Aciertos:** acelerar el andamiaje de los procesadores nuevos reutilizando el
  patron ancho->largo existente; redactar y organizar documentacion en espanol de
  forma consistente; proponer comparaciones estructuradas de herramientas sobre los
  mismos datos.
- **Errores / limites detectados:** la IA asumio al principio que
  `edificios_andorra.geojson` servia para el coropletas por parroquia; la inspeccion
  directa mostro que solo contiene edificios. Tambien hubo que ajustar a mano la
  normalizacion de la coma decimal y los rangos de validacion para que coincidieran
  con el dato real.
- **Criterio de uso:** la IA no decide la gobernanza ni inventa cifras; toda cifra
  proviene de `datos_procesados/` y se verifica con su fuente, vigencia y fecha de
  prueba.

## Reflexion sobre datos

Trabajar con fuentes oficiales de un pais pequeno como Andorra mostro lo valioso de
separar con rigor lo **observado** de lo que es solo **proxy**. La tentacion de
presentar los precios de oferta de Indomio como "el precio real" habria sido un
error de gobernanza; etiquetarlos siempre como PROXY mantiene honesta la lectura. El
principio "0 cifras sin fuente, sin vigencia y sin fecha de prueba" obligo a
renunciar a cifras atractivas pero no trazables, y eso mejoro la calidad del
conjunto: es preferible mostrar menos indicadores bien sostenidos que muchos sin
linaje. Reclasificar dos crudos por su contenido real (y no por su nombre de
archivo) tambien recordo que el nombre de un dataset no es el dato: hay que mirar
dentro. Las preguntas que el lago aun no puede responder quedan declaradas como
pendientes con su motivo, en lugar de rellenarse con estimaciones no fundamentadas.

## Reflexion sobre seguridad

La principal superficie de riesgo no es tecnica sino de **privacidad y
procedencia**: evitar exponer datos de personas y evitar filtrar secretos en el
repositorio. Por eso todo dato de personas se agrega por parroquia (nunca
individuos) y la clave de la compuerta de acceso opcional vive solo en el servidor
(`st.secrets` / variable de entorno), con `.streamlit/secrets.toml` excluido del
control de versiones: una clave versionada se considera, por diseno, una no
conformidad. En el acceso a fuentes externas se actua de forma etica (User-Agent de
navegador real, pausas de cortesia y respeto de los limites de tasa: >= 12 s en
World Bank y Overpass, >= 1 s/peticion en Nominatim), y ante bloqueos anti-bot se
documenta el hallazgo en lugar de forzar el acceso. Mantener los datos crudos
inmutables tambien protege la integridad de la fuente de verdad.
