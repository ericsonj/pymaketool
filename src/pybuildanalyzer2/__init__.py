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
import subprocess
import argparse
from pathlib import Path
import json
from typing import Text
import http.server
import socketserver
import threading
import webbrowser
from urllib.parse import parse_qs, urlparse

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
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Build Analyzer - Memory Regions</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .tabs {
            display: flex;
            background: #e9e9e9;
        }
        .tab {
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: none;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            background: white;
            border-bottom-color: #007acc;
        }
        .tab-content {
            display: none;
            padding: 20px;
        }
        .tab-content.active {
            display: block;
        }
        .search-box {
            margin-bottom: 20px;
            padding: 10px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .progress-bar {
            width: 200px;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50 0%, #FFC107 60%, #F44336 90%);
            border-radius: 10px;
            transition: width 0.3s;
        }
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 12px;
            font-weight: bold;
            color: #333;
        }
        .tree {
            margin-left: 0;
        }
        .tree-item {
            margin: 2px 0;
            cursor: pointer;
        }
        .tree-item.expandable:before {
            content: '▶';
            display: inline-block;
            margin-right: 5px;
            transition: transform 0.2s;
        }
        .tree-item.expanded:before {
            transform: rotate(90deg);
        }
        .tree-children {
            margin-left: 20px;
            display: none;
        }
        .tree-children.expanded {
            display: block;
        }
        .tree-region {
            font-weight: bold;
            color: #007acc;
        }
        .tree-section {
            color: #666;
        }
        .tree-symbol {
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Build Analyzer - Memory Regions</h1>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('regions')">Memory Regions</button>
            <button class="tab" onclick="showTab('details')">Memory Details</button>
        </div>

        <div id="regions" class="tab-content active">
            <table id="regionsTable">
                <thead>
                    <tr>
                        <th>Region</th>
                        <th>Start Address</th>
                        <th>End Address</th>
                        <th>Size</th>
                        <th>Free</th>
                        <th>Used</th>
                        <th>Usage</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Regions data will be populated here -->
                </tbody>
            </table>
        </div>

        <div id="details" class="tab-content">
            <input type="text" class="search-box" placeholder="Search symbols..." id="searchInput" oninput="filterTree()">
            <div id="memoryTree" class="tree">
                <!-- Tree data will be populated here -->
            </div>
        </div>
    </div>

    <script>
        let regionsData = null;
        let filteredData = null;

        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }

        function toKB(bytes) {
            if (bytes < 1024) {
                return bytes + ' B';
            }
            return (bytes / 1024).toFixed(2) + ' KB';
        }

        function populateRegionsTable(regions) {
            const tbody = document.querySelector('#regionsTable tbody');
            tbody.innerHTML = '';
            
            regions.forEach(region => {
                const row = document.createElement('tr');
                const usage = region.length > 0 ? (region.using / region.length * 100) : 0;
                
                row.innerHTML = `
                    <td>${region.name}</td>
                    <td>0x${region.origin.toString(16).toUpperCase().padStart(8, '0')}</td>
                    <td>0x${region.end.toString(16).toUpperCase().padStart(8, '0')}</td>
                    <td>${toKB(region.length)}</td>
                    <td>${toKB(region.length - region.using)}</td>
                    <td>${toKB(region.using)}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${usage}%"></div>
                            <div class="progress-text">${usage.toFixed(2)}%</div>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function createTreeItem(name, addr, loadAddr, size, type, level = 0) {
            const item = document.createElement('div');
            item.className = `tree-item tree-${type}`;
            item.style.marginLeft = `${level * 20}px`;
            
            const addrStr = addr > 0 ? `0x${addr.toString(16).toUpperCase().padStart(8, '0')}` : '';
            const loadAddrStr = loadAddr > 0 ? `0x${loadAddr.toString(16).toUpperCase().padStart(8, '0')}` : '';
            const sizeStr = size > 0 ? toKB(size) : '';
            
            item.innerHTML = `
                <span style="display: inline-block; width: 300px;">${name}</span>
                <span style="display: inline-block; width: 120px;">${addrStr}</span>
                <span style="display: inline-block; width: 120px;">${loadAddrStr}</span>
                <span style="display: inline-block; width: 100px;">${sizeStr}</span>
            `;
            
            return item;
        }

        function populateMemoryTree(regions, searchTerm = '') {
            const container = document.getElementById('memoryTree');
            container.innerHTML = '';
            
            regions.forEach(region => {
                const regionItem = createTreeItem(region.name, region.origin, 0, region.length, 'region', 0);
                regionItem.classList.add('expandable');
                
                const sectionsContainer = document.createElement('div');
                sectionsContainer.className = 'tree-children';
                
                let hasMatchingSections = false;
                
                region.sections.forEach(section => {
                    const sectionMatches = !searchTerm || section.name.toLowerCase().includes(searchTerm.toLowerCase());
                    let hasMatchingSymbols = false;
                    
                    const sectionItem = createTreeItem(section.name, section.addr, section.load_addr, section.size, 'section', 1);
                    
                    const symbolsContainer = document.createElement('div');
                    symbolsContainer.className = 'tree-children';
                    
                    if (section.symbols) {
                        section.symbols.forEach(symbol => {
                            const symbolMatches = !searchTerm || symbol.name.toLowerCase().includes(searchTerm.toLowerCase());
                            
                            if (symbolMatches || sectionMatches) {
                                hasMatchingSymbols = true;
                                const diff = symbol.addr - section.addr;
                                const loadAddr = section.load_addr > 0 ? section.load_addr + diff : 0;
                                const symbolItem = createTreeItem(symbol.name, symbol.addr, loadAddr, symbol.size, 'symbol', 2);
                                symbolsContainer.appendChild(symbolItem);
                            }
                        });
                    }
                    
                    if ((sectionMatches || hasMatchingSymbols) && (!searchTerm || sectionMatches || hasMatchingSymbols)) {
                        hasMatchingSections = true;
                        if (symbolsContainer.children.length > 0) {
                            sectionItem.classList.add('expandable');
                            sectionItem.appendChild(symbolsContainer);
                        }
                        sectionsContainer.appendChild(sectionItem);
                    }
                });
                
                if (!searchTerm || hasMatchingSections) {
                    if (sectionsContainer.children.length > 0) {
                        regionItem.appendChild(sectionsContainer);
                    }
                    container.appendChild(regionItem);
                }
            });
            
            // Add click handlers for expansion
            container.querySelectorAll('.expandable').forEach(item => {
                item.addEventListener('click', function(e) {
                    e.stopPropagation();
                    this.classList.toggle('expanded');
                    const children = this.querySelector('.tree-children');
                    if (children) {
                        children.classList.toggle('expanded');
                    }
                });
            });
            
            // Expand all by default if no search term
            if (!searchTerm) {
                container.querySelectorAll('.expandable').forEach(item => {
                    item.classList.add('expanded');
                    const children = item.querySelector('.tree-children');
                    if (children) {
                        children.classList.add('expanded');
                    }
                });
            }
        }

        function filterTree() {
            const searchTerm = document.getElementById('searchInput').value;
            if (regionsData) {
                populateMemoryTree(regionsData, searchTerm);
            }
        }

        // Load data from server
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                regionsData = data;
                populateRegionsTable(data);
                populateMemoryTree(data);
            })
            .catch(error => {
                console.error('Error loading data:', error);
            });
    </script>
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

    PRINT_FORMAT = '| {0:<15}| {1:<15}| {2:<15}| {3:>12}| {4:>12}| {5:>12} {6:<11} {7:>7} |'

    def __init__(self, regions):
        self.regions = regions

    def __printBar(self, total, using, length=10, usingColor=False):
        str = []
        if total == 0:
            total = 1
            using = 0
        str.append('|')
        rate = using/total
        color = '\033[91m'
        if rate < 0.60:
            color = '\033[92m'
        elif rate < 0.90:
            color = '\033[93m'
        if usingColor:
            str.append(color)
        unit = total/length
        uunit = unit/8
        a = int(using/uunit)
        b = int(a/8)
        c = a - b*8
        str.append(chr(9608)*b)
        if c > 0: 
            str.append(chr(9615 - (1*c)))
        s = b + (1 if c > 0 else 0)
        str.append(' '*(length-s))
        if usingColor:
            str.append('\033[0m')

        str.append('|')
        return ''.join(str)

    def __printRegion(self, region):
        if (region.length == 0):
            return self.PRINT_FORMAT.format(
                        region.name,
                        hex(region.origin),
                        hex(region.end),
                        '0.0K',
                        '0.0K',
                        '0.0K',
                        self.__printBar(10, 0, usingColor=False),
                        '{:.2f}%'.format(0.0)
            )
        name = region.name
        origin = hex(region.origin)
        end = hex(region.end)
        length = toKB(region.length)
        free = toKB(region.length - region.using)
        using = toKB(region.using)
        bar = self.__printBar(region.length, region.using, usingColor=False)
        perc = '{:.2f}%'.format((region.using/region.length)*100)
        print(self.PRINT_FORMAT.format(name, origin, end, length, free, using, bar, perc))


    def __printHeader(self):
        print(self.PRINT_FORMAT.format('Region', 'Start', 'End', 'Size', 'Free', 'Used', '', 'Usage(%)'))


    def printAll(self):
        self.__printHeader()
        for r in self.regions:
            self.__printRegion(r)


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