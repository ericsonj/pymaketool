def get_makefile_content(subdir=None):
    """Return the root Makefile content.

    Args:
        subdir: subdirectory name (e.g. 'pymake') for the new layout,
                or None for the legacy layout.
    """
    makefile_mk_ref = f"{subdir}/makefile.mk" if subdir else "makefile.mk"
    return f"""# Copyright (c) 2020, Ericson Joseph
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


.DEFAULT_GOAL := all

%: prebuild
\t@time -p $(MAKE) -f {makefile_mk_ref} $@

prebuild:
\t@pymaketool $(or $(MAKECMDGOALS),all)

.PHONY: test
test_%:
\t@pymaketesting $(subst test_,,$@)
\t$(MAKE) -C Test/ceedling $(subst test_,,$@)

.INTERMEDIATE: prebuild

.PHONY: VERBOSE
ifndef VERBOSE
MAKEFLAGS += --silent
endif
"""


def get_makefile_mk_content(subdir=None, logkey_width=10):
    """Return the makefile.mk content.

    Args:
        subdir: subdirectory name (e.g. 'pymake') for the new layout,
                or None for the legacy layout.
        logkey_width: field width for the logger-compile label column (default 10).
                      Covers common long keys: CPPCHECK (8), COMPILER (8), FORMAT (6).
                      Increase if your logkeys are longer than 10 chars.
    """
    prefix = f"{subdir}/" if subdir else ""
    return f"""# Copyright (c) 2020, Ericson Joseph
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


## Local functions
define logger-compile
\t@printf \"%{logkey_width}s\\t%-30s\\n\" $(1) $(2)
endef

define logger-compile-lib
\t@printf \"%{logkey_width}s\\t%-25s %-30s\\n\" $(1) $(2) $(3)
endef

.DEFAULT_GOAL := all

CSRC  =
ASSRC =
INCS  =
COMPILER_FLAGS =
SLIBS_OBJECTS =
SLIBS_NAMES =
SRC_DIRS =

include {prefix}vars.mk
include {prefix}srcs.mk

ASSRC_s   = $(filter %.s,$(ASSRC))
ASSRC_S   = $(filter %.S,$(ASSRC))
ASSRC_asm = $(filter %.asm,$(ASSRC))

OBJECTS = $(CSRC:%.c=$(PROJECT_OUT)/%.o) \\
          $(CXXSRC:%.cpp=$(PROJECT_OUT)/%.o) \\
          $(ASSRC_s:%.s=$(PROJECT_OUT)/%.o) \\
          $(ASSRC_S:%.S=$(PROJECT_OUT)/%.o) \\
          $(ASSRC_asm:%.asm=$(PROJECT_OUT)/%.o)

include {prefix}targets.mk

%.o : CFLAGS = $(COMPILER_FLAGS)


$(PROJECT_OUT)/%.o: %.c
\t$(call logger-compile,"CC",$<)
\t@mkdir -p $(dir $@)
\t$(CC) $(CFLAGS) $(INCS) -o $@ -c $<


$(PROJECT_OUT)/%.o: %.cpp
\t$(call logger-compile,"CXX",$<)
\t@mkdir -p $(dir $@)
\t$(CXX) $(CFLAGS) $(INCS) -o $@ -c $<


$(PROJECT_OUT)/%.o: %.s
\t$(call logger-compile,"AS",$<)
\t@mkdir -p $(dir $@)
\t$(CC) $(CFLAGS) $(INCS) -o $@ -c $<


$(PROJECT_OUT)/%.o: %.S
\t$(call logger-compile,"AS",$<)
\t@mkdir -p $(dir $@)
\t$(CC) $(CFLAGS) $(INCS) -o $@ -c $<


$(PROJECT_OUT)/%.o: %.asm
\t$(call logger-compile,"AS",$<)
\t@mkdir -p $(dir $@)
\t$(CC) $(CFLAGS) $(INCS) -o $@ -c $<


all: $(TARGETS)

clean: clean_targets
\t@echo 'CLEAN'
\trm -rf $(addsuffix /*, $(addprefix $(PROJECT_OUT)/,$(SRC_DIRS)))

cleanlibs:
\trm -rf $(SLIBS_OBJECTS:%.a=%.cksum)

.PHONY: clean cleanlibs

-include $(OBJECTS:.o=.d)

.FORCE:
"""


FILE_MAKEFILE = """# Copyright (c) 2020, Ericson Joseph
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


.DEFAULT_GOAL := all

%: prebuild
\t@time -p $(MAKE) -f makefile.mk $@

prebuild:
\t@pymaketool $(or $(MAKECMDGOALS),all)

.PHONY: test
test_%:
\t@pymaketesting $(subst test_,,$@)
\t$(MAKE) -C Test/ceedling $(subst test_,,$@)

.INTERMEDIATE: prebuild

.PHONY: VERBOSE
ifndef VERBOSE
MAKEFLAGS += --silent
endif
"""

FILE_MAKEFILE_MK = """# Copyright (c) 2020, Ericson Joseph
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


## Local functions
define logger-compile
	@printf \"%6s\\t%-30s\\n\" $(1) $(2)
endef

define logger-compile-lib
	@printf \"%6s\\t%-25s %-30s\\n\" $(1) $(2) $(3)
endef

.DEFAULT_GOAL := all

CSRC  =
ASSRC = 
INCS  = 
COMPILER_FLAGS =
SLIBS_OBJECTS = 
SLIBS_NAMES = 
SRC_DIRS =

include vars.mk
include srcs.mk

ASSRC_s   = $(filter %.s,$(ASSRC))
ASSRC_S   = $(filter %.S,$(ASSRC))
ASSRC_asm = $(filter %.asm,$(ASSRC))

OBJECTS = $(CSRC:%.c=$(PROJECT_OUT)/%.o) \
          $(CXXSRC:%.cpp=$(PROJECT_OUT)/%.o) \
          $(ASSRC_s:%.s=$(PROJECT_OUT)/%.o) \
          $(ASSRC_S:%.S=$(PROJECT_OUT)/%.o) \
          $(ASSRC_asm:%.asm=$(PROJECT_OUT)/%.o)

include targets.mk

%.o : CFLAGS = $(COMPILER_FLAGS)


$(PROJECT_OUT)/%.o: %.c
	$(call logger-compile,"CC",$<)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(INCS) -o $@ -c $<


$(PROJECT_OUT)/%.o: %.cpp
	$(call logger-compile,"CXX",$<)
	@mkdir -p $(dir $@)
	$(CXX) $(CFLAGS) $(INCS) -o $@ -c $<


$(PROJECT_OUT)/%.o: %.s
	$(call logger-compile,"AS",$<)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(INCS) -o $@ -c $<


$(PROJECT_OUT)/%.o: %.S
	$(call logger-compile,"AS",$<)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(INCS) -o $@ -c $<


$(PROJECT_OUT)/%.o: %.asm
	$(call logger-compile,"AS",$<)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(INCS) -o $@ -c $<


all: $(TARGETS)

clean: clean_targets
\t@echo 'CLEAN'
\trm -rf $(addsuffix /*, $(addprefix $(PROJECT_OUT)/,$(SRC_DIRS)))

cleanlibs:
\trm -rf $(SLIBS_OBJECTS:%.a=%.cksum)	

.PHONY: clean cleanlibs

-include $(OBJECTS:.o=.d)

.FORCE:
"""

FILE_MAKEFILE_PY = """import os
from pymakelib import ProjectConfig, Makeclass, CompilerOpts, MKVARS, Target
from pymakelib.toolchain import get_gcc_linux

@Makeclass
class Build(ProjectConfig):
    name         = os.path.basename(os.getcwd())
    output_dir   = 'build/obj/'
    compiler_set = get_gcc_linux()

    # Optional: load project variables from a .env file
    # env_file = '.env'

    def compiler_opts(self, opts: CompilerOpts) -> CompilerOpts:
        opts.debugging    = ['-g3']
        opts.standard     = ['-std=c11']
        opts.preprocessor = ['-MP', '-MMD']
        return opts

    def targets(self):
        FOLDER_OUT = 'build/'
        return {
            'TARGET': Target(
                file   = FOLDER_OUT + self.name,
                script = [MKVARS.LD, '-o', '$@', MKVARS.OBJECTS, MKVARS.LDFLAGS],
                logkey = 'OUT',
            ),
        }

    def getPhonyTargets(self):
        return {
            # 'flash': {
            #     'deps': ['all'],
            #     'logkey': 'FLASH',
            #     'script': 'openocd -f board/board.cfg -c "program build/' + self.name + ' verify reset exit"'
            # },
        }
"""
