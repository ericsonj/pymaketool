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


import re
import sys
import getopt


class ItemSizeStat:
    def __init__(self, name, size, addr):
        self.name = name
        self.size = size
        self.addr = addr

    def string(self):
        return self.name + " " + self.size + " " + self.addr

    def getAddr(self):
        return self.addr

    def getSize(self):
        return self.size


def getSizeAddr(line):
    x = re.search("^([A-Za-z0-9_\.]+)[ ]+([a-z0-9]+)[ ]+([a-z0-9]+).*", line)
    if(x):
        return ItemSizeStat(x.group(1), x.group(2), x.group(3))
    else:
        None


def printKB(value, decimals=1):
    return ('{:.'+str(decimals)+'f}').format(value/1000)

def printPrtg(value, decimals=1):
    return ('{:.'+str(decimals)+'f}').format(value*100)


def main(argv):
    totalFlashLen = 0
    totalRAMLen = 0
    sizefile = ''

    try:
        opts, args = getopt.getopt(
            argv, "hF:R:s:", ["flash-len=", "ram-len=", "size-file="])
    except getopt.GetoptError:
        print('armsize.py -F <flash-len:int> -R <ram-len:int> -s <size-file:file>')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-F', '--flash-len'):
            totalFlashLen = int(arg)
        elif opt in ('-R', '--ram-len'):
            totalRAMLen = int(arg)
        elif opt in ('-s', '--size-file'):
            sizefile = arg

    file = open(sizefile, "r")

    STATE_FIND = 0
    STATE_READ = 1
    STATE_END = 2

    state = STATE_FIND

    itemsSize = []

    for line in file:
        if(state == STATE_FIND):
            x = re.search("^section[ ]+size[ ]+addr.*", line)
            if(x):
                state = STATE_READ
        elif state == STATE_READ:
            x = re.search("^Total.*", line)
            if(x):
                state = STATE_END
            else:
                item = getSizeAddr(line)
                itemsSize.append(item)

    RAM_ADDR = int("0x20000000", 16)
    FLASH_ADDR = int("0x8000000", 16)
    TOTAL_RAM = float(totalRAMLen)
    TOTAL_FLASH = float(totalFlashLen)
    RAM_USAGE = 0
    FLASH_USAGE = 0

    for item in itemsSize:
        itemAddr = int(item.getAddr(), 16)
        if(itemAddr >= RAM_ADDR):
            RAM_USAGE = RAM_USAGE + int(item.getSize(), 16)
        elif(itemAddr >= FLASH_ADDR and itemAddr < RAM_ADDR):
            FLASH_USAGE = FLASH_USAGE + int(item.getSize(), 16)

    print('{:<6}{:>14}{:>14}{:>14}'.format('REGION', 'SIZE', 'USED', 'USAGE (%)'))

    perc = (float(RAM_USAGE) / TOTAL_RAM)
    print("RAM:   {:>10} KB {:>10} KB {:>10} %".format(
        printKB(TOTAL_RAM), printKB(RAM_USAGE), printPrtg(perc)))

    perc = (float(FLASH_USAGE) / TOTAL_FLASH)
    print("FLASH: {:>10} KB {:>10} KB {:>10} %".format(
        printKB(TOTAL_FLASH), printKB(FLASH_USAGE), printPrtg(perc)))


if __name__ == "__main__":
    main(sys.argv[1:])
