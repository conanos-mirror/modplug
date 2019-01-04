from conans import ConanFile, tools, MSBuild
from conanos.build import config_scheme
import os, shutil


class ModplugConan(ConanFile):
    name = "modplug"
    version = "0.8.9.0.r274"
    description = "A ModPlug audio rendering engine"
    url = "https://github.com/conanos/modplug"
    homepage = "https://sourceforge.net/projects/modplug-xmms/"
    license = "LGPLv2.1+"
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def source(self):
        url_ = 'https://github.com/ShiftMediaProject/modplug/archive/{version}.tar.gz'
        tools.get(url_.format(version=self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"SMP")):
                msbuild = MSBuild(self)
                build_type = str(self.settings.build_type) + ("DLL" if self.options.shared else "")
                msbuild.build("libmodplug.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'},build_type=build_type)

    def package(self):
        if self.settings.os == 'Windows':
            platforms={'x86': 'Win32', 'x86_64': 'x64'}
            rplatform = platforms.get(str(self.settings.arch))
            self.copy("*", dst=os.path.join(self.package_folder,"include"), src=os.path.join(self.build_folder,"..", "msvc","include"))
            if self.options.shared:
                for i in ["lib","bin"]:
                    self.copy("*", dst=os.path.join(self.package_folder,i), src=os.path.join(self.build_folder,"..","msvc",i,rplatform))
            self.copy("*", dst=os.path.join(self.package_folder,"licenses"), src=os.path.join(self.build_folder,"..", "msvc","licenses"))

            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            shutil.copyfile(os.path.join(self.build_folder,self._source_subfolder,"libmodplug.pc.in"),
                            os.path.join(self.package_folder,"lib","pkgconfig", "libmodplug.pc"))
            lib = "-lmodplugd" if self.options.shared else "-lmodplug"
            replacements = {
                "@prefix@"            : self.package_folder,
                "@exec_prefix@"       : "${prefix}/bin",
                "@libdir@"            : "${prefix}/lib",
                "@VERSION@"           : self.version,
                "-lmodplug"           : lib,
            }
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig", "libmodplug.pc"),s,r)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

