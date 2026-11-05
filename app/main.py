#!/usr/bin/env python3
"""
Punto de entrada de la aplicación BDAutos.
Por defecto abre la interfaz gráfica (CustomTkinter).

Uso:
  .venv/bin/python app/main.py          # GUI
  .venv/bin/python app/gui.py           # GUI (directo)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Silencia el aviso de deprecación de Tk del sistema en macOS
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

APP_DIR = Path(__file__).resolve().parent # directorio de la aplicación
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))



def main() -> int: # función principal que inicia la aplicación
    from gui import main as gui_main

    return gui_main() #iniciando la interfaz


if __name__ == "__main__":
    raise SystemExit(main())
