from pathlib import Path
from . import preconts

def readIgnoreFile(file = Path(preconts.MODULEIGNORE_FILE)):
    ignorelist = []
    try:
        ignoreFile = open(str(file), 'r')
        for line in ignoreFile:
            ignorelist.append(Path(line.rstrip()))
    except:
        pass
    return ignorelist


def writeIgnoreFile( ignoreList: list, file = Path(preconts.MODULEIGNORE_FILE)):

    currList = readIgnoreFile(file)

    try:

        ignoreFile = open(str(file), "w")

        for item in ignoreList:
            if not Path(item) in currList:
                currList.append(item)
        
        ignores = list(map(str, currList))
        ignores = map(lambda x: x + '\n', ignores)
        ignoreFile.writelines(ignores)

    except Exception as e:
        print(e)