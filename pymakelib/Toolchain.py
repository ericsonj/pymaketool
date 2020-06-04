import subprocess
import tempfile


def getGCCHeaderFiles(cmd_gcc):
    gcc_includes = []
    try:
        auxfile = tempfile.NamedTemporaryFile()
        command = "echo | {0} -Wp,-v -x c++ - -fsyntax-only &> {1} ; cat {1} |  grep '^[ ]*/usr.*'".format(
            cmd_gcc, auxfile.name)
        res = subprocess.check_output(["bash", "-c", command])
        for line in res.splitlines():
            gcc_includes.append(line.decode('utf-8').strip())
        auxfile.close()
    except Exception as e:
        print(e)
    return gcc_includes


def confARMeabiGCC(binLocation='', prefix='arm-none-eabi-', extIncludes=[]):
    return confGCC(binLocation, prefix, extIncludes)


def confLinuxGCC(binLocation='', extIncludes=[]):
    return confGCC(binLocation, '', extIncludes)


def confGCC(binLocation='', prefix='', extIncludes=[]):
    cmd_gcc = binLocation + prefix + 'gcc'
    cmd_gxx = binLocation + prefix + 'g++'
    cmd_ld = binLocation + prefix + 'gcc'
    cmd_ar = binLocation + prefix + 'ar'
    cmd_as = binLocation + prefix + 'as'
    cmd_objcopy = binLocation + prefix + 'objcopy'
    cmd_size = binLocation + prefix + 'size'
    cmd_objdump = binLocation + prefix + 'objdump'
    gcc_includes = getGCCHeaderFiles(cmd_gcc)
    gcc_includes = gcc_includes + extIncludes
    return confToolchain(cmd_gcc, cmd_gxx, cmd_ld, cmd_ar, cmd_as, cmd_objcopy, cmd_size, cmd_objdump, gcc_includes)
    

def confToolchain(
    cmd_gcc,
    cmd_gxx,
    cmd_ld,
    cmd_ar,
    cmd_as,
    cmd_objcopy,
    cmd_size,
    cmd_objdump,
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
        'INCLUDES': includes
    }
