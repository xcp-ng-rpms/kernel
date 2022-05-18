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
Release: 7.0.14.1%{?dist}
ExclusiveArch: x86_64
ExclusiveOS: Linux
Summary: The Linux kernel
BuildRequires: gcc
BuildRequires: kmod
BuildRequires: bc
BuildRequires: hostname
BuildRequires: elfutils-libelf-devel
BuildRequires: libunwind-devel
BuildRequires: bison
BuildRequires: flex
%if %{do_kabichk}
BuildRequires: python
%endif
BuildRequires: elfutils-devel, binutils-devel, xz-devel
BuildRequires: python2-devel
BuildRequires: asciidoc xmlto
%{?_cov_buildrequires}
AutoReqProv: no
Provides: kernel-uname-r = %{uname}
Provides: kernel = %{version}-%{release}
Provides: kernel-%{_arch} = %{version}-%{release}
Requires(post): coreutils kmod
Requires(posttrans): coreutils dracut kmod


Source0: kernel-4.19.19.tar.gz
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
Patch7: 0001-gfs2-improve-debug-information-when-lvb-mismatches-a.patch
Patch8: 0001-gfs2-Don-t-set-GFS2_RDF_UPTODATE-when-the-lvb-is-upd.patch
Patch9: 0001-gfs2-slow-the-deluge-of-io-error-messages.patch
Patch10: 0001-gfs2-Use-fs_-functions-instead-of-pr_-function-where.patch
Patch11: 0001-gfs2-getlabel-support.patch
Patch12: 0001-gfs2-Always-check-the-result-of-gfs2_rbm_from_block.patch
Patch13: 0001-gfs2-Clean-up-out-of-bounds-check-in-gfs2_rbm_from_b.patch
Patch14: 0001-gfs2-Move-rs_-sizehint-rgd_gh-fields-into-the-inode.patch
Patch15: 0001-gfs2-Remove-unused-RGRP_RSRV_MINBYTES-definition.patch
Patch16: 0001-gfs2-Rename-bitmap.bi_-len-bytes.patch
Patch17: 0001-gfs2-Fix-some-minor-typos.patch
Patch18: 0001-gfs2-Fix-marking-bitmaps-non-full.patch
Patch19: 0001-gfs2-Remove-unnecessary-gfs2_rlist_alloc-parameter.patch
Patch20: 0001-gfs2-Pass-resource-group-to-rgblk_free.patch
Patch21: 0001-gfs2-write-revokes-should-traverse-sd_ail1_list-in-r.patch
Patch22: 0001-gfs2-Fix-minor-typo-couln-t-versus-couldn-t.patch
Patch23: 0003-mtip32xx-move-the-blk_rq_map_sg-call-to-mtip_hw_subm.patch
Patch24: 0004-mtip32xx-merge-mtip_submit_request-into-mtip_queue_r.patch
Patch25: 0005-mtip32xx-return-a-blk_status_t-from-mtip_send_trim.patch
Patch26: 0006-mtip32xx-remove-__force_bit2int.patch
Patch27: 0007-mtip32xx-add-missing-endianess-annotations-on-struct.patch
Patch28: 0008-mtip32xx-remove-mtip_init_cmd_header.patch
Patch29: 0009-mtip32xx-remove-mtip_get_int_command.patch
Patch30: 0010-mtip32xx-don-t-use-req-special.patch
Patch31: 0011-mtip32xxx-use-for_each_sg.patch
Patch32: 0012-mtip32xx-avoid-using-semaphores.patch
Patch33: 0013-mtip32xx-use-BLK_STS_DEV_RESOURCE-for-device-resourc.patch
Patch34: 0001-cifs-Limit-memory-used-by-lock-request-calls-to-a-pa.patch
Patch35: 0001-always-clear-the-X2APIC_ENABLE-bit-for-PV-guest.patch
Patch36: 0001-xen-pciback-Check-dev_data-before-using-it.patch
Patch37: 0001-gfs2-changes-to-gfs2_log_XXX_bio.patch
Patch38: 0001-gfs2-Remove-vestigial-bd_ops.patch
Patch39: 0001-gfs2-properly-initial-file_lock-used-for-unlock.patch
Patch40: 0001-gfs2-Clean-up-gfs2_is_-ordered-writeback.patch
Patch41: 0001-gfs2-Fix-the-gfs2_invalidatepage-description.patch
Patch42: 0001-gfs2-add-more-timing-info-to-journal-recovery-proces.patch
Patch43: 0001-gfs2-add-a-helper-function-to-get_log_header-that-ca.patch
Patch44: 0001-gfs2-Dump-nrpages-for-inodes-and-their-glocks.patch
Patch45: 0001-gfs2-take-jdata-unstuff-into-account-in-do_grow.patch
Patch46: 0001-dlm-fix-invalid-free.patch
Patch47: 0001-dlm-don-t-allow-zero-length-names.patch
Patch48: 0001-dlm-don-t-leak-kernel-pointer-to-userspace.patch
Patch49: 0001-dlm-Don-t-swamp-the-CPU-with-callbacks-queued-during.patch
Patch50: 0001-dlm-fix-possible-call-to-kfree-for-non-initialized-p.patch
Patch51: 0001-dlm-fix-missing-idr_destroy-for-recover_idr.patch
Patch52: 0001-dlm-NULL-check-before-kmem_cache_destroy-is-not-need.patch
Patch53: 0001-dlm-NULL-check-before-some-freeing-functions-is-not-.patch
Patch54: 0001-dlm-fix-invalid-cluster-name-warning.patch
Patch55: gfs2-revert-fix-loop-in-gfs2_rbm_find.patch
Patch56: 0001-scsi-libfc-free-skb-when-receiving-invalid-flogi-res.patch
Patch57: 0001-Revert-scsi-libfc-Add-WARN_ON-when-deleting-rports.patch
Patch58: 0001-net-crypto-set-sk-to-NULL-when-af_alg_release.patch
Patch59: 0001-xen-netback-fix-occasional-leak-of-grant-ref-mapping.patch
Patch60: 0002-xen-netback-don-t-populate-the-hash-cache-on-XenBus-.patch
Patch61: 0001-gfs2-Fix-missed-wakeups-in-find_insert_glock.patch
Patch62: 0001-gfs2-Fix-an-incorrect-gfs2_assert.patch
Patch63: 0001-ACPI-APEI-Fix-possible-out-of-bounds-access-to-BERT-.patch
Patch64: 0001-efi-cper-Fix-possible-out-of-bounds-access.patch
Patch65: 0001-gfs-no-need-to-check-return-value-of-debugfs_create-.patch
Patch66: 0001-scsi-iscsi-flush-running-unbind-operations-when-remo.patch
Patch67: 0001-xen-Prevent-buffer-overflow-in-privcmd-ioctl.patch
Patch68: 0001-Revert-scsi-fcoe-clear-FC_RP_STARTED-flags-when-rece.patch
Patch69: 0001-gfs2-Fix-lru_count-going-negative.patch
Patch70: 0002-gfs2-clean_journal-improperly-set-sd_log_flush_head.patch
Patch71: 0003-gfs2-Fix-occasional-glock-use-after-free.patch
Patch72: 0001-gfs2-Replace-gl_revokes-with-a-GLF-flag.patch
Patch73: 0005-gfs2-Remove-misleading-comments-in-gfs2_evict_inode.patch
Patch74: 0006-gfs2-Rename-sd_log_le_-revoke-ordered.patch
Patch75: 0007-gfs2-Rename-gfs2_trans_-add_unrevoke-remove_revoke.patch
Patch76: 0001-iomap-Clean-up-__generic_write_end-calling.patch
Patch77: 0002-fs-Turn-__generic_write_end-into-a-void-function.patch
Patch78: 0003-iomap-Fix-use-after-free-error-in-page_done-callback.patch
Patch79: 0004-iomap-Add-a-page_prepare-callback.patch
Patch80: 0008-gfs2-Fix-iomap-write-page-reclaim-deadlock.patch
Patch81: 0001-fs-mark-expected-switch-fall-throughs.patch
Patch82: 0001-gfs2-Fix-loop-in-gfs2_rbm_find-v2.patch
Patch83: 0001-gfs2-Remove-unnecessary-extern-declarations.patch
Patch84: 0001-gfs2-fix-race-between-gfs2_freeze_func-and-unmount.patch
Patch85: 0001-gfs2-read-journal-in-large-chunks.patch
Patch86: 0001-gfs2-Fix-error-path-kobject-memory-leak.patch
Patch87: 0001-gfs2-Fix-sign-extension-bug-in-gfs2_update_stats.patch
Patch88: 0001-Revert-gfs2-Replace-gl_revokes-with-a-GLF-flag.patch
Patch89: 0001-gfs2-Fix-rounding-error-in-gfs2_iomap_page_prepare.patch
Patch90: 0001-iomap-don-t-mark-the-inode-dirty-in-iomap_write_end.patch
Patch91: 0001-gfs2-Clean-up-freeing-struct-gfs2_sbd.patch
Patch92: 0001-gfs2-Use-IS_ERR_OR_NULL.patch
Patch93: 0001-gfs2-kthread-and-remount-improvements.patch
Patch94: 0001-gfs2-eliminate-tr_num_revoke_rm.patch
Patch95: 0001-gfs2-log-which-portion-of-the-journal-is-replayed.patch
Patch96: 0001-gfs2-Warn-when-a-journal-replay-overwrites-a-rgrp-wi.patch
Patch97: 0001-gfs2-Rename-SDF_SHUTDOWN-to-SDF_WITHDRAWN.patch
Patch98: 0001-gfs2-simplify-gfs2_freeze-by-removing-case.patch
Patch99: 0001-gfs2-dump-fsid-when-dumping-glock-problems.patch
Patch100: 0001-gfs2-replace-more-printk-with-calls-to-fs_info-and-f.patch
Patch101: 0001-gfs2-use-page_offset-in-gfs2_page_mkwrite.patch
Patch102: 0001-gfs2-remove-the-unused-gfs2_stuffed_write_end-functi.patch
Patch103: 0001-gfs2-merge-gfs2_writeback_aops-and-gfs2_ordered_aops.patch
Patch104: 0001-gfs2-merge-gfs2_writepage_common-into-gfs2_writepage.patch
Patch105: 0001-gfs2-mark-stuffed_readpage-static.patch
Patch106: 0001-gfs2-use-iomap_bmap-instead-of-generic_block_bmap.patch
Patch107: 0001-gfs2-don-t-use-buffer_heads-in-gfs2_allocate_page_ba.patch
Patch108: 0001-gfs2-Remove-unused-gfs2_iomap_alloc-argument.patch
Patch109: 0001-dlm-check-if-workqueues-are-NULL-before-flushing-des.patch
Patch110: 0001-dlm-no-need-to-check-return-value-of-debugfs_create-.patch
Patch111: 0001-gfs2-Inode-dirtying-fix.patch
Patch112: 0001-gfs2-gfs2_walk_metadata-fix.patch
Patch113: 0001-xen-pci-reserve-MCFG-areas-earlier.patch
Patch114: 0001-kernel-module.c-Only-return-EEXIST-for-modules-that-.patch
Patch115: 0001-net-mlx5e-Force-CHECKSUM_UNNECESSARY-for-short-ether.patch
Patch116: 0001-net-mlx4_en-Force-CHECKSUM_NONE-for-short-ethernet-f.patch
Patch117: 0001-random-add-a-spinlock_t-to-struct-batched_entropy.patch
Patch118: 0001-tcp-limit-payload-size-of-sacked-skbs.patch
Patch119: 0002-tcp-tcp_fragment-should-apply-sane-memory-limits.patch
Patch120: 0003-tcp-add-tcp_min_snd_mss-sysctl.patch
Patch121: 0004-tcp-enforce-tcp_min_snd_mss-in-tcp_mtu_probing.patch
Patch122: 0001-tcp-refine-memory-limit-test-in-tcp_fragment.patch
Patch123: 0002-xen-events-fix-binding-user-event-channels-to-cpus.patch
Patch124: 0003-xen-let-alloc_xenballooned_pages-fail-if-not-enough-.patch
Patch125: 0001-tcp-be-more-careful-in-tcp_fragment.patch
Patch126: 0001-random-always-use-batched-entropy-for-get_random_u-3.patch
Patch127: 0001-block-cleanup-__blkdev_issue_discard.patch
Patch128: 0001-block-fix-32-bit-overflow-in-__blkdev_issue_discard.patch
Patch129: 0001-scsi-libiscsi-Fix-race-between-iscsi_xmit_task-and-i.patch
Patch130: 0001-xen-netback-Reset-nr_frags-before-freeing-skb.patch
Patch131: 0001-openvswitch-change-type-of-UPCALL_PID-attribute-to-N.patch
Patch132: 0001-gfs2-gfs2_iomap_begin-cleanup.patch
Patch133: 0001-gfs2-Add-support-for-IOMAP_ZERO.patch
Patch134: 0001-gfs2-implement-gfs2_block_zero_range-using-iomap_zer.patch
Patch135: 0001-gfs2-Minor-gfs2_alloc_inode-cleanup.patch
Patch136: 0001-gfs2-Always-mark-inode-dirty-in-fallocate.patch
Patch137: 0001-gfs2-untangle-the-logic-in-gfs2_drevalidate.patch
Patch138: 0001-gfs2-Fix-possible-fs-name-overflows.patch
Patch139: 0001-gfs2-Fix-recovery-slot-bumping.patch
Patch140: 0001-gfs2-Minor-PAGE_SIZE-arithmetic-cleanups.patch
Patch141: 0001-gfs2-Delete-an-unnecessary-check-before-brelse.patch
Patch142: 0001-gfs2-separate-holder-for-rgrps-in-gfs2_rename.patch
Patch143: 0001-gfs2-create-function-gfs2_glock_update_hold_time.patch
Patch144: 0001-gfs2-Use-async-glocks-for-rename.patch
Patch145: 0001-gfs2-Improve-mmap-write-vs.-truncate-consistency.patch
Patch146: 0001-gfs2-clear-buf_in_tr-when-ending-a-transaction-in-sw.patch
Patch147: 0001-xen-efi-Set-nonblocking-callbacks.patch
Patch148: 0001-drm-i915-gvt-Allow-F_CMD_ACCESS-on-mmio-0x21f0.patch
Patch149: 0001-gfs2-add-compat_ioctl-support.patch
Patch150: 0001-gfs2-removed-unnecessary-semicolon.patch
Patch151: 0001-gfs2-Some-whitespace-cleanups.patch
Patch152: 0001-gfs2-Improve-mmap-write-vs.-punch_hole-consistency.patch
Patch153: 0001-gfs2-Multi-block-allocations-in-gfs2_page_mkwrite.patch
Patch154: 0001-gfs2-Fix-end-of-file-handling-in-gfs2_page_mkwrite.patch
Patch155: 0001-gfs2-Remove-active-journal-side-effect-from-gfs2_wri.patch
Patch156: 0001-gfs2-make-gfs2_log_shutdown-static.patch
Patch157: 0001-gfs2-fix-glock-reference-problem-in-gfs2_trans_remov.patch
Patch158: 0001-gfs2-Introduce-function-gfs2_withdrawn.patch
Patch159: 0001-gfs2-fix-infinite-loop-in-gfs2_ail1_flush-on-io-erro.patch
Patch160: 0001-gfs2-Don-t-loop-forever-in-gfs2_freeze-if-withdrawn.patch
Patch161: 0001-gfs2-Abort-gfs2_freeze-if-io-error-is-seen.patch
Patch162: 0001-gfs2-Close-timing-window-with-GLF_INVALIDATE_IN_PROG.patch
Patch163: 0001-gfs2-clean-up-iopen-glock-mess-in-gfs2_create_inode.patch
Patch164: 0001-gfs2-Remove-duplicate-call-from-gfs2_create_inode.patch
Patch165: 0001-gfs2-Don-t-write-log-headers-after-file-system-withd.patch
Patch166: 0001-xen-events-remove-event-handling-recursion-detection.patch
Patch167: 0001-gfs2-Another-gfs2_find_jhead-fix.patch
Patch168: 0001-gfs2-eliminate-ssize-parameter-from-gfs2_struct2blk.patch
Patch169: 0001-gfs2-minor-cleanup-remove-unneeded-variable-ret-in-g.patch
Patch170: 0001-gfs2-Avoid-access-time-thrashing-in-gfs2_inode_looku.patch
Patch171: 0001-gfs2-Fix-incorrect-variable-name.patch
Patch172: 0001-gfs2-Remove-GFS2_MIN_LVB_SIZE-define.patch
Patch173: 0001-fs-gfs2-remove-unused-IS_DINODE-and-IS_LEAF-macros.patch
Patch174: 0001-gfs2-remove-unused-LBIT-macros.patch
Patch175: 0001-Revert-gfs2-eliminate-tr_num_revoke_rm.patch
Patch176: 0001-gfs2-fix-gfs2_find_jhead-that-returns-uninitialized-.patch
Patch177: 0001-gfs2-move-setting-current-backing_dev_info.patch
Patch178: 0001-gfs2-fix-O_SYNC-write-handling.patch
Patch179: 0001-drm-i915-gvt-fix-high-order-allocation-failure-on-la.patch
Patch180: 0001-drm-i915-gvt-Add-mutual-lock-for-ppgtt-mm-LRU-list.patch
Patch181: 0002-drm-i915-gvt-more-locking-for-ppgtt-mm-LRU-list.patch
Patch182: 0001-gfs2_atomic_open-fix-O_EXCL-O_CREAT-handling-on-cold.patch
Patch183: 0001-gfs2-Split-gfs2_lm_withdraw-into-two-functions.patch
Patch184: 0001-gfs2-Report-errors-before-withdraw.patch
Patch185: 0001-gfs2-Remove-usused-cluster_wide-arguments-of-gfs2_co.patch
Patch186: 0001-gfs2-Turn-gfs2_consist-into-void-functions.patch
Patch187: 0001-gfs2-Return-bool-from-gfs2_assert-functions.patch
Patch188: 0001-gfs2-Introduce-concept-of-a-pending-withdraw.patch
Patch189: 0001-gfs2-clear-ail1-list-when-gfs2-withdraws.patch
Patch190: 0001-gfs2-Rework-how-rgrp-buffer_heads-are-managed.patch
Patch191: 0001-gfs2-log-error-reform.patch
Patch192: 0001-gfs2-Only-complain-the-first-time-an-io-error-occurs.patch
Patch193: 0001-gfs2-Ignore-dlm-recovery-requests-if-gfs2-is-withdra.patch
Patch194: 0001-gfs2-move-check_journal_clean-to-util.c-for-future-u.patch
Patch195: 0001-gfs2-Allow-some-glocks-to-be-used-during-withdraw.patch
Patch196: 0001-gfs2-Force-withdraw-to-replay-journals-and-wait-for-.patch
Patch197: 0001-gfs2-fix-infinite-loop-when-checking-ail-item-count-.patch
Patch198: 0001-gfs2-Add-verbose-option-to-check_journal_clean.patch
Patch199: 0001-gfs2-Issue-revokes-more-intelligently.patch
Patch200: 0001-gfs2-Prepare-to-withdraw-as-soon-as-an-IO-error-occu.patch
Patch201: 0001-gfs2-Check-for-log-write-errors-before-telling-dlm-t.patch
Patch202: 0001-gfs2-Do-log_flush-in-gfs2_ail_empty_gl-even-if-ail-l.patch
Patch203: 0001-gfs2-Withdraw-in-gfs2_ail1_flush-if-write_cache_page.patch
Patch204: 0001-gfs2-drain-the-ail2-list-after-io-errors.patch
Patch205: 0001-gfs2-Don-t-demote-a-glock-until-its-revokes-are-writ.patch
Patch206: 0001-gfs2-Do-proper-error-checking-for-go_sync-family-of-.patch
Patch207: 0001-gfs2-flesh-out-delayed-withdraw-for-gfs2_log_flush.patch
Patch208: 0001-gfs2-don-t-allow-releasepage-to-free-bd-still-used-f.patch
Patch209: 0001-gfs2-allow-journal-replay-to-hold-sd_log_flush_lock.patch
Patch210: 0001-gfs2-leaf_dealloc-needs-to-allocate-one-more-revoke.patch
Patch211: 0001-gfs2-Additional-information-when-gfs2_ail1_flush-wit.patch
Patch212: 0001-gfs2-Clean-up-inode-initialization-and-teardown.patch
Patch213: 0001-gfs2-Switch-to-list_-first-last-_entry.patch
Patch214: 0001-gfs2-eliminate-gfs2_rsqa_alloc-in-favor-of-gfs2_qa_a.patch
Patch215: 0001-gfs2-Change-inode-qa_data-to-allow-multiple-users.patch
Patch216: 0001-gfs2-Split-gfs2_rsqa_delete-into-gfs2_rs_delete-and-.patch
Patch217: 0001-gfs2-Remove-unnecessary-gfs2_qa_-get-put-pairs.patch
Patch218: 0001-gfs2-don-t-lock-sd_log_flush_lock-in-try_rgrp_unlink.patch
Patch219: 0001-gfs2-instrumentation-wrt-ail1-stuck.patch
Patch220: 0001-gfs2-change-from-write-to-read-lock-for-sd_log_flush.patch
Patch221: 0001-gfs2-Fix-oversight-in-gfs2_ail1_flush.patch
Patch222: 0001-gfs2-fix-withdraw-sequence-deadlock.patch
Patch223: 0001-gfs2-Fix-error-exit-in-do_xmote.patch
Patch224: 0001-gfs2-Fix-BUG-during-unmount-after-file-system-withdr.patch
Patch225: 0001-gfs2-Fix-use-after-free-in-gfs2_logd-after-withdraw.patch
Patch226: 0001-block-call-rq_qos_exit-after-queue-is-frozen.patch
Patch227: 0001-scsi-libfc-free-response-frame-from-GPN_ID.patch
Patch228: 0001-xen-xenbus-ensure-xenbus_map_ring_valloc-returns-pro.patch
Patch229: kbuild-AFTER_LINK.patch
Patch230: commit-info.patch
Patch231: expose-xsversion.patch
Patch232: blktap2.patch
Patch233: blkback-kthread-pid.patch
Patch234: tg3-alloc-repeat.patch
Patch235: map-1MiB-1-1.patch
Patch236: disable-EFI-Properties-table-for-Xen.patch
Patch237: hide-nr_cpus-warning.patch
Patch238: disable-pm-timer.patch
Patch239: net-Do-not-scrub-ignore_df-within-the-same-name-spac.patch
Patch240: enable-fragmention-gre-packets.patch
Patch241: CA-285778-emulex-nic-ip-hdr-len.patch
Patch242: cifs-Change-the-default-value-SecFlags-to-0x83.patch
Patch243: call-kexec-before-offlining-noncrashing-cpus.patch
Patch244: hide-hung-task-for-idle-class.patch
Patch245: xfs-async-wait.patch
Patch246: 0002-scsi-libfc-drop-extra-rport-reference-in-fc_rport_cr.patch
Patch247: 0001-dma-add-dma_get_required_mask_from_max_pfn.patch
Patch248: 0002-x86-xen-correct-dma_get_required_mask-for-Xen-PV-gue.patch
Patch249: xen-balloon-hotplug-select-HOLES_IN_ZONE.patch
Patch250: mm-zero-last-section-tail.patch
Patch251: 0001-pci-export-pci_probe_reset_function.patch
Patch252: 0002-xen-pciback-provide-a-reset-sysfs-file-to-try-harder.patch
Patch253: pciback-disable-root-port-aer.patch
Patch254: pciback-mask-root-port-comp-timeout.patch
Patch255: no-flr-quirk.patch
Patch256: revert-PCI-Probe-for-device-reset-support-during-enumeration.patch
Patch257: CA-135938-nfs-disconnect-on-rpc-retry.patch
Patch258: sunrpc-force-disconnect-on-connection-timeout.patch
Patch259: bonding-balance-slb.patch
Patch260: bridge-lock-fdb-after-garp.patch
Patch261: CP-13181-net-openvswitch-add-dropping-of-fip-and-lldp.patch
Patch262: xen-ioemu-inject-msi.patch
Patch263: pv-iommu-support.patch
Patch264: kexec-reserve-crashkernel-region.patch
Patch265: 0001-xen-swiotlb-rework-early-repeat-code.patch
Patch266: 0001-arch-x86-xen-add-infrastruction-in-xen-to-support-gv.patch
Patch267: 0002-drm-i915-gvt-write-guest-ppgtt-entry-for-xengt-suppo.patch
Patch268: 0003-drm-i915-xengt-xengt-moudule-initial-files.patch
Patch269: 0004-drm-i915-xengt-check-on_destroy-on-pfn_to_mfn.patch
Patch270: 0005-arch-x86-xen-Import-x4.9-interface-for-ioreq.patch
Patch271: 0006-i915-gvt-xengt.c-Use-new-dm_op-instead-of-hvm_op.patch
Patch272: 0007-i915-gvt-xengt.c-New-interface-to-write-protect-PPGT.patch
Patch273: 0008-i915-gvt-xengt.c-Select-vgpu-type-according-to-low_g.patch
Patch274: 0009-drm-i915-gvt-Don-t-output-error-message-when-DomU-ma.patch
Patch275: 0010-drm-i915-gvt-xengt-Correctly-get-low-mem-max-gfn.patch
Patch276: 0011-drm-i915-gvt-Fix-dom0-call-trace-at-shutdown-or-rebo.patch
Patch277: 0012-hvm-dm_op.h-Sync-dm_op-interface-to-xen-4.9-release.patch
Patch278: 0013-drm-i915-gvt-Apply-g2h-adjust-for-GTT-mmio-access.patch
Patch279: 0014-drm-i915-gvt-Apply-g2h-adjustment-during-fence-mmio-.patch
Patch280: 0015-drm-i915-gvt-Patch-the-gma-in-gpu-commands-during-co.patch
Patch281: 0016-drm-i915-gvt-Retrieve-the-guest-gm-base-address-from.patch
Patch282: 0017-drm-i915-gvt-Align-the-guest-gm-aperture-start-offse.patch
Patch283: 0018-drm-i915-gvt-Add-support-to-new-VFIO-subregion-VFIO_.patch
Patch284: 0019-drm-i915-gvt-Implement-vGPU-status-save-and-restore-.patch
Patch285: 0020-vfio-Implement-new-Ioctl-VFIO_IOMMU_GET_DIRTY_BITMAP.patch
Patch286: 0021-drm-i915-gvt-Add-dev-node-for-vGPU-state-save-restor.patch
Patch287: 0022-drm-i915-gvt-Add-interface-to-control-the-vGPU-runni.patch
Patch288: 0023-drm-i915-gvt-Modify-the-vGPU-save-restore-logic-for-.patch
Patch289: 0024-drm-i915-gvt-Add-log-dirty-support-for-XENGT-migrati.patch
Patch290: 0025-drm-i915-gvt-xengt-Add-iosrv_enabled-to-track-iosrv-.patch
Patch291: 0026-drm-i915-gvt-Add-xengt-ppgtt-write-handler.patch
Patch292: 0027-drm-i915-gvt-xengt-Impliment-mpt-dma_map-unmap_guest.patch
Patch293: 0028-drm-i915-gvt-introduce-a-new-VFIO-region-for-vfio-de.patch
Patch294: 0029-drm-i915-gvt-change-the-return-value-of-opregion-acc.patch
Patch295: 0030-drm-i915-gvt-Rebase-the-code-to-gvt-staging-for-live.patch
Patch296: 0031-drm-i915-gvt-Apply-g2h-adjustment-to-buffer-start-gm.patch
Patch297: 0032-drm-i915-gvt-Fix-xengt-opregion-handling-in-migratio.patch
Patch298: 0033-drm-i915-gvt-XenGT-migration-optimize.patch
Patch299: 0034-drm-i915-gvt-Add-vgpu-execlist-info-into-migration-d.patch
Patch300: 0035-drm-i915-gvt-Emulate-ring-mode-register-restore-for-.patch
Patch301: 0036-drm-i915-gvt-Use-copy_to_user-to-return-opregion.patch
Patch302: 0037-drm-i915-gvt-Expose-opregion-in-vgpu-open.patch
Patch303: 0038-drm-i915-gvt-xengt-Don-t-shutdown-vm-at-ioreq-failur.patch
Patch304: 0039-drm-i915-gvt-Emulate-hw-status-page-address-register.patch
Patch305: 0040-drm-i915-gvt-migration-copy-vregs-on-vreg-load.patch
Patch306: 0041-drm-i915-gvt-Fix-a-command-corruption-caused-by-live.patch
Patch307: 0042-drm-i915-gvt-update-force-to-nonpriv-register-whitel.patch
Patch308: 0043-drm-i915-gvt-xengt-Fix-xengt-instance-destroy-error.patch
Patch309: 0044-drm-i915-gvt-invalidate-old-ggtt-page-when-update-gg.patch
Patch310: 0045-drm-i915-gvt-support-inconsecutive-partial-gtt-entry.patch
Patch311: set-XENMEM_get_mfn_from_pfn-hypercall-number.patch
Patch312: gvt-enforce-primary-class-id.patch
Patch313: gvt-use-xs-vgpu-type.patch
Patch314: xengt-pviommu-basic.patch
Patch315: xengt-pviommu-unmap.patch
Patch316: get_domctl_interface_version.patch
Patch317: xengt-fix-shutdown-failures.patch
Patch318: xengt-i915-gem-vgtbuffer.patch
Patch319: xengt-gtt-2m-alignment.patch
Patch320: net-core__order-3_frag_allocator_causes_swiotlb_bouncing_under_xen.patch
Patch321: idle_cpu-return-0-during-softirq.patch
Patch322: default-xen-swiotlb-size-128MiB.patch
Patch323: dlm__increase_socket_backlog_to_avoid_hangs_with_16_nodes.patch
Patch324: dlm_handle_uevent_erestartsys.patch
Patch325: gfs2-add-skippiness.patch
Patch326: GFS2__Avoid_recently_demoted_rgrps
Patch327: gfs2-debug-rgrp-sweep
Patch328: gfs2-restore-kabi.patch
Patch329: xsa331-linux.patch
Patch330: xsa332-linux-01.patch
Patch331: v11-0003-xen-events-fix-race-in-evtchn_fifo_unmask.patch
Patch332: xsa332-linux-02.patch
Patch333: xsa332-linux-03.patch
Patch334: xsa332-linux-04.patch
Patch335: xsa332-linux-05.patch
Patch336: xsa332-linux-06.patch
Patch337: xsa332-linux-07.patch
Patch338: xsa332-linux-08.patch
Patch339: xsa332-linux-09.patch
Patch340: xsa332-linux-10.patch
Patch341: xsa332-linux-11.patch
Patch342: 0001-Add-shadow-variables-support-from-kpatch.patch
Patch343: 0002-xen-xenbus-Allow-watches-discard-events-before-queue.patch
Patch344: 0003-xen-xenbus-Add-will_handle-callback-support-in-xenbu.patch
Patch345: 0004-xen-xenbus-xen_bus_type-Support-will_handle-watch-ca.patch
Patch346: 0005-xen-xenbus-Count-pending-messages-for-each-watch.patch
Patch347: 0006-xenbus-xenbus_backend-Disallow-pending-watch-message.patch
Patch348: xsa350-linux.patch
Patch349: xsa361-linux-1.patch
Patch350: xsa361-linux-2.patch
Patch351: xsa361-linux-3.patch
Patch352: xsa361-linux-4.patch
Patch353: xsa362-linux-1.patch
Patch354: xsa362-linux-2.patch
Patch355: xsa362-linux-3.patch
Patch356: 0001-xen-netback-avoid-race-in-xenvif_rx_ring_slots_avail.patch
Patch357: xsa365-linux.patch
Patch358: xsa371-linux.patch
Patch359: xsa367-linux.patch
Patch360: 0001-xen-netback-fix-spurious-event-detection-for-common-.patch
Patch361: 0007-xen-evtchn-use-smp-barriers-for-user-event-ring.patch
Patch362: 0008-xen-evtchn-use-READ-WRITE_ONCE-for-accessing-ring-in.patch
Patch363: xen-events-reset-affinity-of-2-level-event-when-tearing-it-down.patch
Patch364: xen-events-don-t-unmask-an-event-channel-when-an-eoi-is-pending.patch
Patch365: xen-events-avoid-handling-the-same-event-on-two-cpus-at-the-same-time.patch
Patch366: 0001-x86-ioperm-Add-new-paravirt-function-update_io_bitma.patch
Patch367: 0001-bpf-x86-Validate-computation-of-branch-displacements.patch
Patch368: 0002-bpf-x86-Validate-computation-of-branch-displacements.patch
Patch369: 0001-xen-events-fix-setting-irq-affinity.patch
Patch370: 0001-xen-events-reset-active-flag-for-lateeoi-events-late.patch
Patch371: 0001-seq_file-disallow-extremely-large-seq-buffer-allocat.patch
Patch372: 0001-xen-events-Fix-race-in-set_evtchn_to_irq.patch
Patch373: 0001-bpf-Do-not-use-ax-register-in-interpreter-on-div-mod.patch
Patch374: 0002-bpf-Fix-32-bit-src-register-truncation-on-div-mod.patch
Patch375: 0003-bpf-Fix-truncation-handling-for-mod32-dst-reg-wrt-ze.patch
Patch376: 0001-x86-timer-Skip-PIT-initialization-on-modern-chipsets.patch
Patch377: 0001-x86-timer-Force-PIT-initialization-when-X86_FEATURE_.patch
Patch378: 0001-x86-timer-Don-t-skip-PIT-setup-when-APIC-is-disabled.patch
Patch379: xsa392-linux-1.patch
Patch380: xsa392-linux-2.patch
Patch381: abi-version.patch
Patch382: xen_dom0_64bit-efi.patch

Provides: gitsha(ssh://git@code.citrite.net/XSU/linux-stable.git) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
Provides: gitsha(ssh://git@code.citrite.net/XS/linux.pg.git) = 36ae6b3fc7679d819f05402b14b2fb74a31507b4

%if %{do_kabichk}
%endif

%description
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions of the
operating system: memory allocation, process allocation, device input
and output, etc.


%package headers
Provides: gitsha(ssh://git@code.citrite.net/XSU/linux-stable.git) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
Provides: gitsha(ssh://git@code.citrite.net/XS/linux.pg.git) = 36ae6b3fc7679d819f05402b14b2fb74a31507b4
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
Provides: gitsha(ssh://git@code.citrite.net/XSU/linux-stable.git) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
Provides: gitsha(ssh://git@code.citrite.net/XS/linux.pg.git) = 36ae6b3fc7679d819f05402b14b2fb74a31507b4
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
Provides: gitsha(ssh://git@code.citrite.net/XSU/linux-stable.git) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
Provides: gitsha(ssh://git@code.citrite.net/XS/linux.pg.git) = 36ae6b3fc7679d819f05402b14b2fb74a31507b4
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
Provides: gitsha(ssh://git@code.citrite.net/XSU/linux-stable.git) = dffbba4348e9686d6bf42d54eb0f2cd1c4fb3520
Provides: gitsha(ssh://git@code.citrite.net/XS/linux.pg.git) = 36ae6b3fc7679d819f05402b14b2fb74a31507b4
Summary: %{pythonperfsum}
Provides: python2-perf
%description -n python2-perf
%{pythonperfdesc}

%prep
%autosetup -p1
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
echo %{version}-%{release} > .xsversion
make silentoldconfig
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
  make EXTRA_CFLAGS="${RPM_OPT_FLAGS}" LDFLAGS="%{__global_ldflags}" %{?cross_opts} V=1 NO_PERF_READ_VDSO32=1 NO_PERF_READ_VDSOX32=1 WERROR=0 HAVE_CPLUS_DEMANGLE=1 NO_GTK2=1 NO_STRLCPY=1 NO_BIONIC=1 NO_JVMTI=1 prefix=%{_prefix}
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

%{?_cov_results_package}

%changelog
* Fri May 13 2022 Andrew Lindh <andrew@netplex.net>
- Fix UEFI Dom0 boot EFIFB with 64 bit BAR from Xen (from kernel 5.17)

* Thu Jan 13 2022 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-7.0.14.1
- Security update based on XS82E036 (XSA-392)
- Remove new Citrix Commercial COPYING file that doesn't concern us (we don't ship their logo)
- *** Upstream changelog ***
- * Thu Dec 09 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.14
- - CP-37340: Clarify licensing and conform to Fedora packaging guidelines
- - CA-361715: Limit netback rx queue length (XSA-392)

* Wed Oct 27 2021 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-7.0.13.1
- Bugfix update based on XS82E034
- *** Upstream changelog ***
- * Mon Sep 20 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.13
- - CA-358056: CVE-2021-3444: bpf: Fix truncation handling for mod32 dst reg wrt zero
- - CA-358059: CVE-2021-3600: bpf: Fix 32 bit src register truncation on div/mod
- - CA-357418: Fix race in set_evtchn_to_irq
- - CA-356822: CVE-2021-33909: size_t-to-int vulnerability in Linux's filesystem layer
- - CA-354789: Backport upstream patch to fix warning in evtchn_interrupt()

* Thu Jul 29 2021 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-7.0.12.1
- Bugfix update based on XS82E030
- *** Upstream changelog ***
- * Fri Jun 18 2021 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.12
- - CA-353048: Add new paravirt function for ioperm() syscall support
- - CA-353093: CVE-2021-29154: Validate computation of branch displacements for x86
- - CA-355291: Fix affinity setting for xen-dyn-lateeoi IRQs

* Tue Mar 30 2021 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-7.0.11.1
- Security (XSAs 367 and 371) and bugfix update
- XSA-367: Linux: netback fails to honor grant mapping errors
- XSA-371: Linux: blkback driver may leak persistent grants
- Patches backported from linus kernel to fix event-related issues caused by XSA-332
- Remove xsa332-linux-fix-perfs.patch, not needed anymore
- *** Upstream changelog ***
- * Fri Mar 19 2021 Lin Liu <lin.liu@citrix.com> - 4.19.19-7.0.11
- - CA-349120: Backport patches to fix spurious event-related warnings
- - CA-352473: XSA-367: Linux: netback fails to honor grant mapping errors
- - CA-352682: XSA-371: Linux: blkback driver may leak persistent grants

* Wed Feb 24 2021 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-7.0.10.1
- Security update
- Fix XSAs 361 362 365
- Fix use-after-free in xen-netback caused by XSA-332
- See https://xenbits.xen.org/xsa/
- *** Upstream changelog ***
- * Wed Feb 04 2021 Igor Druzhinin <igor.druzhinin@citrix.com> - 4.19.19-7.0.10
- - CA-351672: XSA-361: Linux: grant mapping error handling issues
- - CA-351671: XSA-362: Linux: backends treating grant mapping errors as bug
- - CA-351597: Fix use-after-free in xen-netback caused by XSA-332
- - CA-351723: XSA-365: Linux: error handling issues in blkback's grant mapping
- - CA-351672: XSA-361: More grant mapping error handling issues

* Thu Feb 11 2021 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-7.0.9.2
- Fix network perf issue caused by XSA 332 patches
- Related to https://github.com/xcp-ng/xcp/issues/453

* Wed Dec 16 2020 Samuel Verschelde <stormi-xcp@ylix.fr> - 4.19.19-7.0.9.1
- Security update (XSAs 349 and 350)
- Sync to 4.19.19-7.0.9

* Thu Dec 03 2020 Sergey Dyasli <sergey.dyasli@citrix.com> - 4.19.19-7.0.9
- CA-349623: XSA-349 - Frontends can trigger OOM in Backends by update a watched path
- CA-349624: XSA-350 - Use after free triggered by block frontend in Linux blkback

* Wed Oct 07 2020 Ross Lagerwall <ross.lagerwall@citrix.com> - 4.19.19-7.0.8
- CA-346372: Add fix for XSA-331
- CA-346374: Add fix for XSA-332

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
