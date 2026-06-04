#!/usr/bin/env python3

# Copyright (c) 2020, Ericson Joseph
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of pyMakeTool nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from pathlib import Path
import sys
import os
import re
import copy
import argparse
from pymakelib import preconts as K
from pymakelib import prelib as plib
from pymakelib import moduleignore
from pymakelib import eclipse_files
from pymakelib import make_files
from pymakelib import addon
from pymakelib import Logger
from pymakelib import project
from pymakelib import getProjectInstance
from pymakelib.version import get_version

log = Logger.getLogger()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "goal", type=str, help="Makefile command goal", default=None, nargs="?"
    )
    parser.add_argument(
        "--init",
        type=str,
        help="initialize project",
        const=os.path.basename(os.getcwd()),
        dest="project_name",
        nargs="?",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {get_version()}")
    args = parser.parse_args()

    goal = args.goal

    if args.project_name:
        # Default subdir for new projects
        subdir = K.MAKEFILE_SUBDIR_CANDIDATES[0]  # 'pymake'
        subdir_path = Path(subdir)

        fproject = open(".project", "w")
        print("Init {0} project (layout: {1}/)".format(args.project_name, subdir))
        fproject.write(eclipse_files.FILE_PROJECT.format(args.project_name))
        fproject.close()
        try:
            subdir_path.mkdir(exist_ok=True)
        except Exception as e:
            log.exception(e)

        fileset = [
            ["Makefile", make_files.get_makefile_content(subdir=subdir)],
            [str(subdir_path / K.MAKEFILE_MK), make_files.get_makefile_mk_content(subdir=subdir)],
            [str(subdir_path / K.MAKEFILE_PY), make_files.FILE_MAKEFILE_PY],
        ]

        for f in fileset:
            try:
                fileout = open(f[0], "x")
                fileout.write(f[1])
                fileout.close()
            except Exception as e:
                log.exception(e)

        sys.exit()

    USE_EXCLUDE_FOLDERS = True

    # ------------------------------------------------------
    # ------------------------------------------------------
    # ------------------------------------------------------

    if not goal:
        print("pymaketool: error: Add a goal (target)")
        sys.exit()

    modules = []
    modulesPaths = []
    ignoreModuleList = []

    # Add project path to sys.path for users scripts
    sys.path.append(str(os.getcwd()))

    import warnings
    project_root = Path(".").resolve()
    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            config_dir, layout_mode = plib.resolve_config_dir(project_root)
        for w in caught_warnings:
            print(str(w.message), file=sys.stderr)
    except FileNotFoundError:
        print("Not a pymaketool project")
        sys.exit()

    projSettings, compilerOpts, compilerSettings = plib.read_Makefilepy(config_dir=config_dir)

    globalSettings = {
        "PROJECT_SETTINGS": projSettings,
        "COMPILER_OTPS": compilerOpts,
        "COMPILER_SETTINGS": compilerSettings,
    }

    project.setSettings(globalSettings)

    # Get ignore configuration from Makefile.py if available
    projectInstance = plib.getProjectInstance()
    ignore_config = {}
    if projectInstance and hasattr(projectInstance, 'getIgnoreConfig'):
        ignore_config = projectInstance.getIgnoreConfig()
    
    # Read and compile ignore patterns with gitignore-style semantics
    ignore_spec = moduleignore.read_ignore_spec(
        project_root=project_root,
        config_dir=config_dir,
        makefile_config=ignore_config
    )

    # Execute GenHeaders
    # Use os.walk(followlinks=True) so that symlinked directories (e.g.
    # TARGET/ and wrapper/ in the pytest-qemu-pic32mk workspace) are scanned.
    def _rglob_follow(pattern: str):
        import fnmatch
        results = []
        for root, dirs, files in os.walk(".", followlinks=True):
            for fname in files:
                if fnmatch.fnmatch(fname, pattern):
                    results.append(Path(root) / fname)
        return results

    headersPaths = _rglob_follow("*[.|_]h.py")
    for gheader in headersPaths:
        fileout = re.sub("[.|_]h.py", ".h", str(gheader))
        print(f"Generator: {gheader} > {fileout}")
        plib.readGenHeader(gheader)

    _make_inst_early = getProjectInstance()
    _raw_paths: list[Path] = list(set(_rglob_follow("*[.|_]mk.py")) | set(_rglob_follow("mk.py")))
    _sort_modules_fn = getattr(_make_inst_early, 'sort_modules', None) if _make_inst_early else None
    if callable(_sort_modules_fn):
        from typing import cast, Callable
        _typed_sort = cast(Callable[[list[Path]], list[Path]], _sort_modules_fn)
        modulesPaths: list[Path] = _typed_sort(_raw_paths)
    else:
        modulesPaths = sorted(_raw_paths)
    
    # Filter out ignored modules before loading (more efficient)
    if ignore_spec:
        filtered_paths = []
        for module_path in modulesPaths:
            # Normalize to project-relative POSIX path for matching
            try:
                rel_path = module_path.relative_to(project_root)
                posix_path = str(rel_path).replace('\\', '/')
            except ValueError:
                # Path outside project root, use as-is
                posix_path = str(module_path).replace('\\', '/')
            
            if not ignore_spec.match_file(posix_path):
                filtered_paths.append(module_path)
        
        modulesPaths = filtered_paths
    
    # Load modules
    for filename in modulesPaths:
        mod = plib.readModule(filename, copy.deepcopy(compilerOpts), goal, project_root=Path(".").resolve())
        modules.extend(mod)

    # Write CSRC
    srcsfile = open(config_dir / K.SRCS_MK, "w")

    includes = []

    def getLineSeparator(key: str, num: int):
        header = ""
        for _ in range(num):
            header += key
        return header

    log.debug("**load modules**")
    all_srcs = []
    _make_inst = getProjectInstance()
    _sort_fn = getattr(_make_inst, 'sort_sources', None) if _make_inst else None
    modules = sorted(modules, key=lambda mod: mod.orden)
    for mod in modules:
        if mod.isEmpty():
            log.debug(f"module '{mod.filename}' is empty, module skiped*")
            continue

        mod_filename = f"{mod.filename}:{mod.module_name}"
        print("Module: {}".format(mod_filename))
        log.info("read module '{}'".format(mod_filename))
        srcsfile.write("{}\n".format(getLineSeparator("#", 52)))
        srcsfile.write("#{0:^50}#\n".format(str(mod_filename)))
        srcsfile.write("{}\n".format(getLineSeparator("#", 52)))

        if mod.staticLib:
            log.debug(
                f"module '{mod_filename}' static library name {mod.staticLib.name}"
            )
            log.debug(
                f"module '{mod_filename}' static output directory {mod.staticLib.outputDir}"
            )
            mkkey = mod.staticLib.name.upper()
            srcsfile.write("{}_NAME = {}\n".format(mkkey, mod.staticLib.name))
            srcsfile.write(
                "{}_OUTPUT = {}\n".format(mkkey, str(mod.staticLib.outputDir))
            )
            library = mod.staticLib.outputDir / Path("lib" + mod.staticLib.name + ".a")
            srcsfile.write("{}_AR = {}\n".format(mkkey, str(library)))
            srcsfile.write("\n")

        prefixSrcs = ""
        if mod.staticLib:
            prefixSrcs = mod.staticLib.name.upper() + "_"

        _src_paths = [Path(s) for s in mod.srcs]
        _sorted_srcs = _sort_fn(_src_paths) if callable(_sort_fn) else sorted(_src_paths, key=str)
        for src in _sorted_srcs:
            if str(src).endswith(".c"):
                srcsfile.write("{}CSRC += {}\n".format(prefixSrcs, src))
            elif str(src).endswith(".cpp"):
                srcsfile.write("{}CXXSRC += {}\n".format(prefixSrcs, src))
            elif str(src).endswith((".s", ".S", ".asm")):
                srcsfile.write("{}ASSRC += {}\n".format(prefixSrcs, src))
            all_srcs.append(str(src))

        # Informational record of skip/exclude patterns (module-path prefixed).
        _skips = (getattr(mod, 'skip_srcs_patterns', []) or []) + (getattr(mod, 'skip_incs_patterns', []) or [])
        for pat in dict.fromkeys(_skips):
            srcsfile.write("SKIP_PATTERNS += {}\n".format(pat))

        srcsfile.write("\n")

        if not mod.staticLib:
            for d in sorted(mod.getDirs(), key=str):
                srcsfile.write("SRC_DIRS += {}\n".format(str(d)))

        srcsfile.write("\n")

        for inc in sorted(mod.incs, key=str):
            if inc:
                srcsfile.write("INCS += -I{}\n".format(inc))
                includes.append(inc)

        srcsfile.write("\n")

        if mod.flags:
            if mod.staticLib:
                for src in sorted(mod.srcs, key=str):
                    objs = (
                        str(src)
                        .replace(".c", ".o")
                        .replace(".s", ".o")
                        .replace(".S", ".o")
                        .replace(".asm", ".o")
                    )
                    mkkey = mod.staticLib.name.upper()
                    outputObj = "$({}_OUTPUT)/".format(mkkey) + str(objs)
                    srcsfile.write(
                        "{} : CFLAGS = {}\n".format(
                            outputObj, plib.compilerOptsByModuleToLine(mod.flags)
                        )
                    )
            else:
                for src in sorted(mod.srcs, key=str):
                    objs = str(src).replace(".cpp", ".o")
                    objs = objs.replace(".c", ".o")
                    objs = (
                        objs.replace(".s", ".o")
                        .replace(".S", ".o")
                        .replace(".asm", ".o")
                    )
                    ouputobj = Path(str(projSettings["FOLDER_OUT"]) + "/" + str(objs))
                    log.debug(ouputobj)
                    srcsfile.write(
                        "{} : CFLAGS = {}\n".format(
                            str(ouputobj), plib.compilerOptsByModuleToLine(mod.flags)
                        )
                    )

        srcsfile.write("\n")

        if mod.staticLib:
            mkkey = mod.staticLib.name.upper()
            srcsfile.write("{0}".format(mod.staticLib.lib_objs))
            srcsfile.write("\n\n" if mod.staticLib.lib_objs else "")
            srcsfile.write("{}".format(mod.staticLib.lib_objs_compile))
            srcsfile.write("\n\n" if mod.staticLib.lib_objs_compile else "")
            srcsfile.write("{}\n".format(mod.staticLib.lib_compile))
            srcsfile.write("\n\n")
            srcsfile.write("SLIBS_NAMES += {}\n".format(mod.staticLib.lib_linked))
            srcsfile.write("SLIBS_OBJECTS += {}\n".format(mod.staticLib.library))
            if mod.staticLib.rebuild:
                srcsfile.write("\n")
                for src in mod.srcs:
                    obj = (
                        str(src)
                        .replace(".c", ".o")
                        .replace(".s", ".o")
                        .replace(".S", ".o")
                        .replace(".asm", ".o")
                    )
                    mkkey = mod.staticLib.name.upper()
                    outputObj = "$({}_OUTPUT)/".format(mkkey) + str(obj)
                    srcsfile.write("{} : .FORCE\n".format(outputObj))
                srcsfile.write("\n\n")

        srcsfile.write("\n")

    srcsfile.close()

    strIncs = []
    aux = []

    if compilerSettings["INCLUDES"]:
        aux += compilerSettings["INCLUDES"]
    if includes:
        aux += includes

    strIncs = [str(i) for i in aux]

    listToExclude = []

    if USE_EXCLUDE_FOLDERS:

        allIncFoldes = []
        includes = [str(i) for i in includes]

        for filename in Path(".").rglob("*.h"):
            allIncFoldes.append(str(filename.parent))

        allIncFoldes = list(dict.fromkeys(allIncFoldes))
        allIncFoldes.sort()

        filtedist = []
        parent = ""
        for p in allIncFoldes:
            if parent == "":
                parent = p
                filtedist.append(p)
            elif p.startswith(parent + "/"):
                None
            else:
                parent = p
                filtedist.append(p)

        allIncFoldes = filtedist

        p = re.compile("^(I|i)nc(lude)*$")

        for allinc in allIncFoldes:
            aux = allinc + "/"
            if not any(aux.startswith(a + "/") for a in includes):
                if (
                    not str(allinc).startswith("Test/ceedling")
                    and not allinc == "."
                    and not str(allinc).startswith(str(projSettings["FOLDER_OUT"]))
                ):
                    auxpath = Path(allinc)
                    if p.match(auxpath.name):
                        listToExclude.append(str(auxpath.parent))
                    else:
                        listToExclude.append(allinc)

        listToExclude.append("Test/ceedling")

    cproject_setting = {
        "C_SETTINGS": projSettings,
        "C_TARGETS": compilerOpts["TARGETS"],
        "C_INCLUDES": strIncs,
        "C_SYMBOLS": compilerOpts["MACROS"],
        "C_EXCLUDE": listToExclude,
        "C_SRCS": all_srcs,
        "C_COMPILER_OPTS": compilerOpts,
        "C_CONFIG_DIR": str(config_dir),
    }

    try:
        # Execute init function of plugins
        for initFunc in addon.initAddonFuncs:
            initFunc(cproject_setting, compilerSettings)

        # Execute class of plugins
        for obj in addon.initAddonClass:
            p = obj(cproject_setting, compilerSettings)
            p.init()
    except Exception as ex:
        log.exception(ex)
        exit(-1)
