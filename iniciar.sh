# Lanza la interfaz gráfica de BDAutos
set -euo pipefail
cd "$(dirname "$0")"

export TK_SILENCE_DEPRECATION=1

if ! command -v docker >/dev/null 2>&1; then #verificación del comando docker
  echo "Docker no está instalado o no está disponible en PATH." >&2
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then #verificación de entorno virtual
  echo "No hay .venv. Créalo con:"
  echo "  /opt/homebrew/bin/python3.12 -m venv .venv"
  echo "  .venv/bin/pip install -r app/requirements.txt"
  exit 1
fi
#################################################################
echo "Iniciando MongoDB con Docker Compose..." # Inicia MongoDB en segundo plano
docker compose up -d --wait mongodb

echo "Sincronizando datos de BDAutos..."
.venv/bin/python scripts/migrate.py --no-drop

# Trae Python al frente en macOS (evita ventana invisible detrás del Terminal)
osascript >/dev/null 2>&1 <<'APPLESCRIPT' || true
tell application "System Events"
  set procs to (every process whose name contains "Python")
  repeat with p in procs
    try
      set frontmost of p to true
    end try
  end repeat
end tell
APPLESCRIPT

exec .venv/bin/python app/main.py #
