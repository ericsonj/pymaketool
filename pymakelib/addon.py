import inspect

initAddonFuncs = []
initAddonClass = []

def init(func):
    initAddonFuncs.append(func)


def add(inst):
    if inspect.isclass(inst):
        initAddonClass.append(inst)
    elif inspect.isfunction(inst):
        initAddonFuncs.append(inst)


class AddonAbstract:
    def __init__(self, projectSettings, compilerSettings):
        self.projectSettings = projectSettings
        self.compilerSettings = compilerSettings
    def init(self):
        pass