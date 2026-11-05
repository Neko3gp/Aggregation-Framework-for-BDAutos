"""
Migra BDAutosU2.sql (modelo relacional) hacia MongoDB bdautos
usando embedding + linking según el diseño del proyecto.
"""


# ETAPA 1: importaciones y configuración general.
# Importaciones de módulos necesarios para la migración de datos desde un archivo SQL a una base de datos MongoDB
from __future__ import annotations # Soporta anotaciones de tipo en tiempo de ejecución
import argparse
import os
import re
import sys
from pathlib import Path
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1] # Raíz del proyecto
DEFAULT_SQL = ROOT / "data" / "BDAutosU2.sql" # Ruta por defecto del archivo SQL
DEFAULT_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017") 
DB_NAME = os.environ.get("MONGODB_DB", "bdautos")

#expresiones y patrones para extraer procesar las sentencias del sql y convertirlas en documentos de MongoDB
INSERT_RE = re.compile( # Expresión regular para extraer las sentencias INSERT
    r"INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.+)\);", # Patrón para coincidir con las sentencias INSERT
    re.IGNORECASE,
)

# ETAPA 2: lectura y conversión de valores provenientes del SQL.
# Definimos el parse para convertir los valores de las sentencias SQL en tipos de datos aceptables para MongoDB
def parse_value(raw: str): 
    raw = raw.strip()
    if raw.startswith("'") and raw.endswith("'"): #si el valor está entre comillas simples, se trata como cadena de texto
        return raw[1:-1].replace("''", "'") #se eliminan las comillas y se reemplazan las comillas dobles por simples
    
    if "." in raw: #si el valor contiene un punto, se trata como número flotante
        return float(raw)
    return int(raw)



def parse_values(payload: str) -> list: #función para separar valores de una sentencia
    parts: list[str] = [] #en una lista que almacenará los valores separados
    current: list[str] = [] #en una lista que almacenará el valor actual
    in_str = False 
    for ch in payload: #ciclo que recorre cada carácter del payload y ver si está en una cadena de texto
        if ch == "'" and not in_str: # la comilla simple indica el inicio de una cadena
            in_str = True #se marca que estamos en una cadena
            current.append(ch) #ch se agrega a la lista current para formar el valor completo
       
        elif ch == "'" and in_str: # la comilla simple indica el final de una cadena
            in_str = False #se marca que ya no estamos en una cadena
            current.append(ch)
       
        elif ch == "," and not in_str: #la coma indica el final de un valor, mientras no estemos en una cadena
            parts.append("".join(current).strip()) #valor actual se agrega a la lista parts y se reinicia current para el siguiente valor
            current = []
       
        else: #si no es una comilla ni una coma, se agrega el carácter al valor actual
            current.append(ch)
   
    if current: #si hay un valor actual pendiente, se agrega a la lista parts
        parts.append("".join(current).strip())
    return [parse_value(p) for p in parts] #regresamos una lista ya parseada de valores

# ETAPA 3: carga de las tablas SQL en memoria.
# Definimos la función que carga las tablas y las organiza en un diccionario
def load_sql_tables(sql_path: Path) -> dict[str, list[list]]:
    tables: dict[str, list[list]] = {
        "CONTINENTS": [],
        "COUNTRIES": [],
        "CAR_MAKERS": [],
        "MODEL_DETAILS": [],
        "CAR_NAMES": [],
        "CAR_DETAILS": [],
    }

    text = sql_path.read_text(encoding="utf-8") #leemos el contenido del sql y almacenamos
    for match in INSERT_RE.finditer(text): #recorremos coincidencias y extreamos el nombre de la tabla
        table = match.group(1).upper()
        
        if table not in tables: #si la tabla no está en el diccionario, se ignora
            continue
        tables[table].append(parse_values(match.group(2)))
    return tables #retornamos el diccionario con las tablas y sus valores parseados

# ETAPA 4: transformación del modelo relacional a documentos MongoDB.
# Definimos la función que hace la construcción de documentos para MongoDB
def build_documents(tables: dict[str, list[list]]):
    
    continents = [ #creamos una lista con los continentes
        {"_id": row[0], "contId": row[0], "name": row[1]}
        for row in tables["CONTINENTS"] #recorremos los continentes y creamos un diccionario para cada uno
    ]

    #creamos un diccionario que mapea el id del continente a su documento correspondiente
    continent_by_id = {c["_id"]: c for c in continents} 

    countries = [] #creamos una lista con los países
    for row in tables["COUNTRIES"]:
        cont = continent_by_id[row[2]]
        countries.append(
            {
                "_id": row[0],
                "countryId": row[0],
                "name": row[1],
                "continentId": row[2],  # linking
                "continent": {"id": cont["_id"], "name": cont["name"]},  # embedding snapshot
            }
        )
    country_by_id = {c["_id"]: c for c in countries} #ordenandolos por su id

    models_by_maker: dict[int, list[dict]] = {} # diccionario que mapea el id del fabricante a una lista de modelos
    model_by_id: dict[int, dict] = {}# diccionario que mapea el id del modelo a su documento correspondiente
    for row in tables["MODEL_DETAILS"]:

        # creamos un diccionario con los detalles de cada modelo
        model = {"modelId": row[0], "name": row[2], "makerId": row[1]}
        model_by_id[row[0]] = model
        models_by_maker.setdefault(row[1], []).append(
            {"modelId": row[0], "name": row[2]}
        )

    # creamos una lista con los fabricantes
    makers = []
    maker_by_id: dict[int, dict] = {}#mapeamos el id del fabricante a su documento correspondiente
    for row in tables["CAR_MAKERS"]:
        country = country_by_id[row[3]]
        doc = {
            "_id": row[0],
            "makerId": row[0],
            "name": row[1],
            "fullName": row[2],
            "countryId": row[3],  # linking
            "country": {
                "id": country["_id"],
                "name": country["name"],
            },
            "continent": {
                "id": country["continent"]["id"],
                "name": country["continent"]["name"],
            },
            "models": models_by_maker.get(row[0], []),  # embedding
        }
        makers.append(doc)
        maker_by_id[row[0]] = doc

    # creamos un diccionario que mapea el id del coche a su documento correspondiente
    details_by_id = {row[0]: row for row in tables["CAR_DETAILS"]}
    cars = []
    for row in tables["CAR_NAMES"]: #recorremos los nombres de los coches y creamos un diccionario para cada uno
        id_car, model_id, descr = row
        detail = details_by_id[id_car]
        model = model_by_id[model_id]
        maker = maker_by_id[model["makerId"]]
        cars.append(
            {
                "_id": id_car,
                "idCar": id_car,
                "descr": descr,
                "mpg": detail[1],
                "cylinders": detail[2],
                "edispl": detail[3],
                "horsepower": detail[4],
                "weight": detail[5],
                "accel": detail[6],
                "year": detail[7],
                # embedding de catálogos frecuentes en consultas
                "model": {"id": model["modelId"], "name": model["name"]},
                "maker": {
                    "id": maker["makerId"],
                    "name": maker["name"],
                    "fullName": maker["fullName"],
                },
                "country": {
                    "id": maker["country"]["id"],
                    "name": maker["country"]["name"],
                },
                "continent": {
                    "id": maker["continent"]["id"],
                    "name": maker["continent"]["name"],
                },
                # linking explícito
                "modelId": model["modelId"],
                "makerId": maker["makerId"],
            }
        )

    return continents, countries, makers, cars # devolvemos los documentos creados


# ETAPA 5: conexión, escritura, índices y conteos de MongoDB.
# Definimos la función que migra los datos a MongoDB, insertando o reemplazando documentos según corresponda
def migrate(sql_path: Path, uri: str, drop: bool = True) -> dict[str, int]:
    tables = load_sql_tables(sql_path) #cargamos las tablas desde el sql
    continents, countries, makers, cars = build_documents(tables)

    # creamos la conexión a MongoDB
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[DB_NAME]

# almacenamos los documentos en su respectiva colección
    documents = { 
        "continents": continents,
        "countries": countries,
        "makers": makers,
        "cars": cars,
    }
    for name, items in documents.items():#
        collection = db[name]
        if drop:
            collection.drop()
            if items:
                collection.insert_many(items)
        else:
            for item in items:
                collection.replace_one({"_id": item["_id"]}, item, upsert=True)


# creamos índices para optimizar las consultas
    db.countries.create_index("continentId")
    db.makers.create_index("countryId")
    db.makers.create_index("models.modelId")
    db.cars.create_index("makerId")
    db.cars.create_index("modelId")
    db.cars.create_index("country.name")
    db.cars.create_index("continent.name")
    db.cars.create_index([("year", 1), ("mpg", 1)])

    counts = { #contabilizamos el número de documentos insertados en cada colección
        "continents": db.continents.count_documents({}),
        "countries": db.countries.count_documents({}),
        "makers": db.makers.count_documents({}),
        "models_embedded": sum(len(m["models"]) for m in db.makers.find({}, {"models": 1})),
        "cars": db.cars.count_documents({}),
    }
    client.close()
    return counts

# ETAPA 6: entrada del programa, ejecución y validación final.
# Definimos la función principal que maneja los argumentos de línea de comandos y ejecuta la migración
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrar BDAutosU2.sql a MongoDB")
    parser.add_argument("--sql", type=Path, default=DEFAULT_SQL)
    parser.add_argument("--uri", default=DEFAULT_URI)
    parser.add_argument("--no-drop", action="store_true")
    args = parser.parse_args(argv)

    if not args.sql.exists():
        print(f"No se encontró el SQL: {args.sql}", file=sys.stderr)
        return 1

    # intentamos migrar los datos si no, capturamos cualquier excepción y mostramos el mensaje de error
    try:
        counts = migrate(args.sql, args.uri, drop=not args.no_drop)
    except Exception as exc:  # noqa: BLE001
        print(f"Error de migración: {exc}", file=sys.stderr)
        return 1

    print("Migración completada en base 'bdautos':")
    for key, value in counts.items():
        print(f"  {key}: {value}")
    # verificamos que los conteos sean los esperados si no se muestra un mensaje de advertencia y se retorna un código de error
    expected = { 
        "continents": 5,
        "countries": 17,
        "makers": 20,
        "models_embedded": 42,
        "cars": 138,
    }
    ok = all(counts[k] == expected[k] for k in expected)
    if not ok:
        print("ADVERTENCIA: conteos distintos a los esperados", expected, file=sys.stderr)
        return 2
    print("Conteos verificados OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
