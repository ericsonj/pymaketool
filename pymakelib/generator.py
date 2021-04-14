from os import write
from pathlib import Path
from . import Define as D
from . import preconts as K
from . import Pymaketool
from .module import AbstractModule, StaticLibraryModule
from . import Logger
from abc import ABC, abstractmethod

from pymakelib import module

log = Logger.getLogger()

def getLineSeparator(key: str, num: int):
    header = ''
    for _ in range(num):
        header += key
    return header

def macrosDictToString(macros):
    mstr = []
    if isinstance(macros, dict):
        for key in macros:
            if macros[key] != None and macros[key] != '':
                if isinstance(macros[key], str):
                    mstr.append('-D{}=\\\"{}\\\"'.format(key, macros[key]))
                elif isinstance(macros[key], bool):
                    mstr.append(
                        '-D{}={}'.format(key, '1' if macros[key] else '0'))
                elif isinstance(macros[key], D):
                    mstr.append(
                        '-D{}={}'.format(key, macros[key].getDefine()))
                else:
                    mstr.append('-D{}={}'.format(key, macros[key]))
            else:
                mstr.append('-D{}'.format(key))

    return ' '.join(mstr)


class Generator(ABC):

    def __init__(self, module: AbstractModule, project: Pymaketool):
        self.module = module
        self.project = project
        self.output = []

    @abstractmethod
    def process(self) -> str:
        pass

class MakeGenerator(Generator):

    def __init__(self, module: AbstractModule, project: Pymaketool):
        super().__init__(module, project)

    def isstaticlib(self):
        return isinstance(self.module, StaticLibraryModule)

    def write(self, value):
        self.output.append(value)

    def get_srcs_dirs(self, srcs) -> list:
        dirs = []
        for src in srcs:
            dirs.append(Path(str(src)).parent)
        dirs = list(set(dirs))
        return dirs

    def compiler_opts2str(self, compiler_opts):
        mstr = []
        def proc(moduleCompileOps):
            if isinstance(moduleCompileOps, dict):
                for key in moduleCompileOps:
                    if key == 'TARGETS':
                        continue
                    if (key == K.COMPOPTS_MACROS_KEY and isinstance(moduleCompileOps[key], dict)):
                        macros = macrosDictToString(moduleCompileOps[key])
                        mstr.append(macros)
                    else:
                        mstr.append(' '.join(moduleCompileOps[key]))

            elif isinstance(moduleCompileOps, list):
                for item in moduleCompileOps:
                    mstr.append(item)

        if isinstance(compiler_opts, dict):
            proc(compiler_opts)
        elif isinstance(compiler_opts, list):
            for moduleCompileOps in compiler_opts:
                proc(moduleCompileOps)

        rmstr = list(filter(lambda item: item, mstr))
        rmstr = ' '.join(rmstr)
        rmstr = ' '.join(rmstr.split())
        log.debug(f"compiler options: {rmstr}")
        return rmstr

    def write_header(self):
        mod_path =  f"{self.module.path}"
        self.write("{}\n".format(getLineSeparator('#', 52)))
        self.write("#{0:^50}#\n".format(mod_path))
        self.write("{}\n".format(getLineSeparator('#', 52)))
        self.write("\n")

    def write_srcs(self):
        prefixSrcs = ""
        if self.isstaticlib():
            prefixSrcs = self.module.name.upper() + "_"
        srcs = self.module.getSrcs()
        for src in srcs:
            if str(src).endswith('.c'):
                self.write("{}CSRC += {}\n".format(prefixSrcs, src))
            elif str(src).endswith('.cpp'):
                self.write("{}CXXSRC += {}\n".format(prefixSrcs, src))
            elif str(src).endswith('.s'):
                self.write("{}ASSRC += {}\n".format(prefixSrcs, src))
        self.write('\n') if srcs else None

    def write_incs(self):
        incs = self.module.getIncs()
        for inc in incs:
            if inc:
                self.write("INCS += -I{}\n".format(inc))
        self.write('\n') if incs else None

    def write_compiler_opts(self):
        proj_settings = self.project.projSettings;
        comp_opts = self.module.getCompilerOpts()
        if comp_opts:
            srcs = self.module.getSrcs()
            isstatic = self.isstaticlib()
            for src in srcs:
                if isstatic:
                    objs = str(src).replace('.c', '.o').replace('.s', '.o')
                    mkkey = self.module.name.upper()
                    outputObj = '$({}_OUTPUT)/'.format(mkkey) + str(objs)
                    self.write("{} : CFLAGS = {}\n".format(str(outputObj), self.compiler_opts2str(comp_opts)))
                else:
                    objs = str(src).replace('.cpp', '.o')
                    objs = objs.replace('.c', '.o')
                    objs = objs.replace('.s', '.o')
                    ouputobj = Path(str(proj_settings['FOLDER_OUT']) + '/' + str(objs))
                    log.debug(ouputobj)
                    self.write("{} : CFLAGS = {}\n".format(str(ouputobj), self.compiler_opts2str(comp_opts)))


    def write_staticlib_def(self):
        mod: StaticLibraryModule = self.module
        log.debug(f"module \'{mod.path}\' static library name {mod.name}")
        log.debug(f"module \'{mod.path}\' static output directory {mod.output_dir}")
        mkkey = mod.name.upper()
        self.write('{}_NAME = {}\n'.format(mkkey, mod.name))
        self.write('{}_OUTPUT = {}\n'.format(mkkey, str(mod.output_dir)))
        library = mod.output_dir / Path('lib'+mod.name+'.a')
        self.write('{}_AR = {}\n'.format(mkkey, str(library)))
        self.write('\n')

    def write_staticlib_rules(self):
        mod: StaticLibraryModule = self.module
        mkkey = mod.name.upper()
        self.write('{0}'.format(mod.lib_objs))
        self.write('\n\n' if mod.lib_objs else '')
        self.write('{}'.format(mod.lib_objs_compile))
        self.write('\n\n' if mod.lib_objs_compile else '')
        self.write('{}\n'.format(mod.lib_compile))
        self.write('\n\n')
        self.write('SLIBS_NAMES += {}\n'.format(mod.lib_linked))
        self.write('SLIBS_OBJECTS += {}\n'.format(mod.library))
        if mod.rebuild:
            self.write('\n')
            for src in mod.getSrcs():
                obj = str(src).replace('.c', '.o').replace('.s', '.o')
                mkkey = mod.name.upper()
                outputObj = '$({}_OUTPUT)/'.format(mkkey) + str(obj)
                self.write("{} : .FORCE\n".format(outputObj))
            self.write('\n')

    def process(self) -> str:
        self.write_header()
        if self.isstaticlib():
            self.write_staticlib_def()
        self.write_srcs()
        self.write_incs()
        self.write_compiler_opts()
        if self.isstaticlib():
            self.write_staticlib_rules()
        return ''.join(self.output)


# class MakeGeneratorStaticLib(MakeGenerator):

#     def write_srcs(self):
#         prefix = self.module.module_name.upper() + "_"
#         srcs = self.module.getSrcs()
#         for src in srcs:
#             if str(src).endswith('.c'):
#                 self.write("{}CSRC += {}\n".format(prefix,src))
#             elif str(src).endswith('.cpp'):
#                 self.write("{}CXXSRC += {}\n".format(prefix,src))
#             elif str(src).endswith('.s'):
#                 self.write("{}ASSRC += {}\n".format(prefix, src))
#         self.write('\n') if srcs else None

