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
%define uname_suffix %{lua:
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
%define uname_variant %{lua:
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
%define specrpmversion 6.9.0
%define specversion 6.9.0
%define patchversion 6.9
%define pkgrelease 0.rc7.5
%define kversion 6
%define tarfile_release 6.9.0-0.rc7.5.el10
# This is needed to do merge window version magic
%define patchlevel 9
# This allows pkg_release to have configurable %%{?dist} tag
%define specrelease 0.rc7.5%{?buildid}%{?dist}
# This defines the kabi tarball version
%define kabiversion 6.9.0-0.rc7.5.el10

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
%define klptestarches x86_64 ppc64le

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
BuildRequires: zlib-devel binutils-devel
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
# For TPM operations in UKI initramfs
BuildRequires: tpm2-tools
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

Source100: rheldup3.x509
Source101: rhelkpatch1.x509
Source102: nvidiagpuoot001.x509

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
%define bpftoolversion 7.4.0
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
%{expand:%%kernel_kvm_package %{?1:%{1}}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%else \
%if %{with_efiuki}\
%package %{?1:%{1}-}uki-virt\
Summary: %{variant_summary} unified kernel image for virtual machines\
Provides: installonlypkg(kernel)\
Provides: kernel-%{?1:%{1}-}uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires: kernel%{?1:-%{1}}-modules-core-uname-r = %{KVERREL}%{uname_suffix %{?1:+%{1}}}\
Requires(pre): %{kernel_prereq}\
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
%endif

%if %{with_up_base} && %{with_efiuki}
%description uki-virt
Prebuilt default unified kernel image for virtual machines.
%endif

%if %{with_arm64_16k} && %{with_debug} && %{with_efiuki}
%description 16k-debug-uki-virt
Prebuilt 16k debug unified kernel image for virtual machines.
%endif

%if %{with_arm64_16k_base} && %{with_efiuki}
%description 16k-uki-virt
Prebuilt 16k unified kernel image for virtual machines.
%endif

%if %{with_arm64_64k} && %{with_debug} && %{with_efiuki}
%description 64k-debug-uki-virt
Prebuilt 64k debug unified kernel image for virtual machines.
%endif

%if %{with_arm64_64k_base} && %{with_efiuki}
%description 64k-uki-virt
Prebuilt 64k unified kernel image for virtual machines.
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

# Add DUP and kpatch certificates to system trusted keys for RHEL
%if 0%{?rhel}
%{log_msg "Add DUP and kpatch certificates to system trusted keys for RHEL"}
%if %{signkernel}%{signmodules}
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
for i in *.config; do
  sed -i 's@CONFIG_SYSTEM_TRUSTED_KEYS=""@CONFIG_SYSTEM_TRUSTED_KEYS="certs/rhel.pem"@' $i
done
%endif
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
    cp -a --parents tools/bpf/resolve_btfids/main.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a --parents tools/bpf/resolve_btfids/Build $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    cp --parents security/selinux/include/policycap_names.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp --parents security/selinux/include/policycap.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

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
%ifarch aarch64
    # arch/arm64/include/asm/xen references arch/arm
    cp -a --parents arch/arm/include/asm/xen $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    # arch/arm64/include/asm/opcodes.h references arch/arm
    cp -a --parents arch/arm/include/asm/opcodes.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
%endif
    cp -a include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
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
           --kernel-image $(realpath $KernelImage) \
           --kernel-cmdline 'console=tty0 console=ttyS0' \
	   $KernelUnifiedImage

%if %{signkernel}
	%{log_msg "Sign the EFI UKI kernel"}
	%pesign -s -i $KernelUnifiedImage -o $KernelUnifiedImage.signed -a %{secureboot_ca_0} -c %{secureboot_key_0} -n %{pesign_name_0}

    	if [ ! -s $KernelUnifiedImage.signed ]; then
	   %{log_msg "pesigning failed"}
      	   exit 1
    	fi
    	mv $KernelUnifiedImage.signed $KernelUnifiedImage

# signkernel
%endif


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

        mkdir -p "$RPM_BUILD_ROOT/lib/modules/$KernelVer/$subdirname"

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

        if [ "$module_subdir" == "kernel" ]; then
            # make kmod paths absolute
            sed -e 's|^kernel/|/lib/modules/'$KernelVer'/kernel/|' %{?zipsed} $relative_kmod_list > $absolute_file_list
        else
            # move kmods into subdirs if needed (internal, partner, extra,..)
            move_kmod_list $relative_kmod_list $module_subdir
            # make kmod paths absolute
            sed -e 's|^kernel/|/lib/modules/'$KernelVer'/'$module_subdir'/|' $relative_kmod_list > $absolute_file_list
            # run deny-mod script, this adds blacklist-* files to absolute_file_list
            %{SOURCE20} "$RPM_BUILD_ROOT" lib/modules/$KernelVer $absolute_file_list
%if %{zipmodules}
            # deny-mod script works with kmods as they are now (not compressed),
            # but if they will be we need to add compext to all
            sed -i %{?zipsed} $absolute_file_list
%endif
            # add also dir for the case when there are no kmods
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
        %{SOURCE22} sort -d $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.dep -c configs/def_variants.yaml $variants_param -o ..
        if [ $? -ne 0 ]; then
            echo "8< --- modules.dep ---"
            cat $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.dep
            echo "--- modules.dep --- >8"
            exit 1
        fi

        create_module_file_list "kernel" ../modules-core.list ../kernel${Variant:+-${Variant}}-modules-core.list 1
        create_module_file_list "kernel" ../modules.list ../kernel${Variant:+-${Variant}}-modules.list 0
        create_module_file_list "internal" ../modules-internal.list ../kernel${Variant:+-${Variant}}-modules-internal.list 0
        create_module_file_list "extra" ../modules-extra.list ../kernel${Variant:+-${Variant}}-modules-extra.list 0
        if [[ "$Variant" == "rt" || "$Variant" == "rt-debug" ]]; then
            create_module_file_list "kvm" ../modules-rt-kvm.list ../kernel${Variant:+-${Variant}}-modules-rt-kvm.list 0
        fi
%if 0%{!?fedora:1}
        create_module_file_list "partner" ../modules-partner.list ../kernel${Variant:+-${Variant}}-modules-partner.list 1 0
%endif
    fi # $DoModules -eq 1

    remove_depmod_files()
    {
        # remove files that will be auto generated by depmod at rpm -i time
        pushd $RPM_BUILD_ROOT/lib/modules/$KernelVer/
            # in case below list needs to be extended, remember to add a
            # matching ghost entry in the files section as well
            rm -f modules.{alias,alias.bin,builtin.alias.bin,builtin.bin} \
                  modules.{dep,dep.bin,devname,softdep,symbols,symbols.bin}
        popd
    }

    # Cleanup
    %{log_msg "Cleanup build files"}
    rm -f $RPM_BUILD_ROOT/System.map
    %{log_msg "Remove depmod files"}
    remove_depmod_files

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
        CFLAGS="" LDFLAGS="" make EXTRA_CFLAGS="${BPFBOOTSTRAP_CFLAGS}" EXTRA_LDFLAGS="${BPFBOOTSTRAP_LDFLAGS}" %{?make_opts} %{?clang_make_opts} V=1 -C tools/bpf/bpftool bootstrap

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

%if %{with_bpftool}
%global bpftool_make \
  %{__make} EXTRA_CFLAGS="${RPM_OPT_FLAGS}" EXTRA_LDFLAGS="%{__global_ldflags}" DESTDIR=$RPM_BUILD_ROOT %{?make_opts} VMLINUX_H="${RPM_VMLINUX_H}" V=1
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
%{make} %{?_smp_mflags} ARCH=$Arch V=1 TARGETS="bpf mm net net/forwarding net/mptcp netfilter tc-testing memfd drivers/net/bonding" SKIP_TARGETS="" $force_targets INSTALL_PATH=%{buildroot}%{_libexecdir}/kselftests VMLINUX_H="${RPM_VMLINUX_H}" install

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
%ghost %attr(0600, root, root) /boot/symvers-%{KVERREL}%{?3:+%{3}}.%compext\
%ghost %attr(0600, root, root) /boot/initramfs-%{KVERREL}%{?3:+%{3}}.img\
%ghost %attr(0644, root, root) /boot/config-%{KVERREL}%{?3:+%{3}}\
%{expand:%%files -f kernel-%{?3:%{3}-}modules-core.list %{?3:%{3}-}modules-core}\
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
/lib/modules/%{KVERREL}%{?3:+%{3}}/System.map\
/lib/modules/%{KVERREL}%{?3:+%{3}}/symvers.%compext\
/lib/modules/%{KVERREL}%{?3:+%{3}}/config\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.builtin*\
%attr(0644, root, root) /lib/modules/%{KVERREL}%{?3:+%{3}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-virt.efi\
%ghost /%{image_install_path}/efi/EFI/Linux/%{?-k:%{-k*}}%{!?-k:*}-%{KVERREL}%{?3:+%{3}}.efi\
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
* Tue May 07 2024 Jan Stancek <jstancek@redhat.com> [6.9.0-0.rc7.5.el10]
- Linux 6.9-rc7 (Linus Torvalds)
- epoll: be better about file lifetimes (Linus Torvalds)
- EDAC/versal: Do not log total error counts (Shubhrajyoti Datta)
- EDAC/versal: Check user-supplied data before injecting an error (Shubhrajyoti Datta)
- EDAC/versal: Do not register for NOC errors (Shubhrajyoti Datta)
- powerpc/pseries/iommu: LPAR panics during boot up with a frozen PE (Gaurav Batra)
- powerpc/pseries: make max polling consistent for longer H_CALLs (Nayna Jain)
- x86/mm: Remove broken vsyscall emulation code from the page fault code (Linus Torvalds)
- x86/apic: Don't access the APIC when disabling x2APIC (Thomas Gleixner)
- x86/sev: Add callback to apply RMP table fixups for kexec (Ashish Kalra)
- x86/e820: Add a new e820 table update helper (Ashish Kalra)
- softirq: Fix suspicious RCU usage in __do_softirq() (Zqiang)
- slimbus: qcom-ngd-ctrl: Add timeout for wait operation (Viken Dadhaniya)
- dyndbg: fix old BUG_ON in >control parser (Jim Cromie)
- fpga: dfl-pci: add PCI subdevice ID for Intel D5005 card (Peter Colberg)
- misc/pvpanic-pci: register attributes via pci_driver (Thomas Weißschuh)
- mei: me: add lunar lake point M DID (Alexander Usyskin)
- mei: pxp: match against PCI_CLASS_DISPLAY_OTHER (Daniele Ceraolo Spurio)
- iio:imu: adis16475: Fix sync mode setting (Ramona Gradinariu)
- iio: accel: mxc4005: Reset chip on probe() and resume() (Hans de Goede)
- iio: accel: mxc4005: Interrupt handling fixes (Hans de Goede)
- dt-bindings: iio: health: maxim,max30102: fix compatible check (Javier Carrasco)
- iio: pressure: Fixes SPI support for BMP3xx devices (Vasileios Amoiridis)
- iio: pressure: Fixes BME280 SPI driver data (Vasileios Amoiridis)
- usb: typec: tcpm: Check for port partner validity before consuming it (Badhri Jagan Sridharan)
- usb: typec: tcpm: enforce ready state when queueing alt mode vdm (RD Babiera)
- usb: typec: tcpm: unregister existing source caps before re-registration (Amit Sunil Dhamne)
- usb: typec: tcpm: clear pd_event queue in PORT_RESET (RD Babiera)
- usb: typec: tcpm: queue correct sop type in tcpm_queue_vdm_unlocked (RD Babiera)
- usb: Fix regression caused by invalid ep0 maxpacket in virtual SuperSpeed device (Alan Stern)
- usb: ohci: Prevent missed ohci interrupts (Guenter Roeck)
- usb: typec: qcom-pmic: fix pdphy start() error handling (Johan Hovold)
- usb: typec: qcom-pmic: fix use-after-free on late probe errors (Johan Hovold)
- usb: gadget: f_fs: Fix a race condition when processing setup packets. (Chris Wulff)
- USB: core: Fix access violation during port device removal (Alan Stern)
- usb: dwc3: core: Prevent phy suspend during init (Thinh Nguyen)
- usb: xhci-plat: Don't include xhci.h (Thinh Nguyen)
- usb: gadget: uvc: use correct buffer size when parsing configfs lists (Ivan Avdeev)
- usb: gadget: composite: fix OS descriptors w_value logic (Peter Korsgaard)
- usb: gadget: f_fs: Fix race between aio_cancel() and AIO request complete (Wesley Cheng)
- Input: amimouse - mark driver struct with __refdata to prevent section mismatch (Uwe Kleine-König)
- Input: xpad - add support for ASUS ROG RAIKIRI (Vicki Pfau)
- tracing/probes: Fix memory leak in traceprobe_parse_probe_arg_body() (LuMingYin)
- eventfs: Have "events" directory get permissions from its parent (Steven Rostedt (Google))
- eventfs: Do not treat events directory different than other directories (Steven Rostedt (Google))
- eventfs: Do not differentiate the toplevel events directory (Steven Rostedt (Google))
- tracefs: Still use mount point as default permissions for instances (Steven Rostedt (Google))
- tracefs: Reset permissions on remount if permissions are options (Steven Rostedt (Google))
- eventfs: Free all of the eventfs_inode after RCU (Steven Rostedt (Google))
- eventfs/tracing: Add callback for release of an eventfs_inode (Steven Rostedt (Google))
- swiotlb: initialise restricted pool list_head when SWIOTLB_DYNAMIC=y (Will Deacon)
- clk: samsung: Revert "clk: Use device_get_match_data()" (Marek Szyprowski)
- clk: sunxi-ng: a64: Set minimum and maximum rate for PLL-MIPI (Frank Oltmanns)
- clk: sunxi-ng: common: Support minimum and maximum rate (Frank Oltmanns)
- clk: sunxi-ng: h6: Reparent CPUX during PLL CPUX rate change (Jernej Skrabec)
- clk: qcom: smd-rpm: Restore msm8976 num_clk (Adam Skladowski)
- clk: qcom: gdsc: treat optional supplies as optional (Johan Hovold)
- v6.9-rc6-rt4 (Sebastian Andrzej Siewior)
- printk: Update the printk queue. (Sebastian Andrzej Siewior)
- cxl: Fix cxl_endpoint_get_perf_coordinate() support for RCH (Dave Jiang)
- x86/xen: return a sane initial apic id when running as PV guest (Juergen Gross)
- x86/xen/smp_pv: Register the boot CPU APIC properly (Thomas Gleixner)
- efi/unaccepted: touch soft lockup during memory accept (Chen Yu)
- nvme-tcp: strict pdu pacing to avoid send stalls on TLS (Hannes Reinecke)
- nvmet: fix nvme status code when namespace is disabled (Sagi Grimberg)
- nvmet-tcp: fix possible memory leak when tearing down a controller (Sagi Grimberg)
- nvme: cancel pending I/O if nvme controller is in terminal state (Nilay Shroff)
- nvmet-auth: replace pr_debug() with pr_err() to report an error. (Maurizio Lombardi)
- nvmet-auth: return the error code to the nvmet_auth_host_hash() callers (Maurizio Lombardi)
- nvme: find numa distance only if controller has valid numa id (Nilay Shroff)
- nvme: fix warn output about shared namespaces without CONFIG_NVME_MULTIPATH (Yi Zhang)
- ublk: remove segment count and size limits (Uday Shankar)
- ALSA: hda/realtek: Fix build error without CONFIG_PM (Takashi Iwai)
- ASoC: meson: axg-tdm: add continuous clock support (Jerome Brunet)
- ASoC: meson: axg-tdm-interface: manage formatters in trigger (Jerome Brunet)
- ASoC: meson: axg-card: make links nonatomic (Jerome Brunet)
- ASoC: meson: axg-fifo: use threaded irq to check periods (Jerome Brunet)
- ASoC: cs35l56: fix usages of device_get_named_child_node() (Pierre-Louis Bossart)
- ASoC: da7219-aad: fix usage of device_get_named_child_node() (Pierre-Louis Bossart)
- ASoC: meson: cards: select SND_DYNAMIC_MINORS (Jerome Brunet)
- ASoC: rt715-sdca: volume step modification (Jack Yu)
- ASoC: cs35l56: Avoid static analysis warning of uninitialised variable (Simon Trimmer)
- ASoC: codecs: wsa881x: set clk_stop_mode1 flag (Srinivas Kandagatla)
- ASoC: ti: davinci-mcasp: Fix race condition during probe (Joao Paulo Goncalves)
- ASoC: Intel: avs: Set name of control as in topology (Amadeusz Sławiński)
- ASoC: SOF: Core: Handle error returned by sof_select_ipc_and_paths (Peter Ujfalusi)
- ASoC: rt715: add vendor clear control register (Jack Yu)
- ASoC: cs35l41: Update DSP1RX5/6 Sources for DSP config (Stefan Binding)
- ASoC: cs35l56: Prevent overwriting firmware ASP config (Richard Fitzgerald)
- ASoC: cs35l56: Fix unintended bus access while resetting amp (Richard Fitzgerald)
- ALSA: hda: cs35l56: Exit cache-only after cs35l56_wait_for_firmware_boot() (Richard Fitzgerald)
- regmap: Add regmap_read_bypassed() (Richard Fitzgerald)
- ASoC: SOF: ipc4-pcm: Do not reset the ChainDMA if it has not been allocated (Peter Ujfalusi)
- ASoC: SOF: ipc4-pcm: Introduce generic sof_ipc4_pcm_stream_priv (Peter Ujfalusi)
- ASoC: SOF: ipc4-pcm: Use consistent name for sof_ipc4_timestamp_info pointer (Peter Ujfalusi)
- ASoC: SOF: ipc4-pcm: Use consistent name for snd_sof_pcm_stream pointer (Peter Ujfalusi)
- ASoC: SOF: debug: show firmware/topology prefix/names (Pierre-Louis Bossart)
- ASoC: SOF: pcm: Restrict DSP D0i3 during S0ix to IPC3 (Ranjani Sridharan)
- ASoC: SOF: Intel: add default firmware library path for LNL (Pierre-Louis Bossart)
- ASoC: rt722-sdca: add headset microphone vrefo setting (Jack Yu)
- ASoC: rt722-sdca: modify channel number to support 4 channels (Jack Yu)
- ASoC: dt-bindings: rt5645: add cbj sleeve gpio property (Derek Fang)
- ASoC: rt5645: Fix the electric noise due to the CBJ contacts floating (Derek Fang)
- ASoC: acp: Support microphone from device Acer 315-24p (end.to.start)
- ASoC: Intel: bytcr_rt5640: Apply Asus T100TA quirk to Asus T100TAM too (Hans de Goede)
- ASoC: tegra: Fix DSPK 16-bit playback (Sameer Pujar)
- ASoC: Intel: avs: Fix debug window description (Cezary Rojewski)
- ALSA: hda/realtek: Fix conflicting PCI SSID 17aa:386f for Lenovo Legion models (Takashi Iwai)
- ALSA: hda/realtek - Set GPIO3 to default at S4 state for Thinkpad with ALC1318 (Kailang Yang)
- ALSA: hda: intel-sdw-acpi: fix usage of device_get_named_child_node() (Pierre-Louis Bossart)
- ALSA: hda: intel-dsp-config: harden I2C/I2S codec detection (Pierre-Louis Bossart)
- ALSA: hda/realtek: Fix mute led of HP Laptop 15-da3001TU (Aman Dhoot)
- ALSA: emu10k1: make E-MU FPGA writes potentially more reliable (Oswald Buddenhagen)
- ALSA: emu10k1: fix E-MU dock initialization (Oswald Buddenhagen)
- ALSA: emu10k1: use mutex for E-MU FPGA access locking (Oswald Buddenhagen)
- ALSA: emu10k1: move the whole GPIO event handling to the workqueue (Oswald Buddenhagen)
- ALSA: emu10k1: factor out snd_emu1010_load_dock_firmware() (Oswald Buddenhagen)
- ALSA: emu10k1: fix E-MU card dock presence monitoring (Oswald Buddenhagen)
- drm/panel: ili9341: Use predefined error codes (Andy Shevchenko)
- drm/panel: ili9341: Respect deferred probe (Andy Shevchenko)
- drm/panel: ili9341: Correct use of device property APIs (Andy Shevchenko)
- drm/vmwgfx: Fix invalid reads in fence signaled events (Zack Rusin)
- drm/nouveau/gsp: Use the sg allocator for level 2 of radix3 (Lyude Paul)
- drm/nouveau/firmware: Fix SG_DEBUG error with nvkm_firmware_ctor() (Lyude Paul)
- drm/imagination: Ensure PVR_MIPS_PT_PAGE_COUNT is never zero (Matt Coster)
- drm/ttm: Print the memory decryption status just once (Zack Rusin)
- drm/vmwgfx: Fix Legacy Display Unit (Ian Forbes)
- drm/xe/display: Fix ADL-N detection (Lucas De Marchi)
- drm/xe/vm: prevent UAF in rebind_work_func() (Matthew Auld)
- drm/amd/display: Disable panel replay by default for now (Mario Limonciello)
- drm/amdgpu: fix doorbell regression (Shashank Sharma)
- drm/amdkfd: Flush the process wq before creating a kfd_process (Lancelot SIX)
- drm/amd/display: Disable seamless boot on 128b/132b encoding (Sung Joon Kim)
- drm/amd/display: Fix DC mode screen flickering on DCN321 (Leo Ma)
- drm/amd/display: Add VCO speed parameter for DCN31 FPU (Rodrigo Siqueira)
- drm/amdgpu: once more fix the call oder in amdgpu_ttm_move() v2 (Christian König)
- drm/amd/display: Allocate zero bw after bw alloc enable (Meenakshikumar Somasundaram)
- drm/amd/display: Fix incorrect DSC instance for MST (Hersen Wu)
- drm/amd/display: Atom Integrated System Info v2_2 for DCN35 (Gabe Teeger)
- drm/amd/display: Add dtbclk access to dcn315 (Swapnil Patel)
- drm/amd/display: Ensure that dmcub support flag is set for DCN20 (Rodrigo Siqueira)
- drm/amd/display: Handle Y carry-over in VCP X.Y calculation (George Shen)
- drm/amdgpu: Fix VRAM memory accounting (Mukul Joshi)
- spi: fix null pointer dereference within spi_sync (Mans Rullgard)
- spi: hisi-kunpeng: Delete the dump interface of data registers in debugfs (Devyn Liu)
- spi: axi-spi-engine: fix version format string (David Lechner)
- Set DEBUG_INFO_BTF_MODULES for Fedora (Justin M. Forbes)
- btrfs: set correct ram_bytes when splitting ordered extent (Qu Wenruo)
- btrfs: take the cleaner_mutex earlier in qgroup disable (Josef Bacik)
- btrfs: add missing mutex_unlock in btrfs_relocate_sys_chunks() (Dominique Martinet)
- s390/paes: Reestablish retry loop in paes (Harald Freudenberger)
- s390/zcrypt: Use EBUSY to indicate temp unavailability (Harald Freudenberger)
- s390/zcrypt: Handle ep11 cprb return code (Harald Freudenberger)
- s390/zcrypt: Fix wrong format string in debug feature printout (Harald Freudenberger)
- s390/cio: Ensure the copied buf is NUL terminated (Bui Quang Minh)
- s390/vdso: Add CFI for RA register to asm macro vdso_func (Jens Remus)
- s390/3270: Fix buffer assignment (Sven Schnelle)
- s390/mm: Fix clearing storage keys for huge pages (Claudio Imbrenda)
- s390/mm: Fix storage key clearing for guest huge pages (Claudio Imbrenda)
- xtensa: remove redundant flush_dcache_page and ARCH_IMPLEMENTS_FLUSH_DCACHE_PAGE macros (Barry Song)
- tty: xtensa/iss: Use min() to fix Coccinelle warning (Thorsten Blum)
- xtensa: fix MAKE_PC_FROM_RA second argument (Max Filippov)
- firewire: ohci: fulfill timestamp for some local asynchronous transaction (Takashi Sakamoto)
- firewire: nosy: ensure user_length is taken into account when fetching packet contents (Thanassis Avgerinos)
- thermal/debugfs: Prevent use-after-free from occurring after cdev removal (Rafael J. Wysocki)
- thermal/debugfs: Fix two locking issues with thermal zone debug (Rafael J. Wysocki)
- thermal/debugfs: Free all thermal zone debug memory on zone removal (Rafael J. Wysocki)
- MAINTAINERS: mark MYRICOM MYRI-10G as Orphan (Jakub Kicinski)
- MAINTAINERS: remove Ariel Elior (Jakub Kicinski)
- net: gro: add flush check in udp_gro_receive_segment (Richard Gobert)
- net: gro: fix udp bad offset in socket lookup by adding {inner_}network_offset to napi_gro_cb (Richard Gobert)
- ipv4: Fix uninit-value access in __ip_make_skb() (Shigeru Yoshida)
- s390/qeth: Fix kernel panic after setting hsuid (Alexandra Winter)
- vxlan: Pull inner IP header in vxlan_rcv(). (Guillaume Nault)
- tipc: fix a possible memleak in tipc_buf_append (Xin Long)
- tipc: fix UAF in error path (Paolo Abeni)
- rxrpc: Clients must accept conn from any address (Jeffrey Altman)
- net: core: reject skb_copy(_expand) for fraglist GSO skbs (Felix Fietkau)
- net: bridge: fix multicast-to-unicast with fraglist GSO (Felix Fietkau)
- mptcp: ensure snd_nxt is properly initialized on connect (Paolo Abeni)
- e1000e: change usleep_range to udelay in PHY mdic access (Vitaly Lifshits)
- net: dsa: mv88e6xxx: Fix number of databases for 88E6141 / 88E6341 (Marek Behún)
- cxgb4: Properly lock TX queue for the selftest. (Sebastian Andrzej Siewior)
- rxrpc: Fix using alignmask being zero for __page_frag_alloc_align() (Yunsheng Lin)
- vxlan: Add missing VNI filter counter update in arp_reduce(). (Guillaume Nault)
- vxlan: Fix racy device stats updates. (Guillaume Nault)
- net: qede: use return from qede_parse_actions() (Asbjørn Sloth Tønnesen)
- net: qede: use return from qede_parse_flow_attr() for flow_spec (Asbjørn Sloth Tønnesen)
- net: qede: use return from qede_parse_flow_attr() for flower (Asbjørn Sloth Tønnesen)
- net: qede: sanitize 'rc' in qede_add_tc_flower_fltr() (Asbjørn Sloth Tønnesen)
- MAINTAINERS: add an explicit entry for YNL (Jakub Kicinski)
- net: bcmgenet: synchronize UMAC_CMD access (Doug Berger)
- net: bcmgenet: synchronize use of bcmgenet_set_rx_mode() (Doug Berger)
- net: bcmgenet: synchronize EXT_RGMII_OOB_CTRL access (Doug Berger)
- selftests/bpf: Test PROBE_MEM of VSYSCALL_ADDR on x86-64 (Puranjay Mohan)
- bpf, x86: Fix PROBE_MEM runtime load check (Puranjay Mohan)
- bpf: verifier: prevent userspace memory access (Puranjay Mohan)
- xdp: use flags field to disambiguate broadcast redirect (Toke Høiland-Jørgensen)
- arm32, bpf: Reimplement sign-extension mov instruction (Puranjay Mohan)
- riscv, bpf: Fix incorrect runtime stats (Xu Kuohai)
- bpf, arm64: Fix incorrect runtime stats (Xu Kuohai)
- bpf: Fix a verifier verbose message (Anton Protopopov)
- bpf, skmsg: Fix NULL pointer dereference in sk_psock_skb_ingress_enqueue (Jason Xing)
- MAINTAINERS: bpf: Add Lehui and Puranjay as riscv64 reviewers (Björn Töpel)
- MAINTAINERS: Update email address for Puranjay Mohan (Puranjay Mohan)
- bpf, kconfig: Fix DEBUG_INFO_BTF_MODULES Kconfig definition (Andrii Nakryiko)
- Fix a potential infinite loop in extract_user_to_sg() (David Howells)
- net l2tp: drop flow hash on forward (David Bauer)
- nsh: Restore skb->{protocol,data,mac_header} for outer header in nsh_gso_segment(). (Kuniyuki Iwashima)
- octeontx2-af: avoid off-by-one read from userspace (Bui Quang Minh)
- bna: ensure the copied buf is NUL terminated (Bui Quang Minh)
- ice: ensure the copied buf is NUL terminated (Bui Quang Minh)
- redhat: Use redhatsecureboot701 for ppc64le (Jan Stancek)
- redhat: switch the kernel package to use certs from system-sb-certs (Jan Stancek)
- redhat: replace redhatsecureboot303 signing key with redhatsecureboot601 (Jan Stancek)
- redhat: drop certificates that were deprecated after GRUB's BootHole flaw (Jan Stancek)
- redhat: correct file name of redhatsecurebootca1 (Jan Stancek)
- redhat: align file names with names of signing keys for ppc and s390 (Jan Stancek)
- regulator: change devm_regulator_get_enable_optional() stub to return Ok (Matti Vaittinen)
- regulator: change stubbed devm_regulator_get_enable to return Ok (Matti Vaittinen)
- regulator: vqmmc-ipq4019: fix module autoloading (Krzysztof Kozlowski)
- regulator: qcom-refgen: fix module autoloading (Krzysztof Kozlowski)
- regulator: mt6360: De-capitalize devicetree regulator subnodes (AngeloGioacchino Del Regno)
- regulator: irq_helpers: duplicate IRQ name (Matti Vaittinen)
- KVM: selftests: Add test for uaccesses to non-existent vgic-v2 CPUIF (Oliver Upton)
- KVM: arm64: vgic-v2: Check for non-NULL vCPU in vgic_v2_parse_attr() (Oliver Upton)
- power: supply: mt6360_charger: Fix of_match for usb-otg-vbus regulator (AngeloGioacchino Del Regno)
- power: rt9455: hide unused rt9455_boost_voltage_values (Arnd Bergmann)
- platform/x86: ISST: Add Grand Ridge to HPM CPU list (Srinivas Pandruvada)
- pinctrl: baytrail: Add pinconf group for uart3 (Hans de Goede)
- pinctrl: baytrail: Fix selecting gpio pinctrl state (Hans de Goede)
- pinctrl: renesas: rzg2l: Configure the interrupt type on resume (Claudiu Beznea)
- pinctrl: renesas: rzg2l: Execute atomically the interrupt configuration (Claudiu Beznea)
- dt-bindings: pinctrl: renesas,rzg2l-pinctrl: Allow 'input' and 'output-enable' properties (Lad Prabhakar)
- pinctrl: devicetree: fix refcount leak in pinctrl_dt_to_map() (Zeng Heng)
- pinctrl: mediatek: paris: Rework support for PIN_CONFIG_{INPUT,OUTPUT}_ENABLE (Chen-Yu Tsai)
- pinctrl: mediatek: paris: Fix PIN_CONFIG_INPUT_SCHMITT_ENABLE readback (Chen-Yu Tsai)
- pinctrl: core: delete incorrect free in pinctrl_enable() (Dan Carpenter)
- pinctrl/meson: fix typo in PDM's pin name (Jan Dakinevich)
- pinctrl: pinctrl-aspeed-g6: Fix register offset for pinconf of GPIOR-T (Billy Tsai)
- redhat/configs: Enable CONFIG_DM_VDO in RHEL (Benjamin Marzinski)
- redhat/configs: Enable DRM_NOUVEAU_GSP_DEFAULT everywhere (Neal Gompa)
- v6.9-rc6-rt3 (Sebastian Andrzej Siewior)
- cxgb4: Properly lock TX queue for the selftest. (Sebastian Andrzej Siewior)
- i915: Disable tracepoints (again). (Sebastian Andrzej Siewior)
- v6.9-rc6-rt2 (Sebastian Andrzej Siewior)
- workqueue: Fix divide error in wq_update_node_max_active() (Lai Jiangshan)
- workqueue: The default node_nr_active should have its max set to max_active (Tejun Heo)
- workqueue: Fix selection of wake_cpu in kick_pool() (Sven Schnelle)
- docs/zh_CN: core-api: Update translation of workqueue.rst to 6.9-rc1 (Xingyou Chen)
- Documentation/core-api: Update events_freezable_power references. (Audra Mitchell)
- scsi: sd: Only print updates to permanent stream count (John Garry)
- NFSD: Fix nfsd4_encode_fattr4() crasher (Chuck Lever)
- nfs: Handle error of rpc_proc_register() in nfs_net_init(). (Kuniyuki Iwashima)
- SUNRPC: add a missing rpc_stat for TCP TLS (Olga Kornievskaia)
- bcachefs: fix integer conversion bug (Kent Overstreet)
- bcachefs: btree node scan now fills in sectors_written (Kent Overstreet)
- bcachefs: Remove accidental debug assert (Kent Overstreet)
- erofs: reliably distinguish block based and fscache mode (Christian Brauner)
- erofs: get rid of erofs_fs_context (Baokun Li)
- erofs: modify the error message when prepare_ondemand_read failed (Hongbo Li)
- bounds: Use the right number of bits for power-of-two CONFIG_NR_CPUS (Matthew Wilcox (Oracle))
- kernel.spec: adjust for livepatching kselftests (Joe Lawrence)
- redhat/configs: remove CONFIG_TEST_LIVEPATCH (Joe Lawrence)
- Turn on CONFIG_RANDOM_KMALLOC_CACHES for Fedora (Justin M. Forbes)
- Set Fedora configs for 6.9 (Justin M. Forbes)

* Tue Apr 30 2024 Jan Stancek <jstancek@redhat.com> [6.9.0-0.rc6.4.el10]
- Linux 6.9-rc6 (Linus Torvalds)
- sched/isolation: Fix boot crash when maxcpus < first housekeeping CPU (Oleg Nesterov)
- sched/isolation: Prevent boot crash when the boot CPU is nohz_full (Oleg Nesterov)
- sched/eevdf: Prevent vlag from going out of bounds in reweight_eevdf() (Xuewen Yan)
- sched/eevdf: Fix miscalculation in reweight_entity() when se is not curr (Tianchen Ding)
- sched/eevdf: Always update V if se->on_rq when reweighting (Tianchen Ding)
- cpu: Ignore "mitigations" kernel parameter if CPU_MITIGATIONS=n (Sean Christopherson)
- cpu: Re-enable CPU mitigations by default for !X86 architectures (Sean Christopherson)
- x86/tdx: Preserve shared bit on mprotect() (Kirill A. Shutemov)
- x86/cpu: Fix check for RDPKRU in __show_regs() (David Kaplan)
- x86/CPU/AMD: Add models 0x10-0x1f to the Zen5 range (Wenkuan Wang)
- x86/sev: Check for MWAITX and MONITORX opcodes in the #VC handler (Tom Lendacky)
- irqchip/gic-v3-its: Prevent double free on error (Guanrui Huang)
- gitlab-ci: enable pipelines with c10s buildroot (Michael Hofmann)
- rust: remove `params` from `module` macro example (Aswin Unnikrishnan)
- kbuild: rust: force `alloc` extern to allow "empty" Rust files (Miguel Ojeda)
- kbuild: rust: remove unneeded `@rustc_cfg` to avoid ICE (Miguel Ojeda)
- rust: kernel: require `Send` for `Module` implementations (Wedson Almeida Filho)
- rust: phy: implement `Send` for `Registration` (Wedson Almeida Filho)
- rust: make mutually exclusive with CFI_CLANG (Conor Dooley)
- rust: macros: fix soundness issue in `module!` macro (Benno Lossin)
- rust: init: remove impl Zeroable for Infallible (Laine Taffin Altman)
- docs: rust: fix improper rendering in Arch Support page (Bo-Wei Chen)
- rust: don't select CONSTRUCTORS (Alice Ryhl)
- riscv: T-Head: Test availability bit before enabling MAE errata (Christoph Müllner)
- riscv: thead: Rename T-Head PBMT to MAE (Christoph Müllner)
- RISC-V: selftests: cbo: Ensure asm operands match constraints, take 2 (Andrew Jones)
- perf riscv: Fix the warning due to the incompatible type (Ben Zong-You Xie)
- selftests: sud_test: return correct emulated syscall value on RISC-V (Clément Léger)
- riscv: hwprobe: fix invalid sign extension for RISCV_HWPROBE_EXT_ZVFHMIN (Clément Léger)
- riscv: Fix loading 64-bit NOMMU kernels past the start of RAM (Samuel Holland)
- riscv: Fix TASK_SIZE on 64-bit NOMMU (Samuel Holland)
- smb3: fix lock ordering potential deadlock in cifs_sync_mid_result (Steve French)
- smb3: missing lock when picking channel (Steve French)
- smb: client: Fix struct_group() usage in __packed structs (Gustavo A. R. Silva)
- i2c: smbus: fix NULL function pointer dereference (Wolfram Sang)
- MAINTAINERS: Drop entry for PCA9541 bus master selector (Guenter Roeck)
- eeprom: at24: fix memory corruption race condition (Daniel Okazaki)
- dt-bindings: eeprom: at24: Fix ST M24C64-D compatible schema (Rob Herring)
- profiling: Remove create_prof_cpu_mask(). (Tetsuo Handa)
- soundwire: amd: fix for wake interrupt handling for clockstop mode (Vijendar Mukunda)
- dmaengine: idxd: Fix oops during rmmod on single-CPU platforms (Fenghua Yu)
- dmaengine: xilinx: xdma: Clarify kdoc in XDMA driver (Miquel Raynal)
- dmaengine: xilinx: xdma: Fix synchronization issue (Louis Chauvet)
- dmaengine: xilinx: xdma: Fix wrong offsets in the buffers addresses in dma descriptor (Miquel Raynal)
- dma: xilinx_dpdma: Fix locking (Sean Anderson)
- dmaengine: idxd: Convert spinlock to mutex to lock evl workqueue (Rex Zhang)
- idma64: Don't try to serve interrupts when device is powered off (Andy Shevchenko)
- dmaengine: tegra186: Fix residual calculation (Akhil R)
- dmaengine: owl: fix register access functions (Arnd Bergmann)
- dmaengine: Revert "dmaengine: pl330: issue_pending waits until WFP state" (Vinod Koul)
- phy: ti: tusb1210: Resolve charger-det crash if charger psy is unregistered (Hans de Goede)
- phy: qcom: qmp-combo: fix VCO div offset on v5_5nm and v6 (Johan Hovold)
- phy: phy-rockchip-samsung-hdptx: Select CONFIG_RATIONAL (Cristian Ciocaltea)
- phy: qcom: m31: match requested regulator name with dt schema (Gabor Juhos)
- phy: qcom: qmp-combo: Fix register base for QSERDES_DP_PHY_MODE (Stephen Boyd)
- phy: qcom: qmp-combo: Fix VCO div offset on v3 (Stephen Boyd)
- phy: rockchip: naneng-combphy: Fix mux on rk3588 (Sebastian Reichel)
- phy: rockchip-snps-pcie3: fix clearing PHP_GRF_PCIESEL_CON bits (Sebastian Reichel)
- phy: rockchip-snps-pcie3: fix bifurcation on rk3588 (Michal Tomek)
- phy: freescale: imx8m-pcie: fix pcie link-up instability (Marcel Ziswiler)
- phy: marvell: a3700-comphy: Fix hardcoded array size (Mikhail Kobuk)
- phy: marvell: a3700-comphy: Fix out of bounds read (Mikhail Kobuk)
- soc: mediatek: mtk-socinfo: depends on CONFIG_SOC_BUS (Daniel Golle)
- soc: mediatek: mtk-svs: Append "-thermal" to thermal zone names (AngeloGioacchino Del Regno)
- firmware: qcom: uefisecapp: Fix memory related IO errors and crashes (Maximilian Luz)
- ARM: dts: imx6ull-tarragon: fix USB over-current polarity (Michael Heimpold)
- arm64: dts: imx8mp: Fix assigned-clocks for second CSI2 (Marek Vasut)
- arm64: dts: mediatek: mt2712: fix validation errors (Rafał Miłecki)
- arm64: dts: mediatek: mt7986: prefix BPI-R3 cooling maps with "map-" (Rafał Miłecki)
- arm64: dts: mediatek: mt7986: drop invalid thermal block clock (Rafał Miłecki)
- arm64: dts: mediatek: mt7986: drop "#reset-cells" from Ethernet controller (Rafał Miłecki)
- arm64: dts: mediatek: mt7986: drop invalid properties from ethsys (Rafał Miłecki)
- arm64: dts: mediatek: mt7622: drop "reset-names" from thermal block (Rafał Miłecki)
- arm64: dts: mediatek: mt7622: fix ethernet controller "compatible" (Rafał Miłecki)
- arm64: dts: mediatek: mt7622: fix IR nodename (Rafał Miłecki)
- arm64: dts: mediatek: mt7622: fix clock controllers (Rafał Miłecki)
- arm64: dts: mediatek: mt8186-corsola: Update min voltage constraint for Vgpu (Pin-yen Lin)
- arm64: dts: mediatek: mt8183-kukui: Use default min voltage for MT6358 (Pin-yen Lin)
- arm64: dts: mediatek: mt8195-cherry: Update min voltage constraint for MT6315 (Pin-yen Lin)
- arm64: dts: mediatek: mt8192-asurada: Update min voltage constraint for MT6315 (Pin-yen Lin)
- arm64: dts: mediatek: cherry: Describe CPU supplies (Nícolas F. R. A. Prado)
- arm64: dts: mediatek: mt8195: Add missing gce-client-reg to mutex1 (Nícolas F. R. A. Prado)
- arm64: dts: mediatek: mt8195: Add missing gce-client-reg to mutex (Nícolas F. R. A. Prado)
- arm64: dts: mediatek: mt8195: Add missing gce-client-reg to vpp/vdosys (Nícolas F. R. A. Prado)
- arm64: dts: mediatek: mt8192: Add missing gce-client-reg to mutex (Nícolas F. R. A. Prado)
- arm64: dts: mediatek: mt8183: Add power-domains properity to mfgcfg (Ikjoon Jang)
- ARM: dts: microchip: at91-sama7g54_curiosity: Replace regulator-suspend-voltage with the valid property (Andrei Simion)
- ARM: dts: microchip: at91-sama7g5ek: Replace regulator-suspend-voltage with the valid property (Andrei Simion)
- arm64: dts: qcom: sc8180x: Fix ss_phy_irq for secondary USB controller (Maximilian Luz)
- arm64: dts: qcom: sm8650: Fix the msi-map entries (Manivannan Sadhasivam)
- arm64: dts: qcom: sm8550: Fix the msi-map entries (Manivannan Sadhasivam)
- arm64: dts: qcom: sm8450: Fix the msi-map entries (Manivannan Sadhasivam)
- arm64: dts: qcom: sc8280xp: add missing PCIe minimum OPP (Johan Hovold)
- arm64: dts: qcom: x1e80100: Fix the compatible for cluster idle states (Rajendra Nayak)
- arm64: dts: qcom: Fix type of "wdog" IRQs for remoteprocs (Luca Weiss)
- arm64: dts: rockchip: Fix USB interface compatible string on kobol-helios64 (Rob Herring)
- arm64: dts: rockchip: regulator for sd needs to be always on for BPI-R2Pro (Jose Ignacio Tornos Martinez)
- dt-bindings: rockchip: grf: Add missing type to 'pcie-phy' node (Rob Herring)
- arm64: dts: rockchip: drop redundant disable-gpios in Lubancat 2 (Krzysztof Kozlowski)
- arm64: dts: rockchip: drop redundant disable-gpios in Lubancat 1 (Krzysztof Kozlowski)
- arm64: dts: rockchip: drop redundant pcie-reset-suspend in Scarlet Dumo (Krzysztof Kozlowski)
- arm64: dts: rockchip: mark system power controller and fix typo on orangepi-5-plus (Muhammed Efe Cetin)
- arm64: dts: rockchip: Designate the system power controller on QuartzPro64 (Dragan Simic)
- arm64: dts: rockchip: drop panel port unit address in GRU Scarlet (Krzysztof Kozlowski)
- arm64: dts: rockchip: Remove unsupported node from the Pinebook Pro dts (Dragan Simic)
- arm64: dts: rockchip: Fix the i2c address of es8316 on Cool Pi CM5 (Andy Yan)
- arm64: dts: rockchip: add regulators for PCIe on RK3399 Puma Haikou (Quentin Schulz)
- arm64: dts: rockchip: enable internal pull-up on PCIE_WAKE# for RK3399 Puma (Quentin Schulz)
- arm64: dts: rockchip: enable internal pull-up on Q7_USB_ID for RK3399 Puma (Quentin Schulz)
- arm64: dts: rockchip: fix alphabetical ordering RK3399 puma (Iskander Amara)
- arm64: dts: rockchip: enable internal pull-up for Q7_THRM# on RK3399 Puma (Iskander Amara)
- arm64: dts: rockchip: set PHY address of MT7531 switch to 0x1f (Arınç ÜNAL)
- mm/hugetlb: fix DEBUG_LOCKS_WARN_ON(1) when dissolve_free_hugetlb_folio() (Miaohe Lin)
- selftests: mm: protection_keys: save/restore nr_hugepages value from launch script (Muhammad Usama Anjum)
- stackdepot: respect __GFP_NOLOCKDEP allocation flag (Andrey Ryabinin)
- hugetlb: check for anon_vma prior to folio allocation (Vishal Moola (Oracle))
- mm: zswap: fix shrinker NULL crash with cgroup_disable=memory (Johannes Weiner)
- mm: turn folio_test_hugetlb into a PageType (Matthew Wilcox (Oracle))
- mm: support page_mapcount() on page_has_type() pages (Matthew Wilcox (Oracle))
- mm: create FOLIO_FLAG_FALSE and FOLIO_TYPE_OPS macros (Matthew Wilcox (Oracle))
- mm/hugetlb: fix missing hugetlb_lock for resv uncharge (Peter Xu)
- selftests: mm: fix unused and uninitialized variable warning (Muhammad Usama Anjum)
- selftests/harness: remove use of LINE_MAX (Edward Liaw)
- mmc: moxart: fix handling of sgm->consumed, otherwise WARN_ON triggers (Sergei Antonov)
- mmc: sdhci-of-dwcmshc: th1520: Increase tuning loop count to 128 (Maksim Kiselev)
- mmc: sdhci-msm: pervent access to suspended controller (Mantas Pucka)
- ARC: [plat-hsdk]: Remove misplaced interrupt-cells property (Alexey Brodkin)
- ARC: Fix typos (Bjorn Helgaas)
- ARC: mm: fix new code about cache aliasing (Vineet Gupta)
- ARC: Fix -Wmissing-prototypes warnings (Vineet Gupta)
- mtd: limit OTP NVMEM cell parse to non-NAND devices (Christian Marangi)
- mtd: diskonchip: work around ubsan link failure (Arnd Bergmann)
- mtd: rawnand: qcom: Fix broken OP_RESET_DEVICE command in qcom_misc_cmd_type_exec() (Christian Marangi)
- mtd: rawnand: brcmnand: Fix data access violation for STB chip (William Zhang)
- gpio: tangier: Use correct type for the IRQ chip data (Andy Shevchenko)
- gpio: tegra186: Fix tegra186_gpio_is_accessible() check (Prathamesh Shete)
- cxl/core: Fix potential payload size confusion in cxl_mem_get_poison() (Dan Williams)
- dm: restore synchronous close of device mapper block device (Ming Lei)
- dm vdo murmurhash: remove unneeded semicolon (Matthew Sakai)
- netfs: Fix the pre-flush when appending to a file in writethrough mode (David Howells)
- netfs: Fix writethrough-mode error handling (David Howells)
- ntfs3: add legacy ntfs file operations (Christian Brauner)
- ntfs3: enforce read-only when used as legacy ntfs driver (Christian Brauner)
- ntfs3: serve as alias for the legacy ntfs driver (Christian Brauner)
- block: fix module reference leakage from bdev_open_by_dev error path (Yu Kuai)
- fs: Return ENOTTY directly if FS_IOC_GETUUID or FS_IOC_GETFSSYSFSPATH fail (Günther Noack)
- LoongArch: Lately init pmu after smp is online (Bibo Mao)
- LoongArch: Fix callchain parse error with kernel tracepoint events (Huacai Chen)
- LoongArch: Fix access error when read fault on a write-only VMA (Jiantao Shan)
- LoongArch: Fix a build error due to __tlb_remove_tlb_entry() (David Hildenbrand)
- LoongArch: Fix Kconfig item and left code related to CRASH_CORE (Baoquan He)
- MAINTAINERS: Update Uwe's email address, drop SIOX maintenance (Uwe Kleine-König)
- drm/xe/guc: Fix arguments passed to relay G2H handlers (Michal Wajdeczko)
- drm/xe: call free_gsc_pkt only once on action add failure (Himal Prasad Ghimiray)
- drm/xe: Remove sysfs only once on action add failure (Himal Prasad Ghimiray)
- Revert "drm/etnaviv: Expose a few more chipspecs to userspace" (Christian Gmeiner)
- drm/etnaviv: fix tx clock gating on some GC7000 variants (Derek Foreman)
- fbdev: fix incorrect address computation in deferred IO (Nam Cao)
- drm/atomic-helper: fix parameter order in drm_format_conv_state_copy() call (Lucas Stach)
- drm/gma500: Remove lid code (Patrik Jakobsson)
- drm/amdgpu/mes: fix use-after-free issue (Jack Xiao)
- drm/amdgpu/sdma5.2: use legacy HDP flush for SDMA2/3 (Alex Deucher)
- drm/amdgpu: Fix the ring buffer size for queue VM flush (Prike Liang)
- drm/amdkfd: Add VRAM accounting for SVM migration (Mukul Joshi)
- drm/amd/pm: Restore config space after reset (Lijo Lazar)
- drm/amdgpu/umsch: don't execute umsch test when GPU is in reset/suspend (Lang Yu)
- drm/amdkfd: Fix rescheduling of restore worker (Felix Kuehling)
- drm/amdgpu: Update BO eviction priorities (Felix Kuehling)
- drm/amdgpu/vpe: fix vpe dpm setup failed (Peyton Lee)
- drm/amdgpu: Assign correct bits for SDMA HDP flush (Lijo Lazar)
- drm/amdgpu/pm: Remove gpu_od if it's an empty directory (Ma Jun)
- drm/amdkfd: make sure VM is ready for updating operations (Lang Yu)
- drm/amdgpu: Fix leak when GPU memory allocation fails (Mukul Joshi)
- drm/amdkfd: Fix eviction fence handling (Felix Kuehling)
- drm/amd/display: Set color_mgmt_changed to true on unsuspend (Joshua Ashton)
- vDPA: code clean for vhost_vdpa uapi (Zhu Lingshan)
-  fs/9p: mitigate inode collisions (Eric Van Hensbergen)
- ACPI: CPPC: Fix access width used for PCC registers (Vanshidhar Konda)
- ACPI: CPPC: Fix bit_offset shift in MASK_VAL() macro (Jarred White)
- ACPI: PM: s2idle: Evaluate all Low-Power S0 Idle _DSM functions (Rafael J. Wysocki)
- netfilter: nf_tables: honor table dormant flag from netdev release event path (Pablo Neira Ayuso)
- ipvs: Fix checksumming on GSO of SCTP packets (Ismael Luceno)
- af_unix: Suppress false-positive lockdep splat for spin_lock() in __unix_gc(). (Kuniyuki Iwashima)
- net: b44: set pause params only when interface is up (Peter Münster)
- tls: fix lockless read of strp->msg_ready in ->poll (Sabrina Dubroca)
- dpll: fix dpll_pin_on_pin_register() for multiple parent pins (Arkadiusz Kubalewski)
- net: ravb: Fix registered interrupt names (Geert Uytterhoeven)
- octeontx2-af: fix the double free in rvu_npc_freemem() (Su Hui)
- net: ethernet: ti: am65-cpts: Fix PTPv1 message type on TX packets (Jason Reeder)
- ice: fix LAG and VF lock dependency in ice_reset_vf() (Jacob Keller)
- iavf: Fix TC config comparison with existing adapter TC config (Sudheer Mogilappagari)
- i40e: Report MFS in decimal base instead of hex (Erwan Velu)
- i40e: Do not use WQ_MEM_RECLAIM flag for workqueue (Sindhu Devale)
- net/mlx5e: Advertise mlx5 ethernet driver updates sk_buff md_dst for MACsec (Rahul Rameshbabu)
- macsec: Detect if Rx skb is macsec-related for offloading devices that update md_dst (Rahul Rameshbabu)
- ethernet: Add helper for assigning packet type when dest address does not match device address (Rahul Rameshbabu)
- macsec: Enable devices to advertise whether they update sk_buff md_dst during offloads (Rahul Rameshbabu)
- net: ti: icssg-prueth: Fix signedness bug in prueth_init_rx_chns() (Dan Carpenter)
- wifi: iwlwifi: mvm: fix link ID management (Johannes Berg)
- wifi: mac80211: fix unaligned le16 access (Johannes Berg)
- wifi: mac80211: remove link before AP (Johannes Berg)
- wifi: mac80211_hwsim: init peer measurement result (Johannes Berg)
- wifi: nl80211: don't free NULL coalescing rule (Johannes Berg)
- wifi: mac80211: mlme: re-parse if AP mode is less than client (Johannes Berg)
- wifi: mac80211: mlme: fix memory leak (Johannes Berg)
- wifi: mac80211: mlme: re-parse with correct mode (Johannes Berg)
- wifi: mac80211: fix idle calculation with multi-link (Johannes Berg)
- Revert "wifi: iwlwifi: bump FW API to 90 for BZ/SC devices" (Johannes Berg)
- wifi: iwlwifi: mvm: return uid from iwl_mvm_build_scan_cmd (Miri Korenblit)
- wifi: iwlwifi: mvm: remove old PASN station when adding a new one (Avraham Stern)
- wifi: mac80211: split mesh fast tx cache into local/proxied/forwarded (Felix Fietkau)
- wifi: ath11k: use RCU when accessing struct inet6_dev::ac_list (Kalle Valo)
- wifi: cfg80211: fix the order of arguments for trace events of the tx_rx_evt class (Igor Artemiev)
- wifi: mac80211: ensure beacon is non-S1G prior to extracting the beacon timestamp field (Richard Kinder)
- wifi: mac80211: don't use rate mask for scanning (Johannes Berg)
- wifi: mac80211: check EHT/TTLM action frame length (Johannes Berg)
- net: phy: dp83869: Fix MII mode failure (MD Danish Anwar)
- Bluetooth: qca: set power_ctrl_enabled on NULL returned by gpiod_get_optional() (Bartosz Golaszewski)
- Bluetooth: hci_sync: Using hci_cmd_sync_submit when removing Adv Monitor (Chun-Yi Lee)
- Bluetooth: qca: fix NULL-deref on non-serdev setup (Johan Hovold)
- Bluetooth: qca: fix NULL-deref on non-serdev suspend (Johan Hovold)
- Bluetooth: btusb: mediatek: Fix double free of skb in coredump (Sean Wang)
- Bluetooth: MGMT: Fix failing to MGMT_OP_ADD_UUID/MGMT_OP_REMOVE_UUID (Luiz Augusto von Dentz)
- Bluetooth: qca: fix invalid device address check (Johan Hovold)
- Bluetooth: hci_event: Fix sending HCI_OP_READ_ENC_KEY_SIZE (Luiz Augusto von Dentz)
- Bluetooth: btusb: Fix triggering coredump implementation for QCA (Zijun Hu)
- Bluetooth: btusb: Add Realtek RTL8852BE support ID 0x0bda:0x4853 (WangYuli)
- Bluetooth: hci_sync: Use advertised PHYs on hci_le_ext_create_conn_sync (Luiz Augusto von Dentz)
- Bluetooth: Fix type of len in {l2cap,sco}_sock_getsockopt_old() (Nathan Chancellor)
- eth: bnxt: fix counting packets discarded due to OOM and netpoll (Jakub Kicinski)
- igc: Fix LED-related deadlock on driver unbind (Lukas Wunner)
- Revert "net: txgbe: fix clk_name exceed MAX_DEV_ID limits" (Duanqiang Wen)
- Revert "net: txgbe: fix i2c dev name cannot match clkdev" (Duanqiang Wen)
- mlxsw: spectrum_acl_tcam: Fix memory leak when canceling rehash work (Ido Schimmel)
- mlxsw: spectrum_acl_tcam: Fix incorrect list API usage (Ido Schimmel)
- mlxsw: spectrum_acl_tcam: Fix warning during rehash (Ido Schimmel)
- mlxsw: spectrum_acl_tcam: Fix memory leak during rehash (Ido Schimmel)
- mlxsw: spectrum_acl_tcam: Rate limit error message (Ido Schimmel)
- mlxsw: spectrum_acl_tcam: Fix possible use-after-free during rehash (Ido Schimmel)
- mlxsw: spectrum_acl_tcam: Fix possible use-after-free during activity update (Ido Schimmel)
- mlxsw: spectrum_acl_tcam: Fix race during rehash delayed work (Ido Schimmel)
- mlxsw: spectrum_acl_tcam: Fix race in region ID allocation (Ido Schimmel)
- net: openvswitch: Fix Use-After-Free in ovs_ct_exit (Hyunwoo Kim)
- net: phy: mediatek-ge-soc: follow netdev LED trigger semantics (Daniel Golle)
- net: gtp: Fix Use-After-Free in gtp_dellink (Hyunwoo Kim)
- tcp: Fix Use-After-Free in tcp_ao_connect_init (Hyunwoo Kim)
- net: usb: ax88179_178a: stop lying about skb->truesize (Eric Dumazet)
- ipv4: check for NULL idev in ip_route_use_hint() (Eric Dumazet)
- net: fix sk_memory_allocated_{add|sub} vs softirqs (Eric Dumazet)
- tools: ynl: don't ignore errors in NLMSG_DONE messages (Jakub Kicinski)
- ax25: Fix netdev refcount issue (Duoming Zhou)
- NFC: trf7970a: disable all regulators on removal (Paul Geurts)
- MAINTAINERS: eth: mark IBM eHEA as an Orphan (David Christensen)
- net: dsa: mv88e6xx: fix supported_interfaces setup in mv88e6250_phylink_get_caps() (Matthias Schiffer)
- bnxt_en: Fix error recovery for 5760X (P7) chips (Michael Chan)
- bnxt_en: Fix the PCI-AER routines (Vikas Gupta)
- bnxt_en: refactor reset close code (Vikas Gupta)
- bridge/br_netlink.c: no need to return void function (Hangbin Liu)
- mailmap: add entries for Alex Elder (Alex Elder)
- icmp: prevent possible NULL dereferences from icmp_build_probe() (Eric Dumazet)
- net: usb: qmi_wwan: add Telit FN920C04 compositions (Daniele Palmas)
- mlxsw: pci: Fix driver initialization with old firmware (Ido Schimmel)
- mlxsw: core_env: Fix driver initialization with old firmware (Ido Schimmel)
- mlxsw: core: Unregister EMAD trap using FORWARD action (Ido Schimmel)
- net: bcmasp: fix memory leak when bringing down interface (Justin Chen)
- udp: preserve the connected status if only UDP cmsg (Yick Xie)
- vxlan: drop packets from invalid src-address (David Bauer)
- net: libwx: fix alloc msix vectors failed (Duanqiang Wen)
- Revert "NFSD: Convert the callback workqueue to use delayed_work" (Chuck Lever)
- Revert "NFSD: Reschedule CB operations when backchannel rpc_clnt is shut down" (Chuck Lever)
- HID: mcp-2221: cancel delayed_work only when CONFIG_IIO is enabled (Abdelrahman Morsy)
- HID: logitech-dj: allow mice to use all types of reports (Yaraslau Furman)
- HID: i2c-hid: Revert to await reset ACK before reading report descriptor (Kenny Levinsen)
- HID: nintendo: Fix N64 controller being identified as mouse (Nuno Pereira)
- MAINTAINERS: update Benjamin's email address (Benjamin Tissoires)
- HID: intel-ish-hid: ipc: Fix dev_err usage with uninitialized dev->devc (Zhang Lixu)
- HID: i2c-hid: remove I2C_HID_READ_PENDING flag to prevent lock-up (Nam Cao)
- Turn on ISM for Fedora (Justin M. Forbes)
- btrfs: fix wrong block_start calculation for btrfs_drop_extent_map_range() (Qu Wenruo)
- btrfs: fix information leak in btrfs_ioctl_logical_to_ino() (Johannes Thumshirn)
- btrfs: fallback if compressed IO fails for ENOSPC (Sweet Tea Dorminy)
- btrfs: scrub: run relocation repair when/only needed (Naohiro Aota)
- btrfs: remove colon from messages with state (David Sterba)

* Thu Apr 25 2024 Jan Stancek <jstancek@redhat.com> [6.9.0-0.rc5.3.el10]
- cifs: reinstate original behavior again for forceuid/forcegid (Takayuki Nagata)
- smb: client: fix rename(2) regression against samba (Paulo Alcantara)
- cifs: Add tracing for the cifs_tcon struct refcounting (David Howells)
- cifs: Fix reacquisition of volume cookie on still-live connection (David Howells)
- redhat/configs: enable CONFIG_TEST_LOCKUP for non-debug kernels (Čestmír Kalina)
- redhat/rhel_files: add test_lockup.ko to modules-extra (Čestmír Kalina)
- Turn off some Fedora UBSAN options to avoid false positives (Justin M. Forbes)
- ksmbd: add continuous availability share parameter (Namjae Jeon)
- ksmbd: common: use struct_group_attr instead of struct_group for network_open_info (Namjae Jeon)
- ksmbd: clear RENAME_NOREPLACE before calling vfs_rename (Marios Makassikis)
- ksmbd: validate request buffer size in smb2_allocate_rsp_buf() (Namjae Jeon)
- ksmbd: fix slab-out-of-bounds in smb2_allocate_rsp_buf (Namjae Jeon)
- bcachefs: If we run merges at a lower watermark, they must be nonblocking (Kent Overstreet)
- bcachefs: Fix inode early destruction path (Kent Overstreet)
- bcachefs: Fix deadlock in journal write path (Kent Overstreet)
- bcachefs: Tweak btree key cache shrinker so it actually frees (Kent Overstreet)
- bcachefs: bkey_cached.btree_trans_barrier_seq needs to be a ulong (Kent Overstreet)
- bcachefs: Fix missing call to bch2_fs_allocator_background_exit() (Kent Overstreet)
- bcachefs: Check for journal entries overruning end of sb clean section (Kent Overstreet)
- bcachefs: Fix bio alloc in check_extent_checksum() (Kent Overstreet)
- bcachefs: fix leak in bch2_gc_write_reflink_key (Kent Overstreet)
- bcachefs: KEY_TYPE_error is allowed for reflink (Kent Overstreet)
- bcachefs: Fix bch2_dev_btree_bitmap_marked_sectors() shift (Kent Overstreet)
- bcachefs: make sure to release last journal pin in replay (Kent Overstreet)
- bcachefs: node scan: ignore multiple nodes with same seq if interior (Kent Overstreet)
- bcachefs: Fix format specifier in validate_bset_keys() (Nathan Chancellor)
- bcachefs: Fix null ptr deref in twf from BCH_IOCTL_FSCK_OFFLINE (Kent Overstreet)
- Revert "svcrdma: Add Write chunk WRs to the RPC's Send WR chain" (Chuck Lever)
- docs: verify/bisect: stable regressions: first stable, then mainline (Thorsten Leemhuis)
- docs: verify/bisect: describe how to use a build host (Thorsten Leemhuis)
- docs: verify/bisect: explain testing reverts, patches and newer code (Thorsten Leemhuis)
- docs: verify/bisect: proper headlines and more spacing (Thorsten Leemhuis)
- docs: verify/bisect: add and fetch stable branches ahead of time (Thorsten Leemhuis)
- docs: verify/bisect: use git switch, tag kernel, and various fixes (Thorsten Leemhuis)
- Linux 6.9-rc5 (Linus Torvalds)
- peci: linux/peci.h: fix Excess kernel-doc description warning (Randy Dunlap)
- binder: check offset alignment in binder_get_object() (Carlos Llamas)
- comedi: vmk80xx: fix incomplete endpoint checking (Nikita Zhandarovich)
- mei: vsc: Unregister interrupt handler for system suspend (Sakari Ailus)
- Revert "mei: vsc: Call wake_up() in the threaded IRQ handler" (Sakari Ailus)
- misc: rtsx: Fix rts5264 driver status incorrect when card removed (Ricky Wu)
- mei: me: disable RPL-S on SPS and IGN firmwares (Alexander Usyskin)
- interconnect: Don't access req_list while it's being manipulated (Mike Tipton)
- interconnect: qcom: x1e80100: Remove inexistent ACV_PERF BCM (Konrad Dybcio)
- speakup: Avoid crash on very long word (Samuel Thibault)
- Documentation: embargoed-hardware-issues.rst: Add myself for Power (Michael Ellerman)
- fs: sysfs: Fix reference leak in sysfs_break_active_protection() (Alan Stern)
- serial: stm32: Reset .throttled state in .startup() (Uwe Kleine-König)
- serial: stm32: Return IRQ_NONE in the ISR if no handling happend (Uwe Kleine-König)
- serial: core: Fix missing shutdown and startup for serial base port (Tony Lindgren)
- serial: core: Clearing the circular buffer before NULLifying it (Andy Shevchenko)
- MAINTAINERS: mailmap: update Richard Genoud's email address (Richard Genoud)
- serial/pmac_zilog: Remove flawed mitigation for rx irq flood (Finn Thain)
- serial: 8250_pci: Remove redundant PCI IDs (Andy Shevchenko)
- serial: core: Fix regression when runtime PM is not enabled (Tony Lindgren)
- serial: mxs-auart: add spinlock around changing cts state (Emil Kronborg)
- serial: 8250_dw: Revert: Do not reclock if already at correct rate (Hans de Goede)
- serial: 8250_lpc18xx: disable clks on error in probe() (Dan Carpenter)
- USB: serial: option: add Telit FN920C04 rmnet compositions (Daniele Palmas)
- USB: serial: option: add Rolling RW101-GL and RW135-GL support (Vanillan Wang)
- USB: serial: option: add Lonsung U8300/U9300 product (Coia Prant)
- USB: serial: option: add support for Fibocom FM650/FG650 (Chuanhong Guo)
- USB: serial: option: support Quectel EM060K sub-models (Jerry Meng)
- USB: serial: option: add Fibocom FM135-GL variants (bolan wang)
- usb: dwc3: ep0: Don't reset resource alloc flag (Thinh Nguyen)
- Revert "usb: cdc-wdm: close race between read and workqueue" (Greg Kroah-Hartman)
- thunderbolt: Avoid notify PM core about runtime PM resume (Gil Fine)
- thunderbolt: Fix wake configurations after device unplug (Gil Fine)
- thunderbolt: Do not create DisplayPort tunnels on adapters of the same router (Mika Westerberg)
- usb: misc: onboard_usb_hub: Disable the USB hub clock on failure (Fabio Estevam)
- usb: dwc2: host: Fix dereference issue in DDMA completion flow. (Minas Harutyunyan)
- usb: typec: mux: it5205: Fix ChipID value typo (AngeloGioacchino Del Regno)
- MAINTAINERS: Drop Li Yang as their email address stopped working (Uwe Kleine-König)
- usb: gadget: fsl: Initialize udc before using it (Uwe Kleine-König)
- usb: Disable USB3 LPM at shutdown (Kai-Heng Feng)
- usb: gadget: f_ncm: Fix UAF ncm object at re-bind after usb ep transport error (Norihiko Hama)
- usb: typec: tcpm: Correct the PDO counting in pd_set (Kyle Tso)
- usb: gadget: functionfs: Wait for fences before enqueueing DMABUF (Paul Cercueil)
- usb: gadget: functionfs: Fix inverted DMA fence direction (Paul Cercueil)
- usb: typec: ucsi: Fix connector check on init (Christian A. Ehrhardt)
- usb: phy: MAINTAINERS: mark Freescale USB PHY as orphaned (Krzysztof Kozlowski)
- xhci: Fix root hub port null pointer dereference in xhci tracepoints (Mathias Nyman)
- usb: xhci: correct return value in case of STS_HCE (Oliver Neukum)
- sched: Add missing memory barrier in switch_mm_cid (Mathieu Desnoyers)
- x86/cpufeatures: Fix dependencies for GFNI, VAES, and VPCLMULQDQ (Eric Biggers)
- x86/fred: Fix incorrect error code printout in fred_bad_type() (Hou Wenlong)
- x86/fred: Fix INT80 emulation for FRED (Xin Li (Intel))
- x86/retpolines: Enable the default thunk warning only on relevant configs (Borislav Petkov (AMD))
- x86/bugs: Fix BHI retpoline check (Josh Poimboeuf)
- fedora: aarch64: Enable a QCom Robotics platforms requirements (Peter Robinson)
- fedora: updates for 6.9 merge window (Peter Robinson)
- gitlab-ci: rename GitLab jobs ark -> rawhide (Michael Hofmann)
- gitlab-ci: add initial version (Michael Hofmann)
- Linux v6.9.0-0.rc5

* Mon Apr 22 2024 Jan Stancek <jstancek@redhat.com> [6.9.0-0.rc4.2.el10]
- blk-iocost: do not WARN if iocg was already offlined (Li Nan)
- block: propagate partition scanning errors to the BLKRRPART ioctl (Christoph Hellwig)
- MAINTAINERS: update to working email address (James Bottomley)
- KVM: x86: Stop compiling vmenter.S with OBJECT_FILES_NON_STANDARD (Sean Christopherson)
- KVM: SVM: Create a stack frame in __svm_sev_es_vcpu_run() (Sean Christopherson)
- KVM: SVM: Save/restore args across SEV-ES VMRUN via host save area (Sean Christopherson)
- KVM: SVM: Save/restore non-volatile GPRs in SEV-ES VMRUN via host save area (Sean Christopherson)
- KVM: SVM: Clobber RAX instead of RBX when discarding spec_ctrl_intercepted (Sean Christopherson)
- KVM: SVM: Drop 32-bit "support" from __svm_sev_es_vcpu_run() (Sean Christopherson)
- KVM: SVM: Wrap __svm_sev_es_vcpu_run() with #ifdef CONFIG_KVM_AMD_SEV (Sean Christopherson)
- KVM: SVM: Create a stack frame in __svm_vcpu_run() for unwinding (Sean Christopherson)
- KVM: SVM: Remove a useless zeroing of allocated memory (Christophe JAILLET)
- KVM: Drop unused @may_block param from gfn_to_pfn_cache_invalidate_start() (Sean Christopherson)
- KVM: selftests: Add coverage of EPT-disabled to vmx_dirty_log_test (David Matlack)
- KVM: x86/mmu: Fix and clarify comments about clearing D-bit vs. write-protecting (David Matlack)
- KVM: x86/mmu: Remove function comments above clear_dirty_{gfn_range,pt_masked}() (David Matlack)
- KVM: x86/mmu: Write-protect L2 SPTEs in TDP MMU when clearing dirty status (David Matlack)
- KVM: x86/mmu: Precisely invalidate MMU root_role during CPUID update (Sean Christopherson)
- KVM: VMX: Disable LBR virtualization if the CPU doesn't support LBR callstacks (Sean Christopherson)
- perf/x86/intel: Expose existence of callback support to KVM (Sean Christopherson)
- KVM: VMX: Snapshot LBR capabilities during module initialization (Sean Christopherson)
- KVM: VMX: Ignore MKTME KeyID bits when intercepting #PF for allow_smaller_maxphyaddr (Tao Su)
- KVM: selftests: fix supported_flags for riscv (Andrew Jones)
- KVM: selftests: fix max_guest_memory_test with more that 256 vCPUs (Maxim Levitsky)
- KVM: selftests: Verify post-RESET value of PERF_GLOBAL_CTRL in PMCs test (Sean Christopherson)
- KVM: x86/pmu: Set enable bits for GP counters in PERF_GLOBAL_CTRL at "RESET" (Sean Christopherson)
- KVM: x86/mmu: x86: Don't overflow lpage_info when checking attributes (Rick Edgecombe)
- KVM: x86/pmu: Disable support for adaptive PEBS (Sean Christopherson)
- KVM: Explicitly disallow activatating a gfn_to_pfn_cache with INVALID_GPA (Sean Christopherson)
- KVM: Check validity of offset+length of gfn_to_pfn_cache prior to activation (Sean Christopherson)
- KVM: Add helpers to consolidate gfn_to_pfn_cache's page split check (Sean Christopherson)
- KVM: x86/pmu: Do not mask LVTPC when handling a PMI on AMD platforms (Sandipan Das)
- KVM: x86: Snapshot if a vCPU's vendor model is AMD vs. Intel compatible (Sean Christopherson)
- selftests/powerpc/papr-vpd: Fix missing variable initialization (Nathan Lynch)
- powerpc/crypto/chacha-p10: Fix failure on non Power10 (Michael Ellerman)
- powerpc/iommu: Refactor spapr_tce_platform_iommu_attach_dev() (Shivaprasad G Bhat)
- clk: mediatek: mt7988-infracfg: fix clocks for 2nd PCIe port (Daniel Golle)
- clk: mediatek: Do a runtime PM get on controllers during probe (Pin-yen Lin)
- clk: Get runtime PM before walking tree for clk_summary (Stephen Boyd)
- clk: Get runtime PM before walking tree during disable_unused (Stephen Boyd)
- clk: Initialize struct clk_core kref earlier (Stephen Boyd)
- clk: Don't hold prepare_lock when calling kref_put() (Stephen Boyd)
- clk: Remove prepare_lock hold assertion in __clk_release() (Stephen Boyd)
- clk: Provide !COMMON_CLK dummy for devm_clk_rate_exclusive_get() (Uwe Kleine-König)
- tools/include: Sync arm64 asm/cputype.h with the kernel sources (Namhyung Kim)
- tools/include: Sync asm-generic/bitops/fls.h with the kernel sources (Namhyung Kim)
- tools/include: Sync x86 asm/msr-index.h with the kernel sources (Namhyung Kim)
- tools/include: Sync x86 asm/irq_vectors.h with the kernel sources (Namhyung Kim)
- tools/include: Sync x86 CPU feature headers with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/sound/asound.h with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/linux/kvm.h and asm/kvm.h with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/linux/fs.h with the kernel sources (Namhyung Kim)
- tools/include: Sync uapi/drm/i915_drm.h with the kernel sources (Namhyung Kim)
- perf lock contention: Add a missing NULL check (Namhyung Kim)
- perf annotate: Make sure to call symbol__annotate2() in TUI (Namhyung Kim)
- ubsan: Add awareness of signed integer overflow traps (Kees Cook)
- configs/hardening: Disable CONFIG_UBSAN_SIGNED_WRAP (Nathan Chancellor)
- configs/hardening: Fix disabling UBSAN configurations (Nathan Chancellor)
- iommufd: Add config needed for iommufd_fail_nth (Muhammad Usama Anjum)
- iommufd: Add missing IOMMUFD_DRIVER kconfig for the selftest (Jason Gunthorpe)
- RDMA/mlx5: Fix port number for counter query in multi-port configuration (Michael Guralnik)
- RDMA/cm: Print the old state when cm_destroy_id gets timeout (Mark Zhang)
- RDMA/rxe: Fix the problem "mutex_destroy missing" (Yanjun.Zhu)
- fs/9p: drop inodes immediately on non-.L too (Joakim Sindholt)
- fs/9p: Revert "fs/9p: fix dups even in uncached mode" (Eric Van Hensbergen)
- fs/9p: remove erroneous nlink init from legacy stat2inode (Eric Van Hensbergen)
- 9p: explicitly deny setlease attempts (Jeff Layton)
- fs/9p: fix the cache always being enabled on files with qid flags (Joakim Sindholt)
- fs/9p: translate O_TRUNC into OTRUNC (Joakim Sindholt)
- fs/9p: only translate RWX permissions for plain 9P2000 (Joakim Sindholt)
- cuse: add kernel-doc comments to cuse_process_init_reply() (Yang Li)
- fuse: fix leaked ENOSYS error on first statx call (Danny Lin)
- fuse: fix parallel dio write on file open in passthrough mode (Amir Goldstein)
- fuse: fix wrong ff->iomode state changes from parallel dio write (Amir Goldstein)
- arm64: hibernate: Fix level3 translation fault in swsusp_save() (Yaxiong Tian)
- arm64/head: Disable MMU at EL2 before clearing HCR_EL2.E2H (Ard Biesheuvel)
- arm64/head: Drop unnecessary pre-disable-MMU workaround (Ard Biesheuvel)
- arm64/hugetlb: Fix page table walk in huge_pte_alloc() (Anshuman Khandual)
- s390/mm: Fix NULL pointer dereference (Sven Schnelle)
- s390/cio: log fake IRB events (Peter Oberparleiter)
- s390/cio: fix race condition during online processing (Peter Oberparleiter)
- s390/qdio: handle deferred cc1 (Peter Oberparleiter)
- bootconfig: Fix the kerneldoc of _xbc_exit() (Masami Hiramatsu (Google))
- bootconfig: use memblock_free_late to free xbc memory to buddy (Qiang Zhang)
- init/main.c: Fix potential static_command_line memory overflow (Yuntao Wang)
- thermal/debugfs: Add missing count increment to thermal_debug_tz_trip_up() (Rafael J. Wysocki)
- ALSA: seq: ump: Fix conversion from MIDI2 to MIDI1 UMP messages (Takashi Iwai)
- ALSA: hda/realtek - Enable audio jacks of Haier Boyue G42 with ALC269VC (Ai Chao)
- ALSA: hda/realtek: Add quirks for Huawei Matebook D14 NBLB-WAX9N (Mauro Carvalho Chehab)
- ALSA: hda/realtek: Fix volumn control of ThinkBook 16P Gen4 (Huayu Zhang)
- ALSA: hda/realtek: Fixes for Asus GU605M and GA403U sound (Vitalii Torshyn)
- ALSA: hda/tas2781: Add new vendor_id and subsystem_id to support ThinkPad ICE-1 (Shenghao Ding)
- ALSA: hda/tas2781: correct the register for pow calibrated data (Shenghao Ding)
- ALSA: hda/realtek: Add quirk for HP SnowWhite laptops (Vitaly Rodionov)
- drm/xe/vm: prevent UAF with asid based lookup (Matthew Auld)
- drm/xe: Fix bo leak in intel_fb_bo_framebuffer_init (Maarten Lankhorst)
- drm/panel: novatek-nt36682e: don't unregister DSI device (Dmitry Baryshkov)
- drm/panel: visionox-rm69299: don't unregister DSI device (Dmitry Baryshkov)
- drm/nouveau/dp: Don't probe eDP ports twice harder (Lyude Paul)
- drm/nouveau/kms/nv50-: Disable AUX bus for disconnected DP ports (Lyude Paul)
- drm/v3d: Don't increment `enabled_ns` twice (Maíra Canal)
- drm/vmwgfx: Sort primary plane formats by order of preference (Zack Rusin)
- drm/vmwgfx: Fix crtc's atomic check conditional (Zack Rusin)
- drm/vmwgfx: Fix prime import/export (Zack Rusin)
- drm/ttm: stop pooling cached NUMA pages v2 (Christian König)
- drm: nv04: Fix out of bounds access (Mikhail Kobuk)
- nouveau: fix instmem race condition around ptr stores (Dave Airlie)
- drm/radeon: silence UBSAN warning (v3) (Alex Deucher)
- drm/radeon: make -fstrict-flex-arrays=3 happy (Alex Deucher)
- drm/amdgpu: fix visible VRAM handling during faults (Christian König)
- drm/amdgpu: validate the parameters of bo mapping operations more clearly (xinhui pan)
- Revert "drm/amd/display: fix USB-C flag update after enc10 feature init" (Alex Deucher)
- drm/amdkfd: Fix memory leak in create_process failure (Felix Kuehling)
- drm/amdgpu: remove invalid resource->start check v2 (Christian König)
- nilfs2: fix OOB in nilfs_set_de_type (Jeongjun Park)
- MAINTAINERS: update Naoya Horiguchi's email address (Naoya Horiguchi)
- fork: defer linking file vma until vma is fully initialized (Miaohe Lin)
- mm/shmem: inline shmem_is_huge() for disabled transparent hugepages (Sumanth Korikkar)
- mm,page_owner: defer enablement of static branch (Oscar Salvador)
- Squashfs: check the inode number is not the invalid value of zero (Phillip Lougher)
- mm,swapops: update check in is_pfn_swap_entry for hwpoison entries (Oscar Salvador)
- mm/memory-failure: fix deadlock when hugetlb_optimize_vmemmap is enabled (Miaohe Lin)
- mm/userfaultfd: allow hugetlb change protection upon poison entry (Peter Xu)
- mm,page_owner: fix printing of stack records (Oscar Salvador)
- mm,page_owner: fix accounting of pages when migrating (Oscar Salvador)
- mm,page_owner: fix refcount imbalance (Oscar Salvador)
- mm,page_owner: update metadata for tail pages (Oscar Salvador)
- userfaultfd: change src_folio after ensuring it's unpinned in UFFDIO_MOVE (Lokesh Gidra)
- mm/madvise: make MADV_POPULATE_(READ|WRITE) handle VM_FAULT_RETRY properly (David Hildenbrand)
- scsi: core: Fix handling of SCMD_FAIL_IF_RECOVERING (Bart Van Assche)
- scsi: ufs: qcom: Add missing interconnect bandwidth values for Gear 5 (Manivannan Sadhasivam)
- net: ethernet: ti: am65-cpsw-nuss: cleanup DMA Channels before using them (Siddharth Vadapalli)
- net: usb: ax88179_178a: avoid writing the mac address before first reading (Jose Ignacio Tornos Martinez)
- netfilter: nf_tables: fix memleak in map from abort path (Pablo Neira Ayuso)
- netfilter: nf_tables: restore set elements when delete set fails (Pablo Neira Ayuso)
- netfilter: nf_tables: missing iterator type in lookup walk (Pablo Neira Ayuso)
- net: ravb: Fix RX byte accounting for jumbo packets (Paul Barker)
- net: ravb: Fix GbEth jumbo packet RX checksum handling (Paul Barker)
- net: ravb: Allow RX loop to move past DMA mapping errors (Paul Barker)
- net: ravb: Count packets instead of descriptors in R-Car RX path (Paul Barker)
- net: ethernet: mtk_eth_soc: fix WED + wifi reset (Felix Fietkau)
- net:usb:qmi_wwan: support Rolling modules (Vanillan Wang)
- ice: Fix checking for unsupported keys on non-tunnel device (Marcin Szycik)
- ice: tc: allow zero flags in parsing tc flower (Michal Swiatkowski)
- ice: tc: check src_vsi in case of traffic from VF (Michal Swiatkowski)
- selftests: kselftest_harness: fix Clang warning about zero-length format (Jakub Kicinski)
- net/sched: Fix mirred deadlock on device recursion (Eric Dumazet)
- s390/ism: Properly fix receive message buffer allocation (Gerd Bayer)
- net: dsa: mt7530: fix port mirroring for MT7988 SoC switch (Arınç ÜNAL)
- net: dsa: mt7530: fix mirroring frames received on local port (Arınç ÜNAL)
- tun: limit printing rate when illegal packet received by tun dev (Lei Chen)
- net: stmmac: Fix IP-cores specific MAC capabilities (Serge Semin)
- net: stmmac: Fix max-speed being ignored on queue re-init (Serge Semin)
- net: stmmac: Apply half-duplex-less constraint for DW QoS Eth only (Serge Semin)
- selftests/tcp_ao: Printing fixes to confirm with format-security (Dmitry Safonov)
- selftests/tcp_ao: Fix fscanf() call for format-security (Dmitry Safonov)
- selftests/tcp_ao: Zero-init tcp_ao_info_opt (Dmitry Safonov)
- selftests/tcp_ao: Make RST tests less flaky (Dmitry Safonov)
- octeontx2-pf: fix FLOW_DIS_IS_FRAGMENT implementation (Asbjørn Sloth Tønnesen)
- inet: bring NLM_DONE out to a separate recv() again (Jakub Kicinski)
- net: change maximum number of UDP segments to 128 (Yuri Benditovich)
- net/mlx5e: Prevent deadlock while disabling aRFS (Carolina Jubran)
- net/mlx5e: Acquire RTNL lock before RQs/SQs activation/deactivation (Carolina Jubran)
- net/mlx5e: Use channel mdev reference instead of global mdev instance for coalescing (Rahul Rameshbabu)
- net/mlx5: Restore mistakenly dropped parts in register devlink flow (Shay Drory)
- net/mlx5: SD, Handle possible devcom ERR_PTR (Tariq Toukan)
- net/mlx5: Lag, restore buckets number to default after hash LAG deactivation (Shay Drory)
- net: sparx5: flower: fix fragment flags handling (Asbjørn Sloth Tønnesen)
- af_unix: Don't peek OOB data without MSG_OOB. (Kuniyuki Iwashima)
- af_unix: Call manage_oob() for every skb in unix_stream_read_generic(). (Kuniyuki Iwashima)
- netfilter: flowtable: incorrect pppoe tuple (Pablo Neira Ayuso)
- netfilter: flowtable: validate pppoe header (Pablo Neira Ayuso)
- netfilter: nft_set_pipapo: do not free live element (Florian Westphal)
- netfilter: nft_set_pipapo: walk over current view on netlink dump (Pablo Neira Ayuso)
- netfilter: br_netfilter: skip conntrack input hook for promisc packets (Pablo Neira Ayuso)
- netfilter: nf_tables: Fix potential data-race in __nft_obj_type_get() (Ziyang Xuan)
- netfilter: nf_tables: Fix potential data-race in __nft_expr_type_get() (Ziyang Xuan)
- gpiolib: swnode: Remove wrong header inclusion (Andy Shevchenko)
- gpio: lpc32xx: fix module autoloading (Krzysztof Kozlowski)
- gpio: crystalcove: Use -ENOTSUPP consistently (Andy Shevchenko)
- gpio: wcove: Use -ENOTSUPP consistently (Andy Shevchenko)
- Revert "vmgenid: emit uevent when VMGENID updates" (Jason A. Donenfeld)
- random: handle creditable entropy from atomic process context (Jason A. Donenfeld)
- platform/x86/amd/pmc: Extend Framework 13 quirk to more BIOSes (Mario Limonciello)
- platform/x86/intel-uncore-freq: Increase minor number support (Srinivas Pandruvada)
- platform/x86: ISST: Add Granite Rapids-D to HPM CPU list (Srinivas Pandruvada)
- platform/x86/amd: pmf: Add quirk for ROG Zephyrus G14 (Mario Limonciello)
- platform/x86/amd: pmf: Add infrastructure for quirking supported funcs (Mario Limonciello)
- platform/x86/amd: pmf: Decrease error message to debug (Mario Limonciello)
- gitlab-ci: harmonize DataWarehouse tree names (Michael Hofmann)
- redhat/configs: Enable CONFIG_INTEL_IOMMU_SCALABLE_MODE_DEFAULT_ON for rhel (Jerry Snitselaar)
- spec: make sure posttrans script doesn't fail if /boot is non-POSIX (glb)
- btrfs: do not wait for short bulk allocation (Qu Wenruo)
- btrfs: zoned: add ASSERT and WARN for EXTENT_BUFFER_ZONED_ZEROOUT handling (Naohiro Aota)
- btrfs: zoned: do not flag ZEROOUT on non-dirty extent buffer (Naohiro Aota)
- dt-bindings: pwm: mediatek,pwm-disp: Document power-domains property (AngeloGioacchino Del Regno)
- pwm: dwc: allow suspend/resume for 16 channels (Raag Jadav)
- Turn on UBSAN for Fedora (Justin M. Forbes)
- Turn on XEN_BALLOON_MEMORY_HOTPLUG for Fedora (Justin M. Forbes)
- NFSD: fix endianness issue in nfsd4_encode_fattr4 (Vasily Gorbik)
- SUNRPC: Fix rpcgss_context trace event acceptor field (Steven Rostedt (Google))
- bcachefs: set_btree_iter_dontneed also clears should_be_locked (Kent Overstreet)
- bcachefs: fix error path of __bch2_read_super() (Chao Yu)
- bcachefs: Check for backpointer bucket_offset >= bucket size (Kent Overstreet)
- bcachefs: bch_member.btree_allocated_bitmap (Kent Overstreet)
- bcachefs: sysfs internal/trigger_journal_flush (Kent Overstreet)
- bcachefs: Fix bch2_btree_node_fill() for !path (Kent Overstreet)
- bcachefs: add safety checks in bch2_btree_node_fill() (Kent Overstreet)
- bcachefs: Interior known are required to have known key types (Kent Overstreet)
- bcachefs: add missing bounds check in __bch2_bkey_val_invalid() (Kent Overstreet)
- bcachefs: Fix btree node merging on write buffer btrees (Kent Overstreet)
- bcachefs: Disable merges from interior update path (Kent Overstreet)
- bcachefs: Run merges at BCH_WATERMARK_btree (Kent Overstreet)
- bcachefs: Fix missing write refs in fs fio paths (Kent Overstreet)
- bcachefs: Fix deadlock in journal replay (Kent Overstreet)
- bcachefs: Go rw if running any explicit recovery passes (Kent Overstreet)
- bcachefs: Standardize helpers for printing enum strs with bounds checks (Kent Overstreet)
- bcachefs: don't queue btree nodes for rewrites during scan (Kent Overstreet)
- bcachefs: fix race in bch2_btree_node_evict() (Kent Overstreet)
- bcachefs: fix unsafety in bch2_stripe_to_text() (Kent Overstreet)
- bcachefs: fix unsafety in bch2_extent_ptr_to_text() (Kent Overstreet)
- bcachefs: btree node scan: handle encrypted nodes (Kent Overstreet)
- bcachefs: Check for packed bkeys that are too big (Kent Overstreet)
- bcachefs: Fix UAFs of btree_insert_entry array (Kent Overstreet)
- bcachefs: Don't use bch2_btree_node_lock_write_nofail() in btree split path (Kent Overstreet)
- selftests/harness: Prevent infinite loop due to Assert in FIXTURE_TEARDOWN (Shengyu Li)
- selftests/ftrace: Limit length in subsystem-enable tests (Yuanhe Shu)
- Linux 6.9-rc4 (Linus Torvalds)
- kernfs: annotate different lockdep class for of->mutex of writable files (Amir Goldstein)
- x86/cpu/amd: Move TOPOEXT enablement into the topology parser (Thomas Gleixner)
- x86/cpu/amd: Make the NODEID_MSR union actually work (Thomas Gleixner)
- x86/cpu/amd: Make the CPUID 0x80000008 parser correct (Thomas Gleixner)
- x86/bugs: Replace CONFIG_SPECTRE_BHI_{ON,OFF} with CONFIG_MITIGATION_SPECTRE_BHI (Josh Poimboeuf)
- x86/bugs: Remove CONFIG_BHI_MITIGATION_AUTO and spectre_bhi=auto (Josh Poimboeuf)
- x86/bugs: Clarify that syscall hardening isn't a BHI mitigation (Josh Poimboeuf)
- x86/bugs: Fix BHI handling of RRSBA (Josh Poimboeuf)
- x86/bugs: Rename various 'ia32_cap' variables to 'x86_arch_cap_msr' (Ingo Molnar)
- x86/bugs: Cache the value of MSR_IA32_ARCH_CAPABILITIES (Josh Poimboeuf)
- x86/bugs: Fix BHI documentation (Josh Poimboeuf)
- x86/cpu: Actually turn off mitigations by default for SPECULATION_MITIGATIONS=n (Sean Christopherson)
- x86/topology: Don't update cpu_possible_map in topo_set_cpuids() (Thomas Gleixner)
- x86/bugs: Fix return type of spectre_bhi_state() (Daniel Sneddon)
- x86/apic: Force native_apic_mem_read() to use the MOV instruction (Adam Dunlap)
- selftests: kselftest: Fix build failure with NOLIBC (Oleg Nesterov)
- selftests: timers: Fix abs() warning in posix_timers test (John Stultz)
- selftests: kselftest: Mark functions that unconditionally call exit() as __noreturn (Nathan Chancellor)
- selftests: timers: Fix posix_timers ksft_print_msg() warning (John Stultz)
- selftests: timers: Fix valid-adjtimex signed left-shift undefined behavior (John Stultz)
- bug: Fix no-return-statement warning with !CONFIG_BUG (Adrian Hunter)
- timekeeping: Use READ/WRITE_ONCE() for tick_do_timer_cpu (Thomas Gleixner)
- selftests/timers/posix_timers: Reimplement check_timer_distribution() (Oleg Nesterov)
- irqflags: Explicitly ignore lockdep_hrtimer_exit() argument (Arnd Bergmann)
- perf/x86: Fix out of range data (Namhyung Kim)
- locking: Make rwsem_assert_held_write_nolockdep() build with PREEMPT_RT=y (Sebastian Andrzej Siewior)
- irqchip/gic-v3-its: Fix VSYNC referencing an unmapped VPE on GIC v4.1 (Nianyao Tang)
- vhost: correct misleading printing information (Xianting Tian)
- vhost-vdpa: change ioctl # for VDPA_GET_VRING_SIZE (Michael S. Tsirkin)
- virtio: store owner from modules with register_virtio_driver() (Krzysztof Kozlowski)
- vhost: Add smp_rmb() in vhost_enable_notify() (Gavin Shan)
- vhost: Add smp_rmb() in vhost_vq_avail_empty() (Gavin Shan)
- swiotlb: do not set total_used to 0 in swiotlb_create_debugfs_files() (Dexuan Cui)
- swiotlb: fix swiotlb_bounce() to do partial sync's correctly (Michael Kelley)
- swiotlb: extend buffer pre-padding to alloc_align_mask if necessary (Petr Tesarik)
- ata: libata-core: Allow command duration limits detection for ACS-4 drives (Igor Pylypiv)
- ata: libata-scsi: Fix ata_scsi_dev_rescan() error path (Damien Le Moal)
- ata: ahci: Add mask_port_map module parameter (Damien Le Moal)
- zonefs: Use str_plural() to fix Coccinelle warning (Thorsten Blum)
- smb3: fix broken reconnect when password changing on the server by allowing password rotation (Steve French)
- smb: client: instantiate when creating SFU files (Paulo Alcantara)
- smb3: fix Open files on server counter going negative (Steve French)
- smb: client: fix NULL ptr deref in cifs_mark_open_handles_for_deleted_file() (Paulo Alcantara)
- arm64: tlb: Fix TLBI RANGE operand (Gavin Shan)
- MAINTAINERS: Change Krzysztof Kozlowski's email address (Krzysztof Kozlowski)
- cache: sifive_ccache: Partially convert to a platform driver (Samuel Holland)
- firmware: arm_ffa: Fix the partition ID check in ffa_notification_info_get() (Jens Wiklander)
- firmware: arm_scmi: Make raw debugfs entries non-seekable (Cristian Marussi)
- firmware: arm_scmi: Fix wrong fastchannel initialization (Pierre Gondois)
- arm64: dts: imx8qm-ss-dma: fix can lpcg indices (Frank Li)
- arm64: dts: imx8-ss-dma: fix can lpcg indices (Frank Li)
- arm64: dts: imx8-ss-dma: fix adc lpcg indices (Frank Li)
- arm64: dts: imx8-ss-dma: fix pwm lpcg indices (Frank Li)
- arm64: dts: imx8-ss-dma: fix spi lpcg indices (Frank Li)
- arm64: dts: imx8-ss-conn: fix usb lpcg indices (Frank Li)
- arm64: dts: imx8-ss-lsio: fix pwm lpcg indices (Frank Li)
- ARM: dts: imx7s-warp: Pass OV2680 link-frequencies (Fabio Estevam)
- ARM: dts: imx7-mba7: Use 'no-mmc' property (Fabio Estevam)
- arm64: dts: imx8-ss-conn: fix usdhc wrong lpcg clock order (Frank Li)
- arm64: dts: freescale: imx8mp-venice-gw73xx-2x: fix USB vbus regulator (Tim Harvey)
- arm64: dts: freescale: imx8mp-venice-gw72xx-2x: fix USB vbus regulator (Tim Harvey)
- ARM: OMAP2+: fix USB regression on Nokia N8x0 (Aaro Koskinen)
- mmc: omap: restore original power up/down steps (Aaro Koskinen)
- mmc: omap: fix deferred probe (Aaro Koskinen)
- mmc: omap: fix broken slot switch lookup (Aaro Koskinen)
- ARM: OMAP2+: fix N810 MMC gpiod table (Aaro Koskinen)
- ARM: OMAP2+: fix bogus MMC GPIO labels on Nokia N8x0 (Aaro Koskinen)
- iommu/amd: Change log message severity (Vasant Hegde)
- iommu/vt-d: Fix WARN_ON in iommu probe path (Lu Baolu)
- iommu/vt-d: Allocate local memory for page request queue (Jacob Pan)
- iommu/vt-d: Fix wrong use of pasid config (Xuchun Shang)
- iommu: mtk: fix module autoloading (Krzysztof Kozlowski)
- iommu/amd: Do not enable SNP when V2 page table is enabled (Vasant Hegde)
- iommu/amd: Fix possible irq lock inversion dependency issue (Vasant Hegde)
- Revert "PCI: Mark LSI FW643 to avoid bus reset" (Bjorn Helgaas)
- MAINTAINERS: Drop Gustavo Pimentel as PCI DWC Maintainer (Manivannan Sadhasivam)
- block: fix that blk_time_get_ns() doesn't update time after schedule (Yu Kuai)
- raid1: fix use-after-free for original bio in raid1_write_request() (Yu Kuai)
- block: allow device to have both virt_boundary_mask and max segment size (Ming Lei)
- block: fix q->blkg_list corruption during disk rebind (Ming Lei)
- blk-iocost: avoid out of bounds shift (Rik van Riel)
- io-uring: correct typo in comment for IOU_F_TWQ_LAZY_WAKE (Haiyue Wang)
- io_uring/net: restore msg_control on sendzc retry (Pavel Begunkov)
- io_uring: Fix io_cqring_wait() not restoring sigmask on get_timespec64() failure (Alexey Izbyshev)
- MAINTAINERS: remove myself as a Reviewer for Ceph (Jeff Layton)
- ceph: switch to use cap_delay_lock for the unlink delay list (Xiubo Li)
- ceph: redirty page before returning AOP_WRITEPAGE_ACTIVATE (NeilBrown)
- Kconfig: add some hidden tabs on purpose (Linus Torvalds)
- ring-buffer: Only update pages_touched when a new page is touched (Steven Rostedt (Google))
- tracing: hide unused ftrace_event_id_fops (Arnd Bergmann)
- tracing: Fix FTRACE_RECORD_RECURSION_SIZE Kconfig entry (Prasad Pandit)
- eventfs: Fix kernel-doc comments to functions (Yang Li)
- MIPS: scall: Save thread_info.syscall unconditionally on entry (Jiaxun Yang)
- amdkfd: use calloc instead of kzalloc to avoid integer overflow (Dave Airlie)
- drm/msm/adreno: Set highest_bank_bit for A619 (Luca Weiss)
- drm/msm: fix the `CRASHDUMP_READ` target of `a6xx_get_shader_block()` (Miguel Ojeda)
- dt-bindings: display/msm: sm8150-mdss: add DP node (Dmitry Baryshkov)
- drm/msm/dp: fix typo in dp_display_handle_port_status_changed() (Abhinav Kumar)
- drm/msm/dpu: make error messages at dpu_core_irq_register_callback() more sensible (Dmitry Baryshkov)
- drm/msm/dp: assign correct DP controller ID to x1e80100 interface table (Kuogee Hsieh)
- drm/msm/dpu: don't allow overriding data from catalog (Dmitry Baryshkov)
- drm/msm: Add newlines to some debug prints (Stephen Boyd)
- drm/msm/dp: fix runtime PM leak on connect failure (Johan Hovold)
- drm/msm/dp: fix runtime PM leak on disconnect (Johan Hovold)
- drm/xe: Label RING_CONTEXT_CONTROL as masked (Ashutosh Dixit)
- drm/xe/xe_migrate: Cast to output precision before multiplying operands (Himal Prasad Ghimiray)
- drm/xe/hwmon: Cast result to output precision on left shift of operand (Karthik Poosa)
- drm/xe/display: Fix double mutex initialization (Lucas De Marchi)
- drm/vmwgfx: Enable DMA mappings with SEV (Zack Rusin)
- drm/client: Fully protect modes[] with dev->mode_config.mutex (Ville Syrjälä)
- gpu: host1x: Do not setup DMA for virtual devices (Thierry Reding)
- accel/ivpu: Fix deadlock in context_xa (Jacek Lawrynowicz)
- accel/ivpu: Fix missed error message after VPU rename (Jacek Lawrynowicz)
- accel/ivpu: Return max freq for DRM_IVPU_PARAM_CORE_CLOCK_RATE (Jacek Lawrynowicz)
- accel/ivpu: Improve clarity of MMU error messages (Wachowski, Karol)
- accel/ivpu: Put NPU back to D3hot after failed resume (Jacek Lawrynowicz)
- accel/ivpu: Fix PCI D0 state entry in resume (Wachowski, Karol)
- accel/ivpu: Remove d3hot_after_power_off WA (Jacek Lawrynowicz)
- accel/ivpu: Check return code of ipc->lock init (Wachowski, Karol)
- nouveau: fix function cast warning (Arnd Bergmann)
- nouveau/gsp: Avoid addressing beyond end of rpc->entries (Kees Cook)
- Revert "drm/qxl: simplify qxl_fence_wait" (Alex Constantino)
- drm/ast: Fix soft lockup (Jammy Huang)
- drm/panfrost: Fix the error path in panfrost_mmu_map_fault_addr() (Boris Brezillon)
- drm/amdgpu: differentiate external rev id for gfx 11.5.0 (Yifan Zhang)
- drm/amd/display: Adjust dprefclk by down spread percentage. (Zhongwei)
- drm/amd/display: Set VSC SDP Colorimetry same way for MST and SST (Harry Wentland)
- drm/amd/display: Program VSC SDP colorimetry for all DP sinks >= 1.4 (Harry Wentland)
- drm/amd/display: fix disable otg wa logic in DCN316 (Fudongwang)
- drm/amd/display: Do not recursively call manual trigger programming (Dillon Varone)
- drm/amd/display: always reset ODM mode in context when adding first plane (Wenjing Liu)
- drm/amdgpu: fix incorrect number of active RBs for gfx11 (Tim Huang)
- drm/amd/display: Return max resolution supported by DWB (Alex Hung)
- amd/amdkfd: sync all devices to wait all processes being evicted (Zhigang Luo)
- drm/amdgpu: clear set_q_mode_offs when VM changed (ZhenGuo Yin)
- drm/amdgpu: Fix VCN allocation in CPX partition (Lijo Lazar)
- drm/amd/pm: fix the high voltage issue after unload (Kenneth Feng)
- drm/amd/display: Skip on writeback when it's not applicable (Alex Hung)
- drm/amdgpu: implement IRQ_STATE_ENABLE for SDMA v4.4.2 (Tao Zhou)
- drm/amdgpu: add smu 14.0.1 discovery support (Yifan Zhang)
- drm/amd/swsmu: Update smu v14.0.0 headers to be 14.0.1 compatible (lima1002)
- drm/amdgpu : Increase the mes log buffer size as per new MES FW version (shaoyunl)
- drm/amdgpu : Add mes_log_enable to control mes log feature (shaoyunl)
- drm/amd/pm: fixes a random hang in S4 for SMU v13.0.4/11 (Tim Huang)
- drm/amd/display: add DCN 351 version for microcode load (Li Ma)
- drm/amdgpu: Reset dGPU if suspend got aborted (Lijo Lazar)
- drm/amdgpu/umsch: reinitialize write pointer in hw init (Lang Yu)
- drm/amdgpu: Refine IB schedule error logging (Lijo Lazar)
- drm/amdgpu: always force full reset for SOC21 (Alex Deucher)
- drm/amdkfd: Reset GPU on queue preemption failure (Harish Kasiviswanathan)
- drm/i915/vrr: Disable VRR when using bigjoiner (Ville Syrjälä)
- drm/i915: Disable live M/N updates when using bigjoiner (Ville Syrjälä)
- drm/i915: Disable port sync when bigjoiner is used (Ville Syrjälä)
- drm/i915/psr: Disable PSR when bigjoiner is used (Ville Syrjälä)
- drm/i915/guc: Fix the fix for reset lock confusion (John Harrison)
- drm/i915/hdcp: Fix get remote hdcp capability function (Suraj Kandpal)
- drm/i915/cdclk: Fix voltage_level programming edge case (Ville Syrjälä)
- drm/i915/cdclk: Fix CDCLK programming order when pipes are active (Ville Syrjälä)
- docs: point out that python3-pyyaml is now required (Thorsten Leemhuis)
- cxl: Add checks to access_coordinate calculation to fail missing data (Dave Jiang)
- cxl: Consolidate dport access_coordinate ->hb_coord and ->sw_coord into ->coord (Dave Jiang)
- cxl: Fix incorrect region perf data calculation (Dave Jiang)
- cxl: Fix retrieving of access_coordinates in PCIe path (Dave Jiang)
- cxl: Remove checking of iter in cxl_endpoint_get_perf_coordinates() (Dave Jiang)
- cxl/core: Fix initialization of mbox_cmd.size_out in get event (Kwangjin Ko)
- cxl/core/regs: Fix usage of map->reg_type in cxl_decode_regblock() before assigned (Dave Jiang)
- cxl/mem: Fix for the index of Clear Event Record Handle (Yuquan Wang)
- Drivers: hv: vmbus: Don't free ring buffers that couldn't be re-encrypted (Michael Kelley)
- uio_hv_generic: Don't free decrypted memory (Rick Edgecombe)
- hv_netvsc: Don't free decrypted memory (Rick Edgecombe)
- Drivers: hv: vmbus: Track decrypted status in vmbus_gpadl (Rick Edgecombe)
- Drivers: hv: vmbus: Leak pages if set_memory_encrypted() fails (Rick Edgecombe)
- hv/hv_kvp_daemon: Handle IPv4 and Ipv6 combination for keyfile format (Shradha Gupta)
- hv: vmbus: Convert sprintf() family to sysfs_emit() family (Li Zhijian)
- mshyperv: Introduce hv_numa_node_to_pxm_info() (Nuno Das Neves)
- x86/hyperv: Cosmetic changes for hv_apic.c (Erni Sri Satya Vennela)
- ACPI: bus: allow _UID matching for integer zero (Raag Jadav)
- ACPI: scan: Do not increase dep_unmet for already met dependencies (Hans de Goede)
- PM: s2idle: Make sure CPUs will wakeup directly on resume (Anna-Maria Behnsen)
- net: ena: Set tx_info->xdpf value to NULL (David Arinzon)
- net: ena: Fix incorrect descriptor free behavior (David Arinzon)
- net: ena: Wrong missing IO completions check order (David Arinzon)
- net: ena: Fix potential sign extension issue (David Arinzon)
- Bluetooth: l2cap: Don't double set the HCI_CONN_MGMT_CONNECTED bit (Archie Pusaka)
- Bluetooth: hci_sock: Fix not validating setsockopt user input (Luiz Augusto von Dentz)
- Bluetooth: ISO: Fix not validating setsockopt user input (Luiz Augusto von Dentz)
- Bluetooth: L2CAP: Fix not validating setsockopt user input (Luiz Augusto von Dentz)
- Bluetooth: RFCOMM: Fix not validating setsockopt user input (Luiz Augusto von Dentz)
- Bluetooth: SCO: Fix not validating setsockopt user input (Luiz Augusto von Dentz)
- Bluetooth: Fix memory leak in hci_req_sync_complete() (Dmitry Antipov)
- Bluetooth: hci_sync: Fix using the same interval and window for Coded PHY (Luiz Augusto von Dentz)
- Bluetooth: ISO: Don't reject BT_ISO_QOS if parameters are unset (Luiz Augusto von Dentz)
- af_unix: Fix garbage collector racing against connect() (Michal Luczaj)
- net: dsa: mt7530: trap link-local frames regardless of ST Port State (Arınç ÜNAL)
- Revert "s390/ism: fix receive message buffer allocation" (Gerd Bayer)
- net: sparx5: fix wrong config being used when reconfiguring PCS (Daniel Machon)
- net/mlx5: fix possible stack overflows (Arnd Bergmann)
- net/mlx5: Disallow SRIOV switchdev mode when in multi-PF netdev (Tariq Toukan)
- net/mlx5e: RSS, Block XOR hash with over 128 channels (Carolina Jubran)
- net/mlx5e: Do not produce metadata freelist entries in Tx port ts WQE xmit (Rahul Rameshbabu)
- net/mlx5e: HTB, Fix inconsistencies with QoS SQs number (Carolina Jubran)
- net/mlx5e: Fix mlx5e_priv_init() cleanup flow (Carolina Jubran)
- net/mlx5e: RSS, Block changing channels number when RXFH is configured (Carolina Jubran)
- net/mlx5: Correctly compare pkt reformat ids (Cosmin Ratiu)
- net/mlx5: Properly link new fs rules into the tree (Cosmin Ratiu)
- net/mlx5: offset comp irq index in name by one (Michael Liang)
- net/mlx5: Register devlink first under devlink lock (Shay Drory)
- net/mlx5: E-switch, store eswitch pointer before registering devlink_param (Shay Drory)
- netfilter: complete validation of user input (Eric Dumazet)
- r8169: add missing conditional compiling for call to r8169_remove_leds (Heiner Kallweit)
- net: dsa: mt7530: fix enabling EEE on MT7531 switch on all boards (Arınç ÜNAL)
- r8169: fix LED-related deadlock on module removal (Heiner Kallweit)
- pds_core: Fix pdsc_check_pci_health function to use work thread (Brett Creeley)
- ipv6: fix race condition between ipv6_get_ifaddr and ipv6_del_addr (Jiri Benc)
- nfc: llcp: fix nfc_llcp_setsockopt() unsafe copies (Eric Dumazet)
- mISDN: fix MISDN_TIME_STAMP handling (Eric Dumazet)
- net: add copy_safe_from_sockptr() helper (Eric Dumazet)
- ipv4/route: avoid unused-but-set-variable warning (Arnd Bergmann)
- ipv6: fib: hide unused 'pn' variable (Arnd Bergmann)
- octeontx2-af: Fix NIX SQ mode and BP config (Geetha sowjanya)
- af_unix: Clear stale u->oob_skb. (Kuniyuki Iwashima)
- net: ks8851: Handle softirqs at the end of IRQ thread to fix hang (Marek Vasut)
- net: ks8851: Inline ks8851_rx_skb() (Marek Vasut)
- net: stmmac: mmc_core: Add GMAC mmc tx/rx missing statistics (Minda Chen)
- net: stmmac: mmc_core: Add GMAC LPI statistics (Minda Chen)
- bnxt_en: Reset PTP tx_avail after possible firmware reset (Pavan Chebbi)
- bnxt_en: Fix error recovery for RoCE ulp client (Vikas Gupta)
- bnxt_en: Fix possible memory leak in bnxt_rdma_aux_device_init() (Vikas Gupta)
- s390/ism: fix receive message buffer allocation (Gerd Bayer)
- geneve: fix header validation in geneve[6]_xmit_skb (Eric Dumazet)
- MAINTAINERS: Drop Li Yang as their email address stopped working (Uwe Kleine-König)
- batman-adv: Avoid infinite loop trying to resize local TT (Sven Eckelmann)
- lib: checksum: hide unused expected_csum_ipv6_magic[] (Arnd Bergmann)
- octeontx2-pf: Fix transmit scheduler resource leak (Hariprasad Kelam)
- virtio_net: Do not send RSS key if it is not supported (Breno Leitao)
- xsk: validate user input for XDP_{UMEM|COMPLETION}_FILL_RING (Eric Dumazet)
- u64_stats: fix u64_stats_init() for lockdep when used repeatedly in one file (Petr Tesarik)
- net: openvswitch: fix unwanted error log on timeout policy probing (Ilya Maximets)
- scsi: qla2xxx: Fix off by one in qla_edif_app_getstats() (Dan Carpenter)
- scsi: hisi_sas: Modify the deadline for ata_wait_after_reset() (Xiang Chen)
- scsi: hisi_sas: Handle the NCQ error returned by D2H frame (Xiang Chen)
- scsi: target: Fix SELinux error when systemd-modules loads the target module (Maurizio Lombardi)
- scsi: sg: Avoid race in error handling & drop bogus warn (Alexander Wetzel)
- LoongArch: Include linux/sizes.h in addrspace.h to prevent build errors (Randy Dunlap)
- LoongArch: Update dts for Loongson-2K2000 to support GMAC/GNET (Huacai Chen)
- LoongArch: Update dts for Loongson-2K2000 to support PCI-MSI (Huacai Chen)
- LoongArch: Update dts for Loongson-2K2000 to support ISA/LPC (Huacai Chen)
- LoongArch: Update dts for Loongson-2K1000 to support ISA/LPC (Huacai Chen)
- LoongArch: Make virt_addr_valid()/__virt_addr_valid() work with KFENCE (Huacai Chen)
- LoongArch: Make {virt, phys, page, pfn} translation work with KFENCE (Huacai Chen)
- mm: Move lowmem_page_address() a little later (Huacai Chen)
- bcachefs: Fix __bch2_btree_and_journal_iter_init_node_iter() (Kent Overstreet)
- bcachefs: Kill read lock dropping in bch2_btree_node_lock_write_nofail() (Kent Overstreet)
- bcachefs: Fix a race in btree_update_nodes_written() (Kent Overstreet)
- bcachefs: btree_node_scan: Respect member.data_allowed (Kent Overstreet)
- bcachefs: Don't scan for btree nodes when we can reconstruct (Kent Overstreet)
- bcachefs: Fix check_topology() when using node scan (Kent Overstreet)
- bcachefs: fix eytzinger0_find_gt() (Kent Overstreet)
- bcachefs: fix bch2_get_acl() transaction restart handling (Kent Overstreet)
- bcachefs: fix the count of nr_freed_pcpu after changing bc->freed_nonpcpu list (Hongbo Li)
- bcachefs: Fix gap buffer bug in bch2_journal_key_insert_take() (Kent Overstreet)
- bcachefs: Rename struct field swap to prevent macro naming collision (Thorsten Blum)
- MAINTAINERS: Add entry for bcachefs documentation (Bagas Sanjaya)
- Documentation: filesystems: Add bcachefs toctree (Bagas Sanjaya)
- bcachefs: JOURNAL_SPACE_LOW (Kent Overstreet)
- bcachefs: Disable errors=panic for BCH_IOCTL_FSCK_OFFLINE (Kent Overstreet)
- bcachefs: Fix BCH_IOCTL_FSCK_OFFLINE for encrypted filesystems (Kent Overstreet)
- bcachefs: fix rand_delete unit test (Kent Overstreet)
- bcachefs: fix ! vs ~ typo in __clear_bit_le64() (Dan Carpenter)
- bcachefs: Fix rebalance from durability=0 device (Kent Overstreet)
- bcachefs: Print shutdown journal sequence number (Kent Overstreet)
- bcachefs: Further improve btree_update_to_text() (Kent Overstreet)
- bcachefs: Move btree_updates to debugfs (Kent Overstreet)
- bcachefs: Bump limit in btree_trans_too_many_iters() (Kent Overstreet)
- bcachefs: Make snapshot_is_ancestor() safe (Kent Overstreet)
- bcachefs: create debugfs dir for each btree (Thomas Bertschinger)
- platform/chrome: cros_ec_uart: properly fix race condition (Noah Loomans)
- Use LLVM=1 for clang_lto build (Nikita Popov)
- redhat: fix def_variants.yaml check (Jan Stancek)
- kprobes: Fix possible use-after-free issue on kprobe registration (Zheng Yejian)
- fs/proc: Skip bootloader comment if no embedded kernel parameters (Masami Hiramatsu)
- fs/proc: remove redundant comments from /proc/bootconfig (Zhenhua Huang)
- media: mediatek: vcodec: support 36 bits physical address (Yunfei Dong)
- media: mediatek: vcodec: adding lock to protect encoder context list (Yunfei Dong)
- media: mediatek: vcodec: adding lock to protect decoder context list (Yunfei Dong)
- media: mediatek: vcodec: Fix oops when HEVC init fails (Nicolas Dufresne)
- media: mediatek: vcodec: Handle VP9 superframe bitstream with 8 sub-frames (Irui Wang)
- randomize_kstack: Improve entropy diffusion (Kees Cook)
- ubsan: fix unused variable warning in test module (Arnd Bergmann)
- gcc-plugins/stackleak: Avoid .head.text section (Ard Biesheuvel)
- tools/power turbostat: v2024.04.10 (Len Brown)
- tools/power/turbostat: Add support for Xe sysfs knobs (Zhang Rui)
- tools/power/turbostat: Add support for new i915 sysfs knobs (Zhang Rui)
- tools/power/turbostat: Introduce BIC_SAM_mc6/BIC_SAMMHz/BIC_SAMACTMHz (Zhang Rui)
- tools/power/turbostat: Fix uncore frequency file string (Justin Ernst)
- tools/power/turbostat: Unify graphics sysfs snapshots (Zhang Rui)
- tools/power/turbostat: Cache graphics sysfs path (Zhang Rui)
- tools/power/turbostat: Enable MSR_CORE_C1_RES support for ICX (Zhang Rui)
- tools/power turbostat: Add selftests (Patryk Wlazlyn)
- tools/power turbostat: read RAPL counters via perf (Patryk Wlazlyn)
- tools/power turbostat: Add proper re-initialization for perf file descriptors (Patryk Wlazlyn)
- tools/power turbostat: Clear added counters when in no-msr mode (Patryk Wlazlyn)
- tools/power turbostat: add early exits for permission checks (Patryk Wlazlyn)
- tools/power turbostat: detect and disable unavailable BICs at runtime (Patryk Wlazlyn)
- tools/power turbostat: Add reading aperf and mperf via perf API (Patryk Wlazlyn)
- tools/power turbostat: Add --no-perf option (Patryk Wlazlyn)
- tools/power turbostat: Add --no-msr option (Patryk Wlazlyn)
- tools/power turbostat: enhance -D (debug counter dump) output (Len Brown)
- tools/power turbostat: Fix warning upon failed /dev/cpu_dma_latency read (Len Brown)
- tools/power turbostat: Read base_hz and bclk from CPUID.16H if available (Patryk Wlazlyn)
- tools/power turbostat: Print ucode revision only if valid (Patryk Wlazlyn)
- tools/power turbostat: Expand probe_intel_uncore_frequency() (Len Brown)
- tools/power turbostat: Do not print negative LPI residency (Chen Yu)
- tools/power turbostat: Fix Bzy_MHz documentation typo (Peng Liu)
- tools/power turbostat: Increase the limit for fd opened (Wyes Karny)
- tools/power turbostat: Fix added raw MSR output (Doug Smythies)
- platform/x86: lg-laptop: fix %%s null argument warning (Gergo Koteles)
- platform/x86: intel-vbtn: Update tablet mode switch at end of probe (Gwendal Grignou)
- platform/x86: intel-vbtn: Use acpi_has_method to check for switch (Gwendal Grignou)
- platform/x86: toshiba_acpi: Silence logging for some events (Hans de Goede)
- platform/x86/intel/hid: Add Lunar Lake and Arrow Lake support (Sumeet Pawnikar)
- platform/x86/intel/hid: Don't wake on 5-button releases (David McFarland)
- platform/x86: acer-wmi: Add support for Acer PH18-71 (Bernhard Rosenkränzer)
- redhat: sanity check yaml files (Jan Stancek)
- spec: rework filter-mods and mod-denylist (Jan Stancek)
- nouveau: fix devinit paths to only handle display on GSP. (Dave Airlie)
- compiler.h: Add missing quote in macro comment (Thorsten Blum)
- KVM: x86: Add BHI_NO (Daniel Sneddon)
- x86/bhi: Mitigate KVM by default (Pawan Gupta)
- x86/bhi: Add BHI mitigation knob (Pawan Gupta)
- x86/bhi: Enumerate Branch History Injection (BHI) bug (Pawan Gupta)
- x86/bhi: Define SPEC_CTRL_BHI_DIS_S (Daniel Sneddon)
- x86/bhi: Add support for clearing branch history at syscall entry (Pawan Gupta)
- x86/syscall: Don't force use of indirect calls for system calls (Linus Torvalds)
- x86/bugs: Change commas to semicolons in 'spectre_v2' sysfs file (Josh Poimboeuf)
- btrfs: always clear PERTRANS metadata during commit (Boris Burkov)
- btrfs: make btrfs_clear_delalloc_extent() free delalloc reserve (Boris Burkov)
- btrfs: qgroup: convert PREALLOC to PERTRANS after record_root_in_trans (Boris Burkov)
- btrfs: record delayed inode root in transaction (Boris Burkov)
- btrfs: qgroup: fix qgroup prealloc rsv leak in subvolume operations (Boris Burkov)
- btrfs: qgroup: correctly model root qgroup rsv in convert (Boris Burkov)
- memblock tests: fix undefined reference to `BIT' (Wei Yang)
- memblock tests: fix undefined reference to `panic' (Wei Yang)
- memblock tests: fix undefined reference to `early_pfn_to_nid' (Wei Yang)
- Linux 6.9-rc3 (Linus Torvalds)
- x86/retpoline: Add NOENDBR annotation to the SRSO dummy return thunk (Borislav Petkov (AMD))
- x86/mce: Make sure to grab mce_sysfs_mutex in set_bank() (Borislav Petkov (AMD))
- x86/CPU/AMD: Track SNP host status with cc_platform_*() (Borislav Petkov (AMD))
- x86/cc: Add cc_platform_set/_clear() helpers (Borislav Petkov (AMD))
- x86/kvm/Kconfig: Have KVM_AMD_SEV select ARCH_HAS_CC_PLATFORM (Borislav Petkov (AMD))
- x86/coco: Require seeding RNG with RDRAND on CoCo systems (Jason A. Donenfeld)
- x86/numa/32: Include missing <asm/pgtable_areas.h> (Arnd Bergmann)
- x86/resctrl: Fix uninitialized memory read when last CPU of domain goes offline (Reinette Chatre)
- timers/migration: Return early on deactivation (Anna-Maria Behnsen)
- timers/migration: Fix ignored event due to missing CPU update (Frederic Weisbecker)
- vdso: Use CONFIG_PAGE_SHIFT in vdso/datapage.h (Arnd Bergmann)
- timers: Fix text inconsistencies and spelling (Randy Dunlap)
- tick/sched: Fix struct tick_sched doc warnings (Randy Dunlap)
- tick/sched: Fix various kernel-doc warnings (Randy Dunlap)
- timers: Fix kernel-doc format and add Return values (Randy Dunlap)
- time/timekeeping: Fix kernel-doc warnings and typos (Randy Dunlap)
- time/timecounter: Fix inline documentation (Randy Dunlap)
- perf/x86/intel/ds: Don't clear ->pebs_data_cfg for the last PEBS event (Kan Liang)
- redhat: regenerate test-data (Jan Stancek) [RHEL-29722]
- redhat/Makefile.variables: don't set DISTRO (Jan Stancek) [RHEL-29722]
- redhat/Makefile.variables: set PATCHLIST_URL to none (Jan Stancek) [RHEL-29722]
- redhat/kernel.spec.template: fix with_realtime (Jan Stancek) [RHEL-29722]
- Linux v6.9.0-0.rc4

* Mon Apr 08 2024 Jan Stancek <jstancek@redhat.com> [6.9.0-0.rc2.1.el10]
- remove ARK .gitlab-ci.yml (Jan Stancek)
- redhat: update rpminspect with c9s one (Jan Stancek)
- redhat: remove fedora configs and files (Jan Stancek)
- redhat: init RHEL10.0 beta variables and dist tag (Jan Stancek) [RHEL-29722]
- nfsd: hold a lighter-weight client reference over CB_RECALL_ANY (Jeff Layton)
- SUNRPC: Fix a slow server-side memory leak with RPC-over-TCP (Chuck Lever)
- i2c: pxa: hide unused icr_bits[] variable (Arnd Bergmann)
- xfs: allow cross-linking special files without project quota (Andrey Albershteyn)
- smb: client: fix potential UAF in cifs_signal_cifsd_for_reconnect() (Paulo Alcantara)
- smb: client: fix potential UAF in smb2_is_network_name_deleted() (Paulo Alcantara)
- smb: client: fix potential UAF in is_valid_oplock_break() (Paulo Alcantara)
- smb: client: fix potential UAF in smb2_is_valid_oplock_break() (Paulo Alcantara)
- smb: client: fix potential UAF in smb2_is_valid_lease_break() (Paulo Alcantara)
- smb: client: fix potential UAF in cifs_stats_proc_show() (Paulo Alcantara)
- smb: client: fix potential UAF in cifs_stats_proc_write() (Paulo Alcantara)
- smb: client: fix potential UAF in cifs_dump_full_key() (Paulo Alcantara)
- smb: client: fix potential UAF in cifs_debug_files_proc_show() (Paulo Alcantara)
- smb3: retrying on failed server close (Ritvik Budhiraja)
- smb: client: serialise cifs_construct_tcon() with cifs_mount_mutex (Paulo Alcantara)
- smb: client: handle DFS tcons in cifs_construct_tcon() (Paulo Alcantara)
- smb: client: refresh referral without acquiring refpath_lock (Paulo Alcantara)
- smb: client: guarantee refcounted children from parent session (Paulo Alcantara)
- cifs: Fix caching to try to do open O_WRONLY as rdwr on server (David Howells)
- smb: client: fix UAF in smb2_reconnect_server() (Paulo Alcantara)
- smb: client: replace deprecated strncpy with strscpy (Justin Stitt)
- firewire: ohci: mask bus reset interrupts between ISR and bottom half (Adam Goldman)
- spi: mchp-pci1xxx: Fix a possible null pointer dereference in pci1xxx_spi_probe (Huai-Yuan Liu)
- spi: spi-fsl-lpspi: remove redundant spi_controller_put call (Carlos Song)
- spi: s3c64xx: Use DMA mode from fifo size (Jaewon Kim)
- regulator: tps65132: Add of_match table (André Apitzsch)
- regmap: maple: Fix uninitialized symbol 'ret' warnings (Richard Fitzgerald)
- regmap: maple: Fix cache corruption in regcache_maple_drop() (Richard Fitzgerald)
- nvme-fc: rename free_ctrl callback to match name pattern (Daniel Wagner)
- nvmet-fc: move RCU read lock to nvmet_fc_assoc_exists (Daniel Wagner)
- nvmet: implement unique discovery NQN (Hannes Reinecke)
- nvme: don't create a multipath node for zero capacity devices (Christoph Hellwig)
- nvme: split nvme_update_zone_info (Christoph Hellwig)
- nvme-multipath: don't inherit LBA-related fields for the multipath node (Christoph Hellwig)
- block: fix overflow in blk_ioctl_discard() (Li Nan)
- nullblk: Fix cleanup order in null_add_dev() error path (Damien Le Moal)
- io_uring/kbuf: hold io_buffer_list reference over mmap (Jens Axboe)
- io_uring/kbuf: protect io_buffer_list teardown with a reference (Jens Axboe)
- io_uring/kbuf: get rid of bl->is_ready (Jens Axboe)
- io_uring/kbuf: get rid of lower BGID lists (Jens Axboe)
- io_uring: use private workqueue for exit work (Jens Axboe)
- io_uring: disable io-wq execution of multishot NOWAIT requests (Jens Axboe)
- io_uring/rw: don't allow multishot reads without NOWAIT support (Jens Axboe)
- scsi: ufs: core: Fix MCQ mode dev command timeout (Peter Wang)
- scsi: libsas: Align SMP request allocation to ARCH_DMA_MINALIGN (Yihang Li)
- scsi: sd: Unregister device if device_add_disk() failed in sd_probe() (Li Nan)
- scsi: ufs: core: WLUN suspend dev/link state error recovery (Peter Wang)
- scsi: mylex: Fix sysfs buffer lengths (Arnd Bergmann)
- nios2: Only use built-in devicetree blob if configured to do so (Guenter Roeck)
- dt-bindings: timer: narrow regex for unit address to hex numbers (Krzysztof Kozlowski)
- dt-bindings: soc: fsl: narrow regex for unit address to hex numbers (Krzysztof Kozlowski)
- dt-bindings: remoteproc: ti,davinci: remove unstable remark (Krzysztof Kozlowski)
- dt-bindings: clock: ti: remove unstable remark (Krzysztof Kozlowski)
- dt-bindings: clock: keystone: remove unstable remark (Krzysztof Kozlowski)
- of: module: prevent NULL pointer dereference in vsnprintf() (Sergey Shtylyov)
- dt-bindings: ufs: qcom: document SM6125 UFS (Krzysztof Kozlowski)
- dt-bindings: ufs: qcom: document SC7180 UFS (Krzysztof Kozlowski)
- dt-bindings: ufs: qcom: document SC8180X UFS (Krzysztof Kozlowski)
- of: dynamic: Synchronize of_changeset_destroy() with the devlink removals (Herve Codina)
- driver core: Introduce device_link_wait_removal() (Herve Codina)
- docs: dt-bindings: add missing address/size-cells to example (Krzysztof Kozlowski)
- MAINTAINERS: Add TPM DT bindings to TPM maintainers (Rob Herring)
- stackdepot: rename pool_index to pool_index_plus_1 (Peter Collingbourne)
- x86/mm/pat: fix VM_PAT handling in COW mappings (David Hildenbrand)
- MAINTAINERS: change vmware.com addresses to broadcom.com (Alexey Makhalov)
- selftests/mm: include strings.h for ffsl (Edward Liaw)
- mm: vmalloc: fix lockdep warning (Uladzislau Rezki (Sony))
- mm: vmalloc: bail out early in find_vmap_area() if vmap is not init (Uladzislau Rezki (Sony))
- init: open output files from cpio unpacking with O_LARGEFILE (John Sperbeck)
- mm/secretmem: fix GUP-fast succeeding on secretmem folios (David Hildenbrand)
- arm64/ptrace: Use saved floating point state type to determine SVE layout (Mark Brown)
- riscv: process: Fix kernel gp leakage (Stefan O'Rear)
- riscv: Disable preemption when using patch_map() (Alexandre Ghiti)
- riscv: Fix warning by declaring arch_cpu_idle() as noinstr (Alexandre Ghiti)
- riscv: use KERN_INFO in do_trap (Andreas Schwab)
- riscv: Fix vector state restore in rt_sigreturn() (Björn Töpel)
- riscv: mm: implement pgprot_nx (Jisheng Zhang)
- riscv: compat_vdso: align VDSOAS build log (Masahiro Yamada)
- RISC-V: Update AT_VECTOR_SIZE_ARCH for new AT_MINSIGSTKSZ (Victor Isaev)
- riscv: Mark __se_sys_* functions __used (Sami Tolvanen)
- drivers/perf: riscv: Disable PERF_SAMPLE_BRANCH_* while not supported (Pu Lehui)
- riscv: compat_vdso: install compat_vdso.so.dbg to /lib/modules/*/vdso/ (Masahiro Yamada)
- riscv: hwprobe: do not produce frtace relocation (Vladimir Isaev)
- riscv: Fix spurious errors from __get/put_kernel_nofault (Samuel Holland)
- riscv: mm: Fix prototype to avoid discarding const (Samuel Holland)
- s390/entry: align system call table on 8 bytes (Sumanth Korikkar)
- s390/pai: fix sampling event removal for PMU device driver (Thomas Richter)
- s390/preempt: mark all functions __always_inline (Ilya Leoshkevich)
- s390/atomic: mark all functions __always_inline (Ilya Leoshkevich)
- s390/mm: fix NULL pointer dereference (Heiko Carstens)
- PM: EM: fix wrong utilization estimation in em_cpu_energy() (Vincent Guittot)
- ACPI: thermal: Register thermal zones without valid trip points (Stephen Horvath)
- thermal: gov_power_allocator: Allow binding without trip points (Nikita Travkin)
- thermal: gov_power_allocator: Allow binding without cooling devices (Nikita Travkin)
- gpio: cdev: fix missed label sanitizing in debounce_setup() (Kent Gibson)
- gpio: cdev: check for NULL labels when sanitizing them for irqs (Bartosz Golaszewski)
- gpiolib: Fix triggering "kobject: 'gpiochipX' is not initialized, yet" kobject_get() errors (Hans de Goede)
- ata: sata_gemini: Check clk_enable() result (Chen Ni)
- ata: sata_mv: Fix PCI device ID table declaration compilation warning (Arnd Bergmann)
- ata: ahci_st: Remove an unused field in struct st_ahci_drv_data (Christophe JAILLET)
- ata: pata_macio: drop driver owner assignment (Krzysztof Kozlowski)
- ata: sata_sx4: fix pdc20621_get_from_dimm() on 64-bit (Arnd Bergmann)
- ASoC: SOF: Core: Add remove_late() to sof_init_environment failure path (Chaitanya Kumar Borah)
- ASoC: SOF: amd: fix for false dsp interrupts (Vijendar Mukunda)
- ASoC: SOF: Intel: lnl: Disable DMIC/SSP offload on remove (Peter Ujfalusi)
- ASoC: wm_adsp: Fix missing mutex_lock in wm_adsp_write_ctl() (Richard Fitzgerald)
- ASoC: codecs: ES8326: Removing the control of ADC_SCALE (Zhang Yi)
- ASoC: codecs: ES8326: Solve a headphone detection issue after suspend and resume (Zhang Yi)
- ASoC: codecs: ES8326: modify clock table (Zhang Yi)
- ASoC: codecs: ES8326: Solve error interruption issue (Zhang Yi)
- ASoC: Intel: avs: boards: Add modules description (Amadeusz Sławiński)
- ASoC: amd: acp: fix for acp_init function error handling (Vijendar Mukunda)
- ASoC: rt-sdw*: add __func__ to all error logs (Pierre-Louis Bossart)
- ASoC: rt722-sdca-sdw: fix locking sequence (Pierre-Louis Bossart)
- ASoC: rt712-sdca-sdw: fix locking sequence (Pierre-Louis Bossart)
- ASoC: rt711-sdw: fix locking sequence (Pierre-Louis Bossart)
- ASoC: rt711-sdca: fix locking sequence (Pierre-Louis Bossart)
- ASoC: rt5682-sdw: fix locking sequence (Pierre-Louis Bossart)
- ASoC: ops: Fix wraparound for mask in snd_soc_get_volsw (Stephen Lee)
- ASoC: amd: acp: fix for acp pdm configuration check (Vijendar Mukunda)
- ASoC: SOF: Intel: hda: Compensate LLP in case it is not reset (Peter Ujfalusi)
- ALSA: hda: Add pplcllpl/u members to hdac_ext_stream (Peter Ujfalusi)
- ASoC: SOF: ipc4-pcm: Correct the delay calculation (Peter Ujfalusi)
- ASoC: SOF: sof-pcm: Add pointer callback to sof_ipc_pcm_ops (Peter Ujfalusi)
- ASoC: SOF: ipc4-pcm: Invalidate the stream_start_offset in PAUSED state (Peter Ujfalusi)
- ASoC: SOF: ipc4-pcm: Combine the SOF_IPC4_PIPE_PAUSED cases in pcm_trigger (Peter Ujfalusi)
- ASoC: SOF: ipc4-pcm: Move struct sof_ipc4_timestamp_info definition locally (Peter Ujfalusi)
- ASoC: SOF: Remove the get_stream_position callback (Peter Ujfalusi)
- ASoC: SOF: Intel: hda-common-ops: Do not set the get_stream_position callback (Peter Ujfalusi)
- ASoC: SOF: ipc4-pcm: Use the snd_sof_pcm_get_dai_frame_counter() for pcm_delay (Peter Ujfalusi)
- ASoC: SOF: Intel: Set the dai/host get frame/byte counter callbacks (Peter Ujfalusi)
- ASoC: SOF: Introduce a new callback pair to be used for PCM delay reporting (Peter Ujfalusi)
- ASoC: SOF: Intel: mtl/lnl: Use the generic get_stream_position callback (Peter Ujfalusi)
- ASoC: SOF: Intel: hda: Implement get_stream_position (Linear Link Position) (Peter Ujfalusi)
- ASoC: SOF: Intel: hda-pcm: Use dsp_max_burst_size_in_ms to place constraint (Peter Ujfalusi)
- ASoC: SOF: ipc4-topology: Save the DMA maximum burst size for PCMs (Peter Ujfalusi)
- ASoC: SOF: Add dsp_max_burst_size_in_ms member to snd_sof_pcm_stream (Peter Ujfalusi)
- ASoC: cs42l43: Correct extraction of data pointer in suspend/resume (Charles Keepax)
- ASoC: SOF: mtrace: rework mtrace timestamp setting (Rander Wang)
- ASoC: cs-amp-lib: Check for no firmware controls when writing calibration (Simon Trimmer)
- ASoC: SOF: Intel: hda-dsp: Skip IMR boot on ACE platforms in case of S3 suspend (Peter Ujfalusi)
- ALSA: line6: Zero-initialize message buffers (Takashi Iwai)
- ALSA: hda/realtek: cs35l41: Support ASUS ROG G634JYR (Luke D. Jones)
- ALSA: hda/realtek: Update Panasonic CF-SZ6 quirk to support headset with microphone (I Gede Agastya Darma Laksana)
- ALSA: hda/realtek: Add sound quirks for Lenovo Legion slim 7 16ARHA7 models (Christian Bendiksen)
- Revert "ALSA: emu10k1: fix synthesizer sample playback position and caching" (Oswald Buddenhagen)
- OSS: dmasound/paula: Mark driver struct with __refdata to prevent section mismatch (Uwe Kleine-König)
- ALSA: hda/realtek: Add quirks for ASUS Laptops using CS35L56 (Simon Trimmer)
- ASoC: tas2781: mark dvc_tlv with __maybe_unused (Gergo Koteles)
- ALSA: hda: cs35l56: Add ACPI device match tables (Simon Trimmer)
- ALSA: hda/realtek - Fix inactive headset mic jack (Christoffer Sandberg)
- drm/i915/mst: Reject FEC+MST on ICL (Ville Syrjälä)
- drm/i915/mst: Limit MST+DSC to TGL+ (Ville Syrjälä)
- drm/i915/dp: Fix the computation for compressed_bpp for DISPLAY < 13 (Ankit Nautiyal)
- drm/i915/gt: Enable only one CCS for compute workload (Andi Shyti)
- drm/i915/gt: Do not generate the command streamer for all the CCS (Andi Shyti)
- drm/i915/gt: Disable HW load balancing for CCS (Andi Shyti)
- drm/i915/gt: Limit the reserved VM space to only the platforms that need it (Andi Shyti)
- drm/i915/psr: Fix intel_psr2_sel_fetch_et_alignment usage (Jouni Högander)
- drm/i915/psr: Move writing early transport pipe src (Jouni Högander)
- drm/i915/psr: Calculate PIPE_SRCSZ_ERLY_TPT value (Jouni Högander)
- drm/i915/dp: Remove support for UHBR13.5 (Arun R Murthy)
- drm/i915/dp: Fix DSC state HW readout for SST connectors (Imre Deak)
- drm/xe: Use ordered wq for preempt fence waiting (Matthew Brost)
- drm/xe: Move vma rebinding to the drm_exec locking loop (Thomas Hellström)
- drm/xe: Make TLB invalidation fences unordered (Thomas Hellström)
- drm/xe: Rework rebinding (Thomas Hellström)
- drm/xe: Use ring ops TLB invalidation for rebinds (Thomas Hellström)
- drm/display: fix typo (Oleksandr Natalenko)
- drm/prime: Unbreak virtgpu dma-buf export (Rob Clark)
- nouveau/uvmm: fix addr/range calcs for remap operations (Dave Airlie)
- drm/nouveau/gr/gf100: Remove second semicolon (Colin Ian King)
- drm/panfrost: fix power transition timeout warnings (Christian Hewitt)
- 9p: remove SLAB_MEM_SPREAD flag usage (Chengming Zhou)
- 9p: Fix read/write debug statements to report server reply (Dominique Martinet)
- 9p/trans_fd: remove Excess kernel-doc comment (Randy Dunlap)
- ksmbd: do not set SMB2_GLOBAL_CAP_ENCRYPTION for SMB 3.1.1 (Namjae Jeon)
- ksmbd: validate payload size in ipc response (Namjae Jeon)
- ksmbd: don't send oplock break if rename fails (Namjae Jeon)
- aio: Fix null ptr deref in aio_complete() wakeup (Kent Overstreet)
- fs,block: yield devices early (Christian Brauner)
- block: count BLK_OPEN_RESTRICT_WRITES openers (Christian Brauner)
- block: handle BLK_OPEN_RESTRICT_WRITES correctly (Christian Brauner)
- redhat/configs: remove CONFIG_INTEL_MENLOW as it is obsolete. (David Arcari)
- redhat: enable changes to build rt variants (Clark Williams)
- Add localversion for -RT release (Thomas Gleixner)
- sysfs: Add /sys/kernel/realtime entry (Clark Williams)
- riscv: allow to enable RT (Jisheng Zhang)
- riscv: add PREEMPT_AUTO support (Jisheng Zhang)
- POWERPC: Allow to enable RT (Sebastian Andrzej Siewior)
- powerpc/stackprotector: work around stack-guard init from atomic (Sebastian Andrzej Siewior)
- powerpc/kvm: Disable in-kernel MPIC emulation for PREEMPT_RT (Bogdan Purcareata)
- powerpc/pseries: Select the generic memory allocator. (Sebastian Andrzej Siewior)
- powerpc/pseries/iommu: Use a locallock instead local_irq_save() (Sebastian Andrzej Siewior)
- powerpc: traps: Use PREEMPT_RT (Sebastian Andrzej Siewior)
- ARM64: Allow to enable RT (Sebastian Andrzej Siewior)
- ARM: Allow to enable RT (Sebastian Andrzej Siewior)
- ARM: vfp: Move sending signals outside of vfp_lock()ed section. (Sebastian Andrzej Siewior)
- ARM: vfp: Use vfp_lock() in vfp_support_entry(). (Sebastian Andrzej Siewior)
- ARM: vfp: Use vfp_lock() in vfp_sync_hwstate(). (Sebastian Andrzej Siewior)
- ARM: vfp: Provide vfp_lock() for VFP locking. (Sebastian Andrzej Siewior)
- arm: Disable FAST_GUP on PREEMPT_RT if HIGHPTE is also enabled. (Sebastian Andrzej Siewior)
- ARM: enable irq in translation/section permission fault handlers (Yadi.hu)
- arm: Disable jump-label on PREEMPT_RT. (Thomas Gleixner)
- sched: define TIF_ALLOW_RESCHED (Thomas Gleixner)
- Revert "drm/i915: Depend on !PREEMPT_RT." (Sebastian Andrzej Siewior)
- drm/i915/guc: Consider also RCU depth in busy loop. (Sebastian Andrzej Siewior)
- drm/i915: Drop the irqs_disabled() check (Sebastian Andrzej Siewior)
- drm/i915/gt: Use spin_lock_irq() instead of local_irq_disable() + spin_lock() (Sebastian Andrzej Siewior)
- drm/i915/gt: Queue and wait for the irq_work item. (Sebastian Andrzej Siewior)
- drm/i915: skip DRM_I915_LOW_LEVEL_TRACEPOINTS with NOTRACE (Sebastian Andrzej Siewior)
- drm/i915: Disable tracing points on PREEMPT_RT (Sebastian Andrzej Siewior)
- drm/i915: Don't check for atomic context on PREEMPT_RT (Sebastian Andrzej Siewior)
- drm/i915: Don't disable interrupts on PREEMPT_RT during atomic updates (Mike Galbraith)
- drm/i915: Use preempt_disable/enable_rt() where recommended (Mike Galbraith)
- printk: Avoid false positive lockdep report for legacy printing (John Ogness)
- printk: Provide threadprintk boot argument (John Ogness)
- printk: Add kthread for all legacy consoles (John Ogness)
- serial: 8250: Revert "drop lockdep annotation from serial8250_clear_IER()" (John Ogness)
- serial: 8250: Switch to nbcon console (John Ogness)
- printk: nbcon: Provide function to reacquire ownership (John Ogness)
- tty: sysfs: Add nbcon support for 'active' (John Ogness)
- proc: Add nbcon support for /proc/consoles (John Ogness)
- printk: nbcon: Show replay message on takeover (John Ogness)
- printk: Provide helper for message prepending (John Ogness)
- printk: nbcon: Start printing threads (John Ogness)
- printk: nbcon: Stop threads on shutdown/reboot (John Ogness)
- printk: nbcon: Add printer thread wakeups (Thomas Gleixner)
- printk: nbcon: Add context to console_is_usable() (John Ogness)
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
- printk: nbcon: Assign priority based on CPU state (John Ogness)
- printk: nbcon: Use nbcon consoles in console_flush_all() (John Ogness)
- printk: Track registered boot consoles (John Ogness)
- printk: nbcon: Provide function to flush using write_atomic() (Thomas Gleixner)
- printk: Add @flags argument for console_is_usable() (John Ogness)
- printk: Let console_is_usable() handle nbcon (John Ogness)
- printk: Make console_is_usable() available to nbcon (John Ogness)
- printk: nbcon: Do not rely on proxy headers (John Ogness)
- printk: nbcon: Implement processing in port->lock wrapper (John Ogness)
- serial: core: Provide low-level functions to lock port (John Ogness)
- printk: nbcon: Use driver synchronization while registering (John Ogness)
- printk: nbcon: Add callbacks to synchronize with driver (John Ogness)
- printk: nbcon: Add detailed doc for write_atomic() (John Ogness)
- printk: Check printk_deferred_enter()/_exit() usage (Sebastian Andrzej Siewior)
- printk: nbcon: Remove return value for write_atomic() (John Ogness)
- printk: Properly deal with nbcon consoles on seq init (John Ogness)
- printk: Add notation to console_srcu locking (John Ogness)
- time: Allow to preempt after a callback. (Sebastian Andrzej Siewior)
- softirq: Add function to preempt serving softirqs. (Sebastian Andrzej Siewior)
- sched/core: Provide a method to check if a task is PI-boosted. (Sebastian Andrzej Siewior)
- zram: Replace bit spinlocks with spinlock_t for PREEMPT_RT. (Mike Galbraith)
- softirq: Wake ktimers thread also in softirq. (Junxiao Chang)
- tick: Fix timer storm since introduction of timersd (Frederic Weisbecker)
- rcutorture: Also force sched priority to timersd on boosting test. (Frederic Weisbecker)
- softirq: Use a dedicated thread for timer wakeups. (Sebastian Andrzej Siewior)
- sched/rt: Don't try push tasks if there are none. (Sebastian Andrzej Siewior)
- x86: Enable RT also on 32bit (Sebastian Andrzej Siewior)
- x86: Allow to enable RT (Sebastian Andrzej Siewior)
- drm/ttm/tests: Let ttm_bo_test consider different ww_mutex implementation. (Sebastian Andrzej Siewior)
- Locking: Let PREEMPT_RT compile again with new rwsem asserts. (Sebastian Andrzej Siewior)
- perf: Split __perf_pending_irq() out of perf_pending_irq() (Sebastian Andrzej Siewior)
- perf: Remove perf_swevent_get_recursion_context() from perf_pending_task(). (Sebastian Andrzej Siewior)
- perf: Enqueue SIGTRAP always via task_work. (Sebastian Andrzej Siewior)
- perf: Move irq_work_queue() where the event is prepared. (Sebastian Andrzej Siewior)
- net: Rename rps_lock to backlog_lock. (Sebastian Andrzej Siewior)
- net: Use backlog-NAPI to clean up the defer_list. (Sebastian Andrzej Siewior)
- net: Allow to use SMP threads for backlog NAPI. (Sebastian Andrzej Siewior)
- net: Remove conditional threaded-NAPI wakeup based on task state. (Sebastian Andrzej Siewior)
- Linux v6.9.0-0.rc2


###
# The following Emacs magic makes C-c C-e use UTC dates.
# Local Variables:
# rpm-change-log-uses-utc: t
# End:
###
