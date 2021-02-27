# __settings = None
from pymakelib import Pymaketool
from pymakelib import log
from pymakelib.Module import CompilerOptions

def setSettings(settings):
    global __settings
    try:
        _ = __settings
    except NameError:
        log.debug(f"create global modules list")
        __settings = settings


def getSettings():
    auxsetts = None
    try:
        _ = __settings
        return __settings
    except NameError:
        log.debug("not project settings found")
        p = Pymaketool()
        globalSettings = {
            'PROJECT_SETTINGS':  p.projSettings,
            'COMPILER_OTPS':     p.compilerOpts,
            'COMPILER_SETTINGS': p.compilerSettings
        }
        setSettings(globalSettings)
        auxsetts = __settings
        pass
    return auxsetts

    
