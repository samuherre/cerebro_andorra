"""Punto de entrada de la App_Streamlit de Cerebro Andorra.

Este módulo es el que se lanza desde la raíz del repositorio con::

    streamlit run app/streamlit_app.py

Define la navegación de la aplicación mediante una barra lateral que enruta a
las cuatro vistas del proyecto (Req 5.1, 6.1, 7.1, 8.1):

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
arranca con normalidad. La clave nunca se versiona (Req 8.7, 8.8).

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

from vistas import (  # noqa: E402
    economia,
    fuentes,
    mapa,
    panorama,
    poblacion,
    preguntas,
    vivienda,
)

# Mapa de navegación: rótulo de la barra lateral -> función render() de la vista
# correspondiente. El orden define el orden de las opciones en el menú.
# Primero las vistas heredadas de la v1 y a continuación las nuevas de la Parte 2
# (Mapa, Preguntas y Economía), conservando un orden lógico (Req 8.3).
_VISTAS = {
    "Panorama": panorama.render,
    "Gente / Población": poblacion.render,
    "Vivienda": vivienda.render,
    "Fuentes y Método": fuentes.render,
    "Mapa": mapa.render,
    "Preguntas (Entrega 1)": preguntas.render,
    "Economía": economia.render,
}

# Nombres del grupo que se muestran de forma visible en la barra lateral del
# Despliegue_Publico (Req 8.3). TODO: completar con los nombres reales de los
# integrantes del grupo antes de publicar.
_EQUIPO = "Equipo: [Nombres del grupo]"

# Nombre de la clave de la Compuerta_Acceso tanto en st.secrets como en la
# variable de entorno. La clave NUNCA se versiona (ver .gitignore /
# .streamlit/secrets.toml); se compara siempre en el servidor (Req 8.7, 8.8).
_NOMBRE_CLAVE_COMPUERTA = "CLAVE_ACCESO"


def _clave_compuerta_configurada() -> str | None:
    """Devuelve la clave de la Compuerta_Acceso si está configurada, o None.

    La compuerta es OPCIONAL: solo se activa si existe una clave en el servidor,
    ya sea en ``st.secrets`` o en una variable de entorno. Si no hay clave
    configurada, devuelve ``None`` y la app funciona con normalidad (compuerta
    desactivada por defecto). La clave nunca se almacena en el repositorio
    (Req 8.7, 8.8).

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
    """Compuerta_Acceso OPCIONAL comparada en el servidor (Req 8.7, 8.8).

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
    ``render()`` de la vista correspondiente (Req 5.1, 6.1, 7.1, 8.1).

    Returns:
        None. El efecto es la representación de la app en la interfaz de
        Streamlit.
    """
    st.set_page_config(
        page_title="Cerebro Andorra",
        page_icon="🇦🇩",
        layout="wide",
    )

    # Compuerta_Acceso OPCIONAL: solo pide clave si hay una configurada en el
    # servidor (st.secrets / variable de entorno). Si no, no interrumpe el
    # arranque y la app funciona con normalidad (Req 8.7, 8.8).
    if not compuerta_acceso():
        return

    st.sidebar.title("Cerebro Andorra")
    st.sidebar.write(
        "Cerebro de datos del Principat d'Andorra. Toda cifra se muestra con su "
        "fuente, vigencia, fecha de prueba y etiqueta de linaje."
    )

    seleccion = st.sidebar.radio(
        "Vistas",
        options=list(_VISTAS.keys()),
        index=0,
    )

    # Nombres del grupo visibles en la barra lateral (Req 8.3).
    st.sidebar.caption(_EQUIPO)

    # Enrutar: invocar el render() de la vista elegida.
    _VISTAS[seleccion]()


if __name__ == "__main__":
    main()
