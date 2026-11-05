"""Operaciones y formatos compartidos por la interfaz de consultas."""

from __future__ import annotations

import json
from typing import Any

from bson import json_util


def dumps(value: Any) -> str:
    """Convierte valores de MongoDB a JSON legible para mostrarlo en la GUI."""
    return json.dumps(
        json.loads(json_util.dumps(value)),
        indent=2,
        ensure_ascii=False,
    )


def run_query(db: Any, query: dict[str, Any]) -> list[dict[str, Any]]:
    """Ejecuta el pipeline de una consulta sobre la colección indicada."""
    return list(db[query["collection"]].aggregate(query["pipeline"]))


def explain_pipeline(pipeline: list[dict[str, Any]]) -> str:
    """Genera una explicación educativa de cada etapa del pipeline."""
    # Estos textos traducen los operadores de MongoDB a explicaciones para el equipo.
    stage_help = {
        "$match": "Filtra y conserva solo los documentos que cumplen las condiciones.",
        "$project": "Selecciona los campos de salida; 1 incluye y 0 excluye.",
        "$sort": "Ordena los resultados; 1 es ascendente y -1 descendente.",
        "$group": "Agrupa documentos y calcula valores por cada grupo.",
        "$count": "Cuenta cuántos documentos llegan hasta esta etapa.",
        "$limit": "Limita la cantidad de documentos que continúan.",
        "$unwind": "Separa cada elemento de un arreglo en un documento independiente.",
        "$lookup": "Relaciona esta colección con otra colección, como un JOIN.",
        "$bucket": "Clasifica valores numéricos dentro de rangos definidos.",
        "$addFields": "Agrega campos calculados sin eliminar los campos existentes.",
        "$setWindowFields": "Calcula valores sobre ventanas o particiones de documentos.",
        "$facet": "Ejecuta varias subconsultas en paralelo sobre los mismos documentos.",
    }
    operator_help = {
        "$gte": "mayor o igual que",
        "$gt": "mayor que",
        "$lte": "menor o igual que",
        "$lt": "menor que",
        "$eq": "igual a",
        "$ne": "distinto de",
        "$or": "cumplir al menos una condición",
        "$and": "cumplir todas las condiciones",
        "$regex": "coincidir con un patrón de texto",
        "$avg": "promedio",
        "$sum": "suma o conteo cuando se suma 1",
        "$min": "valor mínimo",
        "$max": "valor máximo",
        "$round": "redondeo",
        "$size": "tamaño de un arreglo",
        "$filter": "filtrado de elementos de un arreglo",
        "$cond": "condición tipo si/entonces/sino",
        "$switch": "varias condiciones tipo caso",
        "$push": "acumular valores en un arreglo",
        "$addToSet": "acumular valores únicos",
        "$first": "tomar el primer valor según el orden previo",
        "$slice": "tomar una parte de un arreglo",
        "$divide": "división",
        "$multiply": "multiplicación",
        "$subtract": "resta",
        "$rank": "posición dentro de una partición ordenada",
    }

    def operators(value: object) -> list[str]:
        """Busca operadores MongoDB dentro de diccionarios y listas anidadas."""
        found: list[str] = []
        if isinstance(value, dict):
            # Recorre cada campo y revisa tanto la clave actual como sus valores internos.
            for key, nested in value.items():
                if key.startswith("$") and key not in found:
                    found.append(key)
                # La llamada recursiva permite detectar operadores a cualquier profundidad.
                for operator in operators(nested):
                    if operator not in found:
                        found.append(operator)
        elif isinstance(value, list):
            # Algunos operadores reciben listas; también se recorren sus elementos.
            for nested in value:
                for operator in operators(nested):
                    if operator not in found:
                        found.append(operator)
        return found

    lines = ["Lectura del pipeline, paso a paso:"]
    # Procesa las etapas en el mismo orden en que MongoDB ejecuta el pipeline.
    for number, stage in enumerate(pipeline, start=1):
        name, body = next(iter(stage.items()))
        lines.append(f"\n{number}. {name}")
        lines.append(stage_help.get(name, "Transforma los documentos en esta etapa."))

        used = operators(body)
        # Conserva solo las explicaciones disponibles para los operadores detectados.
        details = [
            f"{operator}: {operator_help[operator]}"
            for operator in used
            if operator in operator_help
        ]
        if details:
            lines.append("Operadores: " + "; ".join(details) + ".")

        # Agrega detalles específicos para las etapas que tienen información útil adicional.
        if name == "$sort":
            # Recorre los campos ordenados e indica si cada uno es ascendente o descendente.
            fields = [
                f"{field} ({'ascendente' if direction == 1 else 'descendente'})"
                for field, direction in body.items()
            ]
            lines.append("Orden aplicado: " + ", ".join(fields) + ".")
        elif name == "$project":
            # Recorre los campos proyectados para explicar qué verá el usuario.
            lines.append(
                "Campos visibles o calculados: "
                + ", ".join(str(field) for field in body)
                + "."
            )
        elif name == "$match":
            lines.append(
                "Condiciones aplicadas: "
                + json.dumps(body, ensure_ascii=False, separators=(",", ": "))
            )
        elif name == "$lookup":
            lines.append(
                f"Relaciona {body.get('localField', 'un campo local')} con "
                f"{body.get('foreignField', 'un campo externo')} de "
                f"{body.get('from', 'otra colección')}."
            )
        elif name == "$bucket":
            # Recorre los límites numéricos que forman los rangos del bucket.
            lines.append(
                "Rangos: "
                + ", ".join(str(boundary) for boundary in body.get("boundaries", []))
                + f"; valor fuera de rango: {body.get('default', 'sin default')}."
            )

    return "\n".join(lines)


def summarize_results(results: list[dict[str, Any]]) -> str:
    """Devuelve una lectura breve del número y tipo de resultados obtenidos."""
    if not results:
        return "La consulta se ejecutó correctamente, pero no encontró documentos."
    if len(results) == 1:
        return (
            "La consulta devolvió un documento resumen. "
            "La tabla muestra sus campos principales."
        )
    return (
        f"La consulta devolvió {len(results)} documentos. "
        "La tabla muestra una vista rápida del primero; el JSON completo está a la izquierda."
    )


def display_value(value: object, max_length: int = 100) -> str:
    """Convierte un valor a texto compacto y recorta textos demasiado extensos."""
    text = json.dumps(
        json.loads(json_util.dumps(value)),
        ensure_ascii=False,
        separators=(",", ": "),
    )
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text
