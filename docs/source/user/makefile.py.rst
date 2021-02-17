.. _makefile.py:

Makefile.py
===========

**Makefile.py** is used to build **vars.mk** and **targets.mk**.

Example of Makefile.py for build a linux application:

.. code-block:: python

    from os.path import basename
    from pymakelib import MKVARS
    from pymakelib import Toolchain as tool

    def getProjectSettings():
        """
        Return the project settings.

        Returns:
            dict: with keys PROJECT_NAME and FODLER_OUT
        """
        return {
            'PROJECT_NAME': basename(os.getcwd()),
            'FOLDER_OUT':   'Release/Objects/'
        }

    def getTargetsScript():
        """
        Return the of targets
        """
        PROJECT_NAME = basename(os.getcwd())
        FOLDER_OUT = 'Release/'
        TARGET = FOLDER_OUT + PROJECT_NAME

        TARGETS = {
            # target
            'TARGET': {
                # key of target
                'LOGKEY':  'OUT',
                # Name of output file
                'FILE':    TARGET,
                # Script to generate de output file
                'SCRIPT':  [MKVARS.LD, '-o', '$@', MKVARS.OBJECTS, MKVARS.LDFLAGS]
            },
            'TARGET_ZIP': {
                # key of target
                'LOGKEY':   'ZIP',
                # Name of output file
                'FILE':     TARGET + '.zip',
                # Script to generate de output file
                'SCRIPT':   ['zip', TARGET + '.zip', MKVARS.TARGET]
            }
        }

        return TARGETS


    def getCompilerSet():
        """
        Return the compilet set.

        Returns:
            dict with path of executables: 
            'CC', 'CXX', 'LD', 'AR', 'AS', 'OBJCOPY', 'SIZE', 'OBJDUMP'. 
        """
        return tool.confLinuxGCC()


    LIBRARIES = [ '-lpthread']

    def getCompilerOpts():
        """
        Return all compiler options.

        Returns:
            dict with:
            KEY: name of group of options
            VALUE: list of options
        """
        PROJECT_DEF = {
            'HAVE_CONFIG_H':  None
        }

        return {
            'MACROS': PROJECT_DEF,
            'MACHINE-OPTS': [
            ],
            'OPTIMIZE-OPTS': [
            ],
            'OPTIONS': [
            ],
            'DEBUGGING-OPTS': [
                '-g3'
            ],
            'PREPROCESSOR-OPTS': [
                '-MP',
                '-MMD'
            ],
            'WARNINGS-OPTS': [
            ],
            'CONTROL-C-OPTS': [
                '-std=gnu11'
            ],
            'GENERAL-OPTS': [
            ],
            'LIBRARIES': LIBRARIES
        }


    def getLinkerOpts():
        """
        Return all linker options.

        Returns:
            dict with:
            KEY: name of group of options
            VALUE: list of options
        """
        return {
            'LINKER-SCRIPT': [
            ],
            'MACHINE-OPTS': [
            ],
            'GENERAL-OPTS': [
            ],
            'LINKER-OPTS': [
            ],
            'LIBRARIES': LIBRARIES
        }

Example of Makefile to build firmware for STM32F4 microcontroller:

.. code-block:: python

    import os
    from os.path import basename
    from pybuild import MKVARS

    PROJECT_NAME = basename(os.getcwd())
    FOLDER_OUT = 'Release/stm32f4-sandbox/'

    TARGET_ELF = FOLDER_OUT + PROJECT_NAME + '.elf'
    TARGET_HEX = FOLDER_OUT + PROJECT_NAME + '.hex'
    TARGET_MAP = FOLDER_OUT + PROJECT_NAME + '.map'
    TARGET_BIN = FOLDER_OUT + PROJECT_NAME + '.bin'


    def getProjectSettings():
        return {
            'PROJECT_NAME': PROJECT_NAME,
            'FOLDER_OUT':   FOLDER_OUT,
        }


    def getTargetsScript():

        TARGETS = {
            'TARGET': {
                'LOGKEY':  'LD',
                'FILE':    TARGET_ELF,
                'SCRIPT':  [MKVARS.LD, '-o', '$@', MKVARS.OBJECTS, MKVARS.LDFLAGS]
            },
            'TARGET_HEX': {
                'LOGKEY':   'HEX',
                'FILE':     TARGET_HEX,
                'SCRIPT':   [MKVARS.OBJCOPY, '-O', 'ihex', MKVARS.TARGET, TARGET_HEX]
            },
            'TARGET_BIN': {
                'LOGKEY':   'BIN',
                'FILE':     TARGET_BIN,
                'SCRIPT':   [MKVARS.OBJCOPY, '-O', 'binary', MKVARS.TARGET, TARGET_BIN]
            }
        }

        return TARGETS


    def getCompilerSet():
        pfx = 'arm-none-eabi-'
        return {
            'CC':       pfx + 'gcc',
            'CXX':      pfx + 'g++',
            'LD':       pfx + 'gcc',
            'AR':       pfx + 'ar',
            'AS':       pfx + 'as',
            'OBJCOPY':  pfx + 'objcopy',
            'SIZE':     pfx + 'size',
            'OBJDUMP':  pfx + 'objdump',
            'INCLUDES': [
                toolchain + 'arm-none-eabi/include',
                toolchain + 'arm-none-eabi/include/c++/8.2.1',
                toolchain + 'arm-none-eabi/include/c++/8.2.1/arm-none-eabi',
                toolchain + 'arm-none-eabi/include/c++/8.2.1/backward',
                toolchain + 'lib/gcc/arm-none-eabi/8.2.1/include',
                toolchain + 'lib/gcc/arm-none-eabi/8.2.1/include-fixed'
            ]
        }


    def getCompilerOpts():

        PROJECT_DEF = {
            'USE_HAL_DRIVE':            None,
            'CORE_CM4':                 None,
            'STM32F407xx':              None,
            'DEBUG':                    None,
            'VERSION':                  "0.0.1",
            'STM32F4xx':                None,
        }

        return {
            'MACROS': PROJECT_DEF,
            'MACHINE-OPTS': [
                '-mcpu=cortex-m4',
                '-mfpu=fpv4-sp-d16',
                '-mfloat-abi=hard',
                '-mthumb'
            ],
            'OPTIMIZE-OPTS': [
                '-O0'
            ],
            'OPTIONS': [
                '-ffunction-sections',
                '-fstack-usage',
                '-fdata-sections '
            ],
            'DEBUGGING-OPTS': [
                '-g3'
            ],
            'PREPROCESSOR-OPTS': [
                '-MP',
                '-MMD'
            ],
            'WARNINGS-OPTS': [
                '-Wall'
            ],
            'CONTROL-C-OPTS': [
                '-std=gnu11'
            ],
            'GENERAL-OPTS': [
                '--specs=nano.specs'
            ]
        }


    def getLinkerOpts():
        return {
            'LINKER-SCRIPT': [
                '-TSTM32F407VETX_FLASH.ld'
            ],
            'MACHINE-OPTS': [
                '-mcpu=cortex-m4',
                '-mfpu=fpv4-sp-d16',
                '-mfloat-abi=hard',
                '-mthumb'
            ],
            'GENERAL-OPTS': [
                '--specs=nosys.specs'
            ],
            'LINKER-OPTS': [
                '-Wl,-Map='+TARGET_MAP,
                '-Wl,--gc-sections',
                '-static',
                '-Wl,--start-group',
                '-lc',
                '-lm',
                '-Wl,--end-group',
                '-u_printf_float'
            ]
        }

Makeclass
---------

**Makefile.py** in class mode:

.. code-block:: python
    
    from pymakelib import IProject, Makeclass

    @Makeclass
    class Project(IProject):

        def getProjectSettings(self, **kwargs):
            ...

        def getTargetsScript(self, **kwargs):
            ...

        def getCompilerSet(self, **kwargs):
            ...

        def getCompilerOpts(self, **kwargs):
            ...
        
        def getLinkerOpts(self, **kwargs):
            ...
