import tkinter as tk
from tkinter import ttk


class EinstellungenFrame(ttk.Frame):
    def __init__(self, container, controller, **kwargs):
        super().__init__(container, **kwargs)

        self.controller = controller

        # Variablen für Diagramme
        self.y_lim_drehmoment_einst = tk.IntVar()
        self.y_lim_temperatur_einst = tk.IntVar()

        # -- Frame 1 für die Einstellungen der Diagramme
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)

        lbl_einst_analyse = ttk.Label(self, text="Einstellungen für Analyse", font=("Helvetica", 11, "bold"))
        lbl_einst_analyse.grid(column=0, row=0, sticky="W")

        self.frm_analyse = ttk.Frame(self, relief="groove", borderwidth=2)
        self.frm_analyse.grid(column=0, row=1, pady=(0, 20), sticky="NSEW")
        self.frm_analyse.columnconfigure(2, weight=1)
        self.frm_analyse.rowconfigure(1, weight=0)
        self.frm_analyse.rowconfigure(2, weight=0)
        self.frm_analyse.rowconfigure(3, weight=0)

        self.lbl_drehmoment = ttk.Label(self.frm_analyse, text="Bereich für Y-Achse Drehmoment [+/- Nm]")
        self.lbl_drehmoment.grid(column=0, row=0, padx=20, pady=(20, 10), sticky="W")
        self.sb_y_lim_drehmoment = ttk.Spinbox(self.frm_analyse, width=6, textvariable=self.y_lim_drehmoment_einst,
                                               justify=tk.CENTER, from_=100, to=500, increment=10)
        self.sb_y_lim_drehmoment.grid(column=1, row=0, pady=(15, 10), sticky="EW")
        # Setzen mit initialem Wert
        self.sb_y_lim_drehmoment.set(value=300)

        self.lbl_temperatur = ttk.Label(self.frm_analyse, text="Bereich für Y-Achse Temperatur [+/- Nm]")
        self.lbl_temperatur.grid(column=0, row=1, padx=20, pady=(10, 20), sticky="W")
        self.sb_y_lim_temperatur = ttk.Spinbox(self.frm_analyse, width=6, textvariable=self.y_lim_temperatur_einst,
                                               justify=tk.CENTER, from_=50, to=200, increment=10)
        self.sb_y_lim_temperatur.grid(column=1, row=1, pady=(10, 15), sticky="EW")
        # Setzen mit initialem Wert
        self.sb_y_lim_temperatur.set(value=120)

        lbl_einst_bericht = ttk.Label(self, text="Einstellungen für Bericht", font=("Helvetica", 11, "bold"))
        lbl_einst_bericht.grid(column=0, row=2, sticky="W")

        self.frm_bericht = ttk.Frame(self, relief="groove", borderwidth=2)
        self.frm_bericht.grid(column=0, row=3, pady=(0, 20), sticky="NSEW")
        self.lbl_todo = ttk.Label(self.frm_bericht, text="Aktuelle sind noch keine Einstellungen verfügbar.")
        self.lbl_todo.grid(column=0, row=0, padx=20, pady=(20, 10), sticky="W")
