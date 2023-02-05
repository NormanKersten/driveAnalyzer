import threading
import tkinter as tk
from tkinter import ttk, messagebox, font
from app import DriveAnalyzerVersion
from ui import AnalyseFrame, MessungFrame, DokuFrame, EinstellungenFrame, BerichtFrame
from utils import select_file, set_dpi_awareness

set_dpi_awareness()


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aktuelle SW-Version aus dem change log holen
        sw_version = DriveAnalyzerVersion()
        self.latest_version = sw_version.get_version()
        self.sw_name = sw_version.get_name()

        # Eigenschaften das Hauptfenster
        self.title(self.sw_name)
        self.resizable(False, False)
        self.geometry("800x650")

        # Objekt von "TkDefaultFont"
        self.defaultFont = font.nametofont("TkDefaultFont")
        # Überschreiben mit eigener Schrift Einstellung
        # self.defaultFont.configure(
        #     family="Courier",
        #     size=10,
        #     weight=font.NORMAL)  # BOLD

        # Dictionary für die Status-Meldungen
        self.status_dict = {"OK": "OK", "VERARBEITEN": "Daten werden verarbeitet ..."}
        # Variable für Anzeige des Status und initiales setzten
        self.status_var = tk.StringVar(value=self.status_dict["OK"])
        # Variable für den Status der Statusbar, sodass mehrere Anfragen berücksichtigt werden
        self.status_bar_run = 0
        # Dictionary zum Speichern der MessungInfo Objekte
        self.messungen = dict()
        # Globale Variable für die ausgewählte Messung
        self.messung_selected = ""

        # -- Erzeugen der Frames und Implementierung der Funktion zum Wechsel der Frames --
        # Dictionary zum Speichern der Frames
        self.frames = dict()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # -- Frame 1: Container für die verschiedenen Frames --
        container_frame = ttk.Frame(self)
        container_frame.columnconfigure(0, weight=1)
        container_frame.rowconfigure(0, weight=1)
        container_frame.grid(column=0, row=0, padx=20, pady=(20, 20), sticky="NSEW")

        frame_doku = DokuFrame(container_frame, self)
        frame_doku.grid(row=0, column=0, sticky="NSEW")

        frame_einst = EinstellungenFrame(container_frame, self)
        frame_einst.grid(row=0, column=0, sticky="NSEW")

        frame_bericht = BerichtFrame(container_frame, self)
        frame_bericht.grid(row=0, column=0, sticky="NSEW")

        frame_analyse = AnalyseFrame(container_frame, self)
        frame_analyse.grid(row=0, column=0, sticky="NSEW")
        # frame_messung zuletzt, da dieser zuerst angezeigt werden soll
        frame_messung = MessungFrame(container_frame, self)
        frame_messung.grid(row=0, column=0, sticky="NSEW")

        self.frames[MessungFrame] = frame_messung
        self.frames[AnalyseFrame] = frame_analyse
        self.frames[EinstellungenFrame] = frame_einst
        self.frames[DokuFrame] = frame_doku
        self.frames[BerichtFrame] = frame_bericht

        # -- Seperator --
        ttk.Separator(self, orient="horizontal").grid(column=0, row=1, padx=(0, 0), pady=(0, 20), sticky="SEW")

        # -- Frame 2: Status Frame, gleich für alle Frames --
        frm_status = ttk.Frame(self)
        frm_status.grid(column=0, row=2, padx=20, pady=(0, 20), sticky="NSEW")
        # Status Bar
        status_frame = ttk.Frame(frm_status)
        status_frame.grid(column=0, row=1, sticky="SEW")
        status_frame.rowconfigure(0, weight=1)
        self.lbl_status = ttk.Label(status_frame, text="Status:")
        self.lbl_status.grid(column=0, row=0, sticky="W")
        self.lbl_status_txt = ttk.Label(status_frame, width=25, textvariable=self.status_var)
        self.lbl_status_txt.grid(column=1, row=0, padx=(10, 10), sticky="W")
        self.progressbar = ttk.Progressbar(status_frame, mode="indeterminate", length=460)
        self.progressbar.grid(column=2, row=0, columnspan=2, sticky="EW")
        self.frm_overlay = ttk.Frame(status_frame)
        self.frm_overlay.grid(column=2, row=0, columnspan=2, sticky="NSEW")

    # -- UI Methoden --
    def show_frame(self, container):
        frame = self.frames[container]
        if container == DokuFrame:
            root.title("Dokumentation")
        # Objekt der Messung zur Analyse oder dem Bericht übergeben
        elif container == AnalyseFrame or container == BerichtFrame:
            # Einstellungen im Analyse Frame aktualisieren
            self.frames[AnalyseFrame].update_einstellungen(self.frames[EinstellungenFrame].y_lim_drehmoment_einst.get(),
                                                           self.frames[EinstellungenFrame].y_lim_temperatur_einst.get())
            # Wenn eine Messung ausgewählt ist, wird das entsprechende Objekt dem AnalyseFrame
            # oder BerichtFrame übergeben
            if self.frames[MessungFrame].messung_liste.curselection() != ():
                selected_index = self.frames[MessungFrame].messung_liste.curselection()
                container.update_frm(frame, messung=self.messungen[self.frames[MessungFrame].
                                     messung_liste.get(selected_index)])
                root.title(self.frames[MessungFrame].messung_liste.get(selected_index))
            else:
                container.clear_frm(frame)
        else:
            root.title(self.sw_name)
        frame.tkraise()

    def status_ok(self):
        self.status_bar_run -= 1
        if self.status_bar_run == 0:
            self.progressbar.stop()
            self.frm_overlay.grid()
            self.status_var.set(self.status_dict["OK"])

    def status_verarbeiten(self):
        self.status_bar_run += 1
        self.status_var.set(self.status_dict["VERARBEITEN"])
        self.progressbar.start()
        self.frm_overlay.grid_remove()

    # -- Menü erstellen --
    def create_menu(self):
        menubar = tk.Menu(self)

        datei_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=datei_menu)
        datei_menu.add_command(label="Öffnen", command=lambda: threading.Thread(target=self.load_file).start())
        datei_menu.add_command(label="Messungen", command=lambda: self.show_frame(MessungFrame))
        # TODO: Möglichkeit für weiteren Ausbau der App
        # datei_menu.add_command(label="Zusammenfügen", command=donothing)
        datei_menu.add_command(label="Schließen", command=self.close_file)
        datei_menu.add_separator()
        datei_menu.add_command(label="Beenden", command=self._quit_app)

        auswerten_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Auswerten", menu=auswerten_menu)
        auswerten_menu.add_command(label="Bericht", command=lambda: self.show_frame(BerichtFrame))
        auswerten_menu.add_command(label="Analyse", command=lambda: self.show_frame(AnalyseFrame))
        auswerten_menu.add_separator()
        auswerten_menu.add_command(label="Einstellungen", command=lambda: self.show_frame(EinstellungenFrame))

        hilfe_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=hilfe_menu)
        hilfe_menu.add_command(label="Über...", command=self.show_about)
        hilfe_menu.add_command(label="Dokumentation", command=lambda: self.show_frame(DokuFrame))

        self.config(menu=menubar)

    # -- Menü-Methoden --
    def load_file(self):
        dateiname = select_file()
        self.frames[MessungFrame].add_messung(dateiname=dateiname)

    def close_file(self):
        self.frames[MessungFrame].del_messung()

    def show_about(self):
        messagebox.showinfo(title=f"Über {self.sw_name}",
                            message=f"Version:\t {self.latest_version}\n"
                                    "Ersteller:\t Norman Kersten")

    @staticmethod
    def _quit_app():
        root.quit()     # stoppen der mainloop
        root.destroy()  # für Windows empfohlen


if __name__ == "__main__":
    root = App()
    root.create_menu()
    # Anwendung auf Bildschirm zentrieren
    root.eval('tk::PlaceWindow . center')
    root.mainloop()
