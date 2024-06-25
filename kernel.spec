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
%define specrpmversion 6.10.0
%define specversion 6.10.0
%define patchversion 6.10
%define pkgrelease 0.rc5.12
%define kversion 6
%define tarfile_release 6.10.0-0.rc5.12.el10
# This is needed to do merge window version magic
%define patchlevel 10
# This allows pkg_release to have configurable %%{?dist} tag
%define specrelease 0.rc5.12%{?buildid}%{?dist}
# This defines the kabi tarball version
%define kabiversion 6.10.0-0.rc5.12.el10

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
        %{SOURCE22} -l "../filtermods-$KernelVer.log" sort -d $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.dep -c configs/def_variants.yaml $variants_param -o ..
        if [ $? -ne 0 ]; then
            echo "8< --- filtermods-$KernelVer.log ---"
            cat "../filtermods-$KernelVer.log"
            echo "--- filtermods-$KernelVer.log --- >8"

            echo "8< --- modules.dep ---"
            cat $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.dep
            echo "--- modules.dep --- >8"
            exit 1
        fi

        create_module_file_list "kernel" ../modules-core.list ../kernel${Variant:+-${Variant}}-modules-core.list 1
        create_module_file_list "kernel" ../modules.list ../kernel${Variant:+-${Variant}}-modules.list 0
        create_module_file_list "internal" ../modules-internal.list ../kernel${Variant:+-${Variant}}-modules-internal.list 0
        create_module_file_list "kernel" ../modules-extra.list ../kernel${Variant:+-${Variant}}-modules-extra.list 0
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
%{make} %{?_smp_mflags} ARCH=$Arch V=1 TARGETS="bpf mm net net/forwarding net/mptcp netfilter tc-testing memfd drivers/net/bonding iommu" SKIP_TARGETS="" $force_targets INSTALL_PATH=%{buildroot}%{_libexecdir}/kselftests VMLINUX_H="${RPM_VMLINUX_H}" install

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
* Tue Jun 25 2024 Jan Stancek <jstancek@redhat.com> [6.10.0-0.rc5.12.el10]
- redhat: kernel.spec: add missing sound/soc/sof/sof-audio.h to kernel-devel package (Jaroslav Kysela)
- Linux 6.10-rc5 (Linus Torvalds)
- i2c: ocores: set IACK bit after core is enabled (Grygorii Tertychnyi)
- dt-bindings: i2c: google,cros-ec-i2c-tunnel: correct path to i2c-controller schema (Krzysztof Kozlowski)
- dt-bindings: i2c: atmel,at91sam: correct path to i2c-controller schema (Krzysztof Kozlowski)
- docs: i2c: summary: be clearer with 'controller/target' and 'adapter/client' pairs (Wolfram Sang)
- docs: i2c: summary: document 'local' and 'remote' targets (Wolfram Sang)
- docs: i2c: summary: document use of inclusive language (Wolfram Sang)
- docs: i2c: summary: update speed mode description (Wolfram Sang)
- docs: i2c: summary: update I2C specification link (Wolfram Sang)
- docs: i2c: summary: start sentences consistently. (Wolfram Sang)
- i2c: Add nop fwnode operations (Sakari Ailus)
- cifs: Move the 'pid' from the subreq to the req (David Howells)
- cifs: Only pick a channel once per read request (David Howells)
- cifs: Defer read completion (David Howells)
- cifs: fix typo in module parameter enable_gcm_256 (Steve French)
- cifs: drop the incorrect assertion in cifs_swap_rw() (Barry Song)
- memblock: use numa_valid_node() helper to check for invalid node ID (Mike Rapoport (IBM))
- mips: fix compat_sys_lseek syscall (Arnd Bergmann)
- MIPS: mipsmtregs: Fix target register for MFTC0 (Jiaxun Yang)
- x86/resctrl: Don't try to free nonexistent RMIDs (Dave Martin)
- drm/vmwgfx: Fix missing HYPERVISOR_GUEST dependency (Alexey Makhalov)
- KVM: PPC: Book3S HV: Prevent UAF in kvm_spapr_tce_attach_iommu_group() (Michael Ellerman)
- powerpc/crypto: Add generated P8 asm to .gitignore (Nathan Lynch)
- rust: avoid unused import warning in `rusttest` (Miguel Ojeda)
- regulator: axp20x: AXP717: fix LDO supply rails and off-by-ones (Andre Przywara)
- regulator: bd71815: fix ramp values (Kalle Niemi)
- regulator: core: Fix modpost error "regulator_get_regmap" undefined (Biju Das)
- regulator: tps6594-regulator: Fix the number of irqs for TPS65224 and TPS6594 (Thomas Richard)
- spi: spi-imx: imx51: revert burst length calculation back to bits_per_word (Marc Kleine-Budde)
- spi: Fix SPI slave probe failure (Amit Kumar Mahapatra)
- spi: Fix OCTAL mode support (Patrice Chotard)
- spi: stm32: qspi: Clamp stm32_qspi_get_mode() output to CCR_BUSWIDTH_4 (Patrice Chotard)
- spi: stm32: qspi: Fix dual flash mode sanity test in stm32_qspi_setup() (Patrice Chotard)
- spi: cs42l43: Drop cs35l56 SPI speed down to 11MHz (Charles Keepax)
- spi: cs42l43: Correct SPI root clock speed (Charles Keepax)
- NFSD: grab nfsd_mutex in nfsd_nl_rpc_status_get_dumpit() (Lorenzo Bianconi)
- nfsd: fix oops when reading pool_stats before server is started (Jeff Layton)
- xfs: fix unlink vs cluster buffer instantiation race (Dave Chinner)
- bcachefs: Move the ei_flags setting to after initialization (Youling Tang)
- bcachefs: Fix a UAF after write_super() (Kent Overstreet)
- bcachefs: Use bch2_print_string_as_lines for long err (Kent Overstreet)
- bcachefs: Fix I_NEW warning in race path in bch2_inode_insert() (Kent Overstreet)
- bcachefs: Replace bare EEXIST with private error codes (Kent Overstreet)
- bcachefs: Fix missing alloc_data_type_set() (Kent Overstreet)
- closures: Change BUG_ON() to WARN_ON() (Kent Overstreet)
- bcachefs: fix alignment of VMA for memory mapped files on THP (Youling Tang)
- bcachefs: Fix safe errors by default (Kent Overstreet)
- bcachefs: Fix bch2_trans_put() (Kent Overstreet)
- bcachefs: set_worker_desc() for delete_dead_snapshots (Kent Overstreet)
- bcachefs: Fix bch2_sb_downgrade_update() (Kent Overstreet)
- bcachefs: Handle cached data LRU wraparound (Kent Overstreet)
- bcachefs: Guard against overflowing LRU_TIME_BITS (Kent Overstreet)
- bcachefs: delete_dead_snapshots() doesn't need to go RW (Kent Overstreet)
- bcachefs: Fix early init error path in journal code (Kent Overstreet)
- bcachefs: Check for invalid btree IDs (Kent Overstreet)
- bcachefs: Fix btree ID bitmasks (Kent Overstreet)
- bcachefs: Fix shift overflow in read_one_super() (Kent Overstreet)
- bcachefs: Fix a locking bug in the do_discard_fast() path (Kent Overstreet)
- bcachefs: Fix array-index-out-of-bounds (Kent Overstreet)
- bcachefs: Fix initialization order for srcu barrier (Kent Overstreet)
- ata: ahci: Do not enable LPM if no LPM states are supported by the HBA (Niklas Cassel)
- pwm: stm32: Fix error message to not describe the previous error path (Uwe Kleine-König)
- pwm: stm32: Fix calculation of prescaler (Uwe Kleine-König)
- pwm: stm32: Refuse too small period requests (Uwe Kleine-König)
- firmware: psci: Fix return value from psci_system_suspend() (Sudeep Holla)
- riscv: dts: sophgo: disable write-protection for milkv duo (Haylen Chu)
- arm64: dts: imx8qm-mek: fix gpio number for reg_usdhc2_vmmc (Frank Li)
- arm64: dts: freescale: imx8mm-verdin: enable hysteresis on slow input pin (Max Krummenacher)
- arm64: dts: imx93-11x11-evk: Remove the 'no-sdio' property (Fabio Estevam)
- arm64: dts: freescale: imx8mp-venice-gw73xx-2x: fix BT shutdown GPIO (Tim Harvey)
- arm: dts: imx53-qsb-hdmi: Disable panel instead of deleting node (Liu Ying)
- arm64: dts: imx8mp: Fix TC9595 input clock on DH i.MX8M Plus DHCOM SoM (Marek Vasut)
- arm64: dts: freescale: imx8mm-verdin: Fix GPU speed (Joao Paulo Goncalves)
- LoongArch: KVM: Remove an unneeded semicolon (Yang Li)
- LoongArch: Fix multiple hardware watchpoint issues (Hui Li)
- LoongArch: Trigger user-space watchpoints correctly (Hui Li)
- LoongArch: Fix watchpoint setting error (Hui Li)
- LoongArch: Only allow OBJTOOL & ORC unwinder if toolchain supports -mthin-add-sub (Xi Ruoyao)
- KVM: selftests: Fix RISC-V compilation (Andrew Jones)
- KVM: Stop processing *all* memslots when "null" mmu_notifier handler is found (Babu Moger)
- KVM: Fix a data race on last_boosted_vcpu in kvm_vcpu_on_spin() (Breno Leitao)
- KVM: selftests: x86: Prioritize getting max_gfn from GuestPhysBits (Tao Su)
- KVM: selftests: Fix shift of 32 bit unsigned int more than 32 bits (Colin Ian King)
- KVM: SEV-ES: Fix svm_get_msr()/svm_set_msr() for KVM_SEV_ES_INIT guests (Michael Roth)
- KVM: arm64: FFA: Release hyp rx buffer (Vincent Donnefort)
- KVM: arm64: Disassociate vcpus from redistributor region on teardown (Marc Zyngier)
- KVM: Discard zero mask with function kvm_dirty_ring_reset (Bibo Mao)
- virt: guest_memfd: fix reference leak on hwpoisoned page (Paolo Bonzini)
- kvm: do not account temporary allocations to kmem (Alexey Dobriyan)
- MAINTAINERS: Drop Wanpeng Li as a Reviewer for KVM Paravirt support (Sean Christopherson)
- KVM: x86: Always sync PIR to IRR prior to scanning I/O APIC routes (Sean Christopherson)
- scsi: usb: uas: Do not query the IO Advice Hints Grouping mode page for USB/UAS devices (Bart Van Assche)
- scsi: core: Introduce the BLIST_SKIP_IO_HINTS flag (Bart Van Assche)
- scsi: ufs: core: Free memory allocated for model before reinit (Joel Slebodnick)
- drm/xe/vf: Don't touch GuC irq registers if using memory irqs (Michal Wajdeczko)
- drm/amdgpu: init TA fw for psp v14 (Likun Gao)
- drm/amdgpu: cleanup MES11 command submission (Christian König)
- drm/amdgpu: fix UBSAN warning in kv_dpm.c (Alex Deucher)
- drm/radeon: fix UBSAN warning in kv_dpm.c (Alex Deucher)
- drm/amd/display: Disable CONFIG_DRM_AMD_DC_FP for RISC-V with clang (Nathan Chancellor)
- drm/amd/display: Attempt to avoid empty TUs when endpoint is DPIA (Michael Strauss)
- drm/amd/display: change dram_clock_latency to 34us for dcn35 (Paul Hsieh)
- drm/amd/display: Change dram_clock_latency to 34us for dcn351 (Daniel Miess)
- drm/amdgpu: revert "take runtime pm reference when we attach a buffer" v2 (Christian König)
- drm/amdgpu: Indicate CU havest info to CP (Harish Kasiviswanathan)
- drm/amd/display: prevent register access while in IPS (Hamza Mahfooz)
- drm/amdgpu: fix locking scope when flushing tlb (Yunxiang Li)
- drm/amd/display: Remove redundant idle optimization check (Roman Li)
- drm/i915/mso: using joiner is not possible with eDP MSO (Jani Nikula)
- ovl: fix encoding fid for lower only root (Miklos Szeredi)
- ovl: fix copy-up in tmpfile (Miklos Szeredi)
- io_uring/rsrc: fix incorrect assignment of iter->nr_segs in io_import_fixed (Chenliang Li)
- RDMA/mana_ib: Ignore optional access flags for MRs (Konstantin Taranov)
- RDMA/mlx5: Add check for srq max_sge attribute (Patrisious Haddad)
- RDMA/mlx5: Fix unwind flow as part of mlx5_ib_stage_init_init (Yishai Hadas)
- RDMA/mlx5: Ensure created mkeys always have a populated rb_key (Jason Gunthorpe)
- RDMA/mlx5: Follow rb_key.ats when creating new mkeys (Jason Gunthorpe)
- RDMA/mlx5: Remove extra unlock on error path (Jason Gunthorpe)
- RDMA/rxe: Fix responder length checking for UD request packets (Honggang LI)
- RDMA/rxe: Fix data copy for IB_SEND_INLINE (Honggang LI)
- RDMA/bnxt_re: Fix the max msix vectors macro (Selvin Xavier)
- ALSA: hda: Use imply for suggesting CONFIG_SERIAL_MULTI_INSTANTIATE (Takashi Iwai)
- ALSA: hda/realtek: Add quirk for Lenovo Yoga Pro 7 14AHP9 (Pablo Caño)
- ACPI: mipi-disco-img: Switch to new Intel CPU model defines (Hans de Goede)
- ACPI: scan: Ignore camera graph port nodes on all Dell Tiger, Alder and Raptor Lake models (Hans de Goede)
- ACPICA: Revert "ACPICA: avoid Info: mapping multiple BARs. Your kernel is fine." (Raju Rangoju)
- thermal: int340x: processor_thermal: Support shared interrupts (Srinivas Pandruvada)
- thermal/drivers/mediatek/lvts_thermal: Return error in case of invalid efuse data (Julien Panis)
- thermal/drivers/mediatek/lvts_thermal: Remove filtered mode for mt8188 (Julien Panis)
- thermal: core: Change PM notifier priority to the minimum (Rafael J. Wysocki)
- thermal: core: Synchronize suspend-prepare and post-suspend actions (Rafael J. Wysocki)
- dmaengine: ioatdma: Fix missing kmem_cache_destroy() (Nikita Shubin)
- dt-bindings: dma: fsl-edma: fix dma-channels constraints (Krzysztof Kozlowski)
- dmaengine: fsl-edma: avoid linking both modules (Arnd Bergmann)
- dmaengine: ioatdma: Fix kmemleak in ioat_pci_probe() (Nikita Shubin)
- dmaengine: ioatdma: Fix error path in ioat3_dma_probe() (Nikita Shubin)
- dmaengine: ioatdma: Fix leaking on version mismatch (Nikita Shubin)
- dmaengine: ti: k3-udma-glue: Fix of_k3_udma_glue_parse_chn_by_id() (Siddharth Vadapalli)
- dmaengine: idxd: Fix possible Use-After-Free in irq_process_work_list (Li RongQing)
- dmaengine: xilinx: xdma: Fix data synchronisation in xdma_channel_isr() (Louis Chauvet)
- phy: qcom: qmp-combo: Switch from V6 to V6 N4 register offsets (Abel Vesa)
- phy: qcom-qmp: pcs: Add missing v6 N4 register offsets (Abel Vesa)
- phy: qcom-qmp: qserdes-txrx: Add missing registers offsets (Abel Vesa)
- soundwire: fix usages of device_get_named_child_node() (Pierre-Louis Bossart)
- redhat/kernel.spec: fix attributes of symvers file (Jan Stancek)
- redhat: add filtermods rule for iommu tests (Jan Stancek)
- btrfs: zoned: allocate dummy checksums for zoned NODATASUM writes (Johannes Thumshirn)
- btrfs: retry block group reclaim without infinite loop (Boris Burkov)
- net: usb: rtl8150 fix unintiatilzed variables in rtl8150_get_link_ksettings (Oliver Neukum)
- selftests: virtio_net: add forgotten config options (Jiri Pirko)
- bnxt_en: Restore PTP tx_avail count in case of skb_pad() error (Pavan Chebbi)
- bnxt_en: Set TSO max segs on devices with limits (Michael Chan)
- bnxt_en: Update firmware interface to 1.10.3.44 (Michael Chan)
- net: stmmac: Assign configured channel value to EXTTS event (Oleksij Rempel)
- selftests: add selftest for the SRv6 End.DX6 behavior with netfilter (Jianguo Wu)
- selftests: add selftest for the SRv6 End.DX4 behavior with netfilter (Jianguo Wu)
- netfilter: move the sysctl nf_hooks_lwtunnel into the netfilter core (Jianguo Wu)
- seg6: fix parameter passing when calling NF_HOOK() in End.DX4 and End.DX6 behaviors (Jianguo Wu)
- netfilter: ipset: Fix suspicious rcu_dereference_protected() (Jozsef Kadlecsik)
- net: do not leave a dangling sk pointer, when socket creation fails (Ignat Korchagin)
- net/tcp_ao: Don't leak ao_info on error-path (Dmitry Safonov)
- ice: Fix VSI list rule with ICE_SW_LKUP_LAST type (Marcin Szycik)
- ipv6: bring NLM_DONE out to a separate recv() again (Jakub Kicinski)
- selftests: openvswitch: Set value to nla flags. (Adrian Moreno)
- octeontx2-pf: Fix linking objects into multiple modules (Geetha sowjanya)
- octeontx2-pf: Add error handling to VLAN unoffload handling (Simon Horman)
- virtio_net: fixing XDP for fully checksummed packets handling (Heng Qi)
- virtio_net: checksum offloading handling fix (Heng Qi)
- net: usb: ax88179_178a: improve reset check (Jose Ignacio Tornos Martinez)
- net: stmmac: No need to calculate speed divider when offload is disabled (Xiaolei Wang)
- net: phy: dp83tg720: get master/slave configuration in link down state (Oleksij Rempel)
- net: phy: dp83tg720: wake up PHYs in managed mode (Oleksij Rempel)
- selftests: openvswitch: Use bash as interpreter (Simon Horman)
- ptp: fix integer overflow in max_vclocks_store (Dan Carpenter)
- sched: act_ct: add netns into the key of tcf_ct_flow_table (Xin Long)
- tipc: force a dst refcount before doing decryption (Xin Long)
- net/sched: act_api: fix possible infinite loop in tcf_idr_check_alloc() (David Ruth)
- net: phy: mxl-gpy: Remove interrupt mask clearing from config_init (Raju Lakkaraju)
- net: lan743x: Support WOL at both the PHY and MAC appropriately (Raju Lakkaraju)
- net: lan743x: disable WOL upon resume to restore full data path operation (Raju Lakkaraju)
- qca_spi: Make interrupt remembering atomic (Stefan Wahren)
- netns: Make get_net_ns() handle zero refcount net (Yue Haibing)
- xfrm6: check ip6_dst_idev() return value in xfrm6_get_saddr() (Eric Dumazet)
- ipv6: prevent possible NULL dereference in rt6_probe() (Eric Dumazet)
- ipv6: prevent possible NULL deref in fib6_nh_init() (Eric Dumazet)
- selftests: mptcp: userspace_pm: fixed subtest names (Matthieu Baerts (NGI0))
- tcp: clear tp->retrans_stamp in tcp_rcv_fastopen_synack() (Eric Dumazet)
- netrom: Fix a memory leak in nr_heartbeat_expiry() (Gavrilov Ilia)
- ice: implement AQ download pkg retry (Wojciech Drewek)
- ice: fix 200G link speed message log (Paul Greenwalt)
- ice: avoid IRQ collision to fix init failure on ACPI S3 resume (En-Wei Wu)
- netdev-genl: fix error codes when outputting XDP features (Jakub Kicinski)
- bpf: Harden __bpf_kfunc tag against linker kfunc removal (Tony Ambardar)
- compiler_types.h: Define __retain for __attribute__((__retain__)) (Tony Ambardar)
- bpf: Avoid splat in pskb_pull_reason (Florian Westphal)
- bpf: fix UML x86_64 compile failure (Maciej Żenczykowski)
- selftests/bpf: Add test coverage for reg_set_min_max handling (Daniel Borkmann)
- bpf: Reduce stack consumption in check_stack_write_fixed_off (Daniel Borkmann)
- bpf: Fix reg_set_min_max corruption of fake_reg (Daniel Borkmann)
- MAINTAINERS: mailmap: Update Stanislav's email address (Stanislav Fomichev)
- wifi: mac80211: fix monitor channel with chanctx emulation (Johannes Berg)
- wifi: mac80211: Avoid address calculations via out of bounds array indexing (Kenton Groombridge)
- wifi: mac80211: Recalc offload when monitor stop (Remi Pommarel)
- wifi: iwlwifi: scan: correctly check if PSC listen period is needed (Ayala Beker)
- wifi: iwlwifi: mvm: fix ROC version check (Shaul Triebitz)
- wifi: iwlwifi: mvm: unlock mvm mutex (Shaul Triebitz)
- wifi: cfg80211: wext: add extra SIOCSIWSCAN data check (Dmitry Antipov)
- wifi: cfg80211: wext: set ssids=NULL for passive scans (Johannes Berg)
- cipso: make cipso_v4_skbuff_delattr() fully remove the CIPSO options (Ondrej Mosnacek)
- cipso: fix total option length computation (Ondrej Mosnacek)
- net: mvpp2: use slab_build_skb for oversized frames (Aryan Srivastava)
- ALSA: hda: cs35l56: Select SERIAL_MULTI_INSTANTIATE (Simon Trimmer)
- ALSA: hda/realtek: Add more codec ID to no shutup pins list (Kailang Yang)
- sound/oss/dmasound: add missing MODULE_DESCRIPTION() macro (Jeff Johnson)
- ALSA: hda/realtek: Add quirk for Lenovo Yoga Pro 7 14ARP8 (Gergely Meszaros)
- ALSA: hda/realtek: Enable headset mic on IdeaPad 330-17IKB 81DM (Ajrat Makhmutov)
- ALSA: hda: tas2781: Component should be unbound before deconstruction (Simon Trimmer)
- ALSA: hda: cs35l41: Component should be unbound before deconstruction (Simon Trimmer)
- ALSA: hda: cs35l56: Component should be unbound before deconstruction (Simon Trimmer)
- ALSA/hda: intel-dsp-config: Document AVS as dsp_driver option (Peter Ujfalusi)
- ALSA: hda/realtek: Support Lenovo Thinkbook 13x Gen 4 (Stefan Binding)
- ALSA: hda/realtek: Support Lenovo Thinkbook 16P Gen 5 (Stefan Binding)
- ALSA: hda: cs35l41: Support Lenovo Thinkbook 13x Gen 4 (Stefan Binding)
- ALSA: hda: cs35l41: Support Lenovo Thinkbook 16P Gen 5 (Stefan Binding)
- ALSA: hda/realtek: Remove Framework Laptop 16 from quirks (Dustin L. Howett)
- ALSA: hda/realtek: Limit mic boost on N14AP7 (Edson Juliano Drosdeck)
- ALSA: hda/realtek: fix mute/micmute LEDs don't work for ProBook 445/465 G11. (Andy Chi)
- ALSA: seq: ump: Fix missing System Reset message handling (Takashi Iwai)
- ALSA: hda: cs35l41: Possible null pointer dereference in cs35l41_hda_unbind() (Simon Trimmer)
- ALSA: hda: cs35l56: Fix lifecycle of codec pointer (Simon Trimmer)
- mfd: axp20x: AXP717: Fix missing IRQ status registers range (Andre Przywara)
- fedora: arm: Enable basic support for S32G-VNP-RDB3 board (Enric Balletbo i Serra)
- v6.10-rc4-rt7 (Sebastian Andrzej Siewior)
- i915: Update the _WAIT_FOR_ATOMIC_CHECK() comment. (Sebastian Andrzej Siewior)
- net: Update the BH series to v8. (Sebastian Andrzej Siewior)
- tracing: Build event generation tests only as modules (Masami Hiramatsu (Google))
- Revert "MIPS: pci: lantiq: restore reset gpio polarity" (Thomas Bogendoerfer)
- mips: bmips: BCM6358: make sure CBR is correctly set (Christian Marangi)
- MIPS: pci: lantiq: restore reset gpio polarity (Martin Schiller)
- MIPS: Routerboard 532: Fix vendor retry check code (Ilpo Järvinen)
- selftests/fchmodat2: fix clang build failure due to -static-libasan (John Hubbard)
- selftests/openat2: fix clang build failures: -static-libasan, LOCAL_HDRS (John Hubbard)
- selftests: seccomp: fix format-zero-length warnings (Amer Al Shanawany)
- selftests: filesystems: fix warn_unused_result build warnings (Amer Al Shanawany)
- cpumask: limit FORCE_NR_CPUS to just the UP case (Linus Torvalds)
- efi/arm64: Fix kmemleak false positive in arm64_efi_rt_init() (Waiman Long)
- efi/x86: Free EFI memory map only when installing a new one. (Ard Biesheuvel)
- efi/arm: Disable LPAE PAN when calling EFI runtime services (Ard Biesheuvel)
- ima: Avoid blocking in RCU read-side critical section (GUO Zihua)
- redhat: make bnx2xx drivers unmaintained in rhel-10 (John Meneghini) [RHEL-36646 RHEL-41231]
- Revert "mm: mmap: allow for the maximum number of bits for randomizing mmap_base by default" (Linus Torvalds)
- kcov: don't lose track of remote references during softirqs (Aleksandr Nogikh)
- mm: shmem: fix getting incorrect lruvec when replacing a shmem folio (Baolin Wang)
- mm/debug_vm_pgtable: drop RANDOM_ORVALUE trick (Peter Xu)
- mm: fix possible OOB in numa_rebuild_large_mapping() (Kefeng Wang)
- mm/migrate: fix kernel BUG at mm/compaction.c:2761! (Hugh Dickins)
- selftests: mm: make map_fixed_noreplace test names stable (Mark Brown)
- mm/memfd: add documentation for MFD_NOEXEC_SEAL MFD_EXEC (Jeff Xu)
- mm: mmap: allow for the maximum number of bits for randomizing mmap_base by default (Rafael Aquini)
- gcov: add support for GCC 14 (Peter Oberparleiter)
- zap_pid_ns_processes: clear TIF_NOTIFY_SIGNAL along with TIF_SIGPENDING (Oleg Nesterov)
- mm: huge_memory: fix misused mapping_large_folio_support() for anon folios (Ran Xiaokai)
- lib/alloc_tag: fix RCU imbalance in pgalloc_tag_get() (Suren Baghdasaryan)
- lib/alloc_tag: do not register sysctl interface when CONFIG_SYSCTL=n (Suren Baghdasaryan)
- MAINTAINERS: remove Lorenzo as vmalloc reviewer (Lorenzo Stoakes)
- Revert "mm: init_mlocked_on_free_v3" (David Hildenbrand)
- mm/page_table_check: fix crash on ZONE_DEVICE (Peter Xu)
- gcc: disable '-Warray-bounds' for gcc-9 (Yury Norov)
- ocfs2: fix NULL pointer dereference in ocfs2_abort_trigger() (Joseph Qi)
- ocfs2: fix NULL pointer dereference in ocfs2_journal_dirty() (Joseph Qi)
- MAINTAINERS: Update entries for Kees Cook (Kees Cook)
- kunit/overflow: Adjust for __counted_by with DEFINE_RAW_FLEX() (Kees Cook)
- yama: document function parameter (Christian Göttsche)
- mm/util: Swap kmemdup_array() arguments (Jean-Philippe Brucker)
- Drivers: hv: Cosmetic changes for hv.c and balloon.c (Aditya Nagesh)
- Documentation: hyperv: Improve synic and interrupt handling description (Michael Kelley)
- Documentation: hyperv: Update spelling and fix typo (Michael Kelley)
- tools: hv: suppress the invalid warning for packed member alignment (Saurabh Sengar)
- hv_balloon: Enable hot-add for memblock sizes > 128 MiB (Michael Kelley)
- hv_balloon: Use kernel macros to simplify open coded sequences (Michael Kelley)
- redhat/configs: Disable CONFIG_NFP (Kamal Heib) [RHEL-36647]
- Enable CONFIG_PWRSEQ_{SIMPLIE,EMMC} on aarch64 (Charles Mirabile)
- Fix SERIAL_SC16IS7XX configs for Fedora (Justin M. Forbes)

* Tue Jun 18 2024 Jan Stancek <jstancek@redhat.com> [6.10.0-0.rc4.11.el10]
- v6.10-rc4-rt6 (Sebastian Andrzej Siewior)
- Linux 6.10-rc4 (Linus Torvalds)
- parisc: Try to fix random segmentation faults in package builds (John David Anglin)
- i2c: designware: Fix the functionality flags of the slave-only interface (Jean Delvare)
- i2c: at91: Fix the functionality flags of the slave-only interface (Jean Delvare)
- USB: class: cdc-wdm: Fix CPU lockup caused by excessive log messages (Alan Stern)
- xhci: Handle TD clearing for multiple streams case (Hector Martin)
- xhci: Apply broken streams quirk to Etron EJ188 xHCI host (Kuangyi Chiang)
- xhci: Apply reset resume quirk to Etron EJ188 xHCI host (Kuangyi Chiang)
- xhci: Set correct transferred length for cancelled bulk transfers (Mathias Nyman)
- thunderbolt: debugfs: Fix margin debugfs node creation condition (Aapo Vienamo)
- usb-storage: alauda: Check whether the media is initialized (Shichao Lai)
- usb: typec: ucsi: Ack also failed Get Error commands (Heikki Krogerus)
- kcov, usb: disable interrupts in kcov_remote_start_usb_softirq (Andrey Konovalov)
- dt-bindings: usb: realtek,rts5411: Add missing "additionalProperties" on child nodes (Rob Herring (Arm))
- usb: typec: tcpm: Ignore received Hard Reset in TOGGLING state (Kyle Tso)
- usb: typec: tcpm: fix use-after-free case in tcpm_register_source_caps (Amit Sunil Dhamne)
- USB: xen-hcd: Traverse host/ when CONFIG_USB_XEN_HCD is selected (John Ernberg)
- usb: typec: ucsi: glink: increase max ports for x1e80100 (Johan Hovold)
- Revert "usb: chipidea: move ci_ulpi_init after the phy initialization" (Peter Chen)
- serial: drop debugging WARN_ON_ONCE() from uart_write() (Tetsuo Handa)
- serial: sc16is7xx: re-add Kconfig SPI or I2C dependency (Hugo Villeneuve)
- serial: sc16is7xx: rename Kconfig CONFIG_SERIAL_SC16IS7XX_CORE (Hugo Villeneuve)
- serial: port: Don't block system suspend even if bytes are left to xmit (Douglas Anderson)
- serial: 8250_pxa: Configure tx_loadsz to match FIFO IRQ level (Doug Brown)
- serial: 8250_dw: Revert "Move definitions to the shared header" (Andy Shevchenko)
- serial: 8250_dw: Don't use struct dw8250_data outside of 8250_dw (Andy Shevchenko)
- tty: n_tty: Fix buffer offsets when lookahead is used (Ilpo Järvinen)
- staging: vchiq_debugfs: Fix NPD in vchiq_dump_state (Stefan Wahren)
- drivers: core: synchronize really_probe() and dev_uevent() (Dirk Behme)
- sysfs: Unbreak the build around sysfs_bin_attr_simple_read() (Lukas Wunner)
- driver core: remove devm_device_add_groups() (Greg Kroah-Hartman)
- .editorconfig: remove trim_trailing_whitespace option (Greg Kroah-Hartman)
- iio: inkern: fix channel read regression (Johan Hovold)
- iio: imu: inv_mpu6050: stabilized timestamping in interrupt (Jean-Baptiste Maneyrol)
- iio: adc: ad7173: Fix sampling frequency setting (Dumitru Ceclan)
- iio: adc: ad7173: Clear append status bit (Dumitru Ceclan)
- iio: imu: inv_icm42600: delete unneeded update watermark call (Jean-Baptiste Maneyrol)
- iio: imu: inv_icm42600: stabilized timestamp in interrupt (Jean-Baptiste Maneyrol)
- iio: invensense: fix odr switching to same value (Jean-Baptiste Maneyrol)
- iio: adc: ad7173: Remove index from temp channel (Dumitru Ceclan)
- iio: adc: ad7173: Add ad7173_device_info names (Dumitru Ceclan)
- iio: adc: ad7173: fix buffers enablement for ad7176-2 (Dumitru Ceclan)
- iio: temperature: mlx90635: Fix ERR_PTR dereference in mlx90635_probe() (Harshit Mogalapalli)
- iio: imu: bmi323: Fix trigger notification in case of error (Vasileios Amoiridis)
- iio: dac: ad5592r: fix temperature channel scaling value (Marc Ferland)
- iio: pressure: bmp280: Fix BMP580 temperature reading (Adam Rizkalla)
- dt-bindings: iio: dac: fix ad354xr output range (Angelo Dureghello)
- iio: adc: ad9467: fix scan type sign (David Lechner)
- jfs: xattr: fix buffer overflow for invalid xattr (Greg Kroah-Hartman)
- misc: microchip: pci1xxxx: Fix a memory leak in the error handling of gp_aux_bus_probe() (Yongzhi Liu)
- misc: microchip: pci1xxxx: fix double free in the error handling of gp_aux_bus_probe() (Yongzhi Liu)
- parport: amiga: Mark driver struct with __refdata to prevent section mismatch (Uwe Kleine-König)
- mei: vsc: Fix wrong invocation of ACPI SID method (Hans de Goede)
- mei: vsc: Don't stop/restart mei device during system suspend/resume (Wentong Wu)
- mei: me: release irq in mei_me_pci_resume error path (Tomas Winkler)
- mei: demote client disconnect warning on suspend to debug (Alexander Usyskin)
- ata: libata-scsi: Set the RMB bit only for removable media devices (Damien Le Moal)
- RAS/AMD/ATL: Use system settings for MI300 DRAM to normalized address translation (Yazen Ghannam)
- RAS/AMD/ATL: Fix MI300 bank hash (Yazen Ghannam)
- firewire: core: record card index in bus_reset_handle tracepoints event (Takashi Sakamoto)
- firewire: core: record card index in tracepoinrts events derived from bus_reset_arrange_template (Takashi Sakamoto)
- firewire: core: record card index in async_phy_inbound tracepoints event (Takashi Sakamoto)
- firewire: core: record card index in async_phy_outbound_complete tracepoints event (Takashi Sakamoto)
- firewire: core: record card index in async_phy_outbound_initiate tracepoints event (Takashi Sakamoto)
- firewire: core: record card index in tracepoinrts events derived from async_inbound_template (Takashi Sakamoto)
- firewire: core: record card index in tracepoinrts events derived from async_outbound_initiate_template (Takashi Sakamoto)
- firewire: core: record card index in tracepoinrts events derived from async_outbound_complete_template (Takashi Sakamoto)
- firewire: fix website URL in Kconfig (Takashi Sakamoto)
- leds: class: Revert: "If no default trigger is given, make hw_control trigger the default trigger" (Hans de Goede)
- Enable ALSA (CONFIG_SND) on aarch64 (Charles Mirabile) [RHEL-40411]
- redhat: Remove DIST_BRANCH variable (Eder Zulian)
- xfs: make sure sb_fdblocks is non-negative (Wengang Wang)
- ksmbd: fix missing use of get_write in in smb2_set_ea() (Namjae Jeon)
- ksmbd: move leading slash check to smb2_get_name() (Namjae Jeon)
- x86/boot: Don't add the EFI stub to targets, again (Benjamin Segall)
- x86/uaccess: Fix missed zeroing of ia32 u64 get_user() range checking (Kees Cook)
- tick/nohz_full: Don't abuse smp_call_function_single() in tick_setup_device() (Oleg Nesterov)
- s390/mm: Restore mapping of kernel image using large pages (Alexander Gordeev)
- s390/mm: Allow large pages only for aligned physical addresses (Alexander Gordeev)
- s390: Update defconfigs (Heiko Carstens)
- drm/xe: move disable_c6 call (Riana Tauro)
- drm/xe: flush engine buffers before signalling user fence on all engines (Andrzej Hajda)
- drm/xe/pf: Assert LMEM provisioning is done only on DGFX (Michal Wajdeczko)
- drm/xe/xe_gt_idle: use GT forcewake domain assertion (Riana Tauro)
- MAINTAINERS: Update Xe driver maintainers (Thomas Hellström)
- MAINTAINERS: update Xe driver maintainers (Oded Gabbay)
- drm/exynos/vidi: fix memory leak in .get_modes() (Jani Nikula)
- drm/exynos: dp: drop driver owner initialization (Krzysztof Kozlowski)
- drm/exynos: hdmi: report safe 640x480 mode as a fallback when no EDID found (Marek Szyprowski)
- arm/komeda: Remove all CONFIG_DEBUG_FS conditional compilations (pengfuyuan)
- drm/mediatek: Call drm_atomic_helper_shutdown() at shutdown time (Douglas Anderson)
- drm: renesas: shmobile: Call drm_atomic_helper_shutdown() at shutdown time (Douglas Anderson)
- drm/nouveau: remove unused struct 'init_exec' (Dr. David Alan Gilbert)
- drm/nouveau: don't attempt to schedule hpd_work on headless cards (Vasily Khoruzhick)
- drm/amdgpu: Fix the BO release clear memory warning (Arunpravin Paneer Selvam)
- drm/bridge/panel: Fix runtime warning on panel bridge release (Adam Miotk)
- drm/komeda: check for error-valued pointer (Amjad Ouled-Ameur)
- drm: panel-orientation-quirks: Add quirk for Aya Neo KUN (Tobias Jakobi)
- drm: have config DRM_WERROR depend on !WERROR (Jani Nikula)
- vfio/pci: Insert full vma on mmap'd MMIO fault (Alex Williamson)
- vfio/pci: Use unmap_mapping_range() (Alex Williamson)
- vfio: Create vfio_fs_type with inode per device (Alex Williamson)
- loop: Disable fallocate() zero and discard if not supported (Cyril Hrubis)
- nvme: fix namespace removal list (Keith Busch)
- nvmet: always initialize cqe.result (Daniel Wagner)
- nvmet-passthru: propagate status from id override functions (Daniel Wagner)
- nvme: avoid double free special payload (Chunguang Xu)
- nbd: Remove __force casts (Christoph Hellwig)
- block: unmap and free user mapped integrity via submitter (Anuj Gupta)
- block: fix request.queuelist usage in flush (Chengming Zhou)
- block: Optimize disk zone resource cleanup (Damien Le Moal)
- block: sed-opal: avoid possible wrong address reference in read_sed_opal_key() (Su Hui)
- io_uring: fix cancellation overwriting req->flags (Pavel Begunkov)
- io_uring/rsrc: don't lock while !TASK_RUNNING (Pavel Begunkov)
- scsi: mpi3mr: Fix ATA NCQ priority support (Damien Le Moal)
- scsi: ufs: core: Quiesce request queues before checking pending cmds (Ziqi Chen)
- scsi: core: Disable CDL by default (Damien Le Moal)
- scsi: mpt3sas: Avoid test/set_bit() operating in non-allocated memory (Breno Leitao)
- scsi: sd: Use READ(16) when reading block zero on large capacity disks (Martin K. Petersen)
- iommu/amd: Fix panic accessing amd_iommu_enable_faulting (Dimitri Sivanich)
- cpufreq: intel_pstate: Check turbo_is_disabled() in store_no_turbo() (Rafael J. Wysocki)
- ACPI: x86: Force StorageD3Enable on more products (Mario Limonciello)
- ACPI: EC: Evaluate orphan _REG under EC device (Rafael J. Wysocki)
- thermal: gov_step_wise: Restore passive polling management (Rafael J. Wysocki)
- thermal: ACPI: Invalidate trip points with temperature of 0 or below (Rafael J. Wysocki)
- thermal: core: Do not fail cdev registration because of invalid initial state (Rafael J. Wysocki)
- bnxt_en: Adjust logging of firmware messages in case of released token in __hwrm_send() (Aleksandr Mishin)
- af_unix: Read with MSG_PEEK loops if the first unread byte is OOB (Rao Shoaib)
- bnxt_en: Cap the size of HWRM_PORT_PHY_QCFG forwarded response (Michael Chan)
- gve: Clear napi->skb before dev_kfree_skb_any() (Ziwei Xiao)
- ionic: fix use after netif_napi_del() (Taehee Yoo)
- Revert "igc: fix a log entry using uninitialized netdev" (Sasha Neftin)
- net: bridge: mst: fix suspicious rcu usage in br_mst_set_state (Nikolay Aleksandrov)
- net: bridge: mst: pass vlan group directly to br_mst_vlan_set_state (Nikolay Aleksandrov)
- net/ipv6: Fix the RT cache flush via sysctl using a previous delay (Petr Pavlu)
- netfilter: Use flowlabel flow key when re-routing mangled packets (Florian Westphal)
- netfilter: ipset: Fix race between namespace cleanup and gc in the list:set type (Jozsef Kadlecsik)
- netfilter: nft_inner: validate mandatory meta and payload (Davide Ornaghi)
- net: stmmac: replace priv->speed with the portTransmitRate from the tc-cbs parameters (Xiaolei Wang)
- gve: ignore nonrelevant GSO type bits when processing TSO headers (Joshua Washington)
- Bluetooth: fix connection setup in l2cap_connect (Pauli Virtanen)
- Bluetooth: L2CAP: Fix rejecting L2CAP_CONN_PARAM_UPDATE_REQ (Luiz Augusto von Dentz)
- Bluetooth: hci_sync: Fix not using correct handle (Luiz Augusto von Dentz)
- net: pse-pd: Use EOPNOTSUPP error code instead of ENOTSUPP (Kory Maincent)
- tcp: use signed arithmetic in tcp_rtx_probe0_timed_out() (Eric Dumazet)
- mailmap: map Geliang's new email address (Geliang Tang)
- mptcp: pm: update add_addr counters after connect (YonglongLi)
- mptcp: pm: inc RmAddr MIB counter once per RM_ADDR ID (YonglongLi)
- mptcp: ensure snd_una is properly initialized on connect (Paolo Abeni)
- net/sched: initialize noop_qdisc owner (Johannes Berg)
- net/mlx5e: Fix features validation check for tunneled UDP (non-VXLAN) packets (Gal Pressman)
- geneve: Fix incorrect inner network header offset when innerprotoinherit is set (Gal Pressman)
- net dsa: qca8k: fix usages of device_get_named_child_node() (Andy Shevchenko)
- tcp: fix race in tcp_v6_syn_recv_sock() (Eric Dumazet)
- netdevsim: fix backwards compatibility in nsim_get_iflink() (David Wei)
- net: stmmac: dwmac-qcom-ethqos: Configure host DMA width (Sagar Cheluvegowda)
- liquidio: Adjust a NULL pointer handling path in lio_vf_rep_copy_packet (Aleksandr Mishin)
- net: hns3: add cond_resched() to hns3 ring buffer init process (Jie Wang)
- net: hns3: fix kernel crash problem in concurrent scenario (Yonglong Liu)
- dt-bindings: net: dp8386x: Add MIT license along with GPL-2.0 (Udit Kumar)
- net: sfp: Always call `sfp_sm_mod_remove()` on remove (Csókás, Bence)
- NFS: add barriers when testing for NFS_FSDATA_BLOCKED (NeilBrown)
- SUNRPC: return proper error from gss_wrap_req_priv (Chen Hanxiao)
- NFSv4.1 enforce rootpath check in fs_location query (Olga Kornievskaia)
- NFS: abort nfs_atomic_open_v23 if name is too long. (NeilBrown)
- nfs: don't invalidate dentries on transient errors (Scott Mayhew)
- nfs: Avoid flushing many pages with NFS_FILE_SYNC (Jan Kara)
- nfs: propagate readlink errors in nfs_symlink_filler (Sagi Grimberg)
- MAINTAINERS: Change email address for Trond Myklebust (Trond Myklebust)
- NFSv4: Fix memory leak in nfs4_set_security_label (Dmitry Mastykin)
- x86/mm/numa: Use NUMA_NO_NODE when calling memblock_set_node() (Jan Beulich)
- memblock: make memblock_set_node() also warn about use of MAX_NUMNODES (Jan Beulich)
- v6.10-rc3-rt5 (Sebastian Andrzej Siewior)
- locking: Introduce nested-BH locking, v6 (Sebastian Andrzej Siewior)
- ARM: 9405/1: ftrace: Don't assume stack frames are contiguous in memory (Ard Biesheuvel)
- clkdev: don't fail clkdev_alloc() if over-sized (Russell King (Oracle))
- bcachefs: Fix rcu_read_lock() leak in drop_extra_replicas (Kent Overstreet)
- bcachefs: Add missing bch_inode_info.ei_flags init (Kent Overstreet)
- bcachefs: Add missing synchronize_srcu_expedited() call when shutting down (Kent Overstreet)
- bcachefs: Check for invalid bucket from bucket_gen(), gc_bucket() (Kent Overstreet)
- bcachefs: Replace bucket_valid() asserts in bucket lookup with proper checks (Kent Overstreet)
- bcachefs: Fix snapshot_create_lock lock ordering (Kent Overstreet)
- bcachefs: Fix refcount leak in check_fix_ptrs() (Kent Overstreet)
- bcachefs: Leave a buffer in the btree key cache to avoid lock thrashing (Kent Overstreet)
- bcachefs: Fix reporting of freed objects from key cache shrinker (Kent Overstreet)
- bcachefs: set sb->s_shrinker->seeks = 0 (Kent Overstreet)
- bcachefs: increase key cache shrinker batch size (Kent Overstreet)
- bcachefs: Enable automatic shrinking for rhashtables (Kent Overstreet)
- bcachefs: fix the display format for show-super (Hongbo Li)
- bcachefs: fix stack frame size in fsck.c (Kent Overstreet)
- bcachefs: Delete incorrect BTREE_ID_NR assertion (Kent Overstreet)
- bcachefs: Fix incorrect error handling found_btree_node_is_readable() (Kent Overstreet)
- bcachefs: Split out btree_write_submit_wq (Kent Overstreet)
- mailmap: Add my outdated addresses to the map file (Andy Shevchenko)
- v6.10-rc3-rt4 (Sebastian Andrzej Siewior)
- iomap: Fix iomap_adjust_read_range for plen calculation (Ritesh Harjani (IBM))
- iomap: keep on increasing i_size in iomap_write_end() (Zhang Yi)
- cachefiles: remove unneeded include of <linux/fdtable.h> (Gao Xiang)
- fs/file: fix the check in find_next_fd() (Yuntao Wang)
- cachefiles: make on-demand read killable (Baokun Li)
- cachefiles: flush all requests after setting CACHEFILES_DEAD (Baokun Li)
- cachefiles: Set object to close if ondemand_id < 0 in copen (Zizhi Wo)
- cachefiles: defer exposing anon_fd until after copy_to_user() succeeds (Baokun Li)
- cachefiles: never get a new anonymous fd if ondemand_id is valid (Baokun Li)
- cachefiles: add spin_lock for cachefiles_ondemand_info (Baokun Li)
- cachefiles: add consistency check for copen/cread (Baokun Li)
- cachefiles: remove err_put_fd label in cachefiles_ondemand_daemon_read() (Baokun Li)
- cachefiles: fix slab-use-after-free in cachefiles_ondemand_daemon_read() (Baokun Li)
- cachefiles: fix slab-use-after-free in cachefiles_ondemand_get_fd() (Baokun Li)
- cachefiles: remove requests from xarray during flushing requests (Baokun Li)
- cachefiles: add output string to cachefiles_obj_[get|put]_ondemand_fd (Baokun Li)
- statx: Update offset commentary for struct statx (John Garry)
- netfs: fix kernel doc for nets_wait_for_outstanding_io() (Christian Brauner)
- debugfs: continue to ignore unknown mount options (Christian Brauner)
- gitlab-ci: merge ark-latest before tagging cki-gating (Michael Hofmann)
- gitlab-ci: do not merge ark-latest for gating pipelines for Rawhide (Michael Hofmann)
- disable CONFIG_KVM_INTEL_PROVE_VE (Paolo Bonzini)
- redhat: remove the merge subtrees script (Derek Barbosa)
- redhat: rhdocs: delete .get_maintainer.conf (Derek Barbosa)
- redhat: rhdocs: Remove the rhdocs directory (Derek Barbosa)
- redhat/configs: Disable CONFIG_QLA3XXX (Kamal Heib) [RHEL-36646]
- Linux 6.10-rc3 (Linus Torvalds)
- perf bpf: Fix handling of minimal vmlinux.h file when interrupting the build (Namhyung Kim)
- Revert "perf record: Reduce memory for recording PERF_RECORD_LOST_SAMPLES event" (Arnaldo Carvalho de Melo)
- tools headers arm64: Sync arm64's cputype.h with the kernel sources (Arnaldo Carvalho de Melo)
- tools headers uapi: Sync linux/stat.h with the kernel sources to pick STATX_SUBVOL (Arnaldo Carvalho de Melo)
- tools headers UAPI: Update i915_drm.h with the kernel sources (Arnaldo Carvalho de Melo)
- tools headers UAPI: Sync kvm headers with the kernel sources (Arnaldo Carvalho de Melo)
- tools arch x86: Sync the msr-index.h copy with the kernel sources (Arnaldo Carvalho de Melo)
- tools headers: Update the syscall tables and unistd.h, mostly to support the new 'mseal' syscall (Arnaldo Carvalho de Melo)
- perf trace beauty: Update the arch/x86/include/asm/irq_vectors.h copy with the kernel sources to pick POSTED_MSI_NOTIFICATION (Arnaldo Carvalho de Melo)
- perf beauty: Update copy of linux/socket.h with the kernel sources (Arnaldo Carvalho de Melo)
- tools headers UAPI: Sync fcntl.h with the kernel sources to pick F_DUPFD_QUERY (Arnaldo Carvalho de Melo)
- tools headers UAPI: Sync linux/prctl.h with the kernel sources (Arnaldo Carvalho de Melo)
- tools include UAPI: Sync linux/stat.h with the kernel sources (Arnaldo Carvalho de Melo)
- EDAC/igen6: Convert PCIBIOS_* return codes to errnos (Ilpo Järvinen)
- EDAC/amd64: Convert PCIBIOS_* return codes to errnos (Ilpo Järvinen)
- Linux v6.10.0-0.rc4

* Mon Jun 10 2024 Patrick Talbert <ptalbert@redhat.com> [6.10.0-0.rc2.10.el10]
- clk: sifive: Do not register clkdevs for PRCI clocks (Samuel Holland)
- cifs: Don't advance the I/O iterator before terminating subrequest (David Howells)
- smb: client: fix deadlock in smb2_find_smb_tcon() (Enzo Matsumiya)
- HID: Ignore battery for ELAN touchscreens 2F2C and 4116 (Louis Dalibard)
- HID: i2c-hid: elan: fix reset suspend current leakage (Johan Hovold)
- dt-bindings: HID: i2c-hid: elan: add 'no-reset-on-power-off' property (Johan Hovold)
- dt-bindings: HID: i2c-hid: elan: add Elan eKTH5015M (Johan Hovold)
- dt-bindings: HID: i2c-hid: add dedicated Ilitek ILI2901 schema (Johan Hovold)
- input: Add support for "Do Not Disturb" (Aseda Aboagye)
- input: Add event code for accessibility key (Aseda Aboagye)
- hid: asus: asus_report_fixup: fix potential read out of bounds (Andrew Ballance)
- HID: logitech-hidpp: add missing MODULE_DESCRIPTION() macro (Jeff Johnson)
- HID: intel-ish-hid: fix endian-conversion (Arnd Bergmann)
- HID: nintendo: Fix an error handling path in nintendo_hid_probe() (Christophe JAILLET)
- HID: logitech-dj: Fix memory leak in logi_dj_recv_switch_to_dj_mode() (José Expósito)
- HID: core: remove unnecessary WARN_ON() in implement() (Nikita Zhandarovich)
- HID: nvidia-shield: Add missing check for input_ff_create_memless (Chen Ni)
- HID: intel-ish-hid: Fix build error for COMPILE_TEST (Zhang Lixu)
- modpost: do not warn about missing MODULE_DESCRIPTION() for vmlinux.o (Masahiro Yamada)
- kbuild: explicitly run mksysmap as sed script from link-vmlinux.sh (Richard Acayan)
- kconfig: remove wrong expr_trans_bool() (Masahiro Yamada)
- kconfig: doc: document behavior of 'select' and 'imply' followed by 'if' (Masahiro Yamada)
- kconfig: doc: fix a typo in the note about 'imply' (Masahiro Yamada)
- kconfig: gconf: give a proper initial state to the Save button (Masahiro Yamada)
- kconfig: remove unneeded code for user-supplied values being out of range (Masahiro Yamada)
- media: intel/ipu6: add csi2 port sanity check in notifier bound (Bingbu Cao)
- media: intel/ipu6: update the maximum supported csi2 port number to 6 (Bingbu Cao)
- media: mei: csi: Warn less verbosely of a missing device fwnode (Sakari Ailus)
- media: mei: csi: Put the IPU device reference (Sakari Ailus)
- media: intel/ipu6: fix the buffer flags caused by wrong parentheses (Bingbu Cao)
- media: intel/ipu6: Fix an error handling path in isys_probe() (Christophe JAILLET)
- media: intel/ipu6: Move isys_remove() close to isys_probe() (Christophe JAILLET)
- media: intel/ipu6: Fix some redundant resources freeing in ipu6_pci_remove() (Christophe JAILLET)
- media: Documentation: v4l: Fix ACTIVE route flag (Sakari Ailus)
- media: mgb4: Fix double debugfs remove (Martin Tůma)
- irqchip/gic-v3-its: Fix potential race condition in its_vlpi_prop_update() (Hagar Hemdan)
- irqchip/sifive-plic: Chain to parent IRQ after handlers are ready (Samuel Holland)
- irqchip/riscv-intc: Prevent memory leak when riscv_intc_init_common() fails (Sunil V L)
- x86/amd_nb: Check for invalid SMN reads (Yazen Ghannam)
- x86/kexec: Fix bug with call depth tracking (David Kaplan)
- perf/core: Fix missing wakeup when waiting for context reference (Haifeng Xu)
- locking/atomic: scripts: fix ${atomic}_sub_and_test() kerneldoc (Carlos Llamas)
- redhat/configs: fedora: Enable some drivers for IPU6 support (Hans de Goede)
- nilfs2: fix nilfs_empty_dir() misjudgment and long loop on I/O errors (Ryusuke Konishi)
- mm: fix xyz_noprof functions calling profiled functions (Suren Baghdasaryan)
- codetag: avoid race at alloc_slab_obj_exts (Thadeu Lima de Souza Cascardo)
- mm/hugetlb: do not call vma_add_reservation upon ENOMEM (Oscar Salvador)
- mm/ksm: fix ksm_zero_pages accounting (Chengming Zhou)
- mm/ksm: fix ksm_pages_scanned accounting (Chengming Zhou)
- kmsan: do not wipe out origin when doing partial unpoisoning (Alexander Potapenko)
- vmalloc: check CONFIG_EXECMEM in is_vmalloc_or_module_addr() (Cong Wang)
- mm: page_alloc: fix highatomic typing in multi-block buddies (Johannes Weiner)
- nilfs2: fix potential kernel bug due to lack of writeback flag waiting (Ryusuke Konishi)
- memcg: remove the lockdep assert from __mod_objcg_mlstate() (Sebastian Andrzej Siewior)
- mm: arm64: fix the out-of-bounds issue in contpte_clear_young_dirty_ptes (Barry Song)
- mm: huge_mm: fix undefined reference to `mthp_stats' for CONFIG_SYSFS=n (Barry Song)
- mm: drop the 'anon_' prefix for swap-out mTHP counters (Baolin Wang)
- gpio: add missing MODULE_DESCRIPTION() macros (Jeff Johnson)
- gpio: tqmx86: fix broken IRQ_TYPE_EDGE_BOTH interrupt type (Matthias Schiffer)
- gpio: tqmx86: store IRQ trigger type and unmask status separately (Matthias Schiffer)
- gpio: tqmx86: introduce shadow register for GPIO output value (Matthias Schiffer)
- gpio: tqmx86: fix typo in Kconfig label (Gregor Herburger)
- nvme: fix nvme_pr_* status code parsing (Weiwen Hu)
- nvme-fabrics: use reserved tag for reg read/write command (Chunguang Xu)
- null_blk: fix validation of block size (Andreas Hindborg)
- io_uring: fix possible deadlock in io_register_iowq_max_workers() (Hagar Hemdan)
- io_uring/io-wq: avoid garbage value of 'match' in io_wq_enqueue() (Su Hui)
- io_uring/napi: fix timeout calculation (Jens Axboe)
- io_uring: check for non-NULL file pointer in io_file_can_poll() (Jens Axboe)
- btrfs: protect folio::private when attaching extent buffer folios (Qu Wenruo)
- btrfs: fix leak of qgroup extent records after transaction abort (Filipe Manana)
- btrfs: fix crash on racing fsync and size-extending write into prealloc (Omar Sandoval)
- SUNRPC: Fix loop termination condition in gss_free_in_token_pages() (Chuck Lever)
- Revert "riscv: mm: accelerate pagefault when badaccess" (Palmer Dabbelt)
- riscv: fix overlap of allocated page and PTR_ERR (Nam Cao)
- KVM: s390x: selftests: Add shared zeropage test (David Hildenbrand)
- s390/crash: Do not use VM info if os_info does not have it (Alexander Gordeev)
- arm64/io: add constant-argument check (Arnd Bergmann)
- arm64: armv8_deprecated: Fix warning in isndep cpuhp starting process (Wei Li)
- platform/x86/amd/hsmp: Check HSMP support on AMD family of processors (Suma Hegde)
- platform/x86: dell-smbios: Simplify error handling (Armin Wolf)
- platform/x86: dell-smbios: Fix wrong token data in sysfs (Armin Wolf)
- platform/x86: yt2-1380: add CONFIG_EXTCON dependency (Arnd Bergmann)
- platform/x86: touchscreen_dmi: Use 2-argument strscpy() (Andy Shevchenko)
- platform/x86: touchscreen_dmi: Drop "silead,max-fingers" property (Hans de Goede)
- Input: silead - Always support 10 fingers (Hans de Goede)
- iommu/amd: Fix Invalid wait context issue (Vasant Hegde)
- iommu/amd: Check EFR[EPHSup] bit before enabling PPR (Vasant Hegde)
- iommu/amd: Fix workqueue name (Vasant Hegde)
- iommu: Return right value in iommu_sva_bind_device() (Lu Baolu)
- iommu/dma: Fix domain init (Robin Murphy)
- iommu/amd: Fix sysfs leak in iommu init (Kun(llfl))
- ata: pata_macio: Fix max_segment_size with PAGE_SIZE == 64K (Michael Ellerman)
- drm/komeda: remove unused struct 'gamma_curve_segment' (Dr. David Alan Gilbert)
- drm/vmwgfx: Don't memcmp equivalent pointers (Ian Forbes)
- drm/vmwgfx: remove unused struct 'vmw_stdu_dma' (Dr. David Alan Gilbert)
- drm/vmwgfx: Don't destroy Screen Target when CRTC is enabled but inactive (Ian Forbes)
- drm/vmwgfx: Standardize use of kibibytes when logging (Ian Forbes)
- drm/vmwgfx: Remove STDU logic from generic mode_valid function (Ian Forbes)
- drm/vmwgfx: 3D disabled should not effect STDU memory limits (Ian Forbes)
- drm/vmwgfx: Filter modes which exceed graphics memory (Ian Forbes)
- drm/panel: sitronix-st7789v: Add check for of_drm_get_panel_orientation (Chen Ni)
- drm/amdgpu/pptable: Fix UBSAN array-index-out-of-bounds (Tasos Sahanidis)
- drm/amd: Fix shutdown (again) on some SMU v13.0.4/11 platforms (Mario Limonciello)
- drm/xe/pf: Update the LMTT when freeing VF GT config (Michal Wajdeczko)
- scsi: ufs: mcq: Fix error output and clean up ufshcd_mcq_abort() (Chanwoo Lee)
- scsi: core: Handle devices which return an unusually large VPD page count (Martin K. Petersen)
- scsi: mpt3sas: Add missing kerneldoc parameter descriptions (Deming Wang)
- scsi: qedf: Set qed_slowpath_params to zero before use (Saurav Kashyap)
- scsi: qedf: Wait for stag work during unload (Saurav Kashyap)
- scsi: qedf: Don't process stag work during unload and recovery (Saurav Kashyap)
- scsi: sr: Fix unintentional arithmetic wraparound (Justin Stitt)
- scsi: core: alua: I/O errors for ALUA state transitions (Martin Wilck)
- scsi: mpi3mr: Use proper format specifier in mpi3mr_sas_port_add() (Nathan Chancellor)
- PCI: Revert the cfg_access_lock lockdep mechanism (Dan Williams)
- selftests: net: lib: set 'i' as local (Matthieu Baerts (NGI0))
- selftests: net: lib: avoid error removing empty netns name (Matthieu Baerts (NGI0))
- selftests: net: lib: support errexit with busywait (Matthieu Baerts (NGI0))
- net: ethtool: fix the error condition in ethtool_get_phy_stats_ethtool() (Su Hui)
- ipv6: fix possible race in __fib6_drop_pcpu_from() (Eric Dumazet)
- af_unix: Annotate data-race of sk->sk_shutdown in sk_diag_fill(). (Kuniyuki Iwashima)
- af_unix: Use skb_queue_len_lockless() in sk_diag_show_rqlen(). (Kuniyuki Iwashima)
- af_unix: Use skb_queue_empty_lockless() in unix_release_sock(). (Kuniyuki Iwashima)
- af_unix: Use unix_recvq_full_lockless() in unix_stream_connect(). (Kuniyuki Iwashima)
- af_unix: Annotate data-race of net->unx.sysctl_max_dgram_qlen. (Kuniyuki Iwashima)
- af_unix: Annotate data-races around sk->sk_sndbuf. (Kuniyuki Iwashima)
- af_unix: Annotate data-races around sk->sk_state in UNIX_DIAG. (Kuniyuki Iwashima)
- af_unix: Annotate data-race of sk->sk_state in unix_stream_read_skb(). (Kuniyuki Iwashima)
- af_unix: Annotate data-races around sk->sk_state in sendmsg() and recvmsg(). (Kuniyuki Iwashima)
- af_unix: Annotate data-race of sk->sk_state in unix_accept(). (Kuniyuki Iwashima)
- af_unix: Annotate data-race of sk->sk_state in unix_stream_connect(). (Kuniyuki Iwashima)
- af_unix: Annotate data-races around sk->sk_state in unix_write_space() and poll(). (Kuniyuki Iwashima)
- af_unix: Annotate data-race of sk->sk_state in unix_inq_len(). (Kuniyuki Iwashima)
- af_unix: Annodate data-races around sk->sk_state for writers. (Kuniyuki Iwashima)
- af_unix: Set sk->sk_state under unix_state_lock() for truly disconencted peer. (Kuniyuki Iwashima)
- net: wwan: iosm: Fix tainted pointer delete is case of region creation fail (Aleksandr Mishin)
- igc: Fix Energy Efficient Ethernet support declaration (Sasha Neftin)
- ice: map XDP queues to vectors in ice_vsi_map_rings_to_vectors() (Larysa Zaremba)
- ice: add flag to distinguish reset from .ndo_bpf in XDP rings config (Larysa Zaremba)
- ice: remove af_xdp_zc_qps bitmap (Larysa Zaremba)
- ice: fix reads from NVM Shadow RAM on E830 and E825-C devices (Jacob Keller)
- ice: fix iteration of TLVs in Preserved Fields Area (Jacob Keller)
- Revert "xsk: Document ability to redirect to any socket bound to the same umem" (Magnus Karlsson)
- Revert "xsk: Support redirect to any socket bound to the same umem" (Magnus Karlsson)
- bpf: Set run context for rawtp test_run callback (Jiri Olsa)
- bpf: Fix a potential use-after-free in bpf_link_free() (Cong Wang)
- bpf, devmap: Remove unnecessary if check in for loop (Thorsten Blum)
- libbpf: don't close(-1) in multi-uprobe feature detector (Andrii Nakryiko)
- bpf: Fix bpf_session_cookie BTF_ID in special_kfunc_set list (Jiri Olsa)
- selftests/bpf: fix inet_csk_accept prototype in test_sk_storage_tracing.c (Andrii Nakryiko)
- ptp: Fix error message on failed pin verification (Karol Kolacinski)
- net/sched: taprio: always validate TCA_TAPRIO_ATTR_PRIOMAP (Eric Dumazet)
- net/mlx5: Fix tainted pointer delete is case of flow rules creation fail (Aleksandr Mishin)
- net/mlx5: Always stop health timer during driver removal (Shay Drory)
- net/mlx5: Stop waiting for PCI if pci channel is offline (Moshe Shemesh)
- net: ethernet: mtk_eth_soc: handle dma buffer size soc specific (Frank Wunderlich)
- rtnetlink: make the "split" NLM_DONE handling generic (Jakub Kicinski)
- mptcp: count CLOSE-WAIT sockets for MPTCP_MIB_CURRESTAB (Jason Xing)
- tcp: count CLOSE-WAIT sockets for TCP_MIB_CURRESTAB (Jason Xing)
- selftests: hsr: add missing config for CONFIG_BRIDGE (Hangbin Liu)
- vxlan: Fix regression when dropping packets due to invalid src addresses (Daniel Borkmann)
- net: sched: sch_multiq: fix possible OOB write in multiq_tune() (Hangyu Hua)
- ionic: fix kernel panic in XDP_TX action (Taehee Yoo)
- net: phy: Micrel KSZ8061: fix errata solution not taking effect problem (Tristram Ha)
- net/smc: avoid overwriting when adjusting sock bufsizes (Wen Gu)
- octeontx2-af: Always allocate PF entries from low prioriy zone (Subbaraya Sundeep)
- net: tls: fix marking packets as decrypted (Jakub Kicinski)
- wifi: rtlwifi: Ignore IEEE80211_CONF_CHANGE_RETRY_LIMITS (Bitterblue Smith)
- wifi: mt76: mt7615: add missing chanctx ops (Johannes Berg)
- wifi: wilc1000: document SRCU usage instead of SRCU (Alexis Lothoré)
- Revert "wifi: wilc1000: set atomic flag on kmemdup in srcu critical section" (Alexis Lothoré)
- Revert "wifi: wilc1000: convert list management to RCU" (Alexis Lothoré)
- wifi: ath11k: move power type check to ASSOC stage when connecting to 6 GHz AP (Baochen Qiang)
- wifi: ath11k: fix WCN6750 firmware crash caused by 17 num_vdevs (Carl Huang)
- wifi: ath10k: fix QCOM_RPROC_COMMON dependency (Dmitry Baryshkov)
- wifi: ath11k: Fix error path in ath11k_pcic_ext_irq_config (Breno Leitao)
- wifi: mac80211: fix UBSAN noise in ieee80211_prep_hw_scan() (Dmitry Antipov)
- wifi: mac80211: correctly parse Spatial Reuse Parameter Set element (Lingbo Kong)
- wifi: mac80211: fix Spatial Reuse element size check (Lingbo Kong)
- wifi: iwlwifi: mvm: don't read past the mfuart notifcation (Emmanuel Grumbach)
- wifi: iwlwifi: mvm: Fix scan abort handling with HW rfkill (Ilan Peer)
- wifi: iwlwifi: mvm: check n_ssids before accessing the ssids (Miri Korenblit)
- wifi: iwlwifi: mvm: properly set 6 GHz channel direct probe option (Ayala Beker)
- wifi: iwlwifi: mvm: handle BA session teardown in RF-kill (Johannes Berg)
- wifi: iwlwifi: mvm: Handle BIGTK cipher in kek_kck cmd (Yedidya Benshimol)
- wifi: iwlwifi: mvm: remove stale STA link data during restart (Benjamin Berg)
- wifi: iwlwifi: dbg_ini: move iwl_dbg_tlv_free outside of debugfs ifdef (Shahar S Matityahu)
- wifi: iwlwifi: mvm: set properly mac header (Mordechay Goodstein)
- wifi: iwlwifi: mvm: revert gen2 TX A-MPDU size to 64 (Johannes Berg)
- wifi: iwlwifi: mvm: d3: fix WoWLAN command version lookup (Yedidya Benshimol)
- wifi: iwlwifi: mvm: fix a crash on 7265 (Emmanuel Grumbach)
- wifi: iwlwifi: mvm: always set the TWT IE offset (Shaul Triebitz)
- wifi: iwlwifi: mvm: don't initialize csa_work twice (Miri Korenblit)
- wifi: mac80211: pass proper link id for channel switch started notification (Aditya Kumar Singh)
- wifi: cfg80211: fix 6 GHz scan request building (Johannes Berg)
- wifi: mac80211: handle tasklet frames before stopping (Johannes Berg)
- wifi: mac80211: apply mcast rate only if interface is up (Johannes Berg)
- wifi: cfg80211: pmsr: use correct nla_get_uX functions (Lin Ma)
- wifi: cfg80211: Lock wiphy in cfg80211_get_station (Remi Pommarel)
- wifi: cfg80211: fully move wiphy work to unbound workqueue (Johannes Berg)
- wifi: cfg80211: validate HE operation element parsing (Johannes Berg)
- wifi: mac80211: Fix deadlock in ieee80211_sta_ps_deliver_wakeup() (Remi Pommarel)
- wifi: mac80211: mesh: init nonpeer_pm to active by default in mesh sdata (Nicolas Escande)
- wifi: mac80211: mesh: Fix leak of mesh_preq_queue objects (Nicolas Escande)
- lib/test_rhashtable: add missing MODULE_DESCRIPTION() macro (Jeff Johnson)
- net: dst_cache: add two DEBUG_NET warnings (Eric Dumazet)
- ila: block BH in ila_output() (Eric Dumazet)
- ipv6: sr: block BH in seg6_output_core() and seg6_input_core() (Eric Dumazet)
- net: ipv6: rpl_iptunnel: block BH in rpl_output() and rpl_input() (Eric Dumazet)
- ipv6: ioam: block BH from ioam6_output() (Eric Dumazet)
- vmxnet3: disable rx data ring on dma allocation failure (Matthias Stocker)
- net: phy: micrel: fix KSZ9477 PHY issues after suspend/resume (Tristram Ha)
- net/tcp: Don't consider TCP_CLOSE in TCP_AO_ESTABLISHED (Dmitry Safonov)
- net/ncsi: Fix the multi thread manner of NCSI driver (DelphineCCChiu)
- net: rps: fix error when CONFIG_RFS_ACCEL is off (Jason Xing)
- ax25: Replace kfree() in ax25_dev_free() with ax25_dev_put() (Duoming Zhou)
- ax25: Fix refcount imbalance on inbound connections (Lars Kellogg-Stedman)
- virtio_net: fix a spurious deadlock issue (Heng Qi)
- virtio_net: fix possible dim status unrecoverable (Heng Qi)
- ethtool: init tsinfo stats if requested (Vadim Fedorenko)
- MAINTAINERS: remove Peter Geis (Peter Geis)
- virtio_net: fix missing lock protection on control_buf access (Heng Qi)
- tomoyo: update project links (Tetsuo Handa)
- efi: Add missing __nocfi annotations to runtime wrappers (Ard Biesheuvel)
- efi: pstore: Return proper errors on UEFI failures (Guilherme G. Piccoli)
- efi/libstub: zboot.lds: Discard .discard sections (Nathan Chancellor)

* Thu Jun 06 2024 Patrick Talbert <ptalbert@redhat.com> [6.10.0-0.rc2.9.el10]
- v6.10-rc2-rt3 (Sebastian Andrzej Siewior)
- printk: Update the printk series. (Sebastian Andrzej Siewior)
- tcp: move inet_twsk_schedule helper out of header (Florian Westphal)
- net: tcp: un-pin the tw_timer (Florian Westphal)
- net: tcp/dccp: prepare for tw_timer un-pinning (Valentin Schneider)
- net: Move per-CPU flush-lists to bpf_net_context on PREEMPT_RT. (Sebastian Andrzej Siewior)
- net: Reference bpf_redirect_info via task_struct on PREEMPT_RT. (Sebastian Andrzej Siewior)
- net: Use nested-BH locking for bpf_scratchpad. (Sebastian Andrzej Siewior)
- seg6: Use nested-BH locking for seg6_bpf_srh_states. (Sebastian Andrzej Siewior)
- lwt: Don't disable migration prio invoking BPF. (Sebastian Andrzej Siewior)
- dev: Use nested-BH locking for softnet_data.process_queue. (Sebastian Andrzej Siewior)
- dev: Remove PREEMPT_RT ifdefs from backlog_lock.*(). (Sebastian Andrzej Siewior)
- net: softnet_data: Make xmit.recursion per task. (Sebastian Andrzej Siewior)
- netfilter: br_netfilter: Use nested-BH locking for brnf_frag_data_storage. (Sebastian Andrzej Siewior)
- net/ipv4: Use nested-BH locking for ipv4_tcp_sk. (Sebastian Andrzej Siewior)
- net/tcp_sigpool: Use nested-BH locking for sigpool_scratch. (Sebastian Andrzej Siewior)
- net: Use nested-BH locking for napi_alloc_cache. (Sebastian Andrzej Siewior)
- net: Use __napi_alloc_frag_align() instead of open coding it. (Sebastian Andrzej Siewior)
- locking/local_lock: Add local nested BH locking infrastructure. (Sebastian Andrzej Siewior)
- locking/local_lock: Introduce guard definition for local_lock. (Sebastian Andrzej Siewior)
- thermal: trip: Trigger trip down notifications when trips involved in mitigation become invalid (Rafael J. Wysocki)
- thermal: core: Introduce thermal_trip_crossed() (Rafael J. Wysocki)
- thermal/debugfs: Allow tze_seq_show() to print statistics for invalid trips (Rafael J. Wysocki)
- thermal/debugfs: Print initial trip temperature and hysteresis in tze_seq_show() (Rafael J. Wysocki)
- PNP: Hide pnp_bus_type from the non-PNP code (Andy Shevchenko)
- PNP: Make dev_is_pnp() to be a function and export it for modules (Andy Shevchenko)
- ACPI: APEI: EINJ: Fix einj_dev release leak (Dan Williams)
- ACPI: EC: Avoid returning AE_OK on errors in address space handler (Armin Wolf)
- ACPI: EC: Abort address space access upon error (Armin Wolf)
- ACPI: AC: Properly notify powermanagement core about changes (Thomas Weißschuh)
- cpufreq: intel_pstate: Fix unchecked HWP MSR access (Srinivas Pandruvada)
- cpufreq: amd-pstate: Fix the inconsistency in max frequency units (Dhananjay Ugwekar)
- cpufreq: amd-pstate: remove global header file (Arnd Bergmann)
- tools/power/cpupower: Fix Pstate frequency reporting on AMD Family 1Ah CPUs (Dhananjay Ugwekar)
- btrfs: ensure fast fsync waits for ordered extents after a write failure (Filipe Manana)
- bcachefs: Fix trans->locked assert (Kent Overstreet)
- bcachefs: Rereplicate now moves data off of durability=0 devices (Kent Overstreet)
- bcachefs: Fix GFP_KERNEL allocation in break_cycle() (Kent Overstreet)
- i2c: Remove I2C_CLASS_SPD (Heiner Kallweit)
- i2c: synquacer: Remove a clk reference from struct synquacer_i2c (Christophe JAILLET)
- tpm: Switch to new Intel CPU model defines (Tony Luck)
- tpm_tis: Do *not* flush uninitialized work (Jan Beulich)
- KVM: x86/mmu: Don't save mmu_invalidate_seq after checking private attr (Tao Su)
- KVM: arm64: Ensure that SME controls are disabled in protected mode (Fuad Tabba)
- KVM: arm64: Refactor CPACR trap bit setting/clearing to use ELx format (Fuad Tabba)
- KVM: arm64: Consolidate initializing the host data's fpsimd_state/sve in pKVM (Fuad Tabba)
- KVM: arm64: Eagerly restore host fpsimd/sve state in pKVM (Fuad Tabba)
- KVM: arm64: Allocate memory mapped at hyp for host sve state in pKVM (Fuad Tabba)
- KVM: arm64: Specialize handling of host fpsimd state on trap (Fuad Tabba)
- KVM: arm64: Abstract set/clear of CPTR_EL2 bits behind helper (Fuad Tabba)
- KVM: arm64: Fix prototype for __sve_save_state/__sve_restore_state (Fuad Tabba)
- KVM: arm64: Reintroduce __sve_save_state (Fuad Tabba)
- KVM: arm64: nv: Expose BTI and CSV_frac to a guest hypervisor (Marc Zyngier)
- KVM: arm64: nv: Fix relative priorities of exceptions generated by ERETAx (Marc Zyngier)
- KVM: arm64: AArch32: Fix spurious trapping of conditional instructions (Marc Zyngier)
- KVM: arm64: Allow AArch32 PSTATE.M to be restored as System mode (Marc Zyngier)
- KVM: arm64: Fix AArch32 register narrowing on userspace write (Marc Zyngier)
- RISC-V: KVM: Fix incorrect reg_subtype labels in kvm_riscv_vcpu_set_reg_isa_ext function (Quan Zhou)
- RISC-V: KVM: No need to use mask when hart-index-bit is 0 (Yong-Xuan Wang)
- KVM: x86: Drop support for hand tuning APIC timer advancement from userspace (Sean Christopherson)
- KVM: SEV-ES: Delegate LBR virtualization to the processor (Ravi Bangoria)
- KVM: SEV-ES: Disallow SEV-ES guests when X86_FEATURE_LBRV is absent (Ravi Bangoria)
- KVM: SEV-ES: Prevent MSR access post VMSA encryption (Nikunj A Dadhania)
- KVM: SVM: WARN on vNMI + NMI window iff NMIs are outright masked (Sean Christopherson)
- KVM: x86: Force KVM_WERROR if the global WERROR is enabled (Sean Christopherson)
- KVM: x86: Disable KVM_INTEL_PROVE_VE by default (Sean Christopherson)
- KVM: VMX: Enumerate EPT Violation #VE support in /proc/cpuinfo (Sean Christopherson)
- KVM: x86/mmu: Print SPTEs on unexpected #VE (Sean Christopherson)
- KVM: VMX: Dump VMCS on unexpected #VE (Sean Christopherson)
- KVM: x86/mmu: Add sanity checks that KVM doesn't create EPT #VE SPTEs (Sean Christopherson)
- KVM: nVMX: Always handle #VEs in L0 (never forward #VEs from L2 to L1) (Sean Christopherson)
- KVM: nVMX: Initialize #VE info page for vmcs02 when proving #VE support (Sean Christopherson)
- KVM: VMX: Don't kill the VM on an unexpected #VE (Sean Christopherson)
- KVM: x86/mmu: Use SHADOW_NONPRESENT_VALUE for atomic zap in TDP MMU (Isaku Yamahata)
- of: property: Fix fw_devlink handling of interrupt-map (Marc Zyngier)
- of/irq: Factor out parsing of interrupt-map parent phandle+args from of_irq_parse_raw() (Rob Herring (Arm))
- dt-bindings: arm: stm32: st,mlahb: Drop spurious "reg" property from example (Rob Herring (Arm))
- dt-bindings: arm: sunxi: Fix incorrect '-' usage (Rob Herring (Arm))
- of: of_test: add MODULE_DESCRIPTION() (Jeff Johnson)
- redhat: add missing UKI_secureboot_cert hunk (Patrick Talbert)
- v6.10-rc2-rt2 (Sebastian Andrzej Siewior)
- selftests/futex: don't pass a const char* to asprintf(3) (John Hubbard)
- selftests/futex: don't redefine .PHONY targets (all, clean) (John Hubbard)
- selftests/tracing: Fix event filter test to retry up to 10 times (Masami Hiramatsu (Google))
- selftests/futex: pass _GNU_SOURCE without a value to the compiler (John Hubbard)
- selftests/overlayfs: Fix build error on ppc64 (Michael Ellerman)
- selftests/openat2: Fix build warnings on ppc64 (Michael Ellerman)
- selftests: cachestat: Fix build warnings on ppc64 (Michael Ellerman)
- tracing/selftests: Fix kprobe event name test for .isra. functions (Steven Rostedt (Google))
- selftests/ftrace: Update required config (Masami Hiramatsu (Google))
- selftests/ftrace: Fix to check required event file (Masami Hiramatsu (Google))
- kselftest/alsa: Ensure _GNU_SOURCE is defined (Mark Brown)
- redhat/kernel.spec: keep extra modules in original directories (Jan Stancek)
- cxl/region: Fix memregion leaks in devm_cxl_add_region() (Li Zhijian)
- cxl/test: Add missing vmalloc.h for tools/testing/cxl/test/mem.c (Dave Jiang)
- LoongArch: Fix GMAC's phy-mode definitions in dts (Huacai Chen)
- LoongArch: Override higher address bits in JUMP_VIRT_ADDR (Jiaxun Yang)
- LoongArch: Fix entry point in kernel image header (Jiaxun Yang)
- LoongArch: Add all CPUs enabled by fdt to NUMA node 0 (Jiaxun Yang)
- LoongArch: Fix built-in DTB detection (Jiaxun Yang)
- LoongArch: Remove CONFIG_ACPI_TABLE_UPGRADE in platform_init() (Tiezhu Yang)
- redhat/configs: Move CONFIG_BLK_CGROUP_IOCOST=y to common/generic (Waiman Long)
- Linux v6.10.0-0.rc2

* Tue Jun 04 2024 Jan Stancek <jstancek@redhat.com> [6.10.0-0.rc2.8.el10]
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
- proc: consoles: Add notation to c_start/c_stop (John Ogness)
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
- printk: nbcon: Use nbcon consoles in console_flush_all() (John Ogness)
- printk: Track registered boot consoles (John Ogness)
- printk: nbcon: Provide function to flush using write_atomic() (Thomas Gleixner)
- printk: nbcon: Add helper to assign priority based on CPU state (John Ogness)
- printk: Add @flags argument for console_is_usable() (John Ogness)
- printk: Let console_is_usable() handle nbcon (John Ogness)
- printk: Make console_is_usable() available to nbcon (John Ogness)
- printk: nbcon: Do not rely on proxy headers (John Ogness)
- serial: core: Implement processing in port->lock wrapper (John Ogness)
- nbcon: Provide functions for drivers to acquire console for non-printing (John Ogness)
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
- memcg: Remove the lockdep assert from __mod_objcg_mlstate(). (Sebastian Andrzej Siewior)
- pinctrl: renesas: rzg2l: Use spin_{lock,unlock}_irq{save,restore} (Claudiu Beznea)
- drm/ttm/tests: Let ttm_bo_test consider different ww_mutex implementation. (Sebastian Andrzej Siewior)
- perf: Split __perf_pending_irq() out of perf_pending_irq() (Sebastian Andrzej Siewior)
- perf: Remove perf_swevent_get_recursion_context() from perf_pending_task(). (Sebastian Andrzej Siewior)
- perf: Enqueue SIGTRAP always via task_work. (Sebastian Andrzej Siewior)
- perf: Move irq_work_queue() where the event is prepared. (Sebastian Andrzej Siewior)
- Turn on CONFIG_MFD_QCOM_PM8008 for Fedora aarch64 (Justin M. Forbes)


###
# The following Emacs magic makes C-c C-e use UTC dates.
# Local Variables:
# rpm-change-log-uses-utc: t
# End:
###
