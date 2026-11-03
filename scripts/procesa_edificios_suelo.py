"""Procesamiento de morfología urbana, edificios y equipamiento territorial (tramo Lago).

Lee ``../datos_crudos/edificios_andorra.geojson`` (y opcionalmente
``../datos_crudos/pois_osm_andorra.json`` cuando se ejecuta el extractor de POIs
de OpenStreetMap) y produce dos tablas gobernadas (linaje OBSERVADO, licencia ODbL):

1. ``../datos_procesados/edificios_suelo.csv``: resumen de uso del suelo y
   alturas (plantas ``building:levels``) de los 1.144 edificios catastrados.
2. ``../datos_procesados/equipamientos_suelo.csv``: puntos de interés e
   infraestructura (transporte, salud, educación, servicios públicos, turismo y
   comercio) georreferenciados y asignados a su parròquia canónica.
"""

import datetime
import json
import math
import os

import gobernanza

FUENTE_OSM_EDIFICIOS = "OpenStreetMap vía Overpass API (ODbL)"
RUTA_GEOJSON_EDIFICIOS = "../datos_crudos/edificios_andorra.geojson"
RUTA_POIS_OSM = "../datos_crudos/pois_osm_andorra.json"

RUTA_SALIDA_EDIFICIOS = "../datos_procesados/edificios_suelo.csv"
RUTA_SALIDA_EQUIPAMIENTOS = "../datos_procesados/equipamientos_suelo.csv"

COLUMNAS_EDIFICIOS = [
    "uso_suelo",
    "categoria_osm",
    "num_edificios",
    "con_pisos_declarados",
    "pisos_medios",
    "pisos_maximos",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]

COLUMNAS_EQUIPAMIENTOS = [
    "parroquia",
    "dominio",
    "tipo_equipamiento",
    "nombre",
    "lat",
    "lon",
    "fuente",
    "vigencia",
    "fecha_prueba",
    "linaje",
]

CENTROIDES_PARROQUIES = {
    "Andorra la Vella": (42.5063, 1.5218),
    "Canillo": (42.5676, 1.5976),
    "Encamp": (42.5361, 1.5836),
    "Escaldes-Engordany": (42.5100, 1.5389),
    "La Massana": (42.5448, 1.5146),
    "Ordino": (42.5557, 1.5331),
    "Sant Julià de Lòria": (42.4637, 1.4914),
}

MAPA_USO_EDIFICIO = {
    "apartments": ("Residencial plurifamiliar", "Apartamentos"),
    "residential": ("Residencial plurifamiliar", "Residencial"),
    "house": ("Residencial unifamiliar", "Casas"),
    "detached": ("Residencial unifamiliar", "Vivienda aislada"),
    "terrace": ("Residencial unifamiliar", "Adosados"),
    "hotel": ("Turismo y hostelería", "Hoteles"),
    "school": ("Educación y cultura", "Colegios"),
    "college": ("Educación y cultura", "Centros de educación superior"),
    "chapel": ("Patrimonio y culto", "Capillas / templos"),
    "commercial": ("Comercio y oficinas", "Edificios comerciales"),
    "retail": ("Comercio y oficinas", "Locales minoristas"),
    "office": ("Comercio y oficinas", "Oficinas"),
    "industrial": ("Industria y logística", "Naves industriales"),
    "warehouse": ("Industria y logística", "Almacenes"),
    "hangar": ("Industria y logística", "Hangares"),
    "transportation": ("Transporte y movilidad", "Infraestructura de transporte"),
    "service": ("Servicios e infraestructura", "Edificios de servicio"),
    "grandstand": ("Deporte y recreación", "Graderíos / recintos deportivos"),
    "shed": ("Auxiliar y equipamiento menor", "Cobertizos / anexos"),
    "roof": ("Auxiliar y equipamiento menor", "Cubiertas"),
    "construction": ("En desarrollo", "En construcción"),
    "ruins": ("Patrimonio y culto", "Ruinas históricas"),
    "yes": ("Huella edificada general", "Edificación sin uso específico"),
}

MAPA_EQUIPAMIENTOS = {
    # Transporte y movilidad
    "bus_station": ("Transporte y movilidad", "Estación de autobuses"),
    "bus_stop": ("Transporte y movilidad", "Parada de autobús"),
    "fuel": ("Transporte y movilidad", "Estación de servicio / gasolinera"),
    "charging_station": ("Transporte y movilidad", "Punto de recarga eléctrica"),
    "parking": ("Transporte y movilidad", "Aparcamiento público"),
    "aerialway": ("Transporte y movilidad", "Teleférico / remonte de montaña"),
    # Salud y emergencias
    "hospital": ("Salud y emergencias", "Hospital"),
    "clinic": ("Salud y emergencias", "Centro de salud / clínica"),
    "doctors": ("Salud y emergencias", "Consultorio médico"),
    "pharmacy": ("Salud y emergencias", "Farmacia"),
    "dentist": ("Salud y emergencias", "Clínica dental"),
    "fire_station": ("Salud y emergencias", "Parque de bomberos"),
    "police": ("Salud y emergencias", "Comisaría de policía"),
    "social_facility": ("Salud y emergencias", "Centro de atención social"),
    # Educación, cultura y ciudadanía
    "school": ("Educación y cultura", "Colegio / centro educativo"),
    "college": ("Educación y cultura", "Instituto / educación superior"),
    "university": ("Educación y cultura", "Universidad"),
    "library": ("Educación y cultura", "Biblioteca"),
    "museum": ("Educación y cultura", "Museo"),
    "courthouse": ("Educación y cultura", "Juzgado / equipamiento cívico"),
    "townhall": ("Educación y cultura", "Comú / sede municipal"),
    "place_of_worship": ("Educación y cultura", "Templo / patrimonio religioso"),
    "conference_centre": ("Educación y cultura", "Centro de congresos"),
    # Turismo, comercio y servicios
    "hotel": ("Turismo y servicios", "Hotel / alojamiento"),
    "guest_house": ("Turismo y servicios", "Hostal / pensión"),
    "restaurant": ("Turismo y servicios", "Restaurante"),
    "cafe": ("Turismo y servicios", "Cafetería"),
    "fast_food": ("Turismo y servicios", "Comida rápida"),
    "bar": ("Turismo y servicios", "Bar / local de ocio"),
    "bank": ("Turismo y servicios", "Entidad bancaria"),
    "marketplace": ("Turismo y servicios", "Mercado"),
    "recycling": ("Energía y ambiente", "Punto de reciclaje"),
}


def _centroide_geometria(geometria: dict) -> "tuple[float, float] | None":
    """Calcula el centroide aproximado (lat, lon) de una geometría GeoJSON."""
    if not isinstance(geometria, dict):
        return None
    tipo = geometria.get("type")
    coords = geometria.get("coordinates")
    if not coords:
        return None

    if tipo == "Point" and len(coords) >= 2:
        return float(coords[1]), float(coords[0])

    puntos: list[tuple[float, float]] = []

    def _recolecta(nodo):
        if isinstance(nodo, (list, tuple)):
            if (
                len(nodo) >= 2
                and isinstance(nodo[0], (int, float))
                and isinstance(nodo[1], (int, float))
            ):
                puntos.append((float(nodo[1]), float(nodo[0])))
            else:
                for hijo in nodo:
                    _recolecta(hijo)

    _recolecta(coords)
    if not puntos:
        return None
    lat_media = sum(p[0] for p in puntos) / len(puntos)
    lon_media = sum(p[1] for p in puntos) / len(puntos)
    return round(lat_media, 6), round(lon_media, 6)


def _parroquia_mas_cercana(lat: float, lon: float, addr_city: str = "") -> str:
    """Resuelve la parròquia canónica por etiqueta postal o cercanía al centroide."""
    ciudad = str(addr_city or "").strip().lower()
    if "escaldes" in ciudad:
        return "Escaldes-Engordany"
    if "canillo" in ciudad:
        return "Canillo"
    if "encamp" in ciudad:
        return "Encamp"
    if "ordino" in ciudad:
        return "Ordino"
    if "massana" in ciudad:
        return "La Massana"
    if "sant juli" in ciudad or "loria" in ciudad or "lòria" in ciudad:
        return "Sant Julià de Lòria"
    if "andorra" in ciudad:
        return "Andorra la Vella"

    mejor_parroquia = "Andorra la Vella"
    menor_dist = float("inf")
    for nombre, (clat, clon) in CENTROIDES_PARROQUIES.items():
        dist = math.hypot(lat - clat, lon - clon)
        if dist < menor_dist:
            menor_dist = dist
            mejor_parroquia = nombre
    return mejor_parroquia


def _extrae_pisos(valor) -> "float | None":
    if valor is None:
        return None
    try:
        num = float(str(valor).strip().replace(",", "."))
        return num if 0 < num <= 60 else None
    except (ValueError, TypeError):
        return None


def procesa(fecha_prueba: str) -> None:
    """Procesa edificios_andorra.geojson (y pois_osm_andorra.json si existe)."""
    print("[INICIO] Procesamiento de edificios y equipamiento del suelo (OSM).")

    if not os.path.exists(RUTA_GEOJSON_EDIFICIOS):
        print(f"[AVISO] No existe '{RUTA_GEOJSON_EDIFICIOS}'.")
        gobernanza.escribe_csv([], RUTA_SALIDA_EDIFICIOS, COLUMNAS_EDIFICIOS)
        gobernanza.escribe_csv([], RUTA_SALIDA_EQUIPAMIENTOS, COLUMNAS_EQUIPAMIENTOS)
        return

    try:
        with open(RUTA_GEOJSON_EDIFICIOS, "r", encoding="utf-8") as f:
            geojson = json.load(f)
    except Exception as error:
        print(f"[ERROR] Error al leer '{RUTA_GEOJSON_EDIFICIOS}': {error}.")
        gobernanza.escribe_csv([], RUTA_SALIDA_EDIFICIOS, COLUMNAS_EDIFICIOS)
        gobernanza.escribe_csv([], RUTA_SALIDA_EQUIPAMIENTOS, COLUMNAS_EQUIPAMIENTOS)
        return

    timestamp_raw = str(geojson.get("timestamp", "2026"))[:4]
    vigencia = timestamp_raw if timestamp_raw.isdigit() else "2026"
    features = geojson.get("features") or []

    # 1) Agregación de edificios por tipología y alturas
    grupos_edificios: dict[tuple[str, str], list[float | None]] = {}
    equipamientos: list[dict] = []
    vistos_pois: set[tuple[str, str, float, float]] = set()

    for feat in features:
        props = feat.get("properties") or {}
        b_tag = str(props.get("building", "yes")).strip().lower()
        uso_suelo, categoria_osm = MAPA_USO_EDIFICIO.get(
            b_tag, ("Otros usos urbanos", b_tag.capitalize())
        )
        pisos = _extrae_pisos(props.get("building:levels"))
        grupos_edificios.setdefault((uso_suelo, categoria_osm), []).append(pisos)

        # Extraer equipamiento si el edificio tiene amenity / tourism / school / hotel
        centroide = _centroide_geometria(feat.get("geometry") or {})
        if centroide is None:
            continue
        lat, lon = centroide
        parroquia = _parroquia_mas_cercana(lat, lon, props.get("addr:city", ""))
        nombre_poi = (
            props.get("name")
            or props.get("name:ca")
            or props.get("brand")
            or "Sin nombre específico"
        )

        clave_tipo = (
            props.get("amenity")
            or props.get("tourism")
            or (b_tag if b_tag in ("hotel", "school", "college", "transportation") else None)
        )
        if clave_tipo and str(clave_tipo) in MAPA_EQUIPAMIENTOS:
            dominio, tipo_eq = MAPA_EQUIPAMIENTOS[str(clave_tipo)]
            huella = (dominio, tipo_eq, round(lat, 4), round(lon, 4))
            if huella not in vistos_pois:
                vistos_pois.add(huella)
                equipamientos.append(
                    {
                        "parroquia": parroquia,
                        "dominio": dominio,
                        "tipo_equipamiento": tipo_eq,
                        "nombre": str(nombre_poi).strip(),
                        "lat": lat,
                        "lon": lon,
                        "fuente": FUENTE_OSM_EDIFICIOS,
                        "vigencia": vigencia,
                        "fecha_prueba": fecha_prueba,
                        "linaje": gobernanza.LINAJE_OBSERVADO,
                    }
                )

    # 2) Si existe el archivo adicional de POIs de todo Andorra (descarga_pois_osm.py),
    #    incorporar sus nodos para cubrir las 7 parròquies con transporte, salud y educación.
    if os.path.exists(RUTA_POIS_OSM):
        try:
            with open(RUTA_POIS_OSM, "r", encoding="utf-8") as f_pois:
                datos_pois = json.load(f_pois)
            for elem in datos_pois.get("elements", []):
                tags = elem.get("tags") or {}
                lat = elem.get("lat") or (elem.get("center") or {}).get("lat")
                lon = elem.get("lon") or (elem.get("center") or {}).get("lon")
                if lat is None or lon is None:
                    continue
                lat_f, lon_f = round(float(lat), 6), round(float(lon), 6)
                clave_tipo = (
                    tags.get("amenity")
                    or tags.get("healthcare")
                    or ("bus_stop" if tags.get("highway") == "bus_stop" else None)
                    or ("aerialway" if tags.get("aerialway") else None)
                    or tags.get("tourism")
                )
                if clave_tipo and str(clave_tipo) in MAPA_EQUIPAMIENTOS:
                    dominio, tipo_eq = MAPA_EQUIPAMIENTOS[str(clave_tipo)]
                    huella = (dominio, tipo_eq, round(lat_f, 4), round(lon_f, 4))
                    if huella in vistos_pois:
                        continue
                    vistos_pois.add(huella)
                    parroquia = _parroquia_mas_cercana(
                        lat_f, lon_f, tags.get("addr:city", "")
                    )
                    nombre_poi = (
                        tags.get("name")
                        or tags.get("name:ca")
                        or tags.get("operator")
                        or tipo_eq
                    )
                    equipamientos.append(
                        {
                            "parroquia": parroquia,
                            "dominio": dominio,
                            "tipo_equipamiento": tipo_eq,
                            "nombre": str(nombre_poi).strip(),
                            "lat": lat_f,
                            "lon": lon_f,
                            "fuente": FUENTE_OSM_EDIFICIOS,
                            "vigencia": vigencia,
                            "fecha_prueba": fecha_prueba,
                            "linaje": gobernanza.LINAJE_OBSERVADO,
                        }
                    )
        except Exception as error:
            print(f"[AVISO] No se pudo integrar '{RUTA_POIS_OSM}': {error}.")

    registros_edificios: list[dict] = []
    for (uso_suelo, categoria_osm), lista_pisos in sorted(
        grupos_edificios.items(), key=lambda x: len(x[1]), reverse=True
    ):
        declarados = [p for p in lista_pisos if p is not None]
        pisos_medios = (
            round(sum(declarados) / len(declarados), 2) if declarados else 0.0
        )
        pisos_max = int(max(declarados)) if declarados else 0
        registros_edificios.append(
            {
                "uso_suelo": uso_suelo,
                "categoria_osm": categoria_osm,
                "num_edificios": len(lista_pisos),
                "con_pisos_declarados": len(declarados),
                "pisos_medios": pisos_medios,
                "pisos_maximos": pisos_max,
                "fuente": FUENTE_OSM_EDIFICIOS,
                "vigencia": vigencia,
                "fecha_prueba": fecha_prueba,
                "linaje": gobernanza.LINAJE_OBSERVADO,
            }
        )

    validos_edif = gobernanza.filtra_registros_validos(
        registros_edificios, "edificios_suelo"
    )
    validos_equip = gobernanza.filtra_registros_validos(
        equipamientos, "equipamientos_suelo"
    )

    gobernanza.escribe_csv(validos_edif, RUTA_SALIDA_EDIFICIOS, COLUMNAS_EDIFICIOS)
    gobernanza.escribe_csv(
        validos_equip, RUTA_SALIDA_EQUIPAMIENTOS, COLUMNAS_EQUIPAMIENTOS
    )
    print(
        f"[FIN] Suelo y equipamiento completados: {len(validos_edif)} categorías "
        f"de edificios y {len(validos_equip)} equipamientos georreferenciados."
    )


if __name__ == "__main__":
    procesa(datetime.date.today().isoformat())
