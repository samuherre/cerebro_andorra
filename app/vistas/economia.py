"""Vista Economía de la App_Streamlit de Cerebro Andorra.

Reúne dos dominios económicos del país a partir de los datos procesados, ambos
con linaje OBSERVADO (datos oficiales del Departament d'Estadística d'Andorra):

1. **Turismo** (``turismo.csv``): el presupuesto de funcionamiento
   (``DESPESES DE FUNCIONAMENT``) y el total del presupuesto de despeses
   (``TOTAL PRESSUPOST DE DESPESES``) de Andorra Turisme SAU por año
   (2020-2025), en euros (Req 3.7).
2. **Inversiones inmobiliarias** (``inversiones_inmobiliarias.csv``): el número
   de inversiones inmobiliarias por año (2020-2025) (Req 4.7).
3. **Economía World Bank** (``economia_worldbank.csv``): los indicadores
   macroeconómicos del Banco Mundial (PIB, IPC, PIB per cápita) por año, con su
   serie temporal y su última cifra gobernada (Req 5.1-5.5).

La sección de economía resuelve de forma dinámica su ``id_fuente`` desde el
Inventario_Fuentes (buscando la fuente ``economia_worldbank``) en lugar de
fijarlo por constante, de modo que la vista siga el inventario como fuente de
verdad. Si la tabla de economía no tiene ningún indicador integrado
(DataFrame ``None`` o vacío, como cuando no se ha descargado ningún JSON del
Banco Mundial), se muestra un mensaje explícito de ausencia de fuente económica
real, sin renderizar cifras ni gráficos del dominio (Req 5.3).

Toda cifra se muestra exclusivamente a través de ``componentes.cifra_gobernada``
—reconstruyendo su Metadato_Cifra (fuente, vigencia, fecha de prueba) y su
Etiqueta_Linaje a partir de cada fila—, de modo que el principio rector del
proyecto ("0 cifras sin fuente, sin vigencia y sin fecha de prueba") quede
garantizado. Se pasa además el ``id_fuente`` correspondiente (``F03`` turismo,
``F04`` inversiones) para habilitar el Detalle_Gobernanza a un clic.

Si un dominio no tiene datos (DataFrame ``None`` o vacío) se muestra un mensaje
de ausencia en español en esa sección, sin interrumpir la carga del resto de la
vista (Req 3.8, 4.8).

Como este módulo vive en ``app/vistas/`` y reutiliza los módulos hermanos
``carga_datos.py`` y ``componentes.py`` (ubicados en ``app/``), se añade la
carpeta ``app/`` al ``sys.path`` resolviéndola de forma relativa a este archivo.

Mensajes de consola y textos de interfaz en español, coherentes con el resto del
proyecto.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de módulos hermanos ------
# parents[1] sube desde app/vistas/economia.py hasta app/; desde ahí se importan
# carga_datos y componentes sin necesidad de convertir app/ en un paquete.
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path
import componentes  # noqa: E402 - import tras ajustar sys.path

# ID_Fuente estables en el Inventario_Fuentes para habilitar el
# Detalle_Gobernanza a un clic bajo cada cifra (Req 5.5).
_ID_FUENTE_TURISMO = "F03"
_ID_FUENTE_INVERSIONES = "F04"

# Subcadenas identificadoras del `nombre` de la fuente de economía en el
# Inventario_Fuentes, para resolver su ID_Fuente de forma dinámica (sin fijarlo
# por constante). Se busca por subcadena porque el `nombre` del inventario
# (``economia_worldbank.csv``) no coincide carácter a carácter con el campo
# `fuente` de los datos procesados (Req 5.5).
_CLAVES_ECONOMIA = ("economia_worldbank", "world bank", "banco mundial")

# Códigos de indicador World Bank que la Vista_Economia muestra en su sección
# económica, en el orden de presentación: PIB, IPC y PIB per cápita (Req 5.1).
# La población total (``SP.POP.TOTL``) se excluye aquí por pertenecer al dominio
# de población, no al de economía.
_INDICADORES_ECONOMIA = (
    "NY.GDP.MKTP.CD",
    "FP.CPI.TOTL.ZG",
    "NY.GDP.PCAP.CD",
)

# Nombres de las dos partidas del presupuesto de turismo tal como quedan
# normalizadas en turismo.csv (en mayúsculas, en catalán).
_PARTIDA_FUNCIONAMENT = "DESPESES DE FUNCIONAMENT"
_PARTIDA_TOTAL = "TOTAL PRESSUPOST DE DESPESES"

# Rótulos en español para presentar cada partida en la interfaz.
_ETIQUETA_PARTIDA = {
    _PARTIDA_FUNCIONAMENT: "Presupuesto de funcionamiento",
    _PARTIDA_TOTAL: "Total del presupuesto de despeses",
}


def _metadato_de_fila(fila: "pd.Series") -> "dict | None":
    """Construye el Metadato_Cifra de una fila, o ``None`` si falta algún campo.

    Reúne ``fuente``, ``vigencia`` y ``fecha_prueba`` presentes en el registro
    procesado. Si faltara alguna de esas columnas se devuelve ``None`` para que
    ``cifra_gobernada`` trate la cifra como no disponible por metadato
    incompleto, en lugar de romper la vista.

    Args:
        fila: registro (``pd.Series``) de turismo o de inversiones.

    Returns:
        Diccionario con ``fuente``, ``vigencia`` y ``fecha_prueba``, o ``None``
        si el registro no dispone de esas columnas.
    """
    campos = ("fuente", "vigencia", "fecha_prueba")
    if not all(campo in fila.index for campo in campos):
        return None
    return {campo: fila[campo] for campo in campos}


def _linaje_de_fila(fila: "pd.Series") -> "str | None":
    """Devuelve la Etiqueta_Linaje de la fila, o ``None`` si no la tiene.

    Si la columna ``linaje`` falta o está vacía se devuelve ``None`` para que
    ``cifra_gobernada`` omita la cifra por linaje ausente.

    Args:
        fila: registro (``pd.Series``) de turismo o de inversiones.

    Returns:
        La etiqueta de linaje, o ``None`` si no está disponible.
    """
    if "linaje" not in fila.index:
        return None
    valor = fila["linaje"]
    if valor is None or pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto or None


def _euros(valor: float) -> str:
    """Formatea un importe en euros con separador de miles en estilo español.

    Args:
        valor: importe numérico en euros.

    Returns:
        Cadena del tipo ``"20.867.866 €"`` (miles separados por punto).
    """
    entero = int(round(float(valor)))
    return f"{entero:,}".replace(",", ".") + " €"


def _seccion_turismo() -> None:
    """Renderiza la sección de presupuesto de turismo por año.

    Carga ``turismo.csv`` y, para cada año (periodo) disponible, muestra el
    presupuesto de funcionamiento y el total del presupuesto de despeses como
    cifras gobernadas (linaje OBSERVADO), reconstruyendo el Metadato_Cifra y el
    linaje desde cada fila y pasando ``id_fuente=F03`` para habilitar el
    Detalle_Gobernanza (Req 3.7).

    Si no hay datos (DataFrame ``None`` o vacío), muestra un mensaje de ausencia
    en español sin interrumpir el resto de la vista (Req 3.8).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.header("Turismo")
    st.caption(
        "Presupuesto de Andorra Turisme SAU por año (datos oficiales, linaje "
        "OBSERVADO)."
    )

    turismo = carga_datos.carga_turismo()
    if turismo is None or turismo.empty:
        st.warning(
            "Presupuesto de turismo: Dato no disponible. No se pudieron cargar "
            "los datos procesados de turismo."
        )
        return

    # Años disponibles en orden ascendente. Si no hay columna 'periodo' o ningún
    # periodo numérico, se trata como ausencia de datos.
    periodos = pd.to_numeric(turismo.get("periodo"), errors="coerce").dropna()
    if periodos.empty:
        st.warning(
            "Presupuesto de turismo: Dato no disponible. No se pudo identificar "
            "el año de ninguna partida."
        )
        return

    anios = sorted({int(p) for p in periodos})

    for anio in anios:
        st.subheader(f"Año {anio}")
        filas_anio = turismo[
            pd.to_numeric(turismo["periodo"], errors="coerce") == anio
        ]

        columna_funcionamiento, columna_total = st.columns(2)
        for partida, columna in (
            (_PARTIDA_FUNCIONAMENT, columna_funcionamiento),
            (_PARTIDA_TOTAL, columna_total),
        ):
            etiqueta = _ETIQUETA_PARTIDA[partida]
            fila_partida = filas_anio[filas_anio.get("partida") == partida]
            with columna:
                if fila_partida.empty:
                    # La partida no está presente para este año: cifra ausente.
                    componentes.cifra_gobernada(
                        f"{etiqueta} ({anio})",
                        None,
                        None,
                        None,
                        id_fuente=_ID_FUENTE_TURISMO,
                    )
                    continue

                fila = fila_partida.iloc[0]
                valor_eur = pd.to_numeric(
                    fila.get("valor_eur"), errors="coerce"
                )
                valor = None if pd.isna(valor_eur) else _euros(valor_eur)

                componentes.cifra_gobernada(
                    f"{etiqueta} ({anio})",
                    valor,
                    _metadato_de_fila(fila),
                    _linaje_de_fila(fila),
                    id_fuente=_ID_FUENTE_TURISMO,
                )


def _seccion_inversiones() -> None:
    """Renderiza la sección de número de inversiones inmobiliarias por año.

    Carga ``inversiones_inmobiliarias.csv`` y, para cada año disponible, muestra
    el número de inversiones como cifra gobernada (linaje OBSERVADO),
    reconstruyendo el Metadato_Cifra y el linaje desde cada fila y pasando
    ``id_fuente=F04`` para habilitar el Detalle_Gobernanza (Req 4.7).

    Si no hay datos (DataFrame ``None`` o vacío), muestra un mensaje de ausencia
    en español sin interrumpir el resto de la vista (Req 4.8).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.header("Inversiones inmobiliarias")
    st.caption(
        "Número de inversiones inmobiliarias por año (datos oficiales, linaje "
        "OBSERVADO)."
    )

    inversiones = carga_datos.carga_inversiones()
    if inversiones is None or inversiones.empty:
        st.warning(
            "Inversiones inmobiliarias: Dato no disponible. No se pudieron "
            "cargar los datos procesados de inversiones."
        )
        return

    # Años disponibles en orden ascendente. Sin columna 'anio' o sin ningún año
    # numérico, se trata como ausencia de datos.
    anios_serie = pd.to_numeric(inversiones.get("anio"), errors="coerce").dropna()
    if anios_serie.empty:
        st.warning(
            "Inversiones inmobiliarias: Dato no disponible. No se pudo "
            "identificar el año de ningún registro."
        )
        return

    anios = sorted({int(a) for a in anios_serie})

    # Mostrar las cifras en filas de hasta 3 columnas para un diseño compacto y
    # responsive (cada columna se expande al ancho del contenedor).
    for inicio in range(0, len(anios), 3):
        grupo = anios[inicio:inicio + 3]
        columnas = st.columns(len(grupo))
        for anio, columna in zip(grupo, columnas):
            filas_anio = inversiones[
                pd.to_numeric(inversiones["anio"], errors="coerce") == anio
            ]
            with columna:
                if filas_anio.empty:
                    componentes.cifra_gobernada(
                        f"Nº de inversiones ({anio})",
                        None,
                        None,
                        None,
                        id_fuente=_ID_FUENTE_INVERSIONES,
                    )
                    continue

                fila = filas_anio.iloc[0]
                num = pd.to_numeric(
                    fila.get("num_inversiones"), errors="coerce"
                )
                valor = None if pd.isna(num) else int(num)

                componentes.cifra_gobernada(
                    f"Nº de inversiones ({anio})",
                    valor,
                    _metadato_de_fila(fila),
                    _linaje_de_fila(fila),
                    id_fuente=_ID_FUENTE_INVERSIONES,
                )


def _id_fuente_economia(inventario) -> "str | None":
    """Resuelve el ID_Fuente de la economía World Bank desde el inventario.

    Recorre el Inventario_Fuentes y devuelve el ``id_fuente`` de la primera fila
    cuyo campo ``nombre`` contiene (sin distinguir mayúsculas) alguna de las
    subcadenas de ``_CLAVES_ECONOMIA`` (``economia_worldbank``, ``world bank``,
    ``banco mundial``). Permite pasar el ``id_fuente`` real al
    Detalle_Gobernanza de cada cifra (Req 5.5) sin fijarlo por constante, de
    modo que la vista siga el inventario como fuente de verdad.

    Args:
        inventario: ``DataFrame`` del Inventario_Fuentes, o ``None`` si no se
            pudo cargar.

    Returns:
        El ``id_fuente`` de la primera fila coincidente, o ``None`` si el
        inventario no está disponible o ninguna fila coincide.
    """
    if inventario is None or inventario.empty:
        return None
    if "nombre" not in inventario.columns or "id_fuente" not in inventario.columns:
        return None

    for _, fila in inventario.iterrows():
        nombre = str(fila.get("nombre", "")).lower()
        if any(clave in nombre for clave in _CLAVES_ECONOMIA):
            id_fuente = fila.get("id_fuente")
            if id_fuente is None or str(id_fuente).strip() == "":
                return None
            return str(id_fuente).strip()
    return None


def _grafico_serie_indicador(
    datos_indicador: "pd.DataFrame", nombre: str, unidad: str
) -> None:
    """Dibuja la serie temporal (año→valor) de un indicador con Plotly.

    Usa un import perezoso de Plotly Express para que el módulo siga siendo
    importable aunque la librería no esté instalada (validación/``py_compile``);
    si la dependencia falta, degrada de forma segura con un mensaje en español
    sin interrumpir el resto de la vista. El gráfico se dibuja con
    ``use_container_width=True`` para ser usable también en móvil.

    Args:
        datos_indicador: filas del indicador con columnas ``anio`` y ``valor``.
        nombre: nombre legible del indicador (p. ej. "PIB (US$ corrientes)").
        unidad: unidad del indicador para rotular el eje de valores.
    """
    serie = datos_indicador.copy()
    serie["anio"] = pd.to_numeric(serie.get("anio"), errors="coerce")
    serie["valor"] = pd.to_numeric(serie.get("valor"), errors="coerce")
    serie = serie.dropna(subset=["anio", "valor"]).sort_values("anio")

    if serie.empty:
        st.caption(
            "No hay una serie temporal representable para este indicador."
        )
        return

    try:
        import plotly.express as px
    except Exception as error:  # noqa: BLE001 - degradación segura en la app
        print(f"[economia] No se pudo importar plotly: {error}.")
        st.caption(
            "No se pudo cargar la librería de gráficos (plotly); se muestra la "
            "última cifra sin la serie temporal."
        )
        return

    etiqueta_valor = f"Valor ({unidad})" if unidad else "Valor"
    figura = px.line(
        serie,
        x="anio",
        y="valor",
        markers=True,
        labels={"anio": "Año", "valor": etiqueta_valor},
        title=nombre,
    )
    figura.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(figura, use_container_width=True)


def _seccion_economia() -> None:
    """Renderiza la sección de indicadores macroeconómicos del Banco Mundial.

    Carga ``economia_worldbank.csv`` vía ``carga_datos.carga_economia()`` y, por
    cada indicador económico (PIB, IPC, PIB per cápita), muestra su serie
    temporal (año→valor) y su última cifra —la del año máximo disponible— a
    través de ``componentes.cifra_gobernada`` (linaje OBSERVADO), resolviendo el
    ``id_fuente`` de forma dinámica desde el Inventario_Fuentes para habilitar
    el Detalle_Gobernanza a un clic (Req 5.1, 5.2, 5.5). Si un indicador carece
    de gobernanza completa, ``cifra_gobernada`` lo omite mostrando su motivo
    (Req 5.4).

    Si no hay ningún indicador integrado (DataFrame ``None`` o vacío, como
    cuando no se ha descargado ningún JSON del Banco Mundial), muestra un
    mensaje explícito de ausencia de fuente económica real, sin renderizar
    cifras ni gráficos del dominio (Req 5.3).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.header("Macroeconomía (Banco Mundial)")
    st.caption(
        "Indicadores macroeconómicos de Andorra del Banco Mundial (World Bank "
        "Open Data), con linaje OBSERVADO."
    )

    economia = carga_datos.carga_economia()
    if economia is None or economia.empty:
        # Ausencia total de fuente económica real: no se renderiza ninguna cifra
        # ni gráfico del dominio, solo el mensaje explícito (Req 5.3).
        st.warning(
            "Macroeconomía: no hay ninguna fuente económica real integrada. No "
            "se ha podido cargar ningún indicador del Banco Mundial "
            "(economia_worldbank.csv está vacío o no disponible), por lo que no "
            "se muestran cifras ni gráficos económicos."
        )
        return

    if "codigo" not in economia.columns:
        st.warning(
            "Macroeconomía: la tabla de economía no tiene la columna 'codigo', "
            "no se pueden identificar los indicadores."
        )
        return

    # ID_Fuente resuelto dinámicamente desde el inventario (Req 5.5).
    inventario = carga_datos.carga_inventario()
    id_fuente = _id_fuente_economia(inventario)

    # Recorrer los indicadores económicos en el orden de presentación. Se
    # muestran solo los que tengan al menos una fila en la tabla; los ausentes
    # se declaran con un mensaje de ausencia por indicador sin romper el resto.
    algun_indicador = False
    for codigo in _INDICADORES_ECONOMIA:
        filas_indicador = economia[economia["codigo"].astype(str).str.strip() == codigo]
        if filas_indicador.empty:
            continue

        algun_indicador = True

        # Nombre y unidad legibles del indicador (tomados de la propia tabla).
        nombre = str(filas_indicador.iloc[0].get("indicador", codigo)) or codigo
        unidad = str(filas_indicador.iloc[0].get("unidad", "") or "")

        st.subheader(nombre)

        # Serie temporal del indicador (Req 5.1).
        _grafico_serie_indicador(filas_indicador, nombre, unidad)

        # Última cifra: la del año máximo disponible (Req 5.2).
        anios = pd.to_numeric(
            filas_indicador.get("anio"), errors="coerce"
        ).dropna()
        if anios.empty:
            componentes.cifra_gobernada(
                f"{nombre} (última cifra)",
                None,
                None,
                None,
                id_fuente=id_fuente,
            )
            continue

        anio_reciente = int(anios.max())
        filas_reciente = filas_indicador[
            pd.to_numeric(filas_indicador["anio"], errors="coerce") == anio_reciente
        ]
        fila = filas_reciente.iloc[0]

        valor_num = pd.to_numeric(pd.Series([fila.get("valor")]), errors="coerce").iloc[0]
        valor = None if pd.isna(valor_num) else _formatea_valor_economia(valor_num, unidad)

        componentes.cifra_gobernada(
            f"{nombre} ({anio_reciente})",
            valor,
            _metadato_de_fila(fila),
            _linaje_de_fila(fila),
            id_fuente=id_fuente,
        )

    if not algun_indicador:
        # Hay tabla, pero ninguno de los indicadores económicos esperados tiene
        # filas: se trata como ausencia de fuente económica real (Req 5.3).
        st.warning(
            "Macroeconomía: no hay ningún indicador económico integrado (PIB, "
            "IPC o PIB per cápita) en la tabla del Banco Mundial, por lo que no "
            "se muestran cifras ni gráficos económicos."
        )


def _formatea_valor_economia(valor: float, unidad: str) -> str:
    """Formatea el valor de un indicador económico según su unidad.

    Presenta las magnitudes monetarias grandes (US$) con separador de miles en
    estilo español y los porcentajes/tasas con dos decimales, anexando la
    unidad cuando está disponible.

    Args:
        valor: valor numérico del indicador.
        unidad: unidad del indicador (p. ej. "US$", "% anual").

    Returns:
        Cadena legible del valor con su unidad.
    """
    unidad_norm = unidad.strip()
    texto_unidad = f" {unidad_norm}" if unidad_norm else ""

    # Importes monetarios grandes: entero con separador de miles estilo español.
    if "$" in unidad_norm or "US" in unidad_norm.upper():
        entero = int(round(float(valor)))
        return f"{entero:,}".replace(",", ".") + texto_unidad

    # Porcentajes, tasas y demás: dos decimales en estilo español.
    return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + texto_unidad


def render() -> None:
    """Renderiza la Vista Economía completa.

    Punto de entrada que ``streamlit_app.py`` invoca para pintar la vista.
    Presenta tres secciones identificables y separadas —turismo, inversiones
    inmobiliarias y macroeconomía del Banco Mundial—, cada una con sus cifras
    gobernadas de linaje OBSERVADO. Un fallo de datos en una sección muestra su
    mensaje de ausencia sin interrumpir la carga de las otras (Req 3.7, 3.8,
    4.7, 4.8, 5.1-5.5).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.title("Economía")
    st.write(
        "Indicadores económicos oficiales de Andorra: el presupuesto de turismo, "
        "el número de inversiones inmobiliarias por año y los indicadores "
        "macroeconómicos del Banco Mundial. Toda cifra se muestra con su fuente, "
        "vigencia, fecha de prueba y etiqueta de linaje."
    )

    _seccion_turismo()
    st.divider()
    _seccion_inversiones()
    st.divider()
    _seccion_economia()
