"""Test de propiedad (Hypothesis) para la consistencia del filtro por año de la
Vista Gente/Población de Cerebro Andorra.

Verifica el Requisito 6.3: al seleccionar un año dentro del rango disponible,
toda cifra de población mostrada en la Vista_Poblacion corresponde a ese año
seleccionado y a ningún otro.

Reto de testeo: ``app/vistas/poblacion.py`` renderiza mediante Streamlit y usa
``st.selectbox`` para elegir el año, filtra el DataFrame a ese año y muestra
cada parròquia a través de ``cifra_gobernada`` (``app/componentes.py``). Para
comprobar la consistencia del filtro de forma determinista:

- Se registra un módulo ``streamlit`` falso en ``sys.modules`` ANTES de importar
  ``componentes`` y ``poblacion``. El doble apila el texto renderizado (en
  concreto los ``st.caption``, que incluyen "Vigencia: {vigencia}") en una lista
  compartida y ofrece dobles inertes para el resto de la API usada
  (``header``/``write``/``subheader``/``info``/``warning``/``metric``/
  ``markdown``, ``columns`` como gestores de contexto y ``cache_data`` como
  passthrough).
- ``st.selectbox`` devuelve un año que el propio test controla mediante una
  variable de módulo (``_fake_streamlit._anio_forzado``), de modo que se puede
  forzar cualquier año disponible generado por Hypothesis.
- Se monkeypatchea ``carga_datos.carga_poblacion`` para que devuelva un
  DataFrame generado por Hypothesis que abarca varios años en 2020..2025, con
  ``vigencia == str(anio)`` en cada fila (linaje OBSERVADO).

Como para población ``vigencia`` coincide con ``str(anio)`` y ``cifra_gobernada``
renderiza "Vigencia: {vigencia}" en un ``st.caption``, la propiedad se comprueba
inspeccionando que todos los captions con "Vigencia:" referencian el año
seleccionado y ninguno referencia otro año.

Comentarios y textos en español, coherentes con el resto del proyecto.
"""

import re
import sys
import types
from pathlib import Path

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st_hyp

# --- Captura compartida de lo renderizado por el streamlit falso ------------
# Cada caption/metric/etc. vuelca su texto aquí; el test la limpia por caso.
_CAPTURA_RENDER: list[str] = []


def _registra(*args, **kwargs) -> None:
    """Doble de una función de Streamlit: acumula sus argumentos como texto."""
    for arg in args:
        _CAPTURA_RENDER.append(str(arg))
    for valor in kwargs.values():
        _CAPTURA_RENDER.append(str(valor))


class _ColumnaDummy:
    """Gestor de contexto inerte que imita una columna de ``st.columns``."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _columns(spec, **kwargs):
    """Doble de ``st.columns``: devuelve tantas columnas dummy como se pidan."""
    n = spec if isinstance(spec, int) else len(spec)
    return [_ColumnaDummy() for _ in range(n)]


def _selectbox(label=None, *args, **kwargs):
    """Doble de ``st.selectbox``.

    Para el selector de año devuelve el año forzado por el test; para cualquier
    otro selector (p. ej. el de parròquia que añade la vista enriquecida de la
    Parte 3) devuelve la primera opción disponible, de modo que ``render()``
    siga su curso sin alterar la propiedad bajo prueba (que inspecciona las
    cifras de población total del año seleccionado).
    """
    options = kwargs.get("options")
    if args:
        options = args[0]
    if label == "Año" or options is None:
        return _fake_streamlit._anio_forzado
    opciones = list(options)
    return opciones[0] if opciones else None


class _ContenedorDummy:
    """Gestor de contexto inerte para ``st.expander``/``st.popover``."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _expander(*args, **kwargs):
    """Doble de ``st.expander``: contenedor inerte."""
    return _ContenedorDummy()


def _cache_data(func=None, **kwargs):
    """Doble de ``st.cache_data``: passthrough (con y sin argumentos)."""
    if func is not None:
        return func

    def _decorador(f):
        return f

    return _decorador


# --- Inyección del streamlit falso ANTES de importar los módulos de la app --
_fake_streamlit = types.ModuleType("streamlit")
_fake_streamlit.header = _registra
_fake_streamlit.write = _registra
_fake_streamlit.subheader = _registra
_fake_streamlit.info = _registra
_fake_streamlit.warning = _registra
_fake_streamlit.metric = _registra
_fake_streamlit.caption = _registra
_fake_streamlit.markdown = _registra
_fake_streamlit.columns = _columns
_fake_streamlit.selectbox = _selectbox
_fake_streamlit.cache_data = _cache_data
_fake_streamlit.divider = _registra
_fake_streamlit.dataframe = _registra
_fake_streamlit.plotly_chart = _registra
_fake_streamlit.expander = _expander
_fake_streamlit._anio_forzado = None
sys.modules["streamlit"] = _fake_streamlit

# Añadir app/ y app/vistas al sys.path para importar los módulos de la app.
_DIR_APP = Path(__file__).resolve().parents[1] / "app"
_DIR_VISTAS = _DIR_APP / "vistas"
for _dir in (_DIR_APP, _DIR_VISTAS):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import carga_datos  # noqa: E402 - import tras registrar el streamlit falso
import componentes  # noqa: E402 - import tras registrar el streamlit falso
import poblacion  # noqa: E402 - import tras registrar el streamlit falso


def _rebind_streamlit_falso() -> None:
    """Reengancha el streamlit falso de ESTE archivo en los módulos de la app.

    Otro archivo de test puede haberse importado antes y haber dejado los
    módulos de la app (``poblacion``/``componentes``/``carga_datos``) enganchados
    a SU propio streamlit falso, porque cada módulo hace ``import streamlit as
    st`` a nivel de módulo y ese enlace se resuelve una sola vez, en el primer
    import. Al reasignar aquí el atributo ``st`` de cada módulo ya importado (y
    ``sys.modules['streamlit']``) al doble de este archivo, garantizamos que las
    llamadas de UI (``st.selectbox``/``st.caption``/...) usen y vuelquen en el
    doble de ESTE archivo mientras corre este test, con independencia del orden
    de importación de la suite.
    """
    sys.modules["streamlit"] = _fake_streamlit
    poblacion.st = _fake_streamlit
    componentes.st = _fake_streamlit
    carga_datos.st = _fake_streamlit


# Años soportados por la vista (rango 2020..2025).
_ANIOS = list(range(poblacion.ANIO_MIN, poblacion.ANIO_MAX + 1))

# Las 7 parròquies de Andorra (nombres estables para las filas generadas).
_PARROQUIES = (
    "Andorra la Vella",
    "Escaldes-Engordany",
    "Encamp",
    "La Massana",
    "Ordino",
    "Sant Julià de Lòria",
    "Canillo",
)


def _construye_df(anios: list[int]) -> pd.DataFrame:
    """Construye un DataFrame de población para los años dados.

    Cada (año, parròquia) es una fila con ``vigencia == str(anio)`` y linaje
    OBSERVADO, de modo que todo el metadato de gobernanza esté completo y la
    cifra se renderice.
    """
    registros = []
    for anio in anios:
        for i, parroquia in enumerate(_PARROQUIES):
            registros.append(
                {
                    "parroquia": parroquia,
                    "anio": anio,
                    "poblacion": 1000 + anio + i,
                    "fuente": "Departament d'Estadística",
                    "vigencia": str(anio),
                    "fecha_prueba": "2025-01-15",
                    "linaje": "OBSERVADO",
                }
            )
    return pd.DataFrame(registros)


# Estrategia: subconjunto no vacío de años disponibles + un año seleccionado
# entre ellos. Se usa 'data' para muestrear el año seleccionado dependiente de
# los años generados.
@st_hyp.composite
def _anios_y_seleccion(draw):
    anios = draw(
        st_hyp.lists(
            st_hyp.sampled_from(_ANIOS), min_size=1, max_size=len(_ANIOS), unique=True
        )
    )
    anios = sorted(anios)
    anio_sel = draw(st_hyp.sampled_from(anios))
    return anios, anio_sel


# Feature: cerebro-andorra-web, Property 12: El filtro por año seleccionado es consistente
@settings(max_examples=100)
@given(_anios_y_seleccion())
def test_filtro_por_anio_es_consistente(datos):
    """Validates: Requirements 6.3

    Para cualquier año seleccionado dentro del rango disponible, toda cifra de
    población mostrada en la Vista_Poblacion corresponde a ese año seleccionado.
    """
    anios, anio_sel = datos
    df = _construye_df(anios)

    # Reenganchar el streamlit falso de este archivo por si otro test lo cambió,
    # y (re)aplicar el monkeypatch de la carga que otro archivo pudo reemplazar.
    _rebind_streamlit_falso()
    carga_datos.carga_poblacion = lambda: df
    # Aislar la propiedad del estado del disco: sin desgloses, la vista no
    # renderiza los gráficos por parròquia.
    carga_datos.carga_poblacion_desgloses = lambda: None
    # El bloque de indicadores sociales de la Parte 3 (umbrales de pobreza y
    # tasa de fecundidad) renderiza cifras gobernadas OBSERVADO con SU propia
    # vigencia (el año más reciente del indicador), que es independiente del
    # año seleccionado en el selector de población. Esa vigencia NO debe
    # contaminar la captura que inspecciona esta propiedad (consistencia del
    # filtro por año de las cifras de población total), así que se aísla el
    # bloque social devolviendo None en sus cargas, igual que con los desgloses.
    carga_datos.carga_umbrales_pobreza = lambda: None
    carga_datos.carga_tasa_fecundidad = lambda: None

    # Forzar el año elegido en el selector y limpiar la captura previa.
    _fake_streamlit._anio_forzado = anio_sel
    _CAPTURA_RENDER.clear()

    poblacion.render()

    # Localizar todos los "Vigencia: <año>" renderizados por cifra_gobernada.
    vigencias = re.findall(r"Vigencia:\s*(\d{4})", "\n".join(_CAPTURA_RENDER))

    # Debe haberse mostrado al menos una cifra para el año seleccionado.
    assert vigencias, "no se renderizó ninguna cifra de población"

    # Toda vigencia mostrada corresponde exactamente al año seleccionado y a
    # ningún otro año disponible (consistencia del filtro).
    for anio_mostrado in vigencias:
        assert anio_mostrado == str(anio_sel)
