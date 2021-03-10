.. _addons:

Addons
======

pymaketool support addons for extenden functionalities. The addons will be executed before the compilation of the project.
Add the next lines en **Makefile.py**

.. code-block:: python

    from pymakelib import addon

    addon.add(yourAddonFunction)
    # or
    addon.add(yourAddonClass)

Addon  function
---------------

Simple addon, her entry point is a function with two arguments, for example:

.. code-block:: python

    def myAddon(projectSettins, compilerSettings):
        """
        Print project and compiler settings
        """
        print(projectSettins)
        print(compilerSettings)

VSCODE Addon
------------

vscode_addon.py is a simple addon that generate c_cpp_properties.json and launch.json

.. code-block:: python

    import json
    import os

    def vscodeGen_c_cpp_properties(projSett, compSett):
        """
        Generate file .vscode/c_cpp_properties.json
        """
        defines = []
        for d, v in projSett['C_SYMBOLS'].items():
            if not v is None:
                defines.append(str(d) + "=" + str(v))
            else:
                defines.append(str(d))

        # Change here
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
        print("Generate .vscode/c_cpp_properties.json")
        fileout = open(".vscode/c_cpp_properties.json", "w")
        fileout.write("// pymaketool: File autogenerate, see vscode_plugin.py\n")
        fileout.write(output)
        fileout.close()


    def vscodeGen_launch(projSett, compSett):
        """
        Generate file .vscode/launch.json
        """
        outputFile = projSett['C_TARGETS']['TARGET']['FILE']
        launch = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "(gdb) Launch",
                    "type": "cppdbg",
                    "request": "launch",
                    "program": "${workspaceFolder}/" + str(outputFile),
                    "args": [],
                    "stopAtEntry": False,
                    "cwd": "${workspaceFolder}",
                    "environment": [],
                    "console": "externalTerminal",
                    "MIMode": "gdb",
                    "setupCommands": [
                        {
                            "description": "Enable pretty-printing for gdb",
                            "text": "-enable-pretty-printing",
                            "ignoreFailures": True
                        }
                    ]
                }
            ]
        }

        output = json.dumps(launch, indent=4)
        if not os.path.exists('.vscode'):
            os.makedirs('.vscode')
        print("Generate .vscode/launch.json")
        fileout = open(".vscode/launch.json", "w")
        fileout.write("// pymaketool: File autogenerate, see vscode_plugin.py\n")
        fileout.write(output)
        fileout.close()

    def vscode_init(projSett, compSett):
        """
        Entry point of vscode_addon
        """
        # print(projSett) 
        # print(compSett)
        vscodeGen_c_cpp_properties(projSett, compSett)
        vscodeGen_launch(projSett, compSett)

Add in Makefile.py the line:

.. code-block:: python

    addon.add(vscode_init)

Addon  class
------------

Scalable version for development and extenden addons, for example:

.. code-block:: python

    from pymakelib import addon

    class MyAddon(addon.AddonAbstract):
        """
        Print project and compiler settings
        """
        def init(self):
            print(self.projectSettins)
            print(self.compilerSettings)
            
Add in Makefile.py the line:

.. code-block:: python

    addon.add(MyAddon)