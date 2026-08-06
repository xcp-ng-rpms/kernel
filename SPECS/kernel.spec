%global package_speccommit ccb8ee3c01ade60b0ee7a22436d4b25d84702ae4
%global usver 4.19.325
%global cipver 134
%global stver 18
%global xsver 8.0.46
%global xsrel cip%{cipver}.%{xsver}%{?xscount}%{?xshash}
%global package_srccommit refs/tags/v4.19.325-cip%{cipver}
%define uname 4.19.0+1-cip%{cipver}.st%{stver}
%define short_uname 4.19
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
Release: %{?xsrel}.10%{?dist}
ExclusiveArch: x86_64
ExclusiveOS: Linux
Summary: The Linux kernel
BuildRequires: kmod
BuildRequires: dwarves

# These build dependencies are needed for building the main kernel and
# modules as well live patches.
%define core_builddeps() %{lua:
    deps = {
        'bc',
        'bison',
        'gcc',
        'devtoolset-11-elfutils-libelf-devel',
        'devtoolset-11-elfutils-devel',
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
BuildRequires: python2-devel
BuildRequires: asciidoc xmlto
%{?_cov_buildrequires}
AutoReqProv: no
Provides: kernel-uname-r = %{uname}
Provides: kernel = %{version}-%{release}
Provides: kernel-%{_arch} = %{version}-%{release}
Requires(post): coreutils kmod
Requires(posttrans): coreutils dracut kmod

Source0: linux-cip-4.19.325-cip134.tar.gz
Source1: kernel-x86_64.config
Source2: macros.kernel
# Patch0: 0001-Fix-net-ipv4-do-not-handle-duplicate-fragments-as-ov.patch: c763a3cf502 Fix "net: ipv4: do not handle duplicate fragments as overlapping"
# Patch1: 0001-xen-privcmd-allow-fetching-resource-sizes.patch: d8099663adc9 xen/privcmd: allow fetching resource sizes
# Patch2: 0001-block-genhd-add-groups-argument-to-device_add_disk.patch: 1bf6a186c452 block: genhd: add 'groups' argument to device_add_disk
# Patch3: 0002-nvme-register-ns_id-attributes-as-default-sysfs-grou.patch: ea7ac82cf4d8 nvme: register ns_id attributes as default sysfs groups
# Patch4: 0001-mm-zero-remaining-unavailable-struct-pages.patch: 9ac5917a1d28 mm: zero remaining unavailable struct pages
# Patch5: 0002-mm-return-zero_resv_unavail-optimization.patch: f19a50c1e3ba mm: return zero_resv_unavail optimization
# Patch6: 0001-mm-page_alloc.c-fix-uninitialized-memmaps-on-a-parti.patch: 0a69047d8235 mm/page_alloc.c: fix uninitialized memmaps on a partially populated last section
Patch7: 0001-mtip32xx-fully-switch-to-the-generic-DMA-API.patch
Patch8: 0002-mtip32xx-clean-an-indentation-issue-remove-extraneou.patch
# Patch9: 0001-GFS2-Flush-the-GFS2-delete-workqueue-before-stopping.patch: 4d7cf69b77ce GFS2: Flush the GFS2 delete workqueue before stopping the kernel threads
Patch10: 0001-scsi-libfc-retry-PRLI-if-we-cannot-analyse-the-paylo.patch
Patch11: 0001-gfs2-improve-debug-information-when-lvb-mismatches-a.patch
# Patch12: 0001-gfs2-Don-t-set-GFS2_RDF_UPTODATE-when-the-lvb-is-upd.patch: 48b128cddb91 gfs2: Don't set GFS2_RDF_UPTODATE when the lvb is updated
# Patch13: 0001-gfs2-slow-the-deluge-of-io-error-messages.patch: f3afad5d1eff gfs2: slow the deluge of io error messages
Patch14: 0001-gfs2-Use-fs_-functions-instead-of-pr_-function-where.patch
Patch15: 0001-gfs2-getlabel-support.patch
Patch16: 0001-gfs2-Always-check-the-result-of-gfs2_rbm_from_block.patch
Patch17: 0001-gfs2-Clean-up-out-of-bounds-check-in-gfs2_rbm_from_b.patch
Patch18: 0001-gfs2-Move-rs_-sizehint-rgd_gh-fields-into-the-inode.patch
Patch19: 0001-gfs2-Remove-unused-RGRP_RSRV_MINBYTES-definition.patch
Patch20: 0001-gfs2-Rename-bitmap.bi_-len-bytes.patch
Patch21: 0001-gfs2-Fix-some-minor-typos.patch
# Patch22: 0001-gfs2-Fix-marking-bitmaps-non-full.patch: fa3fe5f442ab gfs2: Fix marking bitmaps non-full
Patch23: 0001-gfs2-Remove-unnecessary-gfs2_rlist_alloc-parameter.patch
Patch24: 0001-gfs2-Pass-resource-group-to-rgblk_free.patch
Patch25: 0001-gfs2-write-revokes-should-traverse-sd_ail1_list-in-r.patch
Patch26: 0001-gfs2-Fix-minor-typo-couln-t-versus-couldn-t.patch
Patch27: 0003-mtip32xx-move-the-blk_rq_map_sg-call-to-mtip_hw_subm.patch
Patch28: 0004-mtip32xx-merge-mtip_submit_request-into-mtip_queue_r.patch
Patch29: 0005-mtip32xx-return-a-blk_status_t-from-mtip_send_trim.patch
Patch30: 0006-mtip32xx-remove-__force_bit2int.patch
Patch31: 0007-mtip32xx-add-missing-endianess-annotations-on-struct.patch
Patch32: 0008-mtip32xx-remove-mtip_init_cmd_header.patch
Patch33: 0009-mtip32xx-remove-mtip_get_int_command.patch
Patch34: 0010-mtip32xx-don-t-use-req-special.patch
Patch35: 0011-mtip32xxx-use-for_each_sg.patch
Patch36: 0012-mtip32xx-avoid-using-semaphores.patch
Patch37: 0013-mtip32xx-use-BLK_STS_DEV_RESOURCE-for-device-resourc.patch
# Patch38: 0001-cifs-Limit-memory-used-by-lock-request-calls-to-a-pa.patch: 63715c1f0a67 cifs: Limit memory used by lock request calls to a page
# Patch39: 0001-always-clear-the-X2APIC_ENABLE-bit-for-PV-guest.patch: c818b5b47181 always clear the X2APIC_ENABLE bit for PV guest
# Patch40: 0001-xen-pciback-Check-dev_data-before-using-it.patch: 73c1ca2dda37 xen/pciback: Check dev_data before using it
Patch41: 0001-gfs2-changes-to-gfs2_log_XXX_bio.patch
Patch42: 0001-gfs2-Remove-vestigial-bd_ops.patch
Patch43: 0001-gfs2-properly-initial-file_lock-used-for-unlock.patch
Patch44: 0001-gfs2-Clean-up-gfs2_is_-ordered-writeback.patch
Patch45: 0001-gfs2-Fix-the-gfs2_invalidatepage-description.patch
Patch46: 0001-gfs2-add-more-timing-info-to-journal-recovery-proces.patch
Patch47: 0001-gfs2-add-a-helper-function-to-get_log_header-that-ca.patch
Patch48: 0001-gfs2-Dump-nrpages-for-inodes-and-their-glocks.patch
# Patch49: 0001-gfs2-take-jdata-unstuff-into-account-in-do_grow.patch: 7baf8fd1ffff gfs2: take jdata unstuff into account in do_grow
# Patch50: 0001-dlm-fix-invalid-free.patch: afb4717ab81b dlm: fix invalid free
Patch51: 0001-dlm-don-t-allow-zero-length-names.patch
# Patch52: 0001-dlm-don-t-leak-kernel-pointer-to-userspace.patch: 5c2a3997ae5b dlm: don't leak kernel pointer to userspace
# Patch53: 0001-dlm-Don-t-swamp-the-CPU-with-callbacks-queued-during.patch: ee9268a9b55b dlm: Don't swamp the CPU with callbacks queued during recovery
# Patch54: 0001-dlm-fix-possible-call-to-kfree-for-non-initialized-p.patch: ed22415081ed dlm: fix possible call to kfree() for non-initialized pointer
# Patch55: 0001-dlm-fix-missing-idr_destroy-for-recover_idr.patch: 1bcac298b943 dlm: fix missing idr_destroy for recover_idr
# Patch56: 0001-dlm-NULL-check-before-kmem_cache_destroy-is-not-need.patch: 3b0107ca80fb dlm: NULL check before kmem_cache_destroy is not needed
Patch57: 0001-dlm-NULL-check-before-some-freeing-functions-is-not-.patch
# Patch58: 0001-dlm-fix-invalid-cluster-name-warning.patch: 446a04d879a0 dlm: fix invalid cluster name warning
# Patch59: gfs2-revert-fix-loop-in-gfs2_rbm_find.patch: 8b9be9db8a2a gfs2: Revert "Fix loop in gfs2_rbm_find"
# Patch60: 0001-scsi-libfc-free-skb-when-receiving-invalid-flogi-res.patch: e546c8787e7b scsi: libfc: free skb when receiving invalid flogi resp
# Patch61: 0001-Revert-scsi-libfc-Add-WARN_ON-when-deleting-rports.patch: 29f7b376d399 Revert "scsi: libfc: Add WARN_ON() when deleting rports"
# Patch62: 0001-net-crypto-set-sk-to-NULL-when-af_alg_release.patch: eb5e6869125f net: crypto set sk to NULL when af_alg_release.
# Patch63: 0001-xen-netback-fix-occasional-leak-of-grant-ref-mapping.patch: 947fc52b6bf4 xen-netback: fix occasional leak of grant ref mappings under memory pressure
# Patch64: 0002-xen-netback-don-t-populate-the-hash-cache-on-XenBus-.patch: e5e5840183de xen-netback: don't populate the hash cache on XenBus disconnect
# Patch65: 0001-gfs2-Fix-missed-wakeups-in-find_insert_glock.patch: 4f5a4c888106 gfs2: Fix missed wakeups in find_insert_glock
Patch66: 0001-gfs2-Fix-an-incorrect-gfs2_assert.patch
Patch67: 0001-ACPI-APEI-Fix-possible-out-of-bounds-access-to-BERT-.patch
# Patch68: 0001-efi-cper-Fix-possible-out-of-bounds-access.patch: d60f458e4c4d efi: cper: Fix possible out-of-bounds access
Patch69: 0001-gfs-no-need-to-check-return-value-of-debugfs_create-.patch
# Patch70: 0001-scsi-iscsi-flush-running-unbind-operations-when-remo.patch: a629c32ac2d1 scsi: iscsi: flush running unbind operations when removing a session
# Patch71: 0001-xen-Prevent-buffer-overflow-in-privcmd-ioctl.patch: ed3adb562fc8 xen: Prevent buffer overflow in privcmd ioctl
# Patch72: 0001-Revert-scsi-fcoe-clear-FC_RP_STARTED-flags-when-rece.patch: ee4b8e266229 Revert "scsi: fcoe: clear FC_RP_STARTED flags when receiving a LOGO"
# Patch73: 0001-gfs2-Fix-lru_count-going-negative.patch: bac852089281 gfs2: Fix lru_count going negative
Patch74: 0002-gfs2-clean_journal-improperly-set-sd_log_flush_head.patch
# Patch75: 0003-gfs2-Fix-occasional-glock-use-after-free.patch: c4b51dbcccfc gfs2: Fix occasional glock use-after-free
# Patch76: 0001-gfs2-Replace-gl_revokes-with-a-GLF-flag.patch: don't apply, it gets reverted down the line as Patch94.
Patch77: 0005-gfs2-Remove-misleading-comments-in-gfs2_evict_inode.patch
Patch78: 0001-gfs2-Rename-sd_log_le_-revoke-ordered-rebase-325.patch
Patch79: 0007-gfs2-Rename-gfs2_trans_-add_unrevoke-remove_revoke.patch
Patch80: 0001-iomap-Clean-up-__generic_write_end-calling.patch
Patch81: 0002-fs-Turn-__generic_write_end-into-a-void-function.patch
Patch82: 0003-iomap-Fix-use-after-free-error-in-page_done-callback.patch
Patch83: 0004-iomap-Add-a-page_prepare-callback.patch
Patch84: 0008-gfs2-Fix-iomap-write-page-reclaim-deadlock.patch
Patch85: 0001-fs-mark-expected-switch-fall-throughs.patch
Patch86: 0001-gfs2-Fix-loop-in-gfs2_rbm_find-v2.patch
Patch87: 0001-gfs2-Remove-unnecessary-extern-declarations.patch
Patch88: 0001-gfs2-fix-race-between-gfs2_freeze_func-and-unmount.patch
Patch89: 0001-gfs2-read-journal-in-large-chunks.patch
Patch90: 0001-gfs2-Fix-error-path-kobject-memory-leak.patch
Patch91: 0009-SUNRPC-Ensure-that-the-transport-layer-respect-major.patch
Patch92: 0001-SUNRPC-Start-the-first-major-timeout-calculation-at-rebase-325.patch
# Patch93: 0001-gfs2-Fix-sign-extension-bug-in-gfs2_update_stats.patch: fdc78eedc54d gfs2: Fix sign extension bug in gfs2_update_stats
# Patch94: 0001-Revert-gfs2-Replace-gl_revokes-with-a-GLF-flag.patch: don't revert, simply remove the apply from Patch76
Patch95: 0001-gfs2-Fix-rounding-error-in-gfs2_iomap_page_prepare.patch
Patch96: 0001-iomap-don-t-mark-the-inode-dirty-in-iomap_write_end.patch
Patch97: 0001-gfs2-Clean-up-freeing-struct-gfs2_sbd.patch
Patch98: 0001-gfs2-Use-IS_ERR_OR_NULL.patch
Patch99: 0001-gfs2-kthread-and-remount-improvements.patch
Patch100: 0001-gfs2-eliminate-tr_num_revoke_rm.patch
Patch101: 0001-gfs2-log-which-portion-of-the-journal-is-replayed.patch
Patch102: 0001-gfs2-Warn-when-a-journal-replay-overwrites-a-rgrp-wi.patch
Patch103: 0001-gfs2-Rename-SDF_SHUTDOWN-to-SDF_WITHDRAWN.patch
Patch104: 0001-gfs2-simplify-gfs2_freeze-by-removing-case.patch
Patch105: 0001-gfs2-dump-fsid-when-dumping-glock-problems.patch
Patch106: 0001-gfs2-replace-more-printk-with-calls-to-fs_info-and-f.patch
Patch107: 0001-gfs2-use-page_offset-in-gfs2_page_mkwrite.patch
Patch108: 0001-gfs2-remove-the-unused-gfs2_stuffed_write_end-functi.patch
Patch109: 0001-gfs2-merge-gfs2_writeback_aops-and-gfs2_ordered_aops.patch
Patch110: 0001-gfs2-merge-gfs2_writepage_common-into-gfs2_writepage.patch
Patch111: 0001-gfs2-mark-stuffed_readpage-static.patch
Patch112: 0001-gfs2-use-iomap_bmap-instead-of-generic_block_bmap.patch
Patch113: 0001-gfs2-don-t-use-buffer_heads-in-gfs2_allocate_page_ba.patch
Patch114: 0001-gfs2-Remove-unused-gfs2_iomap_alloc-argument.patch
# Patch115: 0001-dlm-check-if-workqueues-are-NULL-before-flushing-des.patch: e7a41b276974 dlm: check if workqueues are NULL before flushing/destroying
Patch116: 0001-dlm-no-need-to-check-return-value-of-debugfs_create-.patch
Patch117: 0001-gfs2-Inode-dirtying-fix.patch
# Patch118: 0001-gfs2-gfs2_walk_metadata-fix.patch: 21344f0575f0 gfs2: gfs2_walk_metadata fix
# Patch119: 0001-nbd-add-missing-config-put.patch: d093d3183ca2 nbd: add missing config put
# Patch120: 0001-xen-pci-reserve-MCFG-areas-earlier.patch: 2bc2a90a083a xen/pci: reserve MCFG areas earlier
# Patch121: 0001-kernel-module.c-Only-return-EEXIST-for-modules-that-.patch: 09ec6c6783ff kernel/module.c: Only return -EEXIST for modules that have finished loading
# Patch122: 0001-net-mlx5e-Force-CHECKSUM_UNNECESSARY-for-short-ether.patch: b72ea6ec83be net/mlx5e: Force CHECKSUM_UNNECESSARY for short ethernet frames
# Patch123: 0001-net-mlx4_en-Force-CHECKSUM_NONE-for-short-ethernet-f.patch: 4190a7bcd2af net/mlx4_en: Force CHECKSUM_NONE for short ethernet frames
# Patch124: 0001-cifs-allow-calling-SMB2_xxx_free-NULL.patch: b4d965a37d89 cifs: allow calling SMB2_xxx_free(NULL)
# Patch125: 0001-random-add-a-spinlock_t-to-struct-batched_entropy.patch: 944c58523731 random: add a spinlock_t to struct batched_entropy
# Patch126: 0001-tcp-limit-payload-size-of-sacked-skbs.patch: c09be31461ed tcp: limit payload size of sacked skbs
# Patch127: 0002-tcp-tcp_fragment-should-apply-sane-memory-limits.patch: ec83921899a5 tcp: tcp_fragment() should apply sane memory limits
# Patch128: 0003-tcp-add-tcp_min_snd_mss-sysctl.patch: 7f9f8a37e563 tcp: add tcp_min_snd_mss sysctl
# Patch129: 0004-tcp-enforce-tcp_min_snd_mss-in-tcp_mtu_probing.patch: 59222807fcc9 tcp: enforce tcp_min_snd_mss in tcp_mtu_probing()
# Patch130: 0001-tcp-refine-memory-limit-test-in-tcp_fragment.patch: dad3a9314ac9 tcp: refine memory limit test in tcp_fragment()
# Patch131: 0002-xen-events-fix-binding-user-event-channels-to-cpus.patch: 007e5aaf287c xen/events: fix binding user event channels to cpus
# Patch132: 0003-xen-let-alloc_xenballooned_pages-fail-if-not-enough-.patch: e73db096691e xen: let alloc_xenballooned_pages() fail if not enough memory free
# Patch133: 0001-tcp-be-more-careful-in-tcp_fragment.patch: 6323c238bb43 tcp: be more careful in tcp_fragment()
# Patch134: 0001-random-always-use-batched-entropy-for-get_random_u-3.patch: 259f9d9a290e random: always use batched entropy for get_random_u{32,64}
# Patch135: 0001-xen-blkback-set-ring-xenblkd-to-NULL-after-kthread_s.patch: 014ee1c7d184 xen-blkback: set ring->xenblkd to NULL after kthread_stop()
# Patch136: 0001-block-cleanup-__blkdev_issue_discard.patch: b0be61a5a59e block: cleanup __blkdev_issue_discard()
# Patch137: 0001-block-fix-32-bit-overflow-in-__blkdev_issue_discard.patch: f387897cf5b8 block: fix 32 bit overflow in __blkdev_issue_discard()
# Patch138: 0001-scsi-libiscsi-Fix-race-between-iscsi_xmit_task-and-i.patch: 3491857f4292 scsi: libiscsi: Fix race between iscsi_xmit_task and iscsi_complete_task
# Patch139: 0001-xen-netback-Reset-nr_frags-before-freeing-skb.patch: b3410f0f8505 xen/netback: Reset nr_frags before freeing skb
# Patch140: 0001-openvswitch-change-type-of-UPCALL_PID-attribute-to-N.patch: 99952b08537c openvswitch: change type of UPCALL_PID attribute to NLA_UNSPEC
Patch141: 0001-gfs2-gfs2_iomap_begin-cleanup.patch
Patch142: 0001-gfs2-Add-support-for-IOMAP_ZERO.patch
Patch143: 0001-gfs2-implement-gfs2_block_zero_range-using-iomap_zer.patch
Patch144: 0001-gfs2-Minor-gfs2_alloc_inode-cleanup.patch
Patch145: 0001-gfs2-Always-mark-inode-dirty-in-fallocate.patch
Patch146: 0001-gfs2-untangle-the-logic-in-gfs2_drevalidate.patch
Patch147: 0001-gfs2-Fix-possible-fs-name-overflows.patch
Patch148: 0001-gfs2-Fix-recovery-slot-bumping.patch
Patch149: 0001-gfs2-Minor-PAGE_SIZE-arithmetic-cleanups.patch
Patch150: 0001-gfs2-Delete-an-unnecessary-check-before-brelse.patch
Patch151: 0001-gfs2-separate-holder-for-rgrps-in-gfs2_rename.patch
Patch152: 0001-gfs2-create-function-gfs2_glock_update_hold_time.patch
Patch153: 0001-gfs2-Use-async-glocks-for-rename.patch
Patch154: 0001-gfs2-Improve-mmap-write-vs.-truncate-consistency.patch
# Patch155: 0001-gfs2-clear-buf_in_tr-when-ending-a-transaction-in-sw.patch: e0c1e6e55bca gfs2: clear buf_in_tr when ending a transaction in sweep_bh_for_rgrps
# Patch156: 0001-xen-efi-Set-nonblocking-callbacks.patch: 90a886b68faa xen/efi: Set nonblocking callbacks
# Patch157: 0001-net-fix-sk_page_frag-recursion-from-memory-reclaim.patch: 1d5cb12a2539 net: fix sk_page_frag() recursion from memory reclaim
Patch158: 0001-drm-i915-gvt-Allow-F_CMD_ACCESS-on-mmio-0x21f0.patch
Patch159: 0001-gfs2-add-compat_ioctl-support.patch
Patch160: 0001-gfs2-removed-unnecessary-semicolon.patch
Patch161: 0001-gfs2-Some-whitespace-cleanups.patch
Patch162: 0001-gfs2-Improve-mmap-write-vs.-punch_hole-consistency.patch
Patch163: 0001-gfs2-Multi-block-allocations-in-gfs2_page_mkwrite.patch
Patch164: 0001-gfs2-Fix-end-of-file-handling-in-gfs2_page_mkwrite.patch
Patch165: 0001-gfs2-Remove-active-journal-side-effect-from-gfs2_wri.patch
Patch166: 0001-gfs2-make-gfs2_log_shutdown-static.patch
# Patch167: 0001-gfs2-fix-glock-reference-problem-in-gfs2_trans_remov.patch: 0809e1087c3d gfs2: fix glock reference problem in gfs2_trans_remove_revoke
Patch168: 0001-gfs2-Introduce-function-gfs2_withdrawn.patch
Patch169: 0001-gfs2-fix-infinite-loop-in-gfs2_ail1_flush-on-io-erro.patch
Patch170: 0001-gfs2-Don-t-loop-forever-in-gfs2_freeze-if-withdrawn.patch
Patch171: 0001-gfs2-Abort-gfs2_freeze-if-io-error-is-seen.patch
Patch172: 0001-gfs2-Close-timing-window-with-GLF_INVALIDATE_IN_PROG.patch
# Patch173: 0001-gfs2-clean-up-iopen-glock-mess-in-gfs2_create_inode.patch: 19709adfd7cd gfs2: clean up iopen glock mess in gfs2_create_inode
Patch174: 0001-gfs2-Remove-duplicate-call-from-gfs2_create_inode.patch
Patch175: 0001-gfs2-Don-t-write-log-headers-after-file-system-withd.patch
Patch176: 0001-xen-events-remove-event-handling-recursion-detection-rebase-325.patch
Patch177: 0001-gfs2-Another-gfs2_find_jhead-fix.patch
Patch178: 0001-gfs2-eliminate-ssize-parameter-from-gfs2_struct2blk.patch
Patch179: 0001-gfs2-minor-cleanup-remove-unneeded-variable-ret-in-g.patch
Patch180: 0001-gfs2-Avoid-access-time-thrashing-in-gfs2_inode_looku.patch
Patch181: 0001-gfs2-Fix-incorrect-variable-name.patch
Patch182: 0001-gfs2-Remove-GFS2_MIN_LVB_SIZE-define.patch
Patch183: 0001-fs-gfs2-remove-unused-IS_DINODE-and-IS_LEAF-macros.patch
Patch184: 0001-gfs2-remove-unused-LBIT-macros.patch
Patch185: 0001-Revert-gfs2-eliminate-tr_num_revoke_rm.patch
Patch186: 0001-gfs2-fix-gfs2_find_jhead-that-returns-uninitialized-.patch
# Patch187: 0001-gfs2-move-setting-current-backing_dev_info.patch: e57e77e9321c gfs2: move setting current->backing_dev_info
# Patch188: 0001-gfs2-fix-O_SYNC-write-handling.patch: 4b67a516c63d gfs2: fix O_SYNC write handling
Patch189: 0001-drm-i915-gvt-fix-high-order-allocation-failure-on-la.patch
Patch190: 0001-drm-i915-gvt-Add-mutual-lock-for-ppgtt-mm-LRU-list.patch
Patch191: 0002-drm-i915-gvt-more-locking-for-ppgtt-mm-LRU-list.patch
# Patch192: 0001-xenbus-req-body-should-be-updated-before-req-state.patch: d0f7d0913862 xenbus: req->body should be updated before req->state
# Patch193: 0002-xenbus-req-err-should-be-updated-before-req-state.patch: c4e8290c6fdf xenbus: req->err should be updated before req->state
# Patch194: 0001-gfs2_atomic_open-fix-O_EXCL-O_CREAT-handling-on-cold.patch: 777179200cb8 gfs2_atomic_open(): fix O_EXCL|O_CREAT handling on cold dcache
Patch195: 0001-gfs2-Split-gfs2_lm_withdraw-into-two-functions.patch
Patch196: 0001-gfs2-Report-errors-before-withdraw.patch
Patch197: 0001-gfs2-Remove-usused-cluster_wide-arguments-of-gfs2_co.patch
Patch198: 0001-gfs2-Turn-gfs2_consist-into-void-functions.patch
Patch199: 0001-gfs2-Return-bool-from-gfs2_assert-functions.patch
Patch200: 0001-gfs2-Introduce-concept-of-a-pending-withdraw.patch
Patch201: 0001-gfs2-clear-ail1-list-when-gfs2-withdraws.patch
Patch202: 0001-gfs2-Rework-how-rgrp-buffer_heads-are-managed.patch
Patch203: 0001-gfs2-log-error-reform.patch
Patch204: 0001-gfs2-Only-complain-the-first-time-an-io-error-occurs.patch
Patch205: 0001-gfs2-Ignore-dlm-recovery-requests-if-gfs2-is-withdra.patch
Patch206: 0001-gfs2-move-check_journal_clean-to-util.c-for-future-u.patch
Patch207: 0001-gfs2-Allow-some-glocks-to-be-used-during-withdraw.patch
Patch208: 0001-gfs2-Force-withdraw-to-replay-journals-and-wait-for-.patch
Patch209: 0001-gfs2-fix-infinite-loop-when-checking-ail-item-count-.patch
Patch210: 0001-gfs2-Add-verbose-option-to-check_journal_clean.patch
Patch211: 0001-gfs2-Issue-revokes-more-intelligently.patch
Patch212: 0001-gfs2-Prepare-to-withdraw-as-soon-as-an-IO-error-occu.patch
Patch213: 0001-gfs2-Check-for-log-write-errors-before-telling-dlm-t.patch
Patch214: 0001-gfs2-Do-log_flush-in-gfs2_ail_empty_gl-even-if-ail-l.patch
Patch215: 0001-gfs2-Withdraw-in-gfs2_ail1_flush-if-write_cache_page.patch
Patch216: 0001-gfs2-drain-the-ail2-list-after-io-errors.patch
# Patch217: 0001-gfs2-Don-t-demote-a-glock-until-its-revokes-are-writ.patch: 09f8ac747f36 gfs2: Don't demote a glock until its revokes are written
Patch218: 0001-gfs2-Do-proper-error-checking-for-go_sync-family-of-.patch
Patch219: 0001-gfs2-flesh-out-delayed-withdraw-for-gfs2_log_flush.patch
Patch220: 0001-gfs2-don-t-allow-releasepage-to-free-bd-still-used-f.patch
Patch221: 0001-gfs2-allow-journal-replay-to-hold-sd_log_flush_lock.patch
Patch222: 0001-gfs2-leaf_dealloc-needs-to-allocate-one-more-revoke.patch
Patch223: 0001-gfs2-Additional-information-when-gfs2_ail1_flush-wit.patch
Patch224: 0001-gfs2-Clean-up-inode-initialization-and-teardown.patch
Patch225: 0001-gfs2-Switch-to-list_-first-last-_entry.patch
Patch226: 0001-gfs2-eliminate-gfs2_rsqa_alloc-in-favor-of-gfs2_qa_a.patch
Patch227: 0001-gfs2-Change-inode-qa_data-to-allow-multiple-users.patch
Patch228: 0001-gfs2-Split-gfs2_rsqa_delete-into-gfs2_rs_delete-and-.patch
Patch229: 0001-gfs2-Remove-unnecessary-gfs2_qa_-get-put-pairs.patch
Patch230: 0001-gfs2-don-t-lock-sd_log_flush_lock-in-try_rgrp_unlink.patch
Patch231: 0001-gfs2-instrumentation-wrt-ail1-stuck.patch
Patch232: 0001-gfs2-change-from-write-to-read-lock-for-sd_log_flush.patch
Patch233: 0001-gfs2-Fix-oversight-in-gfs2_ail1_flush.patch
Patch234: 0001-gfs2-If-go_sync-returns-error-withdraw-but-skip-inva.patch
Patch235: 0001-dlm-Switch-to-using-wait_event.patch
Patch236: 0001-dlm-use-the-tcp-version-of-accept_from_sock-for-sctp.patch
Patch237: 0002-net-add-sock_set_reuseaddr.patch
Patch238: 0003-net-add-sock_set_sndtimeo.patch
Patch239: 0004-net-add-sock_set_keepalive.patch
Patch240: 0005-net-add-sock_set_rcvbuf.patch
Patch241: 0006-tcp-add-tcp_sock_set_nodelay.patch
Patch242: 0001-sctp-add-sctp_sock_set_nodelay-rebased-325.patch
Patch243: 0009-dlm-dlm_internal-Replace-zero-length-array-with-flex.patch
Patch244: 0010-dlm-user-Replace-zero-length-array-with-flexible-arr.patch
Patch245: 0011-fs-dlm-remove-unneeded-semicolon-in-rcom.c.patch
# Patch246: 0012-dlm-remove-BUG-before-panic.patch: 68728008569c dlm: remove BUG() before panic()
Patch247: 0001-gfs2-fix-withdraw-sequence-deadlock.patch
Patch248: 0001-gfs2-Fix-error-exit-in-do_xmote.patch
Patch249: 0001-gfs2-Fix-BUG-during-unmount-after-file-system-withdr.patch
Patch250: 0001-gfs2-Fix-use-after-free-in-gfs2_logd-after-withdraw.patch
# Patch251: 0001-block-call-rq_qos_exit-after-queue-is-frozen.patch: 9663d294ae28 block: call rq_qos_exit() after queue is frozen
# Patch252: 0001-scsi-libfc-free-response-frame-from-GPN_ID.patch: 8343dffacc1b scsi: libfc: free response frame from GPN_ID
# Patch253: 0001-xen-xenbus-ensure-xenbus_map_ring_valloc-returns-pro.patch: 41722344981f xen/xenbus: ensure xenbus_map_ring_valloc() returns proper grant status
# Patch254: 0013-treewide-Remove-uninitialized_var-usage.patch: b7e389235cfe treewide: Remove uninitialized_var() usage
# Patch255: 0014-dlm-Fix-kobject-memleak.patch: 6a2db034f9b3 dlm: Fix kobject memleak
Patch256: 0001-net-sock-add-sock_set_mark.patch
Patch257: 0015-fs-dlm-set-skb-mark-for-listen-socket.patch
Patch258: 0016-fs-dlm-set-skb-mark-per-peer-socket.patch
Patch259: 0017-fs-dlm-don-t-close-socket-on-invalid-message.patch
Patch260: 0018-fs-dlm-change-handling-of-reconnects.patch
Patch261: 0019-fs-dlm-implement-tcp-graceful-shutdown.patch
# Patch262: 0001-ext4-fix-potential-negative-array-index-in-do_split.patch: TODO add upstream commit
Patch263: 0021-fs-dlm-synchronize-dlm-before-shutdown.patch
Patch264: 0022-fs-dlm-make-connection-hash-lockless.patch
Patch265: 0023-fs-dlm-fix-dlm_local_addr-memory-leak.patch
# Patch266: 0024-fs-dlm-fix-configfs-memory-leak.patch: 13296b64a81c fs: dlm: fix configfs memory leak
Patch267: 0025-fs-dlm-move-free-writequeue-into-con-free.patch
Patch268: 0026-fs-dlm-handle-possible-othercon-writequeues.patch
Patch269: 0027-fs-dlm-use-free_con-to-free-connection.patch
Patch270: 0028-fs-dlm-remove-lock-dependency-warning.patch
Patch271: 0029-fs-dlm-fix-mark-per-nodeid-setting.patch
Patch272: 0030-fs-dlm-handle-range-check-as-callback.patch
Patch273: 0031-fs-dlm-disallow-buffer-size-below-default.patch
Patch274: 0001-fs-dlm-rework-receive-handling-rebased-325.patch
Patch275: 0033-fs-dlm-fix-race-in-nodeid2con.patch
# TODELETE Patch275: 0001-xen-events-avoid-removing-an-event-channel-while-han.patch: 61d359d51a1c xen/events: avoid removing an event channel while handling it
# Patch277: 0002-xen-events-add-a-proper-barrier-to-2-level-uevent-un.patch: 25f6b08895d5 xen/events: add a proper barrier to 2-level uevent unmasking
# Patch278: 0003-xen-events-fix-race-in-evtchn_fifo_unmask.patch: c7f95d899f49 xen/events: fix race in evtchn_fifo_unmask()
# Patch279: 0004-xen-events-add-a-new-late-EOI-evtchn-framework.patch: dea09436da03 xen/events: add a new "late EOI" evtchn framework
# Patch280: 0005-xen-blkback-use-lateeoi-irq-binding.patch: 1506109a85c8 xen/blkback: use lateeoi irq binding
# Patch281: 0006-xen-netback-use-lateeoi-irq-binding.patch: 6a052f3a6282 xen/netback: use lateeoi irq binding
# Patch282: 0007-xen-scsiback-use-lateeoi-irq-binding.patch: fb22061b20ea xen/scsiback: use lateeoi irq binding
# Patch283: 0008-xen-pvcallsback-use-lateeoi-irq-binding.patch: 128b11967a26 xen/pvcallsback: use lateeoi irq binding
# Patch284: 0009-xen-pciback-use-lateeoi-irq-binding.patch: 4988884d53c0 xen/pciback: use lateeoi irq binding
# Patch285: 0010-xen-events-switch-user-event-channels-to-lateeoi-mod.patch: 8363670c4d0b xen/events: switch user event channels to lateeoi model
# Patch286: 0011-xen-events-use-a-common-cpu-hotplug-hook-for-event-c.patch: 536075098940 xen/events: use a common cpu hotplug hook for event channels
# Patch287: 0012-xen-events-defer-eoi-in-case-of-excessive-number-of-.patch: 17ef715c0c88 xen/events: defer eoi in case of excessive number of events
# Patch288: 0013-xen-events-block-rogue-events-for-some-time.patch: c1f90a9cd988 xen/events: block rogue events for some time
Patch289: 0014-xen-events-unmask-a-fifo-event-channel-only-if-it-wa.patch
Patch290: 0034-fs-dlm-fix-proper-srcu-api-call.patch
Patch291: 0035-fs-dlm-define-max-send-buffer.patch
Patch292: 0036-fs-dlm-add-get-buffer-error-handling.patch
Patch293: 0037-fs-dlm-flush-othercon-at-close.patch
Patch294: 0038-fs-dlm-handle-non-blocked-connect-event.patch
Patch295: 0039-fs-dlm-add-helper-for-init-connection.patch
Patch296: 0040-fs-dlm-move-connect-callback-in-node-creation.patch
Patch297: 0041-fs-dlm-move-shutdown-action-to-node-creation.patch
Patch298: 0042-fs-dlm-refactor-sctp-sock-parameter.patch
Patch299: 0043-fs-dlm-listen-socket-out-of-connection-hash.patch
Patch300: 0044-fs-dlm-fix-check-for-multi-homed-hosts.patch
Patch301: 0045-fs-dlm-constify-addr_compare.patch
Patch302: 0046-fs-dlm-check-on-existing-node-address.patch
# Patch303: 0001-xen-netback-avoid-race-in-xenvif_rx_ring_slots_avail.patch: 7740c404d068 xen/netback: avoid race in xenvif_rx_ring_slots_available()
# Patch304: 0001-Xen-x86-don-t-bail-early-from-clear_foreign_p2m_mapp.patch: dfed59ee4b41 Xen/x86: don't bail early from clear_foreign_p2m_mapping()
# Patch305: 0001-Xen-x86-also-check-kernel-mapping-in-set_foreign_p2m.patch: c3d586afdb44 Xen/x86: also check kernel mapping in set_foreign_p2m_mapping()
# Patch306: 0001-Xen-gntdev-correct-dev_bus_addr-handling-in-gntdev_m.patch: ba75f4393225 Xen/gntdev: correct dev_bus_addr handling in gntdev_map_grant_pages()
# Patch307: 0001-Xen-gntdev-correct-error-checking-in-gntdev_map_gran.patch: e07f06f6bbee Xen/gntdev: correct error checking in gntdev_map_grant_pages()
# Patch308: 0001-xen-blkback-don-t-handle-error-by-BUG.patch: a01b49a9bf91 xen-blkback: don't "handle" error by BUG()
# Patch309: 0001-xen-netback-don-t-handle-error-by-BUG.patch: 717faa776ca2 xen-netback: don't "handle" error by BUG()
# Patch310: 0001-xen-scsiback-don-t-handle-error-by-BUG.patch: f84c00fbd27b xen-scsiback: don't "handle" error by BUG()
# Patch311: 0001-xen-blkback-fix-error-handling-in-xen_blkbk_map.patch: 98f16e171e28 xen-blkback: fix error handling in xen_blkbk_map()
# Patch312: 0001-xen-netback-fix-spurious-event-detection-for-common-.patch: 135ba06d0bf8 xen/netback: fix spurious event detection for common event case
Patch313: 0007-xen-evtchn-use-smp-barriers-for-user-event-ring.patch
Patch314: 0008-xen-evtchn-use-READ-WRITE_ONCE-for-accessing-ring-in.patch
# Patch315: xen-events-reset-affinity-of-2-level-event-when-tearing-it-down.patch: a6a76d7234cc xen/events: reset affinity of 2-level event when tearing it down
# Patch316: xen-events-don-t-unmask-an-event-channel-when-an-eoi-is-pending.patch: 3a19f808cb2b xen/events: don't unmask an event channel when an eoi is pending
# Patch317: xen-events-avoid-handling-the-same-event-on-two-cpus-at-the-same-time.patch: d8887e85efca xen/events: avoid handling the same event on two cpus at the same time
Patch318: 0001-x86-ioperm-Add-new-paravirt-function-update_io_bitma.patch
# Patch319: 0001-Xen-gnttab-handle-p2m-update-errors-on-a-per-slot-ba.patch: 1a999d25ef53 Xen/gnttab: handle p2m update errors on a per-slot basis
# Patch320: 0002-xen-netback-respect-gnttab_map_refs-s-return-value.patch: b62d8b5c814b xen-netback: respect gnttab_map_refs()'s return value
# Patch321: 0001-xen-blkback-don-t-leak-persistent-grants-from-xen_bl.patch: 16356ddb5878 xen-blkback: don't leak persistent grants from xen_blkbk_map()
# Patch322: 0001-bpf-x86-Validate-computation-of-branch-displacements.patch: 5f26f1f838aa bpf, x86: Validate computation of branch displacements for x86-64
# Patch323: 0002-bpf-x86-Validate-computation-of-branch-displacements.patch: 7b77ae2a0d6f bpf, x86: Validate computation of branch displacements for x86-32
# Patch324: 0001-xen-events-fix-setting-irq-affinity.patch: d9ab90118cf9 xen/events: fix setting irq affinity
# Patch325: 0001-xen-netback-fix-rx-queue-stall-detection.patch: 1de7644eac41 xen/netback: fix rx queue stall detection
# Patch326: 0002-xen-netback-don-t-queue-unlimited-number-of-packages.patch: c9f17e92917f xen/netback: don't queue unlimited number of packages
# Patch327: 0047-fs-dlm-fix-debugfs-dump.patch: 2efaecaf9603 fs: dlm: fix debugfs dump
Patch328: 0048-fs-dlm-fix-mark-setting-deadlock.patch
Patch329: 0049-fs-dlm-set-connected-bit-after-accept.patch
Patch330: 0050-fs-dlm-set-subclass-for-othercon-sock_mutex.patch
Patch331: 0051-fs-dlm-add-errno-handling-to-check-callback.patch
Patch332: 0052-fs-dlm-add-check-if-dlm-is-currently-running.patch
Patch333: 0053-fs-dlm-change-allocation-limits.patch
Patch334: 0054-fs-dlm-use-GFP_ZERO-for-page-buffer.patch
Patch335: 0055-fs-dlm-simplify-writequeue-handling.patch
Patch336: 0056-fs-dlm-check-on-minimum-msglen-size.patch
Patch337: 0057-fs-dlm-remove-unaligned-memory-access-handling.patch
Patch338: 0058-fs-dlm-flush-swork-on-shutdown.patch
Patch339: 0059-fs-dlm-add-shutdown-hook.patch
Patch340: 0060-fs-dlm-fix-missing-unlock-on-error-in-accept_from_so.patch
# Patch341: 0001-xen-events-reset-active-flag-for-lateeoi-events-late.patch: cda326e5033f xen/events: reset active flag for lateeoi events later
Patch342: 0001-gfs2-fix-a-deadlock-on-withdraw-during-mount.patch
Patch343: 0061-fs-dlm-always-run-complete-for-possible-waiters.patch
Patch344: 0062-fs-dlm-add-dlm-macros-for-ratelimit-log.patch
Patch345: 0063-fs-dlm-fix-srcu-read-lock-usage.patch
Patch346: 0064-fs-dlm-set-is-othercon-flag.patch
Patch347: 0065-fs-dlm-reconnect-if-socket-error-report-occurs.patch
# Patch348: 0066-fs-dlm-cancel-work-sync-othercon.patch: d5473f43e4fb fs: dlm: cancel work sync othercon
Patch349: 0067-fs-dlm-fix-connection-tcp-EOF-handling.patch
Patch350: 0068-fs-dlm-public-header-in-out-utility.patch
Patch351: 0069-fs-dlm-add-more-midcomms-hooks.patch
Patch352: 0070-fs-dlm-make-buffer-handling-per-msg.patch
Patch353: 0071-fs-dlm-add-functionality-to-re-transmit-a-message.patch
Patch354: 0072-fs-dlm-move-out-some-hash-functionality.patch
Patch355: 0073-fs-dlm-add-union-in-dlm-header-for-lockspace-id.patch
Patch356: 0074-fs-dlm-add-reliable-connection-if-reconnect.patch
Patch357: 0075-fs-dlm-add-midcomms-debugfs-functionality.patch
Patch358: 0076-fs-dlm-don-t-allow-half-transmitted-messages.patch
Patch359: 0077-fs-dlm-Fix-memory-leak-of-object-mh.patch
Patch360: 0078-fs-dlm-Fix-spelling-mistake-stucked-stuck.patch
Patch361: 0079-fs-dlm-fix-lowcomms_start-error-case.patch
# Patch362: 0080-fs-dlm-fix-memory-leak-when-fenced.patch: af02ec6cf614 fs: dlm: fix memory leak when fenced
Patch363: 0081-fs-dlm-use-alloc_ordered_workqueue.patch
Patch364: 0082-fs-dlm-move-dlm-allow-conn.patch
Patch365: 0083-fs-dlm-introduce-proto-values.patch
Patch366: 0084-fs-dlm-rename-socket-and-app-buffer-defines.patch
Patch367: 0085-fs-dlm-fix-race-in-mhandle-deletion.patch
Patch368: 0086-fs-dlm-invalid-buffer-access-in-lookup-error.patch
# Patch369: 0001-seq_file-disallow-extremely-large-seq-buffer-allocat.patch: 6de9f0bf7cac seq_file: disallow extremely large seq buffer allocations
# Patch370: 0001-xen-events-Fix-race-in-set_evtchn_to_irq.patch: 387635925cd0 xen/events: Fix race in set_evtchn_to_irq
Patch371: 0087-fs-dlm-use-sk-sk_socket-instead-of-con-sock.patch
Patch372: 0088-fs-dlm-use-READ_ONCE-for-config-var.patch
Patch373: 0089-fs-dlm-fix-typo-in-tlv-prefix.patch
Patch374: 0090-fs-dlm-clear-CF_APP_LIMITED-on-close.patch
Patch375: 0091-fs-dlm-cleanup-and-remove-_send_rcom.patch
Patch376: 0092-fs-dlm-introduce-con_next_wq-helper.patch
Patch377: 0093-fs-dlm-move-to-static-proto-ops.patch
Patch378: 0094-fs-dlm-introduce-generic-listen.patch
Patch379: 0095-fs-dlm-auto-load-sctp-module.patch
Patch380: 0096-fs-dlm-generic-connect-func.patch
Patch381: 0097-fs-dlm-fix-multiple-empty-writequeue-alloc.patch
Patch382: 0098-fs-dlm-move-receive-loop-into-receive-handler.patch
Patch383: 0099-fs-dlm-implement-delayed-ack-handling.patch
Patch384: 0100-fs-dlm-fix-return-EINTR-on-recovery-stopped.patch
Patch385: 0101-fs-dlm-avoid-comms-shutdown-delay-in-release_lockspa.patch
# Patch386: 0001-iommu-vt-d-Fix-agaw-for-a-supported-48-bit-guest-add.patch: 6a9449e95688 iommu/vt-d: Fix agaw for a supported 48 bit guest address width
# Patch387: 0001-bpf-Do-not-use-ax-register-in-interpreter-on-div-mod.patch: c348d806ed1d bpf: Do not use ax register in interpreter on div/mod
# Patch388: 0002-bpf-Fix-32-bit-src-register-truncation-on-div-mod.patch: 8313432df224 bpf: Fix 32 bit src register truncation on div/mod
# Patch389: 0003-bpf-Fix-truncation-handling-for-mod32-dst-reg-wrt-ze.patch: 39f74b7c81cc bpf: Fix truncation handling for mod32 dst reg wrt zero
Patch390: 0001-x86-timer-Skip-PIT-initialization-on-modern-chipsets.patch
Patch391: 0001-x86-timer-Force-PIT-initialization-when-X86_FEATURE_.patch
Patch392: 0001-x86-timer-Don-t-skip-PIT-setup-when-APIC-is-disabled.patch
Patch393: 0001-nbd-Fix-use-after-free-in-pid_show-rebase-325.patch
Patch394: 0001-fs-dlm-remove-check-SCTP-is-loaded-message.patch
Patch395: 0001-fs-dlm-let-handle-callback-data-as-void.patch
Patch396: 0001-fs-dlm-remove-double-list_first_entry-call.patch
Patch397: 0001-fs-dlm-don-t-call-kernel_getpeername-in-error_report.patch
Patch398: 0001-fs-dlm-replace-use-of-socket-sk_callback_lock-with-s.patch
Patch399: 0001-fs-dlm-fix-build-with-CONFIG_IPV6-disabled.patch
Patch400: 0001-fs-dlm-check-for-pending-users-filling-buffers.patch
Patch401: 0001-fs-dlm-remove-wq_alloc-mutex.patch
Patch402: 0001-fs-dlm-memory-cache-for-writequeue_entry.patch
Patch403: 0001-fs-dlm-memory-cache-for-lowcomms-hotpath.patch
Patch404: 0001-fs-dlm-print-cluster-addr-if-non-cluster-node-connec.patch
Patch405: 0001-xen-x86-obtain-upper-32-bits-of-video-frame-buffer-a.patch
Patch406: 0001-xen-x86-obtain-full-video-frame-buffer-address-for-D.patch
Patch407: 0001-dlm-uninitialized-variable-on-error-in-dlm_listen_fo.patch
Patch408: 0001-dlm-add-__CHECKER__-for-false-positives.patch
Patch409: 0001-fs-dlm-fix-grammar-in-lowcomms-output.patch
Patch410: 0001-fs-dlm-fix-race-in-lowcomms.patch
Patch411: 0001-fs-dlm-relax-sending-to-allow-receiving.patch
Patch412: 0001-fs-dlm-fix-sock-release-if-listen-fails.patch
Patch413: 0002-fs-dlm-retry-accept-until-EAGAIN-or-error-returns.patch
Patch414: 0001-fs-dlm-remove-send-repeat-remove-handling-rebase-325.patch
# Patch415: 0001-xen-pvh-set-xen_domain_type-to-HVM-in-xen_pvh_init.patch: 756eda9bc8b7 xen/pvh: set xen_domain_type to HVM in xen_pvh_init
# Patch416: 0001-xen-pvh-correctly-setup-the-PV-EFI-interface-for-dom.patch: 0c47135536b8 xen/pvh: correctly setup the PV EFI interface for dom0
# Patch417: 0001-PCI-pciehp-Fix-AB-BA-deadlock-between-reset_lock-and.patch: 2a226e8ca951 PCI: pciehp: Fix AB-BA deadlock between reset_lock and device_lock
Patch418: 0001-nvme_fc-add-nvme_discovery-sysfs-attribute-to-fc-tra-rebase-325.patch
Patch419: 0001-ACPI-processor-Fix-evaluating-_PDC-method-when-runni.patch
# Patch420: 0001-SUNRPC-Always-drop-the-XPRT_LOCK-on-XPRT_CLOSE_WAIT.patch: 2440f3cebcb0 SUNRPC: Always drop the XPRT_LOCK on XPRT_CLOSE_WAIT
# Patch421: 0001-xen-netback-use-default-TX-queue-size-for-vifs.patch: b42515434f8f xen-netback: use default TX queue size for vifs
Patch422: 0001-gfs2-Expect-EBUSY-after-canceling-dlm-locking-reques.patch
Patch423: 0001-gfs2-Clear-flags-when-withdraw-prevents-xmote.patch
# Patch424: 0002-fs-dlm-fix-race-between-test_bit-and-queue_work.patch: d1ae006b4851 fs: dlm: fix race between test_bit() and queue_work()
Patch425: 0001-xhci-show-fault-reason-for-a-failed-enable-slot-comm.patch
Patch426: 0001-gfs2-Fix-ignore-unlock-failures-after-withdraw.patch
Patch427: 0001-gfs2-finish_xmote-cleanup.patch
Patch428: 0001-gfs2-do_xmote-fixes.patch
Patch429: 0001-x86-xen-time-Reduce-Xen-timer-tick.patch
# Patch430: 0001-decompress_bunzip2-fix-rare-decompression-failure.patch: 16b92b031b4d decompress_bunzip2: fix rare decompression failure
# Patch431: 0002-scsi-scsi_dh_alua-Fix-possible-null-ptr-deref.patch: 89ede9d8b5b8 scsi: scsi_dh_alua: Fix possible null-ptr-deref
# Patch432: 0004-scsi-scsi_dh_alua-always-use-a-2-second-delay-before.patch: cdd92ebe29c2 scsi: scsi_dh_alua: always use a 2 second delay before retrying RTPG
# Patch433: 0005-scsi-scsi_dh_alua-handle-RTPG-sense-code-correctly-d.patch: cf372c60ed13 scsi: scsi_dh_alua: handle RTPG sense code correctly during state transitions
# Patch434: 0006-scsi-scsi_dh_alua-Avoid-crash-during-alua_bus_detach.patch: 509e215d161e scsi: scsi_dh_alua: Avoid crash during alua_bus_detach()
Patch435: 0008-scsi-scsi_dh_alua-Set-transitioning-state-on-Unit-At.patch
Patch436: 0009-scsi-scsi_dh_alua-Prevent-duplicate-pg-info-print-in.patch
# Patch437: 0010-scsi-scsi_dh_alua-Remove-check-for-ASC-24h-in-alua_r.patch: 5fc6e73ba502 scsi: scsi_dh_alua: Remove check for ASC 24h in alua_rtpg()
Patch438: 0012-scsi-scsi_dh_alua-Retry-RTPG-on-a-different-path-aft.patch
# Patch439: 0013-scsi-scsi_dh_alua-Check-for-negative-result-value.patch: f4bde1d1bf90 scsi: scsi_dh_alua: Check for negative result value
# Patch440: 0014-scsi-scsi_dh_alua-Fix-signedness-bug-in-alua_rtpg.patch: c021be62bbcb scsi: scsi_dh_alua: Fix signedness bug in alua_rtpg()
# Patch441: 0001-scsi-scsi_dh_alua-Fix-memleak-for-qdata-in-alua_acti.patch: c110051d335e scsi: scsi_dh_alua: Fix memleak for 'qdata' in alua_activate()
Patch442: 0001-scsi-core-alua-I-O-errors-for-ALUA-state-transitions.patch
Patch443: 0002-scsi-scsi_dh_alua-Properly-handle-the-ALUA-transitio.patch
Patch444: 0001-SUNRPC-Replace-direct-task-wakeups-from-softirq-cont-rebase-325.patch
Patch445: 0004-SUNRPC-Replace-the-queue-timer-with-a-delayed-work-f.patch
# Patch446: 0001-nbd-fix-possible-sysfs-duplicate-warning.patch: cad4448dfc9c nbd: fix possible sysfs duplicate warning
Patch447: 0007-SUNRPC-fix-race-to-sk_err-after-xs_error_report.patch
# Patch448: 0001-nbd-protect-cmd-status-with-cmd-lock.patch: 82b7c99ee141 nbd: protect cmd->status with cmd->lock
# Patch449: 0001-nbd-handle-racing-with-error-ed-out-commands.patch: 1f032ca298dd nbd: handle racing with error'ed out commands
Patch450: 0015-SUNRPC-Fix-backchannel-RPC-soft-lockups.patch
# Patch451: 0001-nbd-fix-a-block_device-refcount-leak-in-nbd_release.patch: d9f4534a9a28 nbd: fix a block_device refcount leak in nbd_release
Patch452: 0001-nbd-Aovid-double-completion-of-a-request-rebase-325.patch
Patch453: 0001-nbd-don-t-handle-response-without-a-corresponding-re.patch
Patch454: 0001-nbd-make-sure-request-completion-won-t-concurrent.patch
Patch455: 0001-cdc_ether-export-usbnet_cdc_zte_rx_fixup.patch
Patch456: 0001-rndis_host-enable-the-bogus-MAC-fixup-for-ZTE-device-rebased-cip134.patch
Patch457: 0003-rndis_host-limit-scope-of-bogus-MAC-address-detectio.patch
Patch458: 0001-SUNRPC-Move-reset-of-TCP-state-variables-into-the-re.patch
Patch459: 0001-nvme-fabrics-reject-I-O-to-offline-device-rebase-325.patch
Patch460: 0001-Add-shadow-variables-support-from-kpatch.patch
# Patch461: 0002-xen-xenbus-Allow-watches-discard-events-before-queue.patch: 9039eb22f995 xen/xenbus: Allow watches discard events before queueing
# Patch462: 0003-xen-xenbus-Add-will_handle-callback-support-in-xenbu.patch: 3a36e4af694a xen/xenbus: Add 'will_handle' callback support in xenbus_watch_path()
# Patch463: 0004-xen-xenbus-xen_bus_type-Support-will_handle-watch-ca.patch: b88c52d02e16 xen/xenbus/xen_bus_type: Support will_handle watch callback
# Patch464: 0005-xen-xenbus-Count-pending-messages-for-each-watch.patch: 85597c4369c9 xen/xenbus: Count pending messages for each watch
# Patch465: 0006-xenbus-xenbus_backend-Disallow-pending-watch-message.patch: be19047894c3 xenbus/xenbus_backend: Disallow pending watch messages
# Patch466: 0001-xen-xenbus-Fix-granting-of-vmalloc-d-memory.patch: 47eb291ba65b xen/xenbus: Fix granting of vmalloc'd memory
# Patch467: 0001-xen-blkfront-switch-kcalloc-to-kvcalloc-for-large-ar.patch: b9b75a460076 xen-blkfront: switch kcalloc to kvcalloc for large array allocation
# Patch468: 0002-xen-blkfront-Adjust-indentation-in-xlvbd_alloc_gendi.patch: 041497b65eb0 xen/blkfront: Adjust indentation in xlvbd_alloc_gendisk
# Patch469: 0003-xen-blkfront-fix-memory-allocation-flags-in-blkfront.patch: 5f547e7cbd84 xen/blkfront: fix memory allocation flags in blkfront_setup_indirect()
# Patch470: 0004-xen-blkfront-allow-discard-nodes-to-be-optional.patch: a4af550350cc xen-blkfront: allow discard-* nodes to be optional
# Patch471: 0001-xen-sync-include-xen-interface-io-ring.h-with-Xen-s-.patch: dcbfd3f13b13 xen: sync include/xen/interface/io/ring.h with Xen's newest version
# Patch472: 0005-xen-blkfront-read-response-from-backend-only-once.patch: b647c449f166 xen/blkfront: read response from backend only once
# Patch473: 0006-xen-blkfront-don-t-take-local-copy-of-a-request-from.patch: 80baa77511ee xen/blkfront: don't take local copy of a request from the ring page
# Patch474: 0007-xen-blkfront-don-t-trust-the-backend-response-data-b.patch: f89a05402f74 xen/blkfront: don't trust the backend response data blindly
# Patch475: 0008-xen-blkfront-harden-blkfront-against-event-channel-s.patch: 269d7124bcfa xen/blkfront: harden blkfront against event channel storms
# Patch476: 0001-xen-netfront-do-not-assume-sk_buff_head-list-is-empt.patch: 47288968eebd xen-netfront: do not assume sk_buff_head list is empty in error handling
# Patch477: 0002-xen-netfront-do-not-use-0U-as-error-return-value-for.patch: a1afd826e549 xen-netfront: do not use ~0U as error return value for xennet_fill_frags()
# Patch478: 0003-xen-netfront-fix-potential-deadlock-in-xennet_remove.patch: 4b635fc2b349 xen-netfront: fix potential deadlock in xennet_remove()
# Patch479: 0004-xen-netfront-stop-tx-queues-during-live-migration.patch: 274c04221d91 xen/netfront: stop tx queues during live migration
# Patch480: 0005-xen-netfront-read-response-from-backend-only-once.patch: e7d1024f5b19 xen/netfront: read response from backend only once
# Patch481: 0006-xen-netfront-don-t-read-data-from-request-on-the-rin.patch: 26509bb5dd2f xen/netfront: don't read data from request on the ring page
# Patch482: 0007-xen-netfront-disentangle-tx_skb_freelist.patch: e52c0efbd23c xen/netfront: disentangle tx_skb_freelist
# Patch483: 0008-xen-netfront-don-t-trust-the-backend-response-data-b.patch: e4e01b0e4b7f xen/netfront: don't trust the backend response data blindly
# Patch484: 0009-xen-netfront-harden-netfront-against-event-channel-s.patch: 3559ca594f15 xen/netfront: harden netfront against event channel storms
# Patch485: 0010-xen-netfront-destroy-queues-before-real_num_tx_queue.patch: 198cdc287769 xen/netfront: destroy queues before real_num_tx_queues is zeroed
# Patch486: 0001-pvcalls-front-read-all-data-before-closing-the-conne.patch: 9699f7a70eb8 pvcalls-front: read all data before closing the connection
# Patch487: 0002-pvcalls-front-don-t-try-to-free-unallocated-rings.patch: 81b8519de1b4 pvcalls-front: don't try to free unallocated rings
# Patch488: 0003-pvcalls-front-properly-allocate-sk.patch: 05ac8a683962 pvcalls-front: properly allocate sk
# Patch489: 0004-pvcalls-front-Avoid-get_free_pages-GFP_KERNEL-under-.patch: 06b919a51772 pvcalls-front: Avoid get_free_pages(GFP_KERNEL) under spinlock
# Patch490: 0005-pvcalls-front-fix-potential-null-dereference.patch: 642e26628cf9 pvcalls-front: fix potential null dereference
# Patch491: 0006-xen-pvcalls-Remove-set-but-not-used-variable.patch: 66f33b2bd2d8 xen/pvcalls: Remove set but not used variable
# Patch492: 0007-pvcalls-front-don-t-return-error-when-the-ring-is-fu.patch: 36a2e9bf242b pvcalls-front: don't return error when the ring is full
# Patch493: 0001-xen-xenbus-don-t-let-xenbus_grant_ring-remove-grants.patch: 8d521d960aef xen/xenbus: don't let xenbus_grant_ring() remove grants in error case
# Patch494: 0002-xen-grant-table-add-gnttab_try_end_foreign_access.patch: 17659846fe33 xen/grant-table: add gnttab_try_end_foreign_access()
# Patch495: 0003-xen-blkfront-don-t-use-gnttab_query_foreign_access-f.patch: 423a3a50dce9 xen/blkfront: don't use gnttab_query_foreign_access() for mapped status
# Patch496: 0004-xen-netfront-don-t-use-gnttab_query_foreign_access-f.patch: 927e4eb8ddf4 xen/netfront: don't use gnttab_query_foreign_access() for mapped status
# Patch497: 0005-xen-scsifront-don-t-use-gnttab_query_foreign_access-.patch: 62a696c15cfc xen/scsifront: don't use gnttab_query_foreign_access() for mapped status
# Patch498: 0006-xen-gntalloc-don-t-use-gnttab_query_foreign_access.patch: fbc57368ea52 xen/gntalloc: don't use gnttab_query_foreign_access()
# Patch499: 0007-xen-remove-gnttab_query_foreign_access.patch: c900f34fc134 xen: remove gnttab_query_foreign_access()
# Patch500: 0008-xen-9p-use-alloc-free_pages_exact.patch: 2466bed361f3 xen/9p: use alloc/free_pages_exact()
# Patch501: 0009-xen-pvcalls-use-alloc-free_pages_exact.patch: f85d03f0f482 xen/pvcalls: use alloc/free_pages_exact()
# Patch502: 0010-xen-gnttab-fix-gnttab_end_foreign_access-without-pag.patch: 92dc0e4a2196 xen/gnttab: fix gnttab_end_foreign_access() without page specified
# Patch503: 0011-xen-netfront-react-properly-to-failing-gnttab_end_fo.patch: c307029d811e xen/netfront: react properly to failing gnttab_end_foreign_access_ref()
# Patch504: 0001-xen-blkfront-fix-leaking-data-in-shared-pages.patch: f4a1391185e3 xen/blkfront: fix leaking data in shared pages
# Patch505: 0002-xen-netfront-fix-leaking-data-in-shared-pages.patch: 3650ac3218c1 xen/netfront: fix leaking data in shared pages
# Patch506: 0003-xen-netfront-force-data-bouncing-when-backend-is-unt.patch: 4b67d8e42dbb xen/netfront: force data bouncing when backend is untrusted
# Patch507: 0004-xen-blkfront-force-data-bouncing-when-backend-is-unt.patch: 981de55fb6b5 xen/blkfront: force data bouncing when backend is untrusted
# Patch508: xsa423-linux.patch: 44dfdecc288b xen/netback: Ensure protocol headers don't fall in the non-linear area
# Patch509: xsa424-linux.patch: d3e1b6151d5d xen/netback: don't call kfree_skb() with interrupts disabled
Patch510: 0002-xen-netback-remove-unused-variables-pending_idx-and-.patch
# Patch511: 0003-xen-netback-don-t-do-grant-copy-across-page-boundary.patch: e14369897067 xen/netback: don't do grant copy across page boundary
Patch512: 0004-xen-netback-remove-not-needed-test-in-xenvif_tx_buil.patch
# Patch513: 0005-xen-netback-use-same-error-messages-for-same-errors.patch: a5353cdecd9b xen/netback: use same error messages for same errors
# Patch514: xsa432-linux.patch: 11e6919ae028 xen/netback: Fix buffer overrun triggered by unusual packet
# Patch515: xsa441-linux.patch: 3fdf2be9089b xen/events: replace evtchn_rwlock with RCU
# Patch516: xsa448-linux.patch: 5bb8270789c8 xen-netback: don't produce zero-size SKB frags
Patch517: kbuild-AFTER_LINK.patch
Patch518: expose-xsversion.patch
Patch519: blktap2.patch
Patch520: blkback-kthread-pid.patch
Patch521: tg3-alloc-repeat.patch
Patch522: disable-EFI-Properties-table-for-Xen.patch
Patch523: net-Do-not-scrub-ignore_df-within-the-same-name-spac.patch
Patch524: enable-fragmention-gre-packets.patch
Patch525: 0001-CA-285778-emulex-nic-ip-hdr-len.patch-rebase-325.patch
Patch526: cifs-Change-the-default-value-SecFlags-to-0x83.patch
Patch527: call-kexec-before-offlining-noncrashing-cpus.patch
Patch528: hide-hung-task-for-idle-class.patch
Patch529: xfs-async-wait.patch
# Patch530: 0002-scsi-libfc-drop-extra-rport-reference-in-fc_rport_cr.patch: 694ec54b7826 scsi: libfc: Handling of extra kref
Patch531: dont-select-pinctrl.patch
Patch532: netscaler_everest_xs8_200g.patch
Patch533: 0001-dma-add-dma_get_required_mask_from_max_pfn.patch
Patch534: 0002-x86-xen-correct-dma_get_required_mask-for-Xen-PV-gue.patch
Patch535: map-1MiB-1-1.patch
Patch536: hide-nr_cpus-warning.patch
Patch537: disable-pm-timer.patch
Patch538: increase-nr-irqs.patch
Patch539: xen-balloon-hotplug-select-HOLES_IN_ZONE.patch
Patch540: 0001-pci-export-pci_probe_reset_function.patch
Patch541: 0002-xen-pciback-provide-a-reset-sysfs-file-to-try-harder.patch
Patch542: pciback-disable-root-port-aer.patch
Patch543: pciback-mask-root-port-comp-timeout.patch
Patch544: no-flr-quirk.patch
Patch545: revert-PCI-Probe-for-device-reset-support-during-enumeration.patch
Patch546: CA-135938-nfs-disconnect-on-rpc-retry.patch
Patch547: 0001-sunrpc-force-disconnect-on-connection-timeout-rebase-325.patch
Patch548: nfs-avoid-double-timeout.patch
Patch549: 0001-bonding-balance-slb-rebase-325.patch
Patch550: 0001-bridge-lock-fdb-after-garp-rebase-325.patch
Patch551: CP-13181-net-openvswitch-add-dropping-of-fip-and-lldp.patch
Patch552: xen-ioemu-inject-msi.patch
Patch553: pv-iommu-support.patch
Patch554: kexec-reserve-crashkernel-region.patch
Patch555: 0001-xen-swiotlb-rework-early-repeat-code.patch
Patch556: 0001-arch-x86-xen-add-infrastruction-in-xen-to-support-gv.patch
Patch557: 0002-drm-i915-gvt-write-guest-ppgtt-entry-for-xengt-suppo.patch
Patch558: 0003-drm-i915-xengt-xengt-moudule-initial-files.patch
Patch559: 0004-drm-i915-xengt-check-on_destroy-on-pfn_to_mfn.patch
Patch560: 0005-arch-x86-xen-Import-x4.9-interface-for-ioreq.patch
Patch561: 0006-i915-gvt-xengt.c-Use-new-dm_op-instead-of-hvm_op.patch
Patch562: 0007-i915-gvt-xengt.c-New-interface-to-write-protect-PPGT.patch
Patch563: 0008-i915-gvt-xengt.c-Select-vgpu-type-according-to-low_g.patch
Patch564: 0009-drm-i915-gvt-Don-t-output-error-message-when-DomU-ma.patch
Patch565: 0010-drm-i915-gvt-xengt-Correctly-get-low-mem-max-gfn.patch
Patch566: 0011-drm-i915-gvt-Fix-dom0-call-trace-at-shutdown-or-rebo.patch
Patch567: 0012-hvm-dm_op.h-Sync-dm_op-interface-to-xen-4.9-release.patch
Patch568: 0001-drm-i915-gvt-Apply-g2h-adjust-for-GTT-mmio-access-rebase-325.patch
Patch569: 0014-drm-i915-gvt-Apply-g2h-adjustment-during-fence-mmio-.patch
Patch570: 0015-drm-i915-gvt-Patch-the-gma-in-gpu-commands-during-co.patch
Patch571: 0016-drm-i915-gvt-Retrieve-the-guest-gm-base-address-from.patch
Patch572: 0001-drm-i915-gvt-Align-the-guest-gm-aperture-start-offse-rebase-325.patch
Patch573: 0018-drm-i915-gvt-Add-support-to-new-VFIO-subregion-VFIO_.patch
Patch574: 0019-drm-i915-gvt-Implement-vGPU-status-save-and-restore-.patch
Patch575: 0020-vfio-Implement-new-Ioctl-VFIO_IOMMU_GET_DIRTY_BITMAP.patch
Patch576: 0021-drm-i915-gvt-Add-dev-node-for-vGPU-state-save-restor.patch
Patch577: 0022-drm-i915-gvt-Add-interface-to-control-the-vGPU-runni.patch
Patch578: 0023-drm-i915-gvt-Modify-the-vGPU-save-restore-logic-for-.patch
Patch579: 0024-drm-i915-gvt-Add-log-dirty-support-for-XENGT-migrati.patch
Patch580: 0025-drm-i915-gvt-xengt-Add-iosrv_enabled-to-track-iosrv-.patch
Patch581: 0026-drm-i915-gvt-Add-xengt-ppgtt-write-handler.patch
Patch582: 0027-drm-i915-gvt-xengt-Impliment-mpt-dma_map-unmap_guest.patch
Patch583: 0028-drm-i915-gvt-introduce-a-new-VFIO-region-for-vfio-de.patch
Patch584: 0029-drm-i915-gvt-change-the-return-value-of-opregion-acc.patch
Patch585: 0030-drm-i915-gvt-Rebase-the-code-to-gvt-staging-for-live.patch
Patch586: 0031-drm-i915-gvt-Apply-g2h-adjustment-to-buffer-start-gm.patch
Patch587: 0032-drm-i915-gvt-Fix-xengt-opregion-handling-in-migratio.patch
Patch588: 0033-drm-i915-gvt-XenGT-migration-optimize.patch
Patch589: 0034-drm-i915-gvt-Add-vgpu-execlist-info-into-migration-d.patch
Patch590: 0035-drm-i915-gvt-Emulate-ring-mode-register-restore-for-.patch
Patch591: 0036-drm-i915-gvt-Use-copy_to_user-to-return-opregion.patch
Patch592: 0037-drm-i915-gvt-Expose-opregion-in-vgpu-open.patch
Patch593: 0038-drm-i915-gvt-xengt-Don-t-shutdown-vm-at-ioreq-failur.patch
Patch594: 0039-drm-i915-gvt-Emulate-hw-status-page-address-register.patch
Patch595: 0040-drm-i915-gvt-migration-copy-vregs-on-vreg-load.patch
Patch596: 0041-drm-i915-gvt-Fix-a-command-corruption-caused-by-live.patch
Patch597: 0042-drm-i915-gvt-update-force-to-nonpriv-register-whitel.patch
Patch598: 0043-drm-i915-gvt-xengt-Fix-xengt-instance-destroy-error.patch
Patch599: 0044-drm-i915-gvt-invalidate-old-ggtt-page-when-update-gg.patch
Patch600: 0045-drm-i915-gvt-support-inconsecutive-partial-gtt-entry.patch
Patch601: set-XENMEM_get_mfn_from_pfn-hypercall-number.patch
Patch602: gvt-enforce-primary-class-id.patch
Patch603: gvt-use-xs-vgpu-type.patch
Patch604: xengt-pviommu-basic.patch
Patch605: xengt-pviommu-unmap.patch
Patch606: get_domctl_interface_version.patch
Patch607: xengt-fix-shutdown-failures.patch
Patch608: xengt-i915-gem-vgtbuffer.patch
Patch609: xengt-gtt-2m-alignment.patch
Patch610: net-core__order-3_frag_allocator_causes_swiotlb_bouncing_under_xen-rebase-325.patch
Patch611: idle_cpu-return-0-during-softirq.patch
Patch612: default-xen-swiotlb-size-128MiB.patch
Patch613: dlm__increase_socket_backlog_to_avoid_hangs_with_16_nodes.patch
Patch614: gfs2-add-skippiness.patch
Patch615: GFS2__Avoid_recently_demoted_rgrps
Patch616: gfs2-debug-rgrp-sweep
Patch617: gfs2-restore-kabi.patch
Patch618: 0001-Add-auxiliary-bus-support-rebase-325.patch
Patch619: 0002-driver-core-auxiliary-bus-move-slab.h-from-include-f.patch
Patch620: 0003-driver-core-auxiliary-bus-make-remove-function-retur.patch
Patch621: 0004-driver-core-auxiliary-bus-minor-coding-style-tweaks.patch
Patch622: 0005-driver-core-auxiliary-bus-Fix-auxiliary-bus-shutdown.patch
Patch623: 0006-driver-core-auxiliary-bus-Fix-calling-stage-for-auxi.patch
Patch624: 0007-driver-core-auxiliary-bus-Remove-unneeded-module-bit.patch
Patch625: 0008-driver-core-auxiliary-bus-Fix-memory-leak-when-drive.patch
Patch626: 0009-Documentation-auxiliary_bus-Clarify-auxiliary_device.patch
Patch627: 0010-Documentation-auxiliary_bus-Clarify-__auxiliary_driv.patch
Patch628: 0011-Documentation-auxiliary_bus-Clarify-the-release-of-d.patch
Patch629: 0012-Documentation-auxiliary_bus-Move-the-text-into-the-c.patch
Patch630: 0013-CP-41018-Make-CONFIG_AUXILIARY_BUS-y-work.patch
Patch631: scsi-avoid-lun-change-loop.patch
Patch632: Avoid-deadlocks-on-NFS-spinlocks.patch
Patch633: 0001-abi-version-rebase-325.patch
%if %{do_kabichk}
Source3: check-kabi
Source4: Module.kabi
%endif
Source5: prepare-build

# XCP-ng patches
# Patch1000: ceph.patch: already included in v4.19.325
# Patch1001: tg3-v4.19.315.patch: already included in v4.19.325
# Patch1002: 0001-perf-probe-Fix-getting-the-kernel-map.patch: 37c6f8089806 perf probe: Fix getting the kernel map
# Patch1003: 0001-ACPI-processor-idle-Check-acpi_bus_get_device-return.patch f001c5c35a00 ACPI: processor: idle: Check acpi_fetch_acpi_dev() return value
# Patch1004: 0001-scsi-target-Fix-XCOPY-NAA-identifier-lookup.patch: fff1180d24e6 scsi: target: Fix XCOPY NAA identifier lookup
# Patch1005: 0001-ext4-fix-off-by-one-error-in-do_split.patch: 6f3510ec1348 ext4: fix off-by-one error in do_split
Patch1006: 0001-SUNRPC-Restore-missing-call-to-cancel_work_sync.patch
# CVE-2026-31431 (used by CopyFail v1)
Patch1007: 0001-crypto-disable-authencesn-module-for-CVE-2026-31431.patch
# CVE-2026-43284 (used by DirtyFrag, DirtyFail, CopyFail v2 Electric Boogaloo)
# Patch1008: 0001-xfrm-esp-avoid-in-place-decrypt-on-shared-skb-frags.patch: d985920ced65 xfrm: esp: avoid in-place decrypt on shared skb frags
# CVE-2026-46333 (used by ssh-keysign-pwn, ptrace_may_dream)
# Patch1009: 0001-ptrace-restore-smp_rmb-in-__ptrace_may_access.patch: TODO upstream equivalent
# Patch1010: 0002-ptrace-slightly-saner-get_dumpable-logic.patch: 326b1c50eedc ptrace: slightly saner 'get_dumpable()' logic
# Patch1011: 0003-kabi-ptrace-slightly-saner-get_dumpable-logic.patch: Not needed given above patch is already in v4.19.325-cip134
# CVE-2026-46300 (used by fragnesia), iterative fixes to CVE-2026-43284
# Patch1012: 0004-net-skbuff-preserve-shared-frag-marker-during-coales.patch: e993af8976a5 net: skbuff: preserve shared-frag marker during coalescing
# Patch1013: 0005-net-skbuff-propagate-shared-frag-marker-through-frag.patch: cb225ad20da0 net: skbuff: propagate shared-frag marker through frag-transfer helpers
# CVE-2026-43494 (used by pintheft)
# Patch1014: 0006-net-rds-reset-op_nents-when-zerocopy-page-pin-fails.patch: ffc1541ce426 net/rds: reset op_nents when zerocopy page pin fails
# CVE-2026-46243 (cifswitch)
# Patch1015: 0007-smb-client-reject-userspace-cifs-spnego-descriptions.patch: 1fca42a8b297 smb: client: reject userspace cifs.spnego descriptions

# Backport fixes in pcieport driver for hotplug hardware detection
Patch1020: 0001-PCI-pciehp-Differentiate-between-surprise-and-safe-r.patch
Patch1021: 0002-PCI-pciehp-Tolerate-Presence-Detect-hardwired-to-zer-rebased-325.patch
# The following patches fix a regression introduced by the previous patches
Patch1022: 0001-PCI-pciehp-Disable-in-band-presence-detect-when-poss.patch
Patch1023: 0002-PCI-pciehp-Wait-for-PDS-if-in-band-presence-is-disab.patch
Patch1024: 0003-PCI-pciehp-Add-DMI-table-for-in-band-presence-detect.patch

# CVE-2026-45840 (openvswitch: cap upcall PID array size and pre-size vport replies)
# Patch1025: 0656-openvswitch-cap-upcall-PID-array-size-and-pre-size-v.patch: 801e108a6bc6 openvswitch: cap upcall PID array size and pre-size vport replies
# CVE-2026-53227 (net: openvswitch: fix possible kfree_skb of ERR_PTR)
Patch1026: 0657-net-openvswitch-fix-possible-kfree_skb-of-ERR_PTR.patch

# CVE-2026-64600 (RefluXFS)
Patch1027: 0001-xfs-resample-the-data-fork-mapping-after-cycling-ILO.patch

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
Requires: devtoolset-11-elfutils-libelf-devel

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

%package -n python2-perf
Summary: %{pythonperfsum}
Provides: python2-perf
%description -n python2-perf
%{pythonperfdesc}

%prep
%autosetup -p1 -n linux-cip-%{version}-cip%{cipver}
%{?_cov_prepare}

%build
source %{SOURCE5}

# This override tweaks the kernel makefiles so that we run debugedit on an
# object before embedding it.  When we later run find-debuginfo.sh, it will
# run debugedit again.  The edits it does change the build ID bits embedded
# in the stripped object, but repeating debugedit is a no-op.  We do it
# beforehand to get the proper final build ID bits into the embedded image.
# This affects the vDSO images in vmlinux, and the vmlinux image in bzImage.
export AFTER_LINK='sh -xc "/usr/lib/rpm/debugedit -b %{buildroot} -d /usr/src/debug -i $@ > $@.id"'

cp -f %{SOURCE1} .config
echo XS_VERSION=%{version}-%{release} > .xsversion
echo XS_BASE_COMMIT=%{package_srccommit} >> .xsversion
echo XS_PQ_COMMIT=%{package_speccommit} >> .xsversion
# make sure configuration is up to date
%{?_cov_wrap} make olddefconfig
bash -c 'diff -u <(grep -v "^#" .config) <(grep -v "^#" %{SOURCE1})'

cp -r `pwd` ../prepared-source
install -m 644 %{SOURCE5} ../prepared-source

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
%global perf_make \
  %{?_cov_wrap} make EXTRA_CFLAGS="${RPM_OPT_FLAGS}" LDFLAGS="%{__global_ldflags}" %{?cross_opts} V=1 NO_PERF_READ_VDSO32=1 NO_PERF_READ_VDSOX32=1 WERROR=0 HAVE_CPLUS_DEMANGLE=1 NO_GTK2=1 NO_STRLCPY=1 NO_BIONIC=1 NO_JVMTI=1 NO_LIBCRYPTO=1 prefix=%{_prefix}
%global perf_python2 -C tools/perf PYTHON=%{__python2}
# perf
# make sure check-headers.sh is executable
chmod +x tools/perf/check-headers.sh
%{perf_make} %{perf_python2} all

pushd tools/perf/Documentation/
make %{?_smp_mflags} man
popd

# eBPF support: pahole encodes the type infos into a small (3MB) .BTF section:
cp vmlinux                                     tmp-vmlinux-with-btf
LLVM_OBJCOPY=objcopy pahole %{?_smp_mflags} -J tmp-vmlinux-with-btf
# Copy the BTF section into a new BTF file which eBPF tools to get kernel types:
objcopy --only-section .BTF                    tmp-vmlinux-with-btf vmlinux.btf
rm                                             tmp-vmlinux-with-btf

%install
# Install kernel
source %{SOURCE5}

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
install -d -m 755 %{buildroot}%{_usrsrc}/kernels/%{uname}-%{_arch}
install -d -m 755 %{buildroot}%{_rpmconfigdir}/macros.d
install -m 644 %{SOURCE2} %{buildroot}%{_rpmconfigdir}/macros.d
echo '%%kernel_version %{uname}' >> %{buildroot}%{_rpmconfigdir}/macros.d/macros.kernel
%{?_cov_install}

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

# Install files for building live patches
mv ../prepared-source %{buildroot}%{lp_devel_dir}
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

# Thus, we can install it here (/lib/.../build is an absolute symlink to this path)
install -m 644 vmlinux.btf %{buildroot}/usr/src/kernels/%{uname}-%{_arch}/vmlinux

%check
# Check that the .BTF section is present at the start of the file:
objdump -h %{buildroot}/usr/src/kernels/%{uname}-%{_arch}/vmlinux|grep " 0 .BTF"

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

%files lp-devel_%{version}_%{release}
%{lp_devel_dir}

%{?_cov_results_package}

%changelog
* Mon Aug 17 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.325-cip134.st18-8.0.46.10
- Rebase to v4.19.325-cip134

* Thu Aug 06 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.19-8.0.46.10
- Backport for CVE-2026-64600 (RefluXFS)

* Tue Aug 04 2026 Philippe Coval <philippe.coval@vates.tech> - 4.19.19-8.0.46.9
- Rebuild against OpenSSL 3.0

* Fri Jul 24 2026 Sebastien Rodot <sebastien.rodot@vates.tech> - 4.19.19-8.0.46.8
- Backport fixes for CVE-2026-45840 (openvswitch: cap upcall PID array size and pre-size vport replies)
- Backport fixes for CVE-2026-53227 (net: openvswitch: fix possible kfree_skb of ERR_PTR)

* Thu Jul 02 2026 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.46.7
- Backport fixes in pcieport driver for hotplug hardware detection

* Wed Jun 03 2026 Lucas Ravagnier <lucas.ravagnier@vates.tech> - 4.19.19-8.0.46.6
- Backport for CVE-2026-46243 (cifswitch)

* Tue May 26 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.19-8.0.46.5
- Backport for CVE-2026-46300 (Fragnesia), iterative fixes to CVE-2026-43284
- Backport for CVE-2026-46333 (ssh-key-sign, ptrace_may_dream)
- Backport for CVE-2026-43494 (pintheft)

* Wed May 13 2026 Yann Dirson <yann.dirson@vates.tech> - 4.19.19-8.0.46.4
- Use short flag and short path to patch command to avoid overflowing a rpm limitation

* Tue May 12 2026 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.46.3
- Backport for CVE-2026-43284 (DirtyFrag, XFRM-ESP path or CopyFail2) from linux-5.10.y

* Fri May 01 2026 Tu Dinh <ngoc-tu.dinh@vates.tech> - 4.19.19-8.0.46.2
- Disable authencesn module for CVE-2026-31431

* Fri Mar 27 2026 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.46.1
- Sync with 4.19.19-8.0.46
- SUNRPC: Restore call to cancel_work_sync()
- *** Upstream changelog ***
  * Thu Mar 19 2026 Frediano Ziglio <frediano.ziglio@citrix.com> - 4.19.19-8.0.46
  - XSI-2150: Avoid deadlocks on NFS spinlocks

* Fri Mar 20 2026 Thierry Escande <thierry.escande@vates.tech> - 4.19.19-8.0.45.1
- Sync with 4.19.19-8.0.45
- Add missing patch for CVE-2020-14314 (use-after-free detected by Syzkaller)
- *** Upstream changelog ***
  * Fri Feb 27 2026 Frediano Ziglio <frediano.ziglio@citrix.com> - 4.19.19-8.0.45
  - CA-400357: Use the correct MAC for rndis_host interfaces
  - CA-395473: Backport a patch to fix CVE-2020-14314
  - XSI-2150: Remove added chunk causing deadlock

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
