# All Global changes to build and install go here.
# Per the below section about __spec_install_pre, any rpm
# environment changes that affect %%install need to go
# here before the %%install macro is pre-built.

# Disable frame pointers
%undefine _include_frame_pointers

# Disable LTO in userspace packages.
%global _lto_cflags %{nil}

# Option to enable compiling with clang instead of gcc.
%bcond_with toolchain_clang

%if %{with toolchain_clang}
%global toolchain clang
%endif

# Compile the kernel with LTO (only supported when building with clang).
%bcond_with clang_lto

%if %{with clang_lto} && %{without toolchain_clang}
{error:clang_lto requires --with toolchain_clang}
%endif

# RPM macros strip everything in BUILDROOT, either with __strip
# or find-debuginfo.sh. Make use of __spec_install_post override
# and save/restore binaries we want to package as unstripped.
%define buildroot_unstripped %{_builddir}/root_unstripped
%define buildroot_save_unstripped() \
(cd %{buildroot}; cp -rav --parents -t %{buildroot_unstripped}/ %1 || true) \
%{nil}
%define __restore_unstripped_root_post \
    echo "Restoring unstripped artefacts %{buildroot_unstripped} -> %{buildroot}" \
    cp -rav %{buildroot_unstripped}/. %{buildroot}/ \
%{nil}

# The kernel's %%install section is special
# Normally the %%install section starts by cleaning up the BUILD_ROOT
# like so:
#
# %%__spec_install_pre %%{___build_pre}\
#     [ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "${RPM_BUILD_ROOT}"\
#     mkdir -p `dirname "$RPM_BUILD_ROOT"`\
#     mkdir "$RPM_BUILD_ROOT"\
# %%{nil}
#
# But because of kernel variants, the %%build section, specifically
# BuildKernel(), moves each variant to its final destination as the
# variant is built.  This violates the expectation of the %%install
# section.  As a result we snapshot the current env variables and
# purposely leave out the removal section.  All global wide changes
# should be added above this line otherwise the %%install section
# will not see them.
%global __spec_install_pre %{___build_pre}

# Replace '-' with '_' where needed so that variants can use '-' in
# their name.
%define uname_suffix() %{lua:
	local flavour = rpm.expand('%{?1:+%{1}}')
	flavour = flavour:gsub('-', '_')
	if flavour ~= '' then
		print(flavour)
	end
}

# This returns the main kernel tied to a debug variant. For example,
# kernel-debug is the debug version of kernel, so we return an empty
# string. However, kernel-64k-debug is the debug version of kernel-64k,
# in this case we need to return "64k", and so on. This is used in
# macros below where we need this for some uname based requires.
%define uname_variant() %{lua:
	local flavour = rpm.expand('%{?1:%{1}}')
	_, _, main, sub = flavour:find("(%w+)-(.*)")
	if main then
		print("+" .. main)
	end
}


# At the time of this writing (2019-03), RHEL8 packages use w2.xzdio
# compression for rpms (xz, level 2).
# Kernel has several large (hundreds of mbytes) rpms, they take ~5 mins
# to compress by single-threaded xz. Switch to threaded compression,
# and from level 2 to 3 to keep compressed sizes close to "w2" results.
#
# NB: if default compression in /usr/lib/rpm/redhat/macros ever changes,
# this one might need tweaking (e.g. if default changes to w3.xzdio,
# change below to w4T.xzdio):
#
# This is disabled on i686 as it triggers oom errors

%ifnarch i686
%define _binary_payload w3T.xzdio
%endif

Summary: The Linux kernel
%if 0%{?fedora}
%define secure_boot_arch x86_64
%else
%define secure_boot_arch x86_64 aarch64 s390x ppc64le
%endif

# Signing for secure boot authentication
%ifarch %{secure_boot_arch}
%global signkernel 1
%else
%global signkernel 0
%endif

# Sign modules on all arches
%global signmodules 1

# Compress modules only for architectures that build modules
%ifarch noarch
%global zipmodules 0
%else
%global zipmodules 1
%endif

# Default compression algorithm
%global compression xz
%global compression_flags --compress
%global compext xz
%if %{zipmodules}
%global zipsed -e 's/\.ko$/\.ko.%compext/'
%endif

%if 0%{?fedora}
%define primary_target fedora
%else
%define primary_target rhel
%endif

#
# genspec.sh variables
#

# kernel package name
%global package_name kernel
%global gemini 0
# Include Fedora files
%global include_fedora 0
# Include RHEL files
%global include_rhel 1
# Include RT files
%global include_rt 1
# Provide Patchlist.changelog file
%global patchlist_changelog 0
# Set released_kernel to 1 when the upstream source tarball contains a
#  kernel release. (This includes prepatch or "rc" releases.)
# Set released_kernel to 0 when the upstream source tarball contains an
#  unreleased kernel development snapshot.
%global released_kernel 0
# Set debugbuildsenabled to 1 to build separate base and debug kernels
#  (on supported architectures). The kernel-debug-* subpackages will
#  contain the debug kernel.
# Set debugbuildsenabled to 0 to not build a separate debug kernel, but
#  to build the base kernel using the debug configuration. (Specifying
#  the --with-release option overrides this setting.)
%define debugbuildsenabled 1
# define buildid .local
%define specrpmversion 6.11.0
%define specversion 6.11.0
%define patchversion 6.11
%define pkgrelease 0.rc6.23
%define kversion 6
%define tarfile_release 6.11.0-0.rc6.23.el10
# This is needed to do merge window version magic
%define patchlevel 11
# This allows pkg_release to have configurable %%{?dist} tag
%define specrelease 0.rc6.23%{?buildid}%{?dist}
# This defines the kabi tarball version
%define kabiversion 6.11.0-0.rc6.23.el10

# If this variable is set to 1, a bpf selftests build failure will cause a
# fatal kernel package build error
%define selftests_must_build 0

#
# End of genspec.sh variables
#

%define pkg_release %{specrelease}

# libexec dir is not used by the linker, so the shared object there
# should not be exported to RPM provides
%global __provides_exclude_from ^%{_libexecdir}/kselftests

# The following build options are (mostly) enabled by default, but may become
# enabled/disabled by later architecture-specific checks.
# Where disabled by default, they can be enabled by using --with <opt> in the
# rpmbuild command, or by forcing these values to 1.
# Where enabled by default, they can be disabled by using --without <opt> in
# the rpmbuild command, or by forcing these values to 0.
#
# standard kernel
%define with_up        %{?_without_up:        0} %{?!_without_up:        1}
# build the base variants
%define with_base      %{?_without_base:      0} %{?!_without_base:      1}
# build also debug variants
%define with_debug     %{?_without_debug:     0} %{?!_without_debug:     1}
# kernel-zfcpdump (s390 specific kernel for zfcpdump)
%define with_zfcpdump  %{?_without_zfcpdump:  0} %{?!_without_zfcpdump:  1}
# kernel-16k (aarch64 kernel with 16K page_size)
%define with_arm64_16k %{?_with_arm64_16k:    1} %{?!_with_arm64_16k:    0}
# kernel-64k (aarch64 kernel with 64K page_size)
%define with_arm64_64k %{?_without_arm64_64k: 0} %{?!_without_arm64_64k: 1}
# kernel-rt (x86_64 and aarch64 only PREEMPT_RT enabled kernel)
%define with_realtime  %{?_without_realtime:  0} %{?!_without_realtime:  1}

# Supported variants
#            with_base with_debug    with_gcov
# up         X         X             X
# zfcpdump   X                       X
# arm64_16k  X         X             X
# arm64_64k  X         X             X
# realtime   X         X             X

# kernel-doc
%define with_doc       %{?_without_doc:       0} %{?!_without_doc:       1}
# kernel-headers
%define with_headers   %{?_without_headers:   0} %{?!_without_headers:   1}
%define with_cross_headers   %{?_without_cross_headers:   0} %{?!_without_cross_headers:   1}
# perf
%define with_perf      %{?_without_perf:      0} %{?!_without_perf:      1}
# libperf
%define with_libperf   %{?_without_libperf:   0} %{?!_without_libperf:   1}
# tools
%define with_tools     %{?_without_tools:     0} %{?!_without_tools:     1}
# bpf tool
%define with_bpftool   %{?_without_bpftool:   0} %{?!_without_bpftool:   1}
# kernel-debuginfo
%define with_debuginfo %{?_without_debuginfo: 0} %{?!_without_debuginfo: 1}
# kernel-abi-stablelists
%define with_kernel_abi_stablelists %{?_without_kernel_abi_stablelists: 0} %{?!_without_kernel_abi_stablelists: 1}
# internal samples and selftests
%define with_selftests %{?_without_selftests: 0} %{?!_without_selftests: 1}
#
# Additional options for user-friendly one-off kernel building:
#
# Only build the base kernel (--with baseonly):
%define with_baseonly  %{?_with_baseonly:     1} %{?!_with_baseonly:     0}
# Only build the debug variants (--with dbgonly):
%define with_dbgonly   %{?_with_dbgonly:      1} %{?!_with_dbgonly:      0}
# Only build the realtime kernel (--with rtonly):
%define with_rtonly    %{?_with_rtonly:       1} %{?!_with_rtonly:       0}
# Control whether we perform a compat. check against published ABI.
%define with_kabichk   %{?_without_kabichk:   0} %{?!_without_kabichk:   1}
# Temporarily disable kabi checks until RC.
%define with_kabichk 0
# Control whether we perform a compat. check against DUP ABI.
%define with_kabidupchk %{?_with_kabidupchk:  1} %{?!_with_kabidupchk:   0}
#
# Control whether to run an extensive DWARF based kABI check.
# Note that this option needs to have baseline setup in SOURCE300.
%define with_kabidwchk %{?_without_kabidwchk: 0} %{?!_without_kabidwchk: 1}
%define with_kabidw_base %{?_with_kabidw_base: 1} %{?!_with_kabidw_base: 0}
#
# Control whether to install the vdso directories.
%define with_vdso_install %{?_without_vdso_install: 0} %{?!_without_vdso_install: 1}
#
# should we do C=1 builds with sparse
%define with_sparse    %{?_with_sparse:       1} %{?!_with_sparse:       0}
#
# Cross compile requested?
%define with_cross    %{?_with_cross:         1} %{?!_with_cross:        0}
#
# build a release kernel on rawhide
%define with_release   %{?_with_release:      1} %{?!_with_release:      0}

# verbose build, i.e. no silent rules and V=1
%define with_verbose %{?_with_verbose:        1} %{?!_with_verbose:      0}

#
# check for mismatched config options
%define with_configchecks %{?_without_configchecks:        0} %{?!_without_configchecks:        1}

#
# gcov support
%define with_gcov %{?_with_gcov:1}%{?!_with_gcov:0}

#
# ipa_clone support
%define with_ipaclones %{?_without_ipaclones: 0} %{?!_without_ipaclones: 1}

# Want to build a vanilla kernel build without any non-upstream patches?
%define with_vanilla %{?_with_vanilla: 1} %{?!_with_vanilla: 0}

# special purpose variants

%ifarch x86_64 aarch64
%define with_efiuki %{?_without_efiuki: 0} %{?!_without_efiuki: 1}
%else
%define with_efiuki 0
%endif

%if 0%{?fedora}
# Kernel headers are being split out into a separate package
%define with_headers 0
%define with_cross_headers 0
# no ipa_clone for now
%define with_ipaclones 0
# no stablelist
%define with_kernel_abi_stablelists 0
# No realtime fedora variants
%define with_realtime 0
%define with_arm64_64k 0
%endif

%if %{with_verbose}
%define make_opts V=1
%else
%define make_opts -s
%endif

%if %{with toolchain_clang}
%ifarch s390x ppc64le
%global llvm_ias 0
%else
%global llvm_ias 1
%endif
%global clang_make_opts HOSTCC=clang CC=clang LLVM_IAS=%{llvm_ias}
%if %{with clang_lto}
# LLVM=1 enables use of all LLVM tools.
%global clang_make_opts %{clang_make_opts} LLVM=1
%endif
%global make_opts %{make_opts} %{clang_make_opts}
# clang does not support the -fdump-ipa-clones option
%global with_ipaclones 0
%endif

# turn off debug kernel and kabichk for gcov builds
%if %{with_gcov}
%define with_debug 0
%define with_kabichk 0
%define with_kabidupchk 0
%define with_kabidwchk 0
%define with_kabidw_base 0
%define with_kernel_abi_stablelists 0
%endif

# turn off kABI DWARF-based check if we're generating the base dataset
%if %{with_kabidw_base}
%define with_kabidwchk 0
%endif

# kpatch_kcflags are extra compiler flags applied to base kernel
# -fdump-ipa-clones is enabled only for base kernels on selected arches
%if %{with_ipaclones}
%ifarch x86_64 ppc64le
%define kpatch_kcflags -fdump-ipa-clones
%else
%define with_ipaclones 0
%endif
%endif

%define make_target bzImage
%define image_install_path boot

%define KVERREL %{specversion}-%{release}.%{_target_cpu}
%define KVERREL_RE %(echo %KVERREL | sed 's/+/[+]/g')
%define hdrarch %_target_cpu
%define asmarch %_target_cpu

%if 0%{!?nopatches:1}
%define nopatches 0
%endif

%if %{with_vanilla}
%define nopatches 1
%endif

%if %{with_release}
%define debugbuildsenabled 1
%endif

%if !%{with_debuginfo}
%define _enable_debug_packages 0
%endif
%define debuginfodir /usr/lib/debug
# Needed because we override almost everything involving build-ids
# and debuginfo generation. Currently we rely on the old alldebug setting.
%global _build_id_links alldebug

# if requested, only build base kernel
%if %{with_baseonly}
%define with_debug 0
%define with_realtime 0
%define with_vdso_install 0
%define with_perf 0
%define with_libperf 0
%define with_tools 0
%define with_bpftool 0
%define with_kernel_abi_stablelists 0
%define with_selftests 0
%define with_ipaclones 0
%endif

# if requested, only build debug kernel
%if %{with_dbgonly}
%define with_base 0
%define with_vdso_install 0
%define with_perf 0
%define with_libperf 0
%define with_tools 0
%define with_bpftool 0
%define with_kernel_abi_stablelists 0
%define with_selftests 0
%define with_ipaclones 0
%endif

# if requested, only build realtime kernel
%if %{with_rtonly}
%define with_realtime 1
%define with_up 0
%define with_debug 0
%define with_debuginfo 0
%define with_vdso_install 0
%define with_perf 0
%define with_libperf 0
%define with_tools 0
%define with_bpftool 0
%define with_kernel_abi_stablelists 0
%define with_selftests 0
%define with_ipaclones 0
%define with_headers 0
%define with_efiuki 0
%define with_zfcpdump 0
%define with_arm64_16k 0
%define with_arm64_64k 0
%endif

# RT kernel is only built on x86_64 and aarch64
%ifnarch x86_64 aarch64
%define with_realtime 0
%endif

# turn off kABI DUP check and DWARF-based check if kABI check is disabled
%if !%{with_kabichk}
%define with_kabidupchk 0
%define with_kabidwchk 0
%endif

%if %{with_vdso_install}
%define use_vdso 1
%endif

# selftests require bpftool to be built.  If bpftools is disabled, then disable selftests
%if %{with_bpftool} == 0
%define with_selftests 0
%endif

%ifnarch noarch
%define with_kernel_abi_stablelists 0
%endif

# Overrides for generic default options

# only package docs noarch
%ifnarch noarch
%define with_doc 0
%define doc_build_fail true
%endif

%if 0%{?fedora}
# don't do debug builds on anything but aarch64 and x86_64
%ifnarch aarch64 x86_64
%define with_debug 0
%endif
%endif

%define all_configs %{name}-%{specrpmversion}-*.config

# don't build noarch kernels or headers (duh)
%ifarch noarch
%define with_up 0
%define with_realtime 0
%define with_headers 0
%define with_cross_headers 0
%define with_tools 0
%define with_perf 0
%define with_libperf 0
%define with_bpftool 0
%define with_selftests 0
%define with_debug 0
%endif

# sparse blows up on ppc
%ifnarch ppc64le
%define with_sparse 0
%endif

# zfcpdump mechanism is s390 only
%ifnarch s390x
%define with_zfcpdump 0
%endif

# 16k and 64k variants only for aarch64
%ifnarch aarch64
%define with_arm64_16k 0
%define with_arm64_64k 0
%endif

%if 0%{?fedora}
# This is not for Fedora
%define with_zfcpdump 0
%endif

# Per-arch tweaks

%ifarch i686
%define asmarch x86
%define hdrarch i386
%define kernel_image arch/x86/boot/bzImage
%endif

%ifarch x86_64
%define asmarch x86
%define kernel_image arch/x86/boot/bzImage
%endif

%ifarch ppc64le
%define asmarch powerpc
%define hdrarch powerpc
%define make_target vmlinux
%define kernel_image vmlinux
%define kernel_image_elf 1
%define use_vdso 0
%endif

%ifarch s390x
%define asmarch s390
%define hdrarch s390
%define kernel_image arch/s390/boot/bzImage
%define vmlinux_decompressor arch/s390/boot/vmlinux
%endif

%ifarch aarch64
%define asmarch arm64
%define hdrarch arm64
%define make_target vmlinuz.efi
%define kernel_image arch/arm64/boot/vmlinuz.efi
%endif

# Should make listnewconfig fail if there's config options
# printed out?
%if %{nopatches}
%define with_configchecks 0
%endif

# To temporarily exclude an architecture from being built, add it to
# %%nobuildarches. Do _NOT_ use the ExclusiveArch: line, because if we
# don't build kernel-headers then the new build system will no longer let
# us use the previous build of that package -- it'll just be completely AWOL.
# Which is a BadThing(tm).

# We only build kernel-headers on the following...
%if 0%{?fedora}
%define nobuildarches i386
%else
%define nobuildarches i386 i686
%endif

%ifarch %nobuildarches
# disable BuildKernel commands
%define with_up 0
%define with_debug 0
%define with_zfcpdump 0
%define with_arm64_16k 0
%define with_arm64_64k 0
%define with_realtime 0

%define with_debuginfo 0
%define with_perf 0
%define with_libperf 0
%define with_tools 0
%define with_bpftool 0
%define with_selftests 0
%define _enable_debug_packages 0
%endif

# Architectures we build tools/cpupower on
%if 0%{?fedora}
%define cpupowerarchs %{ix86} x86_64 ppc64le aarch64
%else
%define cpupowerarchs i686 x86_64 ppc64le aarch64
%endif

# Architectures we build kernel livepatching selftests on
%define klptestarches x86_64 ppc64le s390x

%if 0%{?use_vdso}
%define _use_vdso 1
%else
%define _use_vdso 0
%endif

# If build of debug packages is disabled, we need to know if we want to create
# meta debug packages or not, after we define with_debug for all specific cases
# above. So this must be at the end here, after all cases of with_debug or not.
%define with_debug_meta 0
%if !%{debugbuildsenabled}
%if %{with_debug}
%define with_debug_meta 1
%endif
%define with_debug 0
%endif

# short-hand for "are we building base/non-debug variants of ...?"
%if %{with_up} && %{with_base}
%define with_up_base 1
%else
%define with_up_base 0
%endif
%if %{with_realtime} && %{with_base}
%define with_realtime_base 1
%else
%define with_realtime_base 0
%endif
%if %{with_arm64_16k} && %{with_base}
%define with_arm64_16k_base 1
%else
%define with_arm64_16k_base 0
%endif
%if %{with_arm64_64k} && %{with_base}
%define with_arm64_64k_base 1
%else
%define with_arm64_64k_base 0
%endif

#
# Packages that need to be installed before the kernel is, because the %%post
# scripts use them.
#
%define kernel_prereq  coreutils, systemd >= 203-2, /usr/bin/kernel-install
%define initrd_prereq  dracut >= 027


Name: %{package_name}
License: ((GPL-2.0-only WITH Linux-syscall-note) OR BSD-2-Clause) AND ((GPL-2.0-only WITH Linux-syscall-note) OR BSD-3-Clause) AND ((GPL-2.0-only WITH Linux-syscall-note) OR CDDL-1.0) AND ((GPL-2.0-only WITH Linux-syscall-note) OR Linux-OpenIB) AND ((GPL-2.0-only WITH Linux-syscall-note) OR MIT) AND ((GPL-2.0-or-later WITH Linux-syscall-note) OR BSD-3-Clause) AND ((GPL-2.0-or-later WITH Linux-syscall-note) OR MIT) AND BSD-2-Clause AND (BSD-2-Clause OR Apache-2.0) AND BSD-3-Clause AND BSD-3-Clause-Clear AND GFDL-1.1-no-invariants-or-later AND GPL-1.0-or-later AND (GPL-1.0-or-later OR BSD-3-Clause) AND (GPL-1.0-or-later WITH Linux-syscall-note) AND GPL-2.0-only AND (GPL-2.0-only OR Apache-2.0) AND (GPL-2.0-only OR BSD-2-Clause) AND (GPL-2.0-only OR BSD-3-Clause) AND (GPL-2.0-only OR CDDL-1.0) AND (GPL-2.0-only OR GFDL-1.1-no-invariants-or-later) AND (GPL-2.0-only OR GFDL-1.2-no-invariants-only) AND (GPL-2.0-only WITH Linux-syscall-note) AND GPL-2.0-or-later AND (GPL-2.0-or-later OR BSD-2-Clause) AND (GPL-2.0-or-later OR BSD-3-Clause) AND (GPL-2.0-or-later OR CC-BY-4.0) AND (GPL-2.0-or-later WITH GCC-exception-2.0) AND (GPL-2.0-or-later WITH Linux-syscall-note) AND ISC AND LGPL-2.0-or-later AND (LGPL-2.0-or-later OR BSD-2-Clause) AND (LGPL-2.0-or-later WITH Linux-syscall-note) AND LGPL-2.1-only AND (LGPL-2.1-only OR BSD-2-Clause) AND (LGPL-2.1-only WITH Linux-syscall-note) AND LGPL-2.1-or-later AND (LGPL-2.1-or-later WITH Linux-syscall-note) AND (Linux-OpenIB OR GPL-2.0-only) AND (Linux-OpenIB OR GPL-2.0-only OR BSD-2-Clause) AND Linux-man-pages-copyleft AND MIT AND (MIT OR Apache-2.0) AND (MIT OR GPL-2.0-only) AND (MIT OR GPL-2.0-or-later) AND (MIT OR LGPL-2.1-only) AND (MPL-1.1 OR GPL-2.0-only) AND (X11 OR GPL-2.0-only) AND (X11 OR GPL-2.0-or-later) AND Zlib AND (copyleft-next-0.3.1 OR GPL-2.0-or-later)
URL: https://www.kernel.org/
Version: %{specrpmversion}
Release: %{pkg_release}
# DO NOT CHANGE THE 'ExclusiveArch' LINE TO TEMPORARILY EXCLUDE AN ARCHITECTURE BUILD.
# SET %%nobuildarches (ABOVE) INSTEAD
%if 0%{?fedora}
ExclusiveArch: noarch x86_64 s390x aarch64 ppc64le
%else
ExclusiveArch: noarch i386 i686 x86_64 s390x aarch64 ppc64le
%endif
ExclusiveOS: Linux
%ifnarch %{nobuildarches}
Requires: kernel-core-uname-r = %{KVERREL}
Requires: kernel-modules-uname-r = %{KVERREL}
Requires: kernel-modules-core-uname-r = %{KVERREL}
Provides: installonlypkg(kernel)
%endif


#
# List the packages used during the kernel build
#
BuildRequires: kmod, bash, coreutils, tar, git-core, which
BuildRequires: bzip2, xz, findutils, m4, perl-interpreter, perl-Carp, perl-devel, perl-generators, make, diffutils, gawk, %compression
BuildRequires: gcc, binutils, redhat-rpm-config, hmaccalc, bison, flex, gcc-c++
BuildRequires: net-tools, hostname, bc, elfutils-devel
BuildRequires: dwarves
BuildRequires: python3
BuildRequires: python3-devel
BuildRequires: python3-pyyaml
BuildRequires: kernel-rpm-macros
# glibc-static is required for a consistent build environment (specifically
# CONFIG_CC_CAN_LINK_STATIC=y).
BuildRequires: glibc-static
%if %{with_headers} || %{with_cross_headers}
BuildRequires: rsync
%endif
%if %{with_doc}
BuildRequires: xmlto, asciidoc, python3-sphinx, python3-sphinx_rtd_theme
%endif
%if %{with_sparse}
BuildRequires: sparse
%endif
%if %{with_perf}
BuildRequires: zlib-devel binutils-devel newt-devel perl(ExtUtils::Embed) bison flex xz-devel
BuildRequires: audit-libs-devel python3-setuptools
BuildRequires: java-devel
BuildRequires: libbpf-devel >= 0.6.0-1
BuildRequires: libbabeltrace-devel
BuildRequires: libtraceevent-devel
%ifnarch s390x
BuildRequires: numactl-devel
%endif
%ifarch aarch64
BuildRequires: opencsd-devel >= 1.0.0
%endif
%endif
%if %{with_tools}
BuildRequires: python3-docutils
BuildRequires: gettext ncurses-devel
BuildRequires: libcap-devel libcap-ng-devel
# The following are rtla requirements
BuildRequires: python3-docutils
BuildRequires: libtraceevent-devel
BuildRequires: libtracefs-devel

%ifnarch s390x
BuildRequires: pciutils-devel
%endif
%ifarch i686 x86_64
BuildRequires: libnl3-devel
%endif
%endif
%if %{with_tools} || %{signmodules} || %{signkernel}
BuildRequires: openssl-devel
%endif
%if %{with_bpftool}
BuildRequires: python3-docutils
BuildRequires: zlib-devel binutils-devel llvm-devel
%endif
%if %{with_selftests}
BuildRequires: clang llvm-devel fuse-devel
%ifarch x86_64
BuildRequires: lld
%endif
BuildRequires: libcap-devel libcap-ng-devel rsync libmnl-devel
BuildRequires: numactl-devel
%endif
BuildConflicts: rhbuildsys(DiskFree) < 500Mb
%if %{with_debuginfo}
BuildRequires: rpm-build, elfutils
BuildConflicts: rpm < 4.13.0.1-19
BuildConflicts: dwarves < 1.13
# Most of these should be enabled after more investigation
%undefine _include_minidebuginfo
%undefine _find_debuginfo_dwz_opts
%undefine _unique_build_ids
%undefine _unique_debug_names
%undefine _unique_debug_srcs
%undefine _debugsource_packages
%undefine _debuginfo_subpackages

# Remove -q option below to provide 'extracting debug info' messages
%global _find_debuginfo_opts -r -q

%global _missing_build_ids_terminate_build 1
%global _no_recompute_build_ids 1
%endif
%if %{with_kabidwchk} || %{with_kabidw_base}
BuildRequires: kabi-dw
%endif

%if %{signkernel}%{signmodules}
BuildRequires: openssl
%if %{signkernel}
# ELN uses Fedora signing process, so exclude
%if 0%{?rhel}%{?centos} && !0%{?eln}
BuildRequires: system-sb-certs
%endif
%ifarch x86_64 aarch64
BuildRequires: nss-tools
BuildRequires: pesign >= 0.10-4
%endif
%endif
%endif

%if %{with_cross}
BuildRequires: binutils-%{_build_arch}-linux-gnu, gcc-%{_build_arch}-linux-gnu
%define cross_opts CROSS_COMPILE=%{_build_arch}-linux-gnu-
%define __strip %{_build_arch}-linux-gnu-strip
%endif

# These below are required to build man pages
%if %{with_perf}
BuildRequires: xmlto
%endif
%if %{with_perf} || %{with_tools}
BuildRequires: asciidoc
%endif

%if %{with toolchain_clang}
BuildRequires: clang
%endif

%if %{with clang_lto}
BuildRequires: llvm
BuildRequires: lld
%endif

%if %{with_efiuki}
BuildRequires: dracut
# For dracut UEFI uki binaries
BuildRequires: binutils
# For the initrd
BuildRequires: lvm2
BuildRequires: systemd-boot-unsigned
# For systemd-stub and systemd-pcrphase
BuildRequires: systemd-udev >= 252-1
# For UKI kernel cmdline addons
BuildRequires: systemd-ukify
# For TPM operations in UKI initramfs
BuildRequires: tpm2-tools
# For UKI sb cert
%if 0%{?rhel}%{?centos} && !0%{?eln}
%if 0%{?centos}
BuildRequires: centos-sb-certs >= 9.0-23
%else
BuildRequires: redhat-sb-certs >= 9.4-0.1
%endif
%endif
%endif

# Because this is the kernel, it's hard to get a single upstream URL
# to represent the base without needing to do a bunch of patching. This
# tarball is generated from a src-git tree. If you want to see the
# exact git commit you can run
#
# xzcat -qq ${TARBALL} | git get-tar-commit-id
Source0: linux-%{tarfile_release}.tar.xz

Source1: Makefile.rhelver
Source2: kernel.changelog

Source10: redhatsecurebootca5.cer
Source13: redhatsecureboot501.cer

%if %{signkernel}
# Name of the packaged file containing signing key
%ifarch ppc64le
%define signing_key_filename kernel-signing-ppc.cer
%endif
%ifarch s390x
%define signing_key_filename kernel-signing-s390.cer
%endif

# Fedora/ELN pesign macro expects to see these cert file names, see:
# https://github.com/rhboot/pesign/blob/main/src/pesign-rpmbuild-helper.in#L216
%if 0%{?fedora}%{?eln}
%define pesign_name_0 redhatsecureboot501
%define secureboot_ca_0 %{SOURCE10}
%define secureboot_key_0 %{SOURCE13}
%endif

# RHEL/centos certs come from system-sb-certs
%if 0%{?rhel} && !0%{?eln}
%define secureboot_ca_0 %{_datadir}/pki/sb-certs/secureboot-ca-%{_arch}.cer
%define secureboot_key_0 %{_datadir}/pki/sb-certs/secureboot-kernel-%{_arch}.cer

%if 0%{?centos}
%define pesign_name_0 centossecureboot201
%else
%ifarch x86_64 aarch64
%define pesign_name_0 redhatsecureboot501
%endif
%ifarch s390x
%define pesign_name_0 redhatsecureboot302
%endif
%ifarch ppc64le
%define pesign_name_0 redhatsecureboot701
%endif
%endif
# rhel && !eln
%endif

# signkernel
%endif

Source20: mod-denylist.sh
Source21: mod-sign.sh
Source22: filtermods.py

%define modsign_cmd %{SOURCE21}

%if 0%{?include_rhel}
Source23: x509.genkey.rhel

Source24: %{name}-aarch64-rhel.config
Source25: %{name}-aarch64-debug-rhel.config

Source27: %{name}-ppc64le-rhel.config
Source28: %{name}-ppc64le-debug-rhel.config
Source29: %{name}-s390x-rhel.config
Source30: %{name}-s390x-debug-rhel.config
Source31: %{name}-s390x-zfcpdump-rhel.config
Source32: %{name}-x86_64-rhel.config
Source33: %{name}-x86_64-debug-rhel.config

Source34: def_variants.yaml.rhel

Source41: x509.genkey.centos
# ARM64 64K page-size kernel config
Source42: %{name}-aarch64-64k-rhel.config
Source43: %{name}-aarch64-64k-debug-rhel.config

%endif

%if 0%{?include_fedora}
Source50: x509.genkey.fedora

Source52: %{name}-aarch64-fedora.config
Source53: %{name}-aarch64-debug-fedora.config
Source54: %{name}-aarch64-16k-fedora.config
Source55: %{name}-aarch64-16k-debug-fedora.config
Source56: %{name}-ppc64le-fedora.config
Source57: %{name}-ppc64le-debug-fedora.config
Source58: %{name}-s390x-fedora.config
Source59: %{name}-s390x-debug-fedora.config
Source60: %{name}-x86_64-fedora.config
Source61: %{name}-x86_64-debug-fedora.config

Source62: def_variants.yaml.fedora
%endif

Source70: partial-kgcov-snip.config
Source71: partial-kgcov-debug-snip.config
Source72: partial-clang-snip.config
Source73: partial-clang-debug-snip.config
Source74: partial-clang_lto-x86_64-snip.config
Source75: partial-clang_lto-x86_64-debug-snip.config
Source76: partial-clang_lto-aarch64-snip.config
Source77: partial-clang_lto-aarch64-debug-snip.config
Source80: generate_all_configs.sh
Source81: process_configs.sh

Source86: dracut-virt.conf

Source87: flavors

Source151: uki_create_addons.py
Source152: uki_addons.json

Source100: rheldup3.x509
Source101: rhelkpatch1.x509
Source102: nvidiagpuoot001.x509
Source103: rhelimaca1.x509
Source104: rhelima.x509
Source105: rhelima_centos.x509
Source106: fedoraimaca.x509

%if 0%{?fedora}%{?eln}
%define ima_ca_cert %{SOURCE106}
%endif

%if 0%{?rhel} && !0%{?eln}
%define ima_ca_cert %{SOURCE103}
# rhel && !eln
%endif

%if 0%{?centos}
%define ima_signing_cert %{SOURCE105}
%else
%define ima_signing_cert %{SOURCE104}
%endif

%define ima_cert_name ima.cer

Source200: check-kabi

Source201: Module.kabi_aarch64
Source202: Module.kabi_ppc64le
Source203: Module.kabi_s390x
Source204: Module.kabi_x86_64

Source210: Module.kabi_dup_aarch64
Source211: Module.kabi_dup_ppc64le
Source212: Module.kabi_dup_s390x
Source213: Module.kabi_dup_x86_64

Source300: kernel-abi-stablelists-%{kabiversion}.tar.xz
Source301: kernel-kabi-dw-%{kabiversion}.tar.xz

%if %{include_rt}
# realtime config files
Source474: %{name}-aarch64-rt-rhel.config
Source475: %{name}-aarch64-rt-debug-rhel.config
Source476: %{name}-x86_64-rt-rhel.config
Source477: %{name}-x86_64-rt-debug-rhel.config
%endif

# Sources for kernel-tools
Source2002: kvm_stat.logrotate

# Some people enjoy building customized kernels from the dist-git in Fedora and
# use this to override configuration options. One day they may all use the
# source tree, but in the mean time we carry this to support the legacy workflow
Source3000: merge.py
Source3001: kernel-local
%if %{patchlist_changelog}
Source3002: Patchlist.changelog
%endif

Source4000: README.rst
Source4001: rpminspect.yaml
Source4002: gating.yaml

## Patches needed for building this package

%if !%{nopatches}

Patch1: patch-%{patchversion}-redhat.patch
%endif

# empty final patch to facilitate testing of kernel patches
Patch999999: linux-kernel-test.patch

# END OF PATCH DEFINITIONS

%description
The kernel meta package

#
# This macro does requires, provides, conflicts, obsoletes for a kernel package.
#	%%kernel_reqprovconf [-o] <subpackage>
# It uses any kernel_<subpackage>_conflicts and kernel_<subpackage>_obsoletes
# macros defined above.
#
%define kernel_reqprovconf(o) \
%if %{-o:0}%{!-o:1}\
Provides: kernel = %{specversion}-%{pkg_release}\
%endif\
Provides: kernel-%{_target_cpu} = %{specrpmversion}-%{pkg_release}%{uname_suffix %{?1:+%{1}}}\
Provides: kernel-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires(pre): %{kernel_prereq}\
Requires(pre): %{initrd_prereq}\
Requires(pre): ((linux-firmware >= 20150904-56.git6ebf5d57) if linux-firmware)\
Recommends: linux-firmware\
Requires(preun): systemd >= 200\
Conflicts: xfsprogs < 4.3.0-1\
Conflicts: xorg-x11-drv-vmmouse < 13.0.99\
%{expand:%%{?kernel%{?1:_%{1}}_conflicts:Conflicts: %%{kernel%{?1:_%{1}}_conflicts}}}\
%{expand:%%{?kernel%{?1:_%{1}}_obsoletes:Obsoletes: %%{kernel%{?1:_%{1}}_obsoletes}}}\
%{expand:%%{?kernel%{?1:_%{1}}_provides:Provides: %%{kernel%{?1:_%{1}}_provides}}}\
# We can't let RPM do the dependencies automatic because it'll then pick up\
# a correct but undesirable perl dependency from the module headers which\
# isn't required for the kernel proper to function\
AutoReq: no\
AutoProv: yes\
%{nil}


%package doc
Summary: Various documentation bits found in the kernel source
Group: Documentation
%description doc
This package contains documentation files from the kernel
source. Various bits of information about the Linux kernel and the
device drivers shipped with it are documented in these files.

You'll want to install this package if you need a reference to the
options that can be passed to Linux kernel modules at load time.


%package headers
Summary: Header files for the Linux kernel for use by glibc
Obsoletes: glibc-kernheaders < 3.0-46
Provides: glibc-kernheaders = 3.0-46
%if 0%{?gemini}
Provides: kernel-headers = %{specversion}-%{release}
Obsoletes: kernel-headers < %{specversion}
%endif
%description headers
Kernel-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
glibc package.

%package cross-headers
Summary: Header files for the Linux kernel for use by cross-glibc
%if 0%{?gemini}
Provides: kernel-cross-headers = %{specversion}-%{release}
Obsoletes: kernel-cross-headers < %{specversion}
%endif
%description cross-headers
Kernel-cross-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
cross-glibc package.

%package debuginfo-common-%{_target_cpu}
Summary: Kernel source files used by %{name}-debuginfo packages
Provides: installonlypkg(kernel)
%description debuginfo-common-%{_target_cpu}
This package is required by %{name}-debuginfo subpackages.
It provides the kernel source files common to all builds.

%if %{with_perf}
%package -n perf
%if 0%{gemini}
Epoch: %{gemini}
%endif
Summary: Performance monitoring for the Linux kernel
Requires: bzip2
%description -n perf
This package contains the perf tool, which enables performance monitoring
of the Linux kernel.

%package -n perf-debuginfo
%if 0%{gemini}
Epoch: %{gemini}
%endif
Summary: Debug information for package perf
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{specrpmversion}-%{release}
AutoReqProv: no
%description -n perf-debuginfo
This package provides debug information for the perf package.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_bindir}/perf(\.debug)?|.*%%{_libexecdir}/perf-core/.*|.*%%{_libdir}/libperf-jvmti.so(\.debug)?|XXX' -o perf-debuginfo.list}

%package -n python3-perf
%if 0%{gemini}
Epoch: %{gemini}
%endif
Summary: Python bindings for apps which will manipulate perf events
%description -n python3-perf
The python3-perf package contains a module that permits applications
written in the Python programming language to use the interface
to manipulate perf events.

%package -n python3-perf-debuginfo
%if 0%{gemini}
Epoch: %{gemini}
%endif
Summary: Debug information for package perf python bindings
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{specrpmversion}-%{release}
AutoReqProv: no
%description -n python3-perf-debuginfo
This package provides debug information for the perf python bindings.

# the python_sitearch macro should already be defined from above
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{python3_sitearch}/perf.*so(\.debug)?|XXX' -o python3-perf-debuginfo.list}

# with_perf
%endif

%if %{with_libperf}
%package -n libperf
Summary: The perf library from kernel source
%description -n libperf
This package contains the kernel source perf library.

%package -n libperf-devel
Summary: Developement files for the perf library from kernel source
Requires: libperf = %{version}-%{release}
%description -n libperf-devel
This package includes libraries and header files needed for development
of applications which use perf library from kernel source.

%package -n libperf-debuginfo
Summary: Debug information for package libperf
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n libperf-debuginfo
This package provides debug information for the libperf package.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_libdir}/libperf.so.*(\.debug)?|XXX' -o libperf-debuginfo.list}
# with_libperf
%endif

%if %{with_tools}
%package -n %{package_name}-tools
Summary: Assortment of tools for the Linux kernel
%ifarch %{cpupowerarchs}
Provides:  cpupowerutils = 1:009-0.6.p1
Obsoletes: cpupowerutils < 1:009-0.6.p1
Provides:  cpufreq-utils = 1:009-0.6.p1
Provides:  cpufrequtils = 1:009-0.6.p1
Obsoletes: cpufreq-utils < 1:009-0.6.p1
Obsoletes: cpufrequtils < 1:009-0.6.p1
Obsoletes: cpuspeed < 1:1.5-16
Requires: %{package_name}-tools-libs = %{specrpmversion}-%{release}
%endif
%define __requires_exclude ^%{_bindir}/python
%description -n %{package_name}-tools
This package contains the tools/ directory from the kernel source
and the supporting documentation.

%package -n %{package_name}-tools-libs
Summary: Libraries for the kernels-tools
%description -n %{package_name}-tools-libs
This package contains the libraries built from the tools/ directory
from the kernel source.

%package -n %{package_name}-tools-libs-devel
Summary: Assortment of tools for the Linux kernel
Requires: %{package_name}-tools = %{version}-%{release}
%ifarch %{cpupowerarchs}
Provides:  cpupowerutils-devel = 1:009-0.6.p1
Obsoletes: cpupowerutils-devel < 1:009-0.6.p1
%endif
Requires: %{package_name}-tools-libs = %{version}-%{release}
Provides: %{package_name}-tools-devel
%description -n %{package_name}-tools-libs-devel
This package contains the development files for the tools/ directory from
the kernel source.

%package -n %{package_name}-tools-debuginfo
Summary: Debug information for package %{package_name}-tools
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n %{package_name}-tools-debuginfo
This package provides debug information for package %{package_name}-tools.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_bindir}/centrino-decode(\.debug)?|.*%%{_bindir}/powernow-k8-decode(\.debug)?|.*%%{_bindir}/cpupower(\.debug)?|.*%%{_libdir}/libcpupower.*|.*%%{_bindir}/turbostat(\.debug)?|.*%%{_bindir}/x86_energy_perf_policy(\.debug)?|.*%%{_bindir}/tmon(\.debug)?|.*%%{_bindir}/lsgpio(\.debug)?|.*%%{_bindir}/gpio-hammer(\.debug)?|.*%%{_bindir}/gpio-event-mon(\.debug)?|.*%%{_bindir}/gpio-watch(\.debug)?|.*%%{_bindir}/iio_event_monitor(\.debug)?|.*%%{_bindir}/iio_generic_buffer(\.debug)?|.*%%{_bindir}/lsiio(\.debug)?|.*%%{_bindir}/intel-speed-select(\.debug)?|.*%%{_bindir}/page_owner_sort(\.debug)?|.*%%{_bindir}/slabinfo(\.debug)?|.*%%{_sbindir}/intel_sdsi(\.debug)?|XXX' -o %{package_name}-tools-debuginfo.list}

%package -n rtla
%if 0%{gemini}
Epoch: %{gemini}
%endif
Summary: Real-Time Linux Analysis tools
Requires: libtraceevent
Requires: libtracefs
%description -n rtla
The rtla meta-tool includes a set of commands that aims to analyze
the real-time properties of Linux. Instead of testing Linux as a black box,
rtla leverages kernel tracing capabilities to provide precise information
about the properties and root causes of unexpected results.

%package -n rv
Summary: RV: Runtime Verification
%description -n rv
Runtime Verification (RV) is a lightweight (yet rigorous) method that
complements classical exhaustive verification techniques (such as model
checking and theorem proving) with a more practical approach for
complex systems.
The rv tool is the interface for a collection of monitors that aim
analysing the logical and timing behavior of Linux.

# with_tools
%endif

%if %{with_bpftool}

%if 0%{?fedora}
# bpftoolverion doesn't bump with stable updates so let's stick with
# upstream kernel version for the package name. We still get correct
# output with bpftool -V.
%define bpftoolversion  %specrpmversion
%else
%define bpftoolversion 7.5.0
%endif

%package -n bpftool
Summary: Inspection and simple manipulation of eBPF programs and maps
Version: %{bpftoolversion}
%description -n bpftool
This package contains the bpftool, which allows inspection and simple
manipulation of eBPF programs and maps.

%package -n bpftool-debuginfo
Summary: Debug information for package bpftool
Version: %{bpftoolversion}
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{specrpmversion}-%{release}
AutoReqProv: no
%description -n bpftool-debuginfo
This package provides debug information for the bpftool package.

%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_sbindir}/bpftool(\.debug)?|XXX' -o bpftool-debuginfo.list}

# Setting "Version:" above overrides the internal {version} macro,
# need to restore it here
%define version %{specrpmversion}

# with_bpftool
%endif

%if %{with_selftests}

%package selftests-internal
Summary: Kernel samples and selftests
Requires: binutils, bpftool, iproute-tc, nmap-ncat, python3, fuse-libs, keyutils
%description selftests-internal
Kernel sample programs and selftests.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_libexecdir}/(ksamples|kselftests)/.*|XXX' -o selftests-debuginfo.list}

%define __requires_exclude ^liburandom_read.so.*$

# with_selftests
%endif

%define kernel_gcov_package() \
%package %{?1:%{1}-}gcov\
Summary: gcov graph and source files for coverage data collection.\
%description %{?1:%{1}-}gcov\
%{?1:%{1}-}gcov includes the gcov graph and source files for gcov coverage collection.\
%{nil}

%package -n %{package_name}-abi-stablelists
Summary: The Red Hat Enterprise Linux kernel ABI symbol stablelists
AutoReqProv: no
%description -n %{package_name}-abi-stablelists
The kABI package contains information pertaining to the Red Hat Enterprise
Linux kernel ABI, including lists of kernel symbols that are needed by
external Linux kernel modules, and a yum plugin to aid enforcement.

%if %{with_kabidw_base}
%package kernel-kabidw-base-internal
Summary: The baseline dataset for kABI verification using DWARF data
Group: System Environment/Kernel
AutoReqProv: no
%description kernel-kabidw-base-internal
The package contains data describing the current ABI of the Red Hat Enterprise
Linux kernel, suitable for the kabi-dw tool.
%endif

#
# This macro creates a kernel-<subpackage>-debuginfo package.
#	%%kernel_debuginfo_package <subpackage>
#
# Explanation of the find_debuginfo_opts: We build multiple kernels (debug,
# rt, 64k etc.) so the regex filters those kernels appropriately. We also
# have to package several binaries as part of kernel-devel but getting
# unique build-ids is tricky for these userspace binaries. We don't really
# care about debugging those so we just filter those out and remove it.
%define kernel_debuginfo_package() \
%package %{?1:%{1}-}debuginfo\
Summary: Debug information for package %{name}%{?1:-%{1}}\
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{specrpmversion}-%{release}\
Provides: %{name}%{?1:-%{1}}-debuginfo-%{_target_cpu} = %{specrpmversion}-%{release}\
Provides: installonlypkg(kernel)\
AutoReqProv: no\
%description %{?1:%{1}-}debuginfo\
This package provides debug information for package %{name}%{?1:-%{1}}.\
This is required to use SystemTap with %{name}%{?1:-%{1}}-%{KVERREL}.\
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} --keep-section '.BTF' -p '.*\/usr\/src\/kernels/.*|XXX' -o ignored-debuginfo.list -p '/.*/%%{KVERREL_RE}%{?1:[+]%{1}}/.*|/.*%%{KVERREL_RE}%{?1:\+%{1}}(\.debug)?' -o debuginfo%{?1}.list}\
%{nil}

#
# This macro creates a kernel-<subpackage>-devel package.
#	%%kernel_devel_package [-m] <subpackage> <pretty-name>
#
%define kernel_devel_package(m) \
%package %{?1:%{1}-}devel\
Summary: Development package for building kernel modules to match the %{?2:%{2} }kernel\
Provides: kernel%{?1:-%{1}}-devel-%{_target_cpu} = %{specrpmversion}-%{release}\
Provides: kernel-devel-%{_target_cpu} = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: kernel-devel-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Provides: installonlypkg(kernel)\
AutoReqProv: no\
Requires(pre): findutils\
Requires: findutils\
Requires: perl-interpreter\
Requires: openssl-devel\
Requires: elfutils-libelf-devel\
Requires: bison\
Requires: flex\
Requires: make\
Requires: gcc\
%if %{-m:1}%{!-m:0}\
Requires: kernel-devel-uname-r = %{KVERREL}%{uname_variant %{?1:%{1}}}\
%endif\
%description %{?1:%{1}-}devel\
This package provides kernel headers and makefiles sufficient to build modules\
against the %{?2:%{2} }kernel package.\
%{nil}

#
# This macro creates an empty kernel-<subpackage>-devel-matched package that
# requires both the core and devel packages locked on the same version.
#	%%kernel_devel_matched_package [-m] <subpackage> <pretty-name>
#
%define kernel_devel_matched_package(m) \
%package %{?1:%{1}-}devel-matched\
Summary: Meta package to install matching core and devel packages for a given %{?2:%{2} }kernel\
Requires: %{package_name}%{?1:-%{1}}-devel = %{specrpmversion}-%{release}\
Requires: %{package_name}%{?1:-%{1}}-core = %{specrpmversion}-%{release}\
%description %{?1:%{1}-}devel-matched\
This meta package is used to install matching core and devel packages for a given %{?2:%{2} }kernel.\
%{nil}

#
# kernel-<variant>-ipaclones-internal package
#
%define kernel_ipaclones_package() \
%package %{?1:%{1}-}ipaclones-internal\
Summary: *.ipa-clones files generated by -fdump-ipa-clones for kernel%{?1:-%{1}}\
Group: System Environment/Kernel\
AutoReqProv: no\
%description %{?1:%{1}-}ipaclones-internal\
This package provides *.ipa-clones files.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-internal package.
#	%%kernel_modules_internal_package <subpackage> <pretty-name>
#
%define kernel_modules_internal_package() \
%package %{?1:%{1}-}modules-internal\
Summary: Extra kernel modules to match the %{?2:%{2} }kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-modules-internal-%{_target_cpu} = %{specrpmversion}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-internal-%{_target_cpu} = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: kernel%{?1:-%{1}}-modules-internal = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-internal-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-internal\
This package provides kernel modules for the %{?2:%{2} }kernel package for Red Hat internal usage.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-extra package.
#	%%kernel_modules_extra_package [-m] <subpackage> <pretty-name>
#
%define kernel_modules_extra_package(m) \
%package %{?1:%{1}-}modules-extra\
Summary: Extra kernel modules to match the %{?2:%{2} }kernel\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{specrpmversion}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: kernel%{?1:-%{1}}-modules-extra = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-extra-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
%if %{-m:1}%{!-m:0}\
Requires: kernel-modules-extra-uname-r = %{KVERREL}%{uname_variant %{?1:+%{1}}}\
%endif\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-extra\
This package provides less commonly used kernel modules for the %{?2:%{2} }kernel package.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules package.
#	%%kernel_modules_package [-m] <subpackage> <pretty-name>
#
%define kernel_modules_package(m) \
%package %{?1:%{1}-}modules\
Summary: kernel modules to match the %{?2:%{2}-}core kernel\
Provides: kernel%{?1:-%{1}}-modules-%{_target_cpu} = %{specrpmversion}-%{release}\
Provides: kernel-modules-%{_target_cpu} = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: kernel-modules = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
%if %{-m:1}%{!-m:0}\
Requires: kernel-modules-uname-r = %{KVERREL}%{uname_variant %{?1:+%{1}}}\
%endif\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules\
This package provides commonly used kernel modules for the %{?2:%{2}-}core kernel package.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-core package.
#	%%kernel_modules_core_package [-m] <subpackage> <pretty-name>
#
%define kernel_modules_core_package(m) \
%package %{?1:%{1}-}modules-core\
Summary: Core kernel modules to match the %{?2:%{2}-}core kernel\
Provides: kernel%{?1:-%{1}}-modules-core-%{_target_cpu} = %{specrpmversion}-%{release}\
Provides: kernel-modules-core-%{_target_cpu} = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: kernel-modules-core = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
%if %{-m:1}%{!-m:0}\
Requires: kernel-modules-core-uname-r = %{KVERREL}%{uname_variant %{?1:+%{1}}}\
%endif\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-core\
This package provides essential kernel modules for the %{?2:%{2}-}core kernel package.\
%{nil}

#
# this macro creates a kernel-<subpackage> meta package.
#	%%kernel_meta_package <subpackage>
#
%define kernel_meta_package() \
%package %{1}\
summary: kernel meta-package for the %{1} kernel\
Requires: kernel-%{1}-core-uname-r = %{KVERREL}%{uname_suffix %{1}}\
Requires: kernel-%{1}-modules-uname-r = %{KVERREL}%{uname_suffix %{1}}\
Requires: kernel-%{1}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{1}}\
%if "%{1}" == "rt" || "%{1}" == "rt-debug"\
Requires: realtime-setup\
%endif\
Provides: installonlypkg(kernel)\
%description %{1}\
The meta-package for the %{1} kernel\
%{nil}

%if %{with_realtime}
#
# this macro creates a kernel-rt-<subpackage>-kvm package
# %%kernel_kvm_package <subpackage>
#
%define kernel_kvm_package() \
%package %{?1:%{1}-}kvm\
Summary: KVM modules for package kernel%{?1:-%{1}}\
Group: System Environment/Kernel\
Requires: kernel-uname-r = %{KVERREL}%{uname_suffix %{?1:%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-kvm-%{_target_cpu} = %{version}-%{release}\
AutoReq: no\
%description -n kernel%{?1:-%{1}}-kvm\
This package provides KVM modules for package kernel%{?1:-%{1}}.\
%{nil}
%endif

#
# This macro creates a kernel-<subpackage> and its -devel and -debuginfo too.
#	%%define variant_summary The Linux kernel compiled for <configuration>
#	%%kernel_variant_package [-n <pretty-name>] [-m] [-o] <subpackage>
#
%define kernel_variant_package(n:mo) \
%package %{?1:%{1}-}core\
Summary: %{variant_summary}\
Provides: kernel-%{?1:%{1}-}core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Provides: installonlypkg(kernel)\
%if %{-m:1}%{!-m:0}\
Requires: kernel-core-uname-r = %{KVERREL}%{uname_variant %{?1:+%{1}}}\
Requires: kernel-%{?1:%{1}-}-modules-core-uname-r = %{KVERREL}%{uname_variant %{?1:+%{1}}}\
%endif\
%{expand:%%kernel_reqprovconf %{?1:%{1}} %{-o:%{-o}}}\
%if %{?1:1} %{!?1:0} \
%{expand:%%kernel_meta_package %{?1:%{1}}}\
%endif\
%{expand:%%kernel_devel_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}} %{-m:%{-m}}}\
%{expand:%%kernel_devel_matched_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}} %{-m:%{-m}}}\
%{expand:%%kernel_modules_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}} %{-m:%{-m}}}\
%{expand:%%kernel_modules_core_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}} %{-m:%{-m}}}\
%{expand:%%kernel_modules_extra_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}} %{-m:%{-m}}}\
%if %{-m:0}%{!-m:1}\
%{expand:%%kernel_modules_internal_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%if 0%{!?fedora:1}\
%{expand:%%kernel_modules_partner_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%endif\
%{expand:%%kernel_debuginfo_package %{?1:%{1}}}\
%endif\
%if "%{1}" == "rt" || "%{1}" == "rt-debug"\
%{expand:%%kernel_kvm_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%else \
%if %{with_efiuki}\
%package %{?1:%{1}-}uki-virt\
Summary: %{variant_summary} unified kernel image for virtual machines\
Provides: installonlypkg(kernel)\
Provides: kernel-%{?1:%{1}-}uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires(pre): %{kernel_prereq}\
Requires(pre): systemd >= 254-1\
%package %{?1:%{1}-}uki-virt-addons\
Summary: %{variant_summary} unified kernel image addons for virtual machines\
Provides: installonlypkg(kernel)\
Requires: kernel%{?1:-%{1}}-uki-virt = %{specrpmversion}-%{release}\
Requires(pre): systemd >= 254-1\
%endif\
%endif\
%if %{with_gcov}\
%{expand:%%kernel_gcov_package %{?1:%{1}}}\
%endif\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-partner package.
#	%%kernel_modules_partner_package <subpackage> <pretty-name>
#
%define kernel_modules_partner_package() \
%package %{?1:%{1}-}modules-partner\
Summary: Extra kernel modules to match the %{?2:%{2} }kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-modules-partner-%{_target_cpu} = %{specrpmversion}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-partner-%{_target_cpu} = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: kernel%{?1:-%{1}}-modules-partner = %{specrpmversion}-%{release}%{uname_suffix %{?1:+%{1}}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-partner-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-partner\
This package provides kernel modules for the %{?2:%{2} }kernel package for Red Hat partners usage.\
%{nil}

# Now, each variant package.
%if %{with_zfcpdump}
%define variant_summary The Linux kernel compiled for zfcpdump usage
%kernel_variant_package -o zfcpdump
%description zfcpdump-core
The kernel package contains the Linux kernel (vmlinuz) for use by the
zfcpdump infrastructure.
# with_zfcpdump
%endif

%if %{with_arm64_16k_base}
%define variant_summary The Linux kernel compiled for 16k pagesize usage
%kernel_variant_package 16k
%description 16k-core
The kernel package contains a variant of the ARM64 Linux kernel using
a 16K page size.
%endif

%if %{with_arm64_16k} && %{with_debug}
%define variant_summary The Linux kernel compiled with extra debugging enabled
%if !%{debugbuildsenabled}
%kernel_variant_package -m 16k-debug
%else
%kernel_variant_package 16k-debug
%endif
%description 16k-debug-core
The debug kernel package contains a variant of the ARM64 Linux kernel using
a 16K page size.
This variant of the kernel has numerous debugging options enabled.
It should only be installed when trying to gather additional information
on kernel bugs, as some of these options impact performance noticably.
%endif

%if %{with_arm64_64k_base}
%define variant_summary The Linux kernel compiled for 64k pagesize usage
%kernel_variant_package 64k
%description 64k-core
The kernel package contains a variant of the ARM64 Linux kernel using
a 64K page size.
%endif

%if %{with_arm64_64k} && %{with_debug}
%define variant_summary The Linux kernel compiled with extra debugging enabled
%if !%{debugbuildsenabled}
%kernel_variant_package -m 64k-debug
%else
%kernel_variant_package 64k-debug
%endif
%description 64k-debug-core
The debug kernel package contains a variant of the ARM64 Linux kernel using
a 64K page size.
This variant of the kernel has numerous debugging options enabled.
It should only be installed when trying to gather additional information
on kernel bugs, as some of these options impact performance noticably.
%endif

%if %{with_debug} && %{with_realtime}
%define variant_summary The Linux PREEMPT_RT kernel compiled with extra debugging enabled
%kernel_variant_package rt-debug
%description rt-debug-core
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system:  memory allocation, process allocation, device
input and output, etc.

This variant of the kernel has numerous debugging options enabled.
It should only be installed when trying to gather additional information
on kernel bugs, as some of these options impact performance noticably.
%endif

%if %{with_realtime_base}
%define variant_summary The Linux kernel compiled with PREEMPT_RT enabled
%kernel_variant_package rt
%description rt-core
This package includes a version of the Linux kernel compiled with the
PREEMPT_RT real-time preemption support
%endif

%if %{with_up} && %{with_debug}
%if !%{debugbuildsenabled}
%kernel_variant_package -m debug
%else
%kernel_variant_package debug
%endif
%description debug-core
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system:  memory allocation, process allocation, device
input and output, etc.

This variant of the kernel has numerous debugging options enabled.
It should only be installed when trying to gather additional information
on kernel bugs, as some of these options impact performance noticably.
%endif

%if %{with_up_base}
# And finally the main -core package

%define variant_summary The Linux kernel
%kernel_variant_package
%description core
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.
%endif

%if %{with_up} && %{with_debug} && %{with_efiuki}
%description debug-uki-virt
Prebuilt debug unified kernel image for virtual machines.

%description debug-uki-virt-addons
Prebuilt debug unified kernel image addons for virtual machines.
%endif

%if %{with_up_base} && %{with_efiuki}
%description uki-virt
Prebuilt default unified kernel image for virtual machines.

%description uki-virt-addons
Prebuilt default unified kernel image addons for virtual machines.
%endif

%if %{with_arm64_16k} && %{with_debug} && %{with_efiuki}
%description 16k-debug-uki-virt
Prebuilt 16k debug unified kernel image for virtual machines.

%description 16k-debug-uki-virt-addons
Prebuilt 16k debug unified kernel image addons for virtual machines.
%endif

%if %{with_arm64_16k_base} && %{with_efiuki}
%description 16k-uki-virt
Prebuilt 16k unified kernel image for virtual machines.

%description 16k-uki-virt-addons
Prebuilt 16k unified kernel image addons for virtual machines.
%endif

%if %{with_arm64_64k} && %{with_debug} && %{with_efiuki}
%description 64k-debug-uki-virt
Prebuilt 64k debug unified kernel image for virtual machines.

%description 64k-debug-uki-virt-addons
Prebuilt 64k debug unified kernel image addons for virtual machines.
%endif

%if %{with_arm64_64k_base} && %{with_efiuki}
%description 64k-uki-virt
Prebuilt 64k unified kernel image for virtual machines.

%description 64k-uki-virt-addons
Prebuilt 64k unified kernel image addons for virtual machines.
%endif

%if %{with_ipaclones}
%kernel_ipaclones_package
%endif

%define log_msg() \
	{ set +x; } 2>/dev/null \
	_log_msglineno=$(grep -n %{*} %{_specdir}/${RPM_PACKAGE_NAME}.spec | grep log_msg | cut -d":" -f1) \
	echo "kernel.spec:${_log_msglineno}: %{*}" \
	set -x

%prep
%{log_msg "Start of prep stage"}

%{log_msg "Sanity checks"}

# do a few sanity-checks for --with *only builds
%if %{with_baseonly}
%if !%{with_up}
%{log_msg "Cannot build --with baseonly, up build is disabled"}
exit 1
%endif
%endif

# more sanity checking; do it quietly
if [ "%{patches}" != "%%{patches}" ] ; then
  for patch in %{patches} ; do
    if [ ! -f $patch ] ; then
	%{log_msg "ERROR: Patch  ${patch##/*/}  listed in specfile but is missing"}
      exit 1
    fi
  done
fi 2>/dev/null

patch_command='git --work-tree=. apply'
ApplyPatch()
{
  local patch=$1
  shift
  if [ ! -f $RPM_SOURCE_DIR/$patch ]; then
    exit 1
  fi
  if ! grep -E "^Patch[0-9]+: $patch\$" %{_specdir}/${RPM_PACKAGE_NAME}.spec ; then
    if [ "${patch:0:8}" != "patch-%{kversion}." ] ; then
	%{log_msg "ERROR: Patch  $patch  not listed as a source patch in specfile"}
      exit 1
    fi
  fi 2>/dev/null
  case "$patch" in
  *.bz2) bunzip2 < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
  *.gz)  gunzip  < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
  *.xz)  unxz    < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
  *) $patch_command ${1+"$@"} < "$RPM_SOURCE_DIR/$patch" ;;
  esac
}

# don't apply patch if it's empty
ApplyOptionalPatch()
{
  local patch=$1
  shift
  %{log_msg "ApplyOptionalPatch: $1"}
  if [ ! -f $RPM_SOURCE_DIR/$patch ]; then
    exit 1
  fi
  local C=$(wc -l $RPM_SOURCE_DIR/$patch | awk '{print $1}')
  if [ "$C" -gt 9 ]; then
    ApplyPatch $patch ${1+"$@"}
  fi
}

%{log_msg "Untar kernel tarball"}
%setup -q -n kernel-%{tarfile_release} -c
mv linux-%{tarfile_release} linux-%{KVERREL}

cd linux-%{KVERREL}
cp -a %{SOURCE1} .

%{log_msg "Start of patch applications"}
%if !%{nopatches}

ApplyOptionalPatch patch-%{patchversion}-redhat.patch
%endif

ApplyOptionalPatch linux-kernel-test.patch

%{log_msg "End of patch applications"}
# END OF PATCH APPLICATIONS

# Any further pre-build tree manipulations happen here.
%{log_msg "Pre-build tree manipulations"}
chmod +x scripts/checkpatch.pl
mv COPYING COPYING-%{specrpmversion}-%{release}

# on linux-next prevent scripts/setlocalversion from mucking with our version numbers
rm -f localversion-next localversion-rt

# Mangle /usr/bin/python shebangs to /usr/bin/python3
# Mangle all Python shebangs to be Python 3 explicitly
# -p preserves timestamps
# -n prevents creating ~backup files
# -i specifies the interpreter for the shebang
# This fixes errors such as
# *** ERROR: ambiguous python shebang in /usr/bin/kvm_stat: #!/usr/bin/python. Change it to python3 (or python2) explicitly.
# We patch all sources below for which we got a report/error.
%{log_msg "Fixing Python shebangs..."}
%py3_shebang_fix \
	tools/kvm/kvm_stat/kvm_stat \
	scripts/show_delta \
	scripts/diffconfig \
	scripts/bloat-o-meter \
	scripts/jobserver-exec \
	tools \
	Documentation \
	scripts/clang-tools 2> /dev/null

# only deal with configs if we are going to build for the arch
%ifnarch %nobuildarches

if [ -L configs ]; then
	rm -f configs
fi
mkdir configs
cd configs

%{log_msg "Copy additional source files into buildroot"}
# Drop some necessary files from the source dir into the buildroot
cp $RPM_SOURCE_DIR/%{name}-*.config .
cp %{SOURCE80} .
# merge.py
cp %{SOURCE3000} .
# kernel-local - rename and copy for partial snippet config process
cp %{SOURCE3001} partial-kernel-local-snip.config
cp %{SOURCE3001} partial-kernel-local-debug-snip.config
FLAVOR=%{primary_target} SPECPACKAGE_NAME=%{name} SPECVERSION=%{specversion} SPECRPMVERSION=%{specrpmversion} ./generate_all_configs.sh %{debugbuildsenabled}

# Collect custom defined config options
%{log_msg "Collect custom defined config options"}
PARTIAL_CONFIGS=""
%if %{with_gcov}
PARTIAL_CONFIGS="$PARTIAL_CONFIGS %{SOURCE70} %{SOURCE71}"
%endif
%if %{with toolchain_clang}
PARTIAL_CONFIGS="$PARTIAL_CONFIGS %{SOURCE72} %{SOURCE73}"
%endif
%if %{with clang_lto}
PARTIAL_CONFIGS="$PARTIAL_CONFIGS %{SOURCE74} %{SOURCE75} %{SOURCE76} %{SOURCE77}"
%endif
PARTIAL_CONFIGS="$PARTIAL_CONFIGS partial-kernel-local-snip.config partial-kernel-local-debug-snip.config"

GetArch()
{
  case "$1" in
  *aarch64*) echo "aarch64" ;;
  *ppc64le*) echo "ppc64le" ;;
  *s390x*) echo "s390x" ;;
  *x86_64*) echo "x86_64" ;;
  # no arch, apply everywhere
  *) echo "" ;;
  esac
}

# Merge in any user-provided local config option changes
%{log_msg "Merge in any user-provided local config option changes"}
%ifnarch %nobuildarches
for i in %{all_configs}
do
  kern_arch="$(GetArch $i)"
  kern_debug="$(echo $i | grep -q debug && echo "debug" || echo "")"

  for j in $PARTIAL_CONFIGS
  do
    part_arch="$(GetArch $j)"
    part_debug="$(echo $j | grep -q debug && echo "debug" || echo "")"

    # empty arch means apply to all arches
    if [ "$part_arch" == "" -o "$part_arch" == "$kern_arch" ] && [ "$part_debug" == "$kern_debug" ]
    then
      mv $i $i.tmp
      ./merge.py $j $i.tmp > $i
    fi
  done
  rm -f $i.tmp
done
%endif

%if %{signkernel}%{signmodules}

# Add DUP and kpatch certificates to system trusted keys for RHEL
%if 0%{?rhel}
%{log_msg "Add DUP and kpatch certificates to system trusted keys for RHEL"}
openssl x509 -inform der -in %{SOURCE100} -out rheldup3.pem
openssl x509 -inform der -in %{SOURCE101} -out rhelkpatch1.pem
openssl x509 -inform der -in %{SOURCE102} -out nvidiagpuoot001.pem
cat rheldup3.pem rhelkpatch1.pem nvidiagpuoot001.pem > ../certs/rhel.pem
%if %{signkernel}
%ifarch s390x ppc64le
openssl x509 -inform der -in %{secureboot_ca_0} -out secureboot.pem
cat secureboot.pem >> ../certs/rhel.pem
%endif
%endif

# rhel
%endif

openssl x509 -inform der -in %{ima_ca_cert} -out imaca.pem
cat imaca.pem >> ../certs/rhel.pem

for i in *.config; do
  sed -i 's@CONFIG_SYSTEM_TRUSTED_KEYS=""@CONFIG_SYSTEM_TRUSTED_KEYS="certs/rhel.pem"@' $i
done
%endif

# Adjust FIPS module name for RHEL
%if 0%{?rhel}
%{log_msg "Adjust FIPS module name for RHEL"}
for i in *.config; do
  sed -i 's/CONFIG_CRYPTO_FIPS_NAME=.*/CONFIG_CRYPTO_FIPS_NAME="Red Hat Enterprise Linux %{rhel} - Kernel Cryptographic API"/' $i
done
%endif

%{log_msg "Set process_configs.sh $OPTS"}
cp %{SOURCE81} .
OPTS=""
%if %{with_configchecks}
	OPTS="$OPTS -w -n -c"
%endif
%if %{with clang_lto}
for opt in %{clang_make_opts}; do
  OPTS="$OPTS -m $opt"
done
%endif
%{log_msg "Generate redhat configs"}
RHJOBS=$RPM_BUILD_NCPUS SPECPACKAGE_NAME=%{name} ./process_configs.sh $OPTS %{specrpmversion}

# We may want to override files from the primary target in case of building
# against a flavour of it (eg. centos not rhel), thus override it here if
# necessary
update_scripts() {
	TARGET="$1"

	for i in "$RPM_SOURCE_DIR"/*."$TARGET"; do
		NEW=${i%."$TARGET"}
		cp "$i" "$(basename "$NEW")"
	done
}

%{log_msg "Set scripts/SOURCES targets"}
update_target=%{primary_target}
if [ "%{primary_target}" == "rhel" ]; then
: # no-op to avoid empty if-fi error
%if 0%{?centos}
  update_scripts $update_target
  %{log_msg "Updating scripts/sources to centos version"}
  update_target=centos
%endif
fi
update_scripts $update_target

%endif

%{log_msg "End of kernel config"}
cd ..
# # End of Configs stuff

# get rid of unwanted files resulting from patch fuzz
find . \( -name "*.orig" -o -name "*~" \) -delete >/dev/null

# remove unnecessary SCM files
find . -name .gitignore -delete >/dev/null

cd ..

###
### build
###
%build
%{log_msg "Start of build stage"}

%{log_msg "General arch build configuration"}
rm -rf %{buildroot_unstripped} || true
mkdir -p %{buildroot_unstripped}

%if %{with_sparse}
%define sparse_mflags	C=1
%endif

cp_vmlinux()
{
  eu-strip --remove-comment -o "$2" "$1"
}

# Note we need to disable these flags for cross builds because the flags
# from redhat-rpm-config assume that host == target so target arch
# flags cause issues with the host compiler.
%if !%{with_cross}
%define build_hostcflags  %{?build_cflags}
%define build_hostldflags %{?build_ldflags}
%endif

%define make %{__make} %{?cross_opts} %{?make_opts} HOSTCFLAGS="%{?build_hostcflags}" HOSTLDFLAGS="%{?build_hostldflags}"

InitBuildVars() {
    %{log_msg "InitBuildVars for $1"}

    %{log_msg "InitBuildVars: Initialize build variables"}
    # Initialize the kernel .config file and create some variables that are
    # needed for the actual build process.

    Variant=$1

    # Pick the right kernel config file
    Config=%{name}-%{specrpmversion}-%{_target_cpu}${Variant:+-${Variant}}.config
    DevelDir=/usr/src/kernels/%{KVERREL}${Variant:++${Variant}}

    KernelVer=%{specversion}-%{release}.%{_target_cpu}${Variant:++${Variant}}

    %{log_msg "InitBuildVars: Update Makefile"}
    # make sure EXTRAVERSION says what we want it to say
    # Trim the release if this is a CI build, since KERNELVERSION is limited to 64 characters
    ShortRel=$(perl -e "print \"%{release}\" =~ s/\.pr\.[0-9A-Fa-f]{32}//r")
    perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = -${ShortRel}.%{_target_cpu}${Variant:++${Variant}}/" Makefile

    # if pre-rc1 devel kernel, must fix up PATCHLEVEL for our versioning scheme
    # if we are post rc1 this should match anyway so this won't matter
    perl -p -i -e 's/^PATCHLEVEL.*/PATCHLEVEL = %{patchlevel}/' Makefile

    %{log_msg "InitBuildVars: Copy files"}
    %{make} %{?_smp_mflags} mrproper
    cp configs/$Config .config

    %if %{signkernel}%{signmodules}
    cp configs/x509.genkey certs/.
    %endif

    Arch=`head -1 .config | cut -b 3-`
    %{log_msg "InitBuildVars: USING ARCH=$Arch"}

    KCFLAGS="%{?kcflags}"

    # add kpatch flags for base kernel
    %{log_msg "InitBuildVars: Configure KCFLAGS"}
    if [ "$Variant" == "" ]; then
        KCFLAGS="$KCFLAGS %{?kpatch_kcflags}"
    fi
}

BuildKernel() {
    %{log_msg "BuildKernel for $4"}
    MakeTarget=$1
    KernelImage=$2
    DoVDSO=$3
    Variant=$4
    InstallName=${5:-vmlinuz}

    %{log_msg "Setup variables"}
    DoModules=1
    if [ "$Variant" = "zfcpdump" ]; then
	    DoModules=0
    fi

    # When the bootable image is just the ELF kernel, strip it.
    # We already copy the unstripped file into the debuginfo package.
    if [ "$KernelImage" = vmlinux ]; then
      CopyKernel=cp_vmlinux
    else
      CopyKernel=cp
    fi

%if %{with_gcov}
    %{log_msg "Setup build directories"}
    # Make build directory unique for each variant, so that gcno symlinks
    # are also unique for each variant.
    if [ -n "$Variant" ]; then
        ln -s $(pwd) ../linux-%{KVERREL}-${Variant}
    fi
    %{log_msg "GCOV - continuing build in: $(pwd)"}
    pushd ../linux-%{KVERREL}${Variant:+-${Variant}}
    pwd > ../kernel${Variant:+-${Variant}}-gcov.list
%endif

    %{log_msg "Calling InitBuildVars for $Variant"}
    InitBuildVars $Variant

    %{log_msg "BUILDING A KERNEL FOR ${Variant} %{_target_cpu}..."}

    %{make} ARCH=$Arch olddefconfig >/dev/null

    %{log_msg "Setup build-ids"}
    # This ensures build-ids are unique to allow parallel debuginfo
    perl -p -i -e "s/^CONFIG_BUILD_SALT.*/CONFIG_BUILD_SALT=\"%{KVERREL}\"/" .config
    %{make} ARCH=$Arch KCFLAGS="$KCFLAGS" WITH_GCOV="%{?with_gcov}" %{?_smp_mflags} $MakeTarget %{?sparse_mflags} %{?kernel_mflags}
    if [ $DoModules -eq 1 ]; then
	%{make} ARCH=$Arch KCFLAGS="$KCFLAGS" WITH_GCOV="%{?with_gcov}" %{?_smp_mflags} modules %{?sparse_mflags} || exit 1
    fi

    %{log_msg "Setup RPM_BUILD_ROOT directories"}
    mkdir -p $RPM_BUILD_ROOT/%{image_install_path}
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/systemtap
%if %{with_debuginfo}
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/%{image_install_path}
%endif

%ifarch aarch64
    %{log_msg "Build dtb kernel"}
    %{make} ARCH=$Arch dtbs INSTALL_DTBS_PATH=$RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer
    %{make} ARCH=$Arch dtbs_install INSTALL_DTBS_PATH=$RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer
    cp -r $RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/dtb
    find arch/$Arch/boot/dts -name '*.dtb' -type f -delete
%endif

    %{log_msg "Cleanup temp btf files"}
    # Remove large intermediate files we no longer need to save space
    # (-f required for zfcpdump builds that do not enable BTF)
    rm -f vmlinux.o .tmp_vmlinux.btf

    %{log_msg "Install files to RPM_BUILD_ROOT"}

    # Comment out specific config settings that may use resources not available
    # to the end user so that the packaged config file can be easily reused with
    # upstream make targets
    %if %{signkernel}%{signmodules}
      sed -i -e '/^CONFIG_SYSTEM_TRUSTED_KEYS/{
        i\# The kernel was built with
        s/^/# /
        a\# We are resetting this value to facilitate local builds
        a\CONFIG_SYSTEM_TRUSTED_KEYS=""
        }' .config
    %endif

    # Start installing the results
    install -m 644 .config $RPM_BUILD_ROOT/boot/config-$KernelVer
    install -m 644 .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/config
    install -m 644 System.map $RPM_BUILD_ROOT/boot/System.map-$KernelVer
    install -m 644 System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/System.map

    %{log_msg "Create initrfamfs"}
    # We estimate the size of the initramfs because rpm needs to take this size
    # into consideration when performing disk space calculations. (See bz #530778)
    dd if=/dev/zero of=$RPM_BUILD_ROOT/boot/initramfs-$KernelVer.img bs=1M count=20

    if [ -f arch/$Arch/boot/zImage.stub ]; then
      %{log_msg "Copy zImage.stub to RPM_BUILD_ROOT"}
      cp arch/$Arch/boot/zImage.stub $RPM_BUILD_ROOT/%{image_install_path}/zImage.stub-$KernelVer || :
      cp arch/$Arch/boot/zImage.stub $RPM_BUILD_ROOT/lib/modules/$KernelVer/zImage.stub-$KernelVer || :
    fi

    %if %{signkernel}
    %{log_msg "Copy kernel for signing"}
    if [ "$KernelImage" = vmlinux ]; then
        # We can't strip and sign $KernelImage in place, because
        # we need to preserve original vmlinux for debuginfo.
        # Use a copy for signing.
        $CopyKernel $KernelImage $KernelImage.tosign
        KernelImage=$KernelImage.tosign
        CopyKernel=cp
    fi

    SignImage=$KernelImage

    %ifarch x86_64 aarch64
    %{log_msg "Sign kernel image"}
    %pesign -s -i $SignImage -o vmlinuz.signed -a %{secureboot_ca_0} -c %{secureboot_key_0} -n %{pesign_name_0}
    %endif
    %ifarch s390x ppc64le
    if [ -x /usr/bin/rpm-sign ]; then
	rpm-sign --key "%{pesign_name_0}" --lkmsign $SignImage --output vmlinuz.signed
    elif [ "$DoModules" == "1" -a "%{signmodules}" == "1" ]; then
	chmod +x scripts/sign-file
	./scripts/sign-file -p sha256 certs/signing_key.pem certs/signing_key.x509 $SignImage vmlinuz.signed
    else
	mv $SignImage vmlinuz.signed
    fi
    %endif

    if [ ! -s vmlinuz.signed ]; then
	%{log_msg "pesigning failed"}
        exit 1
    fi
    mv vmlinuz.signed $SignImage
    # signkernel
    %endif

    %{log_msg "copy signed kernel"}
    $CopyKernel $KernelImage \
                $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    chmod 755 $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    cp $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/$InstallName

    # hmac sign the kernel for FIPS
    %{log_msg "hmac sign the kernel for FIPS"}
    %{log_msg "Creating hmac file: $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac"}
    ls -l $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    (cd $RPM_BUILD_ROOT/%{image_install_path} && sha512hmac $InstallName-$KernelVer) > $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac;
    cp $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac $RPM_BUILD_ROOT/lib/modules/$KernelVer/.vmlinuz.hmac

    if [ $DoModules -eq 1 ]; then
	%{log_msg "Install modules in RPM_BUILD_ROOT"}
	# Override $(mod-fw) because we don't want it to install any firmware
	# we'll get it from the linux-firmware package and we don't want conflicts
	%{make} %{?_smp_mflags} ARCH=$Arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT %{?_smp_mflags} modules_install KERNELRELEASE=$KernelVer mod-fw=
    fi

%if %{with_gcov}
    %{log_msg "install gcov-needed files to $BUILDROOT/$BUILD/"}
    # install gcov-needed files to $BUILDROOT/$BUILD/...:
    #   gcov_info->filename is absolute path
    #   gcno references to sources can use absolute paths (e.g. in out-of-tree builds)
    #   sysfs symlink targets (set up at compile time) use absolute paths to BUILD dir
    find . \( -name '*.gcno' -o -name '*.[chS]' \) -exec install -D '{}' "$RPM_BUILD_ROOT/$(pwd)/{}" \;
%endif

    %{log_msg "Add VDSO files"}
    # add an a noop %%defattr statement 'cause rpm doesn't like empty file list files
    echo '%%defattr(-,-,-)' > ../kernel${Variant:+-${Variant}}-ldsoconf.list
    if [ $DoVDSO -ne 0 ]; then
        %{make} ARCH=$Arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT vdso_install KERNELRELEASE=$KernelVer
        if [ -s ldconfig-kernel.conf ]; then
             install -D -m 444 ldconfig-kernel.conf \
                $RPM_BUILD_ROOT/etc/ld.so.conf.d/kernel-$KernelVer.conf
	     echo /etc/ld.so.conf.d/kernel-$KernelVer.conf >> ../kernel${Variant:+-${Variant}}-ldsoconf.list
        fi

        rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/vdso/.build-id
    fi

    %{log_msg "Save headers/makefiles, etc. for kernel-headers"}
    # And save the headers/makefiles etc for building modules against
    #
    # This all looks scary, but the end result is supposed to be:
    # * all arch relevant include/ files
    # * all Makefile/Kconfig files
    # * all script/ files

    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/source
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    (cd $RPM_BUILD_ROOT/lib/modules/$KernelVer ; ln -s build source)
    # dirs for additional modules per module-init-tools, kbuild/modules.txt
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/updates
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/weak-updates
    # CONFIG_KERNEL_HEADER_TEST generates some extra files in the process of
    # testing so just delete
    find . -name *.h.s -delete
    # first copy everything
    cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ ! -e Module.symvers ]; then
        touch Module.symvers
    fi
    cp Module.symvers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -s Module.markers ]; then
      cp Module.markers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    fi

    # create the kABI metadata for use in packaging
    # NOTENOTE: the name symvers is used by the rpm backend
    # NOTENOTE: to discover and run the /usr/lib/rpm/fileattrs/kabi.attr
    # NOTENOTE: script which dynamically adds exported kernel symbol
    # NOTENOTE: checksums to the rpm metadata provides list.
    # NOTENOTE: if you change the symvers name, update the backend too
    %{log_msg "GENERATING kernel ABI metadata"}
    %compression --stdout %compression_flags < Module.symvers > $RPM_BUILD_ROOT/boot/symvers-$KernelVer.%compext
    cp $RPM_BUILD_ROOT/boot/symvers-$KernelVer.%compext $RPM_BUILD_ROOT/lib/modules/$KernelVer/symvers.%compext

%if %{with_kabichk}
    %{log_msg "kABI checking is enabled in kernel SPEC file."}
    chmod 0755 $RPM_SOURCE_DIR/check-kabi
    if [ -e $RPM_SOURCE_DIR/Module.kabi_%{_target_cpu}$Variant ]; then
        cp $RPM_SOURCE_DIR/Module.kabi_%{_target_cpu}$Variant $RPM_BUILD_ROOT/Module.kabi
        $RPM_SOURCE_DIR/check-kabi -k $RPM_BUILD_ROOT/Module.kabi -s Module.symvers || exit 1
        # for now, don't keep it around.
        rm $RPM_BUILD_ROOT/Module.kabi
    else
	%{log_msg "NOTE: Cannot find reference Module.kabi file."}
    fi
%endif

%if %{with_kabidupchk}
    %{log_msg "kABI DUP checking is enabled in kernel SPEC file."}
    if [ -e $RPM_SOURCE_DIR/Module.kabi_dup_%{_target_cpu}$Variant ]; then
        cp $RPM_SOURCE_DIR/Module.kabi_dup_%{_target_cpu}$Variant $RPM_BUILD_ROOT/Module.kabi
        $RPM_SOURCE_DIR/check-kabi -k $RPM_BUILD_ROOT/Module.kabi -s Module.symvers || exit 1
        # for now, don't keep it around.
        rm $RPM_BUILD_ROOT/Module.kabi
    else
	%{log_msg "NOTE: Cannot find DUP reference Module.kabi file."}
    fi
%endif

%if %{with_kabidw_base}
    # Don't build kabi base for debug kernels
    if [ "$Variant" != "zfcpdump" -a "$Variant" != "debug" ]; then
        mkdir -p $RPM_BUILD_ROOT/kabi-dwarf
        tar -xvf %{SOURCE301} -C $RPM_BUILD_ROOT/kabi-dwarf

        mkdir -p $RPM_BUILD_ROOT/kabi-dwarf/stablelists
        tar -xvf %{SOURCE300} -C $RPM_BUILD_ROOT/kabi-dwarf/stablelists

	%{log_msg "GENERATING DWARF-based kABI baseline dataset"}
        chmod 0755 $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh
        $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh generate \
            "$RPM_BUILD_ROOT/kabi-dwarf/stablelists/kabi-current/kabi_stablelist_%{_target_cpu}" \
            "$(pwd)" \
            "$RPM_BUILD_ROOT/kabidw-base/%{_target_cpu}${Variant:+.${Variant}}" || :

        rm -rf $RPM_BUILD_ROOT/kabi-dwarf
    fi
%endif

%if %{with_kabidwchk}
    if [ "$Variant" != "zfcpdump" ]; then
        mkdir -p $RPM_BUILD_ROOT/kabi-dwarf
        tar -xvf %{SOURCE301} -C $RPM_BUILD_ROOT/kabi-dwarf
        if [ -d "$RPM_BUILD_ROOT/kabi-dwarf/base/%{_target_cpu}${Variant:+.${Variant}}" ]; then
            mkdir -p $RPM_BUILD_ROOT/kabi-dwarf/stablelists
            tar -xvf %{SOURCE300} -C $RPM_BUILD_ROOT/kabi-dwarf/stablelists

	    %{log_msg "GENERATING DWARF-based kABI dataset"}
            chmod 0755 $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh
            $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh generate \
                "$RPM_BUILD_ROOT/kabi-dwarf/stablelists/kabi-current/kabi_stablelist_%{_target_cpu}" \
                "$(pwd)" \
                "$RPM_BUILD_ROOT/kabi-dwarf/base/%{_target_cpu}${Variant:+.${Variant}}.tmp" || :

	    %{log_msg "kABI DWARF-based comparison report"}
            $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh compare \
                "$RPM_BUILD_ROOT/kabi-dwarf/base/%{_target_cpu}${Variant:+.${Variant}}" \
                "$RPM_BUILD_ROOT/kabi-dwarf/base/%{_target_cpu}${Variant:+.${Variant}}.tmp" || :
	    %{log_msg "End of kABI DWARF-based comparison report"}
        else
	    %{log_msg "Baseline dataset for kABI DWARF-BASED comparison report not found"}
        fi

        rm -rf $RPM_BUILD_ROOT/kabi-dwarf
    fi
%endif

   %{log_msg "Cleanup Makefiles/Kconfig files"}
    # then drop all but the needed Makefiles/Kconfig files
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
    cp .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/tracing
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/spdxcheck.py

%ifarch s390x
    # CONFIG_EXPOLINE_EXTERN=y produces arch/s390/lib/expoline/expoline.o
    # which is needed during external module build.
    %{log_msg "Copy expoline.o"}
    if [ -f arch/s390/lib/expoline/expoline.o ]; then
      cp -a --parents arch/s390/lib/expoline/expoline.o $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    fi
%endif

    %{log_msg "Copy additional files for make targets"}
    # Files for 'make scripts' to succeed with kernel-devel.
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/security/selinux/include
    cp -a --parents security/selinux/include/classmap.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents security/selinux/include/initial_sid_to_string.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/tools/include/tools
    cp -a --parents tools/include/tools/be_byteshift.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/include/tools/le_byteshift.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    # Files for 'make prepare' to succeed with kernel-devel.
    cp -a --parents tools/include/linux/compiler* $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/include/linux/types.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/build/Build.include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/build/Build $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/build/fixdep.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/objtool/sync-check.sh $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/bpf/resolve_btfids $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    cp --parents security/selinux/include/policycap_names.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents security/selinux/include/policycap.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    cp -a --parents tools/include/asm $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/include/asm-generic $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/include/linux $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/include/uapi/asm $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/include/uapi/asm-generic $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/include/uapi/linux $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/include/vdso $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/scripts/utilities.mak $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/lib/subcmd $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/lib/*.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/objtool/*.[ch] $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/objtool/Build $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/objtool/include/objtool/*.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/lib/bpf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents tools/lib/bpf/Build $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    if [ -f tools/objtool/objtool ]; then
      cp -a tools/objtool/objtool $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/tools/objtool/ || :
    fi
    if [ -f tools/objtool/fixdep ]; then
      cp -a tools/objtool/fixdep $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/tools/objtool/ || :
    fi
    if [ -d arch/$Arch/scripts ]; then
      cp -a arch/$Arch/scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch} || :
    fi
    if [ -f arch/$Arch/*lds ]; then
      cp -a arch/$Arch/*lds $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch}/ || :
    fi
    if [ -f arch/%{asmarch}/kernel/module.lds ]; then
      cp -a --parents arch/%{asmarch}/kernel/module.lds $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
    find $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts \( -iname "*.o" -o -iname "*.cmd" \) -exec rm -f {} +
%ifarch ppc64le
    cp -a --parents arch/powerpc/lib/crtsavres.[So] $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
%endif
    if [ -d arch/%{asmarch}/include ]; then
      cp -a --parents arch/%{asmarch}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
    if [ -d tools/arch/%{asmarch}/include ]; then
      cp -a --parents tools/arch/%{asmarch}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    fi
%ifarch aarch64
    # arch/arm64/include/asm/xen references arch/arm
    cp -a --parents arch/arm/include/asm/xen $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    # arch/arm64/include/asm/opcodes.h references arch/arm
    cp -a --parents arch/arm/include/asm/opcodes.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
%endif
    cp -a include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
    # Cross-reference from include/perf/events/sof.h
    cp -a sound/soc/sof/sof-audio.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/sound/soc/sof
%ifarch i686 x86_64
    # files for 'make prepare' to succeed with kernel-devel
    cp -a --parents arch/x86/entry/syscalls/syscall_32.tbl $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/entry/syscalls/syscall_64.tbl $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs_32.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs_64.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs_common.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/purgatory/purgatory.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/purgatory/stack.S $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/purgatory/setup-x86_64.S $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/purgatory/entry64.S $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/boot/string.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/boot/string.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/boot/ctype.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/

    cp -a --parents scripts/syscalltbl.sh $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents scripts/syscallhdr.sh $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/

    cp -a --parents tools/arch/x86/include/asm $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/arch/x86/include/uapi/asm $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/objtool/arch/x86/lib $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/arch/x86/lib/ $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/arch/x86/tools/gen-insn-attr-x86.awk $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/objtool/arch/x86/ $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

%endif
    %{log_msg "Clean up intermediate tools files"}
    # Clean up intermediate tools files
    find $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/tools \( -iname "*.o" -o -iname "*.cmd" \) -exec rm -f {} +

    # Make sure the Makefile, version.h, and auto.conf have a matching
    # timestamp so that external modules can be built
    touch -r $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile \
        $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/generated/uapi/linux/version.h \
        $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/config/auto.conf

%if %{with_debuginfo}
    eu-readelf -n vmlinux | grep "Build ID" | awk '{print $NF}' > vmlinux.id
    cp vmlinux.id $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/vmlinux.id

    %{log_msg "Copy additional files for kernel-debuginfo rpm"}
    #
    # save the vmlinux file for kernel debugging into the kernel-debuginfo rpm
    # (use mv + symlink instead of cp to reduce disk space requirements)
    #
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
    mv vmlinux $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
    ln -s $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer/vmlinux vmlinux
    if [ -n "%{?vmlinux_decompressor}" ]; then
	    eu-readelf -n  %{vmlinux_decompressor} | grep "Build ID" | awk '{print $NF}' > vmlinux.decompressor.id
	    # Without build-id the build will fail. But for s390 the build-id
	    # wasn't added before 5.11. In case it is missing prefer not
	    # packaging the debuginfo over a build failure.
	    if [ -s vmlinux.decompressor.id ]; then
		    cp vmlinux.decompressor.id $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/vmlinux.decompressor.id
		    cp %{vmlinux_decompressor} $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer/vmlinux.decompressor
	    fi
    fi

    # build and copy the vmlinux-gdb plugin files into kernel-debuginfo
    %{make} ARCH=$Arch %{?_smp_mflags} scripts_gdb
    cp -a --parents scripts/gdb/{,linux/}*.py $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
    # this should be a relative symlink (Kbuild creates an absolute one)
    ln -s scripts/gdb/vmlinux-gdb.py $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer/vmlinux-gdb.py
    %py_byte_compile %{python3} $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer/scripts/gdb
%endif

    %{log_msg "Create modnames"}
    find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name "*.ko" -type f >modnames

    # mark modules executable so that strip-to-file can strip them
    xargs --no-run-if-empty chmod u+x < modnames

    # Generate a list of modules for block and networking.
    %{log_msg "Generate a list of modules for block and networking"}
    grep -F /drivers/ modnames | xargs --no-run-if-empty nm -upA |
    sed -n 's,^.*/\([^/]*\.ko\):  *U \(.*\)$,\1 \2,p' > drivers.undef

    collect_modules_list()
    {
      sed -r -n -e "s/^([^ ]+) \\.?($2)\$/\\1/p" drivers.undef |
        LC_ALL=C sort -u > $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
      if [ ! -z "$3" ]; then
        sed -r -e "/^($3)\$/d" -i $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
      fi
    }

    collect_modules_list networking \
      'register_netdev|ieee80211_register_hw|usbnet_probe|phy_driver_register|rt(l_|2x00)(pci|usb)_probe|register_netdevice'
    collect_modules_list block \
      'ata_scsi_ioctl|scsi_add_host|scsi_add_host_with_dma|blk_alloc_queue|blk_init_queue|register_mtd_blktrans|scsi_esp_register|scsi_register_device_handler|blk_queue_physical_block_size' 'pktcdvd.ko|dm-mod.ko'
    collect_modules_list drm \
      'drm_open|drm_init'
    collect_modules_list modesetting \
      'drm_crtc_init'

    %{log_msg "detect missing or incorrect license tags"}
    # detect missing or incorrect license tags
    ( find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name '*.ko' | xargs /sbin/modinfo -l | \
        grep -E -v 'GPL( v2)?$|Dual BSD/GPL$|Dual MPL/GPL$|GPL and additional rights$' ) && exit 1


    if [ $DoModules -eq 0 ]; then
        %{log_msg "Create empty files for RPM packaging"}
        # Ensure important files/directories exist to let the packaging succeed
        echo '%%defattr(-,-,-)' > ../kernel${Variant:+-${Variant}}-modules-core.list
        echo '%%defattr(-,-,-)' > ../kernel${Variant:+-${Variant}}-modules.list
        echo '%%defattr(-,-,-)' > ../kernel${Variant:+-${Variant}}-modules-extra.list
        echo '%%defattr(-,-,-)' > ../kernel${Variant:+-${Variant}}-modules-internal.list
        echo '%%defattr(-,-,-)' > ../kernel${Variant:+-${Variant}}-modules-partner.list
        mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/kernel
        # Add files usually created by make modules, needed to prevent errors
        # thrown by depmod during package installation
        touch $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.order
        touch $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.builtin
    fi

    # Copy the System.map file for depmod to use
    cp System.map $RPM_BUILD_ROOT/.

    if [[ "$Variant" == "rt" || "$Variant" == "rt-debug" ]]; then
	%{log_msg "Skipping efiuki build"}
    else
%if %{with_efiuki}
        %{log_msg "Setup the EFI UKI kernel"}

        # RHEL/CentOS specific .SBAT entries
%if 0%{?centos}
        SBATsuffix="centos"
%else
        SBATsuffix="rhel"
%endif
        SBAT=$(cat <<- EOF
	linux,1,Red Hat,linux,$KernelVer,mailto:secalert@redhat.com
	linux.$SBATsuffix,1,Red Hat,linux,$KernelVer,mailto:secalert@redhat.com
	kernel-uki-virt.$SBATsuffix,1,Red Hat,kernel-uki-virt,$KernelVer,mailto:secalert@redhat.com
	EOF
	)

	KernelUnifiedImageDir="$RPM_BUILD_ROOT/lib/modules/$KernelVer"
    	KernelUnifiedImage="$KernelUnifiedImageDir/$InstallName-virt.efi"

    	mkdir -p $KernelUnifiedImageDir

    	dracut --conf=%{SOURCE86} \
           --confdir=$(mktemp -d) \
           --verbose \
           --kver "$KernelVer" \
           --kmoddir "$RPM_BUILD_ROOT/lib/modules/$KernelVer/" \
           --logfile=$(mktemp) \
           --uefi \
%if 0%{?rhel} && !0%{?eln}
           --sbat "$SBAT" \
%endif
           --kernel-image $(realpath $KernelImage) \
           --kernel-cmdline 'console=tty0 console=ttyS0' \
	   $KernelUnifiedImage

  KernelAddonsDirOut="$KernelUnifiedImage.extra.d"
  mkdir -p $KernelAddonsDirOut
  python3 %{SOURCE151} %{SOURCE152} $KernelAddonsDirOut virt %{primary_target} %{_target_cpu}

%if %{signkernel}
	%{log_msg "Sign the EFI UKI kernel"}
%if 0%{?fedora}%{?eln}
        %pesign -s -i $KernelUnifiedImage -o $KernelUnifiedImage.signed -a %{secureboot_ca_0} -c %{secureboot_key_0} -n %{pesign_name_0}
%else
%if 0%{?centos}
        UKI_secureboot_name=centossecureboot204
%else
        UKI_secureboot_name=redhatsecureboot504
%endif
        UKI_secureboot_cert=%{_datadir}/pki/sb-certs/secureboot-uki-virt-%{_arch}.cer

        %pesign -s -i $KernelUnifiedImage -o $KernelUnifiedImage.signed -a %{secureboot_ca_0} -c $UKI_secureboot_cert -n $UKI_secureboot_name
# 0%{?fedora}%{?eln}
%endif
        if [ ! -s $KernelUnifiedImage.signed ]; then
            echo "pesigning failed"
            exit 1
        fi
        mv $KernelUnifiedImage.signed $KernelUnifiedImage

      for addon in "$KernelAddonsDirOut"/*; do
        %pesign -s -i $addon -o $addon.signed -a %{secureboot_ca_0} -c %{secureboot_key_0} -n %{pesign_name_0}
        rm -f $addon
        mv $addon.signed $addon
      done

# signkernel
%endif

    # hmac sign the UKI for FIPS
    KernelUnifiedImageHMAC="$KernelUnifiedImageDir/.$InstallName-virt.efi.hmac"
    %{log_msg "hmac sign the UKI for FIPS"}
    %{log_msg "Creating hmac file: $KernelUnifiedImageHMAC"}
    (cd $KernelUnifiedImageDir && sha512hmac $InstallName-virt.efi) > $KernelUnifiedImageHMAC;

# with_efiuki
%endif
	:  # in case of empty block
    fi # "$Variant" == "rt" || "$Variant" == "rt-debug"


    #
    # Generate the modules files lists
    #
    move_kmod_list()
    {
        local module_list="$1"
        local subdir_name="$2"

        mkdir -p "$RPM_BUILD_ROOT/lib/modules/$KernelVer/$subdir_name"

        set +x
        while read -r kmod; do
            local target_file="$RPM_BUILD_ROOT/lib/modules/$KernelVer/$subdir_name/$kmod"
            local target_dir="${target_file%/*}"
            mkdir -p "$target_dir"
            mv "$RPM_BUILD_ROOT/lib/modules/$KernelVer/kernel/$kmod" "$target_dir"
        done < <(sed -e 's|^kernel/||' "$module_list")
        set -x
    }

    create_module_file_list()
    {
        # subdirectory within /lib/modules/$KernelVer where kmods should go
        local module_subdir="$1"
        # kmod list with relative paths produced by filtermods.py
        local relative_kmod_list="$2"
        # list with absolute paths to kmods and other files to be included
        local absolute_file_list="$3"
        # if 1, this adds also all kmod directories to absolute_file_list
        local add_all_dirs="$4"
        local run_mod_deny="$5"

        if [ "$module_subdir" != "kernel" ]; then
            # move kmods into subdirs if needed (internal, partner, extra,..)
            move_kmod_list $relative_kmod_list $module_subdir
        fi

        # make kmod paths absolute
        sed -e 's|^kernel/|/lib/modules/'$KernelVer'/'$module_subdir'/|' $relative_kmod_list > $absolute_file_list

	if [ "$run_mod_deny" -eq 1 ]; then
            # run deny-mod script, this adds blacklist-* files to absolute_file_list
            %{SOURCE20} "$RPM_BUILD_ROOT" lib/modules/$KernelVer $absolute_file_list
	fi

%if %{zipmodules}
        # deny-mod script works with kmods as they are now (not compressed),
        # but if they will be we need to add compext to all
        sed -i %{?zipsed} $absolute_file_list
%endif
        # add also dir for the case when there are no kmods
        # "kernel" subdir is covered in %files section, skip it here
        if [ "$module_subdir" != "kernel" ]; then
                echo "%dir /lib/modules/$KernelVer/$module_subdir" >> $absolute_file_list
        fi

        if [ "$add_all_dirs" -eq 1 ]; then
            (cd $RPM_BUILD_ROOT; find lib/modules/$KernelVer/kernel -mindepth 1 -type d | sort -n) > ../module-dirs.list
            sed -e 's|^lib|%dir /lib|' ../module-dirs.list >> $absolute_file_list
        fi
    }

    if [ $DoModules -eq 1 ]; then
        # save modules.dep for debugging
        cp $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.dep ../

        %{log_msg "Create module list files for all kernel variants"}
        variants_param=""
        if [[ "$Variant" == "rt" || "$Variant" == "rt-debug" ]]; then
            variants_param="-r rt"
        fi
        # this creates ../modules-*.list output, where each kmod path is as it
        # appears in modules.dep (relative to lib/modules/$KernelVer)
        ret=0
        %{SOURCE22} -l "../filtermods-$KernelVer.log" sort -d $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.dep -c configs/def_variants.yaml $variants_param -o .. || ret=$?
        if [ $ret -ne 0 ]; then
            echo "8< --- filtermods-$KernelVer.log ---"
            cat "../filtermods-$KernelVer.log"
            echo "--- filtermods-$KernelVer.log --- >8"

            echo "8< --- modules.dep ---"
            cat $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.dep
            echo "--- modules.dep --- >8"
            exit 1
        fi

        create_module_file_list "kernel" ../modules-core.list ../kernel${Variant:+-${Variant}}-modules-core.list 1 0
        create_module_file_list "kernel" ../modules.list ../kernel${Variant:+-${Variant}}-modules.list 0 0
        create_module_file_list "internal" ../modules-internal.list ../kernel${Variant:+-${Variant}}-modules-internal.list 0 1
        create_module_file_list "kernel" ../modules-extra.list ../kernel${Variant:+-${Variant}}-modules-extra.list 0 1
        if [[ "$Variant" == "rt" || "$Variant" == "rt-debug" ]]; then
            create_module_file_list "kvm" ../modules-rt-kvm.list ../kernel${Variant:+-${Variant}}-modules-rt-kvm.list 0 1
        fi
%if 0%{!?fedora:1}
        create_module_file_list "partner" ../modules-partner.list ../kernel${Variant:+-${Variant}}-modules-partner.list 1 1
%endif
    fi # $DoModules -eq 1

    remove_depmod_files()
    {
        # remove files that will be auto generated by depmod at rpm -i time
        pushd $RPM_BUILD_ROOT/lib/modules/$KernelVer/
            # in case below list needs to be extended, remember to add a
            # matching ghost entry in the files section as well
            rm -f modules.{alias,alias.bin,builtin.alias.bin,builtin.bin} \
                  modules.{dep,dep.bin,devname,softdep,symbols,symbols.bin,weakdep}
        popd
    }

    # Cleanup
    %{log_msg "Cleanup build files"}
    rm -f $RPM_BUILD_ROOT/System.map
    %{log_msg "Remove depmod files"}
    remove_depmod_files

%if %{with_cross}
    make -C $RPM_BUILD_ROOT/lib/modules/$KernelVer/build M=scripts clean
    make -C $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/tools/bpf/resolve_btfids clean
    sed -i 's/REBUILD_SCRIPTS_FOR_CROSS:=0/REBUILD_SCRIPTS_FOR_CROSS:=1/' $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile
%endif

    # Move the devel headers out of the root file system
    %{log_msg "Move the devel headers to RPM_BUILD_ROOT"}
    mkdir -p $RPM_BUILD_ROOT/usr/src/kernels
    mv $RPM_BUILD_ROOT/lib/modules/$KernelVer/build $RPM_BUILD_ROOT/$DevelDir

    # This is going to create a broken link during the build, but we don't use
    # it after this point.  We need the link to actually point to something
    # when kernel-devel is installed, and a relative link doesn't work across
    # the F17 UsrMove feature.
    ln -sf $DevelDir $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    # Generate vmlinux.h and put it to kernel-devel path
    # zfcpdump build does not have btf anymore
    if [ "$Variant" != "zfcpdump" ]; then
	%{log_msg "Build the bootstrap bpftool to generate vmlinux.h"}
        # Build the bootstrap bpftool to generate vmlinux.h
        export BPFBOOTSTRAP_CFLAGS=$(echo "%{__global_compiler_flags}" | sed -r "s/\-specs=[^\ ]+\/redhat-annobin-cc1//")
        export BPFBOOTSTRAP_LDFLAGS=$(echo "%{__global_ldflags}" | sed -r "s/\-specs=[^\ ]+\/redhat-annobin-cc1//")
        CFLAGS="" LDFLAGS="" make EXTRA_CFLAGS="${BPFBOOTSTRAP_CFLAGS}" EXTRA_CXXFLAGS="${BPFBOOTSTRAP_CFLAGS}" EXTRA_LDFLAGS="${BPFBOOTSTRAP_LDFLAGS}" %{?make_opts} %{?clang_make_opts} V=1 -C tools/bpf/bpftool bootstrap

        tools/bpf/bpftool/bootstrap/bpftool btf dump file vmlinux format c > $RPM_BUILD_ROOT/$DevelDir/vmlinux.h
    fi

    %{log_msg "Cleanup kernel-devel and kernel-debuginfo files"}
    # prune junk from kernel-devel
    find $RPM_BUILD_ROOT/usr/src/kernels -name ".*.cmd" -delete
    # prune junk from kernel-debuginfo
    find $RPM_BUILD_ROOT/usr/src/kernels -name "*.mod.c" -delete

    # Red Hat UEFI Secure Boot CA cert, which can be used to authenticate the kernel
    %{log_msg "Install certs"}
    mkdir -p $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer
%if %{signkernel}
    install -m 0644 %{secureboot_ca_0} $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/kernel-signing-ca.cer
    %ifarch s390x ppc64le
    if [ -x /usr/bin/rpm-sign ]; then
        install -m 0644 %{secureboot_key_0} $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/%{signing_key_filename}
    fi
    %endif
%endif

%if 0%{?rhel}
    # Red Hat IMA code-signing cert, which is used to authenticate package files
    install -m 0644 %{ima_signing_cert} $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/%{ima_cert_name}
%endif

%if %{signmodules}
    if [ $DoModules -eq 1 ]; then
        # Save the signing keys so we can sign the modules in __modsign_install_post
        cp certs/signing_key.pem certs/signing_key.pem.sign${Variant:++${Variant}}
        cp certs/signing_key.x509 certs/signing_key.x509.sign${Variant:++${Variant}}
        %ifarch s390x ppc64le
        if [ ! -x /usr/bin/rpm-sign ]; then
            install -m 0644 certs/signing_key.x509.sign${Variant:++${Variant}} $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/kernel-signing-ca.cer
            openssl x509 -in certs/signing_key.pem.sign${Variant:++${Variant}} -outform der -out $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/%{signing_key_filename}
            chmod 0644 $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/%{signing_key_filename}
        fi
        %endif
    fi
%endif

%if %{with_ipaclones}
    %{log_msg "install IPA clones"}
    MAXPROCS=$(echo %{?_smp_mflags} | sed -n 's/-j\s*\([0-9]\+\)/\1/p')
    if [ -z "$MAXPROCS" ]; then
        MAXPROCS=1
    fi
    if [ "$Variant" == "" ]; then
        mkdir -p $RPM_BUILD_ROOT/$DevelDir-ipaclones
        find . -name '*.ipa-clones' | xargs -i{} -r -n 1 -P $MAXPROCS install -m 644 -D "{}" "$RPM_BUILD_ROOT/$DevelDir-ipaclones/{}"
    fi
%endif

%if %{with_gcov}
    popd
%endif
}

###
# DO it...
###

# prepare directories
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/boot
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}

cd linux-%{KVERREL}

%if %{with_debug}
%if %{with_realtime}
BuildKernel %make_target %kernel_image %{_use_vdso} rt-debug
%endif

%if %{with_arm64_16k}
BuildKernel %make_target %kernel_image %{_use_vdso} 16k-debug
%endif

%if %{with_arm64_64k}
BuildKernel %make_target %kernel_image %{_use_vdso} 64k-debug
%endif

%if %{with_up}
BuildKernel %make_target %kernel_image %{_use_vdso} debug
%endif
%endif

%if %{with_zfcpdump}
BuildKernel %make_target %kernel_image %{_use_vdso} zfcpdump
%endif

%if %{with_arm64_16k_base}
BuildKernel %make_target %kernel_image %{_use_vdso} 16k
%endif

%if %{with_arm64_64k_base}
BuildKernel %make_target %kernel_image %{_use_vdso} 64k
%endif

%if %{with_realtime_base}
BuildKernel %make_target %kernel_image %{_use_vdso} rt
%endif

%if %{with_up_base}
BuildKernel %make_target %kernel_image %{_use_vdso}
%endif

%ifnarch noarch i686 %{nobuildarches}
%if !%{with_debug} && !%{with_zfcpdump} && !%{with_up} && !%{with_arm64_16k} && !%{with_arm64_64k} && !%{with_realtime}
# If only building the user space tools, then initialize the build environment
# and some variables so that the various userspace tools can be built.
%{log_msg "Initialize userspace tools build environment"}
InitBuildVars
# Some tests build also modules, and need Module.symvers
if ! [[ -e Module.symvers ]] && [[ -f $DevelDir/Module.symvers ]]; then
    %{log_msg "Found Module.symvers in DevelDir, copying to ."}
    cp "$DevelDir/Module.symvers" .
fi
%endif
%endif

%ifarch aarch64
%global perf_build_extra_opts CORESIGHT=1
%endif
%global perf_make \
  %{__make} %{?make_opts} EXTRA_CFLAGS="${RPM_OPT_FLAGS}" EXTRA_CXXFLAGS="${RPM_OPT_FLAGS}" LDFLAGS="%{__global_ldflags} -Wl,-E" %{?cross_opts} -C tools/perf V=1 NO_PERF_READ_VDSO32=1 NO_PERF_READ_VDSOX32=1 WERROR=0 NO_LIBUNWIND=1 HAVE_CPLUS_DEMANGLE=1 NO_GTK2=1 NO_STRLCPY=1 NO_BIONIC=1 LIBBPF_DYNAMIC=1 LIBTRACEEVENT_DYNAMIC=1 %{?perf_build_extra_opts} prefix=%{_prefix} PYTHON=%{__python3}
%if %{with_perf}
%{log_msg "Build perf"}
# perf
# make sure check-headers.sh is executable
chmod +x tools/perf/check-headers.sh
%{perf_make} DESTDIR=$RPM_BUILD_ROOT all
%endif

%if %{with_libperf}
%global libperf_make \
  %{__make} %{?make_opts} EXTRA_CFLAGS="${RPM_OPT_FLAGS}" LDFLAGS="%{__global_ldflags}" %{?cross_opts} -C tools/lib/perf V=1
  %{log_msg "build libperf"}
%{libperf_make} DESTDIR=$RPM_BUILD_ROOT
%endif

%global tools_make \
  CFLAGS="${RPM_OPT_FLAGS}" LDFLAGS="%{__global_ldflags}" EXTRA_CFLAGS="${RPM_OPT_FLAGS}" %{make} %{?make_opts}

%if %{with_tools}
%ifarch %{cpupowerarchs}
# cpupower
# make sure version-gen.sh is executable.
chmod +x tools/power/cpupower/utils/version-gen.sh
%{log_msg "build cpupower"}
%{tools_make} %{?_smp_mflags} -C tools/power/cpupower CPUFREQ_BENCH=false DEBUG=false
%ifarch x86_64
    pushd tools/power/cpupower/debug/x86_64
    %{log_msg "build centrino-decode powernow-k8-decode"}
    %{tools_make} %{?_smp_mflags} centrino-decode powernow-k8-decode
    popd
%endif
%ifarch x86_64
   pushd tools/power/x86/x86_energy_perf_policy/
   %{log_msg "build x86_energy_perf_policy"}
   %{tools_make}
   popd
   pushd tools/power/x86/turbostat
   %{log_msg "build turbostat"}
   %{tools_make}
   popd
   pushd tools/power/x86/intel-speed-select
   %{log_msg "build intel-speed-select"}
   %{tools_make}
   popd
   pushd tools/arch/x86/intel_sdsi
   %{log_msg "build intel_sdsi"}
   %{tools_make} CFLAGS="${RPM_OPT_FLAGS}"
   popd
%endif
%endif
pushd tools/thermal/tmon/
%{log_msg "build tmon"}
%{tools_make}
popd
pushd tools/iio/
%{log_msg "build iio"}
%{tools_make}
popd
pushd tools/gpio/
%{log_msg "build gpio"}
%{tools_make}
popd
# build VM tools
pushd tools/mm/
%{log_msg "build slabinfo page_owner_sort"}
%{tools_make} slabinfo page_owner_sort
popd
pushd tools/verification/rv/
%{log_msg "build rv"}
%{tools_make}
popd
pushd tools/tracing/rtla
%{log_msg "build rtla"}
%{tools_make}
popd
%endif

if [ -f $DevelDir/vmlinux.h ]; then
  RPM_VMLINUX_H=$DevelDir/vmlinux.h
fi
echo "${RPM_VMLINUX_H}" > ../vmlinux_h_path

%if %{with_bpftool}
%global bpftool_make \
  %{__make} EXTRA_CFLAGS="${RPM_OPT_FLAGS}" EXTRA_CXXFLAGS="${RPM_OPT_FLAGS}" EXTRA_LDFLAGS="%{__global_ldflags}" DESTDIR=$RPM_BUILD_ROOT %{?make_opts} VMLINUX_H="${RPM_VMLINUX_H}" V=1
%{log_msg "build bpftool"}
pushd tools/bpf/bpftool
%{bpftool_make}
popd
%else
%{log_msg "bpftools disabled ... disabling selftests"}
%endif

%if %{with_selftests}
%{log_msg "start build selftests"}
# Unfortunately, samples/bpf/Makefile expects that the headers are installed
# in the source tree. We installed them previously to $RPM_BUILD_ROOT/usr
# but there's no way to tell the Makefile to take them from there.
%{log_msg "install headers for selftests"}
%{make} %{?_smp_mflags} headers_install

# If we re building only tools without kernel, we need to generate config
# headers and prepare tree for modules building. The modules_prepare target
# will cover both.
if [ ! -f include/generated/autoconf.h ]; then
   %{log_msg "modules_prepare for selftests"}
   %{make} %{?_smp_mflags} modules_prepare
fi

%{log_msg "build samples/bpf"}
%{make} %{?_smp_mflags} ARCH=$Arch V=1 M=samples/bpf/ VMLINUX_H="${RPM_VMLINUX_H}" || true

# Prevent bpf selftests to build bpftool repeatedly:
export BPFTOOL=$(pwd)/tools/bpf/bpftool/bpftool

pushd tools/testing/selftests
# We need to install here because we need to call make with ARCH set which
# doesn't seem possible to do in the install section.
%if %{selftests_must_build}
  force_targets="FORCE_TARGETS=1"
%else
  force_targets=""
%endif

%{log_msg "main selftests compile"}
%{make} %{?_smp_mflags} ARCH=$Arch V=1 TARGETS="bpf cgroup mm net net/forwarding net/mptcp netfilter tc-testing memfd drivers/net/bonding iommu cachestat" SKIP_TARGETS="" $force_targets INSTALL_PATH=%{buildroot}%{_libexecdir}/kselftests VMLINUX_H="${RPM_VMLINUX_H}" install

%ifarch %{klptestarches}
	# kernel livepatching selftest test_modules will build against
	# /lib/modules/$(shell uname -r)/build tree unless KDIR is set
	export KDIR=$(realpath $(pwd)/../../..)
	%{make} %{?_smp_mflags} ARCH=$Arch V=1 TARGETS="livepatch" SKIP_TARGETS="" $force_targets INSTALL_PATH=%{buildroot}%{_libexecdir}/kselftests VMLINUX_H="${RPM_VMLINUX_H}" install || true
%endif

# 'make install' for bpf is broken and upstream refuses to fix it.
# Install the needed files manually.
%{log_msg "install selftests"}
for dir in bpf bpf/no_alu32 bpf/progs; do
	# In ARK, the rpm build continues even if some of the selftests
	# cannot be built. It's not always possible to build selftests,
	# as upstream sometimes dependens on too new llvm version or has
	# other issues. If something did not get built, just skip it.
	test -d $dir || continue
	mkdir -p %{buildroot}%{_libexecdir}/kselftests/$dir
	find $dir -maxdepth 1 -type f \( -executable -o -name '*.py' -o -name settings -o \
		-name 'btf_dump_test_case_*.c' -o -name '*.ko' -o \
		-name '*.o' -exec sh -c 'readelf -h "{}" | grep -q "^  Machine:.*BPF"' \; \) -print0 | \
	xargs -0 cp -t %{buildroot}%{_libexecdir}/kselftests/$dir || true
done
%buildroot_save_unstripped "usr/libexec/kselftests/bpf/test_progs"
%buildroot_save_unstripped "usr/libexec/kselftests/bpf/test_progs-no_alu32"
popd
export -n BPFTOOL
%{log_msg "end build selftests"}
%endif

%if %{with_doc}
%{log_msg "start install docs"}
# Make the HTML pages.
%{log_msg "build html docs"}
%{__make} PYTHON=/usr/bin/python3 htmldocs || %{doc_build_fail}

# sometimes non-world-readable files sneak into the kernel source tree
chmod -R a=rX Documentation
find Documentation -type d | xargs chmod u+w
%{log_msg "end install docs"}
%endif

# Module signing (modsign)
#
# This must be run _after_ find-debuginfo.sh runs, otherwise that will strip
# the signature off of the modules.
#
# Don't sign modules for the zfcpdump variant as it is monolithic.

%define __modsign_install_post \
  if [ "%{signmodules}" -eq "1" ]; then \
    %{log_msg "Signing kernel modules ..."} \
    modules_dirs="$(shopt -s nullglob; echo $RPM_BUILD_ROOT/lib/modules/%{KVERREL}*)" \
    for modules_dir in $modules_dirs; do \
        variant_suffix="${modules_dir#$RPM_BUILD_ROOT/lib/modules/%{KVERREL}}" \
        [ "$variant_suffix" == "+zfcpdump" ] && continue \
	%{log_msg "Signing modules for %{KVERREL}${variant_suffix}"} \
        %{modsign_cmd} certs/signing_key.pem.sign${variant_suffix} certs/signing_key.x509.sign${variant_suffix} $modules_dir/ \
    done \
  fi \
  if [ "%{zipmodules}" -eq "1" ]; then \
    %{log_msg "Compressing kernel modules ..."} \
    find $RPM_BUILD_ROOT/lib/modules/ -type f -name '*.ko' | xargs -n 16 -P${RPM_BUILD_NCPUS} -r %compression %compression_flags; \
  fi \
%{nil}

###
### Special hacks for debuginfo subpackages.
###

# This macro is used by %%install, so we must redefine it before that.
%define debug_package %{nil}

%if %{with_debuginfo}

%ifnarch noarch %{nobuildarches}
%global __debug_package 1
%files -f debugfiles.list debuginfo-common-%{_target_cpu}
%endif

%endif

# We don't want to package debuginfo for self-tests and samples but
# we have to delete them to avoid an error messages about unpackaged
# files.
# Delete the debuginfo for kernel-devel files
%define __remove_unwanted_dbginfo_install_post \
  if [ "%{with_selftests}" -ne "0" ]; then \
    rm -rf $RPM_BUILD_ROOT/usr/lib/debug/usr/libexec/ksamples; \
    rm -rf $RPM_BUILD_ROOT/usr/lib/debug/usr/libexec/kselftests; \
  fi \
  rm -rf $RPM_BUILD_ROOT/usr/lib/debug/usr/src; \
%{nil}

#
# Disgusting hack alert! We need to ensure we sign modules *after* all
# invocations of strip occur, which is in __debug_install_post if
# find-debuginfo.sh runs, and __os_install_post if not.
#
%define __spec_install_post \
  %{?__debug_package:%{__debug_install_post}}\
  %{__arch_install_post}\
  %{__os_install_post}\
  %{__remove_unwanted_dbginfo_install_post}\
  %{__restore_unstripped_root_post}\
  %{__modsign_install_post}

###
### install
###

%install

cd linux-%{KVERREL}

# re-define RPM_VMLINUX_H, because it doesn't carry over from %build
RPM_VMLINUX_H="$(cat ../vmlinux_h_path)"

%if %{with_doc}
docdir=$RPM_BUILD_ROOT%{_datadir}/doc/kernel-doc-%{specversion}-%{pkgrelease}

# copy the source over
mkdir -p $docdir
tar -h -f - --exclude=man --exclude='.*' -c Documentation | tar xf - -C $docdir
cat %{SOURCE2} | xz > $docdir/kernel.changelog.xz
chmod 0644 $docdir/kernel.changelog.xz

# with_doc
%endif

# We have to do the headers install before the tools install because the
# kernel headers_install will remove any header files in /usr/include that
# it doesn't install itself.

%if %{with_headers}
# Install kernel headers
%{__make} ARCH=%{hdrarch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_install

find $RPM_BUILD_ROOT/usr/include \
     \( -name .install -o -name .check -o \
        -name ..install.cmd -o -name ..check.cmd \) -delete

%endif

%if %{with_cross_headers}
HDR_ARCH_LIST='arm64 powerpc s390 x86'
mkdir -p $RPM_BUILD_ROOT/usr/tmp-headers

for arch in $HDR_ARCH_LIST; do
	mkdir $RPM_BUILD_ROOT/usr/tmp-headers/arch-${arch}
	%{__make} ARCH=${arch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr/tmp-headers/arch-${arch} headers_install
done

find $RPM_BUILD_ROOT/usr/tmp-headers \
     \( -name .install -o -name .check -o \
        -name ..install.cmd -o -name ..check.cmd \) -delete

# Copy all the architectures we care about to their respective asm directories
for arch in $HDR_ARCH_LIST ; do
	mkdir -p $RPM_BUILD_ROOT/usr/${arch}-linux-gnu/include
	mv $RPM_BUILD_ROOT/usr/tmp-headers/arch-${arch}/include/* $RPM_BUILD_ROOT/usr/${arch}-linux-gnu/include/
done

rm -rf $RPM_BUILD_ROOT/usr/tmp-headers
%endif

%if %{with_kernel_abi_stablelists}
# kabi directory
INSTALL_KABI_PATH=$RPM_BUILD_ROOT/lib/modules/
mkdir -p $INSTALL_KABI_PATH

# install kabi releases directories
tar -xvf %{SOURCE300} -C $INSTALL_KABI_PATH
# with_kernel_abi_stablelists
%endif

%if %{with_perf}
# perf tool binary and supporting scripts/binaries
%{perf_make} DESTDIR=$RPM_BUILD_ROOT lib=%{_lib} install-bin
# remove the 'trace' symlink.
rm -f %{buildroot}%{_bindir}/trace

# For both of the below, yes, this should be using a macro but right now
# it's hard coded and we don't actually want it anyway right now.
# Whoever wants examples can fix it up!

# remove examples
rm -rf %{buildroot}/usr/lib/perf/examples
rm -rf %{buildroot}/usr/lib/perf/include

# python-perf extension
%{perf_make} DESTDIR=$RPM_BUILD_ROOT install-python_ext

# perf man pages (note: implicit rpm magic compresses them later)
mkdir -p %{buildroot}/%{_mandir}/man1
%{perf_make} DESTDIR=$RPM_BUILD_ROOT install-man

# remove any tracevent files, eg. its plugins still gets built and installed,
# even if we build against system's libtracevent during perf build (by setting
# LIBTRACEEVENT_DYNAMIC=1 above in perf_make macro). Those files should already
# ship with libtraceevent package.
rm -rf %{buildroot}%{_libdir}/traceevent
%endif

%if %{with_libperf}
%{libperf_make} DESTDIR=%{buildroot} prefix=%{_prefix} libdir=%{_libdir} install install_headers
# This is installed on some arches and we don't want to ship it
rm -rf %{buildroot}%{_libdir}/libperf.a
%endif

%if %{with_tools}
%ifarch %{cpupowerarchs}
%{make} -C tools/power/cpupower DESTDIR=$RPM_BUILD_ROOT libdir=%{_libdir} mandir=%{_mandir} CPUFREQ_BENCH=false install
rm -f %{buildroot}%{_libdir}/*.{a,la}
%find_lang cpupower
mv cpupower.lang ../
%ifarch x86_64
    pushd tools/power/cpupower/debug/x86_64
    install -m755 centrino-decode %{buildroot}%{_bindir}/centrino-decode
    install -m755 powernow-k8-decode %{buildroot}%{_bindir}/powernow-k8-decode
    popd
%endif
chmod 0755 %{buildroot}%{_libdir}/libcpupower.so*
%endif
%ifarch x86_64
   mkdir -p %{buildroot}%{_mandir}/man8
   pushd tools/power/x86/x86_energy_perf_policy
   %{tools_make} DESTDIR=%{buildroot} install
   popd
   pushd tools/power/x86/turbostat
   %{tools_make} DESTDIR=%{buildroot} install
   popd
   pushd tools/power/x86/intel-speed-select
   %{tools_make} DESTDIR=%{buildroot} install
   popd
   pushd tools/arch/x86/intel_sdsi
   %{tools_make} CFLAGS="${RPM_OPT_FLAGS}" DESTDIR=%{buildroot} install
   popd
%endif
pushd tools/thermal/tmon
%{tools_make} INSTALL_ROOT=%{buildroot} install
popd
pushd tools/iio
%{tools_make} DESTDIR=%{buildroot} install
popd
pushd tools/gpio
%{tools_make} DESTDIR=%{buildroot} install
popd
install -m644 -D %{SOURCE2002} %{buildroot}%{_sysconfdir}/logrotate.d/kvm_stat
pushd tools/kvm/kvm_stat
%{__make} INSTALL_ROOT=%{buildroot} install-tools
%{__make} INSTALL_ROOT=%{buildroot} install-man
install -m644 -D kvm_stat.service %{buildroot}%{_unitdir}/kvm_stat.service
popd
# install VM tools
pushd tools/mm/
install -m755 slabinfo %{buildroot}%{_bindir}/slabinfo
install -m755 page_owner_sort %{buildroot}%{_bindir}/page_owner_sort
popd
pushd tools/verification/rv/
%{tools_make} DESTDIR=%{buildroot} install
popd
pushd tools/tracing/rtla/
%{tools_make} DESTDIR=%{buildroot} install
rm -f %{buildroot}%{_bindir}/hwnoise
rm -f %{buildroot}%{_bindir}/osnoise
rm -f %{buildroot}%{_bindir}/timerlat
(cd %{buildroot}

        ln -sf rtla ./%{_bindir}/hwnoise
        ln -sf rtla ./%{_bindir}/osnoise
        ln -sf rtla ./%{_bindir}/timerlat
)
popd
%endif

%if %{with_bpftool}
pushd tools/bpf/bpftool
%{bpftool_make} prefix=%{_prefix} bash_compdir=%{_sysconfdir}/bash_completion.d/ mandir=%{_mandir} install doc-install
popd
%endif

%if %{with_selftests}
pushd samples
install -d %{buildroot}%{_libexecdir}/ksamples
# install bpf samples
pushd bpf
install -d %{buildroot}%{_libexecdir}/ksamples/bpf
find -type f -executable -exec install -m755 {} %{buildroot}%{_libexecdir}/ksamples/bpf \;
install -m755 *.sh %{buildroot}%{_libexecdir}/ksamples/bpf
# test_lwt_bpf.sh compiles test_lwt_bpf.c when run; this works only from the
# kernel tree. Just remove it.
rm %{buildroot}%{_libexecdir}/ksamples/bpf/test_lwt_bpf.sh
install -m644 *_kern.o %{buildroot}%{_libexecdir}/ksamples/bpf || true
install -m644 tcp_bpf.readme %{buildroot}%{_libexecdir}/ksamples/bpf
popd
# install pktgen samples
pushd pktgen
install -d %{buildroot}%{_libexecdir}/ksamples/pktgen
find . -type f -executable -exec install -m755 {} %{buildroot}%{_libexecdir}/ksamples/pktgen/{} \;
find . -type f ! -executable -exec install -m644 {} %{buildroot}%{_libexecdir}/ksamples/pktgen/{} \;
popd
popd
# install mm selftests
pushd tools/testing/selftests/mm
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/mm/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/mm/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/mm/{} \;
popd
# install cgroup selftests
pushd tools/testing/selftests/cgroup
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/cgroup/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/cgroup/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/cgroup/{} \;
popd
# install drivers/net/mlxsw selftests
pushd tools/testing/selftests/drivers/net/mlxsw
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/drivers/net/mlxsw/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/drivers/net/mlxsw/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/drivers/net/mlxsw/{} \;
popd
# install drivers/net/netdevsim selftests
pushd tools/testing/selftests/drivers/net/netdevsim
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/drivers/net/netdevsim/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/drivers/net/netdevsim/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/drivers/net/netdevsim/{} \;
popd
# install drivers/net/bonding selftests
pushd tools/testing/selftests/drivers/net/bonding
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/drivers/net/bonding/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/drivers/net/bonding/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/drivers/net/bonding/{} \;
popd
# install net/forwarding selftests
pushd tools/testing/selftests/net/forwarding
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/net/forwarding/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/net/forwarding/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/net/forwarding/{} \;
popd
# install net/mptcp selftests
pushd tools/testing/selftests/net/mptcp
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/net/mptcp/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/net/mptcp/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/net/mptcp/{} \;
popd
# install tc-testing selftests
pushd tools/testing/selftests/tc-testing
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/tc-testing/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/tc-testing/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/tc-testing/{} \;
popd
# install livepatch selftests
pushd tools/testing/selftests/livepatch
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/livepatch/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/livepatch/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/livepatch/{} \;
popd
# install netfilter selftests
pushd tools/testing/selftests/netfilter
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/netfilter/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/netfilter/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/netfilter/{} \;
popd

# install memfd selftests
pushd tools/testing/selftests/memfd
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/memfd/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/memfd/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/memfd/{} \;
popd
# install iommu selftests
pushd tools/testing/selftests/iommu
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/iommu/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/iommu/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/iommu/{} \;
popd
%endif

###
### clean
###

###
### scripts
###

%if %{with_tools}
%post -n %{package_name}-tools-libs
/sbin/ldconfig

%postun -n %{package_name}-tools-libs
/sbin/ldconfig
%endif

#
# This macro defines a %%post script for a kernel*-devel package.
#	%%kernel_devel_post [<subpackage>]
# Note we don't run hardlink if ostree is in use, as ostree is
# a far more sophisticated hardlink implementation.
# https://github.com/projectatomic/rpm-ostree/commit/58a79056a889be8814aa51f507b2c7a4dccee526
#
# The deletion of *.hardlink-temporary files is a temporary workaround
# for this bug in the hardlink binary (fixed in util-linux 2.38):
# https://github.com/util-linux/util-linux/issues/1602
#
%define kernel_devel_post() \
%{expand:%%post %{?1:%{1}-}devel}\
if [ -f /etc/sysconfig/kernel ]\
then\
    . /etc/sysconfig/kernel || exit $?\
fi\
if [ "$HARDLINK" != "no" -a -x /usr/bin/hardlink -a ! -e /run/ostree-booted ] \
then\
    (cd /usr/src/kernels/%{KVERREL}%{?1:+%{1}} &&\
     /usr/bin/find . -type f | while read f; do\
       hardlink -c /usr/src/kernels/*%{?dist}.*/$f $f > /dev/null\
     done;\
     /usr/bin/find /usr/src/kernels -type f -name '*.hardlink-temporary' -delete\
    )\
fi\
%if %{with_cross}\
    echo "Building scripts and resolve_btfids"\
    env --unset=ARCH make -C /usr/src/kernels/%{KVERREL}%{?1:+%{1}} prepare_after_cross\
%endif\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-extra package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_extra_post [<subpackage>]
#
%define kernel_modules_extra_post() \
%{expand:%%post %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-internal package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_internal_post [<subpackage>]
#
%define kernel_modules_internal_post() \
%{expand:%%post %{?1:%{1}-}modules-internal}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-internal}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-partner package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_partner_post [<subpackage>]
#
%define kernel_modules_partner_post() \
%{expand:%%post %{?1:%{1}-}modules-partner}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-partner}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

%if %{with_realtime}
#
# This macro defines a %%post script for a kernel*-kvm package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_kvm_post [<subpackage>]
#
%define kernel_kvm_post() \
%{expand:%%post %{?1:%{1}-}kvm}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}kvm}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}
%endif

#
# This macro defines a %%post script for a kernel*-modules package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_post [<subpackage>]
#
%define kernel_modules_post() \
%{expand:%%post %{?1:%{1}-}modules}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
if [ ! -f %{_localstatedir}/lib/rpm-state/%{name}/installing_core_%{KVERREL}%{?1:+%{1}} ]; then\
	mkdir -p %{_localstatedir}/lib/rpm-state/%{name}\
	touch %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}}\
fi\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%posttrans %{?1:%{1}-}modules}\
if [ -f %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}} ]; then\
	rm -f %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}}\
	echo "Running: dracut -f --kver %{KVERREL}%{?1:+%{1}}"\
	dracut -f --kver "%{KVERREL}%{?1:+%{1}}" || exit $?\
fi\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-core package.
#	%%kernel_modules_core_post [<subpackage>]
#
%define kernel_modules_core_post() \
%{expand:%%posttrans %{?1:%{1}-}modules-core}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

# This macro defines a %%posttrans script for a kernel package.
#	%%kernel_variant_posttrans [-v <subpackage>] [-u uki-suffix]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_posttrans(v:u:) \
%{expand:%%posttrans %{?-v:%{-v*}-}%{!?-u*:core}%{?-u*:uki-%{-u*}}}\
%if 0%{!?fedora:1}\
if [ -x %{_sbindir}/weak-modules ]\
then\
    %{_sbindir}/weak-modules --add-kernel %{KVERREL}%{?-v:+%{-v*}} || exit $?\
fi\
%endif\
rm -f %{_localstatedir}/lib/rpm-state/%{name}/installing_core_%{KVERREL}%{?-v:+%{-v*}}\
/bin/kernel-install add %{KVERREL}%{?-v:+%{-v*}} /lib/modules/%{KVERREL}%{?-v:+%{-v*}}/vmlinuz%{?-u:-%{-u*}.efi} || exit $?\
if [[ ! -e "/boot/symvers-%{KVERREL}%{?-v:+%{-v*}}.%compext" ]]; then\
    cp "/lib/modules/%{KVERREL}%{?-v:+%{-v*}}/symvers.%compext" "/boot/symvers-%{KVERREL}%{?-v:+%{-v*}}.%compext"\
    if command -v restorecon &>/dev/null; then\
        restorecon "/boot/symvers-%{KVERREL}%{?-v:+%{-v*}}.%compext"\
    fi\
fi\
%{nil}

#
# This macro defines a %%post script for a kernel package and its devel package.
#	%%kernel_variant_post [-v <subpackage>] [-r <replace>]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_post(v:r:) \
%{expand:%%kernel_devel_post %{?-v*}}\
%{expand:%%kernel_modules_post %{?-v*}}\
%{expand:%%kernel_modules_core_post %{?-v*}}\
%{expand:%%kernel_modules_extra_post %{?-v*}}\
%{expand:%%kernel_modules_internal_post %{?-v*}}\
%if 0%{!?fedora:1}\
%{expand:%%kernel_modules_partner_post %{?-v*}}\
%endif\
%{expand:%%kernel_variant_posttrans %{?-v*:-v %{-v*}}}\
%{expand:%%post %{?-v*:%{-v*}-}core}\
%{-r:\
if [ `uname -i` == "x86_64" -o `uname -i` == "i386" ] &&\
   [ -f /etc/sysconfig/kernel ]; then\
  /bin/sed -r -i -e 's/^DEFAULTKERNEL=%{-r*}$/DEFAULTKERNEL=kernel%{?-v:-%{-v*}}/' /etc/sysconfig/kernel || exit $?\
fi}\
mkdir -p %{_localstatedir}/lib/rpm-state/%{name}\
touch %{_localstatedir}/lib/rpm-state/%{name}/installing_core_%{KVERREL}%{?-v:+%{-v*}}\
%{nil}

#
# This macro defines a %%preun script for a kernel package.
#	%%kernel_variant_preun [-v <subpackage>] -u [uki-suffix]
#
%define kernel_variant_preun(v:u:) \
%{expand:%%preun %{?-v:%{-v*}-}%{!?-u*:core}%{?-u*:uki-%{-u*}}}\
/bin/kernel-install remove %{KVERREL}%{?-v:+%{-v*}} || exit $?\
if [ -x %{_sbindir}/weak-modules ]\
then\
    %{_sbindir}/weak-modules --remove-kernel %{KVERREL}%{?-v:+%{-v*}} || exit $?\
fi\
%{nil}

%if %{with_up_base} && %{with_efiuki}
%kernel_variant_posttrans -u virt
%kernel_variant_preun -u virt
%endif

%if %{with_up_base}
%kernel_variant_preun
%kernel_variant_post
%endif

%if %{with_zfcpdump}
%kernel_variant_preun -v zfcpdump
%kernel_variant_post -v zfcpdump
%endif

%if %{with_up} && %{with_debug} && %{with_efiuki}
%kernel_variant_posttrans -v debug -u virt
%kernel_variant_preun -v debug -u virt
%endif

%if %{with_up} && %{with_debug}
%kernel_variant_preun -v debug
%kernel_variant_post -v debug
%endif

%if %{with_arm64_16k_base}
%kernel_variant_preun -v 16k
%kernel_variant_post -v 16k
%endif

%if %{with_debug} && %{with_arm64_16k}
%kernel_variant_preun -v 16k-debug
%kernel_variant_post -v 16k-debug
%endif

%if %{with_arm64_16k} && %{with_debug} && %{with_efiuki}
%kernel_variant_posttrans -v 16k-debug -u virt
%kernel_variant_preun -v 16k-debug -u virt
%endif

%if %{with_arm64_16k_base} && %{with_efiuki}
%kernel_variant_posttrans -v 16k -u virt
%kernel_variant_preun -v 16k -u virt
%endif

%if %{with_arm64_64k_base}
%kernel_variant_preun -v 64k
%kernel_variant_post -v 64k
%endif

%if %{with_debug} && %{with_arm64_64k}
%kernel_variant_preun -v 64k-debug
%kernel_variant_post -v 64k-debug
%endif

%if %{with_arm64_64k} && %{with_debug} && %{with_efiuki}
%kernel_variant_posttrans -v 64k-debug -u virt
%kernel_variant_preun -v 64k-debug -u virt
%endif

%if %{with_arm64_64k_base} && %{with_efiuki}
%kernel_variant_posttrans -v 64k -u virt
%kernel_variant_preun -v 64k -u virt
%endif

%if %{with_realtime_base}
%kernel_variant_preun -v rt
%kernel_variant_post -v rt -r kernel
%kernel_kvm_post rt
%endif

%if %{with_realtime} && %{with_debug}
%kernel_variant_preun -v rt-debug
%kernel_variant_post -v rt-debug
%kernel_kvm_post rt-debug
%endif

###
### file lists
###

%if %{with_headers}
%files headers
/usr/include/*
%exclude %{_includedir}/cpufreq.h
%endif

%if %{with_cross_headers}
%files cross-headers
/usr/*-linux-gnu/include/*
%endif

%if %{with_kernel_abi_stablelists}
%files -n %{package_name}-abi-stablelists
/lib/modules/kabi-*
%endif

%if %{with_kabidw_base}
%ifarch x86_64 s390x ppc64 ppc64le aarch64
%files kernel-kabidw-base-internal
%defattr(-,root,root)
/kabidw-base/%{_target_cpu}/*
%endif
%endif

# only some architecture builds need kernel-doc
%if %{with_doc}
%files doc
%defattr(-,root,root)
%{_datadir}/doc/kernel-doc-%{specversion}-%{pkgrelease}/Documentation/*
%dir %{_datadir}/doc/kernel-doc-%{specversion}-%{pkgrelease}/Documentation
%dir %{_datadir}/doc/kernel-doc-%{specversion}-%{pkgrelease}
%{_datadir}/doc/kernel-doc-%{specversion}-%{pkgrelease}/kernel.changelog.xz
%endif

%if %{with_perf}
%files -n perf
%{_bindir}/perf
%{_libdir}/libperf-jvmti.so
%dir %{_libexecdir}/perf-core
%{_libexecdir}/perf-core/*
%{_datadir}/perf-core/*
%{_mandir}/man[1-8]/perf*
%{_sysconfdir}/bash_completion.d/perf
%doc linux-%{KVERREL}/tools/perf/Documentation/examples.txt
%{_docdir}/perf-tip/tips.txt

%files -n python3-perf
%{python3_sitearch}/*

%if %{with_debuginfo}
%files -f perf-debuginfo.list -n perf-debuginfo

%files -f python3-perf-debuginfo.list -n python3-perf-debuginfo
%endif
# with_perf
%endif

%if %{with_libperf}
%files -n libperf
%{_libdir}/libperf.so.0
%{_libdir}/libperf.so.0.0.1

%files -n libperf-devel
%{_libdir}/libperf.so
%{_libdir}/pkgconfig/libperf.pc
%{_includedir}/internal/*.h
%{_includedir}/perf/bpf_perf.h
%{_includedir}/perf/core.h
%{_includedir}/perf/cpumap.h
%{_includedir}/perf/perf_dlfilter.h
%{_includedir}/perf/event.h
%{_includedir}/perf/evlist.h
%{_includedir}/perf/evsel.h
%{_includedir}/perf/mmap.h
%{_includedir}/perf/threadmap.h
%{_mandir}/man3/libperf.3.gz
%{_mandir}/man7/libperf-counting.7.gz
%{_mandir}/man7/libperf-sampling.7.gz
%{_docdir}/libperf/examples/sampling.c
%{_docdir}/libperf/examples/counting.c
%{_docdir}/libperf/html/libperf.html
%{_docdir}/libperf/html/libperf-counting.html
%{_docdir}/libperf/html/libperf-sampling.html

%if %{with_debuginfo}
%files -f libperf-debuginfo.list -n libperf-debuginfo
%endif

# with_libperf
%endif


%if %{with_tools}
%ifnarch %{cpupowerarchs}
%files -n %{package_name}-tools
%else
%files -n %{package_name}-tools -f cpupower.lang
%{_bindir}/cpupower
%{_datadir}/bash-completion/completions/cpupower
%ifarch x86_64
%{_bindir}/centrino-decode
%{_bindir}/powernow-k8-decode
%endif
%{_mandir}/man[1-8]/cpupower*
%ifarch x86_64
%{_bindir}/x86_energy_perf_policy
%{_mandir}/man8/x86_energy_perf_policy*
%{_bindir}/turbostat
%{_mandir}/man8/turbostat*
%{_bindir}/intel-speed-select
%{_sbindir}/intel_sdsi
%endif
# cpupowerarchs
%endif
%{_bindir}/tmon
%{_bindir}/iio_event_monitor
%{_bindir}/iio_generic_buffer
%{_bindir}/lsiio
%{_bindir}/lsgpio
%{_bindir}/gpio-hammer
%{_bindir}/gpio-event-mon
%{_bindir}/gpio-watch
%{_mandir}/man1/kvm_stat*
%{_bindir}/kvm_stat
%{_unitdir}/kvm_stat.service
%config(noreplace) %{_sysconfdir}/logrotate.d/kvm_stat
%{_bindir}/page_owner_sort
%{_bindir}/slabinfo

%if %{with_debuginfo}
%files -f %{package_name}-tools-debuginfo.list -n %{package_name}-tools-debuginfo
%endif

%ifarch %{cpupowerarchs}
%files -n %{package_name}-tools-libs
%{_libdir}/libcpupower.so.1
%{_libdir}/libcpupower.so.0.0.1

%files -n %{package_name}-tools-libs-devel
%{_libdir}/libcpupower.so
%{_includedir}/cpufreq.h
%{_includedir}/cpuidle.h
%{_includedir}/powercap.h
%endif

%files -n rtla
%{_bindir}/rtla
%{_bindir}/hwnoise
%{_bindir}/osnoise
%{_bindir}/timerlat
%{_mandir}/man1/rtla-hwnoise.1.gz
%{_mandir}/man1/rtla-osnoise-hist.1.gz
%{_mandir}/man1/rtla-osnoise-top.1.gz
%{_mandir}/man1/rtla-osnoise.1.gz
%{_mandir}/man1/rtla-timerlat-hist.1.gz
%{_mandir}/man1/rtla-timerlat-top.1.gz
%{_mandir}/man1/rtla-timerlat.1.gz
%{_mandir}/man1/rtla.1.gz

%files -n rv
%{_bindir}/rv
%{_mandir}/man1/rv-list.1.gz
%{_mandir}/man1/rv-mon-wip.1.gz
%{_mandir}/man1/rv-mon-wwnr.1.gz
%{_mandir}/man1/rv-mon.1.gz
%{_mandir}/man1/rv.1.gz

# with_tools
%endif

%if %{with_bpftool}
%files -n bpftool
%{_sbindir}/bpftool
%{_sysconfdir}/bash_completion.d/bpftool
%{_mandir}/man8/bpftool-cgroup.8.gz
%{_mandir}/man8/bpftool-gen.8.gz
%{_mandir}/man8/bpftool-iter.8.gz
%{_mandir}/man8/bpftool-link.8.gz
%{_mandir}/man8/bpftool-map.8.gz
%{_mandir}/man8/bpftool-prog.8.gz
%{_mandir}/man8/bpftool-perf.8.gz
%{_mandir}/man8/bpftool.8.gz
%{_mandir}/man8/bpftool-net.8.gz
%{_mandir}/man8/bpftool-feature.8.gz
%{_mandir}/man8/bpftool-btf.8.gz
%{_mandir}/man8/bpftool-struct_ops.8.gz

%if %{with_debuginfo}
%files -f bpftool-debuginfo.list -n bpftool-debuginfo
%defattr(-,root,root)
%endif
%endif

%if %{with_selftests}
%files selftests-internal
%{_libexecdir}/ksamples
%{_libexecdir}/kselftests
%endif

# empty meta-package
%if %{with_up_base}
%ifnarch %nobuildarches noarch
%files
%endif
%endif

# This is %%{image_install_path} on an arch where that includes ELF files,
# or empty otherwise.
%define elf_image_install_path %{?kernel_image_elf:%{image_install_path}}

#
# This macro defines the %%files sections for a kernel package
# and its devel and debuginfo packages.
#	%%kernel_variant_files [-k vmlinux] <use_vdso> <condition> <subpackage>
#
%define kernel_variant_files(k:) \
%if %{2}\
%{expand:%%files %{?1:-f kernel-%{?3:%{3}-}ldsoconf.list} %{?3:%{3}-}core}\
%{!?_licensedir:%global license %%doc}\
%%license linux-%{KVERREL}/COPYING-%{version}-%{release}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}\
%ghost /%{image_install_path}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-%{KVERREL}%{?3:+%{3}}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/.vmlinuz.hmac \
%ghost /%{image_install_path}/.vmlinuz-%{KVERREL}%{?3:+%{3}}.hmac \
%ifarch aarch64\
/lib/modules/%{KVERREL}%{?3:+%{3}}/dtb \
%ghost /%{image_install_path}/dtb-%{KVERREL}%{?3:+%{3}} \
%endif\
/lib/modules/%{KVERREL}%{?3:+%{3}}/System.map\
%ghost /boot/System.map-%{KVERREL}%{?3:+%{3}}\
%dir /lib/modules\
%dir /lib/modules/%{KVERREL}%{?3:+%{3}}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/symvers.%compext\
/lib/modules/%{KVERREL}%{?3:+%{3}}/config\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.builtin*\
%ghost %attr(0644, root, root) /boot/symvers-%{KVERREL}%{?3:+%{3}}.%compext\
%ghost %attr(0600, root, root) /boot/initramfs-%{KVERREL}%{?3:+%{3}}.img\
%ghost %attr(0644, root, root) /boot/config-%{KVERREL}%{?3:+%{3}}\
%{expand:%%files -f kernel-%{?3:%{3}-}modules-core.list %{?3:%{3}-}modules-core}\
%dir /lib/modules\
%dir /lib/modules/%{KVERREL}%{?3:+%{3}}\
%dir /lib/modules/%{KVERREL}%{?3:+%{3}}/kernel\
/lib/modules/%{KVERREL}%{?3:+%{3}}/build\
/lib/modules/%{KVERREL}%{?3:+%{3}}/source\
/lib/modules/%{KVERREL}%{?3:+%{3}}/updates\
/lib/modules/%{KVERREL}%{?3:+%{3}}/weak-updates\
/lib/modules/%{KVERREL}%{?3:+%{3}}/systemtap\
%{_datadir}/doc/kernel-keys/%{KVERREL}%{?3:+%{3}}\
%if %{1}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/vdso\
%endif\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.block\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.drm\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.modesetting\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.networking\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.order\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.alias\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.alias.bin\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.builtin.alias.bin\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.builtin.bin\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.dep\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.dep.bin\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.devname\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.softdep\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.symbols\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.symbols.bin\
%ghost %attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/modules.weakdep\
%{expand:%%files -f kernel-%{?3:%{3}-}modules.list %{?3:%{3}-}modules}\
%{expand:%%files %{?3:%{3}-}devel}\
%defverify(not mtime)\
/usr/src/kernels/%{KVERREL}%{?3:+%{3}}\
%{expand:%%files %{?3:%{3}-}devel-matched}\
%{expand:%%files -f kernel-%{?3:%{3}-}modules-extra.list %{?3:%{3}-}modules-extra}\
%{expand:%%files -f kernel-%{?3:%{3}-}modules-internal.list %{?3:%{3}-}modules-internal}\
%if 0%{!?fedora:1}\
%{expand:%%files -f kernel-%{?3:%{3}-}modules-partner.list %{?3:%{3}-}modules-partner}\
%endif\
%if %{with_debuginfo}\
%ifnarch noarch\
%{expand:%%files -f debuginfo%{?3}.list %{?3:%{3}-}debuginfo}\
%endif\
%endif\
%if "%{3}" == "rt" || "%{3}" == "rt-debug"\
%{expand:%%files -f kernel-%{?3:%{3}-}modules-rt-kvm.list %{?3:%{3}-}kvm}\
%else\
%if %{with_efiuki}\
%{expand:%%files %{?3:%{3}-}uki-virt}\
%dir /lib/modules\
%dir /lib/modules/%{KVERREL}%{?3:+%{3}}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/System.map\
/lib/modules/%{KVERREL}%{?3:+%{3}}/symvers.%compext\
/lib/modules/%{KVERREL}%{?3:+%{3}}/config\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.builtin*\
%attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-virt.efi\
%attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/.%{?-k:%{-k*}}%{!?-k:vmlinuz}-virt.efi.hmac\
%ghost /%{image_install_path}/efi/EFI/Linux/%{?-k:%{-k*}}%{!?-k:*}-%{KVERREL}%{?3:+%{3}}.efi\
%{expand:%%files %{?3:%{3}-}uki-virt-addons}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-virt.efi.extra.d/ \
/lib/modules/%{KVERREL}%{?3:+%{3}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-virt.efi.extra.d/*.addon.efi\
%endif\
%endif\
%if %{?3:1} %{!?3:0}\
%{expand:%%files %{3}}\
%endif\
%if %{with_gcov}\
%ifnarch %nobuildarches noarch\
%{expand:%%files -f kernel-%{?3:%{3}-}gcov.list %{?3:%{3}-}gcov}\
%endif\
%endif\
%endif\
%{nil}

%kernel_variant_files %{_use_vdso} %{with_up_base}
%if %{with_up}
%kernel_variant_files %{_use_vdso} %{with_debug} debug
%endif
%if %{with_arm64_16k}
%kernel_variant_files %{_use_vdso} %{with_debug} 16k-debug
%endif
%if %{with_arm64_64k}
%kernel_variant_files %{_use_vdso} %{with_debug} 64k-debug
%endif
%kernel_variant_files %{_use_vdso} %{with_realtime_base} rt
%if %{with_realtime}
%kernel_variant_files %{_use_vdso} %{with_debug} rt-debug
%endif
%if %{with_debug_meta}
%files debug
%files debug-core
%files debug-devel
%files debug-devel-matched
%files debug-modules
%files debug-modules-core
%files debug-modules-extra
%if %{with_arm64_16k}
%files 16k-debug
%files 16k-debug-core
%files 16k-debug-devel
%files 16k-debug-devel-matched
%files 16k-debug-modules
%files 16k-debug-modules-extra
%endif
%if %{with_arm64_64k}
%files 64k-debug
%files 64k-debug-core
%files 64k-debug-devel
%files 64k-debug-devel-matched
%files 64k-debug-modules
%files 64k-debug-modules-extra
%endif
%endif
%kernel_variant_files %{_use_vdso} %{with_zfcpdump} zfcpdump
%kernel_variant_files %{_use_vdso} %{with_arm64_16k_base} 16k
%kernel_variant_files %{_use_vdso} %{with_arm64_64k_base} 64k

%define kernel_variant_ipaclones(k:) \
%if %{1}\
%if %{with_ipaclones}\
%{expand:%%files %{?2:%{2}-}ipaclones-internal}\
%defattr(-,root,root)\
%defverify(not mtime)\
/usr/src/kernels/%{KVERREL}%{?2:+%{2}}-ipaclones\
%endif\
%endif\
%{nil}

%kernel_variant_ipaclones %{with_up_base}

# plz don't put in a version string unless you're going to tag
# and build.
#
#
%changelog
* Tue Sep 03 2024 Patrick Talbert <ptalbert@redhat.com> [6.11.0-0.rc6.23.el10]
- ata: libata: Fix memory leak for error path in ata_host_alloc() (Zheng Qixing)
- x86/resctrl: Fix arch_mbm_* array overrun on SNC (Peter Newman)
- x86/tdx: Fix data leak in mmio_read() (Kirill A. Shutemov)
- x86/kaslr: Expose and use the end of the physical memory address space (Thomas Gleixner)
- x86/fpu: Avoid writing LBR bit to IA32_XSS unless supported (Mitchell Levy)
- x86/apic: Make x2apic_disable() work correctly (Yuntao Wang)
- perf/x86/intel: Limit the period on Haswell (Kan Liang)
- rtmutex: Drop rt_mutex::wait_lock before scheduling (Roland Xu)
- irqchip/irq-msi-lib: Check for NULL ops in msi_lib_irq_domain_select() (Maxime Chevallier)
- irqchip/gic-v3: Init SRE before poking sysregs (Mark Rutland)
- irqchip/gic-v2m: Fix refcount leak in gicv2m_of_init() (Ma Ke)
- irqchip/riscv-aplic: Fix an IS_ERR() vs NULL bug in probe() (Dan Carpenter)
- irqchip/gic-v4: Fix ordering between vmapp and vpe locks (Marc Zyngier)
- irqchip/sifive-plic: Probe plic driver early for Allwinner D1 platform (Anup Patel)
- Linux 6.11-rc6 (Linus Torvalds)
- cifs: Fix FALLOC_FL_ZERO_RANGE to preflush buffered part of target region (David Howells)
- cifs: Fix copy offload to flush destination region (David Howells)
- netfs, cifs: Fix handling of short DIO read (David Howells)
- cifs: Fix lack of credit renegotiation on read retry (David Howells)
- bcachefs: Mark more errors as autofix (Kent Overstreet)
- bcachefs: Revert lockless buffered IO path (Kent Overstreet)
- bcachefs: Fix bch2_extents_match() false positive (Kent Overstreet)
- bcachefs: Fix failure to return error in data_update_index_update() (Kent Overstreet)
- apparmor: fix policy_unpack_test on big endian systems (Guenter Roeck)
- Revert "MIPS: csrc-r4k: Apply verification clocksource flags" (Guenter Roeck)
- microblaze: don't treat zero reserved memory regions as error (Mike Rapoport)
- power: sequencing: qcom-wcn: set the wlan-enable GPIO to output (Bartosz Golaszewski)
- USB: serial: option: add MeiG Smart SRM825L (ZHANG Yuntian)
- usb: cdnsp: fix for Link TRB with TC (Pawel Laszczak)
- usb: dwc3: st: add missing depopulate in probe error path (Krzysztof Kozlowski)
- usb: dwc3: st: fix probed platform device ref count on probe error path (Krzysztof Kozlowski)
- usb: dwc3: ep0: Don't reset resource alloc flag (including ep0) (Michael Grzeschik)
- usb: core: sysfs: Unmerge @usb3_hardware_lpm_attr_group in remove_power_attributes() (Zijun Hu)
- usb: typec: fsa4480: Relax CHIP_ID check (Luca Weiss)
- usb: dwc3: xilinx: add missing depopulate in probe error path (Krzysztof Kozlowski)
- usb: dwc3: omap: add missing depopulate in probe error path (Krzysztof Kozlowski)
- dt-bindings: usb: microchip,usb2514: Fix reference USB device schema (Alexander Stein)
- usb: gadget: uvc: queue pump work in uvcg_video_enable() (Xu Yang)
- cdc-acm: Add DISABLE_ECHO quirk for GE HealthCare UI Controller (Ian Ray)
- usb: cdnsp: fix incorrect index in cdnsp_get_hw_deq function (Pawel Laszczak)
- usb: dwc3: core: Prevent USB core invalid event buffer address access (Selvarasu Ganesan)
- MAINTAINERS: Mark UVC gadget driver as orphan (Laurent Pinchart)
- scsi: sd: Ignore command SYNCHRONIZE CACHE error if format in progress (Yihang Li)
- scsi: aacraid: Fix double-free on probe failure (Ben Hutchings)
- scsi: lpfc: Fix overflow build issue (Sherry Yang)
- nfsd: fix nfsd4_deleg_getattr_conflict in presence of third party lease (NeilBrown)
- xfs: reset rootdir extent size hint after growfsrt (Darrick J. Wong)
- xfs: take m_growlock when running growfsrt (Darrick J. Wong)
- xfs: Fix missing interval for missing_owner in xfs fsmap (Zizhi Wo)
- xfs: use XFS_BUF_DADDR_NULL for daddrs in getfsmap code (Darrick J. Wong)
- xfs: Fix the owner setting issue for rmap query in xfs fsmap (Zizhi Wo)
- xfs: don't bother reporting blocks trimmed via FITRIM (Darrick J. Wong)
- xfs: xfs_finobt_count_blocks() walks the wrong btree (Dave Chinner)
- xfs: fix folio dirtying for XFILE_ALLOC callers (Darrick J. Wong)
- xfs: fix di_onlink checking for V1/V2 inodes (Darrick J. Wong)
- MAINTAINERS: Update DTS path for ARM/Microchip (AT91) SoC (Andrei Simion)
- firmware: microchip: fix incorrect error report of programming:timeout on success (Steve Wilkins)
- arm64: dts: qcom: x1e80100: Fix Adreno SMMU global interrupt (Konrad Dybcio)
- arm64: dts: qcom: disable GPU on x1e80100 by default (Dmitry Baryshkov)
- arm64: dts: qcom: x1e80100-crd: Fix backlight (Stephan Gerhold)
- arm64: dts: qcom: x1e80100-yoga-slim7x: fix missing PCIe4 gpios (Johan Hovold)
- arm64: dts: qcom: x1e80100-yoga-slim7x: disable PCIe6a perst pull down (Johan Hovold)
- arm64: dts: qcom: x1e80100-yoga-slim7x: fix up PCIe6a pinctrl node (Johan Hovold)
- arm64: dts: qcom: x1e80100-yoga-slim7x: fix PCIe4 PHY supply (Johan Hovold)
- arm64: dts: qcom: x1e80100-vivobook-s15: fix missing PCIe4 gpios (Johan Hovold)
- arm64: dts: qcom: x1e80100-vivobook-s15: disable PCIe6a perst pull down (Johan Hovold)
- arm64: dts: qcom: x1e80100-vivobook-s15: fix up PCIe6a pinctrl node (Johan Hovold)
- arm64: dts: qcom: x1e80100-vivobook-s15: fix PCIe4 PHY supply (Johan Hovold)
- arm64: dts: qcom: x1e80100-qcp: fix missing PCIe4 gpios (Johan Hovold)
- arm64: dts: qcom: x1e80100-qcp: disable PCIe6a perst pull down (Johan Hovold)
- arm64: dts: qcom: x1e80100-qcp: fix up PCIe6a pinctrl node (Johan Hovold)
- arm64: dts: qcom: x1e80100-qcp: fix PCIe4 PHY supply (Johan Hovold)
- arm64: dts: qcom: x1e80100-crd: fix missing PCIe4 gpios (Johan Hovold)
- arm64: dts: qcom: x1e80100-crd: disable PCIe6a perst pull down (Johan Hovold)
- arm64: dts: qcom: x1e80100-crd: fix up PCIe6a pinctrl node (Johan Hovold)
- arm64: dts: qcom: x1e80100: add missing PCIe minimum OPP (Johan Hovold)
- arm64: dts: qcom: x1e80100: fix PCIe domain numbers (Johan Hovold)
- arm64: dts: qcom: x1e80100-crd: fix PCIe4 PHY supply (Johan Hovold)
- arm64: dts: qcom: ipq5332: Fix interrupt trigger type for usb (Varadarajan Narayanan)
- arm64: dts: qcom: x1e80100-yoga: add wifi calibration variant (Patrick Wildt)
- arm64: defconfig: Add CONFIG_DRM_PANEL_SAMSUNG_ATNA33XC20 (Stephan Gerhold)
- soc: qcom: pd-mapper: Fix singleton refcount (Bjorn Andersson)
- firmware: qcom: tzmem: disable sdm670 platform (Richard Acayan)
- soc: qcom: pmic_glink: Actually communicate when remote goes down (Bjorn Andersson)
- usb: typec: ucsi: Move unregister out of atomic section (Bjorn Andersson)
- soc: qcom: pmic_glink: Fix race during initialization (Bjorn Andersson)
- firmware: qcom: qseecom: remove unused functions (Bartosz Golaszewski)
- firmware: qcom: tzmem: fix virtual-to-physical address conversion (Bartosz Golaszewski)
- firmware: qcom: scm: Mark get_wq_ctx() as atomic call (Murali Nalajala)
- MAINTAINERS: Update Konrad Dybcio's email address (Konrad Dybcio)
- mailmap: Add an entry for Konrad Dybcio (Konrad Dybcio)
- soc: qcom: pd-mapper: mark qcom_pdm_domains as __maybe_unused (Arnd Bergmann)
- soc: qcom: cmd-db: Map shared memory as WC, not WB (Volodymyr Babchuk)
- soc: qcom: pd-mapper: Depend on ARCH_QCOM || COMPILE_TEST (Andrew Halaney)
- arm64: dts: imx8mm-phygate: fix typo pinctrcl-0 (Frank Li)
- arm64: dts: imx95: correct L3Cache cache-sets (Peng Fan)
- arm64: dts: imx95: correct a55 power-domains (Peng Fan)
- arm64: dts: freescale: imx93-tqma9352-mba93xxla: fix typo (Markus Niebel)
- arm64: dts: freescale: imx93-tqma9352: fix CMA alloc-ranges (Markus Niebel)
- ARM: dts: imx6dl-yapp43: Increase LED current to match the yapp4 HW design (Michal Vokáč)
- arm64: dts: imx93: update default value for snps,clk-csr (Shenwei Wang)
- arm64: dts: freescale: tqma9352: Fix watchdog reset (Sascha Hauer)
- arm64: dts: imx8mp-beacon-kit: Fix Stereo Audio on WM8962 (Adam Ford)
- arm64: dts: layerscape: fix thermal node names length (Krzysztof Kozlowski)
- ARM: dts: omap3-n900: correct the accelerometer orientation (Sicelo A. Mhlongo)
- Input: cypress_ps2 - fix waiting for command response (Dmitry Torokhov)
- MAINTAINERS: PCI: Add NXP PCI controller mailing list imx@lists.linux.dev (Frank Li)
- PCI: qcom: Use OPP only if the platform supports it (Manivannan Sadhasivam)
- PCI: qcom-ep: Disable MHI RAM data parity error interrupt for SA8775P SoC (Manivannan Sadhasivam)
- MAINTAINERS: Add Manivannan Sadhasivam as Reviewer for PCI native host bridge and endpoint drivers (Manivannan Sadhasivam)
- block: fix detection of unsupported WRITE SAME in blkdev_issue_write_zeroes (Darrick J. Wong)
- io_uring/kbuf: return correct iovec count from classic buffer peek (Jens Axboe)
- io_uring/rsrc: ensure compat iovecs are copied correctly (Jens Axboe)
- selinux,smack: don't bypass permissions check in inode_setsecctx hook (Scott Mayhew)
- cpufreq/amd-pstate-ut: Don't check for highest perf matching on prefcore (Mario Limonciello)
- cpufreq/amd-pstate: Use topology_logical_package_id() instead of logical_die_id() (Gautham R. Shenoy)
- cpufreq: amd-pstate: Fix uninitialized variable in amd_pstate_cpu_boost_update() (Dan Carpenter)
- dmaengine: dw-edma: Do not enable watermark interrupts for HDMA (Mrinmay Sarkar)
- dmaengine: dw-edma: Fix unmasking STOP and ABORT interrupts for HDMA (Mrinmay Sarkar)
- dmaengine: stm32-dma3: Set lli_size after allocation (Kees Cook)
- dmaengine: ti: omap-dma: Initialize sglen after allocation (Kees Cook)
- dmaengine: dw: Unify ret-val local variables naming (Serge Semin)
- dmaengine: dw: Simplify max-burst calculation procedure (Serge Semin)
- dmaengine: dw: Define encode_maxburst() above prepare_ctllo() callbacks (Serge Semin)
- dmaengine: dw: Simplify prepare CTL_LO methods (Serge Semin)
- dmaengine: dw: Add memory bus width verification (Serge Semin)
- dmaengine: dw: Add peripheral bus width verification (Serge Semin)
- phy: xilinx: phy-zynqmp: Fix SGMII linkup failure on resume (Piyush Mehta)
- phy: exynos5-usbdrd: fix error code in probe() (Dan Carpenter)
- phy: fsl-imx8mq-usb: fix tuning parameter name (Xu Yang)
- phy: qcom: qmp-pcie: Fix X1E80100 PCIe Gen4 PHY initialisation (Abel Vesa)
- soundwire: stream: fix programming slave ports for non-continous port maps (Krzysztof Kozlowski)
- MAINTAINERS: Add Jean-Philippe as SMMUv3 SVA reviewer (Will Deacon)
- iommu: Do not return 0 from map_pages if it doesn't do anything (Jason Gunthorpe)
- iommufd: Do not allow creating areas without READ or WRITE (Jason Gunthorpe)
- iommu/vt-d: Fix incorrect domain ID in context flush helper (Lu Baolu)
- iommu: Handle iommu faults for a bad iopf setup (Pranjal Shrivastava)
- Remove CONFIG_FSCACHE_DEBUG as it has been renamed (Justin M. Forbes)
- Set Fedora configs for 6.11 (Justin M. Forbes)
- drm/v3d: Disable preemption while updating GPU stats (Tvrtko Ursulin)
- video/aperture: optionally match the device in sysfb_disable() (Alex Deucher)
- drm/vmwgfx: Disable coherent dumb buffers without 3d (Zack Rusin)
- drm/vmwgfx: Fix prime with external buffers (Zack Rusin)
- drm/vmwgfx: Prevent unmapping active read buffers (Zack Rusin)
- Revert "drm/ttm: increase ttm pre-fault value to PMD size" (Alex Deucher)
- drm/xe/hwmon: Fix WRITE_I1 param from u32 to u16 (Karthik Poosa)
- drm/xe: Invalidate media_gt TLBs (Matthew Brost)
- drm/i915/dp_mst: Fix MST state after a sink reset (Imre Deak)
- drm/i915: ARL requires a newer GSC firmware (John Harrison)
- drm/i915/dsi: Make Lenovo Yoga Tab 3 X90F DMI match less strict (Hans de Goede)
- drm/amd/pm: Drop unsupported features on smu v14_0_2 (Candice Li)
- drm/amd/pm: Add support for new P2S table revision (Lijo Lazar)
- drm/amdgpu: support for gc_info table v1.3 (Likun Gao)
- drm/amd/display: avoid using null object of framebuffer (Ma Ke)
- drm/amdgpu/gfx12: set UNORD_DISPATCH in compute MQDs (Alex Deucher)
- drm/amd/pm: update message interface for smu v14.0.2/3 (Kenneth Feng)
- drm/amdgpu/swsmu: always force a state reprogram on init (Alex Deucher)
- drm/amdgpu/smu13.0.7: print index for profiles (Alex Deucher)
- drm/amdgpu: align pp_power_profile_mode with kernel docs (Alex Deucher)
- binfmt_elf_fdpic: fix AUXV size calculation when ELF_HWCAP2 is defined (Max Filippov)
- dcache: keep dentry_hashtable or d_hash_shift even when not used (Stephen Brennan)
- hwmon: (pt5161l) Fix invalid temperature reading (Cosmo Chou)
- hwmon: (asus-ec-sensors) remove VRM temp X570-E GAMING (Ross Brown)
- nfc: pn533: Add poll mod list filling check (Aleksandr Mishin)
- netfilter: nf_tables_ipv6: consider network offset in netdev/egress validation (Pablo Neira Ayuso)
- netfilter: nf_tables: restore IP sanity checks for netdev/egress (Pablo Neira Ayuso)
- mailmap: update entry for Sriram Yagnaraman (Sriram Yagnaraman)
- selftests: mptcp: join: check re-re-adding ID 0 signal (Matthieu Baerts (NGI0))
- mptcp: pm: ADD_ADDR 0 is not a new address (Matthieu Baerts (NGI0))
- selftests: mptcp: join: validate event numbers (Matthieu Baerts (NGI0))
- mptcp: avoid duplicated SUB_CLOSED events (Matthieu Baerts (NGI0))
- selftests: mptcp: join: check re-re-adding ID 0 endp (Matthieu Baerts (NGI0))
- mptcp: pm: fix ID 0 endp usage after multiple re-creations (Matthieu Baerts (NGI0))
- mptcp: pm: do not remove already closed subflows (Matthieu Baerts (NGI0))
- selftests: mptcp: join: no extra msg if no counter (Matthieu Baerts (NGI0))
- selftests: mptcp: join: check re-adding init endp with != id (Matthieu Baerts (NGI0))
- mptcp: pm: reset MPC endp ID when re-added (Matthieu Baerts (NGI0))
- mptcp: pm: skip connecting to already established sf (Matthieu Baerts (NGI0))
- mptcp: pm: send ACK on an active subflow (Matthieu Baerts (NGI0))
- selftests: mptcp: join: check removing ID 0 endpoint (Matthieu Baerts (NGI0))
- mptcp: pm: fix RM_ADDR ID for the initial subflow (Matthieu Baerts (NGI0))
- mptcp: pm: reuse ID 0 after delete and re-add (Matthieu Baerts (NGI0))
- net: busy-poll: use ktime_get_ns() instead of local_clock() (Eric Dumazet)
- wifi: iwlwifi: clear trans->state earlier upon error (Emmanuel Grumbach)
- wifi: wfx: repair open network AP mode (Alexander Sverdlin)
- wifi: mac80211: free skb on error path in ieee80211_beacon_get_ap() (Dmitry Antipov)
- wifi: iwlwifi: mvm: don't wait for tx queues if firmware is dead (Emmanuel Grumbach)
- wifi: iwlwifi: mvm: allow 6 GHz channels in MLO scan (Avraham Stern)
- wifi: iwlwifi: mvm: pause TCM when the firmware is stopped (Emmanuel Grumbach)
- wifi: iwlwifi: fw: fix wgds rev 3 exact size (Anjaneyulu)
- wifi: iwlwifi: mvm: take the mutex before running link selection (Emmanuel Grumbach)
- wifi: iwlwifi: mvm: fix iwl_mvm_max_scan_ie_fw_cmd_room() (Daniel Gabay)
- wifi: iwlwifi: mvm: fix iwl_mvm_scan_fits() calculation (Daniel Gabay)
- wifi: iwlwifi: lower message level for FW buffer destination (Benjamin Berg)
- wifi: iwlwifi: mvm: fix hibernation (Emmanuel Grumbach)
- wifi: mac80211: fix beacon SSID mismatch handling (Daniel Gabay)
- wifi: mwifiex: duplicate static structs used in driver instances (Sascha Hauer)
- sctp: fix association labeling in the duplicate COOKIE-ECHO case (Ondrej Mosnacek)
- mptcp: pr_debug: add missing \n at the end (Matthieu Baerts (NGI0))
- mptcp: sched: check both backup in retrans (Matthieu Baerts (NGI0))
- selftests: mptcp: join: cannot rm sf if closed (Matthieu Baerts (NGI0))
- mptcp: close subflow when receiving TCP+FIN (Matthieu Baerts (NGI0))
- tcp: fix forever orphan socket caused by tcp_abort (Xueming Feng)
- gtp: fix a potential NULL pointer dereference (Cong Wang)
- bonding: change ipsec_lock from spin lock to mutex (Jianbo Liu)
- bonding: extract the use of real_device into local variable (Jianbo Liu)
- bonding: implement xdo_dev_state_free and call it after deletion (Jianbo Liu)
- selftests: forwarding: local_termination: Down ports on cleanup (Petr Machata)
- selftests: forwarding: no_forwarding: Down ports on cleanup (Petr Machata)
- net_sched: sch_fq: fix incorrect behavior for small weights (Eric Dumazet)
- ionic: Prevent tx_timeout due to frequent doorbell ringing (Brett Creeley)
- net: ti: icssg-prueth: Fix 10M Link issue on AM64x (MD Danish Anwar)
- ethtool: check device is present when getting link settings (Jamie Bainbridge)
- Bluetooth: hci_core: Fix not handling hibernation actions (Luiz Augusto von Dentz)
- Bluetooth: btnxpuart: Fix random crash seen while removing driver (Neeraj Sanjay Kale)
- Bluetooth: btintel: Allow configuring drive strength of BRI (Kiran K)
- net: ftgmac100: Ensure tx descriptor updates are visible (Jacky Chou)
- net: mana: Fix race of mana_hwc_post_rx_wqe and new hwc response (Haiyang Zhang)
- net: drop special comment style (Johannes Berg)
- pktgen: use cpus_read_lock() in pg_net_init() (Eric Dumazet)
- random: vDSO: reject unknown getrandom() flags (Yann Droneaud)
- LoongArch: KVM: Invalidate guest steal time address on vCPU reset (Bibo Mao)
- LoongArch: Add ifdefs to fix LSX and LASX related warnings (Tiezhu Yang)
- LoongArch: Define ARCH_IRQ_INIT_FLAGS as IRQ_NOPROBE (Huacai Chen)
- LoongArch: Remove the unused dma-direct.h (Miao Wang)
- platform/x86: x86-android-tablets: Make Lenovo Yoga Tab 3 X90F DMI match less strict (Hans de Goede)
- platform/x86: asus-wmi: Fix spurious rfkill on UX8406MA (Mathieu Fenniak)
- platform/x86/amd/pmc: Extend support for PMC features on new AMD platform (Shyam Sundar S K)
- platform/x86/amd/pmc: Fix SMU command submission path on new AMD platform (Shyam Sundar S K)
- fs/nfsd: fix update of inode attrs in CB_GETATTR (Jeff Layton)
- nfsd: fix potential UAF in nfsd4_cb_getattr_release (Jeff Layton)
- nfsd: hold reference to delegation when updating it for cb_getattr (Jeff Layton)
- MAINTAINERS: Update Olga Kornievskaia's email address (Chuck Lever)
- nfsd: prevent panic for nfsv4.0 closed files in nfs4_show_open (Olga Kornievskaia)
- nfsd: ensure that nfsd4_fattr_args.context is zeroed out (Jeff Layton)
- btrfs: fix uninitialized return value from btrfs_reclaim_sweep() (Filipe Manana)
- btrfs: fix a use-after-free when hitting errors inside btrfs_submit_chunk() (Qu Wenruo)
- btrfs: initialize last_extent_end to fix -Wmaybe-uninitialized warning in extent_fiemap() (David Sterba)
- btrfs: run delayed iputs when flushing delalloc (Josef Bacik)
- redhat/configs: Microchip lan743x driver (Izabela Bakollari)
- v6.11-rc5-rt5 (Sebastian Andrzej Siewior)
- printk: Update John's printk series. (Sebastian Andrzej Siewior)
- netfilter: nft_counter: Use u64_stats_t for statistic. (Sebastian Andrzej Siewior)
- v6.11-rc5-rt4 (Sebastian Andrzej Siewior)
- cifs: Fix FALLOC_FL_PUNCH_HOLE support (David Howells)
- smb/client: fix rdma usage in smb2_async_writev() (Stefan Metzmacher)
- smb/client: remove unused rq_iter_size from struct smb_rqst (Stefan Metzmacher)
- smb/client: avoid dereferencing rdata=NULL in smb2_new_read_req() (Stefan Metzmacher)
- tpm: ibmvtpm: Call tpm2_sessions_init() to initialize session support (Stefan Berger)
- selftests/livepatch: wait for atomic replace to occur (Ryan Sullivan)
- pinctrl: rockchip: correct RK3328 iomux width flag for GPIO2-B pins (Huang-Huang Bao)
- pinctrl: starfive: jh7110: Correct the level trigger configuration of iev register (Hal Feng)
- pinctrl: qcom: x1e80100: Fix special pin offsets (Konrad Dybcio)
- pinctrl: mediatek: common-v2: Fix broken bias-disable for PULL_PU_PD_RSEL_TYPE (Nícolas F. R. A. Prado)
- pinctrl: single: fix potential NULL dereference in pcs_get_function() (Ma Ke)
- pinctrl: at91: make it work with current gpiolib (Thomas Blocher)
- pinctrl: qcom: x1e80100: Update PDC hwirq map (Konrad Dybcio)
- ALSA: hda: hda_component: Fix mutex crash if nothing ever binds (Richard Fitzgerald)
- ALSA: hda/realtek: support HP Pavilion Aero 13-bg0xxx Mute LED (Hendrik Borghorst)
- ALSA: hda/realtek: Fix the speaker output on Samsung Galaxy Book3 Ultra (YOUNGJIN JOO)
- ASoC: cs-amp-lib: Ignore empty UEFI calibration entries (Richard Fitzgerald)
- ASoC: cs-amp-lib-test: Force test calibration blob entries to be valid (Richard Fitzgerald)
- ASoC: allow module autoloading for table board_ids (Hongbo Li)
- ASoC: allow module autoloading for table db1200_pids (Hongbo Li)
- ASoC: SOF: amd: Fix for acp init sequence (Vijendar Mukunda)
- ASoC: amd: acp: fix module autoloading (Yuntao Liu)
- ASoC: mediatek: mt8188: Mark AFE_DAC_CON0 register as volatile (YR Yang)
- ASoC: codecs: wcd937x: Fix missing de-assert of reset GPIO (Krzysztof Kozlowski)
- ASoC: SOF: mediatek: Add missing board compatible (Albert Jakieła)
- ASoC: MAINTAINERS: Drop Banajit Goswami from Qualcomm sound drivers (Krzysztof Kozlowski)
- ASoC: SOF: amd: Fix for incorrect acp error register offsets (Vijendar Mukunda)
- ASoC: SOF: amd: move iram-dram fence register programming sequence (Vijendar Mukunda)
- ASoC: codecs: lpass-va-macro: warn on unknown version (Dmitry Baryshkov)
- ASoC: codecs: lpass-macro: fix version strings returned for 1.x codecs (Dmitry Baryshkov)
- ALSA: hda/realtek - FIxed ALC285 headphone no sound (Kailang Yang)
- ALSA: hda/realtek - Fixed ALC256 headphone no sound (Kailang Yang)
- ALSA: hda: cs35l56: Don't use the device index as a calibration index (Simon Trimmer)
- ALSA: seq: Skip event type filtering for UMP events (Takashi Iwai)
- ALSA: hda/realtek: Enable mute/micmute LEDs on HP Laptop 14-ey0xxx (John Sweeney)
- redhat: include resolve_btfids in kernel-devel (Jan Stancek)
- redhat: workaround CKI cross compilation for scripts (Jan Stancek)
- spec: fix "unexpected argument to non-parametric macro" warnings (Jan Stancek)
- Linux v6.11.0-0.rc6

* Tue Aug 27 2024 Jan Stancek <jstancek@redhat.com> [6.11.0-0.rc5.22.el10]
- netfs: Fix interaction of streaming writes with zero-point tracker (David Howells)
- netfs: Fix missing iterator reset on retry of short read (David Howells)
- netfs: Fix trimming of streaming-write folios in netfs_inval_folio() (David Howells)
- netfs: Fix netfs_release_folio() to say no if folio dirty (David Howells)
- afs: Fix post-setattr file edit to do truncation correctly (David Howells)
- mm: Fix missing folio invalidation calls during truncation (David Howells)
- ovl: ovl_parse_param_lowerdir: Add missed '\n' for pr_err (Zhihao Cheng)
- ovl: fix wrong lowerdir number check for parameter Opt_lowerdir (Zhihao Cheng)
- ovl: pass string to ovl_parse_layer() (Christian Brauner)
- backing-file: convert to using fops->splice_write (Ed Tsai)
- Revert "pidfd: prevent creation of pidfds for kthreads" (Christian Brauner)
- romfs: fix romfs_read_folio() (Christian Brauner)
- netfs, ceph: Partially revert "netfs: Replace PG_fscache by setting folio->private and marking dirty" (David Howells)
- Add weakdep support to the kernel spec (Justin M. Forbes)
- redhat: configs: disable PF_KEY in RHEL (Sabrina Dubroca)
- crypto: akcipher - Disable signing and decryption (Vladis Dronov) [RHEL-54183] {CVE-2023-6240}
- crypto: dh - implement FIPS PCT (Vladis Dronov) [RHEL-54183]
- crypto: ecdh - disallow plain "ecdh" usage in FIPS mode (Vladis Dronov) [RHEL-54183]
- crypto: seqiv - flag instantiations as FIPS compliant (Vladis Dronov) [RHEL-54183]
- [kernel] bpf: set default value for bpf_jit_harden (Artem Savkov) [RHEL-51896]
- Linux v6.11.0-0.rc5

* Mon Aug 26 2024 Jan Stancek <jstancek@redhat.com> [6.11.0-0.rc5.21.el10]
- Linux 6.11-rc5 (Linus Torvalds)
- bcachefs: Fix rebalance_work accounting (Kent Overstreet)
- bcachefs: Fix failure to flush moves before sleeping in copygc (Kent Overstreet)
- bcachefs: don't use rht_bucket() in btree_key_cache_scan() (Kent Overstreet)
- bcachefs: add missing inode_walker_exit() (Kent Overstreet)
- bcachefs: clear path->should_be_locked in bch2_btree_key_cache_drop() (Kent Overstreet)
- bcachefs: Fix double assignment in check_dirent_to_subvol() (Yuesong Li)
- bcachefs: Fix refcounting in discard path (Kent Overstreet)
- bcachefs: Fix compat issue with old alloc_v4 keys (Kent Overstreet)
- bcachefs: Fix warning in bch2_fs_journal_stop() (Kent Overstreet)
- fs/super.c: improve get_tree() error message (Kent Overstreet)
- bcachefs: Fix missing validation in bch2_sb_journal_v2_validate() (Kent Overstreet)
- bcachefs: Fix replay_now_at() assert (Kent Overstreet)
- bcachefs: Fix locking in bch2_ioc_setlabel() (Kent Overstreet)
- bcachefs: fix failure to relock in btree_node_fill() (Kent Overstreet)
- bcachefs: fix failure to relock in bch2_btree_node_mem_alloc() (Kent Overstreet)
- bcachefs: unlock_long() before resort in journal replay (Kent Overstreet)
- bcachefs: fix missing bch2_err_str() (Kent Overstreet)
- bcachefs: fix time_stats_to_text() (Kent Overstreet)
- bcachefs: Fix bch2_bucket_gens_init() (Kent Overstreet)
- bcachefs: Fix bch2_trigger_alloc assert (Kent Overstreet)
- bcachefs: Fix failure to relock in btree_node_get() (Kent Overstreet)
- bcachefs: setting bcachefs_effective.* xattrs is a noop (Kent Overstreet)
- bcachefs: Fix "trying to move an extent, but nr_replicas=0" (Kent Overstreet)
- bcachefs: bch2_data_update_init() cleanup (Kent Overstreet)
- bcachefs: Extra debug for data move path (Kent Overstreet)
- bcachefs: Fix incorrect gfp flags (Kent Overstreet)
- bcachefs: fix field-spanning write warning (Kent Overstreet)
- bcachefs: Reallocate table when we're increasing size (Kent Overstreet)
- smb/server: update misguided comment of smb2_allocate_rsp_buf() (ChenXiaoSong)
- smb/server: remove useless assignment of 'file_present' in smb2_open() (ChenXiaoSong)
- smb/server: fix potential null-ptr-deref of lease_ctx_info in smb2_open() (ChenXiaoSong)
- smb/server: fix return value of smb2_open() (ChenXiaoSong)
- ksmbd: the buffer of smb2 query dir response has at least 1 byte (Namjae Jeon)
- s390/boot: Fix KASLR base offset off by __START_KERNEL bytes (Alexander Gordeev)
- s390/boot: Avoid possible physmem_info segment corruption (Alexander Gordeev)
- s390/ap: Refine AP bus bindings complete processing (Harald Freudenberger)
- s390/mm: Pin identity mapping base to zero (Alexander Gordeev)
- s390/mm: Prevent lowcore vs identity mapping overlap (Alexander Gordeev)
- scsi: sd: Do not attempt to configure discard unless LBPME is set (Martin K. Petersen)
- scsi: MAINTAINERS: Add header files to SCSI SUBSYSTEM (Simon Horman)
- scsi: ufs: qcom: Add UFSHCD_QUIRK_BROKEN_LSDBS_CAP for SM8550 SoC (Manivannan Sadhasivam)
- scsi: ufs: core: Add a quirk for handling broken LSDBS field in controller capabilities register (Manivannan Sadhasivam)
- scsi: core: Fix the return value of scsi_logical_block_count() (Chaotian Jing)
- scsi: MAINTAINERS: Update HiSilicon SAS controller driver maintainer (Yihang Li)
- cgroup/cpuset: Eliminate unncessary sched domains rebuilds in hotplug (Waiman Long)
- cgroup/cpuset: Clear effective_xcpus on cpus_allowed clearing only if cpus.exclusive not set (Waiman Long)
- cgroup/cpuset: fix panic caused by partcmd_update (Chen Ridong)
- workqueue: Correct declaration of cpu_pwq in struct workqueue_struct (Uros Bizjak)
- workqueue: Fix spruious data race in __flush_work() (Tejun Heo)
- workqueue: Remove incorrect "WARN_ON_ONCE(!list_empty(&worker->entry));" from dying worker (Lai Jiangshan)
- workqueue: Fix UBSAN 'subtraction overflow' error in shift_and_mask() (Will Deacon)
- workqueue: doc: Fix function name, remove markers (Nikita Shubin)
- MIPS: cevt-r4k: Don't call get_c0_compare_int if timer irq is installed (Jiaxun Yang)
- MIPS: Loongson64: Set timer mode in cpu-probe (Jiaxun Yang)
- KVM: arm64: Make ICC_*SGI*_EL1 undef in the absence of a vGICv3 (Marc Zyngier)
- KVM: arm64: Ensure canonical IPA is hugepage-aligned when handling fault (Oliver Upton)
- KVM: arm64: vgic: Don't hold config_lock while unregistering redistributors (Marc Zyngier)
- KVM: arm64: vgic-debug: Don't put unmarked LPIs (Zenghui Yu)
- NFS: Avoid unnecessary rescanning of the per-server delegation list (Trond Myklebust)
- NFSv4: Fix clearing of layout segments in layoutreturn (Trond Myklebust)
- NFSv4: Add missing rescheduling points in nfs_client_return_marked_delegations (Trond Myklebust)
- nfs: fix bitmap decoder to handle a 3rd word (Jeff Layton)
- nfs: fix the fetch of FATTR4_OPEN_ARGUMENTS (Jeff Layton)
- rpcrdma: Trace connection registration and unregistration (Chuck Lever)
- rpcrdma: Use XA_FLAGS_ALLOC instead of XA_FLAGS_ALLOC1 (Chuck Lever)
- rpcrdma: Device kref is over-incremented on error from xa_alloc (Chuck Lever)
- smb/client: fix typo: GlobalMid_Sem -> GlobalMid_Lock (ChenXiaoSong)
- smb: client: ignore unhandled reparse tags (Paulo Alcantara)
- smb3: fix problem unloading module due to leaked refcount on shutdown (Steve French)
- smb3: fix broken cached reads when posix locks (Steve French)
- Input: himax_hx83112b - fix incorrect size when reading product ID (Dmitry Torokhov)
- Input: i8042 - use new forcenorestore quirk to replace old buggy quirk combination (Werner Sembach)
- Input: i8042 - add forcenorestore quirk to leave controller untouched even on s3 (Werner Sembach)
- Input: i8042 - add Fujitsu Lifebook E756 to i8042 quirk table (Takashi Iwai)
- Input: uinput - reject requests with unreasonable number of slots (Dmitry Torokhov)
- Input: edt-ft5x06 - add support for FocalTech FT8201 (Felix Kaechele)
- dt-bindings: input: touchscreen: edt-ft5x06: Document FT8201 support (Felix Kaechele)
- Input: adc-joystick - fix optional value handling (John Keeping)
- Input: synaptics - enable SMBus for HP Elitebook 840 G2 (Jonathan Denose)
- Input: ads7846 - ratelimit the spi_sync error message (Marek Vasut)
- drm/xe: Free job before xe_exec_queue_put (Matthew Brost)
- drm/xe: Drop HW fence pointer to HW fence ctx (Matthew Brost)
- drm/xe: Fix missing workqueue destroy in xe_gt_pagefault (Stuart Summers)
- drm/xe/uc: Use devm to register cleanup that includes exec_queues (Daniele Ceraolo Spurio)
- drm/xe: use devm instead of drmm for managed bo (Daniele Ceraolo Spurio)
- drm/xe/xe2hpg: Add Wa_14021821874 (Tejas Upadhyay)
- drm/xe: fix WA 14018094691 (Daniele Ceraolo Spurio)
- drm/xe/xe2: Add Wa_15015404425 (Tejas Upadhyay)
- drm/xe/xe2: Make subsequent L2 flush sequential (Tejas Upadhyay)
- drm/xe/xe2lpg: Extend workaround 14021402888 (Bommu Krishnaiah)
- drm/xe/xe2lpm: Extend Wa_16021639441 (Ngai-Mint Kwan)
- drm/xe/bmg: implement Wa_16023588340 (Matthew Auld)
- drm/xe/oa/uapi: Make bit masks unsigned (Geert Uytterhoeven)
- drm/xe/display: Make display suspend/resume work on discrete (Maarten Lankhorst)
- drm/xe: prevent UAF around preempt fence (Matthew Auld)
- drm/xe: Fix tile fini sequence (Matthew Brost)
- drm/xe: Move VM dma-resv lock from xe_exec_queue_create to __xe_exec_queue_init (Matthew Brost)
- drm/xe/observation: Drop empty sysctl table entry (Ashutosh Dixit)
- drm/xe: Fix opregion leak (Lucas De Marchi)
- nouveau/firmware: use dma non-coherent allocator (Dave Airlie)
- drm/i915/hdcp: Use correct cp_irq_count (Suraj Kandpal)
- drm/amdgpu: fix eGPU hotplug regression (Alex Deucher)
- drm/amdgpu: Validate TA binary size (Candice Li)
- drm/amdgpu/sdma5.2: limit wptr workaround to sdma 5.2.1 (Alex Deucher)
- drm/amdgpu: fixing rlc firmware loading failure issue (Yang Wang)
- drm/msm/adreno: Fix error return if missing firmware-name (Rob Clark)
- drm/msm: fix the highest_bank_bit for sc7180 (Abhinav Kumar)
- drm/msm/dpu: take plane rotation into account for wide planes (Dmitry Baryshkov)
- drm/msm/dpu: relax YUV requirements (Dmitry Baryshkov)
- drm/msm/dpu: limit QCM2290 to RGB formats only (Dmitry Baryshkov)
- drm/msm/dpu: cleanup FB if dpu_format_populate_layout fails (Dmitry Baryshkov)
- drm/msm/dp: reset the link phy params before link training (Abhinav Kumar)
- drm/msm/dpu: move dpu_encoder's connector assignment to atomic_enable() (Abhinav Kumar)
- drm/msm/dp: fix the max supported bpp logic (Abhinav Kumar)
- drm/msm/dpu: don't play tricks with debug macros (Dmitry Baryshkov)
- nvme: Remove unused field (Nilay Shroff)
- nvme: move stopping keep-alive into nvme_uninit_ctrl() (Ming Lei)
- block: Drop NULL check in bdev_write_zeroes_sectors() (John Garry)
- block: Read max write zeroes once for __blkdev_issue_write_zeroes() (John Garry)
- io_uring/kbuf: sanitize peek buffer setup (Jens Axboe)
- ACPI: video: Add backlight=native quirk for Dell OptiPlex 7760 AIO (Hans de Goede)
- platform/x86: dell-uart-backlight: Use acpi_video_get_backlight_type() (Hans de Goede)
- ACPI: video: Add Dell UART backlight controller detection (Hans de Goede)
- thermal: of: Fix OF node leak in of_thermal_zone_find() error paths (Krzysztof Kozlowski)
- thermal: of: Fix OF node leak in thermal_of_zone_register() (Krzysztof Kozlowski)
- thermal: of: Fix OF node leak in thermal_of_trips_init() error path (Krzysztof Kozlowski)
- thermal/debugfs: Fix the NULL vs IS_ERR() confusion in debugfs_create_dir() (Yang Ruibin)
- mmc: mmc_test: Fix NULL dereference on allocation failure (Dan Carpenter)
- mmc: dw_mmc: allow biu and ciu clocks to defer (Ben Whitten)
- mmc: mtk-sd: receive cmd8 data when hs400 tuning fail (Mengqi Zhang)
- spi: pxa2xx: Move PM runtime handling to the glue drivers (Andy Shevchenko)
- spi: pxa2xx: Do not override dev->platform_data on probe (Andy Shevchenko)
- spi: spi-fsl-lpspi: limit PRESCALE bit in TCR register (Carlos Song)
- spi: spi-cadence-quadspi: Fix OSPI NOR failures during system resume (Vignesh Raghavendra)
- spi: zynqmp-gqspi: Scale timeout by data size (Sean Anderson)
- power: sequencing: request the WLAN enable GPIO as-is (Bartosz Golaszewski)
- pmdomain: imx: wait SSAR when i.MX93 power domain on (Peng Fan)
- pmdomain: imx: scu-pd: Remove duplicated clocks (Alexander Stein)
- ata: pata_macio: Use WARN instead of BUG (Michael Ellerman)
- ata: pata_macio: Fix DMA table overflow (Michael Ellerman)
- s390/iucv: Fix vargs handling in iucv_alloc_device() (Alexandra Winter)
- net: ovs: fix ovs_drop_reasons error (Menglong Dong)
- netfilter: flowtable: validate vlan header (Pablo Neira Ayuso)
- netfilter: nft_counter: Synchronize nft_counter_reset() against reader. (Sebastian Andrzej Siewior)
- netfilter: nft_counter: Disable BH in nft_counter_offload_stats(). (Sebastian Andrzej Siewior)
- net: xilinx: axienet: Fix dangling multicast addresses (Sean Anderson)
- net: xilinx: axienet: Always disable promiscuous mode (Sean Anderson)
- MAINTAINERS: Mark JME Network Driver as Odd Fixes (Simon Horman)
- MAINTAINERS: Add header files to NETWORKING sections (Simon Horman)
- MAINTAINERS: Add limited globs for Networking headers (Simon Horman)
- MAINTAINERS: Add net_tstamp.h to SOCKET TIMESTAMPING section (Simon Horman)
- MAINTAINERS: Add sonet.h to ATM section of MAINTAINERS (Simon Horman)
- octeontx2-af: Fix CPT AF register offset calculation (Bharat Bhushan)
- net: phy: realtek: Fix setting of PHY LEDs Mode B bit on RTL8211F (Sava Jakovljev)
- net: ngbe: Fix phy mode set to external phy (Mengyuan Lou)
- ice: use internal pf id instead of function number (Michal Swiatkowski)
- ice: fix truesize operations for PAGE_SIZE >= 8192 (Maciej Fijalkowski)
- ice: fix ICE_LAST_OFFSET formula (Maciej Fijalkowski)
- ice: fix page reuse when PAGE_SIZE is over 8k (Maciej Fijalkowski)
- bnxt_en: Fix double DMA unmapping for XDP_REDIRECT (Somnath Kotur)
- ipv6: prevent possible UAF in ip6_xmit() (Eric Dumazet)
- ipv6: fix possible UAF in ip6_finish_output2() (Eric Dumazet)
- ipv6: prevent UAF in ip6_send_skb() (Eric Dumazet)
- netpoll: do not export netpoll_poll_[disable|enable]() (Eric Dumazet)
- selftests: mlxsw: ethtool_lanes: Source ethtool lib from correct path (Ido Schimmel)
- udp: fix receiving fraglist GSO packets (Felix Fietkau)
- mptcp: pm: avoid possible UaF when selecting endp (Matthieu Baerts (NGI0))
- selftests: mptcp: join: validate fullmesh endp on 1st sf (Matthieu Baerts (NGI0))
- mptcp: pm: fullmesh: select the right ID later (Matthieu Baerts (NGI0))
- mptcp: pm: only in-kernel cannot have entries with ID 0 (Matthieu Baerts (NGI0))
- mptcp: pm: check add_addr_accept_max before accepting new ADD_ADDR (Matthieu Baerts (NGI0))
- mptcp: pm: only decrement add_addr_accepted for MPJ req (Matthieu Baerts (NGI0))
- mptcp: pm: only mark 'subflow' endp as available (Matthieu Baerts (NGI0))
- mptcp: pm: remove mptcp_pm_remove_subflow() (Matthieu Baerts (NGI0))
- selftests: mptcp: join: test for flush/re-add endpoints (Matthieu Baerts (NGI0))
- mptcp: pm: re-using ID of unused flushed subflows (Matthieu Baerts (NGI0))
- selftests: mptcp: join: check re-using ID of closed subflow (Matthieu Baerts (NGI0))
- mptcp: pm: re-using ID of unused removed subflows (Matthieu Baerts (NGI0))
- selftests: mptcp: join: check re-using ID of unused ADD_ADDR (Matthieu Baerts (NGI0))
- mptcp: pm: re-using ID of unused removed ADD_ADDR (Matthieu Baerts (NGI0))
- netem: fix return value if duplicate enqueue fails (Stephen Hemminger)
- net: dsa: mv88e6xxx: Fix out-of-bound access (Joseph Huang)
- net: dsa: microchip: fix PTP config failure when using multiple ports (Martin Whitaker)
- igb: cope with large MAX_SKB_FRAGS (Paolo Abeni)
- cxgb4: add forgotten u64 ivlan cast before shift (Nikolay Kuratov)
- dpaa2-switch: Fix error checking in dpaa2_switch_seed_bp() (Dan Carpenter)
- bonding: fix xfrm state handling when clearing active slave (Nikolay Aleksandrov)
- bonding: fix xfrm real_dev null pointer dereference (Nikolay Aleksandrov)
- bonding: fix null pointer deref in bond_ipsec_offload_ok (Nikolay Aleksandrov)
- bonding: fix bond_ipsec_offload_ok return type (Nikolay Aleksandrov)
- ip6_tunnel: Fix broken GRO (Thomas Bogendoerfer)
- kcm: Serialise kcm_sendmsg() for the same socket. (Kuniyuki Iwashima)
- net: mctp: test: Use correct skb for route input check (Jeremy Kerr)
- tcp: prevent concurrent execution of tcp_sk_exit_batch (Florian Westphal)
- selftests: udpgro: no need to load xdp for gro (Hangbin Liu)
- selftests: udpgro: report error when receive failed (Hangbin Liu)
- Bluetooth: MGMT: Add error handling to pair_device() (Griffin Kroah-Hartman)
- Bluetooth: SMP: Fix assumption of Central always being Initiator (Luiz Augusto von Dentz)
- Bluetooth: hci_core: Fix LE quote calculation (Luiz Augusto von Dentz)
- Bluetooth: HCI: Invert LE State quirk to be opt-out rather then opt-in (Luiz Augusto von Dentz)
- tc-testing: don't access non-existent variable on exception (Simon Horman)
- net/mlx5: Fix IPsec RoCE MPV trace call (Patrisious Haddad)
- net/mlx5e: XPS, Fix oversight of Multi-PF Netdev changes (Carolina Jubran)
- net/mlx5e: SHAMPO, Release in progress headers (Dragos Tatulea)
- net/mlx5e: SHAMPO, Fix page leak (Dragos Tatulea)
- net: mscc: ocelot: treat 802.1ad tagged traffic as 802.1Q-untagged (Vladimir Oltean)
- net: dsa: felix: fix VLAN tag loss on CPU reception with ocelot-8021q (Vladimir Oltean)
- net: dsa: provide a software untagging function on RX for VLAN-aware bridges (Vladimir Oltean)
- net: mscc: ocelot: serialize access to the injection/extraction groups (Vladimir Oltean)
- net: mscc: ocelot: fix QoS class for injected packets with "ocelot-8021q" (Vladimir Oltean)
- net: mscc: ocelot: use ocelot_xmit_get_vlan_info() also for FDMA and register injection (Vladimir Oltean)
- selftests: net: bridge_vlan_aware: test that other TPIDs are seen as untagged (Vladimir Oltean)
- selftests: net: local_termination: add PTP frames to the mix (Vladimir Oltean)
- selftests: net: local_termination: don't use xfail_on_veth() (Vladimir Oltean)
- selftests: net: local_termination: introduce new tests which capture VLAN behavior (Vladimir Oltean)
- selftests: net: local_termination: add one more test for VLAN-aware bridges (Vladimir Oltean)
- selftests: net: local_termination: parameterize test name (Vladimir Oltean)
- selftests: net: local_termination: parameterize sending interface (Vladimir Oltean)
- selftests: net: local_termination: refactor macvlan creation/deletion (Vladimir Oltean)
- MAINTAINERS: add selftests to network drivers (Jakub Kicinski)
- bnxt_en: Don't clear ntuple filters and rss contexts during ethtool ops (Pavan Chebbi)
- virtio_net: move netdev_tx_reset_queue() call before RX napi enable (Jiri Pirko)
- kbuild: fix typos "prequisites" to "prerequisites" (Masahiro Yamada)
- Documentation/llvm: turn make command for ccache into code block (Javier Carrasco)
- kbuild: avoid scripts/kallsyms parsing /dev/null (Masahiro Yamada)
- treewide: remove unnecessary <linux/version.h> inclusion (Masahiro Yamada)
- scripts: kconfig: merge_config: config files: add a trailing newline (Anders Roxell)
- Makefile: add $(srctree) to dependency of compile_commands.json target (Alexandre Courbot)
- kbuild: clean up code duplication in cmd_fdtoverlay (Masahiro Yamada)
- platform/x86: ISST: Fix return value on last invalid resource (Srinivas Pandruvada)
- platform/surface: aggregator: Fix warning when controller is destroyed in probe (Maximilian Luz)
- platform/surface: aggregator_registry: Add support for Surface Laptop 6 (Maximilian Luz)
- platform/surface: aggregator_registry: Add fan and thermal sensor support for Surface Laptop 5 (Maximilian Luz)
- platform/surface: aggregator_registry: Add support for Surface Laptop Studio 2 (Maximilian Luz)
- platform/surface: aggregator_registry: Add support for Surface Laptop Go 3 (Maximilian Luz)
- platform/surface: aggregator_registry: Add Support for Surface Pro 10 (Maximilian Luz)
- platform/x86: asus-wmi: Add quirk for ROG Ally X (Luke D. Jones)
- erofs: fix out-of-bound access when z_erofs_gbuf_growsize() partially fails (Gao Xiang)
- erofs: allow large folios for compressed files (Gao Xiang)
- erofs: get rid of check_layout_compatibility() (Hongzhen Luo)
- erofs: simplify readdir operation (Hongzhen Luo)
- ksmbd: Replace one-element arrays with flexible-array members (Thorsten Blum)
- ksmbd: fix spelling mistakes in documentation (Victor Timofei)
- ksmbd: fix race condition between destroy_previous_session() and smb2 operations() (Namjae Jeon)
- ksmbd: Use unsafe_memcpy() for ntlm_negotiate (Namjae Jeon)
- iommufd/selftest: Make dirty_ops static (Jinjie Ruan)
- iommufd/device: Fix hwpt at err_unresv in iommufd_device_do_replace() (Nicolin Chen)
- cxl/test: Skip cxl_setup_parent_dport() for emulated dports (Li Ming)
- cxl/pci: Get AER capability address from RCRB only for RCH dport (Li Ming)
- HID: wacom: Defer calculation of resolution until resolution_code is known (Jason Gerecke)
- HID: multitouch: Add support for GT7868Q (Dmitry Savin)
- HID: amd_sfh: free driver_data after destroying hid device (Olivier Sobrie)
- hid-asus: add ROG Ally X prod ID to quirk list (Luke D. Jones)
- HID: cougar: fix slab-out-of-bounds Read in cougar_report_fixup (Camila Alvarez)
- printk/panic: Allow cpu backtraces to be written into ringbuffer during panic (Ryo Takakura)
- fedora: disable CONFIG_DRM_WERROR (Patrick Talbert)

* Tue Aug 20 2024 Jan Stancek <jstancek@redhat.com> [6.11.0-0.rc4.20.el10]
- Linux 6.11-rc4 (Linus Torvalds)
- mips: sgi-ip22: Fix the build (Bart Van Assche)
- ARM: riscpc: ecard: Fix the build (Bart Van Assche)
- char: xillybus: Check USB endpoints when probing device (Eli Billauer)
- char: xillybus: Refine workqueue handling (Eli Billauer)
- Revert "misc: fastrpc: Restrict untrusted app to attach to privileged PD" (Griffin Kroah-Hartman)
- char: xillybus: Don't destroy workqueue from work item running on it (Eli Billauer)
- Revert "serial: 8250_omap: Set the console genpd always on if no console suspend" (Griffin Kroah-Hartman)
- tty: atmel_serial: use the correct RTS flag. (Mathieu Othacehe)
- tty: vt: conmakehash: remove non-portable code printing comment header (Masahiro Yamada)
- tty: serial: fsl_lpuart: mark last busy before uart_add_one_port (Peng Fan)
- xhci: Fix Panther point NULL pointer deref at full-speed re-enumeration (Mathias Nyman)
- usb: misc: ljca: Add Lunar Lake ljca GPIO HID to ljca_gpio_hids[] (Hans de Goede)
- Revert "usb: typec: tcpm: clear pd_event queue in PORT_RESET" (Xu Yang)
- usb: typec: ucsi: Fix the return value of ucsi_run_command() (Heikki Krogerus)
- usb: xhci: fix duplicate stall handling in handle_tx_event() (Niklas Neronin)
- usb: xhci: Check for xhci->interrupters being allocated in xhci_mem_clearup() (Marc Zyngier)
- thunderbolt: Mark XDomain as unplugged when router is removed (Mika Westerberg)
- thunderbolt: Fix memory leaks in {port|retimer}_sb_regs_write() (Aapo Vienamo)
- btrfs: only enable extent map shrinker for DEBUG builds (Qu Wenruo)
- btrfs: zoned: properly take lock to read/update block group's zoned variables (Naohiro Aota)
- btrfs: tree-checker: add dev extent item checks (Qu Wenruo)
- btrfs: update target inode's ctime on unlink (Jeff Layton)
- btrfs: send: annotate struct name_cache_entry with __counted_by() (Thorsten Blum)
- fuse: Initialize beyond-EOF page contents before setting uptodate (Jann Horn)
- mm/migrate: fix deadlock in migrate_pages_batch() on large folios (Gao Xiang)
- alloc_tag: mark pages reserved during CMA activation as not tagged (Suren Baghdasaryan)
- alloc_tag: introduce clear_page_tag_ref() helper function (Suren Baghdasaryan)
- crash: fix riscv64 crash memory reserve dead loop (Jinjie Ruan)
- selftests: memfd_secret: don't build memfd_secret test on unsupported arches (Muhammad Usama Anjum)
- mm: fix endless reclaim on machines with unaccepted memory (Kirill A. Shutemov)
- selftests/mm: compaction_test: fix off by one in check_compaction() (Dan Carpenter)
- mm/numa: no task_numa_fault() call if PMD is changed (Zi Yan)
- mm/numa: no task_numa_fault() call if PTE is changed (Zi Yan)
- mm/vmalloc: fix page mapping if vm_area_alloc_pages() with high order fallback to order 0 (Hailong Liu)
- mm/memory-failure: use raw_spinlock_t in struct memory_failure_cpu (Waiman Long)
- mm: don't account memmap per-node (Pasha Tatashin)
- mm: add system wide stats items category (Pasha Tatashin)
- mm: don't account memmap on failure (Pasha Tatashin)
- mm/hugetlb: fix hugetlb vs. core-mm PT locking (David Hildenbrand)
- mseal: fix is_madv_discard() (Pedro Falcato)
- powerpc/topology: Check if a core is online (Nysal Jan K.A)
- cpu/SMT: Enable SMT only if a core is online (Nysal Jan K.A)
- powerpc/mm: Fix boot warning with hugepages and CONFIG_DEBUG_VIRTUAL (Christophe Leroy)
- powerpc/mm: Fix size of allocated PGDIR (Christophe Leroy)
- soc: fsl: qbman: remove unused struct 'cgr_comp' (Dr. David Alan Gilbert)
- smb: smb2pdu.h: Use static_assert() to check struct sizes (Gustavo A. R. Silva)
- smb3: fix lock breakage for cached writes (Steve French)
- smb/client: avoid possible NULL dereference in cifs_free_subrequest() (Su Hui)
- i2c: tegra: Do not mark ACPI devices as irq safe (Breno Leitao)
- i2c: qcom-geni: Add missing geni_icc_disable in geni_i2c_runtime_resume (Andi Shyti)
- i2c: Use IS_REACHABLE() for substituting empty ACPI functions (Richard Fitzgerald)
- scsi: mpi3mr: Avoid MAX_PAGE_ORDER WARNING for buffer allocations (Shin'ichiro Kawasaki)
- scsi: mpi3mr: Add missing spin_lock_init() for mrioc->trigger_lock (Shin'ichiro Kawasaki)
- xfs: conditionally allow FS_XFLAG_REALTIME changes if S_DAX is set (Darrick J. Wong)
- xfs: revert AIL TASK_KILLABLE threshold (Darrick J. Wong)
- xfs: attr forks require attr, not attr2 (Darrick J. Wong)
- bcachefs: Fix locking in __bch2_trans_mark_dev_sb() (Kent Overstreet)
- bcachefs: fix incorrect i_state usage (Kent Overstreet)
- bcachefs: avoid overflowing LRU_TIME_BITS for cached data lru (Kent Overstreet)
- bcachefs: Fix forgetting to pass trans to fsck_err() (Kent Overstreet)
- bcachefs: Increase size of cuckoo hash table on too many rehashes (Kent Overstreet)
- bcachefs: bcachefs_metadata_version_disk_accounting_inum (Kent Overstreet)
- bcachefs: Kill __bch2_accounting_mem_mod() (Kent Overstreet)
- bcachefs: Make bkey_fsck_err() a wrapper around fsck_err() (Kent Overstreet)
- bcachefs: Fix warning in __bch2_fsck_err() for trans not passed in (Kent Overstreet)
- bcachefs: Add a time_stat for blocked on key cache flush (Kent Overstreet)
- bcachefs: Improve trans_blocked_journal_reclaim tracepoint (Kent Overstreet)
- bcachefs: Add hysteresis to waiting on btree key cache flush (Kent Overstreet)
- lib/generic-radix-tree.c: Fix rare race in __genradix_ptr_alloc() (Kent Overstreet)
- bcachefs: Convert for_each_btree_node() to lockrestart_do() (Kent Overstreet)
- bcachefs: Add missing downgrade table entry (Kent Overstreet)
- bcachefs: disk accounting: ignore unknown types (Kent Overstreet)
- bcachefs: bch2_accounting_invalid() fixup (Kent Overstreet)
- bcachefs: Fix bch2_trigger_alloc when upgrading from old versions (Kent Overstreet)
- bcachefs: delete faulty fastpath in bch2_btree_path_traverse_cached() (Kent Overstreet)
- memcg_write_event_control(): fix a user-triggerable oops (Al Viro)
- arm64: Fix KASAN random tag seed initialization (Samuel Holland)
- arm64: ACPI: NUMA: initialize all values of acpi_early_node_map to NUMA_NO_NODE (Haibo Xu)
- arm64: uaccess: correct thinko in __get_mem_asm() (Mark Rutland)
- clk: thead: fix dependency on clk_ignore_unused (Drew Fustini)
- block: Fix lockdep warning in blk_mq_mark_tag_wait (Li Lingfeng)
- md/raid1: Fix data corruption for degraded array with slow disk (Yu Kuai)
- s390/dasd: fix error recovery leading to data corruption on ESE devices (Stefan Haberland)
- s390/dasd: Remove DMA alignment (Eric Farman)
- io_uring: fix user_data field name in comment (Caleb Sander Mateos)
- io_uring/sqpoll: annotate debug task == current with data_race() (Jens Axboe)
- io_uring/napi: remove duplicate io_napi_entry timeout assignation (Olivier Langlois)
- io_uring/napi: check napi_enabled in io_napi_add() before proceeding (Olivier Langlois)
- of/irq: Prevent device address out-of-bounds read in interrupt map walk (Stefan Wiehler)
- dt-bindings: eeprom: at25: add fujitsu,mb85rs256 compatible (Francesco Dolcini)
- dt-bindings: Batch-update Konrad Dybcio's email (Konrad Dybcio)
- thermal: gov_bang_bang: Use governor_data to reduce overhead (Rafael J. Wysocki)
- thermal: gov_bang_bang: Add .manage() callback (Rafael J. Wysocki)
- thermal: gov_bang_bang: Split bang_bang_control() (Rafael J. Wysocki)
- thermal: gov_bang_bang: Call __thermal_cdev_update() directly (Rafael J. Wysocki)
- ACPI: EC: Evaluate _REG outside the EC scope more carefully (Rafael J. Wysocki)
- ACPICA: Add a depth argument to acpi_execute_reg_methods() (Rafael J. Wysocki)
- Revert "ACPI: EC: Evaluate orphan _REG under EC device" (Rafael J. Wysocki)
- nvdimm/pmem: Set dax flag for all 'PFN_MAP' cases (Zhihao Cheng)
- rust: x86: remove `-3dnow{,a}` from target features (Miguel Ojeda)
- kbuild: rust-analyzer: mark `rust_is_available.sh` invocation as recursive (Miguel Ojeda)
- rust: add intrinsics to fix `-Os` builds (Miguel Ojeda)
- kbuild: rust: skip -fmin-function-alignment in bindgen flags (Zehui Xu)
- rust: Support latest version of `rust-analyzer` (Sarthak Singh)
- rust: macros: indent list item in `module!`'s docs (Miguel Ojeda)
- rust: fix the default format for CONFIG_{RUSTC,BINDGEN}_VERSION_TEXT (Masahiro Yamada)
- rust: suppress error messages from CONFIG_{RUSTC,BINDGEN}_VERSION_TEXT (Masahiro Yamada)
- RISC-V: hwprobe: Add SCALAR to misaligned perf defines (Evan Green)
- RISC-V: hwprobe: Add MISALIGNED_PERF key (Evan Green)
- riscv: Fix out-of-bounds when accessing Andes per hart vendor extension array (Alexandre Ghiti)
- RISC-V: ACPI: NUMA: initialize all values of acpi_early_node_map to NUMA_NO_NODE (Haibo Xu)
- riscv: change XIP's kernel_map.size to be size of the entire kernel (Nam Cao)
- riscv: entry: always initialize regs->a0 to -ENOSYS (Celeste Liu)
- riscv: Re-introduce global icache flush in patch_text_XXX() (Alexandre Ghiti)
- rtla/osnoise: Prevent NULL dereference in error handling (Dan Carpenter)
- tracing: Return from tracing_buffers_read() if the file has been closed (Steven Rostedt)
- KEYS: trusted: dcp: fix leak of blob encryption key (David Gstir)
- KEYS: trusted: fix DCP blob payload length assignment (David Gstir)
- dm persistent data: fix memory allocation failure (Mikulas Patocka)
- Documentation: dm-crypt.rst warning + error fix (Daniel Yang)
- dm resume: don't return EINVAL when signalled (Khazhismel Kumykov)
- dm suspend: return -ERESTARTSYS instead of -EINTR (Mikulas Patocka)
- iommu: Remove unused declaration iommu_sva_unbind_gpasid() (Yue Haibing)
- iommu: Restore lost return in iommu_report_device_fault() (Barak Biber)
- gpio: mlxbf3: Support shutdown() function (Asmaa Mnebhi)
- ALSA: hda/tas2781: Use correct endian conversion (Takashi Iwai)
- ALSA: usb-audio: Support Yamaha P-125 quirk entry (Juan José Arboleda)
- ALSA: hda: cs35l41: Remove redundant call to hda_cs_dsp_control_remove() (Richard Fitzgerald)
- ALSA: hda: cs35l56: Remove redundant call to hda_cs_dsp_control_remove() (Richard Fitzgerald)
- ALSA: hda/tas2781: fix wrong calibrated data order (Baojun Xu)
- ALSA: usb-audio: Add delay quirk for VIVO USB-C-XE710 HEADSET (Lianqin Hu)
- ALSA: hda/realtek: Add support for new HP G12 laptops (Simon Trimmer)
- spi: Add empty versions of ACPI functions (Richard Fitzgerald)
- ALSA: hda/realtek: Fix noise from speakers on Lenovo IdeaPad 3 15IAU7 (Parsa Poorshikhian)
- ALSA: timer: Relax start tick time check for slave timer elements (Takashi Iwai)
- drm/mediatek: Set sensible cursor width/height values to fix crash (AngeloGioacchino Del Regno)
- drm/xe: Hold a PM ref when GT TLB invalidations are inflight (Matthew Brost)
- drm/xe: Drop xe_gt_tlb_invalidation_wait (Matthew Brost)
- drm/xe: Add xe_gt_tlb_invalidation_fence_init helper (Matthew Brost)
- drm/xe/pf: Fix VF config validation on multi-GT platforms (Michal Wajdeczko)
- drm/xe: Build PM into GuC CT layer (Matthew Brost)
- drm/xe/vf: Fix register value lookup (Michal Wajdeczko)
- drm/xe: Fix use after free when client stats are captured (Umesh Nerlige Ramappa)
- drm/xe: Take a ref to xe file when user creates a VM (Umesh Nerlige Ramappa)
- drm/xe: Add ref counting for xe_file (Umesh Nerlige Ramappa)
- drm/xe: Move part of xe_file cleanup to a helper (Umesh Nerlige Ramappa)
- drm/xe: Validate user fence during creation (Matthew Brost)
- drm/rockchip: inno-hdmi: Fix infoframe upload (Alex Bee)
- drm/v3d: Fix out-of-bounds read in `v3d_csd_job_run()` (Maíra Canal)
- drm: panel-orientation-quirks: Add quirk for Ayn Loki Max (Bouke Sybren Haarsma)
- drm: panel-orientation-quirks: Add quirk for Ayn Loki Zero (Bouke Sybren Haarsma)
- dt-bindings: display: panel: samsung,atna45dc02: Fix indentation (Douglas Anderson)
- drm/amd/amdgpu: add HDP_SD support on gc 12.0.0/1 (Kenneth Feng)
- drm/amdgpu: Update kmd_fw_shared for VCN5 (Yinjie Yao)
- drm/amd/amdgpu: command submission parser for JPEG (David (Ming Qiang) Wu)
- drm/amdgpu/mes12: fix suspend issue (Jack Xiao)
- drm/amdgpu/mes12: sw/hw fini for unified mes (Jack Xiao)
- drm/amdgpu/mes12: configure two pipes hardware resources (Jack Xiao)
- drm/amdgpu/mes12: adjust mes12 sw/hw init for multiple pipes (Jack Xiao)
- drm/amdgpu/mes12: add mes pipe switch support (Jack Xiao)
- drm/amdgpu/mes12: load unified mes fw on pipe0 and pipe1 (Jack Xiao)
- drm/amdgpu/mes: add multiple mes ring instances support (Jack Xiao)
- drm/amdgpu/mes12: update mes_v12_api_def.h (Jack Xiao)
- drm/amdgpu: Actually check flags for all context ops. (Bas Nieuwenhuizen)
- drm/amdgpu/jpeg4: properly set atomics vmid field (Alex Deucher)
- drm/amdgpu/jpeg2: properly set atomics vmid field (Alex Deucher)
- drm/amd/display: Adjust cursor position (Rodrigo Siqueira)
- drm/amd/display: fix cursor offset on rotation 180 (Melissa Wen)
- drm/amd/display: Fix MST BW calculation Regression (Fangzhi Zuo)
- drm/amd/display: Enable otg synchronization logic for DCN321 (Loan Chen)
- drm/amd/display: fix s2idle entry for DCN3.5+ (Hamza Mahfooz)
- drm/amdgpu/mes: fix mes ring buffer overflow (Jack Xiao)
- v6.11-rc3-rt3 (Sebastian Andrzej Siewior)
- crypto: x86/aes-gcm - fix PREEMPT_RT issue in gcm_crypt() (Eric Biggers)
- hrtimer: Annotate hrtimer_cpu_base_.*_expiry() for sparse. (Sebastian Andrzej Siewior)
- timers: Add sparse annotation for timer_sync_wait_running(). (Sebastian Andrzej Siewior)
- locking/rt: Annotate unlock followed by lock for sparse. (Sebastian Andrzej Siewior)
- locking/rt: Add sparse annotation for RCU. (Sebastian Andrzej Siewior)
- locking/rt: Remove one __cond_lock() in RT's spin_trylock_irqsave() (Sebastian Andrzej Siewior)
- locking/rt: Add sparse annotation PREEMPT_RT's sleeping locks. (Sebastian Andrzej Siewior)
- v6.11-rc3-rt2 (Sebastian Andrzej Siewior)
- perf daemon: Fix the build on 32-bit architectures (Arnaldo Carvalho de Melo)
- tools/include: Sync arm64 headers with the kernel sources (Namhyung Kim)
- tools/include: Sync x86 headers with the kernel sources (Namhyung Kim)
- tools/include: Sync filesystem headers with the kernel sources (Namhyung Kim)
- tools/include: Sync network socket headers with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/asm-generic/unistd.h with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/sound/asound.h with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/linux/perf.h with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/linux/kvm.h with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/drm/i915_drm.h with the kernel sources (Namhyung Kim)
- perf tools: Add tools/include/uapi/README (Namhyung Kim)
- kallsyms: Match symbols exactly with CONFIG_LTO_CLANG (Song Liu)
- kallsyms: Do not cleanup .llvm.<hash> suffix before sorting symbols (Song Liu)
- kunit/overflow: Fix UB in overflow_allocation_test (Ivan Orlov)
- gcc-plugins: randstruct: Remove GCC 4.7 or newer requirement (Thorsten Blum)
- refcount: Report UAF for refcount_sub_and_test(0) when counter==0 (Petr Pavlu)
- netfilter: nf_tables: Add locking for NFT_MSG_GETOBJ_RESET requests (Phil Sutter)
- netfilter: nf_tables: Introduce nf_tables_getobj_single (Phil Sutter)
- netfilter: nf_tables: Audit log dump reset after the fact (Phil Sutter)
- selftests: netfilter: add test for br_netfilter+conntrack+queue combination (Florian Westphal)
- netfilter: nf_queue: drop packets with cloned unconfirmed conntracks (Florian Westphal)
- netfilter: flowtable: initialise extack before use (Donald Hunter)
- netfilter: nfnetlink: Initialise extack before use in ACKs (Donald Hunter)
- netfilter: allow ipv6 fragments to arrive on different devices (Tom Hughes)
- net: hns3: use correct release function during uninitialization (Peiyang Wang)
- net: hns3: void array out of bound when loop tnl_num (Peiyang Wang)
- net: hns3: fix a deadlock problem when config TC during resetting (Jie Wang)
- net: hns3: use the user's cfg after reset (Peiyang Wang)
- net: hns3: fix wrong use of semaphore up (Jie Wang)
- selftests: net: lib: kill PIDs before del netns (Matthieu Baerts (NGI0))
- pse-core: Conditionally set current limit during PI regulator registration (Oleksij Rempel)
- net: thunder_bgx: Fix netdev structure allocation (Marc Zyngier)
- net: ethtool: Allow write mechanism of LPL and both LPL and EPL (Danielle Ratson)
- vsock: fix recursive ->recvmsg calls (Cong Wang)
- wifi: ath12k: use 128 bytes aligned iova in transmit path for WCN7850 (Baochen Qiang)
- wifi: iwlwifi: correctly lookup DMA address in SG table (Benjamin Berg)
- wifi: mt76: mt7921: fix NULL pointer access in mt7921_ipv6_addr_change (Bert Karwatzki)
- wifi: brcmfmac: cfg80211: Handle SSID based pmksa deletion (Janne Grunau)
- wifi: rtlwifi: rtl8192du: Initialise value32 in _rtl92du_init_queue_reserved_page (Bitterblue Smith)
- selftest: af_unix: Fix kselftest compilation warnings (Abhinav Jain)
- tcp: Update window clamping condition (Subash Abhinov Kasiviswanathan)
- mptcp: correct MPTCP_SUBFLOW_ATTR_SSN_OFFSET reserved size (Eugene Syromiatnikov)
- mlxbf_gige: disable RX filters until RX path initialized (David Thompson)
- net: mana: Fix doorbell out of order violation and avoid unnecessary doorbell rings (Long Li)
- net: macb: Use rcu_dereference() for idev->ifa_list in macb_suspend(). (Kuniyuki Iwashima)
- net: ethernet: mtk_wed: fix use-after-free panic in mtk_wed_setup_tc_block_cb() (Zheng Zhang)
- net: mana: Fix RX buf alloc_size alignment and atomic op panic (Haiyang Zhang)
- dt-bindings: net: fsl,qoriq-mc-dpmac: add missed property phys (Frank Li)
- net: phy: vitesse: repair vsc73xx autonegotiation (Pawel Dembicki)
- net: dsa: vsc73xx: allow phy resetting (Pawel Dembicki)
- net: dsa: vsc73xx: check busy flag in MDIO operations (Pawel Dembicki)
- net: dsa: vsc73xx: pass value in phy_write operation (Pawel Dembicki)
- net: dsa: vsc73xx: fix port MAC configuration in full duplex mode (Pawel Dembicki)
- net: axienet: Fix register defines comment description (Radhey Shyam Pandey)
- atm: idt77252: prevent use after free in dequeue_rx() (Dan Carpenter)
- igc: Fix qbv tx latency by setting gtxoffset (Faizal Rahim)
- igc: Fix reset adapter logics when tx mode change (Faizal Rahim)
- igc: Fix qbv_config_change_errors logics (Faizal Rahim)
- igc: Fix packet still tx after gate close by reducing i226 MAC retry buffer (Faizal Rahim)
- net: ethernet: use ip_hdrlen() instead of bit shift (Moon Yeounsu)
- net/mlx5e: Fix queue stats access to non-existing channels splat (Gal Pressman)
- net/mlx5e: Correctly report errors for ethtool rx flows (Cosmin Ratiu)
- net/mlx5e: Take state lock during tx timeout reporter (Dragos Tatulea)
- net/mlx5e: SHAMPO, Increase timeout to improve latency (Dragos Tatulea)
- net/mlx5: SD, Do not query MPIR register if no sd_group (Tariq Toukan)
- selftests/net: Add coverage for UDP GSO with IPv6 extension headers (Jakub Sitnicki)
- udp: Fall back to software USO if IPv6 extension headers are present (Jakub Sitnicki)
- net: Make USO depend on CSUM offload (Jakub Sitnicki)
- gtp: pull network headers in gtp_dev_xmit() (Eric Dumazet)
- usbnet: ipheth: fix carrier detection in modes 1 and 4 (Foster Snowhill)
- usbnet: ipheth: do not stop RX on failing RX callback (Foster Snowhill)
- usbnet: ipheth: drop RX URBs with no payload (Foster Snowhill)
- usbnet: ipheth: remove extraneous rx URB length check (Foster Snowhill)
- usbnet: ipheth: race between ipheth_close and error handling (Oliver Neukum)
- media: atomisp: Fix streaming no longer working on BYT / ISP2400 devices (Hans de Goede)
- media: Revert "media: dvb-usb: Fix unexpected infinite loop in dvb_usb_read_remote_control()" (Sean Young)
- Revert "ata: libata-scsi: Honor the D_SENSE bit for CK_COND=1 and no error" (Niklas Cassel)
- redhat/configs: Disable dlm in rhel configs (Andrew Price)
- rhel: aarch64: enable required PSCI configs (Peter Robinson)
- btrfs: fix invalid mapping of extent xarray state (Naohiro Aota)
- btrfs: send: allow cloning non-aligned extent if it ends at i_size (Filipe Manana)
- btrfs: only run the extent map shrinker from kswapd tasks (Filipe Manana)
- btrfs: tree-checker: reject BTRFS_FT_UNKNOWN dir type (Qu Wenruo)
- btrfs: check delayed refs when we're checking if a ref exists (Josef Bacik)
- KVM: SEV: uapi: fix typo in SEV_RET_INVALID_CONFIG (Amit Shah)
- KVM: x86: Disallow read-only memslots for SEV-ES and SEV-SNP (and TDX) (Sean Christopherson)
- KVM: eventfd: Use synchronize_srcu_expedited() on shutdown (Li RongQing)
- KVM: selftests: Add a testcase to verify x2APIC is fully readonly (Michal Luczaj)
- KVM: x86: Make x2APIC ID 100%% readonly (Sean Christopherson)
- KVM: x86: Use this_cpu_ptr() instead of per_cpu_ptr(smp_processor_id()) (Isaku Yamahata)
- KVM: x86: hyper-v: Remove unused inline function kvm_hv_free_pa_page() (Yue Haibing)
- KVM: SVM: Fix an error code in sev_gmem_post_populate() (Dan Carpenter)
- s390/uv: Panic for set and remove shared access UVC errors (Claudio Imbrenda)
- KVM: s390: fix validity interception issue when gisa is switched off (Michael Mueller)
- KVM: arm64: vgic: Hold config_lock while tearing down a CPU interface (Marc Zyngier)
- KVM: selftests: arm64: Correct feature test for S1PIE in get-reg-list (Mark Brown)
- KVM: arm64: Tidying up PAuth code in KVM (Fuad Tabba)
- KVM: arm64: vgic-debug: Exit the iterator properly w/o LPI (Zenghui Yu)
- KVM: arm64: Enforce dependency on an ARMv8.4-aware toolchain (Marc Zyngier)
- docs: KVM: Fix register ID of SPSR_FIQ (Takahiro Itazuri)
- KVM: arm64: vgic: fix unexpected unlock sparse warnings (Sebastian Ott)
- KVM: arm64: fix kdoc warnings in W=1 builds (Sebastian Ott)
- KVM: arm64: fix override-init warnings in W=1 builds (Sebastian Ott)
- KVM: arm64: free kvm->arch.nested_mmus with kvfree() (Danilo Krummrich)
- KVM: SVM: Fix uninitialized variable bug (Dan Carpenter)
- selinux: revert our use of vma_is_initial_heap() (Paul Moore)
- selinux: add the processing of the failure of avc_add_xperms_decision() (Zhen Lei)
- selinux: fix potential counting error in avc_add_xperms_decision() (Zhen Lei)
- Squashfs: sanity check symbolic link size (Phillip Lougher)
- 9p: Fix DIO read through netfs (Dominique Martinet)
- vfs: Don't evict inode under the inode lru traversing context (Zhihao Cheng)
- netfs: Fix handling of USE_PGPRIV2 and WRITE_TO_CACHE flags (David Howells)
- netfs, ceph: Revert "netfs: Remove deprecated use of PG_private_2 as a second writeback flag" (David Howells)
- file: fix typo in take_fd() comment (Mathias Krause)
- pidfd: prevent creation of pidfds for kthreads (Christian Brauner)
- netfs: clean up after renaming FSCACHE_DEBUG config (Lukas Bulwahn)
- libfs: fix infinite directory reads for offset dir (yangerkun)
- nsfs: fix ioctl declaration (Christian Brauner)
- fs/netfs/fscache_cookie: add missing "n_accesses" check (Max Kellermann)
- filelock: fix name of file_lease slab cache (Omar Sandoval)
- netfs: Fault in smaller chunks for non-large folio mappings (Matthew Wilcox (Oracle))
- perf/bpf: Don't call bpf_overflow_handler() for tracing events (Kyle Huey)
- selftests/bpf: Add a test to verify previous stacksafe() fix (Yonghong Song)
- bpf: Fix a kernel verifier crash in stacksafe() (Yonghong Song)
- bpf: Fix updating attached freplace prog in prog_array map (Leon Hwang)
- Linux v6.11.0-0.rc4

* Thu Aug 15 2024 Jan Stancek <jstancek@redhat.com> [6.11.0-0.rc3.19.el10]
- exec: Fix ToCToU between perm check and set-uid/gid usage (Kees Cook)
- binfmt_flat: Fix corruption when not offsetting data start (Kees Cook)
- ksmbd: override fsids for smb2_query_info() (Namjae Jeon)
- ksmbd: override fsids for share path check (Namjae Jeon)
- fedora: Enable AF8133J Magnetometer driver (Peter Robinson)
- platform/x86: ideapad-laptop: add a mutex to synchronize VPC commands (Gergo Koteles)
- platform/x86: ideapad-laptop: move ymc_trigger_ec from lenovo-ymc (Gergo Koteles)
- platform/x86: ideapad-laptop: introduce a generic notification chain (Gergo Koteles)
- platform/x86/amd/pmf: Fix to Update HPD Data When ALS is Disabled (Shyam Sundar S K)
- fix bitmap corruption on close_range() with CLOSE_RANGE_UNSHARE (Al Viro)
- redhat: spec: add cachestat kselftest (Eric Chanudet)
- redhat: hmac sign the UKI for FIPS (Vitaly Kuznetsov)
- not upstream: Disable vdso getrandom when FIPS is enabled (Herbert Xu)
- Linux v6.11.0-0.rc3

* Tue Aug 13 2024 Jan Stancek <jstancek@redhat.com> [6.11.0-0.rc3.18.el10]
- Linux 6.11-rc3 (Linus Torvalds)
- x86/mtrr: Check if fixed MTRRs exist before saving them (Andi Kleen)
- x86/paravirt: Fix incorrect virt spinlock setting on bare metal (Chen Yu)
- x86/acpi: Remove __ro_after_init from acpi_mp_wake_mailbox (Zhiquan Li)
- x86/mm: Fix PTI for i386 some more (Thomas Gleixner)
- timekeeping: Fix bogus clock_was_set() invocation in do_adjtimex() (Thomas Gleixner)
- ntp: Safeguard against time_constant overflow (Justin Stitt)
- ntp: Clamp maxerror and esterror to operating range (Justin Stitt)
- irqchip/riscv-aplic: Retrigger MSI interrupt on source configuration (Yong-Xuan Wang)
- irqchip/xilinx: Fix shift out of bounds (Radhey Shyam Pandey)
- genirq/irqdesc: Honor caller provided affinity in alloc_desc() (Shay Drory)
- usb: typec: ucsi: Fix a deadlock in ucsi_send_command_common() (Heikki Krogerus)
- usb: typec: tcpm: avoid sink goto SNK_UNATTACHED state if not received source capability message (Xu Yang)
- usb: gadget: f_fs: pull out f->disable() from ffs_func_set_alt() (Tudor Ambarus)
- usb: gadget: f_fs: restore ffs_func_disable() functionality (Tudor Ambarus)
- USB: serial: debug: do not echo input by default (Marek Marczykowski-Górecki)
- usb: typec: tipd: Delete extra semi-colon (Harshit Mogalapalli)
- usb: typec: tipd: Fix dereferencing freeing memory in tps6598x_apply_patch() (Harshit Mogalapalli)
- usb: gadget: u_serial: Set start_delayed during suspend (Prashanth K)
- usb: typec: tcpci: Fix error code in tcpci_check_std_output_cap() (Dan Carpenter)
- usb: typec: fsa4480: Check if the chip is really there (Konrad Dybcio)
- usb: gadget: core: Check for unset descriptor (Chris Wulff)
- usb: vhci-hcd: Do not drop references before new references are gained (Oliver Neukum)
- usb: gadget: u_audio: Check return codes from usb_ep_enable and config_ep_by_speed. (Chris Wulff)
- usb: gadget: midi2: Fix the response for FB info with block 0xff (Takashi Iwai)
- dt-bindings: usb: microchip,usb2514: Add USB2517 compatible (Alexander Stein)
- USB: serial: garmin_gps: use struct_size() to allocate pkt (Javier Carrasco)
- USB: serial: garmin_gps: annotate struct garmin_packet with __counted_by (Javier Carrasco)
- USB: serial: add missing MODULE_DESCRIPTION() macros (Jeff Johnson)
- USB: serial: spcp8x5: remove unused struct 'spcp8x5_usb_ctrl_arg' (Dr. David Alan Gilbert)
- tty: vt: conmakehash: cope with abs_srctree no longer in env (Max Krummenacher)
- serial: sc16is7xx: fix invalid FIFO access with special register set (Hugo Villeneuve)
- serial: sc16is7xx: fix TX fifo corruption (Hugo Villeneuve)
- serial: core: check uartclk for zero to avoid divide by zero (George Kennedy)
- driver core: Fix uevent_show() vs driver detach race (Dan Williams)
- Documentation: embargoed-hardware-issues.rst: add a section documenting the "early access" process (Greg Kroah-Hartman)
- Documentation: embargoed-hardware-issues.rst: minor cleanups and fixes (Greg Kroah-Hartman)
- rust: firmware: fix invalid rustdoc link (Andrew Ballance)
- spmi: pmic-arb: add missing newline in dev_err format strings (David Collins)
- spmi: pmic-arb: Pass the correct of_node to irq_domain_add_tree (Konrad Dybcio)
- binder_alloc: Fix sleeping function called from invalid context (Mukesh Ojha)
- binder: fix descriptor lookup for context manager (Carlos Llamas)
- char: add missing NetWinder MODULE_DESCRIPTION() macros (Jeff Johnson)
- misc: mrvl-cn10k-dpi: add PCI_IOV dependency (Arnd Bergmann)
- eeprom: ee1004: Fix locking issues in ee1004_probe() (Armin Wolf)
- fsi: add missing MODULE_DESCRIPTION() macros (Jeff Johnson)
- scsi: sd: Keep the discard mode stable (Li Feng)
- scsi: sd: Move sd_read_cpr() out of the q->limits_lock region (Shin'ichiro Kawasaki)
- scsi: ufs: core: Fix hba->last_dme_cmd_tstamp timestamp updating logic (Vamshi Gajjela)
- nfsd: don't set SVC_SOCK_ANONYMOUS when creating nfsd sockets (Jeff Layton)
- sunrpc: avoid -Wformat-security warning (Arnd Bergmann)
- i2c: qcom-geni: Add missing geni_icc_disable in geni_i2c_runtime_resume (Gaosheng Cui)
- i2c: qcom-geni: Add missing clk_disable_unprepare in geni_i2c_runtime_resume (Gaosheng Cui)
- i2c: testunit: match HostNotify test name with docs (Wolfram Sang)
- i2c: Fix conditional for substituting empty ACPI functions (Richard Fitzgerald)
- i2c: smbus: Send alert notifications to all devices if source not found (Guenter Roeck)
- i2c: smbus: Improve handling of stuck alerts (Guenter Roeck)
- dma-debug: avoid deadlock between dma debug vs printk and netconsole (Rik van Riel)
- bcachefs: bcachefs_metadata_version_disk_accounting_v3 (Kent Overstreet)
- bcachefs: improve bch2_dev_usage_to_text() (Kent Overstreet)
- bcachefs: bch2_accounting_invalid() (Kent Overstreet)
- bcachefs: Switch to .get_inode_acl() (Kent Overstreet)
- cifs: cifs_inval_name_dfs_link_error: correct the check for fullpath (Gleb Korobeynikov)
- Fix spelling errors in Server Message Block (Xiaxi Shen)
- smb3: fix setting SecurityFlags when encryption is required (Steve French)
- spi: spi-fsl-lpspi: Fix scldiv calculation (Stefan Wahren)
- spi: spidev: Add missing spi_device_id for bh2228fv (Geert Uytterhoeven)
- spi: hisi-kunpeng: Add verification for the max_frequency provided by the firmware (Devyn Liu)
- spi: hisi-kunpeng: Add validation for the minimum value of speed_hz (Devyn Liu)
- drm/i915: Attempt to get pages without eviction first (David Gow)
- drm/i915: Allow evicting to use the requested placement (David Gow)
- drm/i915/gem: Fix Virtual Memory mapping boundaries calculation (Andi Shyti)
- drm/i915/gem: Adjust vma offset for framebuffer mmap offset (Andi Shyti)
- drm/i915/display: correct dual pps handling for MTL_PCH+ (Dnyaneshwar Bhadane)
- drm/xe: Take ref to VM in delayed snapshot (Matthew Brost)
- drm/xe/hwmon: Fix PL1 disable flow in xe_hwmon_power_max_write (Karthik Poosa)
- drm/xe: Use dma_fence_chain_free in chain fence unused as a sync (Matthew Brost)
- drm/xe/rtp: Fix off-by-one when processing rules (Lucas De Marchi)
- drm/amdgpu: Add DCC GFX12 flag to enable address alignment (Arunpravin Paneer Selvam)
- drm/amdgpu: correct sdma7 max dw (Frank Min)
- drm/amdgpu: Add address alignment support to DCC buffers (Arunpravin Paneer Selvam)
- drm/amd/display: Skip Recompute DSC Params if no Stream on Link (Fangzhi Zuo)
- drm/amdgpu: change non-dcc buffer copy configuration (Frank Min)
- drm/amdgpu: Forward soft recovery errors to userspace (Joshua Ashton)
- drm/amdgpu: add golden setting for gc v12 (Likun Gao)
- drm/buddy: Add start address support to trim function (Arunpravin Paneer Selvam)
- drm/amd/display: Add missing program DET segment call to pipe init (Rodrigo Siqueira)
- drm/amd/display: Add missing DCN314 to the DML Makefile (Rodrigo Siqueira)
- drm/amdgpu: force to use legacy inv in mmhub (Likun Gao)
- drm/amd/pm: update powerplay structure on smu v14.0.2/3 (Kenneth Feng)
- drm/amd/display: Add missing mcache registers (Rodrigo Siqueira)
- drm/amd/display: Add dcc propagation value (Rodrigo Siqueira)
- drm/amd/display: Add missing DET segments programming (Rodrigo Siqueira)
- drm/amd/display: Replace dm_execute_dmub_cmd with dc_wake_and_execute_dmub_cmd (Rodrigo Siqueira)
- drm/atomic: allow no-op FB_ID updates for async flips (Simon Ser)
- dt-bindings: display: panel: samsung,atna45dc02: Document ATNA45DC02 (Rob Clark)
- drm/bridge-connector: Fix double free in error handling paths (Cristian Ciocaltea)
- drm/omap: add CONFIG_MMU dependency (Arnd Bergmann)
- drm/test: fix the gem shmem test to map the sg table. (Dave Airlie)
- drm/client: fix null pointer dereference in drm_client_modeset_probe (Ma Ke)
- cpumask: Fix crash on updating CPU enabled mask (Gavin Shan)
- cpufreq: intel_pstate: Update Balance performance EPP for Emerald Rapids (Pedro Henrique Kopper)
- syscalls: add back legacy __NR_nfsservctl macro (Arnd Bergmann)
- syscalls: fix fstat() entry again (Arnd Bergmann)
- arm64: dts: ti: k3-j784s4-main: Correct McASP DMAs (Parth Pancholi)
- arm64: dts: ti: k3-j722s: Fix gpio-range for main_pmx0 (Jared McArthur)
- arm64: dts: ti: k3-am62p: Fix gpio-range for main_pmx0 (Jared McArthur)
- arm64: dts: ti: k3-am62p: Add gpio-ranges for mcu_gpio0 (Jared McArthur)
- arm64: dts: ti: k3-am62-verdin-dahlia: Keep CTRL_SLEEP_MOCI# regulator on (Francesco Dolcini)
- arm64: dts: ti: k3-j784s4-evm: Consolidate serdes0 references (Andrew Halaney)
- arm64: dts: ti: k3-j784s4-evm: Assign only lanes 0 and 1 to PCIe1 (Andrew Halaney)
- ARM: pxa/gumstix: fix attaching properties to vbus gpio device (Dmitry Torokhov)
- doc: platform: cznic: turris-omnia-mcu: Use double backticks for attribute value (Marek Behún)
- doc: platform: cznic: turris-omnia-mcu: Fix sphinx-build warning (Marek Behún)
- platform: cznic: turris-omnia-mcu: Make GPIO code optional (Marek Behún)
- platform: cznic: turris-omnia-mcu: Make poweroff and wakeup code optional (Marek Behún)
- platform: cznic: turris-omnia-mcu: Make TRNG code optional (Marek Behún)
- platform: cznic: turris-omnia-mcu: Make watchdog code optional (Marek Behún)
- kprobes: Fix to check symbol prefixes correctly (Masami Hiramatsu (Google))
- bpf: kprobe: remove unused declaring of bpf_kprobe_override (Menglong Dong)
- nvme: reorganize nvme_ns_head fields (Kanchan Joshi)
- nvme: change data type of lba_shift (Kanchan Joshi)
- nvme: remove a field from nvme_ns_head (Kanchan Joshi)
- nvme: remove unused parameter (Kanchan Joshi)
- blk-throttle: remove more latency dead-code (Dr. David Alan Gilbert)
- io_uring/net: don't pick multiple buffers for non-bundle send (Jens Axboe)
- io_uring/net: ensure expanded bundle send gets marked for cleanup (Jens Axboe)
- io_uring/net: ensure expanded bundle recv gets marked for cleanup (Jens Axboe)
- ASoC: cs35l56: Patch CS35L56_IRQ1_MASK_18 to the default value (Simon Trimmer)
- ASoC: meson: axg-fifo: fix irq scheduling issue with PREEMPT_RT (Jerome Brunet)
- MAINTAINERS: Update Cirrus Logic parts to linux-sound mailing list (Charles Keepax)
- ASoC: dt-bindings: qcom,wcd939x: Correct reset GPIO polarity in example (Krzysztof Kozlowski)
- ASoC: dt-bindings: qcom,wcd938x: Correct reset GPIO polarity in example (Krzysztof Kozlowski)
- ASoC: dt-bindings: qcom,wcd934x: Correct reset GPIO polarity in example (Krzysztof Kozlowski)
- ASoC: dt-bindings: qcom,wcd937x: Correct reset GPIO polarity in example (Krzysztof Kozlowski)
- ASoC: amd: yc: Add quirk entry for OMEN by HP Gaming Laptop 16-n0xxx (Takashi Iwai)
- ASoC: codecs: ES8326: button detect issue (Zhang Yi)
- ASoC: amd: yc: Support mic on Lenovo Thinkpad E14 Gen 6 (Krzysztof Stępniak)
- ASoC: cs35l56: Stop creating ALSA controls for firmware coefficients (Simon Trimmer)
- ASoC: wm_adsp: Add control_add callback and export wm_adsp_control_add() (Simon Trimmer)
- ASoC: cs35l56: Handle OTP read latency over SoundWire (Richard Fitzgerald)
- ASoC: codecs: lpass-macro: fix missing codec version (Johan Hovold)
- ASoC: cs-amp-lib: Fix NULL pointer crash if efi.get_variable is NULL (Richard Fitzgerald)
- ASoC: cs42l43: Cache shutter IRQ control pointers (Charles Keepax)
- ASoC: cs35l45: Use new snd_soc_component_get_kcontrol_locked() helper (Charles Keepax)
- ASoC: soc-component: Add new snd_soc_component_get_kcontrol() helpers (Charles Keepax)
- ASoC: cs42l43: Remove redundant semi-colon at end of function (Charles Keepax)
- ASoC: SOF: Remove libraries from topology lookups (Curtis Malainey)
- ASoC: nau8822: Lower debug print priority (Francesco Dolcini)
- ASoC: fsl_micfil: Differentiate register access permission for platforms (Shengjiu Wang)
- ASoC: fsl_micfil: Expand the range of FIFO watermark mask (Shengjiu Wang)
- ASoC: codecs: wsa884x: Correct Soundwire ports mask (Krzysztof Kozlowski)
- ASoC: codecs: wsa883x: Correct Soundwire ports mask (Krzysztof Kozlowski)
- ASoC: codecs: wsa881x: Correct Soundwire ports mask (Krzysztof Kozlowski)
- ASoC: codecs: wcd939x-sdw: Correct Soundwire ports mask (Krzysztof Kozlowski)
- ASoC: codecs: wcd938x-sdw: Correct Soundwire ports mask (Krzysztof Kozlowski)
- ASoC: codecs: wcd937x-sdw: Correct Soundwire ports mask (Krzysztof Kozlowski)
- ASoC: cs530x: Change IN HPF Select kcontrol name (Paul Handrigan)
- ASoC: amd: yc: Support mic on HP 14-em0002la (Bruno Ancona)
- ASoC: sti: add missing probe entry for player and reader (Jerome Audu)
- ALSA: usb-audio: Re-add ScratchAmp quirk entries (Takashi Iwai)
- ALSA: hda/realtek: Add Framework Laptop 13 (Intel Core Ultra) to quirks (Dustin L. Howett)
- ALSA: hda/hdmi: Yet more pin fix for HP EliteDesk 800 G4 (Takashi Iwai)
- ALSA: hda: Add HP MP9 G4 Retail System AMS to force connect list (Steven 'Steve' Kendall)
- ALSA: line6: Fix racy access to midibuf (Takashi Iwai)
- ALSA: hda: cs35l41: Stop creating ALSA Controls for firmware coefficients (Stefan Binding)
- ALSA: hda: cs35l56: Stop creating ALSA controls for firmware coefficients (Simon Trimmer)
- module: make waiting for a concurrent module loader interruptible (Linus Torvalds)
- kernel: config: enable erofs lzma compression (Ian Kent)
- fedora: disable RTL8192CU in Fedora (Peter Robinson)
- ice: Fix incorrect assigns of FEC counts (Mateusz Polchlopek)
- ice: Skip PTP HW writes during PTP reset procedure (Grzegorz Nitka)
- ice: Fix reset handler (Grzegorz Nitka)
- net: dsa: microchip: disable EEE for KSZ8567/KSZ9567/KSZ9896/KSZ9897. (Martin Whitaker)
- ethtool: Fix context creation with no parameters (Gal Pressman)
- net: ethtool: fix off-by-one error in max RSS context IDs (Edward Cree)
- net: pse-pd: tps23881: include missing bitfield.h header (Arnd Bergmann)
- net: fec: Stop PPS on driver remove (Csókás, Bence)
- net: bcmgenet: Properly overlay PHY and MAC Wake-on-LAN capabilities (Florian Fainelli)
- l2tp: fix lockdep splat (James Chapman)
- net: stmmac: dwmac4: fix PCS duplex mode decode (Russell King (Oracle))
- Bluetooth: hci_sync: avoid dup filtering when passive scanning with adv monitor (Anton Khirnov)
- Bluetooth: l2cap: always unlock channel in l2cap_conless_channel() (Dmitry Antipov)
- Bluetooth: hci_qca: fix a NULL-pointer derefence at shutdown (Bartosz Golaszewski)
- Bluetooth: hci_qca: fix QCA6390 support on non-DT platforms (Bartosz Golaszewski)
- Bluetooth: hci_qca: don't call pwrseq_power_off() twice for QCA6390 (Bartosz Golaszewski)
- idpf: fix UAFs when destroying the queues (Alexander Lobakin)
- idpf: fix memleak in vport interrupt configuration (Michal Kubiak)
- idpf: fix memory leaks and crashes while performing a soft reset (Alexander Lobakin)
- bnxt_en : Fix memory out-of-bounds in bnxt_fill_hw_rss_tbl() (Michael Chan)
- net: dsa: bcm_sf2: Fix a possible memory leak in bcm_sf2_mdio_register() (Joe Hattori)
- net/smc: add the max value of fallback reason count (Zhengchao Shao)
- net: usb: qmi_wwan: add MeiG Smart SRM825L (ZHANG Yuntian)
- net: dsa: microchip: Fix Wake-on-LAN check to not return an error (Tristram Ha)
- net: linkwatch: use system_unbound_wq (Eric Dumazet)
- net: bridge: mcast: wait for previous gc cycles when removing port (Nikolay Aleksandrov)
- net: usb: qmi_wwan: fix memory leak for not ip packets (Daniele Palmas)
- virtio-net: unbreak vq resizing when coalescing is not negotiated (Heng Qi)
- virtio-net: check feature before configuring the vq coalescing command (Heng Qi)
- net/tcp: Disable TCP-AO static key after RCU grace period (Dmitry Safonov)
- gve: Fix use of netif_carrier_ok() (Praveen Kaligineedi)
- net: pse-pd: tps23881: Fix the device ID check (Kyle Swenson)
- sctp: Fix null-ptr-deref in reuseport_add_sock(). (Kuniyuki Iwashima)
- MAINTAINERS: update status of sky2 and skge drivers (Stephen Hemminger)
- selftests: mptcp: join: test both signal & subflow (Matthieu Baerts (NGI0))
- selftests: mptcp: join: ability to invert ADD_ADDR check (Matthieu Baerts (NGI0))
- mptcp: pm: do not ignore 'subflow' if 'signal' flag is also set (Matthieu Baerts (NGI0))
- mptcp: pm: don't try to create sf if alloc failed (Matthieu Baerts (NGI0))
- mptcp: pm: reduce indentation blocks (Matthieu Baerts (NGI0))
- mptcp: pm: deny endp with signal + subflow + port (Matthieu Baerts (NGI0))
- mptcp: fully established after ADD_ADDR echo on MPJ (Matthieu Baerts (NGI0))
- tracefs: Use generic inode RCU for synchronizing freeing (Steven Rostedt)
- ring-buffer: Remove unused function ring_buffer_nr_pages() (Jianhui Zhou)
- tracing: Fix overflow in get_free_elt() (Tze-nan Wu)
- function_graph: Fix the ret_stack used by ftrace_graph_ret_addr() (Petr Pavlu)
- eventfs: Use SRCU for freeing eventfs_inodes (Mathias Krause)
- eventfs: Don't return NULL in eventfs_create_dir() (Mathias Krause)
- tracefs: Fix inode allocation (Mathias Krause)
- tracing: Use refcount for trace_event_file reference counter (Steven Rostedt)
- tracing: Have format file honor EVENT_FILE_FL_FREED (Steven Rostedt)
- bcachefs: Use bch2_wait_on_allocator() in btree node alloc path (Kent Overstreet)
- bcachefs: Make allocator stuck timeout configurable, ratelimit messages (Kent Overstreet)
- bcachefs: Add missing path_traverse() to btree_iter_next_node() (Kent Overstreet)
- bcachefs: ec should not allocate from ro devs (Kent Overstreet)
- bcachefs: Improved allocator debugging for ec (Kent Overstreet)
- bcachefs: Add missing bch2_trans_begin() call (Kent Overstreet)
- bcachefs: Add a comment for bucket helper types (Kent Overstreet)
- bcachefs: Don't rely on implicit unsigned -> signed integer conversion (Kent Overstreet)
- lockdep: Fix lockdep_set_notrack_class() for CONFIG_LOCK_STAT (Kent Overstreet)
- bcachefs: Fix double free of ca->buckets_nouse (Kent Overstreet)
- module: warn about excessively long module waits (Linus Torvalds)
- LoongArch: KVM: Remove undefined a6 argument comment for kvm_hypercall() (Dandan Zhang)
- LoongArch: KVM: Remove unnecessary definition of KVM_PRIVATE_MEM_SLOTS (Yuli Wang)
- LoongArch: Use accessors to page table entries instead of direct dereference (Huacai Chen)
- LoongArch: Enable general EFI poweroff method (Miao Wang)
- padata: Fix possible divide-by-0 panic in padata_mt_helper() (Waiman Long)
- mailmap: update entry for David Heidelberg (David Heidelberg)
- memcg: protect concurrent access to mem_cgroup_idr (Shakeel Butt)
- mm: shmem: fix incorrect aligned index when checking conflicts (Baolin Wang)
- mm: shmem: avoid allocating huge pages larger than MAX_PAGECACHE_ORDER for shmem (Baolin Wang)
- mm: list_lru: fix UAF for memory cgroup (Muchun Song)
- kcov: properly check for softirq context (Andrey Konovalov)
- MAINTAINERS: Update LTP members and web (Petr Vorel)
- selftests: mm: add s390 to ARCH check (Nico Pache)
- redhat: Fix the ownership of /lib/modules/<kversion> directory (Vitaly Kuznetsov)
- new configs in drivers/phy (Izabela Bakollari)
- Add support to rh_waived cmdline boot parameter (Ricardo Robaina) [RHEL-26170]
- Linux v6.11.0-0.rc3

* Fri Aug 09 2024 Jan Stancek <jstancek@redhat.com> [6.11.0-0.rc2.17.el10]
- btrfs: avoid using fixed char array size for tree names (Qu Wenruo)
- btrfs: fix double inode unlock for direct IO sync writes (Filipe Manana)
- btrfs: emit a warning about space cache v1 being deprecated (Josef Bacik)
- btrfs: fix qgroup reserve leaks in cow_file_range (Boris Burkov)
- btrfs: implement launder_folio for clearing dirty page reserve (Boris Burkov)
- btrfs: scrub: update last_physical after scrubbing one stripe (Qu Wenruo)
- btrfs: factor out stripe length calculation into a helper (Qu Wenruo)
- power: supply: qcom_battmgr: Ignore extra __le32 in info payload (Stephan Gerhold)
- power: supply: qcom_battmgr: return EAGAIN when firmware service is not up (Neil Armstrong)
- power: supply: axp288_charger: Round constant_charge_voltage writes down (Hans de Goede)
- power: supply: axp288_charger: Fix constant_charge_voltage writes (Hans de Goede)
- power: supply: rt5033: Bring back i2c_set_clientdata (Nikita Travkin)
- vhost-vdpa: switch to use vmf_insert_pfn() in the fault handler (Jason Wang)
- platform/x86/intel/ifs: Initialize union ifs_status to zero (Kuppuswamy Sathyanarayanan)
- platform/x86: msi-wmi-platform: Fix spelling mistakes (Luis Felipe Hernandez)
- platform/x86/amd/pmf: Add new ACPI ID AMDI0107 (Shyam Sundar S K)
- platform/x86/amd/pmc: Send OS_HINT command for new AMD platform (Shyam Sundar S K)
- platform/x86/amd: pmf: Add quirk for ROG Ally X (Luke D. Jones)
- platform/x86: intel-vbtn: Protect ACPI notify handler against recursion (Hans de Goede)
- selftests: ksft: Fix finished() helper exit code on skipped tests (Laura Nao)
- mm, slub: do not call do_slab_free for kfence object (Rik van Riel)
- redhat/configs: Disable gfs2 in rhel configs (Andrew Price)
- redhat/uki_addons/virt: add common FIPS addon (Emanuele Giuseppe Esposito)
- redhat/kernel.spec: add uki_addons to create UKI kernel cmdline addons (Emanuele Giuseppe Esposito)
- Linux v6.11.0-0.rc2

* Tue Aug 06 2024 Jan Stancek <jstancek@redhat.com> [6.11.0-0.rc2.16.el10]
- Linux 6.11-rc2 (Linus Torvalds)
- profiling: remove profile=sleep support (Tetsuo Handa)
- x86/uaccess: Zero the 8-byte get_range case on failure on 32-bit (David Gow)
- x86/mm: Fix pti_clone_entry_text() for i386 (Peter Zijlstra)
- x86/mm: Fix pti_clone_pgtable() alignment assumption (Peter Zijlstra)
- x86/setup: Parse the builtin command line before merging (Borislav Petkov (AMD))
- x86/CPU/AMD: Add models 0x60-0x6f to the Zen5 range (Perry Yuan)
- x86/sev: Fix __reserved field in sev_config (Pavan Kumar Paluri)
- x86/aperfmperf: Fix deadlock on cpu_hotplug_lock (Jonathan Cameron)
- clocksource: Fix brown-bag boolean thinko in cs_watchdog_read() (Paul E. McKenney)
- tick/broadcast: Move per CPU pointer access into the atomic section (Thomas Gleixner)
- sched/core: Fix unbalance set_rq_online/offline() in sched_cpu_deactivate() (Yang Yingliang)
- sched/core: Introduce sched_set_rq_on/offline() helper (Yang Yingliang)
- sched/smt: Fix unbalance sched_smt_present dec/inc (Yang Yingliang)
- sched/smt: Introduce sched_smt_present_inc/dec() helper (Yang Yingliang)
- sched/cputime: Fix mul_u64_u64_div_u64() precision for cputime (Zheng Zucheng)
- perf/x86: Fix smp_processor_id()-in-preemptible warnings (Li Huafei)
- perf/x86/intel/cstate: Add pkg C2 residency counter for Sierra Forest (Zhenyu Wang)
- irqchip/mbigen: Fix mbigen node address layout (Yipeng Zou)
- irqchip/meson-gpio: Convert meson_gpio_irq_controller::lock to 'raw_spinlock_t' (Arseniy Krasnov)
- irqchip/irq-pic32-evic: Add missing 'static' to internal function (Luca Ceresoli)
- irqchip/loongarch-cpu: Fix return value of lpic_gsi_to_irq() (Huacai Chen)
- jump_label: Fix the fix, brown paper bags galore (Peter Zijlstra)
- locking/pvqspinlock: Correct the type of "old" variable in pv_kick_node() (Uros Bizjak)
- arm: dts: arm: versatile-ab: Fix duplicate clock node name (Rob Herring (Arm))
- cifs: update internal version number (Steve French)
- smb: client: fix FSCTL_GET_REPARSE_POINT against NetApp (Paulo Alcantara)
- smb3: add dynamic tracepoints for shutdown ioctl (Steve French)
- cifs: Remove cifs_aio_ctx (David Howells)
- smb: client: handle lack of FSCTL_GET_REPARSE_POINT support (Paulo Alcantara)
- media: uvcvideo: Fix custom control mapping probing (Ricardo Ribalda)
- media: v4l: Fix missing tabular column hint for Y14P format (Jean-Michel Hautbois)
- media: intel/ipu6: select AUXILIARY_BUS in Kconfig (Bingbu Cao)
- media: ipu-bridge: fix ipu6 Kconfig dependencies (Arnd Bergmann)
- rh_flags: fix failed when register_sysctl_sz rh_flags_table to kernel (Ricardo Robaina) [RHEL-52629]
- redhat: regenerate test-data (Jan Stancek) [RHEL-29722]
- redhat: rpminspect.yaml: more tests to ignore selftests (Jan Stancek)
- gitlab-ci: add initial version (Michael Hofmann)
- redhat/Makefile.variables: don't set DISTRO (Jan Stancek) [RHEL-29722]
- redhat/Makefile.variables: set PATCHLIST_URL to none (Jan Stancek) [RHEL-29722]
- redhat/kernel.spec.template: fix with_realtime (Jan Stancek) [RHEL-29722]
- remove ARK .gitlab-ci.yml (Jan Stancek)
- redhat: update rpminspect with c9s one (Jan Stancek)
- redhat: remove fedora configs and files (Jan Stancek)
- redhat: init RHEL10.0 beta variables and dist tag (Jan Stancek) [RHEL-29722]
- scsi: ufs: exynos: Don't resume FMP when crypto support is disabled (Eric Biggers)
- scsi: mpt3sas: Avoid IOMMU page faults on REPORT ZONES (Damien Le Moal)
- scsi: mpi3mr: Avoid IOMMU page faults on REPORT ZONES (Damien Le Moal)
- scsi: ufs: core: Do not set link to OFF state while waking up from hibernation (Manivannan Sadhasivam)
- scsi: Revert "scsi: sd: Do not repeat the starting disk message" (Johan Hovold)
- scsi: ufs: core: Fix deadlock during RTC update (Peter Wang)
- scsi: ufs: core: Bypass quick recovery if force reset is needed (Peter Wang)
- scsi: ufs: core: Check LSDBS cap when !mcq (Kyoungrul Kim)
- xfs: convert comma to semicolon (Chen Ni)
- xfs: convert comma to semicolon (Chen Ni)
- xfs: remove unused parameter in macro XFS_DQUOT_LOGRES (Julian Sun)
- xfs: fix file_path handling in tracepoints (Darrick J. Wong)
- xfs: allow SECURE namespace xattrs to use reserved block pool (Eric Sandeen)
- xfs: fix a memory leak (Darrick J. Wong)
- parisc: fix a possible DMA corruption (Mikulas Patocka)
- parisc: fix unaligned accesses in BPF (Mikulas Patocka)
- runtime constants: deal with old decrepit linkers (Linus Torvalds)
- redhat: enable changes to build rt variants (Clark Williams)
- Add localversion for -RT release (Thomas Gleixner)
- sysfs: Add /sys/kernel/realtime entry (Clark Williams)
- riscv: add PREEMPT_AUTO support (Jisheng Zhang)
- POWERPC: Allow to enable RT (Sebastian Andrzej Siewior)
- powerpc/stackprotector: work around stack-guard init from atomic (Sebastian Andrzej Siewior)
- powerpc/kvm: Disable in-kernel MPIC emulation for PREEMPT_RT (Bogdan Purcareata)
- powerpc/pseries: Select the generic memory allocator. (Sebastian Andrzej Siewior)
- powerpc/pseries/iommu: Use a locallock instead local_irq_save() (Sebastian Andrzej Siewior)
- powerpc: traps: Use PREEMPT_RT (Sebastian Andrzej Siewior)
- ARM: Allow to enable RT (Sebastian Andrzej Siewior)
- ARM: vfp: Move sending signals outside of vfp_lock()ed section. (Sebastian Andrzej Siewior)
- ARM: vfp: Use vfp_lock() in vfp_support_entry(). (Sebastian Andrzej Siewior)
- ARM: vfp: Use vfp_lock() in vfp_sync_hwstate(). (Sebastian Andrzej Siewior)
- ARM: vfp: Provide vfp_lock() for VFP locking. (Sebastian Andrzej Siewior)
- arm: Disable FAST_GUP on PREEMPT_RT if HIGHPTE is also enabled. (Sebastian Andrzej Siewior)
- ARM: enable irq in translation/section permission fault handlers (Yadi.hu)
- arm: Disable jump-label on PREEMPT_RT. (Thomas Gleixner)
- tun: Add missing bpf_net_ctx_clear() in do_xdp_generic() (Jeongjun Park)
- sched: define TIF_ALLOW_RESCHED (Thomas Gleixner)
- Revert "drm/i915: Depend on !PREEMPT_RT." (Sebastian Andrzej Siewior)
- drm/i915/guc: Consider also RCU depth in busy loop. (Sebastian Andrzej Siewior)
- drm/i915: Drop the irqs_disabled() check (Sebastian Andrzej Siewior)
- drm/i915/gt: Use spin_lock_irq() instead of local_irq_disable() + spin_lock() (Sebastian Andrzej Siewior)
- drm/i915: Disable tracing points on PREEMPT_RT (Sebastian Andrzej Siewior)
- drm/i915: Don't check for atomic context on PREEMPT_RT (Sebastian Andrzej Siewior)
- drm/i915: Don't disable interrupts on PREEMPT_RT during atomic updates (Mike Galbraith)
- drm/i915: Use preempt_disable/enable_rt() where recommended (Mike Galbraith)
- time: Allow to preempt after a callback. (Sebastian Andrzej Siewior)
- softirq: Add function to preempt serving softirqs. (Sebastian Andrzej Siewior)
- sched/core: Provide a method to check if a task is PI-boosted. (Sebastian Andrzej Siewior)
- zram: Shrink zram_table_entry::flags. (Sebastian Andrzej Siewior)
- zram: Remove ZRAM_LOCK (Sebastian Andrzej Siewior)
- zram: Replace bit spinlocks with a spinlock_t. (Mike Galbraith)
- softirq: Wake ktimers thread also in softirq. (Junxiao Chang)
- tick: Fix timer storm since introduction of timersd (Frederic Weisbecker)
- rcutorture: Also force sched priority to timersd on boosting test. (Frederic Weisbecker)
- softirq: Use a dedicated thread for timer wakeups. (Sebastian Andrzej Siewior)
- sched/rt: Don't try push tasks if there are none. (Sebastian Andrzej Siewior)
- riscv: allow to enable RT (Jisheng Zhang)
- ARM64: Allow to enable RT (Sebastian Andrzej Siewior)
- x86: Enable RT also on 32bit (Sebastian Andrzej Siewior)
- x86: Allow to enable RT (Sebastian Andrzej Siewior)
- prinkt/nbcon: Add a scheduling point to nbcon_kthread_func(). (Sebastian Andrzej Siewior)
- serial: 8250: Revert "drop lockdep annotation from serial8250_clear_IER()" (John Ogness)
- serial: 8250: Switch to nbcon console (John Ogness)
- printk: nbcon: Add function for printers to reacquire ownership (John Ogness)
- printk: Avoid false positive lockdep report for legacy printing (John Ogness)
- printk: Provide threadprintk boot argument (John Ogness)
- tty: sysfs: Add nbcon support for 'active' (John Ogness)
- proc: Add nbcon support for /proc/consoles (John Ogness)
- proc: consoles: Add notation to c_start/c_stop (John Ogness)
- printk: Add kthread for all legacy consoles (John Ogness)
- printk: nbcon: Show replay message on takeover (John Ogness)
- printk: Provide helper for message prepending (John Ogness)
- printk: nbcon: Start printing threads (John Ogness)
- printk: nbcon: Stop threads on shutdown/reboot (John Ogness)
- printk: nbcon: Add printer thread wakeups (Thomas Gleixner)
- printk: nbcon: Add context to console_is_usable() (John Ogness)
- printk: nbcon: Fix nbcon_cpu_emergency_flush() when preemptible (John Ogness)
- printk: Atomic print in printk context on shutdown (John Ogness)
- printk: nbcon: Introduce printing kthreads (Thomas Gleixner)
- lockdep: Mark emergency sections in lockdep splats (John Ogness)
- rcu: Mark emergency sections in rcu stalls (John Ogness)
- panic: Mark emergency section in oops (John Ogness)
- panic: Mark emergency section in warn (Thomas Gleixner)
- printk: nbcon: Implement emergency sections (Thomas Gleixner)
- printk: Coordinate direct printing in panic (John Ogness)
- printk: Track nbcon consoles (John Ogness)
- printk: Avoid console_lock dance if no legacy or boot consoles (John Ogness)
- printk: nbcon: Add unsafe flushing on panic (John Ogness)
- printk: nbcon: Use nbcon consoles in console_flush_all() (John Ogness)
- printk: Track registered boot consoles (John Ogness)
- printk: nbcon: Provide function to flush using write_atomic() (Thomas Gleixner)
- printk: nbcon: Add helper to assign priority based on CPU state (John Ogness)
- printk: Add @flags argument for console_is_usable() (John Ogness)
- printk: Let console_is_usable() handle nbcon (John Ogness)
- printk: Make console_is_usable() available to nbcon (John Ogness)
- printk: nbcon: Do not rely on proxy headers (John Ogness)
- serial: core: Implement processing in port->lock wrapper (John Ogness)
- nbcon: Add API to acquire context for non-printing operations (John Ogness)
- console: Improve console_srcu_read_flags() comments (John Ogness)
- serial: core: Introduce wrapper to set @uart_port->cons (John Ogness)
- serial: core: Provide low-level functions to lock port (John Ogness)
- printk: nbcon: Use driver synchronization while (un)registering (John Ogness)
- printk: nbcon: Add callbacks to synchronize with driver (John Ogness)
- printk: nbcon: Add detailed doc for write_atomic() (John Ogness)
- printk: Check printk_deferred_enter()/_exit() usage (Sebastian Andrzej Siewior)
- printk: nbcon: Remove return value for write_atomic() (John Ogness)
- printk: Properly deal with nbcon consoles on seq init (Petr Mladek)
- printk: Add notation to console_srcu locking (John Ogness)
- crypto: x86/aes-gcm: Disable FPU around skcipher_walk_done(). (Sebastian Andrzej Siewior)
- task_work: make TWA_NMI_CURRENT handling conditional on IRQ_WORK (Linus Torvalds)


###
# The following Emacs magic makes C-c C-e use UTC dates.
# Local Variables:
# rpm-change-log-uses-utc: t
# End:
###
