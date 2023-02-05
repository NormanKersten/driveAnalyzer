import datetime
import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename
import arrow
from nptdms import TdmsFile
from app.model import MessungInfo


class MessungFrame(ttk.Frame):
    def __init__(self, container, controller, **kwargs):
        super().__init__(container, **kwargs)

        # Controller über welchen auf root Methoden zugegriffen werden kann
        self.controller = controller
        # Variablen zur Anzeige von Informationen zur Messung
        self.start_messung = tk.StringVar()
        self.zyklen_messung = tk.StringVar()
        self.l_messungen = []
        messungen_str = tk.StringVar(value=self.l_messungen.sort())
        self.listbox_last = ""

        def _handle_listbox_selection(event):
            if self.messung_liste.curselection() != ():
                selected_index = self.messung_liste.curselection()
                self.start_messung.set(self.controller.messungen[self.messung_liste.get(selected_index)].start)
                self.zyklen_messung.set(self.controller.messungen[self.messung_liste.get(selected_index)].zyklen)
                self.txt_komment.delete(1.0, "end")
                for zeit, bemerkung in self.controller.messungen[self.messung_liste.get(selected_index)] \
                        .kommentare.items():
                    self.txt_komment.insert("end", f"{zeit} \t {bemerkung} \n")
                self.listbox_last = self.messung_liste.get(selected_index)
                # ausgewählte Messung global speichern
                self.controller.messung_selected = self.controller.messungen[self.messung_liste.get(selected_index)] \
                    .name

            else:
                self.start_messung.set("")
                self.zyklen_messung.set("")
                self.txt_komment.delete(1.0, "end")

        # Frame Einstellungen für den Haupt-Frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)

        messung_label = ttk.Label(self, text="Messungen", font=("Helvetica", 11, "bold"))
        messung_label.grid(column=0, row=0, sticky="W")

        # -- Frame 1: Übersicht zur Messung --
        messung_info = ttk.Frame(self, relief="groove", borderwidth=2)
        messung_info.grid(column=0, row=1, pady=(0, 20), sticky="NSEW")
        self.messung_liste = tk.Listbox(messung_info, selectmode=tk.SINGLE, width=30,
                                        listvariable=messungen_str, height=3)
        self.messung_liste.grid(column=0, row=0, rowspan=2, padx=(10, 0), pady=(10, 10))
        self.messung_liste.bind("<<ListboxSelect>>", _handle_listbox_selection)
        # -- Scrollbar für Listbox --
        list_scroll = ttk.Scrollbar(messung_info, orient="vertical",
                                    command=self.messung_liste.yview)
        list_scroll.grid(column=1, row=0, rowspan=2, padx=(0, 20), pady=(10, 10), sticky="NSE")
        self.messung_liste["yscrollcommand"] = list_scroll.set
        lbl_info_start = ttk.Label(messung_info, text="Start der Messung: ")
        lbl_info_start.grid(column=2, row=0, padx=(10, 0), pady=(15, 5), sticky="EW")
        lbl_info_zyklen = ttk.Label(messung_info, text="Anzahl der Zyklen: ")
        lbl_info_zyklen.grid(column=2, row=1, padx=(10, 0), pady=(5, 15), sticky="EW")
        lbl_txt_info_start = ttk.Label(messung_info, background="white", width=30,
                                       anchor=tk.W, textvariable=self.start_messung)
        lbl_txt_info_start.grid(column=3, row=0, padx=(5, 0), pady=(15, 5), sticky="EW")
        lbl_txt_info_zyklen = ttk.Label(messung_info, background="white", width=30,
                                        anchor=tk.W, textvariable=self.zyklen_messung)
        lbl_txt_info_zyklen.grid(column=3, row=1, padx=(5, 0), pady=(5, 15), sticky="EW")

        # -- Frame 2: Anzeige der Kommentare zur Messung --
        lbl_komment = ttk.Label(self, text="In der Messung gespeicherte Kommentare")
        lbl_komment.grid(column=0, row=2,  sticky="NW")
        frm_komment = ttk.Frame(self, relief="groove", borderwidth=2)
        frm_komment.grid(column=0, row=3, pady=(0, 20), sticky="NSEW")
        frm_komment.columnconfigure(0, weight=1)
        frm_komment.rowconfigure(0, weight=1)
        self.txt_komment = tk.Text(frm_komment, height=15)
        self.txt_komment["state"] = "normal"  # "disabled"
        self.txt_komment.grid(column=0, row=0, padx=(10, 0), pady=(10, 10), sticky="NSEW")
        # -- Scrollbar für Textfeld --
        text_scroll = ttk.Scrollbar(frm_komment, orient="vertical", command=self.txt_komment.yview)
        text_scroll.grid(column=1, row=0, padx=(0, 5), pady=(10, 10), sticky="NS")
        self.txt_komment["yscrollcommand"] = text_scroll.set
        btn_save = ttk.Button(frm_komment, text="Als Text speichern", width=20, command=self._save_log)
        btn_save.grid(column=0, row=1, padx=(0, 0), pady=(0, 10), sticky="E")

    def add_messung(self, dateiname):
        # ----------------------------------------------------------------------------------------------
        # -- Funktion zum Hinzufügen einer Messung zur Anwendung ---------------------------------------
        # -- Die Daten werden aus einer Messdatei gelesen und in einem MessungInfo-Objekt gespeichert --
        # ----------------------------------------------------------------------------------------------
        # Objekt für Informationen zur Messung erzeugen
        messung = MessungInfo()
        # Falls keine Datei gewählt wurde
        if not dateiname:
            messagebox.showwarning("Achtung", "Bitte eine TDMS-Datei auswählen.")
            return
        # Prüfen, ob die Messung bereits vorhanden ist
        for key in self.controller.messungen.keys():
            if os.path.basename(dateiname) == key:
                messagebox.showwarning(title="Keine Messung geladen!",
                                       message="Es ist bereits eine Datei mit dem gleichen Namen vorhanden!")
                return

        try:
            # Statusbar auf lesen setzten
            self.controller.status_verarbeiten()
            with TdmsFile.open(dateiname) as tdms_file:
                # Informationen aus Messung holen und im Objekt speichern
                group_log = tdms_file["Log"]
                group_temp = tdms_file["Temperatur"]
                all_temp_channels = group_temp.channels()
                group_analog = tdms_file["Analog"]
                all_analog_channels = group_analog.channels()
                group_zyklus = tdms_file["Zyklus"]
                all_zyklus_channels = group_zyklus.channels()
                channel_log_bemerkung = group_log["Bemerkung"]
                channel_log_zeit = group_log["Zeit"]
                messung.pfad = dateiname
                messung.name = os.path.basename(dateiname)
                messung.start = tdms_file.properties["name"]
                messung.zyklen = len(group_zyklus["Zyklus"])
                for n in range(0, len(channel_log_zeit)):
                    messung.kommentare.update({((arrow.get(channel_log_zeit[n].astype(datetime.datetime)).to("local")).
                                                format("DD-MM-YYYY HH:mm:ss")): str(channel_log_bemerkung[n])})
                for n in range(1, len(group_temp)):
                    messung.channels_temp.append(all_temp_channels[n].name)
                for n in range(1, len(group_analog)):
                    messung.channels_analog.append(all_analog_channels[n].name)
                for n in range(2, len(group_zyklus)):
                    messung.channels_zyklus.append(all_zyklus_channels[n].name)
                # Schließen der TDMS-Datei
                tdms_file.close()
                # Statusbar auf ok setzen
                self.controller.status_ok()
                # Objekt der Messung als MessungInfo im Dictionary von root speichern
                self.controller.messungen[messung.name] = messung
                # Messung zum UI (Listbox) hinzufügen
                # Listbox unselect, da sonst Fehler, weil aktuell nur ein Item selektiert sein darf
                self.messung_liste.selection_clear(0, tk.END)
                self.messung_liste.insert(tk.END, messung.name)
                self.messung_liste.select_set("end")
                self.messung_liste.event_generate("<<ListboxSelect>>")

        except FileNotFoundError:
            messagebox.showerror("Error", f"Die Datei {dateiname} wurde nicht gefunden oder konnte nicht "
                                          f"verarbeitet werden!")

    def del_messung(self):
        # ----------------------------------------------------------
        # -- Funktion zum Löschen einer Messung aus der Anwendung --
        # ----------------------------------------------------------
        if self.messung_liste.curselection() != ():
            selected_index = self.messung_liste.curselection()
            del self.controller.messungen[self.messung_liste.get(selected_index)]
            # falls die Datei nach dem Schließen wieder geöffnet wird
            if self.listbox_last == self.messung_liste.get(selected_index):
                self.listbox_last = ""
            self.messung_liste.delete(selected_index)
            self.messung_liste.event_generate("<<ListboxSelect>>")
        else:
            return

    def _save_log(self):
        # -------------------------------------------------------------
        # -- Funktion zum Speichern der Kommentare in eine Textdatei --
        # -------------------------------------------------------------
        if self.messung_liste.curselection() != ():
            dateiname = f"{self.controller.messungen[self.messung_liste.get(self.messung_liste.curselection())].name.rsplit('.', 1)[0]}_log_channel"
            datei = asksaveasfilename(
                title="Kommentare speichern",
                defaultextension=".txt",
                initialfile=f"{dateiname}.txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            )

            if not datei:
                return

            with open(datei, mode="w", encoding="utf-8") as log_file:
                text = self.txt_komment.get("1.0", tk.END)
                log_file.write(text)
        else:
            messagebox.showwarning("Achtung", "Es wurde keine Messung ausgewählt.")
            return
