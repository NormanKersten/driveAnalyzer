###################################################################################################
# -- Modul für Daten-Klassen -------------------------------------------------------------------- #
###################################################################################################

class MessungInfo:
    def __init__(self):
        self.pfad = ""
        self.name = ""
        self.start = ""
        self.zyklen = ""
        self.kommentare = dict()
        self.channels_temp = []
        self.channels_analog = []
        self.channels_zyklus = []
