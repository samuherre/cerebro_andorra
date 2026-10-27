"""Vista Gente/Población de la App_Streamlit de Cerebro Andorra.

Presenta la población de las 7 parròquies de Andorra a partir de los datos
procesados, respetando el principio rector del proyecto: "0 cifras sin fuente,
sin vigencia y sin fecha de prueba". Toda cifra se muestra exclusivamente a
través del componente reutilizable ``cifra_gobernada`` con su Metadato_Cifra,
la Etiqueta_Linaje OBSERVADO y el Detalle_Gobernanza a un clic.

Esta versión (Parte 3) enriquece la vista con los Desglose_Poblacion reales
procesados en ``datos_procesados/poblacion_desgloses.csv`` (Req 2):

- Conserva el bloque de población total por parròquia de la Parte 2.
- Añade un selector de parròquia y año que actualiza todas las visualizaciones
  a la selección vigente (Req 2.3).
- Muestra tres visualizaciones gobernadas por dimensión (Req 2.1, 2.2, 2.4):
  una pirámide por edad y sexo, una composición por nacionalidad (top-N + Otros)
  y una distribución por lugar de nacimiento.
- Sustituye el texto de marcador de posición de la v1 (desgloses "candidatos no
  procesados") por datos reales (Req 2.5).
- Si un desglose falta o no tiene filas para la selección vigente, muestra un
  mensaje de ausencia para ESE desglose y conserva visibles los demás y el
  resto de la vista (Req 2.6).
- Añade un bloque de indicadores sociales reclasificados (umbrales de pobreza y
  tasa de fecundidad) mostrados vía ``cifra_gobernada`` OBSERVADO; si un
  indicador tiene < 1 registro, muestra un mensaje de ausencia en español sin
  inventar datos (Req 3.5).

Nota sobre la pirámide (Req 2.2): los crudos por parròquia integrados ofrecen la
edad por tramos (``edad_5``) y el sexo (HOME/DONA) como dimensiones separadas;
no existe en el lago un cruce edad×sexo por parròquia. Para no inventar datos, la
pirámide representa el perfil por tramos de edad (eje vertical) y el reparto
HOME/DONA de la parròquia como barras divergentes (HOME negativo a la izquierda,
DONA a la derecha), mostrando con ``cifra_gobernada`` los totales OBSERVADO.

La app se lanza desde la raíz del repositorio
(``streamlit run app/streamlit_app.py``). Como ``poblacion.py`` vive en
``app/vistas/`` y necesita importar ``carga_datos`` y ``componentes`` de
``app/``, se añade la carpeta ``app/`` al ``sys.path`` resolviéndola de forma
relativa a este archivo (``parents[1]``).

Textos de interfaz y mensajes de consola en español, coherentes con el resto
del proyecto.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de módulos ---------------
# parents[1] sube desde app/vistas/poblacion.py hasta app/; desde ahí se pueden
# importar carga_datos y componentes sin convertir app/ en un paquete.
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path
from componentes import cifra_gobernada  # noqa: E402 - import tras ajustar sys.path

# Rango de años esperado para el selector (Req 6.3 Parte 2 / Req 2.3). Se
# intersecta con los años realmente presentes en los datos para no ofrecer años
# sin cifras.
ANIO_MIN = 2020
ANIO_MAX = 2025

# ID_Fuente estable del desglose de población en el Inventario_Fuentes, para
# habilitar el Detalle_Gobernanza a un clic bajo cada cifra (Req 2.4).
_ID_FUENTE_DESGLOSES = "F10"

# ID_Fuente estables de los indicadores sociales reclasificados en el
# Inventario_Fuentes, para el Detalle_Gobernanza a un clic bajo cada cifra del
# bloque social (Req 3.5). Son valores de respaldo: si el inventario está
# disponible, el ID se resuelve del propio inventario por nombre de archivo.
_ID_FUENTE_UMBRALES = "F11"
_ID_FUENTE_FECUNDIDAD = "F12"

# Nombres de archivo con los que cada indicador social figura en el
# Inventario_Fuentes (columna ``nombre``), usados para resolver su ID_Fuente.
_ARCHIVO_UMBRALES = "umbrales_pobreza.csv"
_ARCHIVO_FECUNDIDAD = "tasa_fecundidad.csv"

# Número máximo de nacionalidades mostradas de forma individual en la
# composición por nacionalidad; el resto se agrega en la categoría "Otros"
# (Req 2.1) para no fabricar ni ocultar datos, solo compactar la lectura.
_TOP_N_NACIONALIDAD = 8

# Etiqueta explícita para el valor agregado de nacionalidades fuera del top-N.
_ETIQUETA_OTROS = "Otros"

# Categoría del crudo de nacionalidad que ya representa un agregado ("ALTRES
# NACIONALITATS"): se trata como parte de "Otros" para no duplicar el residuo.
_CATEGORIA_ALTRES = "ALTRES NACIONALITATS"


def _construye_metadato(fila: "pd.Series") -> "dict | None":
    """Reconstruye el Metadato_Cifra de una fila, o ``None`` si falta un campo.

    Toma los campos de gobernanza que viajan con cada registro procesado y los
    empaqueta en el diccionario que espera ``cifra_gobernada``. Si faltara
    alguna columna, devuelve ``None`` para que ``cifra_gobernada`` trate la
    cifra como no disponible por metadato incompleto en lugar de romper.

    Args:
        fila: fila del DataFrame con las columnas de gobernanza.

    Returns:
        Diccionario con ``fuente``, ``vigencia`` y ``fecha_prueba``, o ``None``.
    """
    campos = ("fuente", "vigencia", "fecha_prueba")
    if not all(campo in fila.index for campo in campos):
        return None
    return {campo: fila[campo] for campo in campos}


def _linaje_de_fila(fila: "pd.Series") -> "str | None":
    """Devuelve la Etiqueta_Linaje de la fila, o ``None`` si no la tiene.

    Args:
        fila: fila del DataFrame con la columna ``linaje``.

    Returns:
        La etiqueta de linaje (p. ej. OBSERVADO), o ``None`` si no está.
    """
    if "linaje" not in fila.index:
        return None
    valor = fila["linaje"]
    if valor is None or pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto or None


def _anios_disponibles(df: "pd.DataFrame") -> "list[int]":
    """Devuelve los años presentes en los datos dentro del rango 2020–2025.

    Filtra los años reales de la tabla al rango soportado por la vista y los
    ordena de forma ascendente, para poblar el selector sólo con años que
    tengan cifras.

    Args:
        df: DataFrame con la columna ``anio``.

    Returns:
        Lista ordenada de años (enteros) disponibles en el rango soportado.
    """
    anios = sorted(
        int(a)
        for a in pd.to_numeric(df["anio"], errors="coerce").dropna().unique()
        if ANIO_MIN <= int(a) <= ANIO_MAX
    )
    return anios


def _filtra_seleccion(
    df: "pd.DataFrame | None", parroquia: str, anio: int
) -> "pd.DataFrame | None":
    """Filtra un desglose a la parròquia y el año de la selección vigente.

    Args:
        df: desglose cargado (o ``None`` si el desglose falta/es ilegible).
        parroquia: parròquia seleccionada.
        anio: año seleccionado.

    Returns:
        Un ``DataFrame`` con las filas de la selección, o ``None`` si el
        desglose falta o no tiene filas para esa parròquia y año (Req 2.6).
    """
    if df is None or df.empty:
        return None
    if "parroquia" not in df.columns or "anio" not in df.columns:
        return None
    seleccion = df[
        (df["parroquia"] == parroquia)
        & (pd.to_numeric(df["anio"], errors="coerce") == anio)
    ]
    if seleccion.empty:
        return None
    return seleccion


def _plotly():
    """Importa Plotly de forma perezosa, o ``None`` si no está disponible.

    El import se hace dentro de la función (no en la cabecera del módulo) para
    que la vista siga cargando aunque Plotly no esté instalado; en ese caso se
    degrada a tabla.

    Returns:
        El módulo ``plotly.graph_objects``, o ``None`` si no se puede importar.
    """
    try:
        import plotly.graph_objects as go  # noqa: WPS433 - import perezoso

        return go
    except Exception as error:  # noqa: BLE001 - degradación segura en la app
        print(f"[poblacion] Plotly no disponible, se usa tabla: {error}.")
        return None


# --- Desglose: pirámide por edad y sexo ------------------------------------


def _ordena_tramos_edad(categorias: "list[str]") -> "list[str]":
    """Ordena los tramos de edad de menor a mayor por su edad inicial.

    Los tramos vienen como ``"DE 00-04 ANYS"`` … ``"DE MÉS DE 85 ANYS"``. Se
    extrae el primer número de cada etiqueta para ordenarlos; el tramo "MÉS DE
    85" (sin par inicial claro) se envía al final.

    Args:
        categorias: lista de etiquetas de tramo de edad.

    Returns:
        La lista de tramos ordenada de menor a mayor edad.
    """
    import re

    def clave(etiqueta: str) -> int:
        numeros = re.findall(r"\d+", str(etiqueta))
        return int(numeros[0]) if numeros else 10**6

    return sorted(categorias, key=clave)


def _piramide_edad_sexo(parroquia: str, anio: int) -> None:
    """Renderiza la pirámide por edad y el reparto por sexo de la selección.

    Muestra dos piezas gobernadas para la parròquia y el año elegidos (Req 2.1,
    2.2, 2.4):

    1. El perfil por tramos de edad (``edad_5``) como barras horizontales (eje
       vertical = tramo de edad), que da la forma de pirámide.
    2. El reparto por sexo (HOME/DONA) como barras divergentes —HOME negativo a
       la izquierda, DONA a la derecha—, con los totales OBSERVADO vía
       ``cifra_gobernada``.

    Si falta alguno de los dos desgloses (edad o sexo) o no hay filas para la
    selección, se muestra un mensaje de ausencia para esa pieza y se conserva la
    otra (Req 2.6).

    Args:
        parroquia: parròquia seleccionada.
        anio: año seleccionado.

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.subheader("Pirámide por edad y sexo")
    st.caption(
        "Perfil por tramos de edad y reparto por sexo de la parròquia "
        "seleccionada (datos oficiales, linaje OBSERVADO). El lago ofrece la "
        "edad y el sexo como desgloses separados por parròquia; para no "
        "inventar datos, no se cruza edad×sexo por tramo."
    )

    go = _plotly()

    # --- Pieza 1: perfil por tramos de edad (edad_5) -----------------------
    edad = _filtra_seleccion(carga_datos.carga_poblacion_edad(), parroquia, anio)
    # Dentro de 'edad' pueden convivir edad_5 y edad_1; para la pirámide usamos
    # los tramos de 5 años (más legibles) si están disponibles.
    if edad is not None and "dimension" in edad.columns:
        edad = edad[edad["dimension"] == "edad_5"]
        if edad.empty:
            edad = None

    if edad is None:
        st.info(
            f"No hay datos de edad por tramos para {parroquia} en {anio}; se "
            "omite el perfil de edad y se conserva el resto de la vista."
        )
    else:
        tramos = _ordena_tramos_edad(list(edad["categoria"].unique()))
        valores_por_tramo = {
            str(fila["categoria"]): pd.to_numeric(fila["valor"], errors="coerce")
            for _, fila in edad.iterrows()
        }
        valores = [valores_por_tramo.get(t) for t in tramos]

        if go is not None:
            figura = go.Figure()
            figura.add_trace(
                go.Bar(
                    y=tramos,
                    x=valores,
                    orientation="h",
                    name="Población",
                    marker_color="#4C78A8",
                )
            )
            figura.update_layout(
                title=f"Población por tramo de edad · {parroquia} · {anio}",
                xaxis_title="Personas",
                yaxis_title="Tramo de edad",
                bargap=0.15,
            )
            st.plotly_chart(figura, use_container_width=True)
        else:
            st.dataframe(
                pd.DataFrame(
                    {"Tramo de edad": tramos, "Población": valores}
                ),
                use_container_width=True,
            )

    # --- Pieza 2: reparto por sexo (HOME/DONA) -----------------------------
    sexo = _filtra_seleccion(carga_datos.carga_poblacion_sexo(), parroquia, anio)
    if sexo is None:
        st.info(
            f"No hay datos de sexo para {parroquia} en {anio}; se omite el "
            "reparto por sexo y se conserva el resto de la vista."
        )
        return

    # Reunir el valor y la fila de gobernanza de HOME y DONA.
    fila_home = sexo[sexo["categoria"] == "HOME"]
    fila_dona = sexo[sexo["categoria"] == "DONA"]
    valor_home = (
        pd.to_numeric(fila_home.iloc[0]["valor"], errors="coerce")
        if not fila_home.empty
        else None
    )
    valor_dona = (
        pd.to_numeric(fila_dona.iloc[0]["valor"], errors="coerce")
        if not fila_dona.empty
        else None
    )

    if go is not None and valor_home is not None and valor_dona is not None:
        figura_sexo = go.Figure()
        # HOME a la izquierda con signo negativo; DONA a la derecha (Req 2.2).
        figura_sexo.add_trace(
            go.Bar(
                y=["Sexo"],
                x=[-int(valor_home)],
                orientation="h",
                name="HOME",
                marker_color="#4C78A8",
                hovertemplate="HOME: %{customdata}<extra></extra>",
                customdata=[int(valor_home)],
            )
        )
        figura_sexo.add_trace(
            go.Bar(
                y=["Sexo"],
                x=[int(valor_dona)],
                orientation="h",
                name="DONA",
                marker_color="#E45756",
                hovertemplate="DONA: %{x}<extra></extra>",
            )
        )
        figura_sexo.update_layout(
            title=f"Reparto por sexo · {parroquia} · {anio}",
            barmode="relative",
            xaxis_title="Personas (HOME a la izquierda, DONA a la derecha)",
        )
        st.plotly_chart(figura_sexo, use_container_width=True)

    # Totales gobernados de HOME y DONA (Req 2.4).
    columna_home, columna_dona = st.columns(2)
    with columna_home:
        if fila_home.empty:
            cifra_gobernada(
                f"Hombres (HOME) · {parroquia} · {anio}",
                None,
                None,
                None,
                id_fuente=_ID_FUENTE_DESGLOSES,
            )
        else:
            f = fila_home.iloc[0]
            cifra_gobernada(
                f"Hombres (HOME) · {parroquia} · {anio}",
                None if valor_home is None or pd.isna(valor_home) else int(valor_home),
                _construye_metadato(f),
                _linaje_de_fila(f),
                id_fuente=_ID_FUENTE_DESGLOSES,
            )
    with columna_dona:
        if fila_dona.empty:
            cifra_gobernada(
                f"Mujeres (DONA) · {parroquia} · {anio}",
                None,
                None,
                None,
                id_fuente=_ID_FUENTE_DESGLOSES,
            )
        else:
            f = fila_dona.iloc[0]
            cifra_gobernada(
                f"Mujeres (DONA) · {parroquia} · {anio}",
                None if valor_dona is None or pd.isna(valor_dona) else int(valor_dona),
                _construye_metadato(f),
                _linaje_de_fila(f),
                id_fuente=_ID_FUENTE_DESGLOSES,
            )


# --- Desglose: composición por nacionalidad --------------------------------


def _composicion_nacionalidad(parroquia: str, anio: int) -> None:
    """Renderiza la composición por nacionalidad de la selección vigente.

    Muestra las ``_TOP_N_NACIONALIDAD`` nacionalidades con más población y
    agrega el resto (incluida la categoría residual "ALTRES NACIONALITATS" del
    crudo) en una categoría "Otros", sin fabricar ni descartar población
    (Req 2.1). La nacionalidad más poblada se presenta como cifra gobernada
    OBSERVADO con su Detalle_Gobernanza (Req 2.4).

    Si el desglose falta o no tiene filas para la selección, muestra un mensaje
    de ausencia para este desglose y conserva el resto de la vista (Req 2.6).

    Args:
        parroquia: parròquia seleccionada.
        anio: año seleccionado.

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.subheader("Composición por nacionalidad")

    nac = _filtra_seleccion(
        carga_datos.carga_poblacion_nacionalidad(), parroquia, anio
    )
    if nac is None:
        st.info(
            f"No hay datos de nacionalidad para {parroquia} en {anio}; se omite "
            "este desglose y se conserva el resto de la vista."
        )
        return

    # Valor numérico por categoría, descartando celdas no numéricas.
    nac = nac.copy()
    nac["valor_num"] = pd.to_numeric(nac["valor"], errors="coerce")
    nac = nac.dropna(subset=["valor_num"])
    if nac.empty:
        st.info(
            f"No hay cifras de nacionalidad legibles para {parroquia} en "
            f"{anio}; se omite este desglose y se conserva el resto de la vista."
        )
        return

    # Separar la categoría residual del crudo ("ALTRES NACIONALITATS") para
    # sumarla a "Otros" y no tratarla como una nacionalidad individual.
    residuo_crudo = nac[nac["categoria"] == _CATEGORIA_ALTRES]["valor_num"].sum()
    individuales = nac[nac["categoria"] != _CATEGORIA_ALTRES].sort_values(
        "valor_num", ascending=False
    )

    top = individuales.head(_TOP_N_NACIONALIDAD)
    resto = individuales.iloc[_TOP_N_NACIONALIDAD:]["valor_num"].sum()
    otros = float(resto) + float(residuo_crudo)

    etiquetas = [str(c) for c in top["categoria"].tolist()]
    valores = [int(v) for v in top["valor_num"].tolist()]
    if otros > 0:
        etiquetas.append(_ETIQUETA_OTROS)
        valores.append(int(round(otros)))

    go = _plotly()
    if go is not None:
        figura = go.Figure(
            go.Bar(
                x=valores,
                y=etiquetas,
                orientation="h",
                marker_color="#54A24B",
            )
        )
        figura.update_layout(
            title=f"Nacionalidades · {parroquia} · {anio}",
            xaxis_title="Personas",
            yaxis_title="Nacionalidad",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(figura, use_container_width=True)
    else:
        st.dataframe(
            pd.DataFrame({"Nacionalidad": etiquetas, "Población": valores}),
            use_container_width=True,
        )

    # Cifra gobernada de la nacionalidad mayoritaria (Req 2.4).
    fila_top = top.iloc[0]
    cifra_gobernada(
        f"Nacionalidad mayoritaria ({fila_top['categoria']}) · {parroquia} · {anio}",
        int(fila_top["valor_num"]),
        _construye_metadato(fila_top),
        _linaje_de_fila(fila_top),
        id_fuente=_ID_FUENTE_DESGLOSES,
    )


# --- Desglose: distribución por lugar de nacimiento ------------------------


def _distribucion_lugar_nacimiento(parroquia: str, anio: int) -> None:
    """Renderiza la distribución por lugar de nacimiento de la selección.

    Muestra la población según el lugar de nacimiento (Andorra, Espanya,
    Portugal, França, Altres) como gráfico de la selección vigente, con la
    categoría mayoritaria presentada como cifra gobernada OBSERVADO y su
    Detalle_Gobernanza (Req 2.1, 2.4).

    Si el desglose falta o no tiene filas para la selección, muestra un mensaje
    de ausencia para este desglose y conserva el resto de la vista (Req 2.6).

    Args:
        parroquia: parròquia seleccionada.
        anio: año seleccionado.

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.subheader("Distribución por lugar de nacimiento")

    lugar = _filtra_seleccion(
        carga_datos.carga_poblacion_lugar_nacimiento(), parroquia, anio
    )
    if lugar is None:
        st.info(
            f"No hay datos de lugar de nacimiento para {parroquia} en {anio}; "
            "se omite este desglose y se conserva el resto de la vista."
        )
        return

    lugar = lugar.copy()
    lugar["valor_num"] = pd.to_numeric(lugar["valor"], errors="coerce")
    lugar = lugar.dropna(subset=["valor_num"]).sort_values(
        "valor_num", ascending=False
    )
    if lugar.empty:
        st.info(
            f"No hay cifras de lugar de nacimiento legibles para {parroquia} en "
            f"{anio}; se omite este desglose y se conserva el resto de la vista."
        )
        return

    etiquetas = [str(c) for c in lugar["categoria"].tolist()]
    valores = [int(v) for v in lugar["valor_num"].tolist()]

    go = _plotly()
    if go is not None:
        figura = go.Figure(
            go.Bar(
                x=etiquetas,
                y=valores,
                marker_color="#B279A2",
            )
        )
        figura.update_layout(
            title=f"Lugar de nacimiento · {parroquia} · {anio}",
            xaxis_title="Lugar de nacimiento",
            yaxis_title="Personas",
        )
        st.plotly_chart(figura, use_container_width=True)
    else:
        st.dataframe(
            pd.DataFrame({"Lugar de nacimiento": etiquetas, "Población": valores}),
            use_container_width=True,
        )

    # Cifra gobernada del lugar de nacimiento mayoritario (Req 2.4).
    fila_top = lugar.iloc[0]
    cifra_gobernada(
        f"Lugar de nacimiento mayoritario ({fila_top['categoria']}) · {parroquia} · {anio}",
        int(fila_top["valor_num"]),
        _construye_metadato(fila_top),
        _linaje_de_fila(fila_top),
        id_fuente=_ID_FUENTE_DESGLOSES,
    )


# --- Bloque de población total (conservado de la Parte 2) ------------------


def _bloque_poblacion_total(anio: int) -> None:
    """Renderiza la población total por parròquia del año seleccionado.

    Conserva el comportamiento de la Parte 2: muestra la población de cada
    parròquia para el año elegido mediante ``cifra_gobernada`` con linaje
    OBSERVADO. Si la tabla de población total no está disponible, muestra un
    mensaje de ausencia para este bloque y conserva el resto de la vista.

    Args:
        anio: año seleccionado en el selector común.

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.subheader(f"Población por parròquia · {anio}")

    df = carga_datos.carga_poblacion()
    if df is None or df.empty:
        st.warning(
            "Población total por parròquia: Dato no disponible. No se pudieron "
            "cargar los datos procesados de población."
        )
        print(
            "[poblacion] Población total no disponible: carga_poblacion() "
            "devolvió None o un DataFrame vacío; se conserva el resto de la vista."
        )
        return

    df_anio = df[pd.to_numeric(df["anio"], errors="coerce") == anio]
    if df_anio.empty:
        st.warning(
            f"Población total por parròquia: no hay cifras para {anio}."
        )
        return

    # Presentar las 7 parròquies en columnas para una lectura compacta.
    columnas = st.columns(2)
    for i, fila_tupla in enumerate(df_anio.itertuples(index=False)):
        fila = pd.Series(fila_tupla._asdict())
        poblacion = pd.to_numeric(fila.get("poblacion"), errors="coerce")
        with columnas[i % len(columnas)]:
            cifra_gobernada(
                etiqueta=str(fila["parroquia"]),
                valor=None if pd.isna(poblacion) else int(poblacion),
                metadato=_construye_metadato(fila),
                linaje=_linaje_de_fila(fila),
                id_fuente="F01",
            )


# --- Bloque social: umbrales de pobreza y tasa de fecundidad ---------------


def _id_fuente_inventario(nombre_archivo: str, id_por_defecto: str) -> str:
    """Resuelve el ID_Fuente de un archivo desde el Inventario_Fuentes.

    Busca en el inventario la fila cuyo ``nombre`` coincide con
    ``nombre_archivo`` y devuelve su ``id_fuente``. Si el inventario no está
    disponible, le faltan columnas o no hay coincidencia, devuelve
    ``id_por_defecto`` para seguir ofreciendo el Detalle_Gobernanza a un clic
    sin romper la vista.

    Args:
        nombre_archivo: nombre del CSV tal como figura en la columna ``nombre``
            del inventario (p. ej. ``"umbrales_pobreza.csv"``).
        id_por_defecto: ID_Fuente de respaldo (p. ej. ``"F11"``).

    Returns:
        El ID_Fuente resuelto del inventario, o ``id_por_defecto``.
    """
    inventario = carga_datos.carga_inventario()
    if (
        inventario is None
        or "nombre" not in inventario.columns
        or "id_fuente" not in inventario.columns
    ):
        return id_por_defecto

    coincidencias = inventario[inventario["nombre"] == nombre_archivo]
    if coincidencias.empty:
        return id_por_defecto

    valor = coincidencias.iloc[0]["id_fuente"]
    if valor is None or pd.isna(valor):
        return id_por_defecto
    texto = str(valor).strip()
    return texto or id_por_defecto


def _fila_anio_mas_reciente(grupo: "pd.DataFrame") -> "pd.Series":
    """Devuelve la fila del año más reciente de un grupo de un indicador.

    Ordena por ``anio`` numérico ascendente y devuelve la última fila (el año
    más alto). Se asume que ``grupo`` no está vacío.

    Args:
        grupo: filas de un mismo indicador, con la columna ``anio``.

    Returns:
        La fila (``pd.Series``) correspondiente al año más reciente.
    """
    grupo = grupo.copy()
    grupo["_anio_num"] = pd.to_numeric(grupo["anio"], errors="coerce")
    grupo = grupo.sort_values("_anio_num")
    return grupo.iloc[-1]


def _bloque_social() -> None:
    """Renderiza el bloque de indicadores sociales reclasificados.

    Muestra los umbrales de pobreza (``umbrales_pobreza.csv``) y la tasa de
    fecundidad (``tasa_fecundidad.csv``) como Indicador_Social_Reclasificado
    OBSERVADO, cada cifra mediante ``cifra_gobernada`` con su Metadato_Cifra y
    su Detalle_Gobernanza a un clic (Req 3.5). Para cada indicador se presenta
    la cifra del año más reciente disponible.

    Si un indicador tiene menos de 1 registro (archivo ausente/ilegible o tabla
    vacía), muestra un mensaje de ausencia en español para ESE indicador, sin
    inventar datos y conservando el resto del bloque y de la vista (Req 3.5).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.subheader("Indicadores sociales")
    st.caption(
        "Umbrales de pobreza y tasa de fecundidad de Andorra, reclasificados "
        "según su contenido real a partir de los crudos oficiales (linaje "
        "OBSERVADO)."
    )

    # --- Umbrales de pobreza ----------------------------------------------
    st.markdown("**Umbrales de pobreza (€ anuales)**")
    umbrales = carga_datos.carga_umbrales_pobreza()
    if umbrales is None or umbrales.empty:
        st.info(
            "Umbrales de pobreza: no hay datos disponibles; se omite este "
            "indicador y se conserva el resto de la vista."
        )
    else:
        id_umbrales = _id_fuente_inventario(_ARCHIVO_UMBRALES, _ID_FUENTE_UMBRALES)
        umbrales = umbrales.copy()
        umbrales["_valor_num"] = pd.to_numeric(
            umbrales["valor_eur"], errors="coerce"
        )
        # Una cifra por cada umbral (indicador), tomando su año más reciente.
        indicadores = sorted(str(i) for i in umbrales["indicador"].dropna().unique())
        columnas = st.columns(len(indicadores)) if indicadores else [st]
        for columna, nombre_umbral in zip(columnas, indicadores):
            grupo = umbrales[umbrales["indicador"] == nombre_umbral]
            fila = _fila_anio_mas_reciente(grupo)
            valor = fila["_valor_num"]
            anio = pd.to_numeric(fila.get("anio"), errors="coerce")
            etiqueta_anio = "" if pd.isna(anio) else f" · {int(anio)}"
            with columna:
                cifra_gobernada(
                    f"{nombre_umbral}{etiqueta_anio}",
                    None if pd.isna(valor) else f"{float(valor):,.2f} €",
                    _construye_metadato(fila),
                    _linaje_de_fila(fila),
                    id_fuente=id_umbrales,
                )

    # --- Tasa de fecundidad -----------------------------------------------
    st.markdown("**Tasa de fecundidad**")
    fecundidad = carga_datos.carga_tasa_fecundidad()
    if fecundidad is None or fecundidad.empty:
        st.info(
            "Tasa de fecundidad: no hay datos disponibles; se omite este "
            "indicador y se conserva el resto de la vista."
        )
        return

    id_fecundidad = _id_fuente_inventario(_ARCHIVO_FECUNDIDAD, _ID_FUENTE_FECUNDIDAD)
    fecundidad = fecundidad.copy()
    fecundidad["_valor_num"] = pd.to_numeric(fecundidad["valor"], errors="coerce")
    fila = _fila_anio_mas_reciente(fecundidad)
    valor = fila["_valor_num"]
    anio = pd.to_numeric(fila.get("anio"), errors="coerce")
    etiqueta_anio = "" if pd.isna(anio) else f" · {int(anio)}"
    nombre_indicador = str(fila.get("indicador", "Tasa de fecundidad"))
    cifra_gobernada(
        f"{nombre_indicador}{etiqueta_anio}",
        None if pd.isna(valor) else round(float(valor), 2),
        _construye_metadato(fila),
        _linaje_de_fila(fila),
        id_fuente=id_fecundidad,
    )


def render() -> None:
    """Renderiza la Vista Gente/Población enriquecida.

    Ofrece un selector común de parròquia y año (rango 2020–2025, por defecto el
    más reciente); al cambiar la selección, todas las visualizaciones se
    actualizan a la selección vigente (Req 2.3). Conserva el bloque de población
    total por parròquia de la Parte 2 y añade los tres desgloses gobernados:
    pirámide por edad y sexo, composición por nacionalidad y distribución por
    lugar de nacimiento (Req 2.1, 2.2, 2.4). Si un desglose falta o no tiene
    filas para la selección, muestra un mensaje de ausencia para ESE desglose y
    conserva el resto de la vista (Req 2.6).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.header("Gente / Población")
    st.write(
        "Población por parròquia de Andorra y sus desgloses por edad, sexo, "
        "nacionalidad y lugar de nacimiento, a partir de los datos oficiales "
        "del Departament d'Estadística (linaje OBSERVADO)."
    )

    # Determinar los años disponibles a partir de los desgloses; si no hay
    # desgloses, recurrir a la tabla de población total para poblar el selector.
    desgloses = carga_datos.carga_poblacion_desgloses()
    df_para_anios = desgloses if desgloses is not None else carga_datos.carga_poblacion()

    if df_para_anios is None or df_para_anios.empty or "anio" not in df_para_anios.columns:
        st.warning(
            "Datos de población no disponibles: no se pudieron cargar ni los "
            "desgloses ni la población total por parròquia."
        )
        print(
            "[poblacion] Datos de población no disponibles: ni los desgloses ni "
            "la población total se pudieron cargar; no se muestran cifras."
        )
        return

    anios = _anios_disponibles(df_para_anios)
    if not anios:
        st.warning(
            "Datos de población no disponibles: no hay años en el rango "
            f"{ANIO_MIN}–{ANIO_MAX} en los datos procesados."
        )
        return

    # Parròquies disponibles para el selector: las presentes en los desgloses,
    # o las canónicas de la población total como respaldo.
    if desgloses is not None and "parroquia" in desgloses.columns:
        parroquias = sorted(str(p) for p in desgloses["parroquia"].dropna().unique())
    else:
        pob = carga_datos.carga_poblacion()
        parroquias = (
            sorted(str(p) for p in pob["parroquia"].dropna().unique())
            if pob is not None and "parroquia" in pob.columns
            else []
        )

    # --- Selector común de parròquia y año (Req 2.3) -----------------------
    anio_reciente = max(anios)
    columna_parroquia, columna_anio = st.columns(2)
    with columna_anio:
        anio_sel = st.selectbox(
            "Año",
            options=anios,
            index=anios.index(anio_reciente),
            help="Al cambiar el año, todas las visualizaciones se actualizan.",
        )
    with columna_parroquia:
        parroquia_sel = (
            st.selectbox(
                "Parròquia",
                options=parroquias,
                help="Al cambiar la parròquia, los desgloses se actualizan.",
            )
            if parroquias
            else None
        )

    # --- Bloque de población total (Parte 2) -------------------------------
    _bloque_poblacion_total(anio_sel)

    st.divider()

    # --- Bloque de indicadores sociales reclasificados (Parte 3, Req 3.5) --
    _bloque_social()

    st.divider()

    # --- Desgloses de población (Parte 3) ----------------------------------
    if parroquia_sel is None:
        st.info(
            "No hay parròquies disponibles en los desgloses; no se muestran los "
            "gráficos por parròquia."
        )
        return

    st.subheader(f"Desgloses de {parroquia_sel} · {anio_sel}")

    _piramide_edad_sexo(parroquia_sel, anio_sel)
    st.divider()
    _composicion_nacionalidad(parroquia_sel, anio_sel)
    st.divider()
    _distribucion_lugar_nacimiento(parroquia_sel, anio_sel)
