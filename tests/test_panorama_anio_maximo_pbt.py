"""Test de propiedad (Hypothesis) para la selección del año máximo en Panorama.

Verifica la Property 10 del diseño: la cifra "del año más reciente" (población
total del Panorama y población por parròquia de la Vista_Poblacion) corresponde
al año máximo presente en los datos, y la etiqueta de año mostrada es ese
máximo.

Los módulos de vista (``app/vistas/panorama.py``) hacen ``import streamlit as st``
a nivel de módulo y llaman a funciones de Streamlit para pintar. Como no hay un
servidor de Streamlit en las pruebas, se inyecta un módulo ``streamlit`` falso
en ``sys.modules`` ANTES de importar las vistas. Ese doble:

- registra en una lista compartida todo el texto renderizado (esp. lo que emite
  ``cifra_gobernada`` a través de ``st.metric``/``st.caption``/``st.markdown``),
- expone ``st.columns`` devolviendo objetos usables como gestores de contexto
  (``with columna:``),
- expone ``st.cache_data`` como decorador passthrough para que ``carga_datos``
  se importe sin un runtime de Streamlit.

Para no leer disco, se monkeypatchea ``carga_datos.carga_poblacion`` dentro del
test para que devuelva el DataFrame generado por Hypothesis.

Mensajes y comentarios en español, coherentes con el resto del proyecto.
"""

import sys
import types
from pathlib import Path

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st_hyp

# --- Lista compartida donde el streamlit falso acumula lo renderizado -------
_CAPTURA_RENDER: list[str] = []


def _registra(*args, **kwargs) -> None:
    """Doble de una función de Streamlit: acumula sus argumentos como texto."""
    for arg in args:
        _CAPTURA_RENDER.append(str(arg))
    for valor in kwargs.values():
        _CAPTURA_RENDER.append(str(valor))


class _ColumnaFalsa:
    """Doble de una columna de Streamlit usable como gestor de contexto.

    Permite ``with columna:`` (patrón que usa panorama.render) sin romper.
    """

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _columns(spec, **kwargs):
    """Doble de ``st.columns``: devuelve tantas columnas como se soliciten."""
    numero = spec if isinstance(spec, int) else len(spec)
    return [_ColumnaFalsa() for _ in range(numero)]


def _cache_data(func=None, **kwargs):
    """Doble de ``st.cache_data``: decorador passthrough (con o sin args)."""
    if func is not None:
        return func

    def _decorador(f):
        return f

    return _decorador


# --- Inyección del streamlit falso ANTES de importar las vistas -------------
_fake_streamlit = types.ModuleType("streamlit")
_fake_streamlit.title = _registra
_fake_streamlit.write = _registra
_fake_streamlit.header = _registra
_fake_streamlit.subheader = _registra
_fake_streamlit.columns = _columns
_fake_streamlit.metric = _registra
_fake_streamlit.caption = _registra
_fake_streamlit.markdown = _registra
_fake_streamlit.warning = _registra
_fake_streamlit.info = _registra
_fake_streamlit.selectbox = _registra
_fake_streamlit.set_page_config = _registra
_fake_streamlit.cache_data = _cache_data
sys.modules["streamlit"] = _fake_streamlit

# Añadir app/ y app/vistas/ al sys.path (parents[1] sube desde tests/ a la raíz).
_RAIZ = Path(__file__).resolve().parents[1]
for _sub in ("app", "app/vistas"):
    _ruta = str(_RAIZ / _sub)
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import carga_datos  # noqa: E402 - import tras registrar el streamlit falso
import componentes  # noqa: E402 - import tras registrar el streamlit falso
import panorama  # noqa: E402 - import tras registrar el streamlit falso


def _rebind_streamlit_falso() -> None:
    """Reengancha el streamlit falso de ESTE archivo en los módulos de la app.

    Otro archivo de test puede haberse importado antes y haber dejado los
    módulos de la app (``panorama``/``componentes``/``carga_datos``) enganchados
    a SU propio streamlit falso, porque cada módulo hace ``import streamlit as
    st`` a nivel de módulo y ese enlace se resuelve una sola vez, en el primer
    import. Al reasignar aquí el atributo ``st`` de cada módulo ya importado (y
    ``sys.modules['streamlit']``) al doble de este archivo, garantizamos que las
    llamadas de UI (``st.metric``/``st.caption``/...) vuelquen en la lista de
    captura de ESTE archivo mientras corre este test, con independencia del
    orden de importación de la suite.
    """
    sys.modules["streamlit"] = _fake_streamlit
    panorama.st = _fake_streamlit
    componentes.st = _fake_streamlit
    carga_datos.st = _fake_streamlit


# --- Generadores ------------------------------------------------------------
# Conjunto de años con al menos 2 valores distintos, dentro de un rango amplio
# alrededor del rango del proyecto para ejercitar la selección del máximo.
_anios = st_hyp.lists(
    st_hyp.integers(min_value=1990, max_value=2100),
    min_size=2,
    max_size=8,
    unique=True,
)

# Población: entero no negativo (coherente con el dominio del dato).
_poblacion = st_hyp.integers(min_value=0, max_value=200_000)


def _construye_df(anios, poblaciones_por_anio) -> pd.DataFrame:
    """Construye un DataFrame de población largo con gobernanza válida.

    Genera un registro por año (una parròquia por simplicidad; la propiedad
    trata de la selección del año, no del número de parròquies), con los campos
    de gobernanza no vacíos y linaje OBSERVADO para que ``cifra_gobernada`` no
    descarte la cifra.
    """
    filas = []
    for anio, poblacion in zip(anios, poblaciones_por_anio):
        filas.append(
            {
                "parroquia": "Andorra la Vella",
                "anio": anio,
                "poblacion": poblacion,
                "fuente": "Departament d'Estadística d'Andorra",
                "vigencia": str(anio),
                "fecha_prueba": "2025-01-15",
                "linaje": "OBSERVADO",
            }
        )
    return pd.DataFrame(filas)


# Feature: cerebro-andorra-web, Property 10: La cifra del año más reciente usa el año máximo disponible
@settings(max_examples=100)
@given(anios=_anios, datos=st_hyp.data())
def test_panorama_usa_el_anio_maximo(anios, datos):
    """Validates: Requirements 5.1, 6.1

    Para cualquier conjunto de datos de población con varios años, la cifra de
    población total del Panorama corresponde al año máximo presente y la
    etiqueta de año mostrada es ese máximo.
    """
    poblaciones = datos.draw(
        st_hyp.lists(_poblacion, min_size=len(anios), max_size=len(anios))
    )
    df = _construye_df(anios, poblaciones)

    anio_maximo = max(anios)
    total_esperado = sum(
        p for a, p in zip(anios, poblaciones) if a == anio_maximo
    )

    # Reenganchar el streamlit falso de este archivo por si otro test lo cambió,
    # y re-aplicar el monkeypatch de la carga (otro archivo pudo reemplazarlo).
    _rebind_streamlit_falso()
    carga_datos.carga_poblacion = lambda: df

    _CAPTURA_RENDER.clear()
    panorama._cifra_poblacion_total()
    render = "\n".join(_CAPTURA_RENDER)

    # La etiqueta de año mostrada es el máximo (aparece en el rótulo de la cifra).
    assert str(anio_maximo) in render

    # La cifra corresponde al total del año máximo (formateado con '.' de miles).
    total_formateado = f"{total_esperado:,}".replace(",", ".")
    assert total_formateado in render

    # Ningún año estrictamente mayor podría haberse elegido: por construcción el
    # máximo es único como valor, así que basta comprobar que se usó ese año.
    for otro in anios:
        if otro != anio_maximo:
            # El rótulo de la cifra no debe anunciar un año distinto del máximo.
            assert f"Población total de Andorra ({otro})" not in render
