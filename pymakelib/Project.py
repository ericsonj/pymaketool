# __settings = None
from pymakelib import Pymaketool
from pymakelib import log
from pymakelib.Module import CompilerOptions
from pymakelib import D

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

def isdefined(key) -> bool:
    """Check if project have define.

    Args:
        key (str or D): name of define or macro

    Returns:
        bool: True if key is defined
    """
    sett = getSettings()
    macros = sett['COMPILER_OTPS']['MACROS']
    return (key in macros)


def define(key) -> str:
    """Get value of define if exist.

    Args:
        key (str): name of define (macro)

    Returns:
        str: value of define in string, if define value is None return '',if key is not defined return None
    """    
    sett = getSettings()
    macros = sett['COMPILER_OTPS']['MACROS']
    if isdefined(key):
        value = macros[key]
        return '' if not value else str(value)
    else:
        return None


def getCompilerOpts() ->  dict:
    """Get the project compiler options

    Returns:
        dict: General project compiler options
    """
    return getSettings()['COMPILER_OTPS']
