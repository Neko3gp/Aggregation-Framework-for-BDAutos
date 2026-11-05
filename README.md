# Proyecto 2a. Evaluación — BDAutos en MongoDB

Universidad Autónoma de Chihuahua · Bases de Datos Avanzado  
Aplicación del **Aggregation Framework** sobre la base **Autos**.

## Requisitos cubiertos

1. Diseño documental con **embedding** y **linking**
2. Migración desde `data/BDAutosU2.sql`
3. **25 consultas** Aggregation
4. **App Python con interfaz gráfica** que muestra código de consulta + resultado
5. Código y scripts necesarios para ejecutar el proyecto

## Estructura

```
Proyecto-2a.-Evaluaci-n/
  data/BDAutosU2.sql
  scripts/migrate.py
  scripts/02_consultas.js
  scripts/export_consultas_js.py
  app/main.py · gui.py · query_service.py
  app/queries.py · db.py · requirements.txt
  docker-compose.yml
  README.md
```

## Requisitos de entorno

- **Python 3.12 de Homebrew** (con Tk): `brew install python@3.12 python-tk@3.12`  
  No uses el Python del sistema (`/usr/bin/python3`): en macOS la ventana Tk no aparece.
- Docker Desktop con soporte para `docker compose`

## Puesta en marcha

```bash
cd Proyecto-2a.-Evaluaci-n
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r app/requirements.txt

# Iniciar MongoDB y migrar datos (persistente en un volumen Docker)
docker compose up -d --wait mongodb
.venv/bin/python scripts/migrate.py

# App con interfaz gráfica
# Este script también inicia MongoDB y sincroniza los datos automáticamente.
./iniciar.sh
# o: .venv/bin/python app/main.py

# Consultas en mongosh (opcional)
mongosh scripts/02_consultas.js

# Detener MongoDB (los datos permanecen en el volumen)
docker compose down

# Eliminar también los datos persistidos, si se desea empezar de cero
docker compose down -v

```

## Flujo de trabajo

El proyecto separa el arranque, la conexión, las consultas y la presentación:

```text
┌────────────────────┐
│     iniciar.sh     │  Inicia Docker, MongoDB y la migración
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  scripts/migrate.py│  Lee el SQL y construye documentos MongoDB
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│      MongoDB       │  Guarda continentes, países, fabricantes y autos
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│     app/main.py    │  Punto de entrada de la aplicación
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│      app/gui.py    │  Construye la ventana y recibe las acciones
└──────┬─────┬───────┘
       │     │
       │     └──────────────────────────────┐
       ▼                                    ▼
┌───────────────┐                    ┌─────────────────────┐
│ app/db.py     │                    │ app/queries.py      │
│ Conecta con   │                    │ Contiene los 25     │
│ MongoDB       │                    │ pipelines           │
└──────┬────────┘                    └──────────┬──────────┘
       └──────────────────┬────────────────────┘
                          ▼
                 ┌─────────────────────┐
                 │ app/query_service.py│
                 │ Ejecuta y procesa   │
                 │ las consultas       │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │      app/gui.py     │
                 │ Muestra código,     │
                 │ explicación y datos │
                 └─────────────────────┘
```

### Responsabilidad de cada archivo Python

- **`app/main.py`**: inicia la aplicación gráfica.
- **`app/gui.py`**: controla la ventana, botones, paneles, tabla y eventos del usuario.
- **`app/db.py`**: centraliza la conexión y validación de MongoDB.
- **`app/queries.py`**: contiene la definición de las 25 consultas Aggregation.
- **`app/query_service.py`**: ejecuta los pipelines y prepara el JSON, las explicaciones y los resúmenes que muestra la interfaz.
- **`scripts/migrate.py`**: lee `data/BDAutosU2.sql`, transforma sus registros y los guarda en MongoDB.
- **`scripts/export_consultas_js.py`**: genera el archivo JavaScript de consultas a partir de `app/queries.py`.

Cuando el usuario selecciona una consulta, `gui.py` obtiene su definición desde `queries.py`. Al ejecutarla, `query_service.py` usa la conexión de `db.py`, envía el pipeline a MongoDB y devuelve los resultados preparados para los paneles de la interfaz.

## Modelo rápido

| Colección | Embedding | Linking |
|-----------|-----------|---------|
| `continents` | — | target |
| `countries` | snapshot continente | `continentId` |
| `makers` | `models[]` + geo | `countryId` |
| `cars` | specs + snapshots | `makerId`, `modelId` |
