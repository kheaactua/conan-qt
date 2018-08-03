#!/usr/bin/env python
# -*- coding: future_fstrings -*-
# -*- coding: utf-8 -*-

import os, shutil, glob, re
from conans import AutoToolsBuildEnvironment, ConanFile, tools, VisualStudioBuildEnvironment
from conans.tools import cpu_count, os_info, SystemPackageTool
from conans.errors import ConanException


class QtConan(ConanFile):
    """
    Qt Conan package
    """

    name        = 'qt'
    version     = "5.3.2"
    description = 'Conan.io package for Qt library.'
    source_dir  = 'qt5'
    license     = 'LGPL'
    url         = 'https://www.qt.io/'
    settings    = 'os', 'arch', 'compiler', 'build_type'
    options = {
        'shared':            [True, False],
        'opengl':            ['desktop', 'dynamic'],
        'openssl':           ['no', 'yes', 'linked'],
    }
    default_options = (
        'shared=True',
        'opengl=desktop',
        'openssl=no',
    )
    requires = (
        'helpers/0.3@ntc/stable',
    )
    exports = 'md5s/md5sums-*.txt'

    license = 'http://doc.qt.io/qt-5/lgpl.html'
    short_paths = True

    build_command = None

    def system_requirements(self):
        pack_names = None
        if os_info.linux_distro == 'ubuntu':
            pack_names = [
                'libgl1-mesa-dev', 'libxcb1', 'libxcb1-dev',
                'libx11-xcb1', 'libx11-xcb-dev', 'libxcb-keysyms1',
                'libxcb-keysyms1-dev', 'libxcb-image0', 'libxcb-image0-dev',
                'libxcb-shm0', 'libxcb-shm0-dev', 'libxcb-icccm4',
                'libxcb-icccm4-dev', 'libxcb-sync1', 'libxcb-sync-dev',
                'libxcb-xfixes0-dev', 'libxrender-dev', 'libxcb-shape0-dev',
                'libxcb-randr0-dev', 'libxcb-render-util0', 'libxcb-render-util0-dev',
                'libxcb-glx0-dev', 'libxcb-xinerama0', 'libxcb-xinerama0-dev',
                'dos2unix', 'xz-utils', 'chrpath', 'libdbus-1-dev'
            ]

            if self.settings.arch == 'x86':
                full_pack_names = []
                for pack_name in pack_names:
                    full_pack_names += [pack_name + ':i386']
                pack_names = full_pack_names

        if pack_names:
            installer = SystemPackageTool()
            try:
                installer.update() # Update the package database
                installer.install(' '.join(pack_names)) # Install the package
            except ConanException:
                self.output.warn('Could not run system requirements installer.  Required packages might be missing.')

    def config_options(self):
        if self.settings.os != 'Windows':
            del self.options.opengl
            del self.options.openssl

    def requirements(self):
        if self.settings.os == 'Windows':
            if self.options.openssl == 'yes':
                self.requires('OpenSSL/1.0.2l@conan/stable', dev=True)
            elif self.options.openssl == 'linked':
                self.requires('OpenSSL/1.0.2l@conan/stable')

    def source(self):
        import platform_helpers

        (release, major) = [int(i) for i in self.version.split('.')[:2]]

        if 'Windows' == self.settings.os:
            tools.download("https://download.qt.io/official_releases/jom/jom_1_1_2.zip", "jom.zip")
            tools.unzip("jom.zip")

        # Debugging flag that should be removed.
        use_local = False

        if use_local:
            download_url = os.path.join(r'C:\\', 'tmp', 'qt-everywhere-opensource-src-{self.version}')
            # This still takes forever...
            self.run(f"robocopy {download_url} {self.source_dir} /s /e")
        else:
            ext = 'tar.xz' if self.settings.os == 'Linux' else 'zip'

            if major >= 9:
                download_url = f'https://download.qt.io/official_releases/qt/{release}.{major}/{self.version}/single/qt-everywhere-opensource-src-{self.version}.{ext}'
            else:
                download_url = f'http://download.qt.io/archive/qt/{release}.{major}/{self.version}/single/qt-everywhere-opensource-src-{self.version}.{ext}'

            archive = os.path.basename(download_url)
            self.output.info("Downloading %s"%download_url)
            tools.download(url=download_url, filename=archive)

            # Check against our cached md5 hashes.
            hash_file = os.path.join('md5s', f'md5sums-{self.version}.txt')
            if not os.path.exists(hash_file):
                raise ConanException(f'Cannot find cached md5sums for Qt {self.version}.  Please download the md5 hashes from %s/md5sums.txt as md5sums-{self.version}.txt and place them in the md5s directory with this recipe.'%(os.path.dirname(download_url)))
            platform_helpers.check_hash(file_path=archive, hash_file=hash_file, fnc=tools.check_md5)

            if ext == 'tar.xz':
                self.run(f'tar xf {archive}')
            else:
                tools.unzip(archive)
            shutil.move(f'qt-everywhere-opensource-src-{self.version}', self.source_dir)
            os.unlink(archive)

    def build(self):
        major = int(self.version.split('.')[1])

        args = [
            '-opensource',
            '-confirm-license',
            '-nomake examples',
            '-nomake tests',
            '-debug' if self.settings.build_type=='Debug' else '-release',
            '-skip script',
            '-make libs',
            '-make tools',
            '-plugin-sql-sqlite',
            f'-prefix {self.package_folder}',
            # "-skip texttospeech",
            # "-skip datavisualization",
            # "-skip scripttools",
            # "-make sql",
            # "-make gui",
            # "-make multimedia -make multimediawidgets",
        ]
        if not self.options.shared:
            args.insert(0, "-static")
        if 'Linux' == self.settings.os:
            args.append('-dbus')

        if major >= 9:
            args.append('-skip webengine')
            args.append('-skip charts')
            args.append('-skip datavis3d')
            args.append('-skip speech')
            args.append('-skip purchasing')
            args.append('-skip remoteobjects')
            args.append('-skip webview')

        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio":
                self._build_msvc(args)
            else:
                self._build_mingw(args)
        else:
            self._build_unix(args)

    def _build_msvc(self, args): # {{{
        from platform_helpers import which

        self.output.info('Using MSVC build procedure')

        # self.build_command = find_executable("jom.exe")
        # self.build_command = which(os.path.join(self.source_dir, "jom.exe"))
        self.build_command = which("jom.exe")
        self.output.info("Attempting to find JOM at %s"%self.build_command)
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
        self.output.info('Using MinGW build procedure')

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
        self.output.info('Using *nix build procedure')

        args += ['-silent']
        if self.settings.os == "Linux":
            args += ["-xcb"]
            if 'clang' in self.settings.compiler:
                args += ['-platform linux-clang']
            elif self.settings.arch == "x86":
                args += ["-platform linux-g++-32"]
        else:
            args += ["-no-framework"]
            if self.settings.arch == "x86":
                args += ["-platform macx-clang-32"]

        self.run("find \"%s\" -name 'configure' -exec chmod u+x {} \\;"%self.source_dir)
        self.run("find \"%s\" -name 'configure' -exec dos2unix {} {} \\;"%self.source_dir)
        self.output.info('Using %s threads'%str(cpu_count()))
        self.output.info('Configure options: %s'%(' '.join(args)))
        self.run(f'cd {self.source_dir} && ./configure %s'%(' '.join(args)))
        self.output.info('Running make')
        self.run(f'cd {self.source_dir} && make -j %s'%(str(cpu_count())))
    # }}}

    def package(self):
        if self.settings.compiler == "Visual Studio":
            vcvars = tools.vcvars_command(self.settings)
            self.run("cd %s && %s && %s install"%(self.source_dir, vcvars, self.build_command))
        elif self.settings.os == "Linux":
            self.run("cd %s && make install"%(self.source_dir))

            # Set the RPATH of the installed binaries
            # Maybe the RUNPATH should also be set? http://blog.qt.io/blog/2011/10/28/rpath-and-runpath/
            # https://forum.qt.io/topic/59670/how-to-compile-qt-with-relative-runpath-paths/4
            self.output.info('Modifying RPATH on Qt binaries to use relative paths')
            binaries = glob.glob(os.path.join(self.package_folder, 'bin', '*'))
            for b in binaries:
                try:
                    # self.output.info(f"chrpath -r '$OGIGIN/../lib' {b}")
                    self.run(f"chrpath -r '$ORIGIN/../lib' {b}")
                except ConanException:
                    self.output.warn(f'Could not modify rpath on {b}')

    def package_info(self):
        libs = [
            'Concurrent', 'Core', 'DBus',
            'Gui', 'Network', 'OpenGL',
            'Sql', 'Test', 'Widgets', 'Xml'
        ]

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

        # Put qmake and DLLs in the path
        if self.settings.os == "Windows":
            self.env_info.path.append(os.path.join(self.package_folder, "bin"))

        # Make it easier for CMake to find Qt
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)

        if 'Linux' == self.settings.os:
            # Populate the pkg-config environment variables
            with tools.pythonpath(self):
                from platform_helpers import adjustPath, appendPkgConfigPath

                pkg_config_path = os.path.join(self.package_folder, 'lib', 'pkgconfig')
                appendPkgConfigPath(adjustPath(pkg_config_path), self.env_info)

                pc_files = glob.glob(adjustPath(os.path.join(pkg_config_path, '*.pc')))
                for f in pc_files:
                    p_name = re.sub(r'\.pc$', '', os.path.basename(f))
                    p_name = re.sub(r'\W', '_', p_name.upper())
                    setattr(self.env_info, f'PKG_CONFIG_{p_name}_PREFIX', adjustPath(self.package_folder))

                appendPkgConfigPath(adjustPath(pkg_config_path), self.env_info)

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
