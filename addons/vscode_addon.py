from pymakelib import plugin
import json
import os

@plugin.init
def vscode_init(projSett, compSett):
    # print(projSett) 
    # print(compSett)
    defines = []
    for d, v in projSett['C_SYMBOLS'].items():
        if not v is None: 
            defines.append(str(d) + "=" + str(v))
        else:
            defines.append(str(d))


    c_cpp_properties = {
        "configurations": [
            {
                'name': 'gcc',
                'defines': defines,
                "compilerPath": compSett['CC'],
                "intelliSenseMode": "linux-gcc-x86",
                "cStandard": "gnu11",
                "cppStandard": "c++17",
                "includePath": projSett['C_INCLUDES'],
                "browse": {
                    "path": projSett['C_INCLUDES'],
                    "limitSymbolsToIncludedHeaders": True,
                    "databaseFilename": "${workspaceFolder}/.vscode/browse.vc.db"
                }
            }
        ],
        "version": 4
    }
    output = json.dumps(c_cpp_properties, indent=4)
    if not os.path.exists('.vscode'):
        os.makedirs('.vscode')
    fileout = open(".vscode/c_cpp_properties.json", "w")
    fileout.write(output)
    fileout.close()