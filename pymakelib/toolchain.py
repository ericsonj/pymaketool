import subprocess
import tempfile
from pathlib import Path

def getGCCHeaderFiles(cmd_gcc):
    gcc_includes = []
    try:
        auxfile = tempfile.NamedTemporaryFile()
        command = "echo | {0} -Wp,-v -x c++ - -fsyntax-only &> {1} ; cat {1} |  grep -e '^\s.*'".format(
            cmd_gcc, auxfile.name)
        res = subprocess.check_output(["bash", "-c", command])
        for line in res.splitlines():
            gcc_includes.append(line.decode('utf-8').strip())
        auxfile.close()
    except Exception as e:
        print(e)
    return gcc_includes


def get_gcc_arm_none_eabi(binLocation='', prefix='arm-none-eabi-', extIncludes=[]) -> dict:
    """Get dictionary with gcc compiler set of arm-none-eabi-

    Args:
        binLocation (str, optional): Location of toolchain binary. Defaults to ''.
        prefix (str, optional): prefix of ARM toolchain. Defaults to 'arm-none-eabi-'.
        extIncludes (list, optional): list of external includes. Defaults to [].

    Returns:
        dict: set of gcc compiler e.g. {'CC': 'arm-none-eabi-gcc' ... }
    """    
    return confGCC(binLocation, prefix, extIncludes)


def confARMeabiGCC(binLocation='', prefix='arm-none-eabi-', extIncludes=[]):
    return confGCC(binLocation, prefix, extIncludes)


def get_gcc_linux(bin_location='', ext_incs=[]) -> dict:
    """Get dictionary with gcc compiler set for linux   

    Args:
        bin_location (str, optional): location of toolchain. Defaults to ''.
        ext_incs (list, optional): list of external includes. Defaults to [].

    Returns:
        dict: set of gcc compiler e.g. {'CC': 'gcc' ... }
    """    
    return confLinuxGCC(binLocation=bin_location, extIncludes=ext_incs)


def confLinuxGCC(binLocation='', extIncludes=[]):
    return confGCC(binLocation, '', extIncludes)


def confGCC(binLocation='', prefix='', extIncludes=[]):
    binpath = Path(binLocation)
    cmd_gcc = str(binpath / (prefix + 'gcc'))
    cmd_gxx = str(binpath / (prefix + 'g++'))
    cmd_ld = str(binpath / (prefix + 'gcc'))
    cmd_ar = str(binpath / (prefix + 'ar'))
    cmd_as = str(binpath / (prefix + 'as'))
    cmd_objcopy = str(binpath / (prefix + 'objcopy'))
    cmd_size = str(binpath / (prefix + 'size'))
    cmd_objdump = str(binpath / (prefix + 'objdump'))
    cmd_nm = str(binpath / (prefix + 'nm'))
    cmd_ranlib = str(binpath / (prefix + 'ranlib'))
    cmd_strings = str(binpath / (prefix + 'strings'))
    cmd_strip = str(binpath / (prefix + 'strip'))
    cmd_cxxfilt = str(binpath / (prefix + 'c++filt'))
    cmd_addr2line = str(binpath / (prefix + 'addr2line'))
    cmd_readelf = str(binpath / (prefix + 'readelf'))
    cmd_elfedit = str(binpath / (prefix + 'elfedit'))

    gcc_includes = getGCCHeaderFiles(cmd_gcc)
    gcc_includes = gcc_includes + extIncludes
    return confToolchain(cmd_gcc,
                         cmd_gxx,
                         cmd_ld,
                         cmd_ar,
                         cmd_as,
                         cmd_objcopy,
                         cmd_size,
                         cmd_objdump,
                         cmd_nm,
                         cmd_ranlib,
                         cmd_strings,
                         cmd_strip,
                         cmd_cxxfilt,
                         cmd_addr2line,
                         cmd_readelf,
                         cmd_elfedit,
                         gcc_includes)


def confToolchain(
    cmd_gcc,
    cmd_gxx,
    cmd_ld,
    cmd_ar,
    cmd_as,
    cmd_objcopy,
    cmd_size,
    cmd_objdump,
    cmd_nm,
    cmd_ranlib,
    cmd_strings,
    cmd_strip,
    cmd_cxxfilt,
    cmd_addr2line,
    cmd_readelf,
    cmd_elfedit,
    includes
):
    return {
        'CC':       cmd_gcc,
        'CXX':      cmd_gxx,
        'LD':       cmd_ld,
        'AR':       cmd_ar,
        'AS':       cmd_as,
        'OBJCOPY':  cmd_objcopy,
        'SIZE':     cmd_size,
        'OBJDUMP':  cmd_objdump,
        'NM':       cmd_nm,
        'RANLIB':   cmd_ranlib,
        'STRINGS':  cmd_strings,
        'STRIP':    cmd_strip,
        'CXXFILT':  cmd_cxxfilt,
        'ADDR2LINE':cmd_addr2line,
        'READELF':  cmd_readelf,
        'ELFEDIT':  cmd_elfedit,
        'INCLUDES': includes
    }
