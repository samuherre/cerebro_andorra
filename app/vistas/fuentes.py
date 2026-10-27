"""Vista_Fuentes de la App_Streamlit de Cerebro Andorra.

Esta vista materializa el Requisito 8 ("Vista Fuentes y Método"): presenta el
Inventario_Fuentes como una tabla auditable con, por cada dataset, su nombre,
su fuente, su Etiqueta_Linaje y su Estado_Dataset, y muestra el motivo cuando
un dataset está en estado ``excluido`` o ``caído`` (Req 8.1, 8.2, 8.3).

El inventario se obtiene de forma cacheada mediante
``carga_datos.carga_inventario()``, que devuelve ``None`` cuando el archivo no
existe o no puede leerse. En ese caso la vista muestra un mensaje que indica la
ausencia del inventario en lugar de la tabla, sin interrumpir la carga de la
app (Req 8.4).

Como la app se lanza desde la raíz del repositorio
(``streamlit run app/streamlit_app.py``) y este archivo vive en ``app/vistas/``,
se añade la carpeta ``app/`` al ``sys.path`` (parents[1]) para poder importar el
módulo ``carga_datos`` sin convertir ``app/`` en un paquete.

Textos de interfaz y mensajes de consola en español, coherentes con el resto
del proyecto.
"""

import sys
from pathlib import Path

import streamlit as st

# --- Resolución de la ruta a app/ y reutilización de la carga de datos ------
# parents[1] sube desde app/vistas/fuentes.py hasta la carpeta app/; desde ahí
# se puede importar carga_datos sin convertir app/ en un paquete.
_DIR_APP = Path(__file__).resolve().parents[1]
if str(_DIR_APP) not in sys.path:
    sys.path.append(str(_DIR_APP))

import carga_datos  # noqa: E402 - import tras ajustar sys.path

# Columnas del Inventario_Fuentes que la vista muestra, en orden de lectura.
# El motivo se incluye porque es significativo para los estados excluido y caído
# (Req 8.3); en los demás estados queda vacío.
_COLUMNAS_INVENTARIO = ["nombre", "fuente", "linaje", "estado", "motivo"]

# Rótulos legibles para el encabezado de la tabla mostrada al usuario.
_ETIQUETAS_COLUMNAS = {
    "nombre": "Nombre",
    "fuente": "Fuente",
    "linaje": "Linaje",
    "estado": "Estado",
    "motivo": "Motivo",
}


def render() -> None:
    """Renderiza la Vista_Fuentes con el Inventario_Fuentes como tabla.

    Carga el inventario mediante ``carga_datos.carga_inventario()``. Si no está
    disponible (archivo inexistente o ilegible), muestra un mensaje de ausencia
    en lugar de la tabla (Req 8.4). En caso contrario, presenta el inventario
    como una tabla con nombre, fuente, linaje, estado y motivo por dataset; el
    motivo es la columna significativa para los estados ``excluido`` y ``caído``
    (Req 8.1, 8.2, 8.3).

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    st.header("Fuentes y Método")
    st.write(
        "Inventario de los datasets del proyecto con su linaje de gobernanza y "
        "su estado de integración. Los datasets excluidos o caídos indican su "
        "motivo."
    )

    inventario = carga_datos.carga_inventario()

    # Degradación segura: sin inventario no se muestra tabla, sólo el aviso de
    # ausencia, conservando el resto de la app operativa (Req 8.4).
    if inventario is None:
        st.warning(
            "Inventario no disponible: no se encontró el Inventario_Fuentes o "
            "no pudo leerse."
        )
        return

    # Seleccionar sólo las columnas esperadas que estén presentes, para ser
    # tolerantes ante variaciones del archivo sin romper la vista.
    columnas_presentes = [
        columna for columna in _COLUMNAS_INVENTARIO if columna in inventario.columns
    ]
    tabla = inventario[columnas_presentes].rename(columns=_ETIQUETAS_COLUMNAS)

    # Mostrar el inventario como tabla ocupando el ancho del contenedor. Se usa
    # st.dataframe por su interactividad (orden por columna, búsqueda) sobre un
    # inventario de pocas filas (Req 8.1, 8.2, 8.3).
    st.dataframe(tabla, use_container_width=True, hide_index=True)
