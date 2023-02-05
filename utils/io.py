import pathlib
from tkinter import filedialog as fd


###################################################################################################
# -- I/O Funktionen ----------------------------------------------------------------------------- #
###################################################################################################

# Funktion zum Öffnen einer Messdatei
def select_file():
    filetypes = (
        ("TDMS-Dateien", "*.tdms"),
        ("Alle Dateien", "*.*")
    )

    filename = fd.askopenfilename(
        title="Datei öffnen",
        # Ohne Parameter "initialdir" wird unter Win 10 das letzte Verzeichnis angezeigt
        # initialdir="/",
        filetypes=filetypes)

    if pathlib.Path(filename).suffix == ".tdms":
        return filename
    else:
        return False
