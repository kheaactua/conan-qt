# Based on https://github.com/osechet/conan-qt/blob/master/conanfile.py

import os
from conans import AutoToolsBuildEnvironment, ConanFile, tools, VisualStudioBuildEnvironment
from conans.tools import cpu_count, os_info, SystemPackageTool, download, unzip
import shutil

def which(program):
    """
    Locate a command.
    """
    def is_exe(fpath):
        """
        Check if a path is executable.
        """
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

class QtConan(ConanFile):
    """
    Qt Conan package

    Tested with Qt 5.9.3, 5.9.4
    """

    name = 'qt'
    description = 'Conan.io package for Qt library.'
    source_dir = 'qt5'
    license = 'LGPL'
    settings = 'os', 'arch', 'compiler', 'build_type'
    options = {
        'shared':            [True, False],
        # 'gamepad':           [True, False],
        # 'canvas3d':          [True, False],
        # 'graphicaleffects':  [True, False],
        # 'imageformats':      [True, False],
        # 'location':          [True, False],
        # 'serialport':        [True, False],
        # 'svg':               [True, False],
        # 'tools':             [True, False],
        # 'webengine':         [True, False],
        # 'websockets':        [True, False],
        # 'xmlpatterns':       [True, False],
        'opengl':            ['desktop', 'dynamic'],
        'openssl':           ['no', 'yes', 'linked'],
    }
    default_options =
        'shared=True',
        # 'canvas3d=True',
        # 'gamepad=False',
        # 'graphicaleffects=False',
        # 'imageformats=False',
        # 'location=False',
        'opengl=desktop',
        'openssl=no'
        # 'serialport=False',
        # 'svg=False',
        # 'tools=True',
        # 'webengine=False',
        # 'websockets=False',
        # 'xmlpatterns=False',


    license = 'http://doc.qt.io/qt-5/lgpl.html'
    short_paths = True

    build_command = None

    def system_requirements(self):
        pack_names = None
        if os_info.linux_distro == "ubuntu":
            pack_names = [
                "libgl1-mesa-dev", "libxcb1", "libxcb1-dev",
                "libx11-xcb1", "libx11-xcb-dev", "libxcb-keysyms1",
                "libxcb-keysyms1-dev", "libxcb-image0", "libxcb-image0-dev",
                "libxcb-shm0", "libxcb-shm0-dev", "libxcb-icccm4",
                "libxcb-icccm4-dev", "libxcb-sync1", "libxcb-sync-dev",
                "libxcb-xfixes0-dev", "libxrender-dev", "libxcb-shape0-dev",
                "libxcb-randr0-dev", "libxcb-render-util0", "libxcb-render-util0-dev",
                "libxcb-glx0-dev", "libxcb-xinerama0", "libxcb-xinerama0-dev",
                "dos2unix", "xz-utils"
            ]

            if self.settings.arch == "x86":
                full_pack_names = []
                for pack_name in pack_names:
                    full_pack_names += [pack_name + ":i386"]
                pack_names = full_pack_names

        if pack_names:
            installer = SystemPackageTool()
            installer.update() # Update the package database
            installer.install(" ".join(pack_names)) # Install the package

    def config_options(self):
        if self.settings.os != "Windows":
            del self.options.opengl
            del self.options.openssl

    def requirements(self):
        if self.settings.os == "Windows":
            if self.options.openssl == "yes":
                self.requires("OpenSSL/1.0.2l@conan/stable", dev=True)
            elif self.options.openssl == "linked":
                self.requires("OpenSSL/1.0.2l@conan/stable")

    def source(self):

        release = int(self.version.split(".")[0])
        major = int(self.version.split(".")[1])
        minor = ".".join(self.version.split(".")[:2])

        download("https://download.qt.io/official_releases/jom/jom_1_1_2.zip", "jom.zip")
        unzip("jom.zip")

        # Debugging flag that should be removed.
        use_local = False

        if use_local:
            download_url = r'C:\\tmp\\qt-everywhere-opensource-src-{self.version}5.9.3'
            # This still takes forever
            self.run(f"robocopy {download_url} {self.source_dir} /s /e")
        else:
            zip_name = f"{self.name}-{self.version}.zip"
            ext = "tar.xz" if self.settings.os == "Linux" else "zip"

            if major >= 9:
                download_url = f'https://download.qt.io/official_releases/qt/{major}/{self.version}/single/qt-everywhere-opensource-src-{self.version}.{ext}'
            else:
                download_url = f'http://download.qt.io/archive/qt/{release}.{major}/{self.version}/single/qt-everywhere-opensource-src-{self.version}.{ext}'

            self.output.info("Downloading %s"%download_url)
            download(download_url, zip_name)
            if ext == 'tar.xz':
                self.run(f"tar xf {zip_name}")
            else:
                unzip(zip_name)
            shutil.move(f"qt-everywhere-opensource-src-{self.version}", self.source_dir)
            os.unlink(zip_name)

    def build(self):
        # submodules = ['qtbase']
        # if self.options.canvas3d:
        #     submodules.append('qtcanvas3d')
        # if self.options.gamepad:
        #     submodules.append('qtgamepad')
        # if self.options.graphicaleffects:
        #     submodules.append('qtgraphicaleffects')
        # if self.options.imageformats:
        #     submodules.append('qtimageformats')
        # if self.options.location:
        #     submodules.append('qtlocation')
        # if self.options.serialport:
        #     submodules.append('qtserialport')
        # if self.options.svg:
        #     submodules.append('qtsvg')
        # if self.options.tools:
        #     submodules.append('qttools')
        # if self.options.webengine:
        #     submodules.append('qtwebengine')
        # if self.options.websockets:
        #     submodules.append('qtwebsockets')
        # if self.options.xmlpatterns:
        #     submodules.append('qtxmlpatterns')

        args = [
            '-opensource',
            '-confirm-license',
            '-nomake examples',
            '-nomake tests',
            '-debug' if self.settings.build_type=='Debug' else '-release',
            '-skip webengine',
            '-skip charts',
            '-skip datavis3d',
            '-skip speech',
            '-skip purchasing',
            '-skip remoteobjects',
            '-skip script',
            '-skip webview',
            '-make libs',
            '-make tools',
            '-plugin-sql-sqlite',
            f'-prefix {self.package_folder}'
            # "-skip texttospeech",
            # "-skip datavisualization",
            # "-skip scripttools",
            # "-make sql",
            # "-make gui",
            # "-make multimedia -make multimediawidgets",
        ]
        if not self.options.shared:
            args.insert(0, "-static")

        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio":
                self._build_msvc(args)
            else:
                self._build_mingw(args)
        else:
            self._build_unix(args)

    def _build_msvc(self, args): # {{{
        # self.build_command = find_executable("jom.exe")
        # self.build_command = which(os.path.join(self.source_dir, "jom.exe"))
        self.build_command = which("jom.exe")
        self.output.info("Attempting to find JOM at %s"%self.build_command)
        self.output.info("self.source_dir = %s"%self.source_dir)
        if self.build_command:
            build_args = ["-j", str(cpu_count())]
        else:
            self.build_command = "nmake.exe"
            build_args = []
        self.output.info("Using '%s %s' to build"%(self.build_command, " ".join(build_args)))

        env = {}
        # env.update({'PATH': ['%s/qtbase/bin' % self.conanfile_directory,
        #                      '%s/gnuwin32/bin' % self.conanfile_directory,
        #                      '%s/qtrepotools/bin' % self.conanfile_directory]})

        # it seems not enough to set the vcvars for older versions
        if self.settings.compiler == "Visual Studio":
            args.append("-mp")
            if self.settings.compiler.version == "15":
                env.update({'QMAKESPEC': 'win32-msvc2017'})
                args += ["-platform win32-msvc2017"]
            if self.settings.compiler.version == "14":
                env.update({'QMAKESPEC': 'win32-msvc2015'})
                args += ["-platform win32-msvc2015"]
            if self.settings.compiler.version == "12":
                env.update({'QMAKESPEC': 'win32-msvc2013'})
                args += ["-platform win32-msvc2013"]
            if self.settings.compiler.version == "11":
                env.update({'QMAKESPEC': 'win32-msvc2012'})
                args += ["-platform win32-msvc2012"]
            if self.settings.compiler.version == "10":
                env.update({'QMAKESPEC': 'win32-msvc2010'})
                args += ["-platform win32-msvc2010"]

        # Do I need this?
        env_build = VisualStudioBuildEnvironment(self)
        env.update(env_build.vars)

        # Workaround for conan-io/conan#1408
        env_keys = list(env.keys())
        for key in env_keys:
            if not env[key]:
                del env[key]

        # The configure tells us to remove these variables
        for key in ['QMAKESPEC', 'XQMAKESPEC', 'QMAKEPATH', 'QMAKEFEATURES']:
            if key in env:
                del env[key]

        with tools.environment_append(env):
            vcvars = tools.vcvars_command(self.settings)

            args += ["-opengl %s" % self.options.opengl]
            if self.options.openssl == "no":
                args += ["-no-openssl"]
            elif self.options.openssl == "yes":
                args += ["-openssl"]
            else:
                args += ["-openssl-linked"]

            self.run("cd %s && %s && configure %s"
                     %(self.source_dir, vcvars, ' '.join(args)))
            self.run("cd %s && %s && %s %s"
                     %(self.source_dir, vcvars, self.build_command, ' '.join(build_args)))
            # self.run("cd %s && %s && %s install" % (self.source_dir, vcvars, build_command))
    # }}}

    def _build_mingw(self, args): # {{{
        env_build = AutoToolsBuildEnvironment(self)
        env = {'PATH': [
                    f'{self.build_folder}/bin',
                    f'{self.build_folder}/qtbase/bin',
                    f'{self.build_folder}/gnuwin32/bin',
                    f'{self.build_folder}/qtrepotools/bin'
                ],
               'QMAKESPEC': 'win32-g++'}
        env.update(env_build.vars)
        with tools.environment_append(env):
            # Workaround for configure using clang first if in the path
            new_path = []
            for item in os.environ['PATH'].split(';'):
                if item != 'C:\\Program Files\\LLVM\\bin':
                    new_path.append(item)
            os.environ['PATH'] = ';'.join(new_path)
            # end workaround
            args += ["-developer-build",
                     "-opengl %s" % self.options.opengl,
                     "-platform win32-g++"]

            self.output.info("Using '%s' threads" % str(cpu_count()))
            self.run("cd %s && configure.bat %s"
                     % (self.source_dir, " ".join(args)))
            self.run("cd %s && mingw32-make -j %s"
                     % (self.source_dir, str(cpu_count())))
            self.run("cd %s && mingw32-make install" % (self.source_dir))
    # }}}

    def _build_unix(self, args): # {{{
        if self.settings.os == "Linux":
            args += ["-silent", "-xcb"]
            if self.settings.arch == "x86":
                args += ["-platform linux-g++-32"]
        else:
            args += ["-silent", "-no-framework"]
            if self.settings.arch == "x86":
                args += ["-platform macx-clang-32"]

        self.output.info("Using '%s' threads" % str(cpu_count()))
        self.output.info("Configure options: %s"%(' '.join(args)))
        self.run(f"find \"{self.source_dir}\" -name 'configure' -exec chmod u+x {{}} \\;")
        self.run(f"find \"{self.source_dir}\" -name 'configure' -exec dos2unix {{}} {{}} \\;")
        self.run("cd %s && ./configure %s"%(self.source_dir, " ".join(args)))
        self.run("cd %s && make -j %s"%(self.source_dir, str(cpu_count())))
    # }}}

    def package(self):
        if self.settings.compiler == "Visual Studio":
            vcvars = tools.vcvars_command(self.settings)
            self.run("cd %s && %s && %s install"%(self.source_dir, vcvars, self.build_command))
        elif self.settings.os == "Linux":
            self.run("cd %s && make install"%(self.source_dir))

    def package_info(self):
        libs = ['Concurrent', 'Core', 'DBus',
                'Gui', 'Network', 'OpenGL',
                'Sql', 'Test', 'Widgets', 'Xml']

        self.cpp_info.libs = []
        self.cpp_info.includedirs = ["include"]
        for lib in libs:
            if self.settings.os == "Windows" and self.settings.build_type == "Debug":
                suffix = "d"
            elif self.settings.os == "Macos" and self.settings.build_type == "Debug":
                suffix = "_debug"
            else:
                suffix = ""
            self.cpp_info.libs += ["Qt5%s%s" % (lib, suffix)]
            self.cpp_info.includedirs += ["include/Qt%s" % lib]

        if self.settings.os == "Windows":
            # Some missing shared libs inside QML and others, but for the test it works
            self.env_info.path.append(os.path.join(self.package_folder, "bin"))

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
