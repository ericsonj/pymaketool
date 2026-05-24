#!/usr/bin/env python3

# Copyright (c) 2021, Ericson Joseph
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

"""
PyBuildAnalyzer2 - Multi-architecture firmware build analyzer

Supports ARM and MIPS32 architectures with architecture-specific map file parsing.
For MIPS32, uses Microchip XC32 compiler map file format (like PIC32).
For ARM, uses standard GNU linker map file format.
"""

import re
import os
import glob
import subprocess
import argparse
from pathlib import Path
import json
import http.server
import socketserver
import threading
import webbrowser
from urllib.parse import parse_qs, urlparse
from rich.console import Console
from rich.table import Table
from rich.text import Text

# ---------------------

def toKB(num):
    if num < 1024:
        return '{} B'.format(num)
    return '{:.2f} KB'.format(num/1024)

class SectionHeader:
    def __init__(self, args):
        self.nr   = args['nr']
        self.name = args['name']
        self.type = args['type']
        self.addr = int("0x"+args['addr'], 16)
        self.off  = int("0x"+args['off'], 16)
        self.size = int("0x"+args['size'], 16)
        self.es   = args['es']
        self.flg  = args['flg']
        self.lk   = int(args['lk'])
        self.inf  = int(args['inf'])
        self.al   = int(args['al'])
        self.load_addr = 0
        self.symbols = []

    def setLoadAddr(self, load_addr):
        self.load_addr = load_addr
    
    def toJSON(self):
        return json.dumps(self, default=lambda x: x.__dict__, indent=4)

    def __repr__(self) -> str:
        return json.dumps(self.__dict__)


class SectionMap:
    def __init__(self, name, addr, length, loadAddr=0):
        self.name = name
        self.addr = addr
        self.loadAddr = loadAddr
        self.length = length
    def __repr__(self) -> str:
        return json.dumps(self.__dict__)

class Symbol:
    def __init__(self, args):
        self.num    = int(args['num'])
        self.value  = int("0x"+args['addr'], 16)
        self.addr   = self.value
        self.size   = int(args['size'])
        self.type   = args['type']
        self.bind   = args['bind']
        self.vis    = args['vis']
        self.ndx    = args['ndx']
        self.name   = args['name']
    def __repr__(self) -> str:
        return json.dumps(self.__dict__)

class MemRegion:
    def __init__(self, name, attr, origin, length):
        self.name = name
        self.attr = attr
        self.origin = origin
        self.length = length
        self.end = origin + length
        self.using = 0
        self.sections = []
    def __repr__(self) -> str:
        return json.dumps(self.__dict__, default=lambda x: x.__dict__)
    def toJSON(self):
        return json.dumps(self, default=lambda x: x.__dict__, indent=4)

class WebRegionsServer:
    def __init__(self, regions: list, port=7777):
        self.regions = regions
        self.port = port
        self.httpd = None

    def get_html_template(self):        
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dist_dir = os.path.join(current_dir, 'dist')
        
        try:
            # Read the index.html file
            html_file = os.path.join(dist_dir, 'index.html')
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            return html_content
            
        except:
            # Fallback to a simple HTML template if dist files don't exist
            return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Build Analyzer - Memory Regions</title>
</head>
<body>
    <div id="root"></div>
    <p>Error: Built files not found. Please build the frontend first.</p>
    <p>Run: <code>pnpm build</code> in the UI project directory</p>
</body>
</html>'''

    def start_server(self):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                self.regions = None
                super().__init__(*args, **kwargs)

            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(self.server.get_html_template().encode())
                elif self.path == '/api/data':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    data = json.dumps(self.server.regions_data, default=lambda x: x.__dict__)
                    self.wfile.write(data.encode())
                elif self.path.startswith('/assets/'):
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    asset_path = os.path.join(current_dir, 'dist', self.path[1:])  # Remove leading slash
                    
                    try:
                        with open(asset_path, 'rb') as f:
                            content = f.read()
                        
                        self.send_response(200)
                        if asset_path.endswith('.js'):
                            self.send_header('Content-type', 'application/javascript')
                        elif asset_path.endswith('.css'):
                            self.send_header('Content-type', 'text/css')
                        else:
                            self.send_header('Content-type', 'application/octet-stream')
                        self.end_headers()
                        self.wfile.write(content)
                    except FileNotFoundError:
                        self.send_response(404)
                        self.end_headers()
                elif self.path == '/vite.svg':
                    # Handle vite.svg if needed, or return 404
                    self.send_response(404)
                    self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()

        class CustomTCPServer(socketserver.TCPServer):
            def __init__(self, *args, **kwargs):
                self.regions_data = []
                super().__init__(*args, **kwargs)

            def get_html_template(self):
                return self.regions_data[0] if hasattr(self, 'html_template') else ''

        Handler.server_version = "BuildAnalyzer/2.0"
        Handler.sys_version = ""

        try:
            with CustomTCPServer(("", self.port), Handler) as httpd:
                httpd.regions_data = self.regions
                httpd.html_template = self.get_html_template()
                httpd.get_html_template = lambda: self.get_html_template()
                
                print(f"Server running on http://localhost:{self.port}")
                print("Press Ctrl+C to stop the server")
                
                # Open browser
                webbrowser.open(f"http://localhost:{self.port}")
                
                self.httpd = httpd
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\nServer stopped.")
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"Port {self.port} is already in use. Please try a different port.")
            else:
                print(f"Error starting server: {e}")

    def show(self):
        self.start_server()


class MemRegionView:

    def __init__(self, regions):
        self.regions = regions

    def _usage_color(self, rate):
        if rate < 0.60:
            return "green"
        if rate < 0.90:
            return "yellow"
        return "red"

    def _bar(self, rate, width=12):
        filled = int(rate * width)
        color = self._usage_color(rate)
        bar = Text()
        bar.append("█" * filled, style=color)
        bar.append("░" * (width - filled), style="dim")
        return bar

    def printAll(self):
        console = Console()
        table = Table(title="Memory Regions", show_lines=False, box=None, header_style="bold cyan")
        table.add_column("Region", style="bold")
        table.add_column("Start")
        table.add_column("End")
        table.add_column("Size", justify="right")
        table.add_column("Free", justify="right")
        table.add_column("Used", justify="right")
        table.add_column("Bar")
        table.add_column("Usage%", justify="right")

        for r in self.regions:
            rate = (r.using / r.length) if r.length > 0 else 0.0
            color = self._usage_color(rate)
            table.add_row(
                r.name,
                hex(r.origin),
                hex(r.end),
                toKB(r.length),
                toKB(r.length - r.using),
                Text(toKB(r.using), style=color),
                self._bar(rate),
                Text(f"{rate * 100:.1f}%", style=color),
            )
        console.print(table)


def parse_mips32_map_file(mapfile_path, sections):
    """Parse MIPS32 map file format (like from PIC32/XC32 compiler)"""
    regions = []
    sectionsMap = []
    
    try:
        with open(mapfile_path, 'r') as mapfile:
            lines = mapfile.readlines()
            
        # Find Memory Configuration section
        mem_config_start = -1
        linker_script_start = -1
        
        for i, line in enumerate(lines):
            if 'Memory Configuration' in line:
                mem_config_start = i
            elif 'Linker script and memory map' in line:
                linker_script_start = i
                break
        
        # Parse Memory Configuration
        if mem_config_start >= 0:
            i = mem_config_start + 1
            while i < len(lines) and (linker_script_start == -1 or i < linker_script_start):
                line = lines[i].strip()
                if line and not line.startswith('Name') and not line.startswith('*default*'):
                    # Expected format: Name Origin Length [Attributes]
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            name = parts[0]
                            origin = int(parts[1], 16)
                            length = int(parts[2], 16)
                            attr = parts[3] if len(parts) > 3 else ''
                            regions.append(MemRegion(name, attr, origin, length))
                        except (ValueError, IndexError):
                            pass
                i += 1
        
        # Filter regions to only include specific MIPS32 regions
        allowed_regions = {'kseg0_program_mem', 'kseg0_data_mem', 'sfrs', 'kseg1_boot_mem'}
        regions = [r for r in regions if r.name in allowed_regions]
        
        # Parse section information from Microchip's memory usage report
        # Look for section pattern like: .text.function_name    0x9d000000          0x180         384
        section_pattern = r'^\s*(?P<name>[.][a-zA-Z0-9_.-]+)\s+(?P<addr>0x[0-9a-fA-F]+)\s+(?P<length>0x[0-9a-fA-F]+)\s+(?P<dec_size>\d+)'
        
        for line in lines:
            line = line.strip()
            match = re.search(section_pattern, line)
            if match:
                name = match.group('name')
                addr = int(match.group('addr'), 16)
                length = int(match.group('length'), 16)
                if length > 0:
                    sectionsMap.append(SectionMap(name, addr, length, addr))  # For MIPS32, addr is both VMA and LMA typically
        
        regions.sort(key=lambda x: x.origin, reverse=False)
        
    except Exception as e:
        print(f"Warning: Error parsing MIPS32 map file: {e}")
        return [], []
    
    return regions, sectionsMap


# ----------------------
def main():
    parser = argparse.ArgumentParser(description='Builder Analyzer for ARM and MIPS32 firmware')
    parser.add_argument('elf', type=str, help='ELF file')
    parser.add_argument('--arch', type=str, choices=['ARM', 'MIPS32'], default='ARM', 
                        help='Target architecture (default: ARM)')
    parser.add_argument('-w', '--web', help='Show in web browser (port 7777)', action="store_true")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 2.0.1')
    args = parser.parse_args()

    # Set cross-compile prefix based on architecture
    if args.arch == 'MIPS32':
        cross_compile_prefix = os.environ.get('CROSS_COMPILE', 'xc32-')
    else:  # ARM
        cross_compile_prefix = os.environ.get('CROSS_COMPILE', '')
    readelf = cross_compile_prefix + 'readelf'

    elffile = args.elf
    if not Path(elffile).exists():
        print("File {0} not found.".format(elffile))
        exit(-1)

    mapfile = elffile.replace(".elf", ".map")
    if not Path(mapfile).exists():
        print("File '{0}' not found".format(mapfile))
        mapfile = None
        exit(1)

    result = subprocess.run([readelf, '-S', '--wide', elffile], stdout=subprocess.PIPE).stdout.splitlines()
    sections = []
    rgx_section_h = r"^\s*\[[ ]*(?P<nr>[0-9]+)\][ ]+(?P<name>[a-zA-Z\\.0-9_-]+)[ ]+(?P<type>[a-zA-Z\\.0-9_-]+)[ ]+(?P<addr>[a-f0-9]+)[ ]+(?P<off>[a-f0-9]+)[ ]+(?P<size>[a-f0-9]+)[ ]+(?P<es>[a-f0-9]{2})[ ]+(?P<flg>[a-zA-Z]*)[ ]+(?P<lk>[0-9]+)[ ]+(?P<inf>[0-9]+)[ ]+(?P<al>[0-9]+)"
    for line in result:
        l = line.decode("utf-8")
        match = re.search(rgx_section_h, l)
        if match:
            s = SectionHeader(match.groupdict())
            sections.append(s)

    result = subprocess.run([readelf, '-s', '--wide', elffile], stdout=subprocess.PIPE).stdout.splitlines()
    symbols = []
    rgx_symbols = r"^\s+(?P<num>[0-9]+):[ ]+(?P<addr>[a-f0-9]+)[ ]+(?P<size>[a-f0-9]+)[ ]+(?P<type>[a-zA-Z0-9]+)[ ]+(?P<bind>[a-zA-Z0-9]+)[ ]+(?P<vis>[a-zA-Z0-9]+)[ ]+(?P<ndx>[a-zA-Z0-9]+)[ ]?(?P<name>[a-zA-Z\\.\\$0-9_-]*)"
    for line in result:
        l = line.decode("utf-8")
        match = re.search(rgx_symbols, l)
        if match:
            s = Symbol(match.groupdict())
            symbols.append(s)

    symbols.sort(key=lambda x: x.addr, reverse=False)

    regions = []
    sectionsMap = []
    if mapfile:
        if args.arch == 'MIPS32':
            # Use MIPS32-specific parser
            regions, sectionsMap = parse_mips32_map_file(mapfile, sections)
        else:
            # Use ARM-specific parser (existing logic)
            memlines = False
            memNewLines = 2
            maplines = False
            mapNewLines = 2
            readStackSize = False
            mapfile_handle = open(mapfile, 'r')
            content = []
            readNextLine = False
            upstream = []
            for line in mapfile_handle:
                if (re.match(r'^Memory Configuration', line)):
                    memlines = True

                if memlines:
                    if (line.strip() == ''):
                        memNewLines = memNewLines - 1
                    if memNewLines == 0:
                        memlines = False
                    line = line.strip()
                    line = re.sub(r'\s+', ' ', line)
                    content.append(line)

                if re.match(r'^[.].*', line):
                    if not ' ' in line.strip():
                        readNextLine = True
                    upstream.append(line.strip())
                else:
                    if readNextLine:
                        upstream[-1] = upstream[-1] + ' ' + line.strip()
                        readNextLine = False
            mapfile_handle.close()

            p = re.compile(r'^[.][a-zA-Z\\.0-9_-]+\s+0x[0-9a-fA-F]+\s+0x[0-9a-fA-F]+.*')
            upstream = list(filter(p.search, upstream))
            lines = upstream
            p = re.compile(
                r'^(?P<name>[.][a-z-A-Z\\.0-9_-]+)\s+(?P<addr>[0-9xa-fA-F]+)+\s+(?P<length>[0-9xa-fA-F]+).*')
            p2 = re.compile(
                r'^(?P<name>[.][a-z-A-Z\\.0-9_-]+)\s+(?P<addr>[0-9xa-fA-F]+)+\s+(?P<length>[0-9xa-fA-F]+)\s+load\s+address\s+(?P<load_addr>[0-9xa-fA-F]+).*')
            for l in lines:
                m = None
                loadAddr = 0
                if 'load' in l:
                    m = p2.search(l)
                    if m:
                        loadAddr = int(m.group('load_addr'), 16)
                else:
                    m = p.search(l)

                if m:
                    name = m.group('name')
                    addr = int(m.group('addr'), 16)
                    length = int(m.group('length'), 16)
                    sectionsMap.append(SectionMap(name, addr, length, loadAddr))

            for line in content:
                if re.match(r'^Memory Configuration', line):
                    content.remove(line)
                elif re.match(r'^Name\s+Origin\s+Length\s+Attributes', line):
                    content.remove(line)
                elif re.match(r'^[*]default[*].*', line):
                    content.remove(line)

            for regin in content:
                values = regin.split(' ')
                try:
                    regions.append(MemRegion(
                        name=values[0],
                        attr=values[3] if len(values) > 3 else '',
                        origin=int(values[1], 16),
                        length=int(values[2], 16)
                    ))
                except:
                    pass
            regions.sort(key=lambda x: x.origin, reverse=False)

    # ------------------------------- 

    for sec in sections:
        if sec.size > 0 and sec.addr > 0:
            syms = list(filter(lambda x: x.ndx == sec.nr and x.size > 0, symbols))
            if syms:
                sec.symbols.extend(syms)

    if regions and sectionsMap:
        if args.arch == 'MIPS32':
            # For MIPS32, don't filter by loadAddr as it may not be applicable
            sectionsMap = list(filter(lambda x: x.addr > 0 and x.length > 0, sectionsMap))
        else:
            # For ARM, keep original filtering logic
            sectionsMap = list(filter(lambda x: x.addr > 0 and x.length > 0 and x.loadAddr > 0 and x.name != '.bss', sectionsMap))
        
        for s in sectionsMap:
            for sec in sections:
                if (sec.name == s.name):
                    sec.setLoadAddr(s.loadAddr)

        for r in regions:
            for sec in sections:
                if sec.size > 0 and sec.addr > 0:
                    if (sec.addr >= r.origin and sec.addr < r.end) or (sec.load_addr > 0 and (sec.load_addr >= r.origin and sec.load_addr < r.end)):
                        r.using += sec.size
                        r.sections.append(sec)

        if args.web:
            win = WebRegionsServer(regions)
            win.show()
        else:
            view = MemRegionView(regions)
            view.printAll()