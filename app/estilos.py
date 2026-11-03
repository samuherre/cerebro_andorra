"""Estilos e identidad visual compartida de la App_Streamlit de Cerebro Andorra.

Centraliza el CSS global y los componentes de cabecera para dar una apariencia
coherente, limpia y agradable a todas las vistas, con la paleta de la bandera de
Andorra (azul, amarillo/dorado y rojo). El CSS se inyecta una sola vez por
sesión desde ``streamlit_app.py`` (``aplica_estilo_global``); cada vista puede
abrir con una cabecera consistente mediante ``cabecera``.

Mantener los textos de interfaz en español, coherentes con el resto del
proyecto.
"""

import streamlit as st

# --- Paleta de marca (bandera de Andorra) ----------------------------------
AZUL = "#1A3C8F"
AZUL_OSCURO = "#122a66"
DORADO = "#F4C542"
ROJO = "#D52B1E"
GRIS_TEXTO = "#1C2433"
GRIS_SUAVE = "#5b6472"

# CSS global de la aplicación. Estiliza el contenedor principal, las tarjetas
# (``st.container(border=True)``), las métricas, la barra lateral, las pestañas
# y los avisos, buscando un aspecto de panel profesional sin perder legibilidad
# en pantallas pequeñas.
_CSS_GLOBAL = f"""
<style>
    /* Ancho de lectura cómodo y algo más de aire arriba */
    .block-container {{
        padding-top: 2.2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }}

    /* Tipografía de los títulos de sección con el azul de marca */
    h1, h2, h3 {{
        color: {AZUL_OSCURO};
        letter-spacing: -0.01em;
    }}

    /* Tarjetas con borde: esquinas suaves, sombra ligera y relleno cómodo */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 14px !important;
        border: 1px solid #e6e9f2 !important;
        box-shadow: 0 1px 3px rgba(18, 42, 102, 0.06);
        background: #ffffff;
    }}

    /* Métricas: valor grande en azul de marca */
    div[data-testid="stMetricValue"] {{
        color: {AZUL};
        font-weight: 700;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {GRIS_SUAVE};
        font-weight: 600;
    }}

    /* Barra lateral con fondo suave y acento */
    section[data-testid="stSidebar"] {{
        background: {GRIS_TEXTO};
    }}
    section[data-testid="stSidebar"] * {{
        color: #eef1f8 !important;
    }}

    /* Pestañas: subrayado de marca en la activa */
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {AZUL} !important;
    }}
    div[data-baseweb="tab-highlight"] {{
        background-color: {AZUL} !important;
    }}

    /* Cabecera "hero" de cada vista */
    .ca-hero {{
        background: linear-gradient(120deg, {AZUL} 0%, {AZUL_OSCURO} 100%);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.4rem;
        color: #ffffff;
        box-shadow: 0 4px 18px rgba(18, 42, 102, 0.18);
    }}
    .ca-hero h1 {{
        color: #ffffff !important;
        margin: 0 0 0.25rem 0;
        font-size: 1.9rem;
    }}
    .ca-hero p {{
        color: #dfe6fb;
        margin: 0;
        font-size: 1rem;
        line-height: 1.45;
    }}
    .ca-hero .ca-franja {{
        display: inline-block;
        height: 6px;
        width: 64px;
        margin-bottom: 0.7rem;
        border-radius: 3px;
        background: linear-gradient(90deg, {AZUL} 0 33%, {DORADO} 33% 66%, {ROJO} 66% 100%);
        background-color: {DORADO};
    }}

    /* Chips de linaje */
    .ca-chip {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }}
    .ca-chip-observado {{ background: #e3f3e8; color: #1e7a3d; border: 1px solid #b7e0c4; }}
    .ca-chip-estimado  {{ background: #fdf3da; color: #96690a; border: 1px solid #f2dca0; }}
    .ca-chip-proxy     {{ background: #e5ecfb; color: {AZUL}; border: 1px solid #c2d1f4; }}
</style>
"""


def aplica_estilo_global() -> None:
    """Inyecta el CSS global de la aplicación (una vez por render de página)."""
    st.markdown(_CSS_GLOBAL, unsafe_allow_html=True)


def cabecera(titulo: str, subtitulo: str) -> None:
    """Dibuja la cabecera "hero" consistente al inicio de una vista.

    Presenta el título de la vista y una frase descriptiva sobre un panel con el
    azul de marca y una franja con los colores de la bandera de Andorra, para
    dar una entrada visual coherente y agradable en todas las secciones.

    Args:
        titulo: título de la vista (p. ej. "Panorama general").
        subtitulo: frase breve que describe la vista.
    """
    st.markdown(
        f"""
        <div class="ca-hero">
            <span class="ca-franja"></span>
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
