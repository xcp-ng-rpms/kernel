%global package_speccommit ab0ac59fd53959995355c0cc3d845e75e7d60f94
%global usver 4.19.325
%global cipver 137
%global xsver 8.0.51
%global xsrel cip%{cipver}.%{xsver}%{?xscount}%{?xshash}
%global package_srccommit refs/tags/v%{usver}-cip%{cipver}
%define uname 4.19.325-cip137
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

# XCP-ng BEGIN: remove support for livepatching support
# %%define lp_devel_dir %%{_usrsrc}/kernel-%%{version}-%%{release}
#
# # Prevent RPM adding Provides/Requires to lp-devel package
# %%global __provides_exclude_from ^%%{lp_devel_dir}/.*$
# %%global __requires_exclude_from ^%%{lp_devel_dir}/.*$
# XCP-ng END

# Be strict when applying patches
%if 0%{?xenserver} < 9
%global __patch /bin/patch -F0
%endif

Name: kernel
License: GPLv2
Version: %{usver}
Release: %{?xsrel}.1.kernelpreview.1%{?dist}
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

Source0: linux-cip-4.19.325-cip137.tar.gz
Source1: kernel-x86_64.config
Source2: macros.kernel
%if %{do_kabichk}
Source3: check-kabi
Source4: Module.kabi
%endif
Source5: prepare-build

# The patch-queue was exported with the following command:
#  git-spec-patches -o SOURCES/ v4.19.19..kernel/xcpng-4.19.19-8.0.51.1/patched v4.19.325-cip137..kernel/xcpng-4.19.325-cip137.8.0.51.1/patched-manual
# kernel/xcpng-4.19.19-8.0.51.1/patched: 8bfcf95dbb4e crypto: x86/aesni-gcm - fix crash on empty plaintext
# kernel/xcpng-4.19.325-cip137.8.0.51.1/patched-manual: cd36b00fcfea localversion-st: rm to avoid conflicts with yum's rpm version constraints.

# Patch0: 8c763a3cf502 ("Fix "net: ipv4: do not handle duplicate fragments as overlapping"")
# Patch1: d8099663adc9 ("xen/privcmd: allow fetching resource sizes")
# Patch2: 1bf6a186c452 ("block: genhd: add 'groups' argument to device_add_disk")
# Patch3: ea7ac82cf4d8 ("nvme: register ns_id attributes as default sysfs groups")
# Patch4: 9ac5917a1d28 ("mm: zero remaining unavailable struct pages")
# Patch5: f19a50c1e3ba ("mm: return zero_resv_unavail optimization")
# Patch6: 0a69047d8235 ("mm/page_alloc.c: fix uninitialized memmaps on a partially populated last section")
Patch7: mtip32xx-fully-switch-to-the-generic-DMA-API.patch
Patch8: mtip32xx-clean-an-indentation-issue-remove-extraneou.patch
# Patch9: 4d7cf69b77ce ("GFS2: Flush the GFS2 delete workqueue before stopping the kernel threads")
Patch10: scsi-libfc-retry-PRLI-if-we-cannot-analyse-the-paylo.patch
Patch11: gfs2-improve-debug-information-when-lvb-mismatches-a.patch
# Patch12: 48b128cddb91 ("gfs2: Don't set GFS2_RDF_UPTODATE when the lvb is updated")
# Patch13: f3afad5d1eff ("gfs2: slow the deluge of io error messages")
Patch14: gfs2-Use-fs_-functions-instead-of-pr_-function-where.patch
Patch15: gfs2-getlabel-support.patch
Patch16: gfs2-Always-check-the-result-of-gfs2_rbm_from_block.patch
Patch17: gfs2-Clean-up-out-of-bounds-check-in-gfs2_rbm_from_b.patch
Patch18: gfs2-Move-rs_-sizehint-rgd_gh-fields-into-the-inode.patch
Patch19: gfs2-Remove-unused-RGRP_RSRV_MINBYTES-definition.patch
Patch20: gfs2-Rename-bitmap.bi_-len-bytes.patch
Patch21: gfs2-Fix-some-minor-typos.patch
# Patch22: fa3fe5f442ab ("gfs2: Fix marking bitmaps non-full")
Patch23: gfs2-Remove-unnecessary-gfs2_rlist_alloc-parameter.patch
Patch24: gfs2-Pass-resource-group-to-rgblk_free.patch
Patch25: gfs2-write-revokes-should-traverse-sd_ail1_list-in-r.patch
Patch26: gfs2-Fix-minor-typo-couln-t-versus-couldn-t.patch
Patch27: mtip32xx-move-the-blk_rq_map_sg-call-to-mtip_hw_subm.patch
Patch28: mtip32xx-merge-mtip_submit_request-into-mtip_queue_r.patch
Patch29: mtip32xx-return-a-blk_status_t-from-mtip_send_trim.patch
Patch30: mtip32xx-remove-__force_bit2int.patch
Patch31: mtip32xx-add-missing-endianess-annotations-on-struct.patch
Patch32: mtip32xx-remove-mtip_init_cmd_header.patch
Patch33: mtip32xx-remove-mtip_get_int_command.patch
Patch34: mtip32xx-don-t-use-req-special.patch
Patch35: mtip32xxx-use-for_each_sg.patch
Patch36: mtip32xx-avoid-using-semaphores.patch
Patch37: mtip32xx-use-BLK_STS_DEV_RESOURCE-for-device-resourc.patch
# Patch38: 63715c1f0a67 ("cifs: Limit memory used by lock request calls to a page")
# Patch39: c818b5b47181 ("always clear the X2APIC_ENABLE bit for PV guest")
# Patch40: 73c1ca2dda37 ("xen/pciback: Check dev_data before using it")
Patch41: gfs2-changes-to-gfs2_log_XXX_bio.patch
Patch42: gfs2-Remove-vestigial-bd_ops.patch
Patch43: gfs2-properly-initial-file_lock-used-for-unlock.patch
Patch44: gfs2-Clean-up-gfs2_is_-ordered-writeback.patch
Patch45: gfs2-Fix-the-gfs2_invalidatepage-description.patch
Patch46: gfs2-add-more-timing-info-to-journal-recovery-proces.patch
Patch47: gfs2-add-a-helper-function-to-get_log_header-that-ca.patch
Patch48: gfs2-Dump-nrpages-for-inodes-and-their-glocks.patch
# Patch49: 7baf8fd1ffff ("gfs2: take jdata unstuff into account in do_grow")
# Patch50: afb4717ab81b ("dlm: fix invalid free")
Patch51: dlm-don-t-allow-zero-length-names.patch
# Patch52: 5c2a3997ae5b ("dlm: don't leak kernel pointer to userspace")
# Patch53: ee9268a9b55b ("dlm: Don't swamp the CPU with callbacks queued during recovery")
# Patch54: ed22415081ed ("dlm: fix possible call to kfree() for non-initialized pointer")
# Patch55: 1bcac298b943 ("dlm: fix missing idr_destroy for recover_idr")
# Patch56: 3b0107ca80fb ("dlm: NULL check before kmem_cache_destroy is not needed")
Patch57: dlm-NULL-check-before-some-freeing-functions-is-not-.patch
# Patch58: 446a04d879a0 ("dlm: fix invalid cluster name warning")
# Patch59: 8b9be9db8a2a ("gfs2: Revert "Fix loop in gfs2_rbm_find"")
# Patch60: e546c8787e7b ("scsi: libfc: free skb when receiving invalid flogi resp")
# Patch61: 29f7b376d399 ("Revert "scsi: libfc: Add WARN_ON() when deleting rports"")
# Patch62: eb5e6869125f ("net: crypto set sk to NULL when af_alg_release.")
# Patch63: 947fc52b6bf4 ("xen-netback: fix occasional leak of grant ref mappings under memory pressure")
# Patch64: e5e5840183de ("xen-netback: don't populate the hash cache on XenBus disconnect")
# Patch65: 4f5a4c888106 ("gfs2: Fix missed wakeups in find_insert_glock")
Patch66: gfs2-Fix-an-incorrect-gfs2_assert.patch
Patch67: ACPI-APEI-Fix-possible-out-of-bounds-access-to-BERT-.patch
# Patch68: d60f458e4c4d ("efi: cper: Fix possible out-of-bounds access")
Patch69: gfs-no-need-to-check-return-value-of-debugfs_create-.patch
# Patch70: a629c32ac2d1 ("scsi: iscsi: flush running unbind operations when removing a session")
# Patch71: ed3adb562fc8 ("xen: Prevent buffer overflow in privcmd ioctl")
# Patch72: ee4b8e266229 ("Revert "scsi: fcoe: clear FC_RP_STARTED flags when receiving a LOGO"")
# Patch73: bac852089281 ("gfs2: Fix lru_count going negative")
Patch74: gfs2-clean_journal-improperly-set-sd_log_flush_head.patch
# Patch75: c4b51dbcccfc ("gfs2: Fix occasional glock use-after-free")
Patch76: gfs2-Replace-gl_revokes-with-a-GLF-flag.patch
Patch77: gfs2-Remove-misleading-comments-in-gfs2_evict_inode.patch
Patch78: gfs2-Rename-sd_log_le_-revoke-ordered.patch
Patch79: gfs2-Rename-gfs2_trans_-add_unrevoke-remove_revoke.patch
Patch80: iomap-Clean-up-__generic_write_end-calling.patch
Patch81: fs-Turn-__generic_write_end-into-a-void-function.patch
Patch82: iomap-Fix-use-after-free-error-in-page_done-callback.patch
Patch83: iomap-Add-a-page_prepare-callback.patch
Patch84: gfs2-Fix-iomap-write-page-reclaim-deadlock.patch
Patch85: fs-mark-expected-switch-fall-throughs.patch
Patch86: gfs2-Fix-loop-in-gfs2_rbm_find-v2.patch
Patch87: gfs2-Remove-unnecessary-extern-declarations.patch
Patch88: gfs2-fix-race-between-gfs2_freeze_func-and-unmount.patch
Patch89: gfs2-read-journal-in-large-chunks.patch
Patch90: gfs2-Fix-error-path-kobject-memory-leak.patch
Patch91: SUNRPC-Ensure-that-the-transport-layer-respect-major.patch
Patch92: SUNRPC-Start-the-first-major-timeout-calculation-at-.patch
# Patch93: fdc78eedc54d ("gfs2: Fix sign extension bug in gfs2_update_stats")
Patch94: Revert-gfs2-Replace-gl_revokes-with-a-GLF-flag.patch
Patch95: gfs2-Fix-rounding-error-in-gfs2_iomap_page_prepare.patch
Patch96: iomap-don-t-mark-the-inode-dirty-in-iomap_write_end.patch
Patch97: gfs2-Clean-up-freeing-struct-gfs2_sbd.patch
Patch98: gfs2-Use-IS_ERR_OR_NULL.patch
Patch99: gfs2-kthread-and-remount-improvements.patch
Patch100: gfs2-eliminate-tr_num_revoke_rm.patch
Patch101: gfs2-log-which-portion-of-the-journal-is-replayed.patch
Patch102: gfs2-Warn-when-a-journal-replay-overwrites-a-rgrp-wi.patch
Patch103: gfs2-Rename-SDF_SHUTDOWN-to-SDF_WITHDRAWN.patch
Patch104: gfs2-simplify-gfs2_freeze-by-removing-case.patch
Patch105: gfs2-dump-fsid-when-dumping-glock-problems.patch
Patch106: gfs2-replace-more-printk-with-calls-to-fs_info-and-f.patch
Patch107: gfs2-use-page_offset-in-gfs2_page_mkwrite.patch
Patch108: gfs2-remove-the-unused-gfs2_stuffed_write_end-functi.patch
Patch109: gfs2-merge-gfs2_writeback_aops-and-gfs2_ordered_aops.patch
Patch110: gfs2-merge-gfs2_writepage_common-into-gfs2_writepage.patch
Patch111: gfs2-mark-stuffed_readpage-static.patch
Patch112: gfs2-use-iomap_bmap-instead-of-generic_block_bmap.patch
Patch113: gfs2-don-t-use-buffer_heads-in-gfs2_allocate_page_ba.patch
Patch114: gfs2-Remove-unused-gfs2_iomap_alloc-argument.patch
# Patch115: e7a41b276974 ("dlm: check if workqueues are NULL before flushing/destroying")
Patch116: dlm-no-need-to-check-return-value-of-debugfs_create-.patch
Patch117: gfs2-Inode-dirtying-fix.patch
# Patch118: 21344f0575f0 ("gfs2: gfs2_walk_metadata fix")
# Patch119: d093d3183ca2 ("nbd: add missing config put")
# Patch120: 2bc2a90a083a ("xen/pci: reserve MCFG areas earlier")
# Patch121: 09ec6c6783ff ("kernel/module.c: Only return -EEXIST for modules that have finished loading")
# Patch122: b72ea6ec83be ("net/mlx5e: Force CHECKSUM_UNNECESSARY for short ethernet frames")
# Patch123: 4190a7bcd2af ("net/mlx4_en: Force CHECKSUM_NONE for short ethernet frames")
# Patch124: b4d965a37d89 ("cifs: allow calling SMB2_xxx_free(NULL)")
# Patch125: 71a47ed651c0 ("cifs: fail i/o on soft mounts if sessionsetup errors out")
# Patch126: 944c58523731 ("random: add a spinlock_t to struct batched_entropy")
# Patch127: c09be31461ed ("tcp: limit payload size of sacked skbs")
# Patch128: ec83921899a5 ("tcp: tcp_fragment() should apply sane memory limits")
# Patch129: 7f9f8a37e563 ("tcp: add tcp_min_snd_mss sysctl")
# Patch130: 59222807fcc9 ("tcp: enforce tcp_min_snd_mss in tcp_mtu_probing()")
# Patch131: dad3a9314ac9 ("tcp: refine memory limit test in tcp_fragment()")
# Patch132: 007e5aaf287c ("xen/events: fix binding user event channels to cpus")
# Patch133: e73db096691e ("xen: let alloc_xenballooned_pages() fail if not enough memory free")
# Patch134: 6323c238bb43 ("tcp: be more careful in tcp_fragment()")
# Patch135: 259f9d9a290e ("random: always use batched entropy for get_random_u{32,64}")
# Patch136: 014ee1c7d184 ("xen-blkback: set ring->xenblkd to NULL after kthread_stop()")
# Patch137: b0be61a5a59e ("block: cleanup __blkdev_issue_discard()")
# Patch138: f387897cf5b8 ("block: fix 32 bit overflow in __blkdev_issue_discard()")
# Patch139: 3491857f4292 ("scsi: libiscsi: Fix race between iscsi_xmit_task and iscsi_complete_task")
# Patch140: b3410f0f8505 ("xen/netback: Reset nr_frags before freeing skb")
# Patch141: 99952b08537c ("openvswitch: change type of UPCALL_PID attribute to NLA_UNSPEC")
Patch142: gfs2-gfs2_iomap_begin-cleanup.patch
Patch143: gfs2-Add-support-for-IOMAP_ZERO.patch
Patch144: gfs2-implement-gfs2_block_zero_range-using-iomap_zer.patch
Patch145: gfs2-Minor-gfs2_alloc_inode-cleanup.patch
Patch146: gfs2-Always-mark-inode-dirty-in-fallocate.patch
Patch147: gfs2-untangle-the-logic-in-gfs2_drevalidate.patch
Patch148: gfs2-Fix-possible-fs-name-overflows.patch
Patch149: gfs2-Fix-recovery-slot-bumping.patch
Patch150: gfs2-Minor-PAGE_SIZE-arithmetic-cleanups.patch
Patch151: gfs2-Delete-an-unnecessary-check-before-brelse.patch
Patch152: gfs2-separate-holder-for-rgrps-in-gfs2_rename.patch
Patch153: gfs2-create-function-gfs2_glock_update_hold_time.patch
Patch154: gfs2-Use-async-glocks-for-rename.patch
Patch155: gfs2-Improve-mmap-write-vs.-truncate-consistency.patch
# Patch156: e0c1e6e55bca ("gfs2: clear buf_in_tr when ending a transaction in sweep_bh_for_rgrps")
# Patch157: 90a886b68faa ("xen/efi: Set nonblocking callbacks")
# Patch158: 1d5cb12a2539 ("net: fix sk_page_frag() recursion from memory reclaim")
Patch159: drm-i915-gvt-Allow-F_CMD_ACCESS-on-mmio-0x21f0.patch
Patch160: gfs2-add-compat_ioctl-support.patch
Patch161: gfs2-removed-unnecessary-semicolon.patch
Patch162: gfs2-Some-whitespace-cleanups.patch
Patch163: gfs2-Improve-mmap-write-vs.-punch_hole-consistency.patch
Patch164: gfs2-Multi-block-allocations-in-gfs2_page_mkwrite.patch
Patch165: gfs2-Fix-end-of-file-handling-in-gfs2_page_mkwrite.patch
Patch166: gfs2-Remove-active-journal-side-effect-from-gfs2_wri.patch
Patch167: gfs2-make-gfs2_log_shutdown-static.patch
# Patch168: 0809e1087c3d ("gfs2: fix glock reference problem in gfs2_trans_remove_revoke")
Patch169: gfs2-Introduce-function-gfs2_withdrawn.patch
Patch170: gfs2-fix-infinite-loop-in-gfs2_ail1_flush-on-io-erro.patch
Patch171: gfs2-Don-t-loop-forever-in-gfs2_freeze-if-withdrawn.patch
Patch172: gfs2-Abort-gfs2_freeze-if-io-error-is-seen.patch
Patch173: gfs2-Close-timing-window-with-GLF_INVALIDATE_IN_PROG.patch
# Patch174: 19709adfd7cd ("gfs2: clean up iopen glock mess in gfs2_create_inode")
Patch175: gfs2-Remove-duplicate-call-from-gfs2_create_inode.patch
Patch176: gfs2-Don-t-write-log-headers-after-file-system-withd.patch
Patch177: xen-events-remove-event-handling-recursion-detection.patch
Patch178: gfs2-Another-gfs2_find_jhead-fix.patch
Patch179: gfs2-eliminate-ssize-parameter-from-gfs2_struct2blk.patch
Patch180: gfs2-minor-cleanup-remove-unneeded-variable-ret-in-g.patch
Patch181: gfs2-Avoid-access-time-thrashing-in-gfs2_inode_looku.patch
Patch182: gfs2-Fix-incorrect-variable-name.patch
Patch183: gfs2-Remove-GFS2_MIN_LVB_SIZE-define.patch
Patch184: fs-gfs2-remove-unused-IS_DINODE-and-IS_LEAF-macros.patch
Patch185: gfs2-remove-unused-LBIT-macros.patch
Patch186: Revert-gfs2-eliminate-tr_num_revoke_rm.patch
Patch187: gfs2-fix-gfs2_find_jhead-that-returns-uninitialized-.patch
# Patch188: e57e77e9321c ("gfs2: move setting current->backing_dev_info")
# Patch189: 4b67a516c63d ("gfs2: fix O_SYNC write handling")
Patch190: drm-i915-gvt-fix-high-order-allocation-failure-on-la.patch
Patch191: drm-i915-gvt-Add-mutual-lock-for-ppgtt-mm-LRU-list.patch
Patch192: drm-i915-gvt-more-locking-for-ppgtt-mm-LRU-list.patch
# Patch193: d0f7d0913862 ("xenbus: req->body should be updated before req->state")
# Patch194: c4e8290c6fdf ("xenbus: req->err should be updated before req->state")
# Patch195: 777179200cb8 ("gfs2_atomic_open(): fix O_EXCL|O_CREAT handling on cold dcache")
Patch196: gfs2-Split-gfs2_lm_withdraw-into-two-functions.patch
Patch197: gfs2-Report-errors-before-withdraw.patch
Patch198: gfs2-Remove-usused-cluster_wide-arguments-of-gfs2_co.patch
Patch199: gfs2-Turn-gfs2_consist-into-void-functions.patch
Patch200: gfs2-Return-bool-from-gfs2_assert-functions.patch
Patch201: gfs2-Introduce-concept-of-a-pending-withdraw.patch
Patch202: gfs2-clear-ail1-list-when-gfs2-withdraws.patch
Patch203: gfs2-Rework-how-rgrp-buffer_heads-are-managed.patch
Patch204: gfs2-log-error-reform.patch
Patch205: gfs2-Only-complain-the-first-time-an-io-error-occurs.patch
Patch206: gfs2-Ignore-dlm-recovery-requests-if-gfs2-is-withdra.patch
Patch207: gfs2-move-check_journal_clean-to-util.c-for-future-u.patch
Patch208: gfs2-Allow-some-glocks-to-be-used-during-withdraw.patch
Patch209: gfs2-Force-withdraw-to-replay-journals-and-wait-for-.patch
Patch210: gfs2-fix-infinite-loop-when-checking-ail-item-count-.patch
Patch211: gfs2-Add-verbose-option-to-check_journal_clean.patch
Patch212: gfs2-Issue-revokes-more-intelligently.patch
Patch213: gfs2-Prepare-to-withdraw-as-soon-as-an-IO-error-occu.patch
Patch214: gfs2-Check-for-log-write-errors-before-telling-dlm-t.patch
Patch215: gfs2-Do-log_flush-in-gfs2_ail_empty_gl-even-if-ail-l.patch
Patch216: gfs2-Withdraw-in-gfs2_ail1_flush-if-write_cache_page.patch
Patch217: gfs2-drain-the-ail2-list-after-io-errors.patch
# Patch218: 09f8ac747f36 ("gfs2: Don't demote a glock until its revokes are written")
Patch219: gfs2-Do-proper-error-checking-for-go_sync-family-of-.patch
Patch220: gfs2-flesh-out-delayed-withdraw-for-gfs2_log_flush.patch
Patch221: gfs2-don-t-allow-releasepage-to-free-bd-still-used-f.patch
Patch222: gfs2-allow-journal-replay-to-hold-sd_log_flush_lock.patch
Patch223: gfs2-leaf_dealloc-needs-to-allocate-one-more-revoke.patch
Patch224: gfs2-Additional-information-when-gfs2_ail1_flush-wit.patch
Patch225: gfs2-Clean-up-inode-initialization-and-teardown.patch
Patch226: gfs2-Switch-to-list_-first-last-_entry.patch
Patch227: gfs2-eliminate-gfs2_rsqa_alloc-in-favor-of-gfs2_qa_a.patch
Patch228: gfs2-Change-inode-qa_data-to-allow-multiple-users.patch
Patch229: gfs2-Split-gfs2_rsqa_delete-into-gfs2_rs_delete-and-.patch
Patch230: gfs2-Remove-unnecessary-gfs2_qa_-get-put-pairs.patch
Patch231: gfs2-don-t-lock-sd_log_flush_lock-in-try_rgrp_unlink.patch
Patch232: gfs2-instrumentation-wrt-ail1-stuck.patch
Patch233: gfs2-change-from-write-to-read-lock-for-sd_log_flush.patch
Patch234: gfs2-Fix-oversight-in-gfs2_ail1_flush.patch
Patch235: gfs2-If-go_sync-returns-error-withdraw-but-skip-inva.patch
Patch236: dlm-Switch-to-using-wait_event.patch
Patch237: dlm-use-the-tcp-version-of-accept_from_sock-for-sctp.patch
Patch238: net-add-sock_set_reuseaddr.patch
Patch239: net-add-sock_set_sndtimeo.patch
Patch240: net-add-sock_set_keepalive.patch
Patch241: net-add-sock_set_rcvbuf.patch
Patch242: tcp-add-tcp_sock_set_nodelay.patch
Patch243: sctp-add-sctp_sock_set_nodelay.patch
Patch244: tcp-add-tcp_sock_set_user_timeout.patch
Patch245: dlm-dlm_internal-Replace-zero-length-array-with-flex.patch
Patch246: dlm-user-Replace-zero-length-array-with-flexible-arr.patch
Patch247: fs-dlm-remove-unneeded-semicolon-in-rcom.c.patch
# Patch248: 68728008569c ("dlm: remove BUG() before panic()")
Patch249: gfs2-fix-withdraw-sequence-deadlock.patch
Patch250: gfs2-Fix-error-exit-in-do_xmote.patch
Patch251: gfs2-Fix-BUG-during-unmount-after-file-system-withdr.patch
Patch252: gfs2-Fix-use-after-free-in-gfs2_logd-after-withdraw.patch
# Patch253: 9663d294ae28 ("block: call rq_qos_exit() after queue is frozen")
# Patch254: 8343dffacc1b ("scsi: libfc: free response frame from GPN_ID")
# Patch255: 41722344981f ("xen/xenbus: ensure xenbus_map_ring_valloc() returns proper grant status")
# Patch256: b7e389235cfe ("treewide: Remove uninitialized_var() usage")
# Patch257: 6a2db034f9b3 ("dlm: Fix kobject memleak")
Patch258: net-sock-add-sock_set_mark.patch
Patch259: fs-dlm-set-skb-mark-for-listen-socket.patch
Patch260: fs-dlm-set-skb-mark-per-peer-socket.patch
Patch261: fs-dlm-don-t-close-socket-on-invalid-message.patch
Patch262: fs-dlm-change-handling-of-reconnects.patch
Patch263: fs-dlm-implement-tcp-graceful-shutdown.patch
# Patch264: b3ddf6ba5e28 ("ext4: fix potential negative array index in do_split()")
Patch265: fs-dlm-synchronize-dlm-before-shutdown.patch
Patch266: fs-dlm-make-connection-hash-lockless.patch
Patch267: fs-dlm-fix-dlm_local_addr-memory-leak.patch
# Patch268: 13296b64a81c ("fs: dlm: fix configfs memory leak")
Patch269: fs-dlm-move-free-writequeue-into-con-free.patch
Patch270: fs-dlm-handle-possible-othercon-writequeues.patch
Patch271: fs-dlm-use-free_con-to-free-connection.patch
Patch272: fs-dlm-remove-lock-dependency-warning.patch
Patch273: fs-dlm-fix-mark-per-nodeid-setting.patch
Patch274: fs-dlm-handle-range-check-as-callback.patch
Patch275: fs-dlm-disallow-buffer-size-below-default.patch
Patch276: fs-dlm-rework-receive-handling.patch
Patch277: fs-dlm-fix-race-in-nodeid2con.patch
# Patch278: 61d359d51a1c ("xen/events: avoid removing an event channel while handling it")
# Patch279: 25f6b08895d5 ("xen/events: add a proper barrier to 2-level uevent unmasking")
# Patch280: c7f95d899f49 ("xen/events: fix race in evtchn_fifo_unmask()")
# Patch281: dea09436da03 ("xen/events: add a new "late EOI" evtchn framework")
# Patch282: 1506109a85c8 ("xen/blkback: use lateeoi irq binding")
# Patch283: 6a052f3a6282 ("xen/netback: use lateeoi irq binding")
# Patch284: fb22061b20ea ("xen/scsiback: use lateeoi irq binding")
# Patch285: 128b11967a26 ("xen/pvcallsback: use lateeoi irq binding")
# Patch286: 4988884d53c0 ("xen/pciback: use lateeoi irq binding")
# Patch287: 8363670c4d0b ("xen/events: switch user event channels to lateeoi model")
# Patch288: 536075098940 ("xen/events: use a common cpu hotplug hook for event channels")
# Patch289: 17ef715c0c88 ("xen/events: defer eoi in case of excessive number of events")
# Patch290: c1f90a9cd988 ("xen/events: block rogue events for some time")
Patch291: xen-events-unmask-a-fifo-event-channel-only-if-it-wa.patch
Patch292: fs-dlm-fix-proper-srcu-api-call.patch
Patch293: fs-dlm-define-max-send-buffer.patch
Patch294: fs-dlm-add-get-buffer-error-handling.patch
Patch295: fs-dlm-flush-othercon-at-close.patch
Patch296: fs-dlm-handle-non-blocked-connect-event.patch
Patch297: fs-dlm-add-helper-for-init-connection.patch
Patch298: fs-dlm-move-connect-callback-in-node-creation.patch
Patch299: fs-dlm-move-shutdown-action-to-node-creation.patch
Patch300: fs-dlm-refactor-sctp-sock-parameter.patch
Patch301: fs-dlm-listen-socket-out-of-connection-hash.patch
Patch302: fs-dlm-fix-check-for-multi-homed-hosts.patch
Patch303: fs-dlm-constify-addr_compare.patch
Patch304: fs-dlm-check-on-existing-node-address.patch
# Patch305: 7740c404d068 ("xen/netback: avoid race in xenvif_rx_ring_slots_available()")
# Patch306: dfed59ee4b41 ("Xen/x86: don't bail early from clear_foreign_p2m_mapping()")
# Patch307: c3d586afdb44 ("Xen/x86: also check kernel mapping in set_foreign_p2m_mapping()")
# Patch308: ba75f4393225 ("Xen/gntdev: correct dev_bus_addr handling in gntdev_map_grant_pages()")
# Patch309: e07f06f6bbee ("Xen/gntdev: correct error checking in gntdev_map_grant_pages()")
# Patch310: a01b49a9bf91 ("xen-blkback: don't "handle" error by BUG()")
# Patch311: 717faa776ca2 ("xen-netback: don't "handle" error by BUG()")
# Patch312: f84c00fbd27b ("xen-scsiback: don't "handle" error by BUG()")
# Patch313: 98f16e171e28 ("xen-blkback: fix error handling in xen_blkbk_map()")
# Patch314: 135ba06d0bf8 ("xen/netback: fix spurious event detection for common event case")
Patch315: xen-evtchn-use-smp-barriers-for-user-event-ring.patch
Patch316: xen-evtchn-use-READ-WRITE_ONCE-for-accessing-ring-in.patch
# Patch317: a6a76d7234cc ("xen/events: reset affinity of 2-level event when tearing it down")
# Patch318: 3a19f808cb2b ("xen/events: don't unmask an event channel when an eoi is pending")
# Patch319: d8887e85efca ("xen/events: avoid handling the same event on two cpus at the same time")
Patch320: x86-ioperm-Add-new-paravirt-function-update_io_bitma.patch
# Patch321: 1a999d25ef53 ("Xen/gnttab: handle p2m update errors on a per-slot basis")
# Patch322: b62d8b5c814b ("xen-netback: respect gnttab_map_refs()'s return value")
# Patch323: 16356ddb5878 ("xen-blkback: don't leak persistent grants from xen_blkbk_map()")
# Patch324: 5f26f1f838aa ("bpf, x86: Validate computation of branch displacements for x86-64")
# Patch325: 7b77ae2a0d6f ("bpf, x86: Validate computation of branch displacements for x86-32")
# Patch326: d9ab90118cf9 ("xen/events: fix setting irq affinity")
# Patch327: 1de7644eac41 ("xen/netback: fix rx queue stall detection")
# Patch328: c9f17e92917f ("xen/netback: don't queue unlimited number of packages")
# Patch329: 2efaecaf9603 ("fs: dlm: fix debugfs dump")
Patch330: fs-dlm-fix-mark-setting-deadlock.patch
Patch331: fs-dlm-set-connected-bit-after-accept.patch
Patch332: fs-dlm-set-subclass-for-othercon-sock_mutex.patch
Patch333: fs-dlm-add-errno-handling-to-check-callback.patch
Patch334: fs-dlm-add-check-if-dlm-is-currently-running.patch
Patch335: fs-dlm-change-allocation-limits.patch
Patch336: fs-dlm-use-GFP_ZERO-for-page-buffer.patch
Patch337: fs-dlm-simplify-writequeue-handling.patch
Patch338: fs-dlm-check-on-minimum-msglen-size.patch
Patch339: fs-dlm-remove-unaligned-memory-access-handling.patch
Patch340: fs-dlm-flush-swork-on-shutdown.patch
Patch341: fs-dlm-add-shutdown-hook.patch
Patch342: fs-dlm-fix-missing-unlock-on-error-in-accept_from_so.patch
# Patch343: cda326e5033f ("xen/events: reset active flag for lateeoi events later")
Patch344: gfs2-fix-a-deadlock-on-withdraw-during-mount.patch
Patch345: fs-dlm-always-run-complete-for-possible-waiters.patch
Patch346: fs-dlm-add-dlm-macros-for-ratelimit-log.patch
Patch347: fs-dlm-fix-srcu-read-lock-usage.patch
Patch348: fs-dlm-set-is-othercon-flag.patch
Patch349: fs-dlm-reconnect-if-socket-error-report-occurs.patch
# Patch350: d5473f43e4fb ("fs: dlm: cancel work sync othercon")
Patch351: fs-dlm-fix-connection-tcp-EOF-handling.patch
Patch352: fs-dlm-public-header-in-out-utility.patch
Patch353: fs-dlm-add-more-midcomms-hooks.patch
Patch354: fs-dlm-make-buffer-handling-per-msg.patch
Patch355: fs-dlm-add-functionality-to-re-transmit-a-message.patch
Patch356: fs-dlm-move-out-some-hash-functionality.patch
Patch357: fs-dlm-add-union-in-dlm-header-for-lockspace-id.patch
Patch358: fs-dlm-add-reliable-connection-if-reconnect.patch
Patch359: fs-dlm-add-midcomms-debugfs-functionality.patch
Patch360: fs-dlm-don-t-allow-half-transmitted-messages.patch
Patch361: fs-dlm-Fix-memory-leak-of-object-mh.patch
Patch362: fs-dlm-Fix-spelling-mistake-stucked-stuck.patch
Patch363: fs-dlm-fix-lowcomms_start-error-case.patch
# Patch364: af02ec6cf614 ("fs: dlm: fix memory leak when fenced")
Patch365: fs-dlm-use-alloc_ordered_workqueue.patch
Patch366: fs-dlm-move-dlm-allow-conn.patch
Patch367: fs-dlm-introduce-proto-values.patch
Patch368: fs-dlm-rename-socket-and-app-buffer-defines.patch
Patch369: fs-dlm-fix-race-in-mhandle-deletion.patch
Patch370: fs-dlm-invalid-buffer-access-in-lookup-error.patch
# Patch371: 6de9f0bf7cac ("seq_file: disallow extremely large seq buffer allocations")
# Patch372: 387635925cd0 ("xen/events: Fix race in set_evtchn_to_irq")
Patch373: fs-dlm-use-sk-sk_socket-instead-of-con-sock.patch
Patch374: fs-dlm-use-READ_ONCE-for-config-var.patch
Patch375: fs-dlm-fix-typo-in-tlv-prefix.patch
Patch376: fs-dlm-clear-CF_APP_LIMITED-on-close.patch
Patch377: fs-dlm-cleanup-and-remove-_send_rcom.patch
Patch378: fs-dlm-introduce-con_next_wq-helper.patch
Patch379: fs-dlm-move-to-static-proto-ops.patch
Patch380: fs-dlm-introduce-generic-listen.patch
Patch381: fs-dlm-auto-load-sctp-module.patch
Patch382: fs-dlm-generic-connect-func.patch
Patch383: fs-dlm-fix-multiple-empty-writequeue-alloc.patch
Patch384: fs-dlm-move-receive-loop-into-receive-handler.patch
Patch385: fs-dlm-implement-delayed-ack-handling.patch
Patch386: fs-dlm-fix-return-EINTR-on-recovery-stopped.patch
Patch387: fs-dlm-avoid-comms-shutdown-delay-in-release_lockspa.patch
# Patch388: 6a9449e95688 ("iommu/vt-d: Fix agaw for a supported 48 bit guest address width")
# Patch389: c348d806ed1d ("bpf: Do not use ax register in interpreter on div/mod")
# Patch390: 8313432df224 ("bpf: Fix 32 bit src register truncation on div/mod")
# Patch391: 39f74b7c81cc ("bpf: Fix truncation handling for mod32 dst reg wrt zero")
Patch392: x86-timer-Skip-PIT-initialization-on-modern-chipsets.patch
Patch393: x86-timer-Force-PIT-initialization-when-X86_FEATURE_.patch
Patch394: x86-timer-Don-t-skip-PIT-setup-when-APIC-is-disabled.patch
Patch395: nbd-Fix-use-after-free-in-pid_show.patch
Patch396: fs-dlm-remove-check-SCTP-is-loaded-message.patch
Patch397: fs-dlm-let-handle-callback-data-as-void.patch
Patch398: fs-dlm-remove-double-list_first_entry-call.patch
Patch399: fs-dlm-don-t-call-kernel_getpeername-in-error_report.patch
Patch400: fs-dlm-replace-use-of-socket-sk_callback_lock-with-s.patch
Patch401: fs-dlm-fix-build-with-CONFIG_IPV6-disabled.patch
Patch402: fs-dlm-check-for-pending-users-filling-buffers.patch
Patch403: fs-dlm-remove-wq_alloc-mutex.patch
Patch404: fs-dlm-memory-cache-for-writequeue_entry.patch
Patch405: fs-dlm-memory-cache-for-lowcomms-hotpath.patch
Patch406: fs-dlm-print-cluster-addr-if-non-cluster-node-connec.patch
Patch407: xen-x86-obtain-upper-32-bits-of-video-frame-buffer-a.patch
Patch408: xen-x86-obtain-full-video-frame-buffer-address-for-D.patch
Patch409: dlm-uninitialized-variable-on-error-in-dlm_listen_fo.patch
Patch410: dlm-add-__CHECKER__-for-false-positives.patch
Patch411: fs-dlm-fix-grammar-in-lowcomms-output.patch
Patch412: fs-dlm-fix-race-in-lowcomms.patch
Patch413: fs-dlm-relax-sending-to-allow-receiving.patch
Patch414: fs-dlm-fix-sock-release-if-listen-fails.patch
Patch415: fs-dlm-retry-accept-until-EAGAIN-or-error-returns.patch
Patch416: fs-dlm-remove-send-repeat-remove-handling.patch
# Patch417: 756eda9bc8b7 ("xen/pvh: set xen_domain_type to HVM in xen_pvh_init")
# Patch418: 0c47135536b8 ("xen/pvh: correctly setup the PV EFI interface for dom0")
# Patch419: 2a226e8ca951 ("PCI: pciehp: Fix AB-BA deadlock between reset_lock and device_lock")
Patch420: nvme_fc-add-nvme_discovery-sysfs-attribute-to-fc-tra.patch
Patch421: ACPI-processor-Fix-evaluating-_PDC-method-when-runni.patch
# Patch422: 2440f3cebcb0 ("SUNRPC: Always drop the XPRT_LOCK on XPRT_CLOSE_WAIT")
# Patch423: b42515434f8f ("xen-netback: use default TX queue size for vifs")
Patch424: gfs2-Expect-EBUSY-after-canceling-dlm-locking-reques.patch
Patch425: gfs2-Clear-flags-when-withdraw-prevents-xmote.patch
# Patch426: d1ae006b4851 ("fs: dlm: fix race between test_bit() and queue_work()")
Patch427: xhci-show-fault-reason-for-a-failed-enable-slot-comm.patch
Patch428: gfs2-Fix-ignore-unlock-failures-after-withdraw.patch
Patch429: gfs2-finish_xmote-cleanup.patch
Patch430: gfs2-do_xmote-fixes.patch
Patch431: x86-xen-time-Reduce-Xen-timer-tick.patch
# Patch432: 16b92b031b4d ("decompress_bunzip2: fix rare decompression failure")
# Patch433: 89ede9d8b5b8 ("scsi: scsi_dh_alua: Fix possible null-ptr-deref")
# Patch434: cdd92ebe29c2 ("scsi: scsi_dh_alua: always use a 2 second delay before retrying RTPG")
# Patch435: cf372c60ed13 ("scsi: scsi_dh_alua: handle RTPG sense code correctly during state transitions")
# Patch436: 509e215d161e ("scsi: scsi_dh_alua: Avoid crash during alua_bus_detach()")
Patch437: scsi-scsi_dh_alua-Set-transitioning-state-on-Unit-At.patch
Patch438: scsi-scsi_dh_alua-Prevent-duplicate-pg-info-print-in.patch
# Patch439: 5fc6e73ba502 ("scsi: scsi_dh_alua: Remove check for ASC 24h in alua_rtpg()")
Patch440: scsi-scsi_dh_alua-Retry-RTPG-on-a-different-path-aft.patch
# Patch441: f4bde1d1bf90 ("scsi: scsi_dh_alua: Check for negative result value")
# Patch442: c021be62bbcb ("scsi: scsi_dh_alua: Fix signedness bug in alua_rtpg()")
# Patch443: c110051d335e ("scsi: scsi_dh_alua: Fix memleak for 'qdata' in alua_activate()")
Patch444: scsi-core-alua-I-O-errors-for-ALUA-state-transitions.patch
Patch445: scsi-scsi_dh_alua-Properly-handle-the-ALUA-transitio.patch
Patch446: From-07e447d39839d0401d5f44243e8e20de0e5ce9ce-Mon-Se.patch
Patch447: SUNRPC-Replace-the-queue-timer-with-a-delayed-work-f.patch
# Patch448: cad4448dfc9c ("nbd: fix possible sysfs duplicate warning")
Patch449: SUNRPC-fix-race-to-sk_err-after-xs_error_report.patch
# Patch450: 82b7c99ee141 ("nbd: protect cmd->status with cmd->lock")
# Patch451: 1f032ca298dd ("nbd: handle racing with error'ed out commands")
Patch452: SUNRPC-Fix-backchannel-RPC-soft-lockups.patch
# Patch453: d9f4534a9a28 ("nbd: fix a block_device refcount leak in nbd_release")
Patch454: nbd-Aovid-double-completion-of-a-request.patch
Patch455: nbd-don-t-handle-response-without-a-corresponding-re.patch
Patch456: nbd-make-sure-request-completion-won-t-concurrent.patch
Patch457: cdc_ether-export-usbnet_cdc_zte_rx_fixup.patch
Patch458: rndis_host-enable-the-bogus-MAC-fixup-for-ZTE-device.patch
Patch459: rndis_host-limit-scope-of-bogus-MAC-address-detectio.patch
Patch460: SUNRPC-Move-reset-of-TCP-state-variables-into-the-re.patch
Patch461: crypto-af_alg-Disallow-concurrent-writes-in-af_alg_s.patch
# Patch462: f9142f21e465 ("crypto: af_alg - zero initialize memory allocated via sock_kmalloc")
# Patch463: 949e09166db8 ("crypto: authencesn - reject too-short AAD (assoclen<8) to match ESP/ESN spec")
# Patch464: e49eb4ec3abc ("crypto: af-alg - fix NULL pointer dereference in scatterwalk")
# Patch465: 7833e91cee5c ("crypto: scatterwalk - Backport memcpy_sglist()")
# Patch466: a6eb232e2cad ("crypto: algif_aead - use memcpy_sglist() instead of null skcipher")
# Patch467: e1d60aac7af8 ("crypto: algif_aead - Revert to operating out-of-place")
# Patch468: 732cdd28b4b0 ("crypto: algif_aead - snapshot IV for async AEAD requests")
# Patch469: 9dde35139b83 ("crypto: authenc - use memcpy_sglist() instead of null skcipher")
# Patch470: 05654d734687 ("crypto: authencesn - Do not place hiseq at end of dst for out-of-place decryption")
# Patch471: 97d1348160c1 ("crypto: authencesn - Fix src offset when decrypting in-place")
# Patch472: ebd01513a069 ("crypto: af_alg - Fix page reassignment overflow in af_alg_pull_tsgl")
# Patch473: ea7be32078f1 ("crypto: algif_aead - Fix minimum RX size check for decryption")
# Patch474: 17a1144baa54 ("crypto: algif_aead - fix uninitialized ctx->init")
Patch475: crypto-af_alg-Fix-incorrect-boolean-values-in-af_alg.patch
# Patch476: d59aae60ed71 ("crypto: af_alg - Remove zero-copy support from skcipher and aead")
# Patch477: 75a578000ae5 ("inet: fully convert sk->sk_rx_dst to RCU rules")
# Patch478: 69c4a5f195a7 ("ipv4: free inet_opt and ireq_opt after an RCU grace period")
# Patch479: f1529ec771e4 ("net/xen-netback: prevent UAF in xenvif_flush_hash()")
Patch480: rcu-Add-a-hlist_nulls_unhashed_lockless-function.patch
Patch481: inet-reject-unhashed-sockets-during-established-look.patch
Patch482: nvme-fabrics-reject-I-O-to-offline-device.patch
Patch483: Add-shadow-variables-support-from-kpatch.patch
# Patch484: 9039eb22f995 ("xen/xenbus: Allow watches discard events before queueing")
# Patch485: 3a36e4af694a ("xen/xenbus: Add 'will_handle' callback support in xenbus_watch_path()")
# Patch486: b88c52d02e16 ("xen/xenbus/xen_bus_type: Support will_handle watch callback")
# Patch487: 85597c4369c9 ("xen/xenbus: Count pending messages for each watch")
# Patch488: be19047894c3 ("xenbus/xenbus_backend: Disallow pending watch messages")
# Patch489: 47eb291ba65b ("xen/xenbus: Fix granting of vmalloc'd memory")
# Patch490: b9b75a460076 ("xen-blkfront: switch kcalloc to kvcalloc for large array allocation")
# Patch491: 041497b65eb0 ("xen/blkfront: Adjust indentation in xlvbd_alloc_gendisk")
# Patch492: 5f547e7cbd84 ("xen/blkfront: fix memory allocation flags in blkfront_setup_indirect()")
# Patch493: a4af550350cc ("xen-blkfront: allow discard-* nodes to be optional")
# Patch494: dcbfd3f13b13 ("xen: sync include/xen/interface/io/ring.h with Xen's newest version")
# Patch495: b647c449f166 ("xen/blkfront: read response from backend only once")
# Patch496: 80baa77511ee ("xen/blkfront: don't take local copy of a request from the ring page")
# Patch497: f89a05402f74 ("xen/blkfront: don't trust the backend response data blindly")
# Patch498: 269d7124bcfa ("xen/blkfront: harden blkfront against event channel storms")
# Patch499: 47288968eebd ("xen-netfront: do not assume sk_buff_head list is empty in error handling")
# Patch500: a1afd826e549 ("xen-netfront: do not use ~0U as error return value for xennet_fill_frags()")
# Patch501: 4b635fc2b349 ("xen-netfront: fix potential deadlock in xennet_remove()")
# Patch502: 274c04221d91 ("xen/netfront: stop tx queues during live migration")
# Patch503: e7d1024f5b19 ("xen/netfront: read response from backend only once")
# Patch504: 26509bb5dd2f ("xen/netfront: don't read data from request on the ring page")
# Patch505: e52c0efbd23c ("xen/netfront: disentangle tx_skb_freelist")
# Patch506: e4e01b0e4b7f ("xen/netfront: don't trust the backend response data blindly")
# Patch507: 3559ca594f15 ("xen/netfront: harden netfront against event channel storms")
# Patch508: 198cdc287769 ("xen/netfront: destroy queues before real_num_tx_queues is zeroed")
# Patch509: 9699f7a70eb8 ("pvcalls-front: read all data before closing the connection")
# Patch510: 81b8519de1b4 ("pvcalls-front: don't try to free unallocated rings")
# Patch511: 05ac8a683962 ("pvcalls-front: properly allocate sk")
# Patch512: 06b919a51772 ("pvcalls-front: Avoid get_free_pages(GFP_KERNEL) under spinlock")
# Patch513: 642e26628cf9 ("pvcalls-front: fix potential null dereference")
# Patch514: 66f33b2bd2d8 ("xen/pvcalls: Remove set but not used variable")
# Patch515: 36a2e9bf242b ("pvcalls-front: don't return error when the ring is full")
# Patch516: 8d521d960aef ("xen/xenbus: don't let xenbus_grant_ring() remove grants in error case")
# Patch517: 17659846fe33 ("xen/grant-table: add gnttab_try_end_foreign_access()")
# Patch518: 423a3a50dce9 ("xen/blkfront: don't use gnttab_query_foreign_access() for mapped status")
# Patch519: 927e4eb8ddf4 ("xen/netfront: don't use gnttab_query_foreign_access() for mapped status")
# Patch520: 62a696c15cfc ("xen/scsifront: don't use gnttab_query_foreign_access() for mapped status")
# Patch521: fbc57368ea52 ("xen/gntalloc: don't use gnttab_query_foreign_access()")
# Patch522: c900f34fc134 ("xen: remove gnttab_query_foreign_access()")
# Patch523: 2466bed361f3 ("xen/9p: use alloc/free_pages_exact()")
# Patch524: f85d03f0f482 ("xen/pvcalls: use alloc/free_pages_exact()")
# Patch525: 92dc0e4a2196 ("xen/gnttab: fix gnttab_end_foreign_access() without page specified")
# Patch526: c307029d811e ("xen/netfront: react properly to failing gnttab_end_foreign_access_ref()")
# Patch527: f4a1391185e3 ("xen/blkfront: fix leaking data in shared pages")
# Patch528: 3650ac3218c1 ("xen/netfront: fix leaking data in shared pages")
# Patch529: 4b67d8e42dbb ("xen/netfront: force data bouncing when backend is untrusted")
# Patch530: 981de55fb6b5 ("xen/blkfront: force data bouncing when backend is untrusted")
# Patch531: 44dfdecc288b ("xen/netback: Ensure protocol headers don't fall in the non-linear area")
# Patch532: d3e1b6151d5d ("xen/netback: don't call kfree_skb() with interrupts disabled")
Patch533: xen-netback-remove-unused-variables-pending_idx-and-.patch
# Patch534: e14369897067 ("xen/netback: don't do grant copy across page boundary")
Patch535: xen-netback-remove-not-needed-test-in-xenvif_tx_buil.patch
# Patch536: a5353cdecd9b ("xen/netback: use same error messages for same errors")
# Patch537: 11e6919ae028 ("xen/netback: Fix buffer overrun triggered by unusual packet")
# Patch538: 3fdf2be9089b ("xen/events: replace evtchn_rwlock with RCU")
# Patch539: 5bb8270789c8 ("xen-netback: don't produce zero-size SKB frags")
Patch540: xen-netback-Fix-UAF-when-reading-statistics-data.patch
Patch541: xen-netback-defer-xenvif_mcast_addr_list_free.patch
Patch542: xen-blkback-Avoid-UAF-when-reading-I-O-statistics.patch
Patch543: xen-netback-Fix-XenBus-connection-failure-cleanup.patch
Patch544: kbuild-AFTER_LINK.patch
Patch545: expose-xsversion.patch
Patch546: blktap2.patch
Patch547: Write-each-kthread-s-pid-into-xenstore-so-that-it-ca.patch
Patch548: Several-order-4-5-allocations-are-required-when-sett.patch
Patch549: disable-EFI-Properties-table-for-Xen.patch
Patch550: net-Do-not-scrub-ignore_df-within-the-same-name-spac.patch
Patch551: enable-fragmention-gre-packets.patch
Patch552: CA-285778-emulex-nic-ip-hdr-len.patch
Patch553: cifs-Change-the-default-value-SecFlags-to-0x83.patch
Patch554: call-kexec-before-offlining-noncrashing-cpus.patch
Patch555: The-CFQ-IO-scheduler-has-the-concept-of-an-idle-IO-s.patch
Patch556: pvsproxy-uses-an-XFS-filesystem-on-top-of-a-blktap-d.patch
# Patch557: 694ec54b7826 ("scsi: libfc: Handling of extra kref")
Patch558: Don-t-select-PINCTRL.patch
Patch559: Add-50G-100G-200G-ethtool-link-modes.patch
Patch560: dma-add-dma_get_required_mask_from_max_pfn.patch
Patch561: x86-xen-correct-dma_get_required_mask-for-Xen-PV-gue.patch
Patch562: map-1MiB-1-1.patch
Patch563: If-the-host-has-more-CPUs-than-the-kernel-is-compile.patch
Patch564: dom0-detects-the-presence-of-the-ACPI-PM-timer-but-c.patch
Patch565: With-many-VMs-it-is-possible-to-hit-the-IRQ-descript.patch
Patch566: xen-balloon-hotplug-select-HOLES_IN_ZONE.patch
Patch567: pci-export-pci_probe_reset_function.patch
Patch568: xen-pciback-provide-a-reset-sysfs-file-to-try-harder.patch
Patch569: Guests-can-potentially-disable-cause-the-PCI-device-.patch
Patch570: pciback-mask-root-port-comp-timeout.patch
Patch571: Some-devices-advertise-FLReset-but-do-not-support-it.patch
Patch572: Revert-PCI-Probe-for-device-reset-support-during-enu.patch
Patch573: CA-135938-nfs-disconnect-on-rpc-retry.patch
Patch574: sunrpc-force-disconnect-on-connection-timeout.patch
Patch575: nfs_access_get_cached-may-call-__nfs_revalidate_inod.patch
Patch576: bonding-balance-slb.patch
Patch577: bridge-lock-fdb-after-garp.patch
Patch578: CP-13181-net-openvswitch-add-dropping-of-fip-and-lld.patch
Patch579: xen-ioemu-inject-msi.patch
Patch580: pv-iommu-support.patch
Patch581: Reserve-the-crashkernel-region-in-the-E820.-This-pre.patch
Patch582: xen-swiotlb-rework-early-repeat-code.patch
Patch583: CA-433052-xen-swiotlb-Check-the-segment-boundary-in-.patch
Patch584: arch-x86-xen-add-infrastruction-in-xen-to-support-gv.patch
Patch585: drm-i915-gvt-write-guest-ppgtt-entry-for-xengt-suppo.patch
Patch586: drm-i915-xengt-xengt-moudule-initial-files.patch
Patch587: drm-i915-xengt-check-on_destroy-on-pfn_to_mfn.patch
Patch588: arch-x86-xen-Import-x4.9-interface-for-ioreq.patch
Patch589: i915-gvt-xengt.c-Use-new-dm_op-instead-of-hvm_op.patch
Patch590: i915-gvt-xengt.c-New-interface-to-write-protect-PPGT.patch
Patch591: i915-gvt-xengt.c-Select-vgpu-type-according-to-low_g.patch
Patch592: drm-i915-gvt-Don-t-output-error-message-when-DomU-ma.patch
Patch593: drm-i915-gvt-xengt-Correctly-get-low-mem-max-gfn.patch
Patch594: drm-i915-gvt-Fix-dom0-call-trace-at-shutdown-or-rebo.patch
Patch595: hvm-dm_op.h-Sync-dm_op-interface-to-xen-4.9-release.patch
Patch596: drm-i915-gvt-Apply-g2h-adjust-for-GTT-mmio-access.patch
Patch597: drm-i915-gvt-Apply-g2h-adjustment-during-fence-mmio-.patch
Patch598: drm-i915-gvt-Patch-the-gma-in-gpu-commands-during-co.patch
Patch599: drm-i915-gvt-Retrieve-the-guest-gm-base-address-from.patch
Patch600: drm-i915-gvt-Align-the-guest-gm-aperture-start-offse.patch
Patch601: drm-i915-gvt-Add-support-to-new-VFIO-subregion-VFIO_.patch
Patch602: drm-i915-gvt-Implement-vGPU-status-save-and-restore-.patch
Patch603: vfio-Implement-new-Ioctl-VFIO_IOMMU_GET_DIRTY_BITMAP.patch
Patch604: drm-i915-gvt-Add-dev-node-for-vGPU-state-save-restor.patch
Patch605: drm-i915-gvt-Add-interface-to-control-the-vGPU-runni.patch
Patch606: drm-i915-gvt-Modify-the-vGPU-save-restore-logic-for-.patch
Patch607: drm-i915-gvt-Add-log-dirty-support-for-XENGT-migrati.patch
Patch608: drm-i915-gvt-xengt-Add-iosrv_enabled-to-track-iosrv-.patch
Patch609: drm-i915-gvt-Add-xengt-ppgtt-write-handler.patch
Patch610: drm-i915-gvt-xengt-Impliment-mpt-dma_map-unmap_guest.patch
Patch611: drm-i915-gvt-introduce-a-new-VFIO-region-for-vfio-de.patch
Patch612: drm-i915-gvt-change-the-return-value-of-opregion-acc.patch
Patch613: drm-i915-gvt-Rebase-the-code-to-gvt-staging-for-live.patch
Patch614: drm-i915-gvt-Apply-g2h-adjustment-to-buffer-start-gm.patch
Patch615: drm-i915-gvt-Fix-xengt-opregion-handling-in-migratio.patch
Patch616: drm-i915-gvt-XenGT-migration-optimize.patch
Patch617: drm-i915-gvt-Add-vgpu-execlist-info-into-migration-d.patch
Patch618: drm-i915-gvt-Emulate-ring-mode-register-restore-for-.patch
Patch619: drm-i915-gvt-Use-copy_to_user-to-return-opregion.patch
Patch620: drm-i915-gvt-Expose-opregion-in-vgpu-open.patch
Patch621: drm-i915-gvt-xengt-Don-t-shutdown-vm-at-ioreq-failur.patch
Patch622: drm-i915-gvt-Emulate-hw-status-page-address-register.patch
Patch623: drm-i915-gvt-migration-copy-vregs-on-vreg-load.patch
Patch624: drm-i915-gvt-Fix-a-command-corruption-caused-by-live.patch
Patch625: drm-i915-gvt-update-force-to-nonpriv-register-whitel.patch
Patch626: drm-i915-gvt-xengt-Fix-xengt-instance-destroy-error.patch
Patch627: drm-i915-gvt-invalidate-old-ggtt-page-when-update-gg.patch
Patch628: drm-i915-gvt-support-inconsecutive-partial-gtt-entry.patch
Patch629: set-XENMEM_get_mfn_from_pfn-hypercall-number.patch
Patch630: gvt-enforce-primary-class-id.patch
Patch631: gvt-use-xs-vgpu-type.patch
Patch632: xengt-pviommu-basic.patch
Patch633: xengt-pviommu-unmap.patch
Patch634: get_domctl_interface_version.patch
Patch635: xengt-fix-shutdown-failures.patch
Patch636: xengt-i915-gem-vgtbuffer.patch
Patch637: xengt-gtt-2m-alignment.patch
Patch638: THIS-PATCH-IS-NOT-INTENDED-TO-BE-UPSTREAMED-IT-HAS-O.patch
Patch639: The-current-implementation-of-idle_cpu-only-consider.patch
Patch640: default-xen-swiotlb-size-128MiB.patch
Patch641: On-a-16-node-virtual-cluster-with-e1000-NICs-joining.patch
Patch642: CA-430722-dlm-bound-TCP-failure-detection-with-TCP_U.patch
Patch643: Add-some-randomisation-to-the-GFS2-resource-group-al.patch
Patch644: When-under-heavy-I-O-load-from-two-or-more-hosts-the.patch
Patch645: Look-for-inconsistencies-in-sweep_bh_for_rgrps.patch
Patch646: Fixing-a-GFS2-deadlock-requires-changing-struct-ioma.patch
Patch647: Add-auxiliary-bus-support.patch
Patch648: driver-core-auxiliary-bus-move-slab.h-from-include-f.patch
Patch649: driver-core-auxiliary-bus-make-remove-function-retur.patch
Patch650: driver-core-auxiliary-bus-minor-coding-style-tweaks.patch
Patch651: driver-core-auxiliary-bus-Fix-auxiliary-bus-shutdown.patch
Patch652: driver-core-auxiliary-bus-Fix-calling-stage-for-auxi.patch
Patch653: driver-core-auxiliary-bus-Remove-unneeded-module-bit.patch
Patch654: driver-core-auxiliary-bus-Fix-memory-leak-when-drive.patch
Patch655: Documentation-auxiliary_bus-Clarify-auxiliary_device.patch
Patch656: Documentation-auxiliary_bus-Clarify-__auxiliary_driv.patch
Patch657: Documentation-auxiliary_bus-Clarify-the-release-of-d.patch
Patch658: Documentation-auxiliary_bus-Move-the-text-into-the-c.patch
Patch659: CP-41018-Make-CONFIG_AUXILIARY_BUS-y-work.patch
Patch660: SDEV_EVT_LUN_CHANGE_REPORTED-events-should-only-be-r.patch
Patch661: XSI-2150-Avoid-deadlocks-on-NFS-spinlocks.patch
# Patch662: ("abi-version") ; removed as we are actually changing the kABI now

# XCP-ng patches

# Patch1000: ("backported ceph code from kernel 4.19.295") already included in base
# Patch1001: ("Backport tg3 driver code from kernel v4.19.315") already included in base
# Patch1002: 37c6f8089806 ("perf probe: Fix getting the kernel map")
# Patch1003: f001c5c35a00 ("ACPI: processor: idle: Check acpi_fetch_acpi_dev() return value")
# Patch1004: fff1180d24e6 ("scsi: target: Fix XCOPY NAA identifier lookup")
# Patch1005: 6f3510ec1348 ("ext4: fix off-by-one error in do_split")
Patch1006: SUNRPC-Restore-missing-call-to-cancel_work_sync.patch

# CVE-2026-31431 (Used by CopyFail v1)
# Patch1007: ("crypto: disable authencesn module for CVE-2026-31431") fixed in base

# CVE-2026-43284 (used by DirtyFrag, DirtyFail, CopyFail v2 Electric Boogaloo)
# Patch1008: d985920ced65 ("xfrm: esp: avoid in-place decrypt on shared skb frags")

# CVE-2026-46333 (used by ssh-keysign-pwn, ptrace_may_dream)
# Patch1009: 31e216cf9dc2 ("ptrace: restore smp_rmb() in __ptrace_may_access()")
# Patch1010: 326b1c50eedc ("ptrace: slightly saner 'get_dumpable()' logic")
# Patch1011: ("!kabi ptrace: slightly saner 'get_dumpable()' logic") not needed

# CVE-2026-46300 (used by fragnesia), iterative fixes to CVE-2026-43284
# Patch1012: e993af8976a5 ("net: skbuff: preserve shared-frag marker during coalescing")
# Patch1013: cb225ad20da0 ("net: skbuff: propagate shared-frag marker through frag-transfer helpers")

# CVE-2026-43494 (used by pintheft)
# Patch1014: ffc1541ce426 ("net/rds: reset op_nents when zerocopy page pin fails")

# CVE-2026-46243 (cifswitch)
# Patch1015: 1fca42a8b297 ("smb: client: reject userspace cifs.spnego descriptions")

# Backport fixes in pcieport driver for hotplug hardware detection
Patch1016: PCI-pciehp-Differentiate-between-surprise-and-safe-r.patch
Patch1017: PCI-pciehp-Tolerate-Presence-Detect-hardwired-to-zer.patch
# The following patches fix a regression introduced by the previous patches
Patch1018: PCI-pciehp-Disable-in-band-presence-detect-when-poss.patch
Patch1019: PCI-pciehp-Wait-for-PDS-if-in-band-presence-is-disab.patch
Patch1020: PCI-pciehp-Add-DMI-table-for-in-band-presence-detect.patch

# CVE-2026-45840 (openvswitch: cap upcall PID array size and pre-size vport replies)
# Patch1021: 801e108a6bc6 ("openvswitch: cap upcall PID array size and pre-size vport replies")

# CVE-2026-53227 (net: openvswitch: fix possible kfree_skb of ERR_PTR)
# Patch1022: 180def09bed2 ("net: openvswitch: fix possible kfree_skb of ERR_PTR")

# CVE-2026-64600 (RefluXFS)
Patch1023: xfs-update-fork-seq-counter-on-data-fork-changes.patch
Patch1024: xfs-resample-the-data-fork-mapping-after-cycling-ILO.patch

# https://github.com/xcp-ng/linux/pull/5
# Patch1025: 242a3e0c75b6 ("SUNRPC: avoid race between mod_timer() and del_timer_sync()")
# Patch1026: bcab4d551a3d ("SUNRPC: use _bh spinlocking on ->transport_lock")
Patch1027: Revert-XSI-2150-Avoid-deadlocks-on-NFS-spinlocks.patch

# Defensive fix pulled in with XSA-527
# Patch1028: ccb02adf3293 ("xen/netback: fix error path of xenvif_connect_data()")

# Fix crash on empty plaintext (regression in 8.0.49 / 8.0.51)
# Patch1029: 8a9fcf4a9f1f ("crypto: x86/aesni-gcm - fix crash on empty plaintext")

# Perf build errors on linux-4.19.325-cip
Patch1030: tools-headers-Grab-copy-of-linux-const.h-needed-by-l.patch
Patch1031: tools-headers-UAPI-Sync-linux-const.h-with-the-kerne.patch

# Remove extra localversion-st to avoid koji errors
Patch1032: localversion-st-rm-to-avoid-conflicts-with-yum-s-rpm.patch

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

# XCP-ng BEGIN: remove support for livepatching support
# %%package lp-devel_%%{version}_%%{release}
# License: GPLv2
# Summary: Development package for building livepatches
# Group: Development/System
# %%{core_builddeps Requires}
#
# %%description lp-devel_%%{version}_%%{release}
# Contains the prepared source files, config, and vmlinux for building live
# patches against base version %%{version}-%%{release}.
# XCP-ng END

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

# Apply all patches, expands to a shorter string to prevent overflow
%global autopatch(qvp:) %{lua:
local patch = rpm.expand("%{__patch} %{!-v:-s} %{-p:-p%{-p*}}")
print("p() { "..patch.." -p1 -i \\"$1\\"; }\\n")
for i, p in ipairs(patches) do
    print("p "..p.."\\n")
end
print("unset p\\n")
}

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

# Removed in e0d262a57fc7 ("x86/purgatory: Do not use __builtin_memcpy and __builtin_memset")
# cp -a --parents arch/x86/purgatory/string.c %{buildroot}%{srcpath}

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

# XCP-ng BEGIN: remove support for livepatching support
# # Install files for building live patches
# mv ../prepared-source %%{buildroot}%%{lp_devel_dir}
# install -m 644 vmlinux %%{buildroot}%%{lp_devel_dir}
# XCP-ng END

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

# XCP-ng BEGIN: remove support for livepatching support
# %%files lp-devel_%%{version}_%%{release}
# %%{lp_devel_dir}
# XCP-ng END

%{?_cov_results_package}

%changelog

* Mon Nov 23 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.325-cip137.8.0.51.1.kernelpreview.1
- Note that the incomplete backport to CVE-2026-64600 was already pulled in 4.19.325-cip137.8.0.46.16.kernelpreview.1
- Sync with 4.19.19-8.0.51.1:
  - Fix regression on AES-GCM encryption through AF_ALG
  - Fix incomplete backport to CVE-2026-64600 (RefluXFS)
  - Sync with 4.19.19-8.0.51
  - *** Upstream changelog ***
  - * Tue Nov 17 2026 Alex Brett <alex.brett@citrix.com> - 4.19.19-8.0.51
    - CA-433053: Fix for XSA-531 / CVE-2026-99286
    - CA-433124: Fix regressions from the AF_ALG concurrent-write backport
    - CA-433120: backport cifs: fail i/o on soft mounts if sessionsetup errors out
    - CA-433052: xen/swiotlb: Check the segment boundary in range_straddles_page_boundary()
    - CA-433291: Backport fix for NoisyTCP / CVE-2026-99288
  - * Fri Nov 06 2026 Alex Brett <alex.brett@citrix.com> - 4.19.19-8.0.50
    - CA-432979: Fix for XSA-526 / CVE-2026-100080
    - CA-432980: Fix for XSA-527 / CVE-2026-100081
    - CA-432981: Fix for XSA-528 / CVE-2026-100082
    - Backport fix for xen-netback UAF in xenvif_flush_hash()
  - * Fri Oct 30 2026 Alex Brett <alex.brett@citrix.com> - 4.19.19-8.0.49
    - CA-432848: Fix CVE-2021-47103 - sk_rx_dst use-after-free
    - CA-432848: Fix CVE-2026-98432 - ipv4 inet_opt use-after-free

* Fri Nov 13 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.325-cip137.8.0.46.16.kernelpreview.1
- Rebase on top of v4.19.325-cip137
- Iterative fix to incomplete CVE-2026-64600 (RefluXFS)

* Tue Nov 10 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.19-8.0.46.16
- Iterative fix to incomplete XSA-526 original fix - XSA-531 / CVE-2026-99286

* Mon Nov 09 2026 Lucas Pottier <lucas.pottier@vates.tech> - 4.19.19-8.0.46.15
- Backport security fixes for:
  - XSA-526 / CVE-2026-100080
  - XSA-527 / CVE-2026-100081
  - XSA-528 / CVE-2026-100082 (Quentin Casasnovas)
  - Use-after-free in xen-netback virtual interfaces hashmap flushing (Quentin Casasnovas)

* Mon Nov 02 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.19-8.0.46.14
- Iterative fix for CVE-2026-98432 that introduced a NULL pointer dereference.

* Mon Nov 02 2026 Quentin Casasnovas <quentin.casasnovas@vates.tech> - 4.19.19-8.0.46.13
- Backport security fix for CVE-2026-98432

* Thu Sep 24 2026 Yann Dirson <yann.dirson@vates.tech> - 4.19.19-8.0.46.12
- Drop lp-devel package

* Wed Sep 02 2026 Tu Dinh <ngoc-tu.dinh@vates.tech> - 4.19.19-8.0.46.11
- SUNRPC: Restore missing synchronization on transport_lock
- Revert "XSI-2150: Avoid deadlocks on NFS spinlocks"

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
