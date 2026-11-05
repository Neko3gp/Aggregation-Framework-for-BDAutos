#!/usr/bin/env python3
"""
Interfaz gráfica BDAutos: selecciona y ejecuta las 25 consultas Aggregation,
mostrando el código del pipeline y los datos resultantes.
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from tkinter import messagebox, ttk

os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

import customtkinter as ctk

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from db import get_db  # noqa: E402
from queries import QUERIES, get_query  # noqa: E402
from query_service import (  # noqa: E402
    display_value,
    dumps,
    explain_pipeline,
    run_query,
    summarize_results,
)

# Configuración visual de la aplicación: colores, tema y paneles principales.
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

BG = "#F3F0E8"
SIDEBAR = "#1F2A24"
SIDEBAR_HOVER = "#2C3B33"
ACCENT = "#C45C26"
TEXT = "#1A1A1A"
MUTED = "#5A5A5A"
PANEL = "#FFFFFF"


class BdAutosApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BDAutos — Aggregation Framework")
        self.geometry("1180x720")
        self.minsize(960, 600)
        self.configure(fg_color=BG)

        self.db = None
        self.selected_id: int | None = None
        self._nav_buttons: dict[int, ctk.CTkButton] = {}

        self._build_header()
        self._build_body()
        self._connect()

        if QUERIES:
            self.select_query(QUERIES[0]["id"])

        self.after(100, self._bring_to_front)

    def _bring_to_front(self) -> None:
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        self.focus_force()
        try:
            import subprocess

            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to set frontmost of '
                    'first process whose name contains "Python" to true',
                ],
                check=False,
                capture_output=True,
            )
        except Exception:
            pass

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=BG, height=64, corner_radius=0)
        header.pack(fill="x", padx=18, pady=(14, 6))

        ctk.CTkLabel(
            header,
            text="BDAutos",
            font=ctk.CTkFont(family="Helvetica", size=28, weight="bold"),
            text_color=TEXT,
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="  ·  25 consultas Aggregation (código + resultado)",
            font=ctk.CTkFont(size=14),
            text_color=MUTED,
        ).pack(side="left", pady=(10, 0))

        self.status = ctk.CTkLabel(
            header,
            text="Conectando…",
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
        )
        self.status.pack(side="right")

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(body, fg_color=SIDEBAR, width=300, corner_radius=14)
        side.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        side.grid_propagate(False)

        ctk.CTkLabel(
            side,
            text="Consultas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#F5F5F5",
        ).pack(anchor="w", padx=16, pady=(16, 8))

        self.nav = ctk.CTkScrollableFrame(side, fg_color="transparent")
        self.nav.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        for q in QUERIES:
            btn = ctk.CTkButton(
                self.nav,
                text=f"{q['id']:02d}. {q['title']}",
                anchor="w",
                height=36,
                fg_color="transparent",
                hover_color=SIDEBAR_HOVER,
                text_color="#E8E8E8",
                font=ctk.CTkFont(size=12),
                command=lambda i=q["id"]: self.select_query(i),
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons[q["id"]] = btn

        right = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=14)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=2)
        right.grid_columnconfigure(1, weight=1)
        right.grid_rowconfigure(4, weight=1)
        right.grid_rowconfigure(6, weight=2)

        self.title_lbl = ctk.CTkLabel(
            right,
            text="",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT,
            anchor="w",
            justify="left",
        )
        self.title_lbl.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=18,
            pady=(16, 4),
        )

        self.desc_lbl = ctk.CTkLabel(
            right,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=MUTED,
            anchor="w",
            justify="left",
            wraplength=780,
        )
        self.desc_lbl.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=18,
            pady=(0, 10),
        )

        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=18,
            pady=(0, 8),
        )

        self.meta_lbl = ctk.CTkLabel(
            actions,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
        )
        self.meta_lbl.pack(side="left")

        ctk.CTkButton(
            actions,
            text="Ejecutar consulta",
            width=160,
            height=34,
            fg_color=ACCENT,
            hover_color="#A84C1F",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.execute_selected,
        ).pack(side="right")

        ctk.CTkLabel(
            right,
            text="Código de la consulta (pipeline)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=(18, 10), pady=(4, 2))

        ctk.CTkLabel(
            right,
            text="¿Cómo se construye?",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#234D2A",
            anchor="w",
        ).grid(row=3, column=1, sticky="w", padx=(8, 18), pady=(4, 2))

        self.code_box = ctk.CTkTextbox(
            right,
            font=ctk.CTkFont(family="Menlo", size=12),
            fg_color="#F7F7F4",
            text_color=TEXT,
            corner_radius=10,
            wrap="none",
        )
        self.code_box.grid(
            row=4,
            column=0,
            sticky="nsew",
            padx=(18, 10),
            pady=(0, 10),
        )

        self.education_box = ctk.CTkTextbox(
            right,
            font=ctk.CTkFont(size=13),
            fg_color="#E7F3E8",
            text_color="#234D2A",
            border_width=1,
            border_color="#A8CFAE",
            corner_radius=10,
            wrap="word",
        )
        self.education_box.grid(
            row=4,
            column=1,
            sticky="nsew",
            padx=(8, 18),
            pady=(0, 10),
        )

        ctk.CTkLabel(
            right,
            text="Resultado JSON completo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(
            row=5,
            column=0,
            sticky="w",
            padx=(18, 10),
            pady=(4, 2),
        )

        self.result_box = ctk.CTkTextbox(
            right,
            font=ctk.CTkFont(family="Menlo", size=12),
            fg_color="#EDF4FB",
            text_color="#1D3850",
            border_width=1,
            border_color="#B7CEE3",
            corner_radius=10,
            wrap="none",
        )
        self.result_box.grid(
            row=6,
            column=0,
            sticky="nsew",
            padx=(18, 10),
            pady=(0, 16),
        )

        ctk.CTkLabel(
            right,
            text="Resumen de la respuesta",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3A2D58",
            anchor="w",
        ).grid(
            row=5,
            column=1,
            sticky="w",
            padx=(8, 18),
            pady=(4, 2),
        )

        summary_frame = ctk.CTkFrame(
            right,
            fg_color="#F1ECFA",
            border_width=1,
            border_color="#CFC1E8",
            corner_radius=10,
        )
        summary_frame.grid(
            row=6,
            column=1,
            sticky="nsew",
            padx=(8, 18),
            pady=(0, 16),
        )
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_rowconfigure(2, weight=1)

        self.summary_count = ctk.CTkLabel(
            summary_frame,
            text="Aún no se ha ejecutado la consulta.",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3A2D58",
            anchor="w",
            justify="left",
            wraplength=300,
        )
        self.summary_count.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))

        self.summary_box = ctk.CTkTextbox(
            summary_frame,
            height=64,
            font=ctk.CTkFont(size=12),
            fg_color="#FAF8FE",
            text_color="#493A67",
            border_width=0,
            corner_radius=8,
            wrap="word",
        )
        self.summary_box.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        table_style = ttk.Style(self)
        table_style.configure(
            "BDAutos.Treeview",
            background="#FAF8FE",
            fieldbackground="#FAF8FE",
            foreground="#493A67",
            rowheight=25,
            font=("Helvetica", 11),
        )
        table_style.configure(
            "BDAutos.Treeview.Heading",
            background="#DCCEF0",
            foreground="#3A2D58",
            font=("Helvetica", 11, "bold"),
        )

        table_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        table_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.summary_table = ttk.Treeview(
            table_frame,
            columns=("campo", "valor"),
            show="headings",
            height=7,
            style="BDAutos.Treeview",
        )
        self.summary_table.heading("campo", text="Campo")
        self.summary_table.heading("valor", text="Valor")
        self.summary_table.column("campo", width=105, anchor="w")
        self.summary_table.column("valor", width=190, anchor="w")
        self.summary_table.grid(row=0, column=0, sticky="nsew")

        table_scroll = ctk.CTkScrollbar(
            table_frame,
            orientation="vertical",
            command=self.summary_table.yview,
            fg_color="#E2D8F1",
            button_color="#A995C8",
            button_hover_color="#8D76B1",
            width=12,
        )
        table_scroll.grid(row=0, column=1, sticky="ns")
        self.summary_table.configure(yscrollcommand=table_scroll.set)

        self.summary_table.tag_configure("odd", background="#F8F5FD")
        self.summary_table.tag_configure("even", background="#EEE8F9")

    def _connect(self) -> None:
        try:
            self.db = get_db()
            n = self.db.cars.count_documents({})
            self.status.configure(
                text=f"MongoDB · bdautos · {n} autos",
                text_color="#2F6B3A",
            )
        except Exception as exc:  # noqa: BLE001
            self.db = None
            self.status.configure(text="Sin conexión a MongoDB", text_color="#A11")
            messagebox.showerror(
                "MongoDB",
                "No se pudo conectar a MongoDB en localhost:27017.\n\n"
                "1) brew services start mongodb-community\n"
                "2) .venv/bin/python scripts/migrate.py\n\n"
                f"{exc}",
            )

    def select_query(self, query_id: int) -> None:
        q = get_query(query_id)
        self.selected_id = query_id

        for qid, btn in self._nav_buttons.items():
            if qid == query_id:
                btn.configure(fg_color=SIDEBAR_HOVER, text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#E8E8E8")

        self.title_lbl.configure(text=f"Consulta {q['id']}: {q['title']}")
        self.desc_lbl.configure(text=q["description"])
        self.meta_lbl.configure(text=f"Colección: {q['collection']}")

        self.code_box.configure(state="normal")
        self.code_box.delete("1.0", "end")
        self.code_box.insert("1.0", dumps(q["pipeline"]))
        self.code_box.configure(state="disabled")

        self.education_box.configure(state="normal")
        self.education_box.delete("1.0", "end")
        self.education_box.insert("1.0", explain_pipeline(q["pipeline"]))
        self.education_box.configure(state="disabled")

        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert(
            "1.0",
            "Pulsa «Ejecutar consulta» para ver los datos resultantes.",
        )
        self.result_box.configure(state="disabled")
        self._reset_summary()

    def _reset_summary(self) -> None:
        self.summary_count.configure(text="Aún no se ha ejecutado la consulta.")
        self.summary_box.configure(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("1.0", "Aquí aparecerá una lectura rápida de la respuesta.")
        self.summary_box.configure(state="disabled")
        for item in self.summary_table.get_children():
            self.summary_table.delete(item)

    def _update_summary(self, results: list[dict]) -> None:
        self.summary_count.configure(
            text=f"{len(results)} documento{'s' if len(results) != 1 else ''} devuelto{'s' if len(results) != 1 else ''}"
        )
        self.summary_box.configure(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("1.0", summarize_results(results))
        self.summary_box.configure(state="disabled")

        for item in self.summary_table.get_children():
            self.summary_table.delete(item)
        if results and isinstance(results[0], dict):
            for index, (field, value) in enumerate(results[0].items()):
                self.summary_table.insert(
                    "",
                    "end",
                    values=(field, display_value(value)),
                    tags=("even" if index % 2 == 0 else "odd",),
                )

    def execute_selected(self) -> None:
        if self.selected_id is None:
            return
        if self.db is None:
            self._connect()
            if self.db is None:
                return

        q = get_query(self.selected_id)
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "Ejecutando…")
        self.result_box.configure(state="disabled")
        self.update_idletasks()

        try:
            results = run_query(self.db, q)
            text = dumps(results)
            footer = f"\n\n# Documentos devueltos: {len(results)}"
            self.result_box.configure(state="normal")
            self.result_box.delete("1.0", "end")
            self.result_box.insert("1.0", text + footer)
            self.result_box.configure(state="disabled")
            self._update_summary(results)
            self.status.configure(
                text=f"OK · Q{q['id']} · {len(results)} docs",
                text_color="#2F6B3A",
            )
        except Exception:  # noqa: BLE001
            err = traceback.format_exc()
            self.result_box.configure(state="normal")
            self.result_box.delete("1.0", "end")
            self.result_box.insert("1.0", err)
            self.result_box.configure(state="disabled")
            self._reset_summary()
            self.summary_count.configure(text="No se pudo generar el resumen.")
            self.status.configure(text="Error al ejecutar", text_color="#A11")


def main() -> int:
    app = BdAutosApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
