from pymakelib import module
import inspect
import logging
import sys

def __getmodule_caller(func):
    def stack_(frame):
        framelist = []
        while frame:
            framelist.append(frame)
            frame = frame.f_back
        return framelist

    stack_list = stack_(sys._getframe(1))
    idx = 0
    for stack in stack_list:
        idx += 1
        if stack.f_code.co_name == func:
            break
    parentframe = stack_list[idx]
    return parentframe.f_code.co_filename


def add_library(name, outputdir, srcs=[], incs=[]):

    @module.ModuleClass
    class _(module.BasicCModule, module.StaticLibraryModule):
                   
        def get_module_name(self):                  # 
            return str(name).capitalize()           #
                                                    # Not need in class mode
        def get_path(self):                         #
            return __getmodule_caller('add_library')  #

        def get_lib_name(self) -> str:
            return name

        def get_lib_outputdir(self) -> str:
            return outputdir

        def getSrcs(self):
            return super().getSrcs() if not srcs else srcs

        def getIncs(self):
            return super().getIncs() if not incs else incs