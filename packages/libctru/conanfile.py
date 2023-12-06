from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import chdir, collect_libs, copy, get, replace_in_file
from conan.tools.gnu import Autotools

import os

class LibctruConan(ConanFile):
    name = 'libctru'
    settings = 'compiler', 'build_type'
    description = 'C library for writing user mode arm11 code for the 3DS (CTR)'
    url = 'https://github.com/devkitPro/libctru'

    _source_subfolder = 'libctru'

    generators = "AutotoolsToolchain"

    def validate(self):
        conan_data = self.conan_data["sources"][self.version]
        minver = conan_data["dka_min"]
        maxver = conan_data.get("dka_max", None)
        ver = int(self.conf.get("user.devkitarm:version"))
        if ver < minver or (maxver and ver > maxver):
            raise ConanInvalidConfiguration("Selected toolchain cannot built this library version. Change your Conan profile to devkitarm >=%s%s" % (minver, (" and <=%s" % maxver) if maxver else ""))

    def source(self):
        conan_data = self.conan_data["sources"][self.version]
        get(self, url=conan_data["url"], sha256=conan_data["sha256"], strip_root=True)

        # Disable -Werror
        replace_in_file(self, "%s/Makefile" % self._source_subfolder, "-Werror", "", strict=False)

    def build(self):
        with chdir(self, os.path.join(self.source_folder, self._source_subfolder)):
            autotools = Autotools(self)
            autotools.make()

    def package(self):
        copy(self, "*", src=self._source_subfolder, dst=self.package_folder)

    def package_info(self):
        self.cpp_info.includedirs = ['include']
        self.cpp_info.libs = collect_libs(self)

        self.buildenv_info.define("CTRULIB", os.path.join(self.package_folder))
