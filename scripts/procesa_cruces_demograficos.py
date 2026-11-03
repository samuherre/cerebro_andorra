"""Procesamiento de cruces demográficos por sexo de Andorra (tramo Lago).

Normaliza los tres desgloses cruzados por sexo a escala nacional que residen en
``datos_crudos/``:
- ``estadistica_id1098`` (Sexo × Edad en tramos de 5 años) -> ``sexo_edad_5``
- ``estadistica_id1104`` (Sexo × Nacionalidad)             -> ``sexo_nacionalidad``
- ``estadistica_id1138`` (Sexo × Lugar de nacimiento)      -> ``sexo_lugar_nacimiento``

Escribe el resultado gobernado (linaje OBSERVADO) en
``../datos_procesados/poblacion_cruces_sexo.csv``.
"""

import datetime

import pandas as pd

import gobernanza

FUENTE_CRUCES = "Departament d'Estadística d'Andorra (sig.govern.ad, id1098/1104/1138)"
RUTA_SALIDA = "../datos_procesados/poblacion_cruces_sexo.csv"

ANIOS_ESPERADOS = [2020, 2021, 2022, 2023, 2024, 2025]
COLUMNAS_SALIDA = [
    "dimension",
    "sexo",
    "categoria",
    "anio",
    "valor",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]

MAPA_SEXO = {
    "HOME": "HOME",
    "HOMES": "HOME",
    "DONA": "DONA",
    "DONES": "DONA",
}

CONFIG_CRUCES = {
    "sexo_edad_5": {
        "archivo": (
            "../datos_crudos/estadistica_id1098_població_població_per_sexe_i_"
            "edat_(trams_5_anys).csv"
        ),
        "prefijo": "POBLACIÓ PER SEXE I EDAT (TRAMS 5 ANYS).",
    },
    "sexo_nacionalidad": {
        "archivo": (
            "../datos_crudos/estadistica_id1104_població_població_per_sexe_i_"
            "nacionalitat.csv"
        ),
        "prefijo": "POBLACIÓ PER SEXE I NACIONALITAT.",
    },
    "sexo_lugar_nacimiento": {
        "archivo": (
            "../datos_crudos/estadistica_id1138_població_població_per_sexe_i_"
            "lloc_de_naixement.csv"
        ),
        "prefijo": "Població per sexe i lloc de naixement.",
    },
}


def _extrae_sexo_categoria(descripcion: str, prefijo: str) -> "tuple[str, str] | None":
    if descripcion is None:
        return None
    texto = str(descripcion).strip()
    if not texto.upper().startswith(prefijo.upper()):
        return None
    resto = texto[len(prefijo) :].strip()
    segmentos = [s.strip() for s in resto.split(". ") if s.strip()]
    if len(segmentos) < 2:
        return None
    sexo = MAPA_SEXO.get(segmentos[0].upper())
    categoria = segmentos[1].strip()
    if sexo is None or not categoria or categoria.upper() == "TOTAL":
        return None
    return sexo, categoria


def _a_entero(valor) -> "int | None":
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    try:
        numero = float(texto.replace(",", ""))
    except (ValueError, TypeError):
        return None
    if numero < 0 or numero != int(numero):
        return None
    return int(numero)


def procesa(fecha_prueba: str) -> None:
    """Procesa los 3 archivos de cruces por sexo y escribe poblacion_cruces_sexo.csv."""
    print("[INICIO] Procesamiento de cruces demográficos por sexo.")
    registros: list[dict] = []

    for dimension, cfg in CONFIG_CRUCES.items():
        ruta = cfg["archivo"]
        try:
            df = pd.read_csv(ruta, sep=";", encoding="utf-8")
        except Exception as error:
            print(f"[AVISO] No se pudo leer '{ruta}': {error}. Se omite '{dimension}'.")
            continue

        for _, fila in df.iterrows():
            par = _extrae_sexo_categoria(fila.get("Descripció"), cfg["prefijo"])
            if par is None:
                continue
            sexo, categoria = par
            for anio in ANIOS_ESPERADOS:
                col = str(anio) if str(anio) in df.columns else anio
                if col not in df.columns:
                    continue
                valor = _a_entero(fila[col])
                if valor is None:
                    continue
                registros.append(
                    {
                        "dimension": dimension,
                        "sexo": sexo,
                        "categoria": categoria,
                        "anio": int(anio),
                        "valor": valor,
                        "fuente": FUENTE_CRUCES,
                        "vigencia": str(anio),
                        "fecha_prueba": fecha_prueba,
                        "linaje": gobernanza.LINAJE_OBSERVADO,
                    }
                )

    validos = gobernanza.filtra_registros_validos(registros, "poblacion_cruces_sexo")
    gobernanza.escribe_csv(validos, RUTA_SALIDA, COLUMNAS_SALIDA)
    print(
        f"[FIN] Cruces demográficos por sexo completados: {len(validos)} registros en '{RUTA_SALIDA}'."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
