%global package_speccommit ccb8ee3c01ade60b0ee7a22436d4b25d84702ae4
%global usver 6.12.66
%define uname 6.12.66
%define short_uname 6.12
%define srcpath /usr/src/kernels/%{uname}-%{_arch}

# Control whether we perform a compat. check against published ABI.
# Default enabled: (to override: --without kabichk)
%define do_kabichk  %{?_without_kabichk: 0} %{?!_without_kabichk: 1}
# Default disabled: (to override: --with kabichk)
#%%define do_kabichk  %%{?_with_kabichk: 1} %%{?!_with_kabichk: 0}

#
# Adjust debuginfo generation to suit building a kernel:
#
# Don't run dwz.
%undefine _find_debuginfo_dwz_opts
# Don't try to generate minidebuginfo.
%undefine _include_minidebuginfo
# Resolve trivial relocations in debug sections.
# This reduces the size of debuginfo.
%define _find_debuginfo_opts -r

# RPM tries to bytecompile Python sources files it finds in /usr/src and fails
# since some of them are for Python 3 only. Just ignore the errors.
%global _python_bytecompile_errors_terminate_build 0

%define lp_devel_dir %{_usrsrc}/kernel-%{version}-%{release}

# Prevent RPM adding Provides/Requires to lp-devel package
%global __provides_exclude_from ^%{lp_devel_dir}/.*$
%global __requires_exclude_from ^%{lp_devel_dir}/.*$

Name: kernel
License: GPLv2
Version: %{usver}
Release: 0.ydi.0
ExclusiveOS: Linux
Summary: The Linux kernel
BuildRequires: kmod
BuildRequires: dwarves
BuildRequires: elfutils-libelf-devel
BuildRequires: elfutils-devel
#BuildRequires: elfutils-debuginfod-client-devel
BuildRequires: libtraceevent-devel
BuildRequires: openssl-devel
BuildRequires: openssl
BuildRequires: rsync
BuildRequires: systemtap-sdt-devel

# These build dependencies are needed for building the main kernel and
# modules as well live patches.
%define core_builddeps() %{lua:
    deps = {
        'bc',
        'bison',
        'gcc',
        'binutils-devel',
        'flex',
        'hostname',
    }
    for _, dep in ipairs(deps) do
        print(rpm.expand("%1") .. ': ' .. dep .. '\\n')
    end
}

%{core_builddeps BuildRequires}
%if %{do_kabichk}
BuildRequires: python
%endif

BuildRequires: xz-devel
BuildRequires: libunwind-devel
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: asciidoc xmlto
%{?_cov_buildrequires}
AutoReqProv: no
Provides: kernel-uname-r = %{uname}
Provides: kernel = %{version}-%{release}
Provides: kernel-%{_arch} = %{version}-%{release}
Requires(post): coreutils kmod
Requires(posttrans): coreutils dracut kmod

Source0: linux-%{usver}.tar.xz
Source1: kernel-x86_64.config
Source2: macros.kernel
%if %{do_kabichk}
Source3: check-kabi
Source4: Module.kabi
%endif

%description
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system. The kernel handles the basic functions of the operating
system: memory allocation, process allocation, device input and output, etc.


%package headers
License: GPLv2
Summary: Header files for the Linux kernel for use by glibc
Group: Development/System
Obsoletes: glibc-kernheaders < 3.0-46
Provides: glibc-kernheaders = 3.0-46
Provides: kernel-headers = %{uname}
Conflicts: kernel-headers < %{uname}

%description headers
Kernel-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
glibc package.

%package devel
License: GPLv2
Summary: Development package for building kernel modules to match the %{uname} kernel
Group: System Environment/Kernel
AutoReqProv: no
Provides: kernel-devel-%{_arch} = %{version}-%{release}
Provides: kernel-devel-uname-r = %{uname}

%description devel
This package provides kernel headers and makefiles sufficient to build modules
against the %{uname} kernel.

%package lp-devel_%{version}_%{release}
License: GPLv2
Summary: Development package for building livepatches
Group: Development/System
%{core_builddeps Requires}

%description lp-devel_%{version}_%{release}
Contains the prepared source files, config, and vmlinux for building live
patches against base version %{version}-%{release}.

%package -n perf
Summary: Performance monitoring for the Linux kernel
License: GPLv2
%description -n perf
This package contains the perf tool, which enables performance monitoring
of the Linux kernel.

%global pythonperfsum Python bindings for apps which will manipulate perf events
%global pythonperfdesc A Python module that permits applications \
written in the Python programming language to use the interface \
to manipulate perf events.

%package -n python3-perf
Summary: %{pythonperfsum}
Provides: python3-perf
%description -n python3-perf
%{pythonperfdesc}

%prep
%autosetup -p1 -n linux-%{usver}
%{?_cov_prepare}

%build

# This override tweaks the kernel makefiles so that we run debugedit on an
# object before embedding it.  When we later run find-debuginfo.sh, it will
# run debugedit again.  The edits it does change the build ID bits embedded
# in the stripped object, but repeating debugedit is a no-op.  We do it
# beforehand to get the proper final build ID bits into the embedded image.
# This affects the vDSO images in vmlinux, and the vmlinux image in bzImage.
export AFTER_LINK='sh -xc "/usr/lib/rpm/debugedit -b %{buildroot} -d /usr/src/debug -i $@ > $@.id"'

cp -f %{SOURCE1} .config
# make sure configuration is up to date
%{?_cov_wrap} make olddefconfig
bash -c 'diff -u <(grep -v "^#" .config) <(grep -v "^#" %{SOURCE1})'

%{?_cov_wrap} make %{?_smp_mflags} bzImage
%{?_cov_wrap} make %{?_smp_mflags} modules

#
# Check the kernel ABI (KABI) has not changed.
#
# The format of kernel ABI version is V.P.0+A.
#
#   V - kernel version (e.g., 3)
#   P - kernel patch level (e.g., 10)
#   A - KABI version.
#
# Note that the version does not include the sub-level version used in
# the stable kernels.  This allows the kernel updates to include the
# latest stable release without changing the KABI.
#
# ABI checking should be disabled by default for development kernels
# (those with a "0" ABI version).
#
# If this check fails you can:
#
# 1. Remove or edit patches until the ABI is the same again.
#
# 2. Remove the functions from the KABI file (if those functions are
#    guaranteed to not be used by any driver or third party module).
#    Be careful with this option.
#
# 3. Increase the ABI version (in the abi-version patch) and copy
#    the Module.symvers file from the build directory to the root of
#    the patchqueue repository and name it Module.kabi.
#
%if %{do_kabichk}
    echo "**** kABI checking is enabled in kernel SPEC file. ****"
    %{SOURCE3} -k %{SOURCE4} -s Module.symvers || exit 1
%endif

# make perf
%define _lto_cflags %{nil}
%global perf_make \
  %{?_cov_wrap} make EXTRA_CFLAGS="${RPM_OPT_FLAGS}" LDFLAGS="%{__global_ldflags}" %{?cross_opts} V=1 NO_PERF_READ_VDSO32=1 NO_PERF_READ_VDSOX32=1 WERROR=0 HAVE_CPLUS_DEMANGLE=1 NO_GTK2=1 NO_STRLCPY=1 NO_BIONIC=1 NO_JVMTI=1 NO_LIBCRYPTO=1 prefix=%{_prefix}
%global perf_python3 -C tools/perf PYTHON=%{__python3}
# perf
# make sure check-headers.sh is executable
chmod +x tools/perf/check-headers.sh
%{perf_make} %{perf_python3} all

pushd tools/perf/Documentation/
make %{?_smp_mflags} man
popd

# # eBPF support: pahole encodes the type infos into a small (3MB) .BTF section:
# cp vmlinux                                     tmp-vmlinux-with-btf
# LLVM_OBJCOPY=objcopy pahole %{?_smp_mflags} -J tmp-vmlinux-with-btf
# # Copy the BTF section into a new BTF file which eBPF tools to get kernel types:
# objcopy --only-section .BTF                    tmp-vmlinux-with-btf vmlinux.btf
# rm                                             tmp-vmlinux-with-btf

%install
# Install kernel
install -d -m 755 %{buildroot}/boot
install -m 644 .config %{buildroot}/boot/config-%{uname}
install -m 644 System.map %{buildroot}/boot/System.map-%{uname}
install -m 644 arch/x86/boot/bzImage %{buildroot}/boot/vmlinuz-%{uname}
truncate -s 20M %{buildroot}/boot/initrd-%{uname}.img
ln -sf vmlinuz-%{uname} %{buildroot}/boot/vmlinuz-%{short_uname}-xen
ln -sf initrd-%{uname}.img %{buildroot}/boot/initrd-%{short_uname}-xen.img

# Install modules
# Override $(mod-fw) because we don't want it to install any firmware
# we'll get it from the linux-firmware package and we don't want conflicts
make INSTALL_MOD_PATH=%{buildroot} modules_install mod-fw=
# mark modules executable so that strip-to-file can strip them
find %{buildroot}/lib/modules/%{uname} -name "*.ko" -type f | xargs chmod u+x

install -d -m 755 %{buildroot}/lib/modules/%{uname}/extra
install -d -m 755 %{buildroot}/lib/modules/%{uname}/updates

make INSTALL_MOD_PATH=%{buildroot} vdso_install

#XCP-ng: needs clarification about how to get debuginfo rpm generated in el10?
# # Save debuginfo
# install -d -m 755 %{buildroot}/usr/lib/debug/lib/modules/%{uname}
# install -m 755 vmlinux %{buildroot}/usr/lib/debug/lib/modules/%{uname}

# Install -headers files
make INSTALL_HDR_PATH=%{buildroot}/usr headers_install

# perf tool binary and supporting scripts/binaries
%{perf_make} %{perf_python3} DESTDIR=%{buildroot} lib=%{_lib} install-bin
# remove the 'trace' symlink.
rm -f %{buildroot}%{_bindir}/trace
# remove the perf-tips
rm -rf %{buildroot}%{_docdir}/perf-tip

# For both of the below, yes, this should be using a macro but right now
# it's hard coded and we don't actually want it anyway right now.
# Whoever wants examples can fix it up!

# remove examples
rm -rf %{buildroot}/usr/lib/perf/examples
# remove the stray header file that somehow got packaged in examples
rm -rf %{buildroot}/usr/lib/perf/include/bpf/

# python-perf extension
%{perf_make} %{perf_python3} DESTDIR=%{buildroot} install-python_ext

# perf man pages (note: implicit rpm magic compresses them later)
install -d %{buildroot}/%{_mandir}/man1
install -pm0644 tools/perf/Documentation/*.1 %{buildroot}/%{_mandir}/man1/

# Install -devel files
install -d -m 755 %{buildroot}%{_usrsrc}/kernels/%{uname}-%{_arch}
install -d -m 755 %{buildroot}%{_rpmconfigdir}/macros.d
install -m 644 %{SOURCE2} %{buildroot}%{_rpmconfigdir}/macros.d
echo '%%kernel_version %{uname}' >> %{buildroot}%{_rpmconfigdir}/macros.d/macros.kernel
%{?_cov_install}

# Setup -devel links correctly
ln -nsfr %{srcpath} %{buildroot}/lib/modules/%{uname}/source
ln -nsfr %{srcpath} %{buildroot}/lib/modules/%{uname}/build

# Copy Makefiles and Kconfigs except in some directories
paths=$(find . -path './Documentation' -prune -o -path './scripts' -prune -o -path './include' -prune -o -type f -a \( -name "Makefile*" -o -name "Kconfig*" \) -print)
cp --parents $paths %{buildroot}%{srcpath}
cp Module.symvers %{buildroot}%{srcpath}
cp System.map %{buildroot}%{srcpath}
cp .config %{buildroot}%{srcpath}
cp -a scripts %{buildroot}%{srcpath}
find %{buildroot}%{srcpath}/scripts -type f -name '*.o' -delete
cp -a tools/objtool/objtool %{buildroot}%{srcpath}/tools/objtool

cp -a --parents arch/x86/include %{buildroot}%{srcpath}
cp -a include %{buildroot}%{srcpath}/include

# files for 'make prepare' to succeed with kernel-devel
cp -a --parents arch/x86/entry/syscalls/syscall_32.tbl %{buildroot}%{srcpath}
cp -a --parents scripts/syscalltbl.sh %{buildroot}%{srcpath}
cp -a --parents scripts/syscallhdr.sh %{buildroot}%{srcpath}
cp -a --parents arch/x86/entry/syscalls/syscall_64.tbl %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs_32.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs_64.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs_common.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs.h %{buildroot}%{srcpath}
cp -a --parents tools/include/tools/le_byteshift.h %{buildroot}%{srcpath}
cp -a --parents arch/x86/purgatory/purgatory.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/purgatory/stack.S %{buildroot}%{srcpath}
cp -a --parents arch/x86/boot/compressed/string.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/purgatory/setup-x86_64.S %{buildroot}%{srcpath}
cp -a --parents arch/x86/purgatory/entry64.S %{buildroot}%{srcpath}
cp -a --parents arch/x86/boot/string.h %{buildroot}%{srcpath}
cp -a --parents arch/x86/boot/string.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/boot/ctype.h %{buildroot}%{srcpath}

# Copy .config to include/config/auto.conf so "make prepare" is unnecessary.
cp -a %{buildroot}%{srcpath}/.config %{buildroot}%{srcpath}/include/config/auto.conf

# Make sure the Makefile and version.h have a matching timestamp so that
# external modules can be built
touch -r %{buildroot}%{srcpath}/Makefile %{buildroot}%{srcpath}/include/generated/uapi/linux/version.h

find %{buildroot} -name '.*.cmd' -type f -delete

# Install files for building live patches
install -m 644 vmlinux %{buildroot}%{lp_devel_dir}

# eBPF support: Install the BTF file to /usr/src/kernels for kernel-devel
# /usr/src/kernels is also used by `perf` to look for vmlinux files with
# DWARF debuginfo, but because the BTF file only contains the BTF section,
# `perf` ignores it while searching for the vmlinux file if kernel-debuginfo:
#
# strace -e file perf probe -v -L icmp_rcv
# Looking at the vmlinux_path (8 entries long)
# open("/boot/vmlinux", O_RDONLY)         = ENOENT
# open("/boot/vmlinux-4.19.0+1", O_RDONLY) = ENOENT
# open("/usr/lib/debug/boot/vmlinux-4.19.0+1", O_RDONLY) = ENOENT
# open("/lib/modules/4.19.0+1/build/vmlinux", O_RDONLY) = 3 <= BTF file is ignored
# open("/usr/lib/debug/lib/modules/4.19.0+1/vmlinux", O_RDONLY) = 3
# Using /usr/lib/debug/lib/modules/4.19.0+1/vmlinux for symbols (file from kernel-debuginfo)
# Open Debuginfo file: /usr/lib/debug/lib/modules/4.19.0+1/vmlinux

# # Thus, we can install it here (/lib/.../build is an absolute symlink to this path)
# install -m 644 vmlinux.btf %{buildroot}/usr/src/kernels/%{uname}-%{_arch}/vmlinux

%check
# # Check that the .BTF section is present at the start of the file:
# objdump -h %{buildroot}/usr/src/kernels/%{uname}-%{_arch}/vmlinux|grep " 0 .BTF"

%post
> %{_localstatedir}/lib/rpm-state/regenerate-initrd-%{uname}

depmod -ae -F /boot/System.map-%{uname} %{uname}

mkdir -p %{_rundir}/reboot-required.d/%{name}
> %{_rundir}/reboot-required.d/%{name}/%{version}-%{release}

%posttrans
depmod -ae -F /boot/System.map-%{uname} %{uname}

if [ -e %{_localstatedir}/lib/rpm-state/regenerate-initrd-%{uname} ]; then
    rm %{_localstatedir}/lib/rpm-state/regenerate-initrd-%{uname}
    dracut -f /boot/initrd-%{uname}.img %{uname}
fi

%files
/boot/vmlinuz-%{uname}
/boot/vmlinuz-%{short_uname}-xen
/boot/initrd-%{short_uname}-xen.img
%ghost /boot/initrd-%{uname}.img
/boot/System.map-%{uname}
/boot/config-%{uname}
%dir /lib/modules/%{uname}
/lib/modules/%{uname}/extra
/lib/modules/%{uname}/kernel
/lib/modules/%{uname}/modules.order
/lib/modules/%{uname}/modules.builtin
/lib/modules/%{uname}/updates
/lib/modules/%{uname}/vdso
%exclude /lib/modules/%{uname}/vdso/.build-id
%ghost /lib/modules/%{uname}/modules.alias
%ghost /lib/modules/%{uname}/modules.alias.bin
%ghost /lib/modules/%{uname}/modules.builtin.bin
%ghost /lib/modules/%{uname}/modules.builtin.alias.bin
%ghost /lib/modules/%{uname}/modules.builtin.modinfo
%ghost /lib/modules/%{uname}/modules.dep
%ghost /lib/modules/%{uname}/modules.dep.bin
%ghost /lib/modules/%{uname}/modules.devname
%ghost /lib/modules/%{uname}/modules.softdep
%ghost /lib/modules/%{uname}/modules.symbols
%ghost /lib/modules/%{uname}/modules.symbols.bin
%doc COPYING
%doc LICENSES/preferred/GPL-2.0
%doc LICENSES/exceptions/Linux-syscall-note
%doc Documentation/process/license-rules.rst

%files headers
/usr/include/*

%files devel
/lib/modules/%{uname}/build
/lib/modules/%{uname}/source
%verify(not mtime) /usr/src/kernels/%{uname}-%{_arch}
%{_rpmconfigdir}/macros.d/macros.kernel

%files -n perf
%{_bindir}/perf
%{_libexecdir}/perf-core
%{_datadir}/perf-core/
%{_mandir}/man[1-8]/perf*
%{_sysconfdir}/bash_completion.d/perf
%doc tools/perf/Documentation/examples.txt
%license COPYING

%files -n python3-perf
%license COPYING
%{python3_sitearch}/*

%files lp-devel_%{version}_%{release}
%{lp_devel_dir}

%{?_cov_results_package}

%changelog
* Wed Jan 21 2026 Yann Dirson <yann.dirson@vates.tech> - 6.12.66-0.ydi.1
- Test-switch to linux-stable
- Removed patches, XS- and RHELkernel-specificities
- Switch to python3
- Disable LTO for building perf (link error)
- Disable BTF usage (TODO: determine what would be needed)
- Use patchlevel in utsname version (not .0) to match upstream
- Add patch to workaround brp-mangle-shebangs from rejecting "python" as
  interpreter
- WIP Disable installation of debug vmlinux

* Thu Jan 15 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.19-8.0.44.1
- Sync with 4.19.19-8.0.44
- *** Upstream changelog ***
  * Fri Oct 31 2025 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.44
  - CA-399062: NFS timeout causes potential deadlock
  - CA-419803 / CA-419762: Backport patches to fix NBD disconnect crash

* Tue Sep 09 2025 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.43.1
- Sync with 4.19.19-8.0.43
- *** Upstream changelog ***
 * Fri Jul 18 2025 Gerald Elder-Vass <gerald.elder-vass@cloud.com> - 4.19.19-8.0.43
 - CA-412882: Register NVMe ns_id attribute(s) as default sysfs groups
 - CA-360450: Fix deadlock on PCI passthrough

* Fri Aug 01 2025 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.42.1
- Sync with 4.19.19-8.0.42
- *** Upstream changelog ***
  * Mon Apr 07 2025 Gerald Elder-Vass <gerald.elder-vass@cloud.com> - 4.19.19-8.0.42
  - XSI-1728: Avoid repeatedly emitting uevents for LUN changes on CHECK_CONDITION
  * Tue Feb 18 2025 Kevin Lampis <klampis@cloud.com> - 4.19.19-8.0.41
  - CP-51825: Add 50G/100G/200G ethtool link modes
  * Tue Feb 18 2025 Kevin Lampis <klampis@cloud.com> - 4.19.19-8.0.40
  - None
  * Thu Jan 09 2025 Gerald Elder-Vass <gerald.elder-vass@citrix.com> - 4.19.19-8.0.39
  - CA-401809: Resolve incorrect coverity warning
  - CA-404447: Improve logging for xhci failures

* Wed Jul 30 2025 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.38.4
- Backport patch for CVE-2020-28374 (scsi: target: Fix XCOPY NAA identifier lookup)

* Mon Jun 23 2025 Teddy Astie <teddy.astie@vates.tech> - 4.19.19-8.0.38.3
- Backport ACPI NULL dereference fix (Minisforum MS-A2 - Ryzen 9 7945HX kernel panic)

* Sun Apr 06 2025 Anthoine Bourgeois <anthoine.bourgeois@vates.tech> - 4.19.19-8.0.38.2
- Backport perf dynamic tracepoints fixes

* Fri Mar 28 2025 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-8.0.38.1
- Sync with 4.19.19-8.0.38
- *** Upstream changelog ***
  * Thu Dec 05 2024 Gerald Elder-Vass <gerald.elder-vass@citrix.com> - 4.19.19-8.0.38
  - CA-401809: DLM failure leaves system unstable fixes
  - CP-49678: Reduce Xen timer tick

* Mon Oct 07 2024 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.37.1
- Sync with 4.19.19-8.0.37
- *** Upstream changelog ***
- * Thu Aug 08 2024 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.37
- - CA-365333: Fix initrd decompression bug
- - CA-395816: Enable config option to fix incorrect firmware fan control

* Mon Aug 12 2024 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-8.0.36.1
- Sync with 4.19.19-8.0.36
- *** Upstream changelog ***
- * Mon Jul 15 2024 Fouad Hilly <fouad.hilly@cloud.com> - 4.19.19-8.0.36
- - New tag due to a wrong build for 4.19.19-8.0.35
- * Wed Jul 10 2024 Fouad Hilly <fouad.hilly@cloud.com> - 4.19.19-8.0.35
- - CA-394994  backport fix agaw for a supported 48 bit guest address width
- - Make sure the kernel configuration is up to date
- - CP-40289: kernel-devel: Add a BPF Type Format (BTF) info file for libbpf
- - CP-48280: Disable Intel Powerclamp driver

* Mon Jun 24 2024 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.34.2
- Backport tg3 driver code from kernel 4.19.315

* Tue Jun 18 2024 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-8.0.34.1
- Sync with 4.19.19-8.0.34
- *** Upstream changelog ***
- * Thu Feb 29 2024 Chunjie Zhu <chunjie.zhu@cloud.com> - 4.19.19-8.0.34
- - CA-387199: Fix for XSI-1566

* Thu Jun 06 2024 Petr Bena <benapetr@gmail.com> - 4.19.19-8.0.33.2
- Integrated ceph code from kernel 4.19.295

* Tue Apr 09 2024 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-8.0.33.1
- Sync with 4.19.19-8.0.33
- *** Upstream changelog ***
- * Thu Jan 11 2024 Alejandro Vallejo <alejandro.vallejo@cloud.com> - 4.19.19-8.0.33
- - CA-387401: Fix for XSA-448

* Mon Jan 22 2024 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-8.0.32.1
- Update to 4.19.19-8.0.32
- *** Upstream changelog ***
- * Wed Oct 18 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.32
- - CA-384066: fix netback vifs queue length
- - Declare setup and dependencies for building live patches
- * Fri Sep 29 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.31
- - CA-383077 / XSI-1502: Backport SUNRPC-Always-drop-the-XPRT_LOCK-on-XPRT_CLOSE_WAIT
- - CA-383484: Backport fix for XSA-441
- * Thu Sep 07 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.30
- - CA-381221: Make NFS timeouts more consistent

* Fri Dec 15 2023 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.29.2
- Disable i40iw driver in kernel config

* Fri Sep 15 2023 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-8.0.29.1
- Update to 4.19.19-8.0.29
- *** Upstream changelog ***
- * Fri Aug 11 2023 Stephen Cheng <stephen.cheng@citrix.com> - 4.19.19-8.0.29
- - CP-41018: Backport auxiliary bus support
- * Wed Aug 09 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.28
- - CP-43107: backport NVMe/FC patches
- * Mon Jul 31 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.27
- - CA-379289: Add a fix for XSA-432
- * Thu Apr 13 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.26
- - CA-371727: Fix evaluation of _PDC ACPI method on dom0
- - CA-376418: Backport fixes to XSA-423
- * Thu Mar 16 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.25
- - CP-42067: add an ELFNOTE about PV-IOMMU support
- * Mon Mar 06 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.24
- - CA-375558: Fix nbd ref counting bug
- - CA-375244: Ensure DLM reconnects after network outage
- * Mon Feb 13 2023 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.23
- - CP-41370: Remove Citrix logo
- - Strip stale config.ini metadata

* Tue Dec 20 2022 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-8.0.22.1
- Update to 4.19.19-8.0.22
- *** Upstream changelog ***
- * Fri Dec 09 2022 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.22
- - Fix booting PVH dom0 with UEFI
- - Fix nvmefc-boot-connections.service.
- - CA-364458 / XSA-396: PV frontends vulnerable to attack by backends
- - CA-368126 / XSA-403: Linux disk/nic frontends data leaks
- - CA-369758 / XSA-423: Guest triggerable NIC reset/abort/crash via netback
- - CA-373544 / XSA-424: Guests can trigger deadlock in netback

* Wed Aug 31 2022 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-8.0.21.1
- Rebase on CH 8.Cloud Preview (8.3)

* Fri Apr 29 2022 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.21
- CA-366138: Backport a patch to fix a CIFS oops
- CA-366517: Fix Linux's ability to use 64bit linear framebuffers

* Mon Feb 14 2022 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.20
- CP-38416: Enable static analysis

* Thu Nov 25 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.19
- CP-38516: Create a subpackage for building live patches

* Wed Sep 29 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.18
- CA-359097: Support crashing on RKL+ CPUs with 8254 clock gating

* Tue Sep 14 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.17
- CA-358059: CVE-2021-3600: bpf: Fix 32 bit src register truncation on div/mod
- CA-358056: CVE-2021-3444: bpf: Fix truncation handling for mod32 dst reg wrt zero

* Wed Aug 18 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.16
- CP-37340: Clarify licensing and conform to Fedora packaging guidelines
- CA-357418: Fix race in set_evtchn_to_irq

* Tue Aug 10 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.15
- CA-356822: CVE-2021-33909: size_t-to-int vulnerability in Linux's filesystem layer

* Mon Jul 05 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.14
- CA-354789: Backport upstream patch to fix warning in evtchn_interrupt()

* Fri Jun 04 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.13
- CA-355291: Fix affinity setting for xen-dyn-lateeoi IRQs

* Thu May 27 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.12
- CA-353093: CVE-2021-29154: Validate computation of branch displacements for x86

* Thu Apr 15 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.11
- CA-353048: Add new paravirt function for ioperm() syscall support
- CA-352473: XSA-367: Linux: netback fails to honor grant mapping errors
- CA-352682: XSA-371: Linux: blkback driver may leak persistent grants

* Tue Mar 23 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.10
- CA-349120: Backport patches to fix spurious event-related warnings

* Thu Feb 25 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.9
- CA-351672: XSA-361: Linux: grant mapping error handling issues
- CA-351671: XSA-362: Linux: backends treating grant mapping errors as bug
- CA-351723: XSA-365: Linux: error handling issues in blkback's grant mapping

* Fri Feb 19 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.8
- Backport XENMEM_acquire_resource size fix
- CA-351820: Build perf with libunwind instead of elfutils libdw
- import-patch-from-git.py: use -C instead of --work-tree
- CA-351597: Fix use-after-free in xen-netback caused by XSA-332

* Thu Jan 28 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.7
- CA-343009: Fix xenbus request races

* Mon Jan 18 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.6
- import-patch-from-git.py: fixup the path for Koji world
- CA-349623: XSA-349 - Frontends can trigger OOM in Backends by update a watched path
- CA-349624: XSA-350 - Use after free triggered by block frontend in Linux blkback

* Mon Nov 30 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.5
- Replace local patch with backport
- CP-35517: Move package to koji
- CP-35517: Fix version information after koji migration

* Tue Nov 03 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.4
- CA-346372, CA-346374: Backport fixes for XSA-331, XSA-332

* Tue Oct 06 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.3
- CP-33978: Update Citrix logo in kernel RPM to 2020 version

* Wed Jul 08 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.2
- Replace local patch with upstream backport
- Put patches into their respective section and fix the build

* Thu Jun 25 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.1
- CA-341597: Revert NR_CPUS to 64 and increase the scaling factor

* Wed Jun 24 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-8.0.0
- CA-341597: Increase NR_CPUS to 512

* Tue May 12 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.7
- CA-339209: Stop building Intel ME drivers and remove MEI from kABI
- CP-31860: Backport GFS2 & DLM modules from v5.7-rc2
- CP-31860: gfs2: Add some v5.7 for-rc5 patches
- CA-338613: Fix busy wait in DLM

* Thu Apr 30 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.6
- CA-337406: Disable EFI pstore backend by default
- CA-338183: Optimize get_random_u{32,64} by removing calls to RDRAND
- CA-308055: Fix an iSCSI use-after-free

* Mon Apr 20 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.5
- CA-337460 - Allow commit lists to be imported chronologically.
- Replace patch with upstream backport

* Thu Mar 26 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.4
- CA-335089, CP-33195: Move PV-IOMMU 1-1 map initialization to Xen
- Restore PV-IOMMU kABI
- CA-337060: Restore best effort unmaps to avoid clashes with reserved regions

* Mon Mar 09 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.3
- CA-334001: Revert upstream fix for CA-306398 since it's not complete
- CA-332618: Fix several FCoE memory leaks
- Replace i915 patches with backports
- CA-335769: xen-netback: Handle unexpected map grant ref return value

* Fri Feb 21 2020 Steven Woods <steven.woods@citrix.com> - 4.19.19-7.0.2
- CP33120: Add Coverity build macros

* Thu Jan 23 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.1
- CA-333532: Fix patch context
- CA-332867: Fix i915 late loading failure due to memory fragmentation

* Wed Jan 08 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.0
- Replace paches with backports and some clean up
- CA-332663: Fix TDR while using latest Intel guest driver with GVT-g
- Remove XenGT symbols from kABI
- CA-332782: backport fixes for blkdiscard bugs

* Thu Nov 28 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.9
- CA-330853: Fix memory corruption on BPDU processing

* Thu Oct 24 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.8
- CP-28248: Build PV frontends inside the kernel image

* Thu Sep 26 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.7
- CA-326847: Fixes for checksum calculation in mlx drivers
- Enable PVH support in Dom0 kernel
- CA-325955: Fix SR-IOV VF init if MCFG is not reserved in E820
- Extend DRM_I915_GEM_VGTBUFFER support to more architectures
- CA-327274: x86/efi: Don't require non-blocking EFI callbacks

* Fri Aug 23 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.6
- CA-325320: Disable the pcc_cpufreq module

* Mon Aug 12 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.5
- CA-320186: Make bnx2fc setup FCoE reliably
- CA-324731: xen/netback: Reset nr_frags before freeing skb
- Backport some GFS2 fixes
- Backport patches from upstream

* Wed Jun 26 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.4
- CA-322114: Fix TCP SACK/MSS vulnerabilites - CVE-2019-1147[7-9]
- CA-322114: Backport follow-up patch for CVE-2019-11478

* Wed Jun 19 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.3
- CA-320089: Fix issues from GFS2 backports
- CA-319469: Avoid amd64_edac_mod loading failures on AMD EPYC machines
- CA-315930: xfs: Avoid deadlock when backed by tapdisk
- Replace a patch with an upstream backport

* Mon Jun 10 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.2
- CA-320214: Mitigate OVMF triple-fault due to GVT-g BAR mapping timeout

* Tue May 28 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.1
- Replace some local GFS2 patches with backports
- gfs2: Restore kABI changes

* Fri Apr 12 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.0
- Replace patches with backports
- CA-314807: Fix buffer overflow in privcmd ioctl

* Fri Mar 22 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-5.0.8
- CA-309637: gfs2: Take log_flush lock during recovery

* Wed Mar 20 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-5.0.7
- CA-310966: gfs2: Avoid deadlocking in gfs2_log_flush

* Mon Mar 18 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-5.0.6
- CA-312608: blktap2: Don't change the elevator

* Mon Mar 11 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-5.0.5
- CA-312266: fix missed wakeups in GFS2
- Replace patches with backports

* Thu Mar 07 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-5.0.4
- CP-30827: Set ABI version to 1 and turn on kABI checking
- CA-310995: Disable hung task warnings for the idle IO scheduling class
- CA-311463: Fix occasional leak of grant ref mappings under memory pressure

* Wed Feb 27 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-5.0.3
- CA-311278: Fix skbuff_head_cache corruption in IPv4 fragmentation
- CA-311302: Backport a fix for CVE-2019-8912
- CA-310396: blktap2: Fix setting the elevator to noop

* Tue Feb 19 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-5.0.2
- CA-310859: Only use pfn_to_bfn if PV-IOMMU is not in operation
- CP-30503: Switch accepted into 4.19+ local patches to backports in the patchqueue

* Thu Feb 14 2019 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-5.0.1
- Misc bugfixes

* Tue Oct 30 2018 Jennifer Herbert <jennifer.herbert@citrix.com> - 4.19
- Update kernel to 4.19

* Fri Sep 28 2018 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.4.52-4.1.0
- CA-296112: Mitigate against CVE-2018-5391
- Add GFS2 resource group skippiness patch
- GFS2: avoid recently demoted resource groups

* Fri Aug 10 2018 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-4.0.12
- CA-295418: Fix initially incorrect GVT-g patch forwardport

* Fri Aug 03 2018 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-4.0.11
- Add XSA-274 patch
- Backport L1TF mitigations from v4.18
- CA-295106: Add xsa270.patch

* Fri Jul 27 2018 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.4.52-4.0.10
- CA-288640: Silence xen_watchdog spam
- CA-290024: add sysfs node to allow toolstack to wait
- CA-294295: Fix Intel CQM when running under Xen
- CA-287658: Fix iscsi_complete_task() race

* Wed May 30 2018 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-4.0.9
- Backport CIFS: Reconnect expired SMB sessions (partial)
- CIFS: Handle STATUS_USER_SESSION_DELETED

* Tue May 15 2018 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-4.0.8
- Backport DLM changes from 4.16
- Backport GFS2 from 4.15

* Mon Apr 16 2018 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-4.0.7
- CA-287508: Fix for skb_warn_bad_offload()

* Mon Apr 09 2018 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-4.0.6
- CA-286864: Fixup blktap blkdevice's elevator to noop

* Wed Mar 28 2018 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.4.52-4.0.4
- CA-277853: Reduce skb_warn_bad_offload noise.
- CA-286713: scsi: devinfo: Add Microsoft iSCSI target to 1024 sector blacklist
- CA-286719: Fixup locking in __iscsi_conn_send_pdu
- CP-26829: Use DMOP rather than HVMOP

* Thu Feb 01 2018 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-4.0.3
- Bump DOMCTL interface version for Xen 4.11
- CP-26571: Backport GFS2 from v4.14.12
- CP-26571: Backport DLM from v4.14.12

* Wed Jan 10 2018 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-4.0.2
- CA-275523: Use the correct firmware for bfa

* Thu Dec 07 2017 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.4.52-4.0.1
- CA-273824: Print name of delayed work, to debug a crash
- CA-273693: Fix retrieving information using scsi_id
- CA-275730: Fix partial gntdev_mmap() cleanup

* Tue Nov 07 2017 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-3.1.9
- CA-269705: [cifs] fix echo infinite loop when session needs reconnect
- CA-270775: Backport, gntdev out of bounds access avoidance, patch

* Mon Oct 23 2017 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-3.1.8
- CA-270432: Backport a fix for a deadlock in libfc

* Mon Oct 16 2017 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-3.1.7
- CA-265082 Disabling DM-MQ as it is not production ready in 4.4 kernel
- CA-268107: Fix various races in ipset

* Tue Sep 05 2017 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-3.1.6
- Remove kernel.spec
- CA-255214: Do not scrub ignore_df for tunnels
- CA-255214: Enable fragemention of GRE packets
- CA-261981: Backport fix for iSCSI crash

* Tue Aug 22 2017 Simon Rowe <simon.rowe@citrix.com> - 4.4.52-3.1.5
- CA-261171: XSA-229 - Fix Xen block IO merge-ability calculation

* Wed May 17 2017 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.4.52-3.1
- Rewrote spec file.
