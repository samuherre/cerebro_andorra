"""Componentes de UI reutilizables de la App_Streamlit de Cerebro Andorra.

Este módulo concentra el patrón de presentación "cifra + metadato + linaje" en
un único punto, de modo que el principio rector del proyecto —"0 cifras sin
fuente, sin vigencia y sin fecha de prueba"— quede garantizado de forma
transversal: todas las vistas deben mostrar sus cifras exclusivamente a través
de ``cifra_gobernada``.

La validación de gobernanza se delega en ``scripts/gobernanza.py`` para no
duplicar la lógica: se reutilizan ``metadato_completo`` y ``LINAJES_VALIDOS``.
Como la app se lanza desde la raíz del repositorio
(``streamlit run app/streamlit_app.py``) y ``scripts/`` no es un paquete
importable por defecto, se añade la carpeta ``scripts/`` al ``sys.path``
resolviéndola de forma relativa a este archivo.

Mensajes de consola y textos de interfaz en español, coherentes con el resto
del proyecto.
"""

import sys
from pathlib import Path

import streamlit as st

# --- Resolución de la ruta a scripts/ y reutilización de gobernanza --------
# parents[1] sube desde app/componentes.py hasta la raíz del repositorio; desde
# ahí se localiza scripts/ y se añade al sys.path para poder importar el módulo
# transversal de gobernanza sin convertir scripts/ en un paquete.
_DIR_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_DIR_SCRIPTS) not in sys.path:
    sys.path.append(str(_DIR_SCRIPTS))

import gobernanza  # noqa: E402 - import tras ajustar sys.path

# --- Distintivos visuales por etiqueta de linaje ---------------------------
# Cada linaje se muestra con un emoji y un color propios para que PROXY (dato de
# mercado extraído de la web) sea inmediatamente distinguible de OBSERVADO (dato
# oficial) y de ESTIMADO (Req 7.2).
_DISTINTIVO_LINAJE = {
    gobernanza.LINAJE_OBSERVADO: {"emoji": "🟢", "color": "green"},
    gobernanza.LINAJE_ESTIMADO: {"emoji": "🟡", "color": "orange"},
    gobernanza.LINAJE_PROXY: {"emoji": "🔵", "color": "blue"},
}


def _badge_linaje(linaje: str) -> str:
    """Construye el texto Markdown de un badge de color para un linaje.

    Devuelve una cadena con el emoji y el nombre del linaje coloreados mediante
    la sintaxis de color de Streamlit (``:color[texto]``), de modo que PROXY sea
    visualmente distinguible de OBSERVADO y ESTIMADO (Req 7.2).

    Args:
        linaje: etiqueta de linaje válida (OBSERVADO/ESTIMADO/PROXY).

    Returns:
        Cadena Markdown lista para pasar a ``st.caption``/``st.markdown``.
    """
    distintivo = _DISTINTIVO_LINAJE.get(linaje, {"emoji": "⚪", "color": "gray"})
    return f"{distintivo['emoji']} :{distintivo['color']}[**{linaje}**]"


def cifra_gobernada(
    etiqueta: str,
    valor,
    metadato: "dict | None",
    linaje: "str | None",
    id_fuente: "str | None" = None,
) -> None:
    """Renderiza una cifra sólo si está correctamente gobernada.

    Reconstruye un registro combinando los campos del ``metadato`` (fuente,
    vigencia, fecha de prueba) con el ``linaje`` y lo valida con
    ``gobernanza.metadato_completo``. Si el registro es válido y ``valor`` no es
    ``None``, muestra la cifra con ``st.metric`` acompañada de su Metadato_Cifra
    y de un badge de color para el linaje, cumpliendo "0 cifras sin fuente, sin
    vigencia y sin fecha de prueba" (Req 3.1, 3.2, 7.2).

    Si se pasa ``id_fuente`` (no ``None``), se añade bajo la cifra el
    ``Detalle_Gobernanza`` a un clic (``detalle_gobernanza``), que revela el
    ID_Fuente junto con el nombre de la fuente, la vigencia y la fecha de prueba
    (Req 5.5). Si ``id_fuente`` es ``None``, el comportamiento es idéntico al de
    la v1: no se renderiza ningún control adicional.

    En caso contrario (valor ausente, metadato incompleto o linaje inválido)
    omite la cifra, muestra un indicador de "Dato no disponible" con el motivo y
    registra la omisión en la bitácora mediante un mensaje en español por
    consola, conservando el resto de cifras de la vista (Req 3.3).

    Args:
        etiqueta: rótulo de la cifra (p. ej. "Población total").
        valor: la cifra a mostrar; ``None`` indica que no hay dato.
        metadato: diccionario con ``fuente``, ``vigencia`` y ``fecha_prueba``,
            o ``None`` si no se dispone de metadato.
        linaje: etiqueta de linaje (OBSERVADO/ESTIMADO/PROXY) o ``None``.
        id_fuente: identificador estable de la fuente (``F##``) para el
            Detalle_Gobernanza, o ``None`` para comportarse como en la v1.

    Returns:
        None. El efecto es la representación en la interfaz de Streamlit.
    """
    # Reconstruir el registro que espera la validación de gobernanza a partir
    # de los campos del metadato más la etiqueta de linaje. Si el metadato no es
    # un diccionario se parte de uno vacío para que la validación falle con un
    # motivo claro en lugar de romper.
    registro: dict = {}
    if isinstance(metadato, dict):
        registro.update(metadato)
    registro["linaje"] = linaje

    # Una cifra ausente (valor None) nunca debe mostrarse: se trata igual que un
    # dato no disponible y se documenta el motivo en la bitácora.
    if valor is None:
        motivo = "no hay valor para la cifra"
        _muestra_no_disponible(etiqueta, motivo)
        return

    # La gobernanza es obligatoria: sin metadato completo ni linaje válido la
    # cifra se omite y se registra el motivo concreto en la bitácora (Req 3.3).
    if not gobernanza.metadato_completo(registro):
        motivo = gobernanza._motivo_exclusion(registro)
        _muestra_no_disponible(etiqueta, motivo)
        return

    # Camino feliz: la cifra está bien gobernada, se muestra con su metadato y
    # el distintivo visual del linaje.
    st.metric(label=etiqueta, value=valor)
    st.caption(
        f"Fuente: {registro['fuente']} · Vigencia: {registro['vigencia']} · "
        f"Fecha de prueba: {registro['fecha_prueba']}"
    )
    st.markdown(f"Linaje: {_badge_linaje(registro['linaje'])}")

    # Si la cifra tiene un ID_Fuente asociado, se ofrece su Detalle_Gobernanza a
    # un clic (Req 5.5). Sin id_fuente, el comportamiento es idéntico al de v1.
    if id_fuente is not None:
        detalle_gobernanza(id_fuente, registro)


def detalle_gobernanza(id_fuente: "str | None", metadato: dict) -> None:
    """Revela el Detalle_Gobernanza de una cifra a un único clic.

    Presenta un control plegable (``st.expander`` o, si está disponible,
    ``st.popover``) que, al activarse, muestra el ID_Fuente de la cifra junto
    con el nombre de la fuente, su vigencia y su fecha de prueba (Req 5.5). El
    control ocupa el ancho del contenedor sin un ancho fijo grande, de modo que
    quede visible dentro de la ventana también en móvil (Req 6.4).

    Reutiliza la validación de gobernanza (``gobernanza.metadato_completo``):
    si el metadato no está completo, no renderiza el detalle y deja constancia
    del motivo en la bitácora mediante un mensaje en español por consola.

    Args:
        id_fuente: identificador estable de la fuente (``F##``), o ``None`` si
            la cifra no tiene ID_Fuente asociado en el Inventario_Fuentes.
        metadato: diccionario con ``fuente``, ``vigencia`` y ``fecha_prueba``
            (y opcionalmente ``linaje``) de la cifra.

    Returns:
        None. El efecto es la representación del control en la interfaz.
    """
    # Sin ID_Fuente no se puede auditar la cifra: no se ofrece el detalle y se
    # documenta el motivo en la bitácora (Req 5.6).
    if id_fuente is None or str(id_fuente).strip() == "":
        motivo = "la cifra no tiene ID_Fuente asociado en el inventario"
        print(f"[componentes] Detalle_Gobernanza omitido: {motivo}.")
        return

    # El metadato debe estar completo para mostrar fuente, vigencia y fecha de
    # prueba; se reutiliza la validación transversal de gobernanza.
    registro: dict = {}
    if isinstance(metadato, dict):
        registro.update(metadato)
    if not gobernanza.metadato_completo(registro):
        motivo = gobernanza._motivo_exclusion(registro)
        print(f"[componentes] Detalle_Gobernanza omitido ({id_fuente}): {motivo}.")
        return

    # Preferir st.popover (control compacto a un clic) cuando la versión de
    # Streamlit lo ofrece; si no, usar st.expander, equivalente funcional. En
    # ambos casos el control se dibuja dentro del ancho del contenedor, sin un
    # ancho fijo grande, para seguir siendo usable en móvil (Req 6.4).
    etiqueta_control = "Detalle de gobernanza"
    abre_control = getattr(st, "popover", None)
    if callable(abre_control):
        contenedor = abre_control(etiqueta_control)
    else:
        contenedor = st.expander(etiqueta_control, expanded=False)

    with contenedor:
        st.markdown(f"**ID Fuente:** {id_fuente}")
        st.markdown(f"**Fuente:** {registro['fuente']}")
        st.markdown(f"**Vigencia:** {registro['vigencia']}")
        st.markdown(f"**Fecha de prueba:** {registro['fecha_prueba']}")


def _muestra_no_disponible(etiqueta: str, motivo: str) -> None:
    """Muestra el indicador de "Dato no disponible" y lo registra en bitácora.

    Presenta en la interfaz una advertencia con la etiqueta de la cifra omitida
    y el motivo de la omisión, y deja constancia del mismo motivo en la bitácora
    mediante un mensaje en español por consola (Req 3.3).

    Args:
        etiqueta: rótulo de la cifra que no puede mostrarse.
        motivo: explicación, en español, de por qué se omite la cifra.
    """
    st.warning(f"{etiqueta}: Dato no disponible")
    st.caption(f"Motivo: {motivo}.")
    print(
        f"[componentes] Cifra omitida '{etiqueta}': {motivo} "
        "(no se cumple '0 cifras sin fuente, sin vigencia y sin fecha de prueba')."
    )
