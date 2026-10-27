# **Datasets y fuentes de datos — Proyecto "Cerebro Andorra"** 

_Documento de referencia para el desarrollo de la web de análisis territorial de Andorra._ 

_Última actualización de la investigación: septiembre 2026._ 

## 0. Resumen rápido: ¿por dónde empezar? 

|**Priorid**<br>**ad**|**Fuente**|**Para qué**|**Acceso**|
|---|---|---|---|
|1|Departament d'Estadística|Población, vivienda, turismo, economía<br>(todo lo oficial)|Descarga CSV parametrizable|
|2|Indomio.es|Precio €/m² por barrio/zona|Scraping HTML (sin API)|
|3|OpenStreetMap / Overpass|Edificios, calles, POIs, geometría base|API REST gratuita|
|4|Cartografia.ad (IDE<br>Andorra)|Mapa base oficial, catastro, topografía|Visor + servicios OGC|
|5|FEDA|Energía (consumo/producción en vivo)|Web scraping (sin API pública)|
|6|aqicn.org|Calidad del aire|API REST real con token|



## 1. Precio de vivienda por barrio / zona (lo más específico que existe) 

Andorra no tiene "distritos" como Lima. Su división administrativa son 7 parròquies (parishes), y dentro de las parroquias grandes hay barrios/zonas informales que sí usan los portales inmobiliarios. Esta es la jerarquía real: 

_Andorra (país) → 7 Parròquies (= tus "zonas" grandes, como Miraflores) → Barrios/zonas dentro de cada parroquia (donde existen) → Poblacions/pueblos (unidad estadística oficial más pequeña)_ 

### 1.1 Indomio.es — la mejor fuente para esto (por barrio, con % de variación interanual) 

Portal inmobiliario que sí publica series por sub-zona. Estructura de URLs (útil para automatizar scraping): 

- Nivel país: https://www.indomio.es/en/mercado-inmobiliario/andorra/andorra-provincia/ 

- Nivel parroquia: https://www.indomio.es/en/mercado-inmobiliario/andorra/{parroquia}/ 

- Nivel barrio (solo existe para Andorra la Vella de momento): https://www.indomio.es/en/mercado-inmobiliario/andorra/andorra-la-vella/{barrio}/ 

Tabla de las 7 parroquias (agosto 2026, venta €/m²) 

|**Parroquia**|**Venta €/m²**|**Var. interanual**|**Alquiler €/m²/mes**|
|---|---|---|---|
|Escaldes-Engordany|8.369|+42,9%|25,91|
|Andorra la Vella|7.115|+14,8%|24,66|
|Ordino|6.443|+27,8%|21,89|
|La Massana|5.767|+13,4%|21,58|
|Canillo|5.860|+21,9%|23,17|
|Encamp|5.516|+16,7%|23,50|



|**Parroquia**|**Venta €/m²**|**Var. interanual**|**Alquiler €/m²/mes**|
|---|---|---|---|
|Sant Julià de Lòria|5.124|+21,3%|19,31|



**Fuente:** <u>https://www.indomio.es/en/mercado-inmobiliario/andorra/andorra-provincia/</u> 

Barrios dentro de Andorra la Vella (único caso con desagregación confirmada) 

|**Barrio**|**Venta €/m²**|**Var. interanual**|**Alquiler €/m²/mes**|
|---|---|---|---|
|Centro|7.407|+11,1%|24,87|
|Santa Coloma|5.608|+16,7%|20,01|
|La Margineda|4.268|+13,8%|12,53|



**Fuente:** <u>https://www.indomio.es/en/mercado-inmobiliario/andorra/andorra-la-vella/</u> 

#### Cómo usarlo 

- No tiene API oficial. Los datos están en HTML plano (nada de JS pesado para el número principal), así que se puede scrapear directo con requests + BeautifulSoup en Python. 

- Revisar periódicamente si otras parroquias grandes (Escaldes-Engordany, La Massana) desarrollan sub-zonas — hoy solo Andorra la Vella las tiene, pero el sitio se actualiza mensualmente. 

- Ellos no ofrecen descarga de series históricas completas gratis: automatiza la captura mes a mes y guarda tú mismo el histórico. 

**⚠️� Aviso legal:** es data de anuncios (oferta, no cierre de venta) — igual que tu tarjeta "PROXY" en el panel de Lima. Etiquétalo como estimado/oferta, no como transacción real. 

- 1.2 AGIA (Col·legi d'Agents i Gestors Immobiliaris d'Andorra) — dato oficial-sectorial 

- Informe semestral con precio medio €/m² por parroquia (no baja a barrio), pero es la fuente que citan los medios como la más fiable porque se basa en operaciones reales del colegio de agentes, no solo anuncios. 

- Buscar: "AGIA informe immobiliari" + semestre. No tiene portal de descarga masiva; se publica como nota de prensa/PDF. 

- Uso: cotejar/calibrar los números de Indomio (que son de oferta) contra estos (más cercanos a transacción real). 

### 1.3 Idealista / Fotocasa — precio por zona dentro de Andorra la Vella 

- Idealista permite filtrar por sub-zona al buscar pisos, ej. <u>https://www.idealista.com/en/venta-viviendas/andorra-la-vella/santa-coloma/, lo que permite calcular el €/m² medio</u> contando los anuncios activos. 

- Fotocasa tiene "índice de precio de vivienda" por ciudad: https://www.fotocasa.es/indice-precio-vivienda/andorra-la- <u>vella/todas-las-zonas — revisa si despliega sub-zonas al entrar (varía según el momento).</u> 

- Ninguno de los dos ofrece API pública gratuita — es scraping de listados (revisa sus términos de uso antes de automatizar a gran escala). 

### 1.4 RealAdvisor — por código postal 

- <u>https://realadvisor.es/es/precios-viviendas/44500-andorra — Andorra la Vella es el CP 44500 (usan CPs "prestados" de</u> España para geolocalizar). Da precio medio de piso y casa, con serie de 5 años. 

- Complementario, no baja a barrio, pero sirve para validar la cifra general de "ciudad". 

### 1.5 Departament d'Estadística — el dato oficial más granular disponible por Gobierno 

- No baja a barrio, pero sí tiene estadística de transacciones inmobiliarias e hipotecas por parroquia y trimestre — es tu dato "observado/oficial" para poner al lado del "estimado" de los portales, igual que el panel de Lima distingue OBSERVADO / ESTIMADO / PROXY. 

- URL banco de datos: https://sig.govern.ad/Sigdde.Public/Inici 

- Buscar temas: "Estadística de transaccions immobiliàries" y "Estadística hipotecària". 

#### Recomendación de diseño para tu panel 

- **OBSERVADO** : Estadística oficial (transacciones/hipotecas por parroquia) 

- **ESTIMADO** : AGIA (semestral, por parroquia) 

- **PROXY** : Indomio/Idealista/Fotocasa (mensual, con desagregación a barrio solo en Andorra la Vella) 

## 2. Estadística oficial general (población, economía, vivienda, turismo) 

**Fuente:** Departament d'Estadística d'Andorra 

Home: https://www.estadistica.ad/ 

Banco de datos navegable: https://sig.govern.ad/Sigdde.Public/Inici 

#### Cómo usarlo 

- No hay API REST documentada públicamente, pero el visor genera URLs de exportación CSV parametrizables por tema/subtema/fecha (patrón: exportar_banc_dades_csv.asp? formules=...&any1=...&any2=...&codi_divisio=...&codi_subtemes=...&codi_tema=...&lang=...). Se puede automatizar armando estas URLs para cada indicador que necesites. 

- Alternativa manual: navegar el banco de datos, elegir tema, exportar a CSV/XLS/XLSX directamente desde la interfaz. 

#### Temas relevantes que tiene 

- Población por parroquia y por "població" (pueblo/villa) — nivel más granular disponible 

- Movimiento turístico en frontera (diario: turistas vs excursionistas) 

- IGI (su IVA) trimestral 

- Transacciones inmobiliarias e hipotecas 

- IPC, salarios, mercado laboral 

- Consumo energético mensual (enlaza con FEDA) 

- Encuesta de Presupuestos Familiares (ingreso/gasto por hogar) 

**Publicación complementaria:** "Andorra in Figures" (Cambra de Comerç + Estadística + Actua) — PDF anual resumen. Buscar en https://www.ccis.ad/en/andorra-en-xifres/. 

## 3. Cartografía / catastro / mapa base (tu "Gemelo 3D") 

##### **IDE Andorra (Infraestructura de Dades Espacials)** 

- Presentación: https://www.cartografia.ad/ 

- Visor de mapas (OGC): https://www.ideandorra.ad/geoportal/ 

- Geoportal alternativo: https://test-cartografia.govern.ad/ 

#### Qué ofrece 

- Catálogo de metadatos (descubrir qué capas existen y cómo acceder) 

- Servicios web OGC: WMS/WFS/WMTS — se pueden consumir desde Leaflet/Mapbox/QGIS directamente sin descargar nada 

- Cartografía topográfica con vuelos fotogramétricos propios desde 1970 (histórico real, distintas épocas) 

- "Guia de carrers": visor de calles con Street View y 3D integrados 

**Sistema de coordenadas:** EPSG:27563 (oficial andorrano); también usan EPSG:4326 y EPSG:23031 para interoperar con España/Francia. Importante para no descuadrar capas al mezclar con OSM (que usa 4326/3857). 

**Cómo usarlo:** conectar el visor OGC como capa WMS en tu propio mapa (Mapbox GL / Leaflet / deck.gl), igual que "Terrain: Mapzen/AWS" que usas en Lima. Para descarga de vectores puntuales, usar el "web de descàrregues" que mencionan (histórico + actual). 

## 4. OpenStreetMap / Overpass — edificios, calles, POIs (gratis, sin depender del gobierno) 

Overpass API: https://overpass-api.de/api/interpreter 

Overpass Turbo (para probar queries visualmente): https://overpass-turbo.eu/ 

Ejemplo de query (todos los edificios de Andorra) 

[out:json][timeout:60]; area["name"="Andorra"]["admin_level"="2"]->.andorra; ( way["building"](area.andorra); relation["building"](area.andorra); ); out geom; 

#### Con Python 

import requests query = """ [out:json][timeout:60]; area["name"="Andorra"]["admin_level"="2"]->.andorra; ( way["building"](area.andorra); relation["building"](area.andorra); ); out geom; """ r = requests.get( "https://overpass-api.de/api/interpreter", params={"data": query} ) data = r.json() 

Nota: pocos edificios en Andorra tienen building:levels (altura) etiquetado — probablemente tengas que aproximar altura con otras capas o dejarlo como "sin dato" para muchos edificios. 

**Extractos ya recortados (más rápido que Overpass en vivo):** Geofabrik — 

<u>https://download.geofabrik.de/europe/andorra.html</u> (formatos .osm.pbf y shapefile, actualizado diario) 

Qué puedes sacar: edificios (polígonos), red viaria completa, comercios/hoteles/restaurantes con categoría, pistas de esquí y remontes, límites de las 7 parroquias como polígonos administrativos. 

## 5. Energía 

##### **FEDA (Forces Elèctriques d'Andorra)** 

- Home energía: https://www.feda.ad/energia-i-meteo 

- Consumo en vivo (día anterior): https://www.feda.ad/energia-i-meteo/energia 

Qué ofrece 

- Producción, importación y consumo de energía a nivel país 

- Mix energético (% renovable/eólico/nuclear importado) 

- Estación meteorológica propia con histórico desde 1934 

**Cómo usarlo:** no hay API pública documentada — es scraping de la página (los números de "consum d'ahir" se ven en HTML). Para series largas, cruzar con los informes mensuales que Estadística publica (demanda total en MWh y en TEP, desglosado por fuente: electricidad, gasoil, gasolina, butano/propano). 

## 6. Calidad del aire — la única con API REST de verdad y fácil 

**aqicn.org (World Air Quality Index) — espejo internacional de las 3-4 estaciones andorranas** 

- Red Andorra: https://aqicn.org/network/ad-aire/ 

- API oficial (gratis con token): https://aqicn.org/api/ → registrarse en https://aqicn.org/data-platform/token/ para obtener token 

- Endpoint ejemplo: https://api.waqi.info/feed/andorra/?token=TU_TOKEN 

**Fuente primaria (sin API, solo consulta web):** Departament de Medi Ambient — Xarxa de vigilància: 

<u>https://www.govern.ad/ca/tematiques/medi-ambient-i-sostenibilitat/atmosfera/qualitat-de-l-aire/xarxa-de-vigilancia</u> (1 estación fija en Escaldes-Engordany + 2 móviles) 

Alternativa: IQAir también cubre Andorra con API de pago/freemium — https://www.iqair.com/us/andorra 

## 7. Turismo 

|**Fuente**|**Qué tiene**|**Acceso**|
|---|---|---|
|Andorra Turisme<br>(visitandorra.com)|Info oficial, campañas, no tanto datos crudos|Web|
|Observatori del Comerç i<br>Turisme (Cambra de Comerç,<br>ccis.ad)|Encuestas a visitantes: gasto medio, motivo de<br>visita, procedencia, por temporada|PDF/infografías periódicas|
|Estadística oficial|Pernoctaciones por parroquia y tipo de<br>alojamiento; entrada diaria de vehículos/visitantes<br>en frontera|CSV vía banco de datos|
|Equivalente MINCETUR|No existe ministerio de turismo separado con<br>dataset propio — todo pasa por Andorra Turisme<br>+ Estadística|—|
|Links:https://visitandorra.com/en/<br>|·https://www.ccis.ad/<br>·https://www.estadistica.ad/||



## 8. Movilidad / tráfico 

**Mobilitat.ad (Departament de Mobilitat)** — https://www.mobilitat.ad/ 

- Mapa de tráfico en tiempo real (fluido/lento/denso/retenciones), cámaras, incidencias, mapa de intensidad media diaria de vehículos. 

- Sin API pública documentada — la app móvil consume un backend propio no abierto. Si necesitas el dato programático, tu mejor opción es AR+I (siguiente punto). 

**AR+I (Andorra Recerca + Innovació)** — https://www.ari.ad/ 

- Modelo nacional de movilidad, estudios de conteo de vehículos por punto (ej. "la Margineda sentit nord") comparando años (2021 vs 2024). Son informes técnicos descargables, no API, pero con series de datos citables y descargables como anexos. 

## 9. Gobierno local — los "Comuns" (equivalente a municipalidad distrital) 

Andorra no tiene alcaldía única; cada parroquia es un Comú independiente con su propia web (algunos publican presupuestos/urbanismo local, sin estandarizar): 

- Comú d'Andorra la Vella — comuandorra.ad 

- Comú d'Escaldes-Engordany — escaldes-engordany.ad 

- Comú de la Massana 

- Comú d'Ordino 

- Comú de Sant Julià de Lòria 

- Comú d'Encamp 

- Comú de Canillo 

Revisar cada uno individualmente si necesitas datos de urbanismo/licencias a nivel de parroquia — no hay agregador central. 

## 10. Demografía / indicadores internacionales (contexto y benchmark) 

|**Fuente**|**Uso**|
|---|---|
|UNECE Statistical Database<br>(w3.unece.org/CountriesInFigures)|Indicadores de género, empleo, comparables entre países|
|Wikipedia — "Demographics of Andorra" y<br>"List of cities and towns in Andorra"|Tablas resumen rápidas con fuente primaria enlazada (útil para poblar<br>rápido mientras conectas las fuentes oficiales)|



## 11. Medio ambiente y riesgos 

- Permafrost/sismicidad: proyectos de AR+I (ej. PERMAPYRENEES-2) — útil como capa de "riesgo natural", aunque es más informe académico que dataset descargable. 

- No se encontró estadística de criminalidad/seguridad pública en abierto (el Cos de Policia no publica desagregado). Si lo necesitas, probablemente requiera solicitud directa vía transparencia/acceso a información pública. 

## 12. Notas de implementación (recomendaciones directas) 

- Empieza por Indomio + Estadística oficial para la capa de vivienda — es tu dato más "vendible" visualmente y ya tienes granularidad de barrio en al menos una parroquia. 

- OSM/Overpass te da la geometría gratis para dibujar el mapa de edificios sin esperar al catastro oficial (que no es abierto). 

- Para todo lo que no tiene API (Estadística, FEDA, Mobilitat, Indomio), arma un pequeño scraper propio y guarda snapshots — así construyes tú mismo el histórico que ellos no exponen en descarga masiva. 

- Etiqueta siempre la fuente como en tu panel de Lima (OBSERVADO / ESTIMADO / PROXY) — es especialmente importante en Andorra porque el dato de vivienda por barrio viene de oferta (portales), no de transacción real. 

