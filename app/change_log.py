###################################################################################################
# -- Klasse mit Informationen zur Anwendung ----------------------------------------------------- #
###################################################################################################

class DriveAnalyzerVersion:
    def __init__(self):
        self.name = "DriveAnalyzer"
        self.change_log = dict()
        # Change_log erzeugen
        self._update_change_log()

    def get_version(self):
        return list(self.change_log.keys())[-1]
        # Für ChangeLog: list(self.change_log.values())[-1]

    def get_name(self):
        return self.name

    def _update_change_log(self):
        self.change_log.update({"V0.3 vom 04-02-2023": "Testversion"})
        # self.change_log.update({"Version": "V1.0 vom 10-02-2023", "ChangeLog": "Initialer Release"})
