import datetime
import os.path
import threading
import tkinter as tk
import zipfile
from tkinter import ttk, messagebox
from tkinter.messagebox import askyesno

import numpy as np
from PIL import Image
from PyPDF2 import PdfMerger
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import AutoMinorLocator
from nptdms import TdmsFile
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app import MessungInfo


class BerichtFrame(ttk.Frame):
    def __init__(self, container, controller, **kwargs):
        super().__init__(container, **kwargs)

        self.controller = controller
        # Objekt der Messung, für welche der Bericht erstellt werden soll
        self.messung_bericht = MessungInfo()

        # Variable für die Prüfstände, welche gewählt werden können
        self.test_rigs = ("Antriebsprüfstand 101", "Antriebsprüfstand 102", "Antriebsprüfstand 103",
                          "Antriebsprüfstand 104", "Antriebsprüfstand 105", "Antriebsprüfstand 106",
                          "Antriebsprüfstand 107", "Antriebsprüfstand 108", "Mobil 01", "Mobil 02")
        # Variable für in der Combobox gewählten Prüfstand
        self.selected_test_rig = tk.StringVar()
        # Variable zum Anzeigen der Messung
        self.messung_name = tk.StringVar()
        # Variable für Checkbutton
        self.check_btn_var = tk.IntVar()

        # Variablen für Einstellungen, gesetzt mit Default Werten
        self.achse_lim_drehmoment = tk.IntVar(value=300)
        self.achse_lim_temperatur = tk.IntVar(value=120)

        # Anzahl der auszuwertenden Zyklen
        self.anzahl_zyklen = 3
        # Mindest Zyklenzahl der Messung, sodass eine Auswertung von drei Bereichen auch sinnvoll ist
        self.min_zyklen_bericht = self.anzahl_zyklen + 5

        # Anzahl der Diagramme für die analogen Bereiche
        self.anzahl_diagramme = tk.IntVar(value=3)

        # Format für den PDF-Ausdruck
        self.fig_width = 11.69  # Querformat A4
        self.fig_height = 8.27  # Querformat A4

        # -- Was soll alles im Bericht erscheinen --
        # Version des DriveAnalyzer
        # Beginn und Ende der Messung
        # wie viele Zyklen

        # Frame Einstellungen für den Haupt-Frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)

        bericht_label = ttk.Label(self, text="Bericht erstellen", font=("Helvetica", 11, "bold"))
        bericht_label.grid(column=0, row=0, sticky="W")

        # -- Frame 1: Eingaben zum Bericht --
        frm_bericht_eingaben = ttk.Frame(self, relief="groove", borderwidth=2)
        frm_bericht_eingaben.grid(column=0, row=1, pady=(0, 10), sticky="NSEW")
        frm_bericht_eingaben.columnconfigure(0, weight=1)
        frm_bericht_eingaben.rowconfigure(2, weight=1)

        frm_kopf = ttk.Frame(frm_bericht_eingaben)
        frm_kopf.grid(column=0, row=0, padx=(10, 5), pady=(10, 10), sticky="NSEW")
        frm_kopf.columnconfigure(1, weight=1)
        frm_kopf.rowconfigure(1, weight=0)
        lbl_messung = ttk.Label(frm_kopf, text="Messung:", width=9)
        lbl_messung.grid(column=0, row=0, padx=(0, 0), sticky="W")
        lbl_messung_aktuell = ttk.Label(frm_kopf, anchor=tk.W, width=40, textvariable=self.messung_name,
                                        font=("Helvetica", 10, "bold"))
        lbl_messung_aktuell.grid(column=1, row=0, padx=(5, 20), sticky="W")
        lbl_testrig = ttk.Label(frm_kopf, text="Datenlogger:")
        lbl_testrig.grid(column=2, row=1, padx=(10, 10), pady=(20, 0), sticky="EW")
        combo_testrigs = ttk.Combobox(frm_kopf, textvariable=self.selected_test_rig, width=20, justify=tk.CENTER)
        combo_testrigs.grid(column=3, row=1, padx=(0, 10), pady=(20, 0), sticky="EW")
        combo_testrigs["values"] = self.test_rigs
        combo_testrigs.current(0)
        lbl_projekt = ttk.Label(frm_kopf, text="Projekt:", width=9)
        lbl_projekt.grid(column=0, row=1, padx=(0, 0), pady=(20, 0), sticky="W")
        self.txt_projekt = tk.Text(frm_kopf, height=1, width=30)
        self.txt_projekt.grid(column=1, row=1, pady=(20, 0), sticky="W")

        lbl_beschreibung = ttk.Label(frm_bericht_eingaben, text="Beschreibung oder weitere Kommentare zur Messung")
        lbl_beschreibung.grid(column=0, row=1, padx=(10, 0), pady=(10, 5), sticky="NW")
        self.txt_komment = tk.Text(frm_bericht_eingaben, height=15, wrap="word")
        self.txt_komment["state"] = "normal"  # "disabled"
        self.txt_komment.grid(column=0, row=2, padx=(10, 0), pady=(0, 10), sticky="NSEW")
        # -- Scrollbar für Textfeld --
        text_scroll = ttk.Scrollbar(frm_bericht_eingaben, orient="vertical", command=self.txt_komment.yview)
        text_scroll.grid(column=1, row=2, padx=(0, 5), pady=(10, 10), sticky="NS")
        self.txt_komment["yscrollcommand"] = text_scroll.set

        frm_buttons = ttk.Frame(self)
        frm_buttons.grid(column=0, row=2, sticky="EW")
        frm_buttons.columnconfigure(0, weight=1)
        check_btn_zip = ttk.Checkbutton(frm_buttons, variable=self.check_btn_var, onvalue=1, offvalue=0,
                                        text="Messdatei anschließend komprimieren")
        check_btn_zip.grid(column=0, row=0, padx=(20, 0), sticky="W")
        self.btn_bericht_drucken = ttk.Button(frm_buttons, text="Bericht drucken", width=20,
                                              command=lambda: threading.Thread(target=self.report).start())
        self.btn_bericht_drucken.grid(column=1, row=0, padx=(0, 20), sticky="E")

    def update_frm(self, messung):
        # Objekt der Messung im Frame speichern und Name in Label anzeigen
        self.messung_bericht = messung
        self.messung_name.set(self.messung_bericht.name)

    def clear_frm(self):
        # Neues Objekt für Messung erzeugen und Namen im Label löschen
        self.messung_bericht = MessungInfo()
        self.messung_name.set(value="")

    def report(self):
        # Objekt der Messung speichern, falls während der Erstellung vom Bericht ein neues Objekt (Messung)
        # dem Frame übergeben wird.
        messung_bericht_report = self.messung_bericht

        # Speichern der Bereiche zur Auswertung der Zyklen in Liste
        zyklen_von = [1, 0, 0]
        zyklen_bis = [0, 0, 0]
        # Liste für Legende der Bereiche, da teilweise abweichend.
        # Z.B.: Zyklus vor 1 bis vor 4, was aber dann Zyklus 1 bois 3 ist
        zyklen_von_legende = [1, 0, 0]
        zyklen_bis_legende = [0, 0, 0]

        # Prüfen, ob ein Bericht für die Messung auch sinnvoll ist
        if len(messung_bericht_report.channels_zyklus) > self.min_zyklen_bericht:
            # Buttons für weitere Diagramme sperren
            self.btn_bericht_drucken["state"] = tk.DISABLED
            # Statusbar triggern
            self.controller.status_verarbeiten()

            # Vorgaben für die Zyklen Bereiche aktualisieren
            zyklen_bis[0] = zyklen_von[0] + self.anzahl_zyklen
            zyklen_von[1] = round(int(messung_bericht_report.zyklen) / 2)
            zyklen_bis[1] = zyklen_von[1] + self.anzahl_zyklen
            zyklen_bis[2] = int(messung_bericht_report.zyklen)
            zyklen_von[2] = zyklen_bis[2] - self.anzahl_zyklen
            # Speichern der Zyklen für Legende der Diagramme
            zyklen_bis_legende[0] = zyklen_bis[0] - 1
            zyklen_von_legende[1] = zyklen_von[1]
            zyklen_bis_legende[1] = zyklen_bis[1] - 1
            zyklen_bis_legende[2] = zyklen_bis[2]
            zyklen_von_legende[2] = zyklen_von[2] + 1

            # Nutzung von memory mapped numpy arrays
            # with tempfile.TemporaryDirectory() as temp_memmap_dir:
            #     tdms_file = TdmsFile.read(messung_bericht_report.pfad, memmap_dir=temp_memmap_dir)

            tdms_file = TdmsFile.read(messung_bericht_report.pfad)
            # Informationen aus Messung holen und im Objekt speichern
            group_zyklus = tdms_file["Zyklus"]
            group_temperatur = tdms_file["Temperatur"]
            group_analog = tdms_file["Analog"]
            all_channels_zyklus = group_zyklus.channels()
            all_channels_analog = group_analog.channels()
            all_channels_temperatur = group_temperatur.channels()
            channel_zyklus_zeit = group_zyklus["Zeit"]
            channel_analog_zeit = group_analog["Zeit"]
            channel_temperatur_zeit = group_temperatur["Zeit"]
            # Da die Zyklen für die x-Achse öfter verwendet werden
            data_zyklus = group_zyklus["Zyklus"][:]

            # Kanäle für die zwei Diagramme aufteilen und in Listen erfassen
            liste_temperaturen = []
            liste_t_n = []
            for channel in all_channels_zyklus:
                # Die Kanäle für Zeit und Zyklus sollen nicht mit in das Diagramm
                if "zeit" in channel.name.lower() or "zyklus" in channel.name.lower():
                    continue
                elif "drehmoment" in channel.name.lower() or "drehzahl" in channel.name.lower():
                    liste_t_n.append(channel)
                else:
                    liste_temperaturen.append(channel)

            # Abbildung 1 mit zwei Diagrammen über allen Zyklen
            fig_1, (t_n, temp) = plt.subplots(nrows=2)
            fig_1.set_figwidth(self.fig_width)
            fig_1.set_figheight(self.fig_height)
            # Titel mit Name der Messung
            fig_1.suptitle(messung_bericht_report.name, fontsize=12)

            # Diagramm für Drehmoment und Drehzahl
            for channel in liste_t_n:
                t_n.plot(data_zyklus,
                         group_zyklus[channel.name][:],
                         label=channel.name)

            t_n.set_title(f"Drehmoment und Drehzahl für {str(len(data_zyklus))} Zyklen",
                          fontweight="bold", size=11)
            t_n.set_xlabel("Zyklus", fontsize=10)
            t_n.set_ylabel("Drehmoment [Nm]\nDrehzahl [1/min]", fontsize=10)
            t_n.set_ylim(-self.achse_lim_drehmoment.get(), self.achse_lim_drehmoment.get())
            t_n.set_yticks(range(-self.achse_lim_drehmoment.get(), self.achse_lim_drehmoment.get(), 20))
            for label in t_n.get_yticklabels()[::2]:  # jede 2te Achsbeschriftung ausblenden
                label.set_visible(False)

            # Teilstriche und Legende hinzufügen
            t_n.minorticks_on()
            t_n.xaxis.set_minor_locator(AutoMinorLocator(6))
            t_n.yaxis.set_minor_locator(AutoMinorLocator(2))
            t_n.legend(prop={"size": 9})
            t_n.grid()
            t_n.grid(which="minor", linestyle='--')

            # Diagramm für Temperaturen
            for m in liste_temperaturen:
                temp.plot(data_zyklus, group_zyklus[m.name][:],
                          label=m.name)
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
            temp.legend(prop={"size": 9})
            temp.grid()
            temp.grid(which="minor", linestyle='--')

            # Abbildung 2 mit drei Diagrammen für Drehmoment und Drehzahl für drei Bereiche
            # Basisobjekt für die Diagramme, mit von Anzahl Diagramme abhängiger Größe
            fig_2 = plt.figure()
            fig_2.set_figwidth(self.fig_width)
            fig_2.set_figheight(self.fig_height)
            fig_2.suptitle(messung_bericht_report.name, fontsize=12)
            # Erzeugen der Diagramme für gewählte Bereiche
            for diagram in range(self.anzahl_diagramme.get()):
                # Zeilen=anzahl_diagramme x Spalten=1 Grid, mit Diagramm an letzter Positions
                t_n = fig_2.add_subplot(self.anzahl_diagramme.get(), 1, diagram + 1)
                # Zeiten für den zu analysierenden Bereich aus Messung holen
                zeit_zyklen_von = channel_zyklus_zeit[zyklen_von[diagram] - 1]
                zeit_zyklen_bis = channel_zyklus_zeit[zyklen_bis[diagram] - 1]

                # Lineare Suche für Beginn und Ende der Auswertung
                # analog_anfang = channel_analog_zeit[0]
                # analog_anfang_index = 0
                # analog_ende = channel_analog_zeit[0]
                # analog_ende_index = 0

                # for n in channel_analog_zeit:
                #     if n > zeit_zyklen_von:
                #         analog_anfang = n
                #         break
                #     analog_anfang_index += 1

                # for n in channel_analog_zeit:
                #     if n > zeit_zyklen_bis:
                #         analog_ende = n
                #         break
                #     analog_ende_index += 1

                # Nutzung von numpy search sorted Algorithmus
                analog_anfang_index = np.searchsorted(channel_analog_zeit, zeit_zyklen_von, side="left")
                analog_ende_index = np.searchsorted(channel_analog_zeit, zeit_zyklen_bis, side="right")

                # Daten für Drehmoment und Drehzahl entsprechend dem gewählten Zyklus Bereich plotten
                for analog in range(1, len(all_channels_analog)):
                    # Prüfen, ob die Längen der Achsen "x" und "y" übereinstimmen
                    if len(channel_analog_zeit[analog_anfang_index:analog_ende_index]) == \
                            len(group_analog[all_channels_analog[analog].name][analog_anfang_index:analog_ende_index]):
                        t_n.plot(
                            channel_analog_zeit[analog_anfang_index:analog_ende_index],
                            group_analog[all_channels_analog[analog].name][analog_anfang_index:analog_ende_index],
                            label=all_channels_analog[analog].name)

                # Gestaltung vom Diagramm
                t_n.set_title(f"Zyklen {str(zyklen_von_legende[diagram])} bis "
                              f"{str(zyklen_bis_legende[diagram])}", fontweight="bold", size=11)
                t_n.set_xlabel("Zeit", fontsize=10)
                t_n.set_ylabel("Drehmoment [Nm]\nDrehzahl [1/min]", fontsize=10)
                t_n.set_ylim(-self.achse_lim_drehmoment.get(), self.achse_lim_drehmoment.get())
                t_n.set_yticks(range(-self.achse_lim_drehmoment.get(), self.achse_lim_drehmoment.get(), 20))
                for label in t_n.get_yticklabels()[::2]:  # jede 2te Achsbeschriftung ausblenden
                    label.set_visible(False)

                # Teilstriche hinzufügen
                t_n.minorticks_on()
                t_n.xaxis.set_minor_locator(AutoMinorLocator(6))
                t_n.yaxis.set_minor_locator(AutoMinorLocator(2))
                t_n.legend(prop={"size": 9})
                t_n.grid()
                t_n.grid(which="minor", linestyle='--')

            # Abbildung 3 mit drei Diagrammen mit den Temperaturen für drei Bereiche
            # Basisobjekt für die Diagramme, mit von Anzahl Diagramme abhängiger Größe
            fig_3 = plt.figure()
            fig_3.set_figwidth(self.fig_width)
            fig_3.set_figheight(self.fig_height)
            fig_3.suptitle(messung_bericht_report.name, fontsize=12)
            # Erzeugen der Diagramme für gewählte Bereiche
            for diagram in range(self.anzahl_diagramme.get()):
                # Zeilen=anzahl_diagramme x Spalten=1 Grid, mit Diagramm an letzter Positions
                temp = fig_3.add_subplot(self.anzahl_diagramme.get(), 1, diagram + 1)
                # Zeiten für den zu analysierenden Bereich aus Messung holen
                zeit_zyklen_von = channel_zyklus_zeit[zyklen_von[diagram] - 1]
                zeit_zyklen_bis = channel_zyklus_zeit[zyklen_bis[diagram] - 1]

                # Nutzung von numpy search sorted Algorithmus
                temperatur_anfang_index = np.searchsorted(channel_temperatur_zeit, zeit_zyklen_von, side="left")
                temperatur_ende_index = np.searchsorted(channel_temperatur_zeit, zeit_zyklen_bis, side="right")

                # Daten für Drehmoment und Drehzahl entsprechend dem gewählten Zyklus Bereich plotten
                for temperatur in range(1, len(all_channels_temperatur)):
                    # Prüfen, ob die Längen der Achsen "x" und "y" übereinstimmen
                    if len(channel_temperatur_zeit[temperatur_anfang_index:temperatur_ende_index]) == \
                            len(group_temperatur[all_channels_temperatur[temperatur].name]
                                [temperatur_anfang_index:temperatur_ende_index]):
                        temp.plot(
                            channel_temperatur_zeit[temperatur_anfang_index:temperatur_ende_index],
                            group_temperatur[all_channels_temperatur[temperatur].name]
                            [temperatur_anfang_index:temperatur_ende_index],
                            label=all_channels_temperatur[temperatur].name)

                # Ausgestaltung vom Diagramm
                temp.set_title(f"Zyklen {str(zyklen_von_legende[diagram])} bis "
                               f"{str(zyklen_bis_legende[diagram])}", fontweight="bold", size=11)
                temp.set_xlabel("Zeit", fontsize=10)
                temp.set_ylabel("Temperatur [°C]", fontsize=10)
                temp.set_ylim(20, self.achse_lim_temperatur.get())
                temp.set_yticks(range(20, self.achse_lim_temperatur.get(), 10))
                # Teilstriche und Legende hinzufügen
                temp.minorticks_on()
                temp.yaxis.set_minor_locator(AutoMinorLocator(5))
                temp.legend(prop={"size": 9})
                temp.grid()
                temp.grid(which="minor", linestyle='--')

            # Schließen der TDMS-Datei
            tdms_file.close()
            # Statusbar auf OK setzen
            self.controller.status_ok()
            # Diagramme einpassen und anzeigen
            fig_1.tight_layout()
            fig_2.tight_layout()
            fig_3.tight_layout()

            # Diagramme in Liste speichern, als PDF drucken und aus dem Speicher entfernen
            figures = (fig_1, fig_2, fig_3)
            self._abbildung_speichern(messung_bericht_report, figures)
            for fig in figures:
                plt.close(fig)
            # Deckblatt zum Bericht erstellen und speichern
            self._deckblatt_bericht(messung_bericht_report)
            # Bericht zusammenfügen
            self._merge_bericht(messung_bericht_report)
            # Buttons wieder freigeben
            self.btn_bericht_drucken["state"] = tk.NORMAL

            # Archivieren der TDMS-Datei, falls gewünscht
            if self.check_btn_var.get() == 1 and askyesno("Bericht", f"Die TDMS-Datei nun archivieren?\n"
                                                                     f"Bitte die Anwendung dann während "
                                                                     f"der Archivierung nicht schließen!"):
                self._zip_tdms(messung_bericht_report)

        else:
            messagebox.showwarning("Achtung", f"Es kann kein Bericht erstellt werden,\nda die Messung zu wenige Zyklen "
                                              f"enthält!")

    def _deckblatt_bericht(self, messung):
        # Funktion zum Erstellen und speichern des Berichtdeckblattes
        # Pfad und Dateiname der PDF-Dateien für den Bericht, sodass PDF im Zielpfad der Messung abgelegt wird
        pdf_dateiname_deckblatt = f"{messung.pfad.rsplit('.', 1)[0]}_Bericht_Deckblatt.pdf"
        # Objekt für Deckblatt erzeugen
        deckblatt = canvas.Canvas(pdf_dateiname_deckblatt, pagesize=A4)
        deckblatt.setPageSize(landscape(A4))
        h, w = A4  # A4 Querformat (595.275590551181, 841.8897637795275)
        # (0,0) ist die Ecke oben links im Dokument!
        # Allgemeine Einstellungen
        deckblatt.setLineWidth(.3)
        deckblatt.setFont('Helvetica-Bold', 14)
        # Mit Daten befüllen
        deckblatt.rect(15, h - 15, w - 30, - h + 40)  # (x, y, width, height)
        deckblatt.drawCentredString(w / 2, h - 50, f"Kurz-Prüfbericht zur Messung: {messung.name}")
        deckblatt.line(w - w + 200, h - 60, w - 200, h - 60)
        # Nutzung der python PIL Image Bibliothek
        feig_logo = ImageReader(
            Image.open("resources\\feig_logo.png"))
        # "resources\\feig_logo.png"
        # "C:\\Users\\Familie_Kersten\\PycharmProjects\\driveAnalyzer\\resources\\feig_logo.png"
        deckblatt.drawImage(feig_logo, 710, h - 120, width=100, preserveAspectRatio=True, mask="auto")
        deckblatt.setFont('Helvetica', 12)
        deckblatt.drawString(50, h - 120, "Projekt:")
        deckblatt.drawString(150, h - 120, self.txt_projekt.get("1.0", "end-1c"))
        deckblatt.drawString(50, h - 140, "Datenlogger:")
        deckblatt.drawString(150, h - 140, self.selected_test_rig.get())
        deckblatt.drawString(400, h - 120, "Start der Messung:")
        deckblatt.drawString(540, h - 120, messung.start)
        deckblatt.drawString(400, h - 140, "Zyklen gesamt:")
        deckblatt.drawString(540, h - 140, str(messung.zyklen))

        # Ab hier mit relativer y-Position drucken
        y = h - 200
        deckblatt.setFont('Helvetica-Bold', 12)
        deckblatt.drawString(50, y, "Beschreibung und/oder weitere Kommentierung:")
        deckblatt.setFont('Helvetica', 11)
        # Text aus Textfeld holen und Zeile für Zeile drucken
        text_from_komment_list = self.txt_komment.get("1.0", "end-1c").split("\n")
        y -= 30
        for line in text_from_komment_list:
            deckblatt.drawString(50, y, line)
            y -= 20

        y -= 30
        deckblatt.setFont('Helvetica-Bold', 12)
        deckblatt.drawString(50, y, "In der Messung gespeicherte Kommentare:")
        deckblatt.setFont('Helvetica', 11)
        # Drucken der Kommentare der Messung
        y -= 30
        for time, log in messung.kommentare.items():
            deckblatt.drawString(50, y, time)
            deckblatt.drawString(200, y, log)
            y -= 20

        # Fusszeile
        deckblatt.setFont('Helvetica', 10)
        deckblatt.drawString(20, h - h + 10, f"{self.controller.sw_name} {self.controller.latest_version}")
        deckblatt.drawRightString(w - 20, h - h + 10, f"Gedruckt am: {datetime.datetime.now().strftime('%c')}")

        # Deckblatt erstellen und speichern
        deckblatt.showPage()
        deckblatt.save()

    @staticmethod
    def _abbildung_speichern(messung, figures):
        # Pfad und Dateiname der PDF-Dateien für den Bericht, sodass PDF im Zielpfad der Messung abgelegt wird
        pdf_dateiname_diagramme = f"{messung.pfad.rsplit('.', 1)[0]}_Bericht_Diagramme.pdf"
        # Objekt von PdfPages erzeugen
        pdf_abb = PdfPages(pdf_dateiname_diagramme)
        # Durch die Liste iterieren und Abbildungen im PDF speichern
        for fig in figures:
            fig.savefig(pdf_abb, format='pdf')

        # Objekt wieder schließen
        pdf_abb.close()

    def _merge_bericht(self, messung):
        merger = PdfMerger()
        # Metadata
        merger.add_metadata({
            "/Title": messung.name,
            "/Subject": "Auswertung der Messung: " + messung.name,
            "/Author": f"{self.controller.sw_name}",
            "/Creator": f"{self.controller.sw_name}",
            "/CreateDate": datetime.datetime.now().strftime('%c'),
        })

        # Pfad und Dateiname der PDF-Dateien für den Bericht, sodass PDF im Zielpfad der Messung abgelegt wird
        pdf_dateiname_diagramme = f"{messung.pfad.rsplit('.', 1)[0]}_Bericht_Diagramme.pdf"
        pdf_dateiname_deckblatt = f"{messung.pfad.rsplit('.', 1)[0]}_Bericht_Deckblatt.pdf"
        pdf_dateiname_bericht = f"{messung.pfad.rsplit('.', 1)[0]}_Bericht.pdf"

        # PDF Dateien anhängen
        merger.append(pdf_dateiname_deckblatt)
        merger.append(pdf_dateiname_diagramme)
        # Schreiben und anschließend Schließen vom merger Objekt
        merger.write(pdf_dateiname_bericht)
        merger.close()

        # Temporäre PDF-Dateien löschen
        if os.path.exists(pdf_dateiname_bericht):
            try:
                os.remove(pdf_dateiname_deckblatt)
                os.remove(pdf_dateiname_diagramme)
            except OSError:
                print(OSError)
                messagebox.showwarning("Bericht", f"Die temporären PDF-Dateien {pdf_dateiname_deckblatt} "
                                                  f"und/oder {pdf_dateiname_diagramme} konnten nicht gelöscht werden.")

        # Anwender benachrichtigen
        messagebox.showinfo("Bericht", f"Der Bericht wurde erfolgreich erstellt und gespeichert:\n"
                                       f"{pdf_dateiname_bericht}")

    def _zip_tdms(self, messung):
        # Funktion zum Archivieren (ZIP komprimiert) der Messdatei (TDMS)
        zip_dateiname = f"{messung.pfad.rsplit('.', 1)[0]}_Archiv.zip"
        # Statusbar triggern und anzeigen, dass Daten verarbeitet werden
        self.controller.status_verarbeiten()
        # ZipFile-Objekt erstellen mit Komprimierung
        with zipfile.ZipFile(zip_dateiname, 'w',
                             compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as zip_tdms:
            zip_tdms.write(messung.pfad, arcname=messung.name)
        # Wenn das ZIP-Archiv vorhanden ist, soll die TDMS-Datei gelöscht werden
        if os.path.exists(zip_dateiname):
            os.remove(messung.pfad)
        # Statusbar zurücksetzen und Benutzer informieren
        self.controller.status_ok()
        messagebox.showinfo("Bericht", f"Die TDMS-Datei wurde erfolgreich archiviert:\n"
                                       f"{zip_dateiname}")
