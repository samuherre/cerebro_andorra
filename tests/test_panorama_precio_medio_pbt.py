"""Test de propiedad (Hypothesis) para el precio de venta medio del Panorama.

Verifica la Propiedad 11 del diseño: para cualquier conjunto no vacío de precios
de venta, el precio de venta medio que muestra la Vista Panorama está acotado
entre el mínimo y el máximo de esos precios y se presenta con a lo sumo dos
decimales (Req 5.2).

La media se calcula dentro de ``app/vistas/panorama.py:_cifra_precio_venta_medio``
y se renderiza a través de ``componentes.cifra_gobernada`` (que usa Streamlit).
Como no hay un servidor de Streamlit en las pruebas, se inyecta un módulo
``streamlit`` falso en ``sys.modules`` ANTES de importar ``panorama``. Ese doble
captura el valor que llega a ``st.metric`` (la cifra formateada) para poder
inspeccionar la media mostrada. Además se monkeypatchea
``carga_datos.carga_precios`` para devolver un DataFrame generado por Hypothesis.

Mensajes y comentarios en español, coherentes con el resto del proyecto.
"""

import sys
import types
from pathlib import Path

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st_hyp

# --- Captura del valor renderizado por st.metric ----------------------------
# ``cifra_gobernada`` llama a ``st.metric(label=..., value=...)`` con la cifra ya
# formateada; guardamos aquí el último ``value`` para poder leer la media.
_CAPTURA_METRIC: list[str] = []


def _fake_metric(*args, **kwargs) -> None:
    """Doble de ``st.metric``: guarda el ``value`` renderizado como texto."""
    valor = kwargs.get("value")
    if valor is None and args:
        # value podría venir posicional (label, value)
        valor = args[-1]
    _CAPTURA_METRIC.append(str(valor))


def _noop(*args, **kwargs) -> None:
    """Doble genérico sin efecto para funciones de UI de Streamlit."""
    return None


class _ColumnaDummy:
    """Contexto vacío para simular las columnas de ``st.columns``."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fake_columns(n, *args, **kwargs):
    """Doble de ``st.columns``: devuelve n columnas usables como contexto."""
    cantidad = n if isinstance(n, int) else len(n)
    return [_ColumnaDummy() for _ in range(cantidad)]


def _cache_data(func=None, *args, **kwargs):
    """Doble de ``st.cache_data``: decorador passthrough (con o sin paréntesis)."""
    if callable(func):
        return func

    def _wrap(f):
        return f

    return _wrap


# --- Inyección del streamlit falso ANTES de importar panorama ---------------
_fake_streamlit = types.ModuleType("streamlit")
_fake_streamlit.metric = _fake_metric
_fake_streamlit.title = _noop
_fake_streamlit.write = _noop
_fake_streamlit.header = _noop
_fake_streamlit.subheader = _noop
_fake_streamlit.caption = _noop
_fake_streamlit.markdown = _noop
_fake_streamlit.warning = _noop
_fake_streamlit.set_page_config = _noop
_fake_streamlit.columns = _fake_columns
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
    llamadas de UI (``st.metric``/``st.caption``/...) vuelquen en la captura de
    ESTE archivo mientras corre este test, con independencia del orden de
    importación de la suite.
    """
    sys.modules["streamlit"] = _fake_streamlit
    panorama.st = _fake_streamlit
    componentes.st = _fake_streamlit
    carga_datos.st = _fake_streamlit


# --- Columnas del DataFrame de precios que consume la vista -----------------
_COLUMNAS_PRECIOS = [
    "parroquia",
    "precio_venta",
    "var_venta",
    "precio_alquiler",
    "var_alquiler",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]


def _construye_df_precios(precios: list[float]) -> pd.DataFrame:
    """Construye un DataFrame de precios de vivienda bien gobernado.

    Rellena una fila por precio de venta con campos de gobernanza válidos
    (fuente/vigencia/fecha_prueba no vacíos y linaje PROXY) para que la cifra
    supere la validación de ``cifra_gobernada`` y llegue a ``st.metric``.
    """
    filas = []
    for indice, precio in enumerate(precios):
        filas.append(
            {
                "parroquia": f"Parroquia {indice}",
                "precio_venta": precio,
                "var_venta": 0.0,
                "precio_alquiler": 0.0,
                "var_alquiler": 0.0,
                "fuente": "Indomio",
                "vigencia": "2025-T3",
                "fecha_prueba": "2025-09-27",
                "linaje": "PROXY",
            }
        )
    return pd.DataFrame(filas, columns=_COLUMNAS_PRECIOS)


# Precios de venta: no negativos, finitos y acotados a valores razonables para
# evitar problemas de precisión con floats enormes; al menos uno.
_precios = st_hyp.lists(
    st_hyp.floats(
        min_value=0.0,
        max_value=1_000_000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
    min_size=1,
    max_size=30,
)


# Feature: cerebro-andorra-web, Property 11: El precio medio del Panorama está acotado y redondeado
@settings(max_examples=100)
@given(precios=_precios)
def test_precio_venta_medio_acotado_y_redondeado(precios):
    """Validates: Requirements 5.2

    Para cualquier conjunto no vacío de precios de venta, el precio de venta
    medio mostrado por la Vista Panorama es >= al mínimo y <= al máximo de esos
    precios (con tolerancia por el redondeo) y tiene a lo sumo dos decimales.
    """
    _CAPTURA_METRIC.clear()

    # Reenganchar el streamlit falso de este archivo por si otro test lo cambió,
    # de modo que st.metric vuelque en _CAPTURA_METRIC de ESTE archivo.
    _rebind_streamlit_falso()

    df = _construye_df_precios(precios)
    # Se sustituye la carga de precios por el DataFrame generado y se restaura
    # después, evitando fixtures de función que Hypothesis no reinicia por caso.
    original_carga_precios = carga_datos.carga_precios
    carga_datos.carga_precios = lambda: df
    try:
        panorama._cifra_precio_venta_medio()
    finally:
        carga_datos.carga_precios = original_carga_precios

    # La vista debe haber renderizado exactamente una cifra a través de metric.
    assert len(_CAPTURA_METRIC) == 1
    mostrado = _CAPTURA_METRIC[0]

    # A lo sumo dos decimales: por el formato .2f la parte decimal tiene 2
    # dígitos; se comprueba explícitamente sobre la cadena y sobre el número.
    valor = float(mostrado)
    assert "." in mostrado
    assert len(mostrado.split(".")[1]) <= 2
    assert round(valor, 2) == valor

    # Acotado entre el mínimo y el máximo de los precios de entrada. Se permite
    # una tolerancia igual a medio ulp de redondeo (0.005) porque redondear la
    # media a dos decimales puede empujarla ligeramente fuera de [min, max]
    # cuando la media coincide casi exactamente con un extremo.
    minimo = min(precios)
    maximo = max(precios)
    assert minimo - 0.005 <= valor <= maximo + 0.005
