"""Test de propiedad de gobernanza válida por registro (Property 7).

Verifica que el pipeline anota gobernanza válida en cada registro de salida:
todo registro tiene ``fuente``, ``vigencia`` y ``fecha_prueba`` no vacíos y un
``linaje`` perteneciente a ``gobernanza.LINAJES_VALIDOS``; además, todo registro
de precios de Indomio tiene ``linaje`` = PROXY y todo registro de población
tiene ``linaje`` = OBSERVADO.

Sub-tarea 6.2 del plan (Validates: Requirements 2.5, 3.4). Usa Hypothesis con
un mínimo de 100 iteraciones. Los mensajes van en español, coherentes con el
resto del proyecto.
"""

import sys
from pathlib import Path

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

# Los módulos del pipeline viven en scripts/; se añaden al path de importación.
RUTA_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(RUTA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUTA_SCRIPTS))

import gobernanza  # noqa: E402
import procesa_poblacion  # noqa: E402
import procesa_vivienda  # noqa: E402

# --- Estrategias de generación de entradas válidas -------------------------

# Nombres canónicos de parròquia que conocen ambos procesadores.
PARROQUIAS = sorted(procesa_poblacion.NOMBRES_CANONICOS.values())

# Municipios de Indomio que se mapean a un nombre canónico de parròquia.
MUNICIPIOS_INDOMIO = sorted(procesa_vivienda.MAPEO_PARROQUIA.keys())


def _celda_precio(valor_entero: int, variacion: float) -> str:
    """Construye una celda de precio Indomio válida como "7,115(+14.8%)".

    Usa la coma como separador de miles para ejercitar el parseo real.
    """
    cuerpo = f"{valor_entero:,}"  # separador de miles con coma (7,115)
    signo = "+" if variacion >= 0 else "-"
    return f"{cuerpo}({signo}{abs(variacion):.1f}%)"


# Registros de población válidos: parroquia/anio/poblacion (Req 3.4).
registros_poblacion = st.lists(
    st.fixed_dictionaries(
        {
            "parroquia": st.sampled_from(PARROQUIAS),
            "anio": st.integers(min_value=2020, max_value=2025),
            "poblacion": st.integers(min_value=0, max_value=100_000),
        }
    ),
    min_size=1,
    max_size=20,
)

# Celdas de precio válidas para el DataFrame de vivienda (Req 2.5).
celda_valida = st.builds(
    _celda_precio,
    valor_entero=st.integers(min_value=1, max_value=999_999),
    variacion=st.floats(
        min_value=-99.9, max_value=99.9, allow_nan=False, allow_infinity=False
    ),
)

# Filas del DataFrame de Indomio: municipio + celdas de venta y alquiler.
filas_vivienda = st.lists(
    st.tuples(st.sampled_from(MUNICIPIOS_INDOMIO), celda_valida, celda_valida),
    min_size=1,
    max_size=10,
)

# Fecha de prueba en formato ISO AAAA-MM-DD.
fechas_prueba = st.dates(
    min_value=pd.Timestamp("2020-01-01").date(),
    max_value=pd.Timestamp("2030-12-31").date(),
).map(lambda d: d.isoformat())


# --- Property 7 ------------------------------------------------------------

# Feature: cerebro-andorra-web, Property 7: El pipeline anota gobernanza válida en cada registro
@settings(max_examples=100)
@given(
    poblacion=registros_poblacion,
    filas=filas_vivienda,
    fecha_prueba=fechas_prueba,
)
def test_pipeline_anota_gobernanza_valida_por_registro(poblacion, filas, fecha_prueba):
    """Todo registro de salida tiene metadato completo y linaje correcto.

    Validates: Requirements 2.5, 3.4
    """
    # --- Rama de población: linaje OBSERVADO -------------------------------
    registros_pob = procesa_poblacion.anota_gobernanza(list(poblacion), fecha_prueba)
    for registro in registros_pob:
        for campo in ("fuente", "vigencia", "fecha_prueba"):
            assert str(registro.get(campo, "")).strip() != "", (
                f"El registro de población debe tener '{campo}' no vacío: {registro}"
            )
        assert registro["linaje"] in gobernanza.LINAJES_VALIDOS
        assert registro["linaje"] == gobernanza.LINAJE_OBSERVADO

    # --- Rama de vivienda: linaje PROXY ------------------------------------
    df_vivienda = pd.DataFrame(
        [
            {"Municipalities": municipio, "Sale €/m²": venta, "Rent €/m²": alquiler}
            for (municipio, venta, alquiler) in filas
        ]
    )
    registros_viv = procesa_vivienda.normaliza_precios(df_vivienda, fecha_prueba)
    for registro in registros_viv:
        for campo in ("fuente", "vigencia", "fecha_prueba"):
            assert str(registro.get(campo, "")).strip() != "", (
                f"El registro de vivienda debe tener '{campo}' no vacío: {registro}"
            )
        assert registro["linaje"] in gobernanza.LINAJES_VALIDOS
        assert registro["linaje"] == gobernanza.LINAJE_PROXY
