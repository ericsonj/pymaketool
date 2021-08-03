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

    def write(self, value):
        self.output.append(value)

    @abstractmethod
    def process(self) -> str:
        pass


class VarsGenerator(Generator):

    def __init__(self, project: Pymaketool):
        super().__init__(None, project)

    def write_cflags(self):
        compOpts = self.project.compilerOpts
        if isinstance(compOpts, dict):
            for key in compOpts:
                self.write('# {0}\n'.format(key))
                if (key == 'MACROS' and isinstance(compOpts[key], dict)):
                    self.write(
                        'COMPILER_FLAGS += {}\n'.format(macrosDictToString(compOpts[key])))
                else:
                    self.write('COMPILER_FLAGS += {}\n'.format(' '.join(compOpts[key])))
            self.write('\n')
        elif isinstance(compOpts, list):
            for item in compOpts:
                self.write('COMPILER_FLAGS += {}\n'.format(item))
            self.write('\n')
        else:
            log.debug("Not load getCompilerOpts")

    def write_ldflags(self):
        print(self.project.compilerOpts)
        # if isinstance(linkOpts, dict):
        #     for keys in linkOpts:
        #         makevars.write('# {0}\n'.format(keys))
        #         makevars.write(
        #             'LDFLAGS += {}\n'.format(list2str(linkOpts[keys])))
        # elif isinstance(linkOpts, list):
        #     for item in linkOpts:
        #         makevars.write('LDFLAGS += {}\n'.format(item))

    def process(self) -> str:
        # strproj = self.project.projSettings['PROJECT_NAME']
        # strproj_out = self.project.projSettings['FOLDER_OUT']
        # self.write(f"PROJECT = {strproj}\n")
        # self.write(f"PROJECT_OUT = {strproj_out}\n")
        # self.write('\n')

        for key, value in self.project.projSettings.items():
            self.write(f"{key} = {value}\n")
        self.write('\n')
        
        for key, value in self.project.compilerSettings.items():
            if key != 'INCLUDES':
                self.write(f"{key:<10} := {value}\n")
        self.write('\n')

        self.write_cflags()
        self.write('\n')

        self.write_ldflags()

        return ''.join(self.output)

class SrcsGenerator(Generator):

    def __init__(self, module, project: Pymaketool):
        super().__init__(module, project)
        self.isstaticlib = isinstance(module, StaticLibraryModule)
        if self.isstaticlib:
            mod:StaticLibraryModule = module
            mod.decorate_module()

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
        if self.isstaticlib:
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
            isstatic = self.isstaticlib
            for src in srcs:
                if isstatic:
                    objs = str(src).replace('.c', '.o').replace('.s', '.o')
                    outputObj = '$({}_OUTPUT)/'.format(self.module.key) + str(objs)
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
        self.write('{}_NAME = {}\n'.format(mod.key, mod.name))
        self.write('{}_OUTPUT = {}\n'.format(mod.key, str(mod.output_dir)))
        library = mod.output_dir / Path('lib'+mod.name+'.a')
        self.write('{}_AR = {}\n'.format(mod.key, str(library)))
        self.write('\n')

    def write_staticlib_rules(self):
        mod: StaticLibraryModule = self.module
        self.write('{0}'.format(mod.objects))
        self.write('\n\n' if mod.objects else '')
        self.write('{}'.format(mod.rule))
        self.write('\n\n' if mod.rule else '')
        self.write('{}\n'.format(mod.command))
        self.write('\n\n')
        self.write('SLIBS_NAMES += {}\n'.format(mod.linker))
        self.write('SLIBS_OBJECTS += {}\n'.format(mod.library))
        if mod.rebuild:
            self.write('\n')
            for src in mod.getSrcs():
                obj = str(src).replace('.c', '.o').replace('.s', '.o')
                outputObj = '$({}_OUTPUT)/'.format(mod.key) + str(obj)
                self.write("{} : .FORCE\n".format(outputObj))
            self.write('\n')

    def process(self) -> str:
        self.write_header()
        if self.isstaticlib:
            self.write_staticlib_def()
        self.write_srcs()
        self.write_incs()
        self.write_compiler_opts()
        if self.isstaticlib:
            self.write_staticlib_rules()
        return ''.join(self.output)


class TargetsGenerator(Generator):

    def __init__(self, project: Pymaketool):
        super().__init__(None, project)

    def process(self) -> str:
        targets = self.project.compilerOpts['TARGETS']
        for key, value in targets.items():
            filedep = value['FILE']
            self.write(f"{key:<15} = {filedep}\n")
        self.write('\n')

        keylist = list(targets)
        last_target = keylist[-1]
        self.write(f"TARGETS = $({last_target})\n")
        self.write('\n')

        count = 0
        for key, value in targets.items():
            filedep = value['FILE']
            script  = ' '.join(value['SCRIPT'])
            logkey  = value['LOGKEY']

            if (key == 'TARGET'):
                self.write(f"$({key}): $(OBJECTS) $(SLIBS_OBJECTS)")
            else:
                self.write(f"$({key}):")

            if count:
                self.write(" $({})\n".format(keylist[count - 1]))
            else:
                self.write("\n")

            self.write(f"\t$(call logger-compile,\"{logkey}\",$@)\n")
            self.write(f"\t{script}\n")
            self.write("\n")
            count += 1

        self.write("clean_targets:\n")
        self.write("\trm -rf")
        for key in keylist:
            self.write(f" $({key})")
        self.write('\n')

        return ''.join(self.output)