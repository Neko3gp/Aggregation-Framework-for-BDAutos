#!/usr/bin/env python3
"""Genera scripts/02_consultas.js a partir de app/queries.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] # Raíz del proyecto
sys.path.insert(0, str(ROOT / "app"))# sirve para importar queries.py desde app

from queries import QUERIES  # noqa: E402

OUT = ROOT / "scripts" / "02_consultas.js"# Directorio de salida


def main() -> None:
    lines = [
        "/**",
        " * BDAutos — 25 consultas Aggregation Framework",
        " * Generado desde app/queries.py. Ejecutar en mongosh tras migrar.",
        " */",
        "",
        "use bdautos;",
        "",
    ]
    for q in QUERIES: #el ciclo recorre cada consulta en QUERIES para generar el código JavaScript correspondiente.
        pipeline = json.dumps(q["pipeline"], indent=2, ensure_ascii=False)
        lines.append("// " + "-" * 66)
        lines.append(f"// Consulta {q['id']}: {q['title']}")
        lines.append(f"// {q['description']}")
        lines.append("// " + "-" * 66)
        lines.append(f'print("\\n=== Consulta {q["id"]}: {q["title"]} ===");')
        lines.append(f"db.{q['collection']}.aggregate(")
        for pline in pipeline.splitlines(): #ciclo for que recorre cada línea del pipeline JSON y la agrega a la lista lines con una sangría de dos espacios.
            lines.append("  " + pline)
        lines.append(");")
        lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8") #escribe el contenido generado en el archivo de salida especificado por OUT, utilizando codificación UTF-8.
    print(f"Escrito {OUT}")


if __name__ == "__main__":
    main()
