"""Punto de entrada de la App_Streamlit de Cerebro Andorra.

Este módulo es el que se lanza desde la raíz del repositorio con::

    streamlit run app/streamlit_app.py

Define la navegación de la aplicación mediante una barra lateral que enruta a
las cuatro vistas del proyecto:

1. Panorama — resumen del país con las cifras clave.
2. Gente / Población — población por parròquia.
3. Vivienda — precios de venta y alquiler (linaje PROXY).
4. Fuentes y Método — inventario auditable de fuentes y su estado.

Cada vista vive en ``app/vistas/`` y expone una función ``render() -> None`` que
pinta su contenido. La carga de datos (``carga_datos``) y los componentes de UI
(``componentes``) los resuelven las propias vistas, que añaden ``app/`` al
``sys.path``; aquí se añade también ``app/`` y ``app/vistas/`` para que los
módulos de vista y sus imports hermanos resuelvan con independencia del
directorio de trabajo desde el que se lance la app.

Incluye además una Compuerta_Acceso OPCIONAL (``compuerta_acceso``): si existe
una clave configurada en el servidor (``st.secrets`` o la variable de entorno
``CLAVE_ACCESO``) se pide esa clave antes de mostrar la app y se compara en el
servidor; si no hay clave configurada, la compuerta queda desactivada y la app
arranca con normalidad. La clave nunca se versiona.

Textos de interfaz y mensajes de consola en español, coherentes con el resto
del proyecto.
"""

import hmac
import os
import sys
from pathlib import Path

import streamlit as st

# --- Resolución de rutas para que los imports resuelvan sin depender del CWD -
# _DIR_APP apunta a app/ (carpeta de este archivo) y _DIR_VISTAS a app/vistas/.
# Añadir ambas al sys.path permite importar los módulos de vista (que a su vez
# importan carga_datos y componentes desde app/) con independencia del
# directorio de trabajo desde el que se ejecute `streamlit run`.
_DIR_APP = Path(__file__).resolve().parent
_DIR_VISTAS = _DIR_APP / "vistas"
for _ruta in (_DIR_APP, _DIR_VISTAS):
    if str(_ruta) not in sys.path:
        sys.path.append(str(_ruta))

import estilos  # noqa: E402
from vistas import (  # noqa: E402
    economia,
    fuentes,
    mapa,
    panorama,
    poblacion,
    preguntas,
    salud_educacion,
    territorio_pueblos,
    transporte_ambiente,
    vivienda,
)

# Definición de las vistas como páginas de navegación (título, icono y función
# de render). El orden define el orden del menú lateral. La antigua pestaña
# "Preguntas (Entrega 1)" pasa a llamarse "Andorra en preguntas", un rótulo
# orientado al usuario final en lugar de la jerga interna del curso.
# Cada entrada es (título, icono, función de render, url_path). El ``url_path``
# es OBLIGATORIO y único: como todas las vistas exponen una función llamada
# ``render``, Streamlit no puede inferir un pathname de URL distinto para cada
# una (todas quedarían como "render" y colisionarían), así que se fija aquí uno
# explícito por página.
_PAGINAS = [
    ("Panorama", ":material/dashboard:", panorama.render, "panorama"),
    ("Población", ":material/groups:", poblacion.render, "poblacion"),
    ("Territorio y pueblos", ":material/location_city:", territorio_pueblos.render, "territorio"),
    ("Vivienda", ":material/apartment:", vivienda.render, "vivienda"),
    ("Economía", ":material/trending_up:", economia.render, "economia"),
    ("Salud y educación", ":material/health_and_safety:", salud_educacion.render, "salud"),
    ("Transporte y ambiente", ":material/directions_bus:", transporte_ambiente.render, "transporte"),
    ("Mapa", ":material/map:", mapa.render, "mapa"),
    ("Andorra en preguntas", ":material/help:", preguntas.render, "preguntas"),
    ("Fuentes y método", ":material/fact_check:", fuentes.render, "fuentes"),
]

# Nombres del grupo que se muestran de forma visible en la barra lateral del
# despliegue publico.
_EQUIPO = "Equipo: Daniel Zapata, Samuel Herrera, Tomas Londono"

# Nombre de la clave de la Compuerta_Acceso tanto en st.secrets como en la
# variable de entorno. La clave NUNCA se versiona (ver .gitignore /
# .streamlit/secrets.toml); se compara siempre en el servidor.
_NOMBRE_CLAVE_COMPUERTA = "CLAVE_ACCESO"


def _clave_compuerta_configurada() -> str | None:
    """Devuelve la clave de la Compuerta_Acceso si está configurada, o None.

    La compuerta es OPCIONAL: solo se activa si existe una clave en el servidor,
    ya sea en ``st.secrets`` o en una variable de entorno. Si no hay clave
    configurada, devuelve ``None`` y la app funciona con normalidad (compuerta
    desactivada por defecto). La clave nunca se almacena en el repositorio.

    Returns:
        La clave configurada (texto no vacío) o ``None`` si la compuerta no está
        activada.
    """
    # 1) st.secrets: se consulta de forma defensiva porque, si no existe el
    #    archivo .streamlit/secrets.toml ni secrets en el despliegue, el acceso
    #    puede lanzar una excepción. En ese caso simplemente no hay clave.
    try:
        valor = st.secrets.get(_NOMBRE_CLAVE_COMPUERTA)
    except Exception:  # noqa: BLE001 - ausencia de secrets no debe romper el arranque
        valor = None

    # 2) Variable de entorno como alternativa (útil en local).
    if not valor:
        valor = os.environ.get(_NOMBRE_CLAVE_COMPUERTA)

    if valor and str(valor).strip():
        return str(valor)
    return None


def compuerta_acceso() -> bool:
    """Compuerta_Acceso OPCIONAL comparada en el servidor.

    Si no hay clave configurada en el servidor (``st.secrets`` o variable de
    entorno), la compuerta está desactivada y la función devuelve ``True`` sin
    pedir nada: la app arranca con normalidad.

    Si hay una clave configurada, pide al usuario que la introduzca y la compara
    en el servidor usando una comparación de tiempo constante
    (``hmac.compare_digest``). La clave introducida no se almacena; solo se
    guarda en la sesión el resultado booleano de la verificación.

    Returns:
        ``True`` si la compuerta está desactivada o la clave es correcta;
        ``False`` si la compuerta está activa y la clave aún no se ha validado.
    """
    clave_esperada = _clave_compuerta_configurada()

    # Compuerta desactivada por defecto: sin clave configurada no se pide nada.
    if clave_esperada is None:
        return True

    # Ya validada en esta sesión: no volver a pedirla.
    if st.session_state.get("_compuerta_ok"):
        return True

    st.title("Cerebro Andorra")
    st.info("Acceso restringido. Introduce la clave para continuar.")
    introducida = st.text_input("Clave de acceso", type="password")

    if not introducida:
        st.stop()

    # Comparación en el servidor, de tiempo constante.
    if hmac.compare_digest(str(introducida), clave_esperada):
        st.session_state["_compuerta_ok"] = True
        return True

    st.error("Clave incorrecta. Inténtalo de nuevo.")
    st.stop()
    return False


def main() -> None:
    """Configura la página y enruta a la vista seleccionada en la barra lateral.

    Establece la configuración global de la página, dibuja la barra lateral con
    el selector de vistas y, según la opción elegida, invoca la función
    ``render()`` de la vista correspondiente.

    Returns:
        None. El efecto es la representación de la app en la interfaz de
        Streamlit.
    """
    st.set_page_config(
        page_title="Cerebro Andorra",
        page_icon="🇦🇩",
        layout="wide",
    )

    # Identidad visual coherente en todas las vistas (CSS de marca).
    estilos.aplica_estilo_global()

    # Compuerta_Acceso OPCIONAL: solo pide clave si hay una configurada en el
    # servidor (st.secrets / variable de entorno). Si no, no interrumpe el
    # arranque y la app funciona con normalidad.
    if not compuerta_acceso():
        return

    # Cabecera de marca en la barra lateral.
    st.sidebar.markdown("### 🇦🇩 Cerebro Andorra")
    st.sidebar.caption(
        "Cerebro de datos del Principat d'Andorra. Toda cifra se muestra con su "
        "fuente, vigencia, fecha de prueba y etiqueta de linaje."
    )

    # Navegación moderna con iconos (st.navigation / st.Page). Cada página
    # envuelve la función render() de su vista conservando título e icono.
    # No se fija `position`: su valor por defecto ya coloca la navegación en la
    # barra lateral y, además, el conjunto de valores admitidos por ese
    # parámetro ha cambiado entre versiones de Streamlit ("sidebar" dejó de ser
    # válido en versiones recientes), así que omitirlo hace la app robusta
    # frente a la versión que resuelva el despliegue (Streamlit Cloud).
    paginas = [
        st.Page(funcion, title=titulo, icon=icono, url_path=ruta, default=(indice == 0))
        for indice, (titulo, icono, funcion, ruta) in enumerate(_PAGINAS)
    ]
    navegacion = st.navigation(paginas)

    # Nombres del grupo visibles en la barra lateral (requisito de la entrega).
    st.sidebar.divider()
    st.sidebar.caption(_EQUIPO)

    # Ejecuta la página seleccionada.
    navegacion.run()


if __name__ == "__main__":
    main()
