import threading
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import AutoMinorLocator
from nptdms import TdmsFile
from app import MessungInfo
from RangeSlider.RangeSlider import RangeSliderH


class AnalyseFrame(ttk.Frame):
    def __init__(self, container, controller, **kwargs):
        super().__init__(container, **kwargs)

        self.controller = controller
        self.l_channels_zyklus = []
        channels_zyklus_str = tk.StringVar(value=self.l_channels_zyklus.sort())
        self.l_channels_analog = []
        channels_analog_str = tk.StringVar(value=self.l_channels_analog.sort())

        self.messung_analyse = MessungInfo()

        # Variablen für Einstellungen, gesetzt mit Default Werten
        self.achse_lim_drehmoment = tk.IntVar()
        self.achse_lim_temperatur = tk.IntVar()

        # Variablen für Check buttons
        self.check_var_min = tk.IntVar(value=1)
        self.check_var_max = tk.IntVar(value=1)
        # Variablen für Range
        self.slider_var_left = tk.IntVar()  # min Zyklen gewählt
        self.slider_var_right = tk.IntVar()  # max Zyklen gewählt
        # Variablen für RadioButton
        self.rb_variable = tk.IntVar()
        rb_values = {"1": 1,
                     "2": 2,
                     "3": 3}
        # Variablen für Spin-boxes zur Eingabe der Zyklen
        self.sb_1_v_von = tk.IntVar()
        self.sb_1_v_bis = tk.IntVar()
        self.sb_2_v_von = tk.IntVar()
        self.sb_2_v_bis = tk.IntVar()
        self.sb_3_v_von = tk.IntVar()
        self.sb_3_v_bis = tk.IntVar()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)

        lbl_zyk_name = ttk.Label(self, text="Auswertung Zyklen", font=("Helvetica", 11, "bold"))
        lbl_zyk_name.grid(column=0, row=0, sticky="W")

        # -- Frame 1: Darstellung über Zyklen --
        self.frm_zyklen = ttk.Frame(self, relief="groove", borderwidth=2)
        self.frm_zyklen.grid(column=0, row=1, pady=(0, 20), sticky="NSEW")
        self.frm_zyklen.columnconfigure(2, weight=1)
        self.frm_zyklen.rowconfigure(1, weight=0)
        self.frm_zyklen.rowconfigure(2, weight=1)
        self.frm_zyklen.rowconfigure(3, weight=0)
        lbl_channels_zyklen = ttk.Label(self.frm_zyklen, text="Verfügbare Messkanäle")
        lbl_channels_zyklen.grid(column=0, row=0, padx=10, pady=(5, 0), sticky="W")
        self.zyklen_liste = tk.Listbox(self.frm_zyklen, selectmode=tk.EXTENDED, width=30,
                                       listvariable=channels_zyklus_str, height=8)
        self.zyklen_liste.grid(column=0, row=1, rowspan=3, padx=(10, 0), pady=(0, 10), sticky="NSEW")
        # self.zyklen_liste.bind("<<ListboxSelect>>", handle_listbox_selection)
        list_zyk_scroll = ttk.Scrollbar(self.frm_zyklen, orient="vertical", command=self.zyklen_liste.yview)
        list_zyk_scroll.grid(column=1, row=1, rowspan=3, padx=(0, 10), pady=(0, 10), sticky="NSW")
        self.zyklen_liste["yscrollcommand"] = list_zyk_scroll.set
        # Frame für Auswahl der Zyklen
        lbl_auswahl = ttk.Label(self.frm_zyklen, text="Auswertebereich für Zyklen")
        lbl_auswahl.grid(column=2, row=1, padx=20, pady=(0, 0), sticky="NW")
        self.frm_auswahl = ttk.Frame(self.frm_zyklen, relief="groove", borderwidth=2)
        self.frm_auswahl.grid(column=2, row=2, padx=20, pady=5, sticky="NSEW")
        self.frm_auswahl.columnconfigure(0, weight=1)
        self.frm_auswahl.rowconfigure(0, weight=1)
        self.rs_zyklen = RangeSliderH(self.frm_auswahl, [self.slider_var_left, self.slider_var_right],
                                      digit_precision=".0f", Width=420, Height=50, padX=30, font_size=10, max_val=1,
                                      show_value=True, bgColor="#f0f0f0", line_s_color="#0f0f0f")
        self.rs_zyklen.grid(column=0, row=0, sticky="EW")

        frm_check_buttons = ttk.Frame(self.frm_zyklen)
        frm_check_buttons.grid(column=2, row=3, padx=(20, 20), sticky="SW")
        self.check_button_min = ttk.Checkbutton(frm_check_buttons, text="MIN", variable=self.check_var_min,
                                                command=self._check_btn_zyklen, offvalue=0, onvalue=1)
        self.check_button_min.grid(column=0, row=0, padx=(0, 0), pady=(10, 10), sticky="NSW")
        # self.check_button_min["state"] = "disabled"
        self.check_button_max = ttk.Checkbutton(frm_check_buttons, text="MAX", variable=self.check_var_max,
                                                command=self._check_btn_zyklen, offvalue=0, onvalue=1)
        self.check_button_max.grid(column=1, row=0, sticky="NSW", padx=(5, 0))

        self.btn_plot_zyklen = ttk.Button(self.frm_zyklen, text="Diagramm erstellen", width=20,
                                          command=lambda: threading.Thread(
                                              target=self._plot_zyklen_background_task).start())
        self.btn_plot_zyklen.grid(column=2, row=3, padx=(0, 20), pady=(10, 10), sticky="SE")

        # -- Frame 2: Darstellung der analogen Messwerte
        lbl_analog_name = ttk.Label(self, text="Auswertung Analog", font=("Helvetica", 11, "bold"))
        lbl_analog_name.grid(column=0, row=2, sticky="W")
        self.frm_analog = ttk.Frame(self, relief="groove", borderwidth=2)
        self.frm_analog.grid(column=0, row=3, pady=(0, 2), sticky="NSEW")
        self.frm_analog.columnconfigure(1, weight=0)
        self.frm_analog.columnconfigure(2, weight=1)
        self.frm_analog.rowconfigure(0, weight=0)
        self.frm_analog.rowconfigure(1, weight=1)
        self.frm_analog.rowconfigure(2, weight=0)
        lbl_channels_analog = ttk.Label(self.frm_analog, text="Verfügbare Messkanäle")
        lbl_channels_analog.grid(column=0, row=0, padx=10, pady=(5, 0), sticky="W")
        self.analog_liste = tk.Listbox(self.frm_analog, selectmode=tk.EXTENDED, width=30,
                                       listvariable=channels_analog_str, height=4)
        self.analog_liste.grid(column=0, row=1, rowspan=2, padx=(10, 0), pady=(0, 10), sticky="NSEW")
        list_ana_scroll = ttk.Scrollbar(self.frm_analog, orient="vertical", command=self.analog_liste.yview)
        list_ana_scroll.grid(column=1, row=1, rowspan=2, padx=(0, 10), pady=(0, 10), sticky="NSW")
        self.analog_liste["yscrollcommand"] = list_ana_scroll.set
        # Frame für Bereiche
        frm_bereiche = ttk.Frame(self.frm_analog)
        frm_bereiche.grid(column=2, row=1, padx=20, sticky="NSEW")
        frm_bereiche.columnconfigure(0, weight=1)
        # Frame für RadioButtons innerhalb im Frame Bereiche
        frm_radio_button = ttk.Frame(frm_bereiche)
        frm_radio_button.grid(column=0, row=0, sticky="EW")
        lbl_analog_bereiche = ttk.Label(frm_radio_button, text="Anzahl der Bereiche:")
        lbl_analog_bereiche.grid(column=0, row=0, sticky="EW")
        # RadioButtons
        for (text, value) in rb_values.items():
            ttk.Radiobutton(frm_radio_button, text=text, variable=self.rb_variable, value=value,
                            command=self._enable_disable_bereiche).grid(column=value, row=0, padx=(10, 0))
        self.rb_variable.set(1)
        # Frames für Bereiche der Auswertung innerhalb Frame Bereiche
        frm_bereich_1 = ttk.Frame(frm_bereiche, relief="groove", borderwidth=2)
        frm_bereich_1.grid(column=0, row=1, pady=5, sticky="NSEW")
        lbl_bereich_1_zyklen = ttk.Label(frm_bereich_1, text="Zyklen")
        lbl_bereich_1_zyklen.grid(column=0, row=0, padx=(10, 10), pady=5)
        self.sb_bereiche_1_von = ttk.Spinbox(frm_bereich_1, width=8, textvariable=self.sb_1_v_von, justify=tk.CENTER)
        self.sb_bereiche_1_von.grid(column=1, row=0)
        lbl_bereiche_1_bis = ttk.Label(frm_bereich_1, text="bis")
        lbl_bereiche_1_bis.grid(column=2, row=0, padx=10)
        self.sb_bereiche_1_bis = ttk.Spinbox(frm_bereich_1, width=8, textvariable=self.sb_1_v_bis, justify=tk.CENTER)
        self.sb_bereiche_1_bis.grid(column=3, row=0)
        lbl_bereiche_1_comment = ttk.Label(frm_bereich_1, text="werden dargestellt.")
        lbl_bereiche_1_comment.grid(column=4, row=0, padx=10)

        frm_bereich_2 = ttk.Frame(frm_bereiche, relief="groove", borderwidth=1)
        frm_bereich_2.grid(column=0, row=2, pady=5, sticky="NSEW")
        lbl_bereich_2_zyklen = ttk.Label(frm_bereich_2, text="Zyklen")
        lbl_bereich_2_zyklen.grid(column=0, row=0, padx=(10, 10), pady=5)
        self.sb_bereiche_2_von = ttk.Spinbox(frm_bereich_2, width=8, textvariable=self.sb_2_v_von, justify=tk.CENTER)
        self.sb_bereiche_2_von.grid(column=1, row=0)
        lbl_bereiche_2_bis = ttk.Label(frm_bereich_2, text="bis")
        lbl_bereiche_2_bis.grid(column=2, row=0, padx=10)
        self.sb_bereiche_2_bis = ttk.Spinbox(frm_bereich_2, width=8, textvariable=self.sb_2_v_bis, justify=tk.CENTER)
        self.sb_bereiche_2_bis.grid(column=3, row=0)
        lbl_bereiche_2_comment = ttk.Label(frm_bereich_2, text="werden dargestellt.")
        lbl_bereiche_2_comment.grid(column=4, row=0, padx=10)
        self.frm_bereich_2_blank = ttk.Frame(frm_bereiche)
        self.frm_bereich_2_blank.grid(column=0, row=2, pady=0, sticky="NSEW")

        frm_bereich_3 = ttk.Frame(frm_bereiche, relief="groove", borderwidth=1)
        frm_bereich_3.grid(column=0, row=3, pady=5, sticky="NSEW")
        lbl_bereich_3_zyklen = ttk.Label(frm_bereich_3, text="Zyklen")
        lbl_bereich_3_zyklen.grid(column=0, row=0, padx=(10, 10), pady=5)
        self.sb_bereiche_3_von = ttk.Spinbox(frm_bereich_3, width=8, textvariable=self.sb_3_v_von, justify=tk.CENTER)
        self.sb_bereiche_3_von.grid(column=1, row=0)
        lbl_bereiche_3_bis = ttk.Label(frm_bereich_3, text="bis")
        lbl_bereiche_3_bis.grid(column=2, row=0, padx=10)
        self.sb_bereiche_3_bis = ttk.Spinbox(frm_bereich_3, width=8, textvariable=self.sb_3_v_bis, justify=tk.CENTER)
        self.sb_bereiche_3_bis.grid(column=3, row=0)
        lbl_bereiche_3_comment = ttk.Label(frm_bereich_3, text="werden dargestellt.")
        lbl_bereiche_3_comment.grid(column=4, row=0, padx=10)
        self.frm_bereich_3_blank = ttk.Frame(frm_bereiche)
        self.frm_bereich_3_blank.grid(column=0, row=3, pady=0, sticky="NSEW")
        # Button für die Erstellung der Diagramme
        self.btn_plot_analog = ttk.Button(self.frm_analog, text="Diagramm erstellen", width=20,
                                          command=lambda: threading.Thread(
                                              target=self._plot_analog_background_task).start())
        self.btn_plot_analog.grid(column=2, row=2, padx=(0, 20), pady=(10, 10), sticky="SE")

    def update_frm(self, messung: MessungInfo):
        # Frame leeren
        self.clear_frm()
        # Frame neu befüllen → Objekt der Messung übernehmen
        self.messung_analyse = messung
        # -- Frame für Zyklen --
        # Erzeugen vom RS und Setzen des "max_val" mit Zyklen aus Messung
        # nicht möglich in "__init__", da "max_val" nicht dynamisch geändert werden kann!
        # RS-Objekte werden dann vom GarbageCollector zerstört
        self.rs_zyklen = RangeSliderH(self.frm_auswahl, [self.slider_var_left, self.slider_var_right],
                                      digit_precision=".0f", Width=420, Height=50, padX=30, font_size=10,
                                      max_val=messung.zyklen, show_value=True,
                                      bgColor="#f0f0f0", line_s_color="#0f0f0f")
        self.rs_zyklen.grid(column=0, row=0, sticky="EW")
        # Funktion zum Befüllen der Liste, je nach Auswahl
        self._check_btn_zyklen()

        # -- Frame für analog Kanäle --
        # Kanäle der Gruppe Analog
        for n in range(0, len(self.messung_analyse.channels_analog)):
            self.analog_liste.insert(tk.END, self.messung_analyse.channels_analog[n])
        # Kanäle der Gruppe Temperatur
        for m in range(0, len(self.messung_analyse.channels_temp)):
            self.analog_liste.insert(tk.END, self.messung_analyse.channels_temp[m])

        # Eingabe für Zyklen (Bereiche der Auswertung) vorausfüllen
        self.sb_bereiche_1_von.config(from_=1, to=self.messung_analyse.zyklen, increment=1)
        self.sb_1_v_von.set(value=1)
        self.sb_bereiche_1_bis.config(from_=1, to=self.messung_analyse.zyklen, increment=1)
        if self.messung_analyse.zyklen < 5:
            self.sb_1_v_bis.set(value=self.messung_analyse.zyklen)
        else:
            self.sb_1_v_bis.set(value=5)
        self.sb_bereiche_2_von.config(from_=1, to=self.messung_analyse.zyklen, increment=1)
        self.sb_2_v_von.set(value=round(self.messung_analyse.zyklen / 2))
        self.sb_bereiche_2_bis.config(from_=1, to=self.messung_analyse.zyklen, increment=1)
        self.sb_2_v_bis.set(value=round(self.messung_analyse.zyklen / 2) + 4)
        self.sb_bereiche_3_von.config(from_=1, to=self.messung_analyse.zyklen, increment=1)
        self.sb_3_v_von.set(value=self.messung_analyse.zyklen - 4)
        self.sb_bereiche_3_bis.config(from_=1, to=self.messung_analyse.zyklen, increment=1)
        self.sb_3_v_bis.set(value=self.messung_analyse.zyklen)

    def clear_frm(self):
        self.zyklen_liste.delete(0, tk.END)
        self.analog_liste.delete(0, tk.END)
        self.messung_analyse = MessungInfo()

    def _check_btn_zyklen(self):
        # -- Kanäle Zyklen --
        # Default: MIN und MAX Kanäle sind deaktiviert
        self.zyklen_liste.delete(0, tk.END)
        # nur MAX Kanäle sind gewählt
        if self.check_var_min.get() == 0 and self.check_var_max.get() == 1:
            for n in range(0, len(self.messung_analyse.channels_zyklus)):
                if "max" in self.messung_analyse.channels_zyklus[n].lower():
                    self.zyklen_liste.insert(tk.END, self.messung_analyse.channels_zyklus[n])
        # Nir MIN Kanäle sind gewählt
        elif self.check_var_min.get() == 1 and self.check_var_max.get() == 0:
            for n in range(0, len(self.messung_analyse.channels_zyklus)):
                if "min" in self.messung_analyse.channels_zyklus[n].lower():
                    self.zyklen_liste.insert(tk.END, self.messung_analyse.channels_zyklus[n])
        # MIN und MAX Kanäle sind gewählt
        elif self.check_var_min.get() == 1 and self.check_var_max.get() == 1:
            for n in range(0, len(self.messung_analyse.channels_zyklus)):
                self.zyklen_liste.insert(tk.END, self.messung_analyse.channels_zyklus[n])

    def _plot_zyklen_background_task(self):
        # Objekt der Messung speichern, falls während der Analyse ein neues Objekt (Messung)
        # dem Frame übergeben wird.
        messung_analyse_zyklen = self.messung_analyse

        # Buttons für weitere Diagramme sperren
        self.btn_plot_zyklen["state"] = tk.DISABLED
        self.btn_plot_analog["state"] = tk.DISABLED
        # die ausgewählten Kanäle für die zwei Diagramme aufteilen und in Listen erfassen
        liste_temperaturen = []
        liste_t_n = []
        if self.zyklen_liste.curselection() != ():
            for i in self.zyklen_liste.curselection():
                if "drehmoment" in self.zyklen_liste.get(i).lower() or "drehzahl" in self.zyklen_liste.get(i).lower():
                    liste_t_n.append(self.zyklen_liste.get(i))
                else:
                    liste_temperaturen.append(self.zyklen_liste.get(i))

            try:
                # Statusbar triggern
                self.controller.status_verarbeiten()
                with TdmsFile.open(messung_analyse_zyklen.pfad) as tdms_file:
                    # Informationen aus Messung holen und im Objekt speichern
                    group_zyklus = tdms_file["Zyklus"]
                    # Da die Zyklen für die x-Achse öfter verwendet werden
                    data_zyklus = group_zyklus["Zyklus"][self.slider_var_left.get():self.slider_var_right.get()]
                    # -- Diagramm mit ein oder zwei Abbildungen erstellen, je nach gewählter Kanäle --
                    if liste_temperaturen and liste_t_n:
                        fig, (t_n, temp) = plt.subplots(nrows=2)
                        fig.set_figwidth(12)
                        fig.set_figheight(7)
                    elif liste_temperaturen and not liste_t_n:
                        fig, (temp) = plt.subplots(nrows=1)
                        fig.set_figwidth(12)
                        fig.set_figheight(4)
                    else:
                        fig, (t_n) = plt.subplots(nrows=1)
                        fig.set_figwidth(12)
                        fig.set_figheight(4)
                    # Titel mit Name der Messung
                    fig.suptitle(messung_analyse_zyklen.name, fontsize=12)
                    # subplot für Drehzahl/Drehmoment
                    if liste_t_n:
                        for n in liste_t_n:
                            t_n.plot(data_zyklus,
                                     group_zyklus[n][self.slider_var_left.get():self.slider_var_right.get()],
                                     label=n)

                        t_n.set_title(f"Drehmoment und Drehzahl für {str(len(data_zyklus))} Zyklen",
                                      fontweight="bold", size=11)
                        t_n.set_xlabel("Zyklus", fontsize=10)
                        t_n.set_ylabel("Drehmoment [Nm]\nDrehzahl [1/min]", fontsize=10)
                        t_n.set_ylim(-self.achse_lim_drehmoment.get(), self.achse_lim_drehmoment.get())
                        t_n.set_yticks(range(-self.achse_lim_drehmoment.get(), self.achse_lim_drehmoment.get(), 20))

                        # Teilstriche und Legende hinzufügen
                        t_n.minorticks_on()
                        t_n.yaxis.set_minor_locator(AutoMinorLocator(2))
                        t_n.legend(prop={"size": 10})
                        t_n.grid()
                        t_n.grid(which="minor", linestyle='--')

                    # subplot für Temperaturen
                    if liste_temperaturen:
                        for m in liste_temperaturen:
                            temp.plot(data_zyklus, group_zyklus[m][
                                                   self.slider_var_left.get():self.slider_var_right.get()],
                                      label=m)
                        # Ausgestaltung vom Diagramm
                        temp.set_title(f"Temperaturen für {str(len(data_zyklus))} Zyklen", fontweight="bold",
                                       size=11)
                        temp.set_xlabel("Zyklus", fontsize=10)
                        temp.set_ylabel("Temperatur [°C]", fontsize=10)
                        temp.set_ylim(20, self.achse_lim_temperatur.get())
                        temp.set_yticks(range(20, self.achse_lim_temperatur.get(), 5))
                        # Teilstriche und Legende hinzufügen
                        temp.minorticks_on()
                        temp.yaxis.set_minor_locator(AutoMinorLocator(5))
                        temp.legend(prop={"size": 10})
                        temp.grid()
                        temp.grid(which="minor", linestyle='--')

                # Schließen der TDMS-Datei
                tdms_file.close()
                # Statusbar auf OK setzen
                self.controller.status_ok()
                # Diagramme einpassen und anzeigen
                fig.tight_layout()
                # Diagramm in neuem Fenster darstellen
                self._plot_in_window(fig)

                # plt.show()

            except FileNotFoundError:
                messagebox.showerror("Error", f"Die Datei {messung_analyse_zyklen.pfad} wurde nicht gefunden oder "
                                              f"konnte nicht verarbeitet werden!")
        else:
            messagebox.showwarning("Achtung", "Es wurde kein Kanal für die Darstellung ausgewählt!")

        # Buttons wieder freigeben
        self.btn_plot_zyklen["state"] = tk.NORMAL
        self.btn_plot_analog["state"] = tk.NORMAL

    def _plot_analog_background_task(self):
        # -- Funktion zum Plotten der Diagramme für analoge Messdaten --
        # die ausgewählten Kanäle für die zwei Diagramme aufteilen und in Listen erfassen

        # Objekt der Messung speichern, falls während der Analyse ein neues Objekt (Messung)
        # dem Frame übergeben wird.
        messung_analyse_analog = self.messung_analyse

        liste_temperaturen = []
        liste_t_n = []
        if self.analog_liste.curselection() != ():
            for k in self.analog_liste.curselection():
                if "drehmoment" in self.analog_liste.get(k).lower() or "drehzahl" in self.analog_liste.get(k).lower():
                    liste_t_n.append(self.analog_liste.get(k))
                else:
                    liste_temperaturen.append(self.analog_liste.get(k))

            # Vorgaben für die Bereiche in Listen (tuples) speichern, falls die Eingaben valide sind
            if self._validate_spin_box_input():
                # Für Berechnung der Bereiche
                zyklen_von = (self.sb_1_v_von.get(), self.sb_2_v_von.get(), self.sb_3_v_von.get() - 1)
                zyklen_bis = (self.sb_1_v_bis.get() + 1, self.sb_2_v_bis.get() + 1, self.sb_3_v_bis.get())
                # Für Legende
                zyklen_von_legende = (self.sb_1_v_von.get(), self.sb_2_v_von.get(), self.sb_3_v_von.get())
                zyklen_bis_legende = (self.sb_1_v_bis.get(), self.sb_2_v_bis.get(), self.sb_3_v_bis.get())
            else:
                messagebox.showwarning("Achtung", f"Bitte Eingaben für die Zyklen korrigieren. \n"
                                                  f"Es sind nur Zyklen von 1 bis {messung_analyse_analog.zyklen} gültig.")
                return

            # Buttons für weitere Diagramme sperren
            self.btn_plot_zyklen["state"] = tk.DISABLED
            self.btn_plot_analog["state"] = tk.DISABLED
            # Lesen und speichern der gewünschten Anzahl der Bereiche/Diagramme -> falls nachträglich
            # vom Benutzer geändert!
            anzahl_diagramme = self.rb_variable.get()

            try:
                # Statusbar triggern
                self.controller.status_verarbeiten()
                with TdmsFile.open(messung_analyse_analog.pfad) as tdms_file:
                    # Informationen aus Messung holen und im Objekt speichern
                    group_zyklus = tdms_file["Zyklus"]
                    channel_zyklus_zeit = group_zyklus["Zeit"]

                    # Falls Kanäle für Drehmoment/Drehzahl ausgewählt wurden
                    if liste_t_n:
                        # Informationen aus Messung holen und im Objekt speichern
                        group_analog = tdms_file["Analog"]
                        channel_analog_zeit = group_analog["Zeit"]
                        # Basisobjekt für die Diagramme, mit von Anzahl Diagramme abhängiger Größe
                        fig_1 = plt.figure()
                        fig_1.set_figwidth(12)
                        fig_1.set_figheight(2.5 * anzahl_diagramme)
                        fig_1.suptitle(messung_analyse_analog.name, fontsize=12)
                        # Erzeugen der Diagramme für gewählte Bereiche
                        for diagram in range(anzahl_diagramme):
                            # Zeilen=anzahl_diagramme x Spalten=1 Grid, mit Diagramm an letzter Positions
                            t_n = fig_1.add_subplot(anzahl_diagramme, 1, diagram + 1)
                            # Zeiten für den zu analysierenden Bereich aus Messung holen
                            zeit_zyklen_von = channel_zyklus_zeit[zyklen_von[diagram] - 1]
                            zeit_zyklen_bis = channel_zyklus_zeit[zyklen_bis[diagram] - 1]

                            # Beginn und Ende für analoge Werte entsprechend der Zeiten ermitteln
                            # Nutzung von numpy search sorted Algorithmus
                            analog_anfang_index = np.searchsorted(channel_analog_zeit, zeit_zyklen_von, side="left")
                            analog_ende_index = np.searchsorted(channel_analog_zeit, zeit_zyklen_bis, side="right")

                            # Daten für Drehmoment und Drehzahl entsprechend dem gewählten Zyklus Bereich plotten
                            for n in liste_t_n:
                                # Prüfen, ob die Längen der Achsen "x" und "y" übereinstimmen
                                if len(channel_analog_zeit[analog_anfang_index:analog_ende_index]) == \
                                        len(group_analog[n][analog_anfang_index:analog_ende_index]):
                                    t_n.plot(
                                        channel_analog_zeit[analog_anfang_index:analog_ende_index],
                                        group_analog[n][analog_anfang_index:analog_ende_index],
                                        label=n)

                            # Gestaltung vom Diagramm
                            t_n.set_title(f"Zyklen {str(zyklen_von_legende[diagram])} bis "
                                          f"{str(zyklen_bis_legende[diagram])}", fontweight="bold", size=11)
                            t_n.set_xlabel("Zeit", fontsize=10)
                            t_n.set_ylabel("Drehmoment [Nm]\nDrehzahl [1/min]", fontsize=10)
                            t_n.set_ylim(-self.achse_lim_drehmoment.get(), self.achse_lim_drehmoment.get())
                            t_n.set_yticks(range(-self.achse_lim_drehmoment.get(), self.achse_lim_drehmoment.get(), 20))
                            for label in t_n.get_yticklabels()[::2]:  # jedes 2. Label ausblenden
                                label.set_visible(False)

                            # Teilstriche hinzufügen
                            t_n.minorticks_on()
                            t_n.xaxis.set_minor_locator(AutoMinorLocator(6))
                            t_n.yaxis.set_minor_locator(AutoMinorLocator(2))

                            t_n.legend(prop={"size": 10})
                            t_n.grid()
                            t_n.grid(which="minor", linestyle='--')

                        # Diagramme einpassen
                        fig_1.tight_layout()

                        # Diagramm in neuem Fenster darstellen
                        self._plot_in_window(fig_1)

                    if liste_temperaturen:
                        # Informationen aus Messung holen und im Objekt speichern
                        group_temperatur = tdms_file["Temperatur"]
                        channel_temperatur_zeit = group_temperatur["Zeit"]
                        # Basisobjekt für die Diagramme, mit von Anzahl Diagramme abhängiger Größe
                        fig_2 = plt.figure()
                        fig_2.set_figwidth(12)
                        fig_2.set_figheight(2.5 * anzahl_diagramme)
                        fig_2.suptitle(messung_analyse_analog.name, fontsize=12)
                        # Erzeugen der Diagramme für gewählte Bereiche
                        for diagram in range(anzahl_diagramme):
                            # Zeilen=anzahl_diagramme x Spalten=1 Grid, mit Diagramm an letzter Positions
                            temp = fig_2.add_subplot(anzahl_diagramme, 1, diagram + 1)
                            # Zeiten für den zu analysierenden Bereich aus Messung holen
                            zeit_zyklen_von = channel_zyklus_zeit[zyklen_von[diagram] - 1]
                            zeit_zyklen_bis = channel_zyklus_zeit[zyklen_bis[diagram] - 1]

                            # Beginn und Ende für analoge Werte entsprechend der Zeiten ermitteln
                            # Nutzung von numpy search sorted Algorithmus
                            temperatur_anfang_index = np.searchsorted(channel_temperatur_zeit, zeit_zyklen_von,
                                                                      side="left")
                            temperatur_ende_index = np.searchsorted(channel_temperatur_zeit, zeit_zyklen_bis,
                                                                    side="right")

                            # Daten für Drehmoment und Drehzahl entsprechend dem gewählten Zyklus Bereich plotten
                            for n in liste_temperaturen:
                                # Prüfen, ob die Längen der Achsen "x" und "y" übereinstimmen
                                if len(channel_temperatur_zeit[temperatur_anfang_index:temperatur_ende_index]) == \
                                        len(group_temperatur[n][temperatur_anfang_index:temperatur_ende_index]):
                                    temp.plot(
                                        channel_temperatur_zeit[temperatur_anfang_index:temperatur_ende_index],
                                        group_temperatur[n][temperatur_anfang_index:temperatur_ende_index],
                                        label=n)

                            # Ausgestaltung vom Diagramm
                            temp.set_title(f"Zyklen {str(zyklen_von_legende[diagram])} bis "
                                           f"{str(zyklen_bis_legende[diagram])}", fontweight="bold", size=11)
                            temp.set_xlabel("Zeit", fontsize=10)
                            temp.set_ylabel("Temperatur [°C]", fontsize=10)
                            temp.set_ylim(20, self.achse_lim_temperatur.get())
                            temp.set_yticks(range(20, self.achse_lim_temperatur.get(), 5))
                            # Teilstriche und Legende hinzufügen
                            temp.minorticks_on()
                            temp.yaxis.set_minor_locator(AutoMinorLocator(5))
                            temp.legend(prop={"size": 10})
                            temp.grid()
                            temp.grid(which="minor", linestyle='--')

                        # Diagramme einpassen
                        fig_2.tight_layout()

                        # Diagramm in neuem Fenster darstellen
                        self._plot_in_window(fig_2)

                # Schließen der TDMS-Datei
                tdms_file.close()
                # Statusbar auf OK setzen
                self.controller.status_ok()

            except FileNotFoundError:
                messagebox.showerror("Error", f"Die Datei {messung_analyse_analog.pfad} wurde nicht gefunden oder "
                                              f"konnte nicht verarbeitet werden!")
        else:
            messagebox.showwarning("Achtung", "Es wurde kein Kanal für die Darstellung ausgewählt!")

        # Buttons wieder freigeben
        self.btn_plot_zyklen["state"] = tk.NORMAL
        self.btn_plot_analog["state"] = tk.NORMAL

    def _enable_disable_bereiche(self):
        # Funktion zum ein- und ausblenden der Bereiche für die Auswertung
        # maximal können drei Bereiche gleichzeitig ausgewählt werden
        # Ausblenden durch Frames, welche über die Bereiche gelegt werden → überdecken
        if self.rb_variable.get() == 1:
            self.frm_bereich_2_blank.grid(column=0, row=2, pady=0, sticky="NSEW")
            self.frm_bereich_3_blank.grid(column=0, row=3, pady=0, sticky="NSEW")

        elif self.rb_variable.get() == 2:
            self.frm_bereich_2_blank.grid_forget()
            self.frm_bereich_3_blank.grid(column=0, row=3, pady=0, sticky="NSEW")

        elif self.rb_variable.get() == 3:
            self.frm_bereich_2_blank.grid_forget()
            self.frm_bereich_3_blank.grid_forget()

    # Prüfen der Eingabe für die Spin-boxes
    def _validate_spin_box_input(self):
        # try-except falls Eingaben keine Integer sind
        try:
            if (self.sb_1_v_von.get() < 1
                    or self.sb_2_v_von.get() < 1
                    or self.sb_3_v_von.get() < 1
                    or self.sb_1_v_bis.get() > self.messung_analyse.zyklen
                    or self.sb_2_v_bis.get() > self.messung_analyse.zyklen
                    or self.sb_3_v_bis.get() > self.messung_analyse.zyklen
            ):
                return False
            else:
                return True
        except:
            return False

    def update_einstellungen(self, drehmoment, temperatur):
        # Funktion zum Aktualisieren der Einstellungen
        self.achse_lim_drehmoment.set(drehmoment)
        self.achse_lim_temperatur.set(temperatur)

    def _plot_in_window(self, fig):
        # Canvas Objekt in eigenen Fenster
        top = tk.Toplevel()
        top.title(self.controller.sw_name)
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, ipady=0)
        # Navigation toolbar hinzufügen
        toolbar = NavigationToolbar2Tk(canvas, top)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
