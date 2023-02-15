import tkinter as tk
from tkinter import ttk, messagebox


class DokuFrame(ttk.Frame):
    def __init__(self, container, controller, **kwargs):
        super().__init__(container, **kwargs)

        self.controller = controller

        # Relativer Pfad zum "resource"-Ordner, welcher mit dem Build erstellt wird
        doku_datei = "C:\\Users\\Familie_Kersten\\PycharmProjects\\driveAnalyzer\\resources\\help.txt"
        # resources\\help.txt
        # C:\\Users\\Familie_Kersten\\PycharmProjects\\driveAnalyzer\\resources\\help.txt

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        # -- Text für Dokumentation --
        txt_doku = tk.Text(self, height=15, wrap=tk.WORD)
        txt_doku["state"] = "normal"
        txt_doku.grid(column=0, row=1, sticky="NSEW")

        # -- Scrollbar für Textfeld --
        scl_text = ttk.Scrollbar(self, orient="vertical", command=txt_doku.yview)
        scl_text.grid(column=1, row=1, sticky="NS")
        txt_doku["yscrollcommand"] = scl_text.set

        # -- Doku aus ext. Ressource (Textfile) lesen und anschließend Textfeld sperren --
        try:
            with open(doku_datei, 'r', encoding='utf-8') as file:
                doku = file.read()
                txt_doku.insert(tk.END, doku)
                txt_doku["state"] = "disabled"  # "normal"
        except FileNotFoundError:
            messagebox.showwarning("Achtung", f"Die Dokumentation konnte nicht geladen werden!")
