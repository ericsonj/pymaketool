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


class Sym:
    def __init__(self, num: int, value: int, size: int, stype: str, bind: str, vis: str, ndx: str, name: str):
        self.num = num
        self.value = value
        self.size = size
        self.stype = stype
        self.bind = bind
        self.vis = vis
        self.ndx = ndx
        self.name = name


def getItemSym(line):
    match = re.findall('^[ ]+(?P<Num>[0-9]+):[ ]+(?P<Value>[a-fA-F0-9]+)[ ]+(?P<Size>[0-9]+)[ ]+(?P<Type>[a-zA-Z0-9]+)[ ]+(?P<Bind>[a-zA-Z0-9]+)[ ]+(?P<Vis>[a-zA-Z0-9]+)[ ]+(?P<Ndx>[a-zA-Z0-9]+)[ ]+(?P<Name>[a-zA-Z0-9_-]*).*', line)
    if match:
        s = Sym(
            int(match[0][0]),
            int(match[0][1], 16),
            int(match[0][2]),
            match[0][3],
            match[0][4],
            match[0][5],
            match[0][6],
            match[0][7]
        )
        return s
    else:
        return None


sizefile = open('simtable.txt')


ramUsage = 7

for line in sizefile:
    item = getItemSym(line)
    if item != None:
        if (item.value >= int("0x20000090", 16) and  item.value < int("0x2000ce14", 16)) and item.size > 0:
            ramUsage += item.size
            print('{}\t\t{}'.format(item.size, item.name))

print('{} B'.format(ramUsage))