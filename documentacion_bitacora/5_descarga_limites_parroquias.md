# Bitácora 5 — Descarga ética del GeoJSON de límites de parròquia

**Fecha de prueba:** 2026-09-27
**Tramo evaluado:** Fuentes / Extracción ética (descarga del GeoJSON de límites administrativos que alimenta la `Vista_Mapa`)
**Script:** `scripts/descarga_limites_parroquias.py`
**Requisitos relacionados:** 1.1 (coropletas por parròquia a partir de los límites administrativos), 11.5 (acceso ético con `User-Agent` de navegador real y respeto del límite de tasa), 11.7 (pausa de cortesía y manejo de bloqueos sin forzar el acceso)

## Objetivo

Documentar cómo se obtiene el insumo geoespacial que falta para el mapa: un GeoJSON con los **límites de las 7 parròquies** de Andorra. El proyecto prioriza extractores web **éticos** ante la falta de APIs abiertas, así que esta entrada registra la estrategia de descarga, las convenciones de cortesía aplicadas y el Plan B ante bloqueos.

## Hallazgo que motiva esta descarga

Al preparar la `Vista_Mapa` se inspeccionó el GeoJSON heredado `datos_crudos/edificios_andorra.geojson` y se confirmó que es un `FeatureCollection` de **edificios individuales** de OpenStreetMap (polígonos con `building`, `name`, `name:ca`). **No contiene límites administrativos de parròquia**: no hay campo de parròquia, ni `admin_level`, ni `boundary`.

Consecuencia: ese archivo **no sirve** para un coropletas por parròquia (se necesita un polígono por cada una de las 7 parròquies, no edificios). Por eso se incorpora un archivo nuevo, `datos_crudos/parroquias_andorra.geojson`, descargado de forma ética por el extractor documentado aquí. El `edificios_andorra.geojson` permanece intacto en el inventario como `candidato` (capa de detalle urbano para una futura iteración).

## Fuente y consulta

- **Fuente:** API de Overpass de OpenStreetMap (`https://overpass-api.de/api/interpreter`). Licencia **ODbL** con atribución.
- **Consulta (Overpass QL):** selecciona el área de Andorra por su código ISO (`ISO3166-1 = "AD"`, `admin_level=2`) y, dentro de ella, las relaciones administrativas de parròquia (`boundary=administrative`, `admin_level=7`). Son los **7 límites**: Canillo, Encamp, Ordino, La Massana, Andorra la Vella, Sant Julià de Lòria y Escaldes-Engordany. Se pide la salida con geometrías (`out geom;`) para consumirla directamente como coropletas.

## Convenciones de acceso ético aplicadas

El extractor sigue las convenciones de acceso a fuentes externas del proyecto:

- **`User-Agent` de navegador real (Req 11.5):** cada petición envía un header `User-Agent` de navegador (cadena tipo Chrome sobre Windows) para identificarnos ante el servidor y evitar bloqueos anti-bot (403/406).
- **Pausa de cortesía de 12 s (Req 11.5, 11.7):** antes de la petición se aplica `time.sleep(PAUSA_CORTESIA_S)` con `PAUSA_CORTESIA_S = 12`. Doce segundos garantizan no superar el límite de ~5 peticiones/minuto declarado por la fuente oficial.
- **Timeout explícito:** la petición HTTP usa un `timeout` de 120 s para no quedar colgada indefinidamente.
- **Mensajes en español:** todo el registro por consola va en español, coherente con el resto del proyecto.

## Manejo explícito de códigos de estado

El extractor maneja de forma explícita el resultado de la petición y lo registra por consola:

- **200 (éxito):** valida que la respuesta sea JSON legible, crea el directorio de salida de forma idempotente (`os.makedirs(..., exist_ok=True)`) y escribe `datos_crudos/parroquias_andorra.geojson`. Devuelve `True`. Si el código es 200 pero el contenido **no** es JSON válido, se trata como fallo: se documenta el hallazgo y se devuelve `False`.
- **429 (límite de peticiones):** no se fuerza el acceso. Se documenta el hallazgo en esta bitácora y se devuelve `False` para activar el Plan B.
- **Cualquier otro código / error de red:** se registra la causa (código HTTP o excepción de `requests`), se documenta el hallazgo y se devuelve `False`.

Ante un 429 o un bloqueo, la función `_documenta_bloqueo_bitacora` **añade** (modo `append`) una entrada fechada al final de este mismo archivo con la fuente, el resultado y la decisión de no forzar el acceso. Las entradas automáticas de hallazgo quedan debajo de esta sección.

## Idempotencia y crudos intactos

- **No re-descarga:** `ya_descargado(ruta)` comprueba si `parroquias_andorra.geojson` ya existe en disco. Si existe, `main()` informa y termina sin descargar (idempotencia y cortesía con la fuente).
- **Nunca toca otros crudos:** este es el **único** script del proyecto que escribe en `datos_crudos/`, y sólo para **crear** este archivo nuevo. No modifica, sobrescribe ni elimina ninguno de los crudos existentes (que son la fuente de verdad inmutable).
- **Fuera del pipeline:** la descarga **no** forma parte de `ejecuta_pipeline.py`; se ejecuta aparte y bajo demanda, para no acoplar la generación del lago a una llamada de red.

## Plan B (cuando `descarga` devuelve `False`)

Si no se consigue el GeoJSON de límites (bloqueo 429, error de red o contenido no válido), `main()` devuelve un código `!= 0` y la `Vista_Mapa` activa su **Plan B**: una representación por **puntos/centroides** de las 7 parròquies con `st.map` (un marcador por parròquia según el indicador seleccionado), sin dependencias adicionales. En ese caso cada parròquia conserva su **cifra gobernada** (valor + metadato + linaje) y queda constancia aquí de que el coropletas quedó pendiente. Cuando el GeoJSON ya existe (nuevo o previo), `main()` devuelve `0` y el mapa usa el coropletas con Plotly Express (ver bitácora 4).

## Cómo ejecutarlo

Desde la carpeta `scripts/` (coherente con la convención de rutas relativas del proyecto):

```powershell
python scripts/descarga_limites_parroquias.py
```

## Actualización (Parte 3) — Fix del HTTP 406 y fallback Nominatim

**Fecha de prueba:** 2026-10-26
**Requisitos relacionados:** 6.1 (Peticion_Etica con cabecera `Accept` correcta y timeout de 30 s), 6.2 (reintentos ≤ 3 ante 429), 6.3 (hasta 3 endpoints mirror y fallback alternativo con licencia clara), 6.4 (validación estricta de 7 polígonos), 8.8 (crudos intactos)

### Hallazgo: el 406 venía de una petición mal formada, no de un bloqueo

El intento original fallaba de forma reproducible con **HTTP 406 (No Aceptable)**. Al diagnosticarlo (ver el hallazgo automático del 2026-10-26 más abajo) se descartó que fuese un bloqueo anti-bot: la causa real era que la petición hacía un `GET` **sin cabecera `Accept`**, y Overpass rechaza la negociación de contenido cuando no se declara el formato de respuesta aceptado. El 406 era, por tanto, un problema nuestro de formato de la Peticion_Etica, no de la fuente.

### Fix aplicado a la petición de Overpass

La función `descarga_overpass(url)` se corrigió así (diseño H3):

- **`POST` en lugar de `GET`**, enviando la consulta Overpass QL en el cuerpo (`data=consulta`).
- **Cabecera `Accept: application/json`** para declarar el formato aceptado (esto es lo que elimina el 406).
- **Cabecera `Content-Type: application/x-www-form-urlencoded`** acorde al cuerpo enviado.
- Se conserva el **`User-Agent` de navegador real**, el **timeout de 30 s** (`TIMEOUT_HTTP_S`) y el manejo explícito de 200 / 429 (reintento ≤ 3, respetando `Retry-After` o esperando ≥ 12 s) / 406 / otros, con registro del código HTTP por consola en español (Req 6.1, 6.2).

Además, la respuesta de Overpass con `out geom;` **no es un GeoJSON**: es el formato propio de Overpass (`elements` con `members` y su `geometry`). Se añadió `_overpass_a_featurecollection(...)` para convertir las relaciones administrativas a un `FeatureCollection` de polígonos antes de validarlas.

### Cadena de mirrors (hasta 3 endpoints)

`descarga(...)` prueba en orden hasta tres endpoints mirror de Overpass antes de rendirse (Req 6.3):

1. `https://overpass-api.de/api/interpreter`
2. `https://overpass.kumi.systems/api/interpreter`
3. `https://maps.mail.ru/osm/tools/overpass/api/interpreter`

El primero que devuelva las 7 parròquies con geometría válida se usa; si un endpoint responde 406/429/error, se pasa al siguiente y se registra el motivo.

### Fallback Nominatim (ODbL)

Si **ningún** endpoint de Overpass produce las 7 parròquies válidas, se recurre al **fallback de Nominatim** (OpenStreetMap), verificado durante el diseño (H2):

```
https://nominatim.openstreetmap.org/search?q=<PARRÒQUIA>,+Andorra&format=json&polygon_geojson=1&limit=1
```

- `construye_featurecollection_nominatim()` hace **una consulta por parròquia** (7 en total) para extraer el `geojson` de polígono (`Polygon`/`MultiPolygon`) de cada una.
- **Pausa de cortesía ≥ 1 s por petición** (`PAUSA_NOMINATIM_S = 1`): Nominatim exige respetar 1 petición/segundo, un ritmo distinto al de Overpass. Se envía igualmente el `User-Agent` de navegador real y el timeout de 30 s.
- **Licencia:** *Data © OpenStreetMap contributors, ODbL 1.0* (campo `licence` verificado en la respuesta). Licencia clara, coherente con el requisito de usar solo endpoints alternativos con licencia identificable (Req 6.3).
- Solo se construye el `FeatureCollection` si se obtienen **exactamente 7 polígonos no vacíos**; en caso contrario se devuelve `None` y no se guarda nada.

### Validación estricta y crudos intactos

`valida_7_parroquies(geojson)` exige un `FeatureCollection` con **exactamente 7 features**, cada una con geometría `Polygon`/`MultiPolygon` de coordenadas no vacías (Req 6.4). Solo si supera esta validación se escribe `datos_crudos/parroquias_andorra.geojson`. El extractor es idempotente (si el archivo ya existe y valida las 7 parròquies no re-descarga, Req 6.5) y es el único que crea este archivo nuevo, sin modificar ni eliminar ningún otro crudo (Req 8.8). Si tras agotar Overpass y Nominatim no se consiguen las 7 parròquies, se documenta en esta bitácora los endpoints probados y los códigos observados y **no** se guarda un GeoJSON inventado; la `Vista_Mapa` activa entonces su Plan B por centroides.

## Conclusión

La descarga del GeoJSON de límites de parròquia se realiza de forma ética (header `User-Agent` de navegador real, pausa de cortesía de 12 s en Overpass y ≥ 1 s en Nominatim, manejo explícito de 200/429/406/errores), idempotente (no re-descarga si ya existe y valida las 7 parròquies) y sin tocar los demás crudos. El **HTTP 406 quedó resuelto** corrigiendo la Peticion_Etica a `POST` con `Accept: application/json` y `Content-Type`, con hasta 3 mirrors de Overpass y un **fallback verificado a Nominatim (ODbL)** que devuelve los polígonos reales de las 7 parròquies. Ante bloqueos se documenta el hallazgo en lugar de forzar el acceso y la `Vista_Mapa` degrada al Plan B por centroides. Queda registrado aquí para trazabilidad de la estrategia de extracción exigida por el proyecto.

## Hallazgo de descarga (2026-10-26 21:01:24)

- Fuente: Overpass API (OpenStreetMap), límites de parròquia.
- Resultado: Error al descargar el GeoJSON (código HTTP 406).
- Decisión: no se fuerza el acceso; la Vista_Mapa usa el Plan B (representación por centroides).
