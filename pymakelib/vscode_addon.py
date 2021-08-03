from .addon import AddonAbstract
from pathlib import Path
import json

class VSCodeAddon(AddonAbstract):

    def init(self):
        newfile = False
        c_cpp_prop = ".vscode/c_cpp_properties.json"
        aux = Path(c_cpp_prop)
        if aux.exists():
            pass
        else:
            Path(".vscode").mkdir(exist_ok=True)
            c_cpp_prop = str(aux)
            newfile = True
            
        json_prop = None
        if not newfile:
            _tmp_cpp = open(c_cpp_prop)
            json_prop = _tmp_cpp.read()
            _tmp_cpp.close()
            
        file_c_cpp = open(str(c_cpp_prop), "w")
        if newfile:
            prop = self.__create_basic_c_cpp_prop()
        else:
            try:
                prop = json.loads(json_prop)
            except Exception as ex:
                print("error load json", ex)
                prop = self.__create_basic_c_cpp_prop()

        self.__fill_properties(prop)
        print("Generate .vscode/c_cpp_properties.json")
        file_c_cpp.write(json.dumps(prop, indent=4))
        file_c_cpp.close()


    def __create_basic_c_cpp_prop(self):
        c_cpp_properties = {
            "configurations": [
                {
                    'name': 'pymaketool',
                    'defines': None,
                    "compilerPath": None,
                    "intelliSenseMode": "linux-gcc-x86",
                    "cStandard": "gnu11",
                    "cppStandard": "c++17",
                    "includePath": None,
                    "browse": {
                        "path": None,
                        "limitSymbolsToIncludedHeaders": True,
                        "databaseFilename": "${workspaceFolder}/.vscode/browse.vc.db"
                    }
                }
            ],
            "version": 4
        }
        return c_cpp_properties
    
    def __fill_properties(self, prop):
        projSett = self.projectSettings
        compSett = self.compilerSettings

        defines = []
        for d, v in projSett['C_SYMBOLS'].items():
            if not v is None:
                defines.append(str(d) + "=" + str(v))
            else:
                defines.append(str(d))

        browse = []        
        for inc in projSett['C_INCLUDES']:
            i = Path(inc)
            browse.append(str(i.parent))

        browse = list(set(browse)) 

        for config in prop['configurations']:
            if config['name'] == "pymaketool":
                config['defines'] = defines
                config['compilerPath'] = compSett['CC']
                config['includePath'] = projSett['C_INCLUDES']
                config['browse']['path'] = browse
                break