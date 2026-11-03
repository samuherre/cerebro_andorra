"""Punto de entrada de la App_Streamlit de Cerebro Andorra.

Este módulo es el que se lanza desde la raíz del repositorio con::

    streamlit run app/streamlit_app.py

Define la navegación de la aplicación mediante una barra lateral que enruta a
las vistas del proyecto.
"""

import hmac
import importlib
import os
import sys
from pathlib import Path

import streamlit as st

# --- Resolución de rutas para que los imports resuelvan sin depender del CWD -
_DIR_APP = Path(__file__).resolve().parent
_DIR_VISTAS = _DIR_APP / "vistas"
for _ruta in (_DIR_APP, _DIR_VISTAS):
    if str(_ruta) not in sys.path:
        sys.path.append(str(_ruta))

import carga_datos  # noqa: E402
import componentes  # noqa: E402
import estilos  # noqa: E402

# En Streamlit Community Cloud, tras un git push sin reinicio del contenedor,
# sys.modules conserva la versión anterior de los módulos auxiliares. Recargar
# explícitamente carga_datos y las vistas evita AttributeError por funciones
# añadidas recientemente.
importlib.reload(carga_datos)
importlib.reload(componentes)
importlib.reload(estilos)

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

for _mod_vista in (
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
):
    importlib.reload(_mod_vista)

# Definición de las vistas como páginas de navegación (título, icono, función
# de render y url_path único).
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
# variable de entorno. La clave NUNCA se versiona.
_NOMBRE_CLAVE_COMPUERTA = "CLAVE_ACCESO"


def _clave_compuerta_configurada() -> str | None:
    """Devuelve la clave de la Compuerta_Acceso si está configurada, o None."""
    try:
        valor = st.secrets.get(_NOMBRE_CLAVE_COMPUERTA)
    except Exception:  # noqa: BLE001 - ausencia de secrets no debe romper el arranque
        valor = None

    if not valor:
        valor = os.environ.get(_NOMBRE_CLAVE_COMPUERTA)

    if valor and str(valor).strip():
        return str(valor)
    return None


def compuerta_acceso() -> bool:
    """Compuerta_Acceso OPCIONAL comparada en el servidor."""
    clave_esperada = _clave_compuerta_configurada()

    if clave_esperada is None:
        return True

    if st.session_state.get("_compuerta_ok"):
        return True

    st.title("Cerebro Andorra")
    st.info("Acceso restringido. Introduce la clave para continuar.")
    introducida = st.text_input("Clave de acceso", type="password")

    if not introducida:
        st.stop()

    if hmac.compare_digest(str(introducida), clave_esperada):
        st.session_state["_compuerta_ok"] = True
        return True

    st.error("Clave incorrecta. Inténtalo de nuevo.")
    st.stop()
    return False


def main() -> None:
    """Configura la página y enruta a la vista seleccionada en la barra lateral."""
    st.set_page_config(
        page_title="Cerebro Andorra",
        page_icon="🇦🇩",
        layout="wide",
    )

    estilos.aplica_estilo_global()

    if not compuerta_acceso():
        return

    st.sidebar.markdown("### 🇦🇩 Cerebro Andorra")
    st.sidebar.caption(
        "Cerebro de datos del Principat d'Andorra. Toda cifra se muestra con su "
        "fuente, vigencia, fecha de prueba y etiqueta de linaje."
    )

    paginas = [
        st.Page(funcion, title=titulo, icon=icono, url_path=ruta, default=(indice == 0))
        for indice, (titulo, icono, funcion, ruta) in enumerate(_PAGINAS)
    ]
    navegacion = st.navigation(paginas)

    st.sidebar.divider()
    st.sidebar.caption(_EQUIPO)

    navegacion.run()


if __name__ == "__main__":
    main()
