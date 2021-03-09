import subprocess
import tempfile


def getCeedlingHeaderFiles():
    ceedling_includes = []
    try:
        auxfile = tempfile.NamedTemporaryFile()
        command = "find /var/lib/gems $HOME/.gem/ -name 'unity.h' 2>&1 | grep '.*ceedling-[0-9\\.\\-]*/vendor/unity/src'"
        res = subprocess.check_output(["bash", "-c", command])
        for line in res.splitlines():
            ceedling_includes.append(line.decode('utf-8').strip())
        auxfile.close()
    except Exception as e:
        print(e)
    return ceedling_includes