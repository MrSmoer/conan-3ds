from conan import ConanFile, tools
from conan.tools.files import chdir, collect_libs, copy, get, patch, replace_in_file
from conan.tools.gnu import Autotools, AutotoolsDeps

import os
import glob

class Conan(ConanFile):
    name = '3ds_examples'
    settings = 'compiler', 'build_type'
    description = 'Examples for 3DS using devkitARM, libctru and citro3d'
    url = 'https://github.com/devkitpro/3ds-examples'

    ## TODO: Add citro2d (citro2d/1.2.0@ctr/stable)
    #build_requires = ["libctru/1.6.0@ctr/stable", "citro3d/1.5.0@ctr/stable", "3dstools/1.1.4@ctr/stable", "dka_general_tools/1.2.0@ctr/stable", "picasso/2.7.0@ctr/stable", "tex3ds/2.0.1@ctr/stable"]

    generators = ["AutotoolsToolchain"]

    # TODO: Make version-specific
    tool_requires = ["dka_general_tools/1.2.0", "picasso/2.7.0"]

    exports_sources = ['45758185_fix_parallel_building.patch']

    def generate(self):
        tc = AutotoolsDeps(self)
        tc.environment.append("LDFLAGS_CONAN", tc.environment.vars(self)["LDFLAGS"])
        tc.generate()

    def requirements(self):
        if self.version == "20150818-2c57809":
            self.requires("libctru/0.6.0")
        if int(self.version) <= 20170714:
            self.requires("citro3d/[<=1.4.0]") # 20170714 requires <= 1.4.0 due to API deprecation
        elif int(self.version) <= 20180513:
            self.requires("citro2d/[>=1.0.0 <1.2.0]")
        elif int(self.version) <= 20190102:
            self.requires("citro2d/[>=1.1.0 <1.2.0]") # 20190102 requires 1.1.0 for ellipse rendering functions
        elif int(self.version) <= 20200417:
            self.requires("libctru/[>=1.6.0]") # 20200417 requires 1.6.0 for new Mii Selector definitions
            self.requires("citro2d/[>=1.1.0 <1.2.0]")
        else:
            # TODO: Requires new devkitarm
            raise Exception("Recent 3ds-examples not supported yet")
            #self.requires("libctru/2.2.1")

    def build_requirements(self):
        # TODO: Old versions only
        if self.version == "20150818-2c57809":
            self.tool_requires("aemstro/51bfeef")
        else:
            # TODO: Move to toolchain?
            self.tool_requires("dka_3dstools/1.1.4")

        if int(self.version) >= 20180513:
            self.tool_requires("tex3ds/[>1.0.1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

        if self.version == "20190102":
            patch(self, base_path=".", patch_file="45758185_fix_parallel_building.patch")

        # The project Makefiles hardcode CFLAGS and LDFLAGS *and* they expect citro3d to be installed into the libctru library...
        # Patch up the Makefiles so it can pick up our libraries
        with chdir(self, self.source_folder):
            for file in glob.iglob('**/Makefile', recursive=True):
                print("Patching %s" % file)
                replace_in_file(self, file, "CFLAGS	:=", "CFLAGS	:= $(CPPFLAGS)", strict=False)
                replace_in_file(self, file, "LDFLAGS	=", "LDFLAGS	= $(LDFLAGS_CONAN)", strict=False)

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            # Parallel builds were broken up until Jan 22, 2019
            autotools.make(args=["-j1"])

    def package(self):
        copy(self, "bin/*", src=self.source_folder, dst=self.package_folder)
