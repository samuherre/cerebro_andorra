Replicar un sistema de información para una ciudad, y explorar herramientas en cada tramo
En grupos de tres o cuatro personas, repliquen para una ciudad que ustedes elijan el sistema de información del ejemplo de Lima, tramo por tramo. En cada tramo prueben por lo menos dos herramientas sobre los mismos datos antes de quedarse con una. Se entregan dos cosas: el sistema funcionando y la bitácora de exploración que justifica cada elección.

3 o 4
personas por grupo
1 ciudad
la eligen ustedes, una distinta por grupo
2 o más
herramientas probadas en cada tramo, sobre los mismos datos
0
cifras sin fuente, sin vigencia o sin fecha de prueba
Fuentes
lo que existe afuera
→
Catálogo
qué hay, qué sirve y por qué
→
Ingesta
scripts que bajan y limpian
→
Lago
el dato limpio, con su fuente
→
Verificación
si falla, no se publica
→
Vistas
lo que ve quien pregunta
En cada eslabón, por lo menos dos herramientas probadas antes de elegir una

Replicar no es copiar. Es reconstruir con las propias manos un sistema que ya funciona, para entender por qué está hecho así; la réplica da la línea de base, y explorar herramientas da el criterio. Quien solo conoce una herramienta no elige: usa la que tiene.

Por eso el taller empieza con el estado actual —qué es hoy un lago de datos, qué es gobernar datos, qué ideas técnicas están moviendo el oficio— y sigue con un laboratorio de ejercicios que se corren sin tarjeta de crédito. Todos los que dicen «corrido» se ejecutaron tal como están, con su salida real.

La ciudad la escogen ustedes. Lima no vale, porque es el ejemplo. Y conviene no casarse con la ciudad antes del rastreo: si casi nada de lo que buscan está abierto, eso es un hallazgo que merece contarse, y una buena razón para cambiar a tiempo.

Siguen en pie las cuatro decisiones —qué mostrar, si se puede usar, cómo protegerlo, con qué herramienta— y la IA entra en todo el recorrido, con su bitácora. Lo que cambia es el orden de las prioridades: primero replicar, después explorar, al final decidir.

Del almacén al lago, y del lago al lakehouse
Un almacén de datos guarda datos ya modelados para consultarlos con SQL; un lago de datos guarda archivos en su forma original, baratos y de cualquier tipo. Durante una década las organizaciones tuvieron los dos y copiaban datos de uno a otro. El lakehouse promete una sola copia, y la competencia de los últimos dos años no fue por el formato de los archivos sino por quién controla el catálogo.

Almacén	Lago	Lakehouse
Qué guarda	Datos estructurados, ya modelados	Archivos de cualquier tipo, crudos o casi	Archivos abiertos, casi siempre Parquet, con una capa de tabla encima
Esquema	Al escribir: nada entra sin forma	Al leer: cada consulta lo interpreta	Al escribir, con evolución controlada
Lo mejor	Consultas rápidas y gobernadas	Barato, flexible, sirve para IA y datos no estructurados	Una sola copia para tableros e IA, con transacciones y versiones
Cómo se echa a perder	Se vuelve caro y rígido: todo cambio pasa por un equipo	Se vuelve pantano: todo está guardado y nadie sabe qué es	Se vuelve dependencia del catálogo de un proveedor
Para explorar	
Snowflake
BigQuery
PostgreSQL
Apache Spark
DuckDB
Polars
Apache Iceberg
Delta Lake
Apache Hudi
DuckLake
Lo que cambió, con fecha
17 oct 2023
Delta Lake 3.0 trae UniForm: una tabla Delta también se puede leer como Iceberg.
Delta Lake
Apache Iceberg
3 jun 2024
Snowflake anuncia Polaris, un catálogo abierto para tablas Iceberg.
Apache Polaris
4 jun 2024
Databricks anuncia la compra de Tabular, la empresa de los creadores de Iceberg.
Databricks
12 jun 2024
Databricks libera Unity Catalog como código abierto y lo aloja en LF AI & Data.
Unity Catalog
3 dic 2024
AWS lanza S3 Tables: tablas Iceberg administradas dentro del almacenamiento de objetos.
AWS
27 may 2025
DuckDB Labs presenta DuckLake: el catálogo en una base de datos SQL y los datos en Parquet.
DuckLake
18 feb 2026
La junta de la Apache Software Foundation aprueba a Polaris como proyecto de nivel superior.
Apache Polaris
13 abr 2026
DuckLake llega a su versión estable, con compatibilidad hacia atrás garantizada.
DuckLake
25 abr 2026
MinIO archiva su edición comunitaria, que ya había perdido la consola de administración y los binarios: también el almacenamiento «gratis» cambia de reglas.
1 jun 2026
Se cierra la fusión de Fivetran y dbt Labs. dbt-core sigue con licencia Apache-2.0.
dbt
Airbyte / Fivetran
Tres lecturas de esa lista, para discutirlas antes de creerlas. La primera: los movimientos de los grandes apuntan a Iceberg como formato común, y los demás formatos se traducen a él. La segunda: la competencia se mudó al catálogo, que es donde se decide qué motor lee qué tabla y con qué permisos. La tercera: el lakehouse bajó de escala, y con DuckDB y DuckLake cabe en un portátil, sin nube.

Un vocabulario que conviene conocer: bronce, plata y oro, las capas que Databricks documenta como medallion architecture. En el Cerebro Lima existen sin ese nombre: lago/raw es bronce, lago/ es plata y las vistas son oro.

El lago de este taller es una carpeta de JSON y Parquet con DuckDB encima: un lakehouse de bolsillo. En el laboratorio lo convierten en DuckLake y en una tabla Iceberg local para ver versiones y viaje en el tiempo sin montar ningún servicio.

Gobernar datos es decidir quién decide, con qué reglas y cómo se comprueba
El DMBOK de DAMA International define el gobierno de datos como el ejercicio de autoridad y control —planificación, monitoreo y aplicación— sobre la gestión de los activos de datos. La distinción que ordena todo es entre gobierno y gestión: el gobierno decide quién responde y con qué reglas; la gestión ejecuta. En un grupo de cuatro personas eso cabe en una página, y aun así hay que escribirla.

Componente	La pregunta	En el Cerebro Lima	Lo mínimo en su sistema	Para explorar
Papeles	¿Quién responde por cada parte?	Un contrato de datos escrito	Los cuatro papeles de la ruta, con nombre en el README	—
Políticas y licencias	¿Qué se puede hacer con cada dato?	Estado y licencia en cada ficha del catálogo	El semáforo aplicado a cada fuente	
Data Contract CLI
Open Policy Agent
Metadatos y catálogo	¿Qué existe y qué significa?	149 fichas en catalogo/	Fichas con fecha de prueba y datos de personas	
Frictionless Framework
OpenMetadata
DataHub
Calidad	¿Se puede confiar?	352 comprobaciones antes de publicar	Comprobaciones que sepan fallar	
dbt
Great Expectations
Soda Core
Linaje	¿De dónde viene y qué afecta?	Fuente e identificador en cada cifra	Cada script dice qué lee y qué escribe	
Marquez
dlt
Privacidad y seguridad	¿A quién podría dañar?	Compuerta en el servidor y cero datos personales en el lago	Nivel de protección decidido y probado	
Presidio
OpenDP
Ciclo de vida	¿Cuándo se actualiza y cuándo se retira?	Fecha de prueba por tema	Actualización programada con verificación	
GitHub Actions
Marcos y normas, al día
DAMA-DMBOK
La guía de referencia de la gestión de datos. La edición vigente es la segunda revisada, de 2024, que no cambió áreas ni definiciones; la tercera está en preparación desde junio de 2025.
ISO/IEC 38505-1
Aplica el modelo de gobierno de TI de ISO/IEC 38500 al gobierno de datos. Su segunda edición es de agosto de 2026 y reemplaza a la de 2017.
ISO 8000
Serie internacional sobre calidad de datos; su parte 51, de 2023, trata el gobierno de datos.
ISO/IEC 42001
Sistema de gestión de inteligencia artificial, de diciembre de 2023: el lugar donde el gobierno de datos se encuentra con la IA dentro de una organización.
Unión Europea · datos
La Ley de Gobernanza de Datos aplica desde el 24 de septiembre de 2023 y la Ley de Datos desde el 12 de septiembre de 2025. Un «ómnibus de datos» propuesto en noviembre de 2025 fundiría la primera en la segunda; al 1 de agosto de 2026 no había acuerdo.
Unión Europea · IA
El artículo 10 de la Ley de IA exige gobierno de datos a los sistemas de alto riesgo. El Reglamento 2026/1744 aplazó esas obligaciones al 2 de diciembre de 2027 para los sistemas del anexo III y al 2 de agosto de 2028 para los productos del anexo I.
Colombia · datos personales
Ley 1581 de 2012 y Decreto 1377 de 2013. Deben inscribir sus bases en el Registro Nacional de Bases de Datos de la SIC las personas jurídicas de naturaleza pública y las sociedades y entidades sin ánimo de lucro con activos de más de 100.000 UVT (Decreto 090 de 2018).
Colombia · política de datos
CONPES 3920 de 2018, Política Nacional de Explotación de Datos; Plan Nacional de Infraestructura de Datos, adoptado por la Resolución 460 de 2022 de MinTIC; Modelo de Gobernanza de la Infraestructura de Datos, creado por el Decreto 1389 de 2022; CONPES 4144 de 2025, Política Nacional de Inteligencia Artificial.
Colombia · apertura y seguridad
Ley 1712 de 2014; la «Guía para el uso y aprovechamiento de datos abiertos en Colombia», de MinTIC; y el Modelo de Seguridad y Privacidad de la Información, actualizado por la Resolución 2277 de 2025 y alineado con ISO/IEC 27001:2022.
Fechas y números de norma verificados contra EUR-Lex, ISO, DAMA International, MinTIC, la SIC, el DNP y Función Pública el 14 de septiembre de 2026.

Hacia dónde va
Del comité al código. El data mesh propuso un gobierno «federado computacional»: reglas comunes que se aplican con programas y no con actas. Los contratos de datos y las políticas como código son esa idea puesta a trabajar.
El catálogo pasó de documentación a infraestructura. Decide qué motor lee qué tabla y con qué permisos, y por eso es donde hoy compiten los catálogos abiertos.
El gobierno de datos se volvió requisito de la IA. La Ley de IA europea le dedica un artículo, y la ISO/IEC 42001 lo lleva a sistema de gestión.
Gobernar también las herramientas. En 2026 Soda Core cambió a una licencia que no es de código abierto, la versión en la nube de Great Expectations dejó de estar disponible y la instalación por defecto de dbt pasó a traer licencia propietaria. Una política de datos que no mira de qué depende el sistema está incompleta.
Los papeles del grupo, con nombre de oficio
Curaduría hace de administración de datos —lo que en inglés se llama data steward—: responde por significado, calidad y licencia. Datos hace de custodia técnica. Seguridad cumple el papel de privacidad. Interfaz habla por quien consume. Si el README dice quién ocupa cada papel, el grupo ya tiene gobierno de datos escrito.


12 ideas técnicas que hoy mueven los sistemas de información, cada una con su trampa
No es una lista de modas. Cada idea trae por qué importa ahora, con un hecho fechado, dónde suele estar la trampa y a qué herramientas lleva; toquen una herramienta para ver su ficha y cómo probarla. Todas se pueden tocar sin tarjeta de crédito, y varias están en el laboratorio.

Formatos y catálogos abiertos
Por qué ahora
Polaris se graduó en la Apache Software Foundation en febrero de 2026 y Unity Catalog es abierto desde junio de 2024: la competencia por el lakehouse se mudó al catálogo.

La trampa
Un formato abierto no garantiza datos portables si los permisos y la historia viven en el catálogo de un proveedor.

Apache Iceberg
Apache Polaris
Unity Catalog
Delta Lake
El lakehouse de bolsillo
Por qué ahora
DuckLake llegó a su versión estable en abril de 2026: catálogo en SQL, datos en Parquet, instantáneas y viaje en el tiempo en un portátil.

La trampa
Un solo nodo tiene techo, y el archivo del catálogo sin copia de respaldo es un punto único de falla.

DuckDB
DuckLake
Polars
Ingesta declarativa
Por qué ahora
Bibliotecas como dlt infieren el esquema, lo versionan y registran cada carga: lo que antes era un script frágil queda con trazabilidad.

La trampa
Inferir el esquema también infiere los errores: un campo que llega vacío el primer día puede quedar con el tipo equivocado.

dlt
Airbyte / Fivetran
Transformación como código, en consolidación
Por qué ahora
Fivetran compró Tobiko Data, la creadora de SQLMesh, en septiembre de 2025, donó SQLMesh a la Linux Foundation en marzo de 2026 y cerró su fusión con dbt Labs en junio.

La trampa
Instalar «dbt» a secas trae hoy una distribución con licencia propietaria; lo abierto es dbt-core. Lean qué instalan.

dbt
SQLMesh
Orquestación por activos
Por qué ahora
Dagster modela los pipelines como activos de datos, y Apache Airflow 3 salió el 22 de abril de 2025.

La trampa
Orquestar un lago de cinco archivos es sobreingeniería: un flujo programado con verificación alcanza.

Dagster
Apache Airflow
GitHub Actions
Contratos de datos
Por qué ahora
El Open Data Contract Standard, del proyecto Bitol en LF AI & Data, ya tiene herramientas que prueban el contrato contra los datos reales.

La trampa
Un contrato que no corre como prueba es documentación, y la documentación envejece en silencio.

Data Contract CLI
Frictionless Framework
Calidad y observabilidad
Por qué ahora
La categoría se reordena: GX Cloud dejó de estar disponible en junio de 2026 y Soda Core cambió de licencia en enero.

La trampa
La herramienta que vigila la calidad también cambia de dueño y de reglas. Eso también va a la bitácora.

Great Expectations
Soda Core
dbt
Capa semántica abierta
Por qué ahora
dbt publicó MetricFlow con licencia Apache-2.0 en octubre de 2025, y la iniciativa Open Semantic Interchange entró a la incubadora de Apache en julio de 2026.

La trampa
Es un estándar en incubación con especificación en borrador: bueno para explorar, prematuro para depender de él.

Cube
dbt
Linaje abierto
Por qué ahora
OpenLineage es el estándar abierto para registrar de dónde viene cada dato, y los catálogos abiertos lo dibujan como grafo.

La trampa
Marquez, su implementación de referencia, no publica versión nueva desde octubre de 2024: la madurez de un proyecto se revisa antes de adoptarlo.

Marquez
OpenMetadata
DataHub
Geoespacial nativo de la nube
Por qué ahora
STAC es estándar comunitario del OGC desde 2025 y COG desde 2023, y Overture publica edificios y lugares de todo el planeta sin cuenta.

La trampa
GeoParquet todavía no es un estándar adoptado, y cada tema de Overture trae su propia licencia.

Overture Maps
PMTiles
tippecanoe
QGIS
kepler.gl
IA sobre los datos
Por qué ahora
Servidores MCP como el de MotherDuck conectan un asistente a un archivo DuckDB local, en solo lectura por defecto, y formatos como Lance juntan vectores y análisis en el mismo lago.

La trampa
Darle escritura a un agente sobre el lago, o creerle una cifra sin ver la consulta que la produjo.

MotherDuck MCP server
MCP (Model Context Protocol)
pgvector
Lance
Privacidad como técnica
Por qué ahora
Presidio está pasando de Microsoft a un proyecto comunitario independiente, y OpenDP enlaza un asistente web para explorar la privacidad diferencial sin programar.

La trampa
La instalación de ejemplo de Presidio usa un modelo en inglés: sobre textos en español puede dejar pasar datos personales.

Presidio
OpenDP
Cada hecho de estas tarjetas se comprobó contra el anuncio oficial, la documentación del proyecto o la fundación que lo aloja, el 14 de septiembre de 2026. Los números de versión se dejaron afuera a propósito.

Lo que se replica: el Cerebro Lima
Un sistema de información sobre Lima Metropolitana con énfasis en el distrito de Miraflores. Es la referencia de la réplica: no hay que copiar su herramienta ni su tamaño, sino su anatomía y sus cuatro decisiones tomadas y escritas.

El sistema
cerebro-lima.vercel.app
Qué hace, en diez pantallas
cerebro-lima.vercel.app/presentacion
Los dos piden clave, y la clave la da el profesor en clase. Que el ejemplo esté protegido aunque casi todo lo que muestra venga de fuentes públicas también es parte del ejemplo.

13
secciones, del panorama a las fuentes
149
fuentes catalogadas en el rastreo
94
de ellas integradas al sistema
352
comprobaciones automáticas antes de publicar; ninguna falló el 2 de septiembre
Las trece secciones son Panorama, Gemelo 3D, Gente, Economía y vivienda, Turismo, Municipio, Seguridad, Territorio y cultura, Correlaciones, Atlas de los 43 distritos, Ambiente y satélite, Escucha social, y Fuentes y método. Fíjense en la última: el sistema dedica una sección entera a contar de dónde sale todo lo demás.

Por dentro, cada tramo de la ruta tiene su carpeta. Esta es la anatomía que se replica; en cada carpeta caben varias herramientas, y probarlas es el laboratorio:

cerebro-lima/
├── ingesta/        un script por tema que baja y limpia, sin llaves
├── catalogo/       cada fuente: entidad, url, vigencia, estado, licencia
├── lago/           el dato limpio; cada cifra con su fuente
│   └── raw/        los crudos: nunca llegan al repositorio
├── territorio/     límites en GeoJSON
├── verificacion/   verificar.py: con un solo fallo no se publica
├── api/            la compuerta: entrar, sesión y datos
└── web/            lo único público: la cáscara, sin datos
Lima usa Python con la biblioteca estándar para la ingesta, JSON en el lago, un script propio de verificación, HTML y JavaScript sin framework para las vistas, MapLibre GL para el mapa y funciones de Vercel para la compuerta. Esa es la réplica mínima; cada pieza tiene alternativas en el laboratorio.

El lago de Lima, por dentro
De 149 fuentes rastreadas, entraron 94
Toquen cada estado para ver casos reales del catálogo. Lo que no entró está tan documentado como lo que sí.

integrado · 94
candidato · 40
caído · 13
declarado · 1
excluido · 1
Integrado. Entró al sistema y alimenta alguna vista.

BCRP · mercado inmobiliario por distrito
Banco Central de Reserva del Perú · Libre con cita
API pública de series, sin llave: precio de venta del m² por distrito.
Hospedajes en OpenStreetMap (Overpass)
Colaboradores de OpenStreetMap · ODbL
Cobertura voluntaria: complementa el registro oficial, no lo sustituye.
Google News RSS · diez consultas sobre Miraflores
Google · Uso personal (términos del feed)
Alimenta la escucha. Los enlaces son redirecciones de Google que no se resuelven.
Fuente: lago/catalogo.json del Cerebro Lima, probado el 2 de septiembre de 2026. El mismo catálogo escribe la licencia de 34 maneras distintas y registra «MEF» y «Ministerio de Economía y Finanzas» como si fueran dos entidades. Normalicen esos dos campos con una lista cerrada desde la primera fuente: después cuesta el doble.

Una ruta de ida y vuelta: cada tramo deja algo hecho y tiene una puerta de salida
El orden importa porque cada tramo produce lo que el siguiente necesita. Pero no es una escalera: si la puerta de salida no abre, se vuelve atrás y la vuelta se anota. En cada tramo hay una réplica que hacer y herramientas que explorar.

La ruta del sistema
Toquen un tramo
Qué hacen, qué dejan hecho, cuándo pueden salir, cómo entra la IA y qué herramientas explorar. La flecha del final vuelve al principio: un sistema vivo se vuelve a rastrear.

Rastreo
→
Pregunta
→
Permiso
→
Contrato y lago
→
Verificación
→
Vistas
→
Protección
→
Entrega
↺
Qué hacen
Anotan una sospecha —para quién sería el sistema y qué preguntaría— y barren las familias de fuentes. Cada enlace lo abre alguien del grupo o lo baja un script.

Qué dejan
La carpeta catalogo/, con una ficha por fuente, incluidas las caídas y las descartadas.

Salen cuando
Cada ficha tiene fecha de prueba, estado y licencia; hay fuentes de por lo menos tres familias distintas, y pueden decir qué no existe para su ciudad.

La IA en este tramo
Ensanchar la búsqueda: equivalentes locales de cada familia, portales que no conocían, fuentes en otros idiomas. Lo que existe no lo decide la IA: lo decide el enlace.

Tecnologías y términos de este tramo
Datos abiertos
Principios FAIR
DCAT
API REST
SODA
CKAN
OGC API y WMTS
STAC
Overture Maps
robots.txt
GTFS
Herramientas para explorar en este tramo
DuckDB
Overture Maps
QGIS
Ir a «El rastreo» → Al laboratorio →

Las vueltas atrás más comunes
Una pregunta no tiene fuente que la responda: de la pregunta al rastreo.
El semáforo excluye la fuente que sostenía una pregunta: del permiso a la pregunta.
La verificación falla: de la verificación a la ingesta, nunca al verificador para aflojarlo.
Una vista necesita una cifra que no está en el lago: de las vistas al contrato.
La herramienta elegida no deja proteger lo que había que proteger: de las vistas al laboratorio, a probar otra.
El ataque consigue sacar algo: de la protección al permiso, porque quizá ese dato no debía publicarse.
Cuatro papeles, y nadie aprueba lo suyo
Curaduría
Fuentes, licencias y catálogo. Pasa cada fuente por el semáforo y responde por el rastreo. Revisa las vistas: que cada cifra llegue a su ficha.

Datos
Contrato, ingesta y verificación. Responde por que el lago se reconstruya igual. Revisa la curaduría: que lo integrado exista y diga lo que el catálogo dice.

Interfaz
Herramienta y vistas. Responde por que el sistema abra en un teléfono y se entienda. Revisa la verificación: que haya comprobaciones de lo que se muestra.

Seguridad
Protección, secretos y datos personales. Ataca el sistema antes que nadie. Revisa todo lo que se publica, incluido el repositorio.

En grupos de tres, un papel se comparte, pero Seguridad la asume siempre alguien que no construyó la compuerta: quien la hizo es quien menos ve sus huecos. La exploración de herramientas no es de un papel: cada papel explora las de su tramo y las anota en la misma bitácora.

Dos revisiones entre grupos
Auditoría de tres cifras
Otro grupo escoge tres cifras al azar del sistema y trata de llegar a la fuente original. Si no llega en un clic, o si la fuente no dice eso, se corrige y queda en la bitácora.

Ataque autorizado
Otro grupo intenta sacar los datos sin la clave, con la terminal y el navegador. Solo contra sistemas del curso y con el acuerdo del grupo atacado. Lo que consiga va a la bitácora de quien fue atacado, con lo que cambió después.

Replicar primero, explorar después
El centro del taller está aquí. Cada grupo replica la base —los mismos scripts del lago, contra su ciudad— y en cada tramo prueba por lo menos dos herramientas sobre los mismos datos antes de quedarse con una. Lo que se entrega no es solo el sistema: es la bitácora que explica por qué quedó cada herramienta y qué se perdió al descartar las otras.

Repliquen la base tal cual. Si algo no corre en su máquina, eso va a la bitácora antes que cualquier exploración.
Exploren con los mismos datos. Comparar dos herramientas sobre fuentes distintas no compara herramientas: compara fuentes.
Anoten con los mismos criterios para todas: qué pidió para empezar, licencia, dónde quedan los datos, si se rehace con un comando, qué resolvió y qué no.
Revisen el estado del proyecto antes de adoptarlo: la fecha de la última versión, si cambió de licencia, si el producto sigue existiendo. En 2026 varias herramientas de datos cambiaron de reglas.
Elijan y escríbanlo, incluido lo que perdieron. Una exploración fallida bien anotada vale tanto como una exitosa.
La mesa del laboratorio
Escojan un tramo y trabajen los ejercicios en orden: primero la réplica, después las exploraciones
«Corrido» quiere decir que se ejecutó tal como está el 14 de septiembre de 2026, con su salida real. «Guiado» trae el comando de la documentación oficial, sin salida verificada aquí.

Ingerir · 3
Guardar y consultar · 4
Probar y contratar · 5
Territorio · 3
Visualizar · 4
Gobernar · 3
IA sobre el lago · 2
réplica
La ingesta base, tal cual
corrido
El script de la lámina del lago, con su ciudad en CIUDAD. Es la línea de base contra la que se compara todo lo demás.

copiar
python3 ingesta/pull_escucha.py
Salida real
Medellín: 20 meses, último 2026-08 con 19552 vistas
Para la bitácora
¿Corrió sin instalar nada?
Si el artículo de su ciudad es una página de desambiguación, ¿qué hace el script?
explorar
La misma fuente con dlt
corrido
dlt carga la misma fuente en una base DuckDB, infiere el esquema y deja registrada cada carga en tablas propias.

dlt
DuckDB
copiar
# explorar/dlt_wikipedia.py      ·   pip install "dlt[duckdb]"
import dlt
from dlt.sources.helpers import requests

UA = {"User-Agent": "taller-sistemas-de-informacion/1.0 (curso universitario)"}

@dlt.resource(name="vistas_wikipedia", write_disposition="replace")
def vistas(articulo="Medellín"):
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
           f"es.wikipedia/all-access/user/{articulo}/monthly/20250101/20260831")
    respuesta = requests.get(url, headers=UA)
    respuesta.raise_for_status()
    yield respuesta.json()["items"]

pipeline = dlt.pipeline(pipeline_name="ciudad", destination="duckdb", dataset_name="escucha")
print(pipeline.run(vistas()))
Salida real, resumida
1 load package(s) were loaded to destination duckdb and into dataset escucha
tablas del esquema escucha:  _dlt_loads · _dlt_pipeline_state · _dlt_version · vistas_wikipedia
últimas filas:  2026080100 → 19552   ·   2026070100 → 15726   (cada una con su _dlt_load_id)
Para la bitácora
¿Qué tablas creó dlt además de la suya, y qué guarda _dlt_loads?
¿Qué pasa si lo corren dos veces con write_disposition="append" en lugar de "replace"?
¿Cuántas líneas escribieron y cuántas dependencias instalaron, frente al script base?
explorar
Consultar una API sin bajarla
corrido
DuckDB lee JSON directamente desde una URL. Aquí consulta el desempeño municipal del DNP en datos.gov.co y convierte el campo de texto a número en la misma consulta.

DuckDB
copiar
# explorar/duckdb_remoto.py      ·   pip install duckdb
import duckdb
from urllib.parse import quote

consulta = "$select=anio,dato&$where=" + quote("codigo_entidad='05001' AND indicador='MDM'") + "&$order=anio"
url = "https://www.datos.gov.co/resource/nkjx-rsq7.json?" + consulta
print(duckdb.sql(f"SELECT anio, CAST(dato AS DOUBLE) AS mdm FROM read_json_auto('{url}')"))
Salida real
anio   mdm
2016   80.7775
2017   71.5909
2018   80.58
2019   83.5959
2020   82.3163
Para la bitácora
¿Por qué hay que codificar las comillas de la consulta con quote()?
El campo dato llegó como texto: ¿dónde lo convirtieron y qué habría pasado si no?
La bitácora de exploración
Una fila por herramienta probada, con las mismas columnas para todas. Va dentro del README de la entrega.

copiar
## Bitácora de exploración
| Tramo | Herramienta | Qué pidió para empezar (cuenta, Docker, memoria, tarjeta) | Licencia (¿OSI? ¿cambió hace poco?) | Dónde quedan los datos | ¿Se rehace con un comando? | Estado del proyecto (última versión) | Qué resolvió de nuestra pregunta | Qué no pudo | ¿Quedó? ¿Por qué? |
|---|---|---|---|---|---|---|---|---|---|
| Lago | DuckDB |  |  |  |  |  |  |  |  |
| Lago | DuckLake |  |  |  |  |  |  |  |  |
Todo lo del laboratorio corre sin tarjeta de crédito. Algunas herramientas piden cuenta, Docker o bastante memoria, y eso también se anota. Si no pueden instalar algo en su equipo, la exploración vale igual si dejan escrito por qué no se pudo.

Antes de decidir qué mostrar, averigüen qué existe
El rastreo es la primera pieza del sistema, no un trámite previo: un catálogo de fuentes que registra lo que sirvió, lo que no y por qué. Empieza con una sospecha anotada —para quién sería y qué preguntaría— que el propio rastreo puede tumbar.

Dónde buscar	Lo que usó Lima	Por dónde empezar en Colombia
Estadística oficial	INEI: censo 2017 y proyecciones de población	DANE: censo, proyecciones y geoportal
Economía y precios	Banco Central de Reserva: API de series sin llave	Banco de la República y DANE
La plata pública	MEF: presupuesto y ejecución municipal, un archivo por año	TerriData del DNP, y SECOP para la contratación
Seguridad, salud y educación	MININTER, MINSA y MINEDU	Los conjuntos de cada sector en datos.gov.co
El portal de la ciudad	Municipalidad de Miraflores en la plataforma nacional de datos abiertos	Datos Abiertos Bogotá, GeoMedellín
Ambiente y riesgo	SENAMHI, IGP y ENFEN	IDEAM, Servicio Geológico Colombiano y, en el Valle de Aburrá, SIATA
Territorio	Límites distritales y OpenStreetMap	Marco Geoestadístico Nacional, OpenStreetMap y Overture Maps
Desde arriba	Sentinel-2 y NASA GIBS	Los mismos: cubren cualquier ciudad, sin llave
Lo que se dice	Wikipedia Pageviews, GDELT y Google News	Los mismos, cada uno con sus términos
Si su ciudad está en otro país, cada fila tiene su equivalente: el instituto de estadística, el banco central, el ministerio de hacienda, el portal de la alcaldía. Las dos últimas filas, y Overture Maps, sirven para cualquier ciudad del mundo.

Un título que coincide no es la cosa. Verifiquen que la fila es su ciudad y no un homónimo, y crucen por código territorial (DIVIPOLA en Colombia, UBIGEO en Perú), nunca por nombre. En Wikipedia en español, «Pasto» es una página de desambiguación que habla de hierba para el ganado; la capital de Nariño es «Pasto (Colombia)». Y buscando «Miraflores» en el portal nacional peruano, la mayoría de resultados eran de San Juan de Miraflores, otro distrito.
Probar es una fecha. Cada fuente lleva el día en que abrieron el enlace y respondió. MEData, el portal de datos abiertos de Medellín, no respondió en nuestras pruebas del 14 de septiembre de 2026: así se anota, y se vuelve a probar.
Lo que no sirvió también va al catálogo, con el error exacto: 403, el dominio no resuelve, se agotó el tiempo, pide sesión. Es la parte del rastreo que le ahorra días al que venga después.
Cobertura y resolución antes que volumen. ¿El dato es de la ciudad, del área metropolitana o del país? ¿Viene por barrio o en un solo total? Una encuesta sin representatividad por ciudad no dice nada de su ciudad, por grande que sea el archivo.
La IA propone, el enlace dispone. Úsenla para ensanchar la búsqueda, pero ninguna fuente entra al catálogo hasta que alguien del grupo la abre o un script la baja. La IA inventa portales, conjuntos de datos y rutas de API con la misma seguridad con que describe los reales.
Cada fuente del catálogo es una ficha. Esta es una real del catálogo de Lima, con sus campos principales, y es de las que no sirvieron:

copiar
{
  "id": "mef_consulta_amigable",
  "nombre": "MEF · Consulta Amigable (apps5.mineco.gob.pe)",
  "entidad": "MEF",
  "url": "https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx?y=2026&ap=ActProy",
  "estado": "caido",
  "licencia": "Datos abiertos del Estado peruano (uso libre con atribución)",
  "nota": "Bloqueada por Imperva (Error 16) desde fuera del Perú, tanto en curl como en navegador. Se usa el CSV equivalente del portal de datos abiertos del MEF."
}
A la ficha de ustedes súmenle dos campos que la de Lima no lleva por fuente: probado, con el día de la prueba, y personas, que dice si el conjunto trae datos de personas y cuáles. El primero les dice cuándo volver a mirar; el segundo decide casi todo lo que viene en la protección.

Un sistema responde las preguntas de alguien
Antes de la primera gráfica: ¿para quién es, y qué necesita saber para decidir algo? Lo que no responde una pregunta de ese alguien sobra, por bonito que sea.

Las seis preguntas con las que abre la presentación de Lima
¿Cuánta gente vive aquí?
¿Cuánto vale el m²?
¿Cómo se financia el municipio?
¿Qué pasa con la seguridad?
¿Cuánto pesa el turismo?
¿Qué hay en el suelo?
Son las que haría un decisor sobre Miraflores. Cada una se responde con una cifra viva del lago, con su vigencia y su fuente, y debajo van las cifras que la matizan. Ninguna se responde con un párrafo.

Para quién
Una alcaldía, un concejal, una vecina, un inversionista, una periodista. Escojan uno y escríbanlo en la portada: cambia qué se muestra primero, con qué palabras y con cuánto detalle.

A qué escala
Una cifra de ciudad esconde las diferencias de adentro. Lima trabaja en dos escalas: los 43 distritos, para comparar, y catorce zonas dentro de Miraflores, para ver dónde pasa lo que pasa.

Contra qué
Un número solo no dice si es mucho o poco. Comparen con ciudades parecidas, con la misma ciudad hace unos años o con el promedio del país, y digan cuál escogieron y por qué. Lima pone a Miraflores contra los otros 42 distritos.

Qué no
Lo que no tiene fuente, lo que no se puede usar y lo que expone a alguien se queda afuera. Y los huecos se dicen dentro del sistema: la presentación de Lima tiene una pantalla que se titula «Lo que el cerebro no sabe, lo dice».

La vigencia va pegada a la cifra, en la misma línea y no en una nota al pie. «99.337 habitantes» no dice lo mismo que «99.337 habitantes en el censo de 2017».
Una métrica se define una vez. Si dos vistas calculan «tasa» de dos maneras, el sistema se contradice solo. Escriban en un único lugar qué es cada métrica y de qué campos sale.
Una correlación describe una asociación, y nunca se publica como efecto. Así lo deja escrito el propio script que calcula las correlaciones del Cerebro Lima.
Las cifras de la prosa se calculan, no se escriben a mano. Un «tercero de Lima» tecleado envejece en silencio: no falla, no se ve mal, simplemente deja de ser cierto. En Lima había varios, y ahora salen del lago.
Un índice compuesto muestra sus pesos y deja moverlos. El atlas de Lima combina bienestar, servicios, mercado y turismo, seguridad, capacidad municipal y demografía, y quien lo mira puede cambiar cuánto pesa cada dimensión.

Que un dato esté en internet no quiere decir que se pueda usar
Son tres preguntas distintas que se suelen confundir: si la fuente deja reutilizar el dato, si el dato habla de personas y si se puede obtener sin saltarse nada. Una fuente puede pasar dos y no la tercera. Aquí también se decide el nivel de protección, que después condiciona la herramienta. Y la misma pregunta vale para las herramientas: también tienen licencia.

La licencia
CC0 y dominio público: sin condiciones. CC BY: con atribución. ODbL, la de OpenStreetMap: con atribución, y lo que se derive de la base se distribuye bajo la misma licencia. «Datos abiertos del Estado»: lean los términos del portal. Y los términos de servicio de una plataforma mandan aunque el botón de descarga funcione.

Las personas
En Colombia rigen la Ley 1581 de 2012, de protección de datos personales, y la Ley 1712 de 2014, de transparencia y acceso a la información pública; en Perú, la Ley 29733. Si su ciudad está en otro país, busquen la equivalente. Que cada registro sea público no autoriza a cruzarlos hasta señalar a alguien.

El acceso
Sin llave: se automatiza. Con llave gratuita: la llave vive en el servidor. En PDF: se transcribe y se marca como declarado. Bloqueado para scripts: no se esquiva. En Lima, ONPE y el JNE respondieron a los scripts con un cortafuegos, y la Consulta Amigable del MEF no abre desde fuera del Perú.

El semáforo de la fuente
Cinco preguntas antes de meter una fuente al sistema
Respóndanlas por cada fuente del catálogo. Salen el estado, el nivel de protección, lo que queda obligado y la ficha lista para copiar.

Casos de Lima
API del BCRP
Google News RSS
Padrón RUC de SUNAT
Aire del SENAMHI
Consulta Amigable
¿Quién lo publica?
Una entidad pública
Academia u ONG
Plataforma colaborativa (OSM, Wikipedia)
Empresa o plataforma privada
Un medio de comunicación
No se sabe
¿Qué licencia o términos declara?
Licencia abierta explícita
Solo pide citar
Uso personal o no comercial
Prohíbe reutilizar
No dice nada
¿Trae datos de personas?
No
Solo conteos por zona
Personas identificables
Texto libre sin revisar
¿Cómo se obtiene?
Descarga o API sin llave
API con llave gratuita
Solo en PDF o en la página
Bloquea scripts o pide sesión
¿Responde hoy?
Sí, y está al día
Sí, pero el dato es viejo
No responde
Estado
integrado
Protección
abierto
Entra al sistema, con las condiciones de abajo.

Atribución visible en la vista donde se usa el dato, no solo en una página de créditos.
En el catálogo: el día de la prueba, la licencia tal como la declara la fuente y la vista que alimenta.
copiar
{
  "id": "id_corto_sin_espacios",
  "nombre": "…",
  "entidad": "…",
  "url": "https://…",
  "cobertura": "…",
  "vigencia": "…",
  "probado": "2026-10-26",
  "estado": "integrado",
  "licencia": "abierta explícita (escriban cuál)",
  "personas": "no",
  "proteccion": "abierto",
  "uso": "…",
  "nota": "…"
}
Es el criterio de este taller para decidir rápido y dejar rastro, no una asesoría jurídica. Los casos de Lima cargan respuestas aproximadas a lo que registró su catálogo. Ante la duda sobre una licencia o sobre datos personales, gana la opción más prudente, y la duda se escribe en la nota.

Primero el contrato, después el lago, y una verificación que sepa fallar
Esta es la réplica mínima del lago de Lima. El contrato de datos es la promesa que el sistema le hace a quien pregunta: toda cifra llega con valor, unidad, vigencia y fuente. Se escribe antes del primer script, y los scripts se escriben contra él. Todo lo de esta lámina se corrió tal como está; las alternativas para cada pieza están en el laboratorio.

El contrato
Un archivo JSON por tema, siempre con la misma forma. Este es real, recortado: lo produjo el script de ingesta de más abajo.

copiar
{
 "tema": "escucha",
 "probado": "2026-09-14",
 "fuentes": [
  { "id": "wikimedia_pageviews", "nombre": "Wikimedia Pageviews API",
    "url": "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/…",
    "estado": "vivo", "licencia": "CC0" }
 ],
 "cifras": {
  "vistas_ultimo_mes": { "valor": 19552, "unidad": "vistas de personas",
                         "vigencia": "2026-08", "fuente": "wikimedia_pageviews" }
 },
 "series": {
  "vistas_mensuales": { "unidad": "vistas de personas", "fuente": "wikimedia_pageviews",
                        "puntos": [["2026-07", 15726], ["2026-08", 19552]] }
 }
}
Ninguna cifra sin fuente, URL y vigencia. Si se leyó de un PDF o de una nota de prensa, la fuente queda con estado declarado.
Las fechas de prueba van por día, nunca con hora y segundos: dicen cuándo se comprobó, no cuándo corrió el script.
Los crudos van a lago/raw, que está en .gitignore y nunca se despliega.
Los números se normalizan en el script: separadores de miles, coma decimal, moneda. Nunca se suma texto.
Las geometrías van en GeoJSON con coordenadas WGS84, simplificadas para que cada capa pese poco. Cuando una capa ya no cabe, es el momento de PMTiles o GeoParquet.
Un script de ingesta por fuente
Este baja cuánta gente busca la ciudad en Wikipedia y escribe el lago con la forma del contrato. Usa solo la biblioteca estándar de Python, no pide llave y sirve para cualquier ciudad con artículo en Wikipedia en español: cambien CIUDAD. Lo corrimos el 14 de septiembre de 2026 con Medellín: veinte meses, y 19.552 vistas en agosto de 2026.

copiar
#!/usr/bin/env python3
"""Ingesta · cuánta gente busca la ciudad en Wikipedia.
Baja las vistas mensuales del artículo y escribe lago/escucha.json con la forma del contrato.
Sin llaves: solo la biblioteca estándar de Python."""
import datetime, json, pathlib, urllib.parse, urllib.request

CIUDAD = "Medellín"                    # título del artículo en es.wikipedia
DESDE, HASTA = "20250101", "20260831"  # meses completos
UA = {"User-Agent": "taller-sistemas-de-informacion/1.0 (curso universitario)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


# Un título que coincide no es la cosa: se exige artículo y se usa el título canónico
t = urllib.parse.quote(CIUDAD.replace(" ", "_"))
resumen = get(f"https://es.wikipedia.org/api/rest_v1/page/summary/{t}")
assert resumen["type"] == "standard", f"«{CIUDAD}» no es un artículo sino {resumen['type']}"
canon = urllib.parse.quote(resumen["titles"]["canonical"])

url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
       f"es.wikipedia/all-access/user/{canon}/monthly/{DESDE}/{HASTA}")
puntos = [[i["timestamp"][:4] + "-" + i["timestamp"][4:6], i["views"]] for i in get(url)["items"]]
ultimo = puntos[-1]

lago = {
    "tema": "escucha",
    "probado": datetime.date.today().isoformat(),
    "fuentes": [{"id": "wikimedia_pageviews", "nombre": "Wikimedia Pageviews API", "url": url,
                 "estado": "vivo", "licencia": "CC0"}],
    "cifras": {"vistas_ultimo_mes": {"valor": ultimo[1], "unidad": "vistas de personas",
                                     "vigencia": ultimo[0], "fuente": "wikimedia_pageviews"}},
    "series": {"vistas_mensuales": {"unidad": "vistas de personas", "fuente": "wikimedia_pageviews",
                                    "puntos": puntos}},
}
pathlib.Path("lago").mkdir(exist_ok=True)
pathlib.Path("lago/escucha.json").write_text(json.dumps(lago, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{CIUDAD}: {len(puntos)} meses, último {ultimo[0]} con {ultimo[1]} vistas")
Para ciudades colombianas, la API SODA de datos.gov.co filtra en el servidor y devuelve solo lo que se pide. Esta consulta trae el puntaje de desempeño municipal de Medellín y, de paso, enseña tres cosas: el campo dato llega como texto y hay que convertirlo antes de hacer cuentas; el conjunto tiene licencia CC BY-SA 4.0, que obliga a compartir igual lo derivado, y sus cifras llegan solo hasta 2020.

copiar
curl -G "https://www.datos.gov.co/resource/nkjx-rsq7.json" \
  --data-urlencode "\$select=anio,dato" \
  --data-urlencode "\$where=codigo_entidad='05001' AND indicador='MDM'" \
  --data-urlencode "\$order=anio"

# [{"anio":"2016","dato":"80.7775"}, … ,{"anio":"2020","dato":"82.3163"}]
Una verificación que sepa fallar
El verificador recorre todo el lago y termina con error si algo no cumple el contrato o si aparece un correo o un celular en cualquier texto. La regla del celular puede dar falsos positivos con números largos que empiezan por 3: si salta, se mira el caso, no se borra la regla. Las comprobaciones de dominio —que la población caiga en un rango sensato, que los barrios sumen la ciudad— las escriben ustedes para su ciudad.

copiar
#!/usr/bin/env python3
"""Verificación antes de publicar: con un solo FAIL no se despliega."""
import glob, json, re, sys

fallos = 0
PII = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}|(?<!\d)3\d{9}(?!\d)")  # correos y celulares colombianos
CAMPOS_PERSONALES = re.compile(r"cedula|documento_identidad|telefono|celular|correo|email", re.I)


def check(nombre, ok, detalle=""):
    global fallos
    print(("PASS " if ok else "FAIL ") + nombre + ("" if ok else f"  <- {detalle}"))
    fallos += 0 if ok else 1


def recorre(x, clave=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from recorre(v, k)
    elif isinstance(x, list):
        for v in x:
            yield from recorre(v, clave)
    else:
        yield clave, x


for ruta in sorted(glob.glob("lago/*.json")):
    lago = json.load(open(ruta, encoding="utf-8"))
    fuentes = lago.get("fuentes", [])
    ids = {f.get("id") for f in fuentes}
    check(f"{ruta}: probado es un día", re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(lago.get("probado"))), lago.get("probado"))
    check(f"{ruta}: toda fuente con url y licencia", fuentes and all(f.get("url") and f.get("licencia") for f in fuentes))
    for clave, c in lago.get("cifras", {}).items():
        completa = c.get("valor") is not None and c.get("unidad") and c.get("vigencia") and c.get("fuente") in ids
        check(f"{ruta}: {clave} con valor, unidad, vigencia y fuente conocida", completa, c)
    pares = list(recorre(lago))
    sospechosos = sorted({k for k, _ in pares if CAMPOS_PERSONALES.search(k)})
    check(f"{ruta}: ningún campo con nombre de dato personal", not sospechosos, sospechosos)
    hallado = next((v for _, v in pares if isinstance(v, str) and PII.search(v)), None)
    check(f"{ruta}: ningún texto con correo o celular", hallado is None, hallado)

# Comprobaciones de dominio: escríbanlas para su ciudad
# pob = json.load(open("lago/demografia.json"))["cifras"]["poblacion"]["valor"]
# check("población en un rango sensato", 2_000_000 < pob < 3_500_000, pob)

print(f"\n{fallos} fallos")
sys.exit(1 if fallos else 0)
Esta es su salida real después de romper el lago a propósito, con una cifra sin fuente y una nota con un correo y un celular ficticios:

PASS lago/escucha.json: probado es un día
PASS lago/escucha.json: toda fuente con url y licencia
PASS lago/escucha.json: vistas_ultimo_mes con valor, unidad, vigencia y fuente conocida
FAIL lago/escucha.json: sin_fuente con valor, unidad, vigencia y fuente conocida  <- {'valor': 12, 'unidad': 'personas', 'vigencia': '2026'}
PASS lago/escucha.json: ningún campo con nombre de dato personal
FAIL lago/escucha.json: ningún texto con correo o celular  <- dudas: escribir a nombre@ejemplo.com o al 3000000000

2 fallos
La puerta de salida del tramo es borrar el lago y reconstruirlo. Si después git muestra cambios que nadie esperaba, la ingesta no es reproducible, y eso se arregla antes de construir una sola vista.

copiar
rm -rf lago
for s in ingesta/pull_*.py; do python3 "$s"; done
python3 verificacion/verificar.py
git diff --stat -- lago/

Elegir la herramienta es elegir dónde quedan los datos
Hay herramientas con código y sin código, y con casi todas se puede hacer un buen sistema. La pregunta que ordena la elección no es cuál se ve mejor: es dónde quedan los datos cuando publican, y si la puerta se puede cerrar de verdad. Por eso se elige después de explorar varias con la misma serie y de decidir el nivel de protección.

Herramienta	¿Código?	Dónde quedan los datos	¿Se puede cerrar de verdad?	Ojo
Código propio en Vercel
HTML y JavaScript, React o Next.js; MapLibre o Leaflet para el mapa
Sí	En su repositorio y en sus funciones	Sí, con una compuerta en el servidor, como Lima	El plan gratuito (Hobby) es solo para uso personal no comercial. Todo lo que quede en la carpeta pública se descarga.
Observable Framework
Generador de sitios estáticos de código abierto
Sí	Los cargadores de datos precalculan instantáneas al construir, y quedan dentro del sitio	No por sí mismo: depende de dónde lo alojen	La instantánea es un archivo más del sitio publicado. No publica versión nueva desde marzo de 2026.
Streamlit Community Cloud
Aplicaciones de datos en Python
Python	En el repositorio de GitHub y en la aplicación	Sí: «solo personas específicas», invitadas por correo	Desde un repositorio público, la aplicación es pública por defecto, y se permite una sola aplicación privada a la vez.
Data Studio
Informes de Google, antes llamados Looker Studio
No	En Google: Sheets, BigQuery o archivos subidos	Sí, compartiendo con cuentas de Google concretas	Con enlace público no se pide iniciar sesión, y las fuentes incrustadas quedan al alcance de quien tenga el enlace.
Power BI
Informes de Microsoft
No	En el servicio de Microsoft	Sí, con los permisos de la organización (inserción segura, SharePoint)	«Publicar en la web» deja el informe abierto a cualquiera, sin autenticación, incluidos datos del modelo que el informe no muestra. Y hasta eso pide licencia de Power BI.
Tableau Public
Visualizaciones en un perfil público
No	En el perfil público de Tableau	No	Los libros y los datos publicados no son privados: cualquiera puede descargarlos.
Datawrapper
Gráficos, mapas y tablas
No	En Datawrapper	Solo mientras no se publique	Publicar es compartir con el mundo. El enlace «Get the data», que deja bajar el CSV, se pone o se quita.
Flourish
Historias y gráficos animados
No	En Flourish	No, en el plan gratuito	En el plan gratuito lo publicado es público y lleva la atribución de Flourish.
kepler.gl
Exploración geoespacial en el navegador
No	Solo en el navegador de quien lo abre	No hace falta mientras no se exporte	Muy bueno para explorar y decidir qué mapa hacer. Lo que exporten para publicar ya no vive solo en su navegador.
Cada fila sale de la documentación de la herramienta, consultada el 14 de septiembre de 2026. Los planes gratuitos cambian: antes de decidir, vuelvan a leer la página de la que elijan.

Fichas en el catálogo, con cómo probarlas
Streamlit
Observable Framework
Data Studio
Power BI
Tableau Public
Datawrapper
Flourish
kepler.gl
MapLibre GL JS
Metabase
Apache Superset
Evidence
Lima usa HTML y JavaScript sin framework para las vistas, MapLibre GL para el mapa en 3D y funciones de Vercel para la compuerta. Es una respuesta, no la respuesta. También se puede combinar: explorar en kepler.gl, consultar el lago con DuckDB, publicar con código propio. Lo que no vale es no saber qué fila eligieron ni qué implica para lo que decidieron proteger.

La justificación va en el README, en tres líneas —qué necesitaban mostrar, qué tenían que proteger y por qué esta herramienta cumple con las dos cosas— y con la fila de la bitácora de exploración de cada herramienta descartada. Para ver más opciones está el stack del curso, que dice de cada herramienta lo que no resuelve; para elegir con qué IA construir cada parte, ¿Qué IA necesito?

Proteger es una decisión, y una clave escrita en el navegador no protege nada
El nivel se decidió con el semáforo; aquí se implementa y se ataca. Si todo es abierto y nada habla de personas, una clave sería teatro. Si algo sí lo necesita, la protección tiene que aguantar a alguien con una terminal.

Abierto
Todo se ve y todo se puede descargar. Es lo correcto cuando las fuentes son abiertas, las licencias lo permiten y ningún dato apunta a una persona. Lo único que se cuida son los secretos del código.

Abierto, solo agregados
Se publican los conteos y los indicadores. Los crudos se quedan en la máquina de quien los procesó y nunca llegan al repositorio ni al despliegue.

Detrás de una compuerta
La clave se compara en el servidor y los datos salen por una función que exige sesión. Es lo que hace Lima. En general sirve para licencias de uso restringido, para cifras que se malinterpretan fuera de contexto o para un trabajo que todavía no se quiere publicar.

No se publica
Hay datos que no deben salir de donde están, ni siquiera detrás de una clave. Decidirlo también es diseñar el sistema, y también se escribe.

La compuerta de mentira es la que se le ocurre a cualquiera, y a cualquier IA, en el primer intento: comparar la clave en el JavaScript y dejar los datos como un archivo más del sitio. En un sitio estático todo archivo de la carpeta pública se descarga sin clave, y la clave misma queda en el código fuente, a un «ver código» de distancia.

De mentira
copiar
// app.js — corre en el navegador. No protege nada.
const CLAVE = 'medellin2026';

boton.onclick = async () => {
  if (entrada.value !== CLAVE) return aviso('Clave incorrecta');
  const datos = await fetch('/datos/lago.json').then(r => r.json());
  pintar(datos);
};
copiar
# Nadie tiene que adivinar nada
curl https://su-sistema.vercel.app/datos/lago.json          # 200: el lago completo
curl -s https://su-sistema.vercel.app/app.js | grep CLAVE   # y la clave, de paso
De verdad
copiar
// api/entrar.js — la clave se compara en el servidor
const crypto = require('crypto');

module.exports = (req, res) => {
  if (!process.env.CLAVE || !process.env.SECRETO) return res.status(500).end();
  const intento = Buffer.from(String((req.body && req.body.clave) || ''));
  const clave = Buffer.from(process.env.CLAVE);
  if (intento.length !== clave.length || !crypto.timingSafeEqual(intento, clave)) {
    return res.status(401).json({ error: 'Clave incorrecta' });
  }
  const vence = String(Date.now() + 12 * 60 * 60 * 1000);   // doce horas
  const firma = crypto.createHmac('sha256', process.env.SECRETO).update(vence).digest('hex');
  res.setHeader('Set-Cookie', 'sesion=' + vence + '.' + firma +
    '; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=43200');
  res.status(200).json({ ok: true });
};
copiar
// api/datos.js — los datos solo salen con una sesión válida
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function sesionValida(req) {
  const m = /(?:^|;\s*)sesion=([^;]+)/.exec(req.headers.cookie || '');
  if (!m || !process.env.SECRETO) return false;
  const [vence, firma = ''] = m[1].split('.');
  const esperada = crypto.createHmac('sha256', process.env.SECRETO).update(vence).digest('hex');
  return firma.length === esperada.length &&
    crypto.timingSafeEqual(Buffer.from(firma), Buffer.from(esperada)) &&
    Number(vence) > Date.now();
}

module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store, private');
  if (!sesionValida(req)) return res.status(401).json({ error: 'Sesión requerida' });
  const f = String(req.query.f || '');
  if (!/^[a-z0-9_]+\.json$/.test(f)) return res.status(404).end();   // lista blanca
  const p = path.join(process.cwd(), 'lago', f);                       // fuera de la carpeta pública
  if (!fs.existsSync(p)) return res.status(404).end();
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.status(200).send(fs.readFileSync(p, 'utf8'));
};
copiar
// vercel.json — web/ es lo único público; lago/ solo viaja dentro de la función
{
  "outputDirectory": "web",
  "functions": { "api/datos.js": { "includeFiles": "lago/**" } }
}
CLAVE y SECRETO van en las variables de entorno del proyecto, nunca en el repositorio. Así funciona, con más cuidado, la compuerta de Lima:

La clave se compara en el servidor, en tiempo constante, contra una variable de entorno. El navegador nunca la ve.
La sesión es una cookie firmada con HMAC-SHA256, que vence a las doce horas y va marcada HttpOnly, Secure y SameSite=Lax: el JavaScript de la página no la puede leer.
Los datos viven fuera de la carpeta pública. Una función los entrega solo con sesión válida, y solo si el nombre del archivo pasa una lista blanca.
Los crudos no viajan. lago/raw está en .gitignore y en .vercelignore: no llega al repositorio ni al despliegue.
Frena los intentos: con doce claves fallidas desde la misma IP en diez minutos, responde 429. El código admite su propio límite, y vale la pena copiar también esa honestidad: «en serverless no es defensa fuerte, solo encarece».
Pide no ser indexado, con la cabecera X-Robots-Tag: noindex en todas sus respuestas.
La prueba no es que la interfaz pida clave: es que la terminal no consiga nada sin ella. Córranla contra Lima y después contra su propio sistema, antes del ataque del otro grupo. Y si exploraron una herramienta sin código, la prueba equivalente es abrir el enlace compartido en una ventana privada, sin sesión.

copiar
# Sin cookie, la cáscara abre y los datos no
curl -s -o /dev/null -w "%{http_code}\n" https://cerebro-lima.vercel.app/                              # 200
curl -s -o /dev/null -w "%{http_code}\n" "https://cerebro-lima.vercel.app/api/datos?f=catalogo.json"  # 401
curl -s -o /dev/null -w "%{http_code}\n" https://cerebro-lima.vercel.app/lago/catalogo.json            # 404

# Y en su repositorio: que ninguna clave haya pasado por el historial
git log -p | grep -n -i -E "clave|secret|password|api_key|token"
Queda un frente que no depende de la compuerta: los secretos en el repositorio. El archivo .env entra al .gitignore antes del primer commit. Si una clave alcanzó a llegar al historial, borrar el archivo no la saca de ahí: se cambia la clave.

La IA hace buena parte del trabajo, y ustedes responden por todo el resultado
Úsenla en cada tramo para convertir sus decisiones en trabajo hecho: buscar, programar, explorar herramientas nuevas, verificar, atacar, documentar. Lo que no se le delega es la estrategia —qué mostrar, qué proteger, a qué fuente y a qué herramienta creerle—. Eso lo firman ustedes.

Tramo	Qué le encargan	Qué comprueban ustedes
Rastreo	Ensanchar la búsqueda: candidatos por familia para su ciudad, con entidad, URL y qué cubre cada uno.	Abrir cada enlace. Lo que nadie abrió no está en el catálogo.
Ingesta	Un script por fuente que baje, limpie y escriba el JSON con la forma del contrato.	Correrlo ustedes y mirar unidades, separadores y códigos territoriales: un «1.234» con punto de miles se lee como uno coma dos, y nadie se entera.
Verificación	Comprobaciones de dominio y, sobre todo, los casos que deberían fallar.	Romper un dato a propósito y ver si la comprobación lo atrapa. Una verificación que nunca falla no está verificando.
Exploración	Una primera versión del mismo ejercicio en una herramienta que no conocen.	Leer la licencia y la fecha de la última versión antes de instalar: la IA no sabe lo que cambió este año.
Vistas	Maquetas, componentes, gráficos y el texto de las lecturas.	Que los números de la prosa salgan del lago y no estén tecleados.
Protección	Atacar su propio sistema: ¿cómo bajaría estos datos alguien sin la clave?	Correr los curl ustedes. La IA también escribe compuertas de mentira si no se le exige otra cosa.
Documentación	El README, el catálogo legible y las bitácoras en limpio.	Que no afirme de una fuente ni de una herramienta lo que su documentación no dice.
El Cerebro Lima se construyó con agentes de programación, Claude Code y Codex, trabajando sobre el mismo repositorio, y a partir del esqueleto de un sistema del mismo tipo hecho antes para Ñuñoa, en Santiago de Chile. La revisión de septiembre encontró lo que deja ese modo de trabajar cuando nadie mira:

Lo que encontró la revisión
Restos de Chile: fuentes con nombres chilenos dentro de la capa de edificios, etiquetas de Ñuñoa que pisaban las de Lima («≤ 500 m del Metro») y un formateador de UF, la unidad de fomento chilena, en una ciudad que cuenta en soles.
Una variable de exposición a tsunami valía cero en las catorce zonas, y aun así el sistema nombraba una «zona más expuesta».
La frase «Central y Maido alternan el n.º 1 desde 2023» era falsa: en 2024 el primer lugar fue para Disfrutar.
Cifras escritas a mano en la prosa, que hoy se calculan desde el lago.
Ninguno de esos errores rompía la página. Todos se veían bien. Por eso verificar no puede ser mirar la pantalla.

Bitácora de IA. Para cada decisión importante: con qué herramienta, qué le encargaron, qué entregó y qué le corrigieron. Si la columna de correcciones queda vacía, es que no revisaron.
La IA no sabe lo que cambió este año. Cuando les recomiende una herramienta, verifiquen licencia y última versión en la fuente: en 2026 varias cambiaron de reglas.
Nada de datos personales en una conversación con una IA. Si una fuente trae personas, se agrega en su máquina antes de pedir ayuda con ella.
Sin llaves pagas. La IA es para construir el sistema. Si además quieren IA dentro del sistema, la vía más honesta es que traduzca preguntas a consultas sobre el lago, muestre la consulta y lea en solo lectura; y que no dependa de una llave que caduque justo cuando alguien lo abra.
Cada herramienta para lo suyo. Buscar un documento, escribir un script y revisar una licencia son tareas distintas, y rara vez las hace bien la misma. Para elegir: ¿Qué IA necesito?

Seis reflexiones para no confundir el sistema con la ciudad
Un sistema de información no es neutral: decide qué cuenta, quién aparece y quién responde cuando algo sale mal. Estas reflexiones no tienen respuesta única, pero exigen una respuesta escrita. Cada grupo escoge por lo menos una y la responde en su README con evidencia de su propio sistema, no con opiniones generales.

Representación
El mapa no es el territorio
Borges imaginó, en «Del rigor en la ciencia», un imperio cuyos cartógrafos levantaron un mapa del tamaño del imperio, tan exacto como inútil, que las generaciones siguientes abandonaron a las inclemencias del sol y de los inviernos. La tentación de hoy es la contraria y más discreta: creer que un sistema con muchas capas ya es la ciudad. Todo sistema de información es una selección, y lo que no entró no desaparece de la calle; desaparece de la decisión. La pregunta de gobierno no es cuánto muestra el sistema, sino qué deja de ver quien lo usa.

La evidencia
El Cerebro Lima catalogó 149 fuentes y usó 94, y su presentación dedica una pantalla entera a «Lo que el cerebro no sabe, lo dice». Declarar el hueco es la forma de que el mapa no se haga pasar por el territorio.
Para responder con su sistema
¿Quién vive en su ciudad y no aparece en ninguna de sus fuentes?
¿Qué decisión podría tomarse mal con su sistema precisamente porque ese hueco no se ve?
Privacidad
Público no es inocuo
Un dato puede ser público y aun así dañar a alguien cuando se cruza con otro. Ningún campo, por separado, dice quién es una persona; juntos, con frecuencia lo dicen. La Ley 1581 de 2012 lo sabe desde su definición: es dato personal el que puede asociarse a personas «determinadas o determinables», y la palabra que pesa es la segunda. Quien publica un conjunto no responde solo por lo que muestra, sino por lo que permite deducir.

La evidencia
Latanya Sweeney estimó en 2000 que el 87 % de la población de Estados Unidos era probablemente única con tres datos: código postal de cinco dígitos, sexo y fecha de nacimiento. El mosaico, más abajo, hace la misma cuenta con una tabla inventada.
Para responder con su sistema
¿Qué columnas de su lago, cruzadas entre sí o con otra fuente pública, señalan a una persona?
¿Qué conteo mínimo por zona van a exigir antes de publicar, y por qué ese número?
Gobierno
Un dato sin dueño es un dato sin gobierno
Cuando todos responden por un dato, nadie responde. El gobierno de datos empieza por una pregunta incómoda y casi administrativa: si esta cifra está mal y alguien tomó una decisión con ella, ¿a quién le reclama? Una organización puede tener tecnología de punta y ninguna respuesta a esa pregunta. Un grupo de cuatro personas, en cambio, puede tenerla escrita en una línea del README.

La evidencia
El catálogo de Lima escribe la licencia de 34 maneras distintas y registra al MEF como dos entidades. No es un error de programación: es lo que le pasa a un campo que no tiene quién lo cuide.
Para responder con su sistema
¿Quién responde, con nombre, por cada tema de su lago?
Si alguien de afuera encuentra un error, ¿por dónde se lo hace saber, y quién decide corregirlo?
Ciclo de vida
Los datos también se mueren
Publicar un sistema es la parte fácil; sostenerlo es la difícil, y casi nunca tiene presupuesto. Los portales se caen, las series dejan de actualizarse y los enlaces siguen apuntando a dominios que ya no existen. Gestionar datos es, sobre todo, gestionar el tiempo: decidir cada cuánto se revisa algo, quién lo revisa y qué dice el sistema el día en que deja de estar al día.

La evidencia
El portal de datos abiertos de la Municipalidad de Miraflores ya no resuelve, aunque la plataforma nacional peruana todavía enlaza a él, y varios de sus conjuntos en esa plataforma traen series de 2018 a 2022 sin actualizar. MEData, el portal de Medellín, no respondió en nuestras pruebas del 14 de septiembre de 2026.
Para responder con su sistema
¿Quién va a mantener su sistema cuando termine el curso, o quién decide apagarlo?
¿Qué debería decir la portada el día en que la fecha de prueba más reciente tenga más de un año?
Calidad y método
¿Más datos, más certeza?
Hay una fe que conviene sospechar: la de que entre más datos, más certeza. Con muchas variables, las coincidencias aparecen solas. Dieciséis indicadores permiten ciento veinte comparaciones de a pares; si cada una se juzga con el umbral habitual del cinco por ciento, cabe esperar alrededor de seis correlaciones «significativas» por puro azar, aunque ninguna variable tenga que ver con otra. Un alud de correlaciones no ilumina la ciudad: la tapa.

La evidencia
El atlas de correlaciones del Cerebro Lima cruza 16 métricas de los 43 distritos en 120 pares, y su script deja escrita la regla: una correlación describe una asociación y nunca se publica como efecto causal.
Para responder con su sistema
¿Cuántas comparaciones hace su sistema sin decirlo, y cuáles podrían ser azar?
¿Qué hallazgo de su sistema defenderían aunque la correlación desapareciera con un año más de datos?
Dependencia
¿De quién es la infraestructura?
Elegir una herramienta es también elegir de quién se depende. En 2026 varias herramientas de datos cambiaron de reglas sin cambiar de nombre, y los sistemas que las usaban heredaron el cambio sin haberlo decidido. Para un sistema público la pregunta es política además de técnica: una ciudad que publica sus datos en un servicio que no controla ha delegado, sin decirlo, una parte de su gobierno.

La evidencia
Soda Core pasó en enero de 2026 a una licencia que no es de código abierto; GX Cloud dejó de estar disponible el 1 de junio; instalar «dbt» a secas trae hoy una distribución con licencia propietaria, y MinIO archivó su edición comunitaria en abril.
Para responder con su sistema
¿Qué pasa con su sistema si la herramienta que eligieron cambia de licencia el próximo año?
¿Qué parte de su sistema podrían mudar a otra herramienta sin reescribirla, y qué parte no?
El mosaico
Quiten el nombre y vean cuántas personas siguen siendo reconocibles
Una tabla de 60 personas inventadas de una misma comuna, sin nombres. Decidan qué atributos publicar y con cuánto detalle: cada punto es una persona, y su color dice cuántas comparten exactamente lo que se publicó sobre ella.

Lugar
Barrio
Solo la comuna
No se publica
Edad
Exacta
De a 5 años
De a 10 años
No se publica
Sexo
Se publica
No se publica
Sector de ocupación
Se publica
No se publica
Personas reconocibles
60 de 60
El grupo más pequeño
1 persona
Grupos distintos
60
sola en su grupo
con 1 a 3 personas más
con 4 o más
60 de 60 personas quedan solas en su combinación. Quien conozca a una de ellas, su edad, su barrio y a qué se dedica, la encuentra en la tabla y lee todo lo demás que se publicó sobre ella.

Datos inventados, generados en el navegador con una semilla fija: no corresponden a nadie. La cuenta es la del k-anonimato: cada combinación de atributos publicados forma un grupo, y un grupo de una sola persona es una persona identificable. El umbral de cinco que se usa aquí es un ejemplo, no una norma: cada grupo decide el suyo y lo declara.

Gestionar datos es ocuparse de que estén bien; gobernarlos es decidir quién responde por que lo estén. Las dos cosas se confunden porque muchas veces las hacen las mismas personas, y se separan en el peor momento: cuando una cifra equivocada ya tomó una decisión por alguien.

Seis reflexiones para dejar de pensar la seguridad como un candado
La seguridad de un sistema de información no se agrega al final, como una puerta: se decide desde el principio, como una forma de gobierno. Estas reflexiones parten del laboratorio y del propio sistema de cada grupo, y cada una trae su evidencia con la procedencia a un clic. También aquí la respuesta va escrita en el README.

Gobierno
La seguridad es una decisión de gobierno
Durante años los marcos de ciberseguridad hablaron de identificar, proteger, detectar, responder y recuperar, como si la seguridad fuera un oficio técnico que empieza cuando alguien ya decidió qué proteger. La versión 2.0 del marco del NIST agregó una función que antes no estaba: gobernar. No es un detalle de redacción. Quién decide qué se protege, con qué recursos y quién responde cuando falla es una pregunta anterior a cualquier cortafuegos, y en este taller se contesta con el semáforo, antes de escribir la compuerta.

La evidencia
El NIST publicó el 26 de febrero de 2024 un marco de seis funciones, con GOBERNAR; la versión anterior tenía cinco, y todas eran operativas.
Para responder con su sistema
¿Quién de su grupo decidió el nivel de protección, y dónde quedó escrito por qué?
¿Qué dato de su sistema protegerían aunque ninguna ley los obligara?
Cadena de suministro
Explorar es ampliar la superficie de ataque
Un laboratorio que invita a probar herramientas invita también a instalar código ajeno, y cada paquete instalado es un tercero con permiso para correr en la máquina de quien lo instala. No se trata de dejar de explorar, sino de explorar como se entra a una casa ajena: en un entorno aislado, leyendo qué se trae y sin credenciales a la mano. Gestionar dependencias es gestionar confianza.

La evidencia
En el último informe de Verizon, el 48 % de las brechas tuvo participación de terceros. En Colombia, más de 50 entidades se vieron afectadas en 2023 por el ataque a un solo proveedor de nube. Y la puerta trasera de XZ Utils la insertó alguien que se había ganado durante años la confianza del proyecto. La cadena del laboratorio, más abajo, muestra cuántos terceros trae cada herramienta.
Para responder con su sistema
¿Cuántos paquetes instalaron para su sistema, y cuántos de ellos sabrían nombrar?
¿Qué harían mañana si uno de esos paquetes resultara comprometido?
Apariencia
Parecer protegido no es estar protegido
Hay medidas que protegen y medidas que tranquilizan, y se parecen demasiado. Una clave comparada en el JavaScript, un candado dibujado en la interfaz o una política que nadie ha probado producen la misma sensación que una compuerta real, y ninguna resiste a alguien con una terminal. La trampa, en el fondo, no es técnica: la apariencia de seguridad cambia la pregunta de si estamos protegidos por la de si lo parecemos.

La evidencia
El principio de acceso y circulación restringida de la Ley 1581 dice que los datos personales, salvo la información pública, no pueden estar disponibles en internet «salvo que el acceso sea técnicamente controlable». Técnicamente controlable no es una ventana que pide clave: es lo que pasa las pruebas de terminal de la lámina de protección.
Para responder con su sistema
¿Qué parte de su sistema parece protegida sin estarlo, y cómo lo demostrarían con una terminal?
Si su protección depende de una herramienta sin código, ¿qué ve alguien que abre el enlace en una ventana privada?
Minimización
El dato más seguro es el que no se guarda
Cada campo que se guarda es una promesa de cuidarlo, y cada copia es una puerta más por donde puede salir. La discusión sobre cifrado, contraseñas y respaldos suele empezar tarde; la decisión más protectora ocurre antes, cuando alguien pregunta si ese dato hace falta. La Ley 1581 lo pone como principio de finalidad: el tratamiento debe obedecer a una finalidad legítima, informada al titular. Lo que no sirve a ninguna pregunta del sistema no debería estar en su lago.

La evidencia
La brecha de Equifax expuso a 147 millones de personas, muchas de ellas sin ninguna relación contractual con la empresa. En el último informe de Verizon, el 48 % de las brechas involucró ransomware.
Para responder con su sistema
¿Qué columna de su lago podrían borrar hoy sin que ninguna pregunta del sistema pierda su respuesta?
¿Dónde hay copias de sus datos fuera del repositorio: descargas, hojas de cálculo, conversaciones con una IA?
Agentes
La herramienta que ayuda también puede actuar
Un asistente que lee un repositorio puede escribirlo, y uno que consulta una base puede borrarla si nadie le quitó el permiso. En julio de 2026 lo que parecía un argumento de ciencia ficción se volvió informe oficial: modelos evaluados en entornos que se creían cerrados encontraron la salida y actuaron sobre sistemas reales. No hace falta un modelo de frontera para que el principio aplique. El agente del grupo trabaja con los permisos que el grupo le dio, y el mínimo privilegio no es desconfianza: es diseño.

La evidencia
El AI Security Institute del Reino Unido documentó 10 de 122 corridas en las que los agentes actuaron por su cuenta sobre internet real, en medio de cuatro divulgaciones en cinco semanas. En el laboratorio, el servidor MCP abre el lago en solo lectura por defecto.
Para responder con su sistema
¿Qué permisos tuvo la IA mientras construían su sistema: repositorio, terminal, credenciales, base de datos?
¿Qué texto de su lago podría traer instrucciones escondidas para un asistente que lo lea?
Ética y ley
La autorización separa un ejercicio de un delito
El ataque entre grupos del taller usa las mismas técnicas que un ataque real. Lo que lo vuelve legítimo no es la intención ni la destreza, sino la autorización. En Colombia la ley lo dice con precisión desde 2009: acceder sin permiso a un sistema informático es delito aunque el sistema esté mal protegido y aunque no se lleve nada. La ética del oficio empieza por pedir permiso por escrito y termina donde termina ese permiso.

La evidencia
El artículo 269A de la Ley 1273 castiga a quien, «sin autorización o por fuera de lo acordado», acceda a un sistema informático «protegido o no con una medida de seguridad»: de 48 a 96 meses de prisión y una multa de 100 a 1.000 SMLMV. En 2025 hubo 69.328 denuncias por delitos informáticos en el país.
Para responder con su sistema
¿Qué dice exactamente el acuerdo con el grupo que los va a atacar, y qué queda por fuera de él?
Si durante el ataque encuentran datos de personas reales, ¿qué hacen con ellos?
La cadena del laboratorio
Cuántos terceros entran con cada herramienta
Paquetes instalados, además del instalador, al poner cada herramienta sola en un entorno limpio. Es la parte visible de la cadena de suministro: cada paquete tiene sus propios mantenedores, sus propias versiones y sus propios riesgos.

Python · pip

duckdb
1
polars
2
overturemaps
9
pyiceberg[sql-sqlite,pyarrow]
28
streamlit
35
dlt[duckdb]
38
frictionless
39
datacontract-cli[duckdb]
58
dbt-duckdb
59
great_expectations
117
JavaScript · npm, con --ignore-scripts

maplibre-gl
25
@observablehq/framework
260
Instalar DuckDB trae un paquete; instalar Great Expectations trae 117. Del lado de JavaScript, Observable Framework trae 260, y dos de esas entradas declaran scripts de instalación, ambas de esbuild: código que correría al instalar si no se usara --ignore-scripts.

copiar
# Python: un entorno limpio por herramienta
python3 -m venv prueba && ./prueba/bin/pip install dbt-duckdb
./prueba/bin/pip list --format=freeze | grep -v "^pip==" | wc -l

# npm: sin correr scripts de instalación de terceros
npm init -y && npm install --ignore-scripts @observablehq/framework
npm ls --all --parseable | tail -n +2 | sort -u | wc -l
Medido para este taller el 14 de septiembre de 2026, con Python 3.14 y pip en entornos virtuales nuevos, y con Node 20 y npm. Las cifras cambian con cada versión y cada sistema operativo, y no se suman entre sí porque muchas dependencias se comparten: repitan la medición con lo que ustedes instalen.

La seguridad de un sistema pequeño casi nunca se juega en un ataque sofisticado, sino en decisiones pequeñas: una clave que viajó por un chat, un paquete que nadie leyó, un permiso de escritura que se dejó por comodidad. Por eso la pregunta de esta lámina no es qué herramienta de seguridad usar, sino qué decisiones tomó el grupo sin darse cuenta de que las estaba tomando.

Las tecnologías de un sistema de información, definidas para decidir
No son definiciones de diccionario: dicen qué cambia en el sistema cuando se usa cada una y dónde suele estar la trampa. Están ordenadas por el estado actual y por el tramo de la ruta en que aparecen. Las herramientas concretas tienen su ficha, con cómo probarlas, al hacer clic en su nombre.

Las tecnologías, tramo por tramo
Escojan un tramo, o véanlas todas
Las marcadas como nuevas se escribieron para este taller; las demás son de uso corriente en el oficio y aquí quedan ubicadas en el tramo donde se usan.

Todas
Estado actual
Rastreo
Pregunta
Permiso
Contrato y lago
Verificación
Vistas
Protección
IA en todo el recorrido
Para pensar
8 términos · 7 nuevos

Estado actual
Gobierno de datosnuevo
El ejercicio de autoridad y control —planificación, monitoreo y aplicación— sobre la gestión de los activos de datos: así lo define el DMBOK de DAMA International. La distinción que ordena todo es entre gobierno y gestión: el gobierno decide quién responde y con qué reglas; la gestión ejecuta. Un equipo que limpia datos sin que nadie haya dicho quién responde por ellos está gestionando sin gobierno.
Catálogo de datosnuevo
Inventario navegable de los datos con sus metadatos: qué significa cada campo, quién responde, de dónde viene, quién lo usa. En el lakehouse actual el catálogo dejó de ser documentación y pasó a ser infraestructura: decide qué motor puede leer qué tabla y con qué permisos, y por eso es donde hoy compiten Apache Polaris y Unity Catalog.
Arquitectura medallónnuevo
Patrón de capas para un lago —bronce para lo crudo, plata para lo limpio y conformado, oro para lo listo para consumir— que Databricks nombra y documenta como medallion architecture. En el Cerebro Lima las tres capas existen sin llamarse así: lago/raw, lago y las vistas. Sirve como vocabulario común; no es una norma.
Viaje en el tiemponuevo
Capacidad de un formato de tabla de consultar los datos como estaban en una versión anterior. DuckLake, Apache Iceberg y Delta Lake la ofrecen porque cada escritura crea una instantánea en lugar de sobrescribir. Sirve para auditar, reproducir un informe viejo o deshacer una carga mala, y cobra en espacio si nadie limpia las instantáneas antiguas.
Producto de datosnuevo
Conjunto de datos tratado como producto: con dueño, usuarios, documentación, contrato y nivel de servicio. Es uno de los cuatro principios del data mesh que Zhamak Dehghani formuló en 2020. La prueba es sencilla: si nadie sabría a quién reclamarle cuando el dato falla, no es un producto, es un archivo.
Data mesh
Arquitectura sociotécnica que trata los datos como producto y devuelve su propiedad a los dominios de negocio, con una plataforma común de autoservicio y gobernanza federada. En organizaciones pequeñas suele ser sobre-ingeniería.
Políticas como códigonuevo
Reglas de acceso y de uso escritas en un lenguaje que un programa evalúa, versionadas junto al sistema en lugar de vivir en un documento. Open Policy Agent, proyecto graduado de la CNCF desde 2021, es la referencia de propósito general. Es el gobierno «computacional» del data mesh llevado a la práctica.
Licencia de código disponiblenuevo
Licencia que deja ver y usar el código pero restringe algo que las licencias de código abierto aprobadas por la OSI no restringen, típicamente ofrecerlo como servicio. Elastic License 2.0 es un ejemplo: Soda Core pasó a ella en enero de 2026. Para un sistema de información importa porque la herramienta de la que depende puede cambiar de reglas sin cambiar de nombre.
Los hechos que traen algunas definiciones —quién publicó un estándar, bajo qué licencia, desde cuándo— se comprobaron contra la fuente primaria de cada tecnología el 14 de septiembre de 2026. Los números de versión se dejaron afuera a propósito, porque caducan en semanas. Si encuentran una definición que ya no es cierta, díganlo: corregirla es parte del ejercicio.

El sistema, la bitácora de exploración y las decisiones por escrito
El sistema
El enlace público y funcionando, con los nombres del grupo visibles. Si tiene compuerta, la clave se le entrega aparte al profesor.

La réplica
El repositorio con el contrato, los scripts de ingesta, la verificación y el catálogo de fuentes completo, con las que no entraron y la razón.

La exploración
La bitácora de exploración: por lo menos dos herramientas probadas en cada tramo, con los mismos criterios, y cuál quedó y por qué.

Las decisiones
Un README con las cuatro decisiones, la bitácora de IA, el resultado de las dos revisiones entre grupos y su posición frente a dos reflexiones: una de datos y una de seguridad.

En clase
Una presentación corta con el sistema abierto en pantalla. Sin diapositivas.

El piso técnico es corto: que abra desde un teléfono; que cada cifra muestre fuente, vigencia y fecha de prueba a un clic; que haya al menos una vista sobre el territorio; que el lago se reconstruya desde los scripts; que cada tramo tenga dos herramientas exploradas y anotadas; que ninguna pieza dependa de una llave paga, y, si hay compuerta, que pase las pruebas de la terminal. Todo lo demás lo deciden ustedes.

Este es el esqueleto del README. Cópienlo al empezar, no al final: se va llenando tramo a tramo, y un README escrito la última noche se nota.

copiar
# <Ciudad> · sistema de información

Grupo: <nombres y papeles> · Enlace: <url> · Revisado: <AAAA-MM-DD>

## Para quién y qué pregunta
- Usuario:
- Preguntas (entre tres y seis):
- Escala y comparación:
- Lo que decidimos no mostrar, y por qué:

## La réplica
- Qué replicamos tal cual del ejemplo y qué tuvimos que cambiar para nuestra ciudad:
- Fuentes catalogadas · integradas · caídas · descartadas: (ver catalogo/)
- Huecos: lo que buscamos y no existe abierto para esta ciudad:

## ¿Se puede usar?
| Fuente | Licencia | Personas | Estado | Condición |
|---|---|---|---|---|

## Bitácora de exploración
| Tramo | Herramienta | Qué pidió para empezar | Licencia | Dónde quedan los datos | ¿Se rehace con un comando? | Estado del proyecto | Qué resolvió | Qué no pudo | ¿Quedó? ¿Por qué? |
|---|---|---|---|---|---|---|---|---|---|

## Protección
- Nivel: abierto · solo agregados · compuerta · no se publica
- Qué protegemos, y de quién:
- Pruebas de terminal o de ventana privada:
- Revisión de secretos en el historial:

## Herramienta elegida para las vistas
- Qué necesitábamos mostrar:
- Qué teníamos que proteger:
- Por qué esta herramienta cumple las dos cosas, y cuál descartamos por poco:

## Nuestra posición
- Una reflexión de gestión y gobierno de datos, y nuestra respuesta con evidencia de nuestro sistema:
- Una reflexión de ciberseguridad, y nuestra respuesta con evidencia de nuestro sistema:

## Bitácora de IA
| Tramo | Herramienta | Qué le encargamos | Qué entregó | Qué le corregimos |
|---|---|---|---|---|

## Revisión cruzada
- Tres cifras auditadas por el grupo <X>: resultado y correcciones
- Ataque del grupo <Y>: qué intentó, qué consiguió, qué cambiamos
- Vueltas atrás en la ruta: de qué tramo a cuál, y por qué
Es un sistema de información
Cada cifra dice de dónde salió, qué cubre y cuándo se probó.
El catálogo cuenta también lo que no sirvió, y por qué.
Probaron varias herramientas sobre los mismos datos y dicen por qué quedó una.
La protección es proporcional a lo que hay que proteger, y está probada.
Las bitácoras muestran lo que corrigieron y las vueltas atrás, no solo lo que salió bien.
Es una vitrina
«Fuente: datos abiertos», sin entidad, documento ni fecha.
Solo aparece lo que funcionó.
Usaron la primera herramienta que apareció y no saben qué licencia tiene.
La clave en el JavaScript, o datos de personas a la vista.
«Lo hizo la IA», sin una sola corrección registrada.
La presentación en clase responde esto
¿Qué herramienta descartaron que casi eligen, qué decidieron no mostrar, y qué tendría que cambiar —en la fuente, en la herramienta o en su propio sistema— para que la respuesta fuera otra?