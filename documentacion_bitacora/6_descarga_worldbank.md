# Bitácora 6 — Descarga ética de economía: World Bank Open Data (OBSERVADO)

**Fecha de prueba:** 2026-10-26
**Tramo evaluado:** Fuentes / Extracción ética (Fuente_Oficial_Nueva que alimenta el Dominio_Economia_Empleo de la `Vista_Economia`)
**Script:** `scripts/descarga_worldbank.py` (extractor de red, fuera del pipeline)
**Procesador asociado:** `scripts/procesa_economia.py` → `datos_procesados/economia_worldbank.csv`
**Requisitos relacionados:** 4.1–4.4 (Peticion_Etica con `User-Agent`, pausa de cortesía y manejo de 200/429/406), 4.7 (entrada de bitácora con descarga ética, linaje OBSERVADO y licencia), 4.8 (reintentos acotados y no guardar parciales)

## Objetivo

Documentar la incorporación de la primera **Fuente_Oficial_Nueva** del dominio de economía: los indicadores macroeconómicos de Andorra publicados por el **Banco Mundial** a través de su API abierta *World Bank Open Data (API v2)*. Esta entrada deja constancia de la estrategia de descarga ética, la licencia de la fuente, el linaje asignado y el manejo explícito de códigos de estado, coherente con el principio rector del proyecto: **"0 cifras sin fuente, sin vigencia y sin fecha de prueba"**.

## Por qué World Bank y no otra fuente

Durante el diseño se compararon tres candidatas para el Dominio_Economia_Empleo (ver `design.md`, comparativa de herramientas):

| Opción | A favor | En contra | Decisión |
| --- | --- | --- | --- |
| **World Bank Open Data API** | Verificada para Andorra (`AD`); JSON estable; licencia CC BY 4.0 clara; sin autenticación | Datos a nivel país, no por parròquia | **Elegida** |
| Portal `sig.govern.ad` (scraping) | Granularidad local | Sin API abierta clara; riesgo anti-bot; licencia difusa | Descartada en la Parte 3 (se intentó, se documenta) |
| Eurostat | Series largas | Cobertura de Andorra muy parcial | Descartada |

Se elige World Bank por tener una API REST abierta, estable, verificada para Andorra y con **licencia identificable de forma clara** (requisito indispensable para integrar una Fuente_Oficial_Nueva, Req 4). La limitación de granularidad (país, no parròquia) se asume de forma explícita: los indicadores se presentan a escala Andorra.

## Fuente, endpoint y licencia

- **Fuente a citar:** *Banco Mundial (World Bank Open Data, API v2)*.
- **Endpoint REST JSON** (verificado para el país `AD`):

  ```
  https://api.worldbank.org/v2/country/AD/indicator/<CODIGO>?format=json&date=2015:2024
  ```

- **Forma de la respuesta:** una lista JSON de dos elementos. El primero es metadata de paginación; el **segundo** es el array de observaciones, cada una con `date` (año, texto) y `value` (número o `null`). El procesador `procesa_economia.py` toma el segundo elemento y **omite** las observaciones con `value = null` (no se inventan cifras).
- **Licencia:** **CC BY 4.0** (atribución). Se registra de forma literal en el `Inventario_Fuentes` (columna `licencia`) y en el `Diccionario_Datos` (Req 4.7, 8.4).
- **Linaje:** **OBSERVADO** (organismo internacional oficial).
- **Acceso:** sin autenticación.

## Indicadores integrados

Todos reales para Andorra, verificados durante el diseño:

| Código WB | Indicador | Unidad |
| --- | --- | --- |
| `NY.GDP.MKTP.CD` | PIB (US$ corrientes) | US$ |
| `FP.CPI.TOTL.ZG` | Inflación, IPC | % anual |
| `NY.GDP.PCAP.CD` | PIB per cápita | US$ |
| `SP.POP.TOTL` | Población total (control cruzado) | personas |

Verificación puntual: `NY.GDP.MKTP.CD` devuelve 2015–2024 con valores reales (2024 ≈ 4.044 mil millones US$).

## Convenciones de acceso ético aplicadas

El extractor sigue las convenciones de acceso a fuentes externas del proyecto (Req 4.1–4.4):

- **`User-Agent` de navegador real:** cada petición envía un header `User-Agent` (cadena tipo Chrome sobre Windows) para identificarnos y evitar bloqueos anti-bot (403/406).
- **Pausa de cortesía de 12 s:** antes de cada indicador se aplica `time.sleep(PAUSA_CORTESIA_S)` con `PAUSA_CORTESIA_S = 12`. Doce segundos garantizan no superar el límite de ~5 peticiones/minuto declarado por la fuente oficial.
- **Timeout explícito:** cada petición usa `TIMEOUT_HTTP_S = 30` segundos para no quedar colgada.
- **Mensajes en español:** todo el registro por consola va en español, coherente con el resto del proyecto.

## Manejo explícito de códigos de estado

El extractor maneja de forma explícita el resultado de cada petición y lo registra por consola (Req 4.1–4.4, 4.8):

- **200 (éxito):** valida que la respuesta sea JSON legible, crea el directorio de salida de forma idempotente (`os.makedirs(..., exist_ok=True)`) y guarda el JSON crudo por indicador en `datos_crudos/worldbank_<codigo>.json`. Devuelve `True`.
- **429 (límite de peticiones):** reintenta hasta `MAX_REINTENTOS_429 = 3` veces, respetando el `Retry-After` de la respuesta si viene o esperando al menos ~60 s entre reintentos. No se guarda ningún archivo parcial si no se alcanza un 200.
- **406 u otro código / error de red:** se registra la causa (código HTTP o excepción de `requests`), se documenta el hallazgo en esta bitácora y **no** se guarda nada.

Ante un bloqueo persistente, el hallazgo se documenta aquí en lugar de forzar el acceso, y la `Vista_Economia` muestra la ausencia de la fuente económica sin inventar cifras (Req 5.3).

## Idempotencia y crudos intactos

- **No re-descarga:** `ya_descargado(codigo)` comprueba si `worldbank_<codigo>.json` ya existe en disco. Si existe, no se vuelve a descargar (idempotencia y cortesía con la fuente).
- **Nunca toca otros crudos:** este extractor solo **crea** archivos nuevos `worldbank_<codigo>.json` en `datos_crudos/`. No modifica, sobrescribe ni elimina ninguno de los crudos existentes (fuente de verdad inmutable).
- **Fuera del pipeline:** la descarga **no** forma parte de `ejecuta_pipeline.py` (principio P6 del diseño); se ejecuta aparte y bajo demanda, para no acoplar la generación del lago a una llamada de red. El procesador `procesa_economia.py` sí está en el pipeline y tolera la ausencia de los JSON escribiendo una tabla vacía con solo cabecera.

## Cómo ejecutarlo

Desde la carpeta `scripts/` (coherente con la convención de rutas relativas del proyecto):

```powershell
python scripts/descarga_worldbank.py
```

## Conclusión

La economía de Andorra se integra desde el **Banco Mundial (World Bank Open Data, API v2)** con licencia clara **CC BY 4.0** y linaje **OBSERVADO**. La descarga es ética (header `User-Agent` de navegador real, pausa de cortesía de 12 s entre indicadores, timeout de 30 s, manejo explícito de 200/429/406), idempotente (no re-descarga si el JSON ya existe) y sin tocar los demás crudos. Ante bloqueos se documenta el hallazgo en lugar de forzar el acceso y la `Vista_Economia` degrada mostrando la ausencia. Queda registrado aquí para trazabilidad de la estrategia de extracción exigida por el proyecto (Req 4.7).
