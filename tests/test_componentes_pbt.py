"""Tests de propiedad (Hypothesis) para el componente de UI cifra_gobernada.

Verifica el principio rector del proyecto —"0 cifras sin fuente, sin vigencia y
sin fecha de prueba"— a nivel de renderizado: toda cifra que llega bien
gobernada al componente ``app/componentes.py:cifra_gobernada`` debe salir
mostrando su fuente, su vigencia, su fecha de prueba y una etiqueta de linaje
válida (OBSERVADO/ESTIMADO/PROXY).

Como ``cifra_gobernada`` se apoya en Streamlit (st.metric, st.caption,
st.markdown, st.warning) y no se dispone de un servidor de Streamlit en las
pruebas, se inyecta un módulo ``streamlit`` falso en ``sys.modules`` ANTES de
importar el componente. Ese doble registra en una lista compartida todo el
texto renderizado, de modo que la propiedad se comprueba inspeccionando lo que
el componente "pintó".

Mensajes y comentarios en español, coherentes con el resto del proyecto.
"""

import sys
import types
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st_hyp

# --- Lista compartida donde el streamlit falso acumula lo renderizado -------
# Cada llamada de UI del componente (metric/caption/markdown/warning) vuelca su
# texto aquí; los tests la limpian antes de cada caso generado.
_CAPTURA_RENDER: list[str] = []


def _registra(*args, **kwargs) -> None:
    """Doble de una función de Streamlit: acumula sus argumentos como texto.

    Recoge tanto los argumentos posicionales como los valores de palabra clave
    (p. ej. ``label`` y ``value`` de ``st.metric``) y los añade, ya como cadena,
    a la lista compartida ``_CAPTURA_RENDER``.
    """
    for arg in args:
        _CAPTURA_RENDER.append(str(arg))
    for valor in kwargs.values():
        _CAPTURA_RENDER.append(str(valor))


# --- Inyección del streamlit falso ANTES de importar el componente ----------
# El componente hace ``import streamlit as st`` a nivel de módulo, así que el
# doble debe estar en sys.modules antes de importarlo para que capture el render
# sin necesitar un servidor de Streamlit en marcha.
_fake_streamlit = types.ModuleType("streamlit")
_fake_streamlit.metric = _registra
_fake_streamlit.caption = _registra
_fake_streamlit.markdown = _registra
_fake_streamlit.warning = _registra
sys.modules["streamlit"] = _fake_streamlit

# Añadir app/ al sys.path para poder importar componentes (parents[1] sube desde
# tests/ hasta la raíz del repositorio; desde ahí se localiza app/).
_DIR_APP = Path(__file__).resolve().parents[1] / "app"
if str(_DIR_APP) not in sys.path:
    sys.path.insert(0, str(_DIR_APP))

import componentes  # noqa: E402 - import tras registrar el streamlit falso
import gobernanza  # noqa: E402 - disponible vía sys.path que ajusta componentes


# --- Generadores ------------------------------------------------------------
# Texto no vacío (tras strip) para los tres campos obligatorios del metadato:
# así el registro generado siempre supera gobernanza.metadato_completo.
_texto_no_vacio = st_hyp.text(min_size=1, max_size=30).filter(
    lambda s: s.strip() != ""
)

# Valor de la cifra: no puede ser None (None fuerza el camino "no disponible").
_valor_cifra = st_hyp.one_of(
    st_hyp.integers(),
    st_hyp.floats(allow_nan=False, allow_infinity=False),
    _texto_no_vacio,
)


# Feature: cerebro-andorra-web, Property 9: Toda cifra renderizada incluye metadato completo y linaje válido
@settings(max_examples=100)
@given(
    etiqueta=_texto_no_vacio,
    valor=_valor_cifra,
    fuente=_texto_no_vacio,
    vigencia=_texto_no_vacio,
    fecha_prueba=_texto_no_vacio,
    linaje=st_hyp.sampled_from(sorted(gobernanza.LINAJES_VALIDOS)),
)
def test_cifra_renderizada_gobernada_incluye_metadato_y_linaje(
    etiqueta, valor, fuente, vigencia, fecha_prueba, linaje
):
    """Validates: Requirements 3.1, 3.2, 5.3, 6.4, 7.2, 8.2

    Para cualquier registro con metadato completo (fuente/vigencia/fecha_prueba
    no vacíos) y linaje válido pasado a ``cifra_gobernada`` junto con un valor no
    nulo, la salida renderizada debe incluir la fuente, la vigencia, la fecha de
    prueba y la etiqueta de linaje.
    """
    _CAPTURA_RENDER.clear()

    metadato = gobernanza.construye_metadato(fuente, vigencia, fecha_prueba)
    componentes.cifra_gobernada(etiqueta, valor, metadato, linaje)

    render = "\n".join(_CAPTURA_RENDER)

    assert fuente in render
    assert vigencia in render
    assert fecha_prueba in render
    assert linaje in render
    assert linaje in gobernanza.LINAJES_VALIDOS
