import tkinter as tk
from tkinter import ttk, messagebox


class DokuFrame(ttk.Frame):
    def __init__(self, container, controller, **kwargs):
        super().__init__(container, **kwargs)

        self.controller = controller

        # Relativer Pfad zum "resource"-Ordner, welcher mit dem Build erstellt wird
        doku_datei = "resources\\help.txt"

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        # -- Text für Dokumentation --
        txt_doku = tk.Text(self, height=15)
        txt_doku["state"] = "normal"
        txt_doku.grid(column=0, row=1, sticky="NSEW")

        # -- Scrollbar für Textfeld --
        scl_text = ttk.Scrollbar(self, orient="vertical", command=txt_doku.yview)
        scl_text.grid(column=1, row=1, sticky="NS")
        txt_doku["yscrollcommand"] = scl_text.set

        # -- Doku aus ext. Ressource (Textfile) lesen und anschließend Textfeld sperren --
        try:
            with open(doku_datei, 'r') as file:
                txt_doku.insert(tk.END, file.read())
                txt_doku["state"] = "disabled"  # "normal"
        except FileNotFoundError:
            messagebox.showwarning("Achtung", f"Die Dokumentation konnte nicht geladen werden!")
