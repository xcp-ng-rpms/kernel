%define uname 4.19.0+1
%define short_uname 4.19
%define srcpath /usr/src/kernels/%{uname}-%{_arch}

# Control whether we perform a compat. check against published ABI.
# Default enabled: (to override: --without kabichk)
%define do_kabichk  %{?_without_kabichk: 0} %{?!_without_kabichk: 1}
# Default disabled: (to override: --with kabichk)
#%%define do_kabichk  %{?_with_kabichk: 1} %{?!_with_kabichk: 0}

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

Name: kernel
License: GPLv2
Version: 4.19.19
Release: 6.0.12.1.2.kmemleak%{?dist}
ExclusiveArch: x86_64
ExclusiveOS: Linux
Summary: The Linux kernel
BuildRequires: gcc
BuildRequires: kmod
BuildRequires: bc
BuildRequires: hostname
BuildRequires: elfutils-libelf-devel
BuildRequires: bison
BuildRequires: flex
%if %{do_kabichk}
BuildRequires: python
%endif
BuildRequires: elfutils-devel, binutils-devel, xz-devel
BuildRequires: python2-devel
BuildRequires: asciidoc xmlto
AutoReqProv: no
Provides: kernel-uname-r = %{uname}
Provides: kernel = %{version}-%{release}
Provides: kernel-%{_arch} = %{version}-%{release}
Requires(post): coreutils kmod
Requires(posttrans): coreutils dracut kmod


Source0: https://code.citrite.net/rest/archive/latest/projects/XSU/repos/linux-stable/archive?at=refs%2Ftags%2Fv4.19.19&format=tar.gz&prefix=kernel-4.19.19#/kernel-4.19.19.tar.gz
Source1: SOURCES/kernel/kernel-x86_64.config
Source2: SOURCES/kernel/macros.kernel
Source3: SOURCES/kernel/check-kabi
Source4: SOURCES/kernel/Module.kabi

Patch0: 0001-Fix-net-ipv4-do-not-handle-duplicate-fragments-as-ov.patch
Patch1: 0001-mm-zero-remaining-unavailable-struct-pages.patch
Patch2: 0002-mm-return-zero_resv_unavail-optimization.patch
Patch3: 0001-mtip32xx-fully-switch-to-the-generic-DMA-API.patch
Patch4: 0002-mtip32xx-clean-an-indentation-issue-remove-extraneou.patch
Patch5: 0001-GFS2-Flush-the-GFS2-delete-workqueue-before-stopping.patch
Patch6: 0001-scsi-libfc-retry-PRLI-if-we-cannot-analyse-the-paylo.patch
Patch7: 0003-mtip32xx-move-the-blk_rq_map_sg-call-to-mtip_hw_subm.patch
Patch8: 0004-mtip32xx-merge-mtip_submit_request-into-mtip_queue_r.patch
Patch9: 0005-mtip32xx-return-a-blk_status_t-from-mtip_send_trim.patch
Patch10: 0006-mtip32xx-remove-__force_bit2int.patch
Patch11: 0007-mtip32xx-add-missing-endianess-annotations-on-struct.patch
Patch12: 0008-mtip32xx-remove-mtip_init_cmd_header.patch
Patch13: 0009-mtip32xx-remove-mtip_get_int_command.patch
Patch14: 0010-mtip32xx-don-t-use-req-special.patch
Patch15: 0011-mtip32xxx-use-for_each_sg.patch
Patch16: 0012-mtip32xx-avoid-using-semaphores.patch
Patch17: 0013-mtip32xx-use-BLK_STS_DEV_RESOURCE-for-device-resourc.patch
Patch18: 0001-cifs-Limit-memory-used-by-lock-request-calls-to-a-pa.patch
Patch19: 0001-always-clear-the-X2APIC_ENABLE-bit-for-PV-guest.patch
Patch20: 0001-xen-pciback-Check-dev_data-before-using-it.patch
Patch21: 0001-gfs2-changes-to-gfs2_log_XXX_bio.patch
Patch22: 0001-gfs2-Remove-vestigial-bd_ops.patch
Patch23: gfs2-revert-fix-loop-in-gfs2_rbm_find.patch
Patch24: 0001-scsi-libfc-free-skb-when-receiving-invalid-flogi-res.patch
Patch25: 0001-Revert-scsi-libfc-Add-WARN_ON-when-deleting-rports.patch
Patch26: 0001-net-crypto-set-sk-to-NULL-when-af_alg_release.patch
Patch27: 0001-xen-netback-fix-occasional-leak-of-grant-ref-mapping.patch
Patch28: 0002-xen-netback-don-t-populate-the-hash-cache-on-XenBus-.patch
Patch29: 0001-gfs2-Fix-missed-wakeups-in-find_insert_glock.patch
Patch30: 0001-gfs2-Fix-an-incorrect-gfs2_assert.patch
Patch31: 0001-ACPI-APEI-Fix-possible-out-of-bounds-access-to-BERT-.patch
Patch32: 0001-efi-cper-Fix-possible-out-of-bounds-access.patch
Patch33: 0001-xen-Prevent-buffer-overflow-in-privcmd-ioctl.patch
Patch34: 0001-Revert-scsi-fcoe-clear-FC_RP_STARTED-flags-when-rece.patch
Patch35: 0001-gfs2-Fix-lru_count-going-negative.patch
Patch36: 0002-gfs2-clean_journal-improperly-set-sd_log_flush_head.patch
Patch37: 0003-gfs2-Fix-occasional-glock-use-after-free.patch
Patch38: 0005-gfs2-Remove-misleading-comments-in-gfs2_evict_inode.patch
Patch39: 0006-gfs2-Rename-sd_log_le_-revoke-ordered.patch
Patch40: 0007-gfs2-Rename-gfs2_trans_-add_unrevoke-remove_revoke.patch
Patch41: 0001-iomap-Clean-up-__generic_write_end-calling.patch
Patch42: 0002-fs-Turn-__generic_write_end-into-a-void-function.patch
Patch43: 0003-iomap-Fix-use-after-free-error-in-page_done-callback.patch
Patch44: 0004-iomap-Add-a-page_prepare-callback.patch
Patch45: 0008-gfs2-Fix-iomap-write-page-reclaim-deadlock.patch
Patch46: 0001-gfs2-Fix-rounding-error-in-gfs2_iomap_page_prepare.patch
Patch47: 0001-iomap-don-t-mark-the-inode-dirty-in-iomap_write_end.patch
Patch48: 0001-gfs2-Inode-dirtying-fix.patch
Patch49: 0001-xen-pci-reserve-MCFG-areas-earlier.patch
Patch50: 0001-kernel-module.c-Only-return-EEXIST-for-modules-that-.patch
Patch51: 0001-net-mlx5e-Force-CHECKSUM_UNNECESSARY-for-short-ether.patch
Patch52: 0001-net-mlx4_en-Force-CHECKSUM_NONE-for-short-ethernet-f.patch
Patch53: 0001-random-add-a-spinlock_t-to-struct-batched_entropy.patch
Patch54: 0001-tcp-limit-payload-size-of-sacked-skbs.patch
Patch55: 0002-tcp-tcp_fragment-should-apply-sane-memory-limits.patch
Patch56: 0003-tcp-add-tcp_min_snd_mss-sysctl.patch
Patch57: 0004-tcp-enforce-tcp_min_snd_mss-in-tcp_mtu_probing.patch
Patch58: 0001-tcp-refine-memory-limit-test-in-tcp_fragment.patch
Patch59: 0002-xen-events-fix-binding-user-event-channels-to-cpus.patch
Patch60: 0003-xen-let-alloc_xenballooned_pages-fail-if-not-enough-.patch
Patch61: 0001-tcp-be-more-careful-in-tcp_fragment.patch
Patch62: 0001-random-always-use-batched-entropy-for-get_random_u-3.patch
Patch63: 0001-block-cleanup-__blkdev_issue_discard.patch
Patch64: 0001-block-fix-32-bit-overflow-in-__blkdev_issue_discard.patch
Patch65: 0001-xen-events-remove-event-handling-recursion-detection.patch
Patch66: kbuild-AFTER_LINK.patch
Patch67: commit-info.patch
Patch68: expose-xsversion.patch
Patch69: blktap2.patch
Patch70: blkback-kthread-pid.patch
Patch71: tg3-alloc-repeat.patch
Patch72: dlm__increase_socket_backlog_to_avoid_hangs_with_16_nodes.patch
Patch73: map-1MiB-1-1.patch
Patch74: disable-EFI-Properties-table-for-Xen.patch
Patch75: hide-nr_cpus-warning.patch
Patch76: disable-pm-timer.patch
Patch77: net-Do-not-scrub-ignore_df-within-the-same-name-spac.patch
Patch78: enable-fragmention-gre-packets.patch
Patch79: 0001-libiscsi-Fix-race-between-iscsi_xmit_task-and-iscsi_.patch
Patch80: CA-285778-emulex-nic-ip-hdr-len.patch
Patch81: cifs-Change-the-default-value-SecFlags-to-0x83.patch
Patch82: call-kexec-before-offlining-noncrashing-cpus.patch
Patch83: 0001-Revert-rtc-cmos-Do-not-assume-irq-8-for-rtc-when-the.patch
Patch84: mm-zero-last-section-tail.patch
Patch85: hide-hung-task-for-idle-class.patch
Patch86: xfs-async-wait.patch
Patch87: 0001-xen-netback-Reset-nr_frags-before-freeing-skb.patch
Patch88: 0001-x86-efi-Don-t-require-non-blocking-EFI-callbacks.patch
Patch89: 0001-dma-add-dma_get_required_mask_from_max_pfn.patch
Patch90: 0002-x86-xen-correct-dma_get_required_mask-for-Xen-PV-gue.patch
Patch91: xen-balloon-hotplug-select-HOLES_IN_ZONE.patch
Patch92: 0001-pci-export-pci_probe_reset_function.patch
Patch93: 0002-xen-pciback-provide-a-reset-sysfs-file-to-try-harder.patch
Patch94: pciback-disable-root-port-aer.patch
Patch95: pciback-mask-root-port-comp-timeout.patch
Patch96: no-flr-quirk.patch
Patch97: revert-PCI-Probe-for-device-reset-support-during-enumeration.patch
Patch98: CA-135938-nfs-disconnect-on-rpc-retry.patch
Patch99: sunrpc-force-disconnect-on-connection-timeout.patch
Patch100: bonding-balance-slb.patch
Patch101: bridge-lock-fdb-after-garp.patch
Patch102: CP-13181-net-openvswitch-add-dropping-of-fip-and-lldp.patch
Patch103: CP-30097-prevent-ovs-vswitchd-kernel-warning.patch
Patch104: xen-ioemu-inject-msi.patch
Patch105: pv-iommu-support.patch
Patch106: kexec-reserve-crashkernel-region.patch
Patch107: 0001-xen-swiotlb-rework-early-repeat-code.patch
Patch108: 0001-arch-x86-xen-add-infrastruction-in-xen-to-support-gv.patch
Patch109: 0002-drm-i915-gvt-write-guest-ppgtt-entry-for-xengt-suppo.patch
Patch110: 0003-drm-i915-xengt-xengt-moudule-initial-files.patch
Patch111: 0004-drm-i915-xengt-check-on_destroy-on-pfn_to_mfn.patch
Patch112: 0005-arch-x86-xen-Import-x4.9-interface-for-ioreq.patch
Patch113: 0006-i915-gvt-xengt.c-Use-new-dm_op-instead-of-hvm_op.patch
Patch114: 0007-i915-gvt-xengt.c-New-interface-to-write-protect-PPGT.patch
Patch115: 0008-i915-gvt-xengt.c-Select-vgpu-type-according-to-low_g.patch
Patch116: 0009-drm-i915-gvt-Don-t-output-error-message-when-DomU-ma.patch
Patch117: 0010-drm-i915-gvt-xengt-Correctly-get-low-mem-max-gfn.patch
Patch118: 0011-drm-i915-gvt-Fix-dom0-call-trace-at-shutdown-or-rebo.patch
Patch119: 0012-hvm-dm_op.h-Sync-dm_op-interface-to-xen-4.9-release.patch
Patch120: 0013-drm-i915-gvt-Apply-g2h-adjust-for-GTT-mmio-access.patch
Patch121: 0014-drm-i915-gvt-Apply-g2h-adjustment-during-fence-mmio-.patch
Patch122: 0015-drm-i915-gvt-Patch-the-gma-in-gpu-commands-during-co.patch
Patch123: 0016-drm-i915-gvt-Retrieve-the-guest-gm-base-address-from.patch
Patch124: 0017-drm-i915-gvt-Align-the-guest-gm-aperture-start-offse.patch
Patch125: 0018-drm-i915-gvt-Add-support-to-new-VFIO-subregion-VFIO_.patch
Patch126: 0019-drm-i915-gvt-Implement-vGPU-status-save-and-restore-.patch
Patch127: 0020-vfio-Implement-new-Ioctl-VFIO_IOMMU_GET_DIRTY_BITMAP.patch
Patch128: 0021-drm-i915-gvt-Add-dev-node-for-vGPU-state-save-restor.patch
Patch129: 0022-drm-i915-gvt-Add-interface-to-control-the-vGPU-runni.patch
Patch130: 0023-drm-i915-gvt-Modify-the-vGPU-save-restore-logic-for-.patch
Patch131: 0024-drm-i915-gvt-Add-log-dirty-support-for-XENGT-migrati.patch
Patch132: 0025-drm-i915-gvt-xengt-Add-iosrv_enabled-to-track-iosrv-.patch
Patch133: 0026-drm-i915-gvt-Add-xengt-ppgtt-write-handler.patch
Patch134: 0027-drm-i915-gvt-xengt-Impliment-mpt-dma_map-unmap_guest.patch
Patch135: 0028-drm-i915-gvt-introduce-a-new-VFIO-region-for-vfio-de.patch
Patch136: 0029-drm-i915-gvt-change-the-return-value-of-opregion-acc.patch
Patch137: 0030-drm-i915-gvt-Rebase-the-code-to-gvt-staging-for-live.patch
Patch138: 0031-drm-i915-gvt-Apply-g2h-adjustment-to-buffer-start-gm.patch
Patch139: 0032-drm-i915-gvt-Fix-xengt-opregion-handling-in-migratio.patch
Patch140: 0033-drm-i915-gvt-XenGT-migration-optimize.patch
Patch141: 0034-drm-i915-gvt-Add-vgpu-execlist-info-into-migration-d.patch
Patch142: 0035-drm-i915-gvt-Emulate-ring-mode-register-restore-for-.patch
Patch143: 0036-drm-i915-gvt-Use-copy_to_user-to-return-opregion.patch
Patch144: 0037-drm-i915-gvt-Expose-opregion-in-vgpu-open.patch
Patch145: 0038-drm-i915-gvt-xengt-Don-t-shutdown-vm-at-ioreq-failur.patch
Patch146: 0039-drm-i915-gvt-Emulate-hw-status-page-address-register.patch
Patch147: 0040-drm-i915-gvt-migration-copy-vregs-on-vreg-load.patch
Patch148: 0041-drm-i915-gvt-Fix-a-command-corruption-caused-by-live.patch
Patch149: 0042-drm-i915-gvt-update-force-to-nonpriv-register-whitel.patch
Patch150: 0043-drm-i915-gvt-xengt-Fix-xengt-instance-destroy-error.patch
Patch151: 0044-drm-i915-gvt-invalidate-old-ggtt-page-when-update-gg.patch
Patch152: 0045-drm-i915-gvt-support-inconsecutive-partial-gtt-entry.patch
Patch153: set-XENMEM_get_mfn_from_pfn-hypercall-number.patch
Patch154: gvt-enforce-primary-class-id.patch
Patch155: gvt-use-xs-vgpu-type.patch
Patch156: xengt-pviommu-basic.patch
Patch157: xengt-pviommu-unmap.patch
Patch158: get_domctl_interface_version.patch
Patch159: xengt-fix-shutdown-failures.patch
Patch160: xengt-i915-gem-vgtbuffer.patch
Patch161: gvt-introduce-gtt-lock.patch
Patch162: xengt-gtt-2m-alignment.patch
Patch163: net-core__order-3_frag_allocator_causes_swiotlb_bouncing_under_xen.patch
Patch164: idle_cpu-return-0-during-softirq.patch
Patch165: default-xen-swiotlb-size-128MiB.patch
Patch166: dlm_handle_uevent_erestartsys.patch
Patch167: gfs2-add-skippiness.patch
Patch168: GFS2__Avoid_recently_demoted_rgrps
Patch169: gfs2-debug-rgrp-sweep
Patch170: gfs2-restore-kabi.patch
Patch171: xsa331-linux.patch
Patch172: xsa332-linux-01.patch
Patch173: v11-0003-xen-events-fix-race-in-evtchn_fifo_unmask.patch
Patch174: xsa332-linux-02.patch
Patch175: xsa332-linux-03.patch
Patch176: xsa332-linux-04.patch
Patch177: xsa332-linux-05.patch
Patch178: xsa332-linux-06.patch
Patch179: xsa332-linux-07.patch
Patch180: xsa332-linux-08.patch
Patch181: xsa332-linux-09.patch
Patch182: xsa332-linux-10.patch
Patch183: xsa332-linux-11.patch
Patch184: abi-version.patch

Provides: gitsha(ssh://git@code.citrite.net/xs/linux.pg.git) = 97c6d6430b54cb1ca99a29a61e55e6ae4516c893
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XSU/repos/linux-stable/archive?at=refs%2Ftags%2Fv4.19.19&format=tar.gz&prefix=kernel-4.19.19#/kernel-4.19.19.tar.gz) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520

%if %{do_kabichk}
%endif

%description
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions of the
operating system: memory allocation, process allocation, device input
and output, etc.


%package headers
Provides: gitsha(ssh://git@code.citrite.net/xs/linux.pg.git) = 97c6d6430b54cb1ca99a29a61e55e6ae4516c893
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XSU/repos/linux-stable/archive?at=refs%2Ftags%2Fv4.19.19&format=tar.gz&prefix=kernel-4.19.19#/kernel-4.19.19.tar.gz) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
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
Provides: gitsha(ssh://git@code.citrite.net/xs/linux.pg.git) = 97c6d6430b54cb1ca99a29a61e55e6ae4516c893
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XSU/repos/linux-stable/archive?at=refs%2Ftags%2Fv4.19.19&format=tar.gz&prefix=kernel-4.19.19#/kernel-4.19.19.tar.gz) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
License: GPLv2
Summary: Development package for building kernel modules to match the %{uname} kernel
Group: System Environment/Kernel
AutoReqProv: no
Provides: kernel-devel-%{_arch} = %{version}-%{release}
Provides: kernel-devel-uname-r = %{uname}
Requires: elfutils-libelf-devel

%description devel
This package provides kernel headers and makefiles sufficient to build modules
against the %{uname} kernel.

%package -n perf
Provides: gitsha(ssh://git@code.citrite.net/xs/linux.pg.git) = 97c6d6430b54cb1ca99a29a61e55e6ae4516c893
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XSU/repos/linux-stable/archive?at=refs%2Ftags%2Fv4.19.19&format=tar.gz&prefix=kernel-4.19.19#/kernel-4.19.19.tar.gz) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
Summary: Performance monitoring for the Linux kernel
License: GPLv2
%description -n perf
This package contains the perf tool, which enables performance monitoring
of the Linux kernel.

%global pythonperfsum Python bindings for apps which will manipulate perf events
%global pythonperfdesc A Python module that permits applications \
written in the Python programming language to use the interface \
to manipulate perf events.

%package -n python2-perf
Provides: gitsha(ssh://git@code.citrite.net/xs/linux.pg.git) = 97c6d6430b54cb1ca99a29a61e55e6ae4516c893
Provides: gitsha(https://code.citrite.net/rest/archive/latest/projects/XSU/repos/linux-stable/archive?at=refs%2Ftags%2Fv4.19.19&format=tar.gz&prefix=kernel-4.19.19#/kernel-4.19.19.tar.gz) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
Summary: %{pythonperfsum}
Provides: python2-perf
%description -n python2-perf
%{pythonperfdesc}

%prep
%autosetup -p1

%build

# This override tweaks the kernel makefiles so that we run debugedit on an
# object before embedding it.  When we later run find-debuginfo.sh, it will
# run debugedit again.  The edits it does change the build ID bits embedded
# in the stripped object, but repeating debugedit is a no-op.  We do it
# beforehand to get the proper final build ID bits into the embedded image.
# This affects the vDSO images in vmlinux, and the vmlinux image in bzImage.
export AFTER_LINK='sh -xc "/usr/lib/rpm/debugedit -b %{buildroot} -d /usr/src/debug -i $@ > $@.id"'

cp -f %{SOURCE1} .config
echo %{version}-%{release} > .xsversion
make silentoldconfig
make %{?_smp_mflags} bzImage
make %{?_smp_mflags} modules

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
%global perf_make \
  make EXTRA_CFLAGS="${RPM_OPT_FLAGS}" LDFLAGS="%{__global_ldflags}" %{?cross_opts} V=1 NO_PERF_READ_VDSO32=1 NO_PERF_READ_VDSOX32=1 WERROR=0 NO_LIBUNWIND=1 HAVE_CPLUS_DEMANGLE=1 NO_GTK2=1 NO_STRLCPY=1 NO_BIONIC=1 NO_JVMTI=1 prefix=%{_prefix}
%global perf_python2 -C tools/perf PYTHON=%{__python2}
# perf
# make sure check-headers.sh is executable
chmod +x tools/perf/check-headers.sh
%{perf_make} %{perf_python2} all

pushd tools/perf/Documentation/
make %{?_smp_mflags} man
popd

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

# Save debuginfo
install -d -m 755 %{buildroot}/usr/lib/debug/lib/modules/%{uname}
install -m 755 vmlinux %{buildroot}/usr/lib/debug/lib/modules/%{uname}

# Install -headers files
make INSTALL_HDR_PATH=%{buildroot}/usr headers_install

# perf tool binary and supporting scripts/binaries
%{perf_make} %{perf_python2} DESTDIR=%{buildroot} lib=%{_lib} install-bin install-traceevent-plugins
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
%{perf_make} %{perf_python2} DESTDIR=%{buildroot} install-python_ext

# perf man pages (note: implicit rpm magic compresses them later)
install -d %{buildroot}/%{_mandir}/man1
install -pm0644 tools/perf/Documentation/*.1 %{buildroot}/%{_mandir}/man1/

# Install -devel files
install -d -m 755 %{buildroot}/usr/src/kernels/%{uname}-%{_arch}
install -d -m 755 %{buildroot}%{_rpmconfigdir}/macros.d
install -m 644 %{SOURCE2} %{buildroot}%{_rpmconfigdir}/macros.d
echo '%%kernel_version %{uname}' >> %{buildroot}%{_rpmconfigdir}/macros.d/macros.kernel

# Setup -devel links correctly
ln -nsf %{srcpath} %{buildroot}/lib/modules/%{uname}/source
ln -nsf %{srcpath} %{buildroot}/lib/modules/%{uname}/build

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
cp -a --parents arch/x86/entry/syscalls/syscalltbl.sh %{buildroot}%{srcpath}
cp -a --parents arch/x86/entry/syscalls/syscallhdr.sh %{buildroot}%{srcpath}
cp -a --parents arch/x86/entry/syscalls/syscall_64.tbl %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs_32.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs_64.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs_common.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/tools/relocs.h %{buildroot}%{srcpath}
cp -a --parents tools/include/tools/le_byteshift.h %{buildroot}%{srcpath}
cp -a --parents arch/x86/purgatory/purgatory.c %{buildroot}%{srcpath}
cp -a --parents arch/x86/purgatory/stack.S %{buildroot}%{srcpath}
cp -a --parents arch/x86/purgatory/string.c %{buildroot}%{srcpath}
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
%ghost /lib/modules/%{uname}/modules.dep
%ghost /lib/modules/%{uname}/modules.dep.bin
%ghost /lib/modules/%{uname}/modules.devname
%ghost /lib/modules/%{uname}/modules.softdep
%ghost /lib/modules/%{uname}/modules.symbols
%ghost /lib/modules/%{uname}/modules.symbols.bin

%files headers
/usr/include/*

%files devel
/lib/modules/%{uname}/build
/lib/modules/%{uname}/source
%verify(not mtime) /usr/src/kernels/%{uname}-%{_arch}
%{_rpmconfigdir}/macros.d/macros.kernel

%files -n perf
%{_bindir}/perf
%dir %{_libdir}/traceevent
%{_libdir}/traceevent/plugins/
%{_libexecdir}/perf-core
%{_datadir}/perf-core/
%{_mandir}/man[1-8]/perf*
%{_sysconfdir}/bash_completion.d/perf
%doc tools/perf/Documentation/examples.txt
%license COPYING

%files -n python2-perf
%license COPYING
%{python2_sitearch}/*

%changelog
* Thu Nov 19 2020 Rushikesh Jadhav <rushikesh7@gmail.com> - 4.19.19-6.0.12.1.2.kmemleak
- Increase CONFIG_DEBUG_KMEMLEAK_EARLY_LOG_SIZE to 16000

* Thu Nov 12 2020 Rushikesh Jadhav <rushikesh7@gmail.com> - 4.19.19-6.0.12.1.1.kmemleak
- Enable kmemleak debug option and kmemleak-test module

* Tue Oct 27 2020 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-6.0.12.1
- Sync to latest hotfix 4.19.19-6.0.12

* Wed Oct 07 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-6.0.12
- CA-346372: Add fix for XSA-331
- CA-346374: Add fix for XSA-332

* Thu Apr 30 2020 Sergey Dyasli <sergey.dyasli@citrix.com> - 4.19.19-6.0.11
- CA-338183: Optimize get_random_u{32,64} by removing calls to RDRAND

* Mon Jan 27 2020 Jennifer Herbert <jennifer.herbert@citrix.com> - 4.19.19-6.0.10
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
