from .addon import AddonAbstract
from . import eclipse_cproject as cp

class EclipseAddon(AddonAbstract):
    """
    Generate Eclipse cproject files.
    """
    def init(self):
        self.generateLanguageSettings()
        self.generateCProject()

    def generateLanguageSettings(self):
        compSett = self.compilerSettings
        cp.generate_languageSettings(compSett)

    def generateCProject(self):
        projSett = self.projectSettings
        cp.generate_cproject(projSett)