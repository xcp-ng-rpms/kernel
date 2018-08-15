%define uname 4.4.0+10
%define short_uname 4.4
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
License: Portions GPL, Portions Non-Redistributable (See description)
Version: 4.4.52
Release: 4.0.7.1
ExclusiveArch: x86_64
ExclusiveOS: Linux
Summary: The Linux kernel
BuildRequires: kmod
BuildRequires: bc
BuildRequires: hostname
%if %{do_kabichk}
BuildRequires: python
%endif
AutoReqProv: no
Provides: kernel-uname-r = %{uname}
Provides: kernel = %{version}-%{release}
Provides: kernel-%{_arch} = %{version}-%{release}
Requires(post): coreutils kmod
Requires(posttrans): coreutils dracut

Source0: https://code.citrite.net/rest/archive/latest/projects/XSU/repos/linux-stable/archive?at=refs%2Ftags%2Fv%{version}&format=tar.gz&prefix=%{name}-%{version}#/%{name}-%{version}.tar.gz
Patch0: 0001-cifs-Make-echo-interval-tunable.patch
Patch1: 0001-security-Add-hook-to-invalidate-inode-security-label.patch
Patch2: 0001-new-helper-memdup_user_nul.patch
Patch3: 0001-cifs-fix-potential-overflow-in-cifs_compose_mount_op.patch
Patch4: 0001-block-support-large-requests-in-blk_rq_map_user_iov.patch
Patch5: 0001-flow_dissector-Correctly-handle-parsing-FCoE.patch
Patch6: 0001-PCI-Update-VPD-definitions.patch
Patch7: 0002-PCI-Use-bitfield-instead-of-bool-for-struct-pci_vpd_.patch
Patch8: 0003-PCI-Determine-actual-VPD-size-on-first-access.patch
Patch9: 0001-scsi-qla4xxx-shut-up-warning-for-rd_reg_indirect.patch
Patch10: 0001-cifs-Allow-using-O_DIRECT-with-cache-loose.patch
Patch11: 0002-cifs-Check-uniqueid-for-SMB2-and-return-ESTALE-if-ne.patch
Patch12: 0001-scsi-Export-function-scsi_scan.c-sanitize_inquiry_st.patch
Patch13: 0001-netfilter-ipset-Fix-set-list-type-crash-when-flush-d.patch
Patch14: 0001-netfilter-ipset-fix-race-condition-in-ipset-save-swa.patch
Patch15: 0001-fix-the-copy-vs.-map-logics-in-blk_rq_map_user_iov.patch
Patch16: 0003-x86-PCI-Mark-Broadwell-EP-Home-Agent-1-as-having-non.patch
Patch17: 0001-cifs-unbreak-TCP-session-reuse.patch
Patch18: 0001-xen-evtchn-add-IOCTL_EVTCHN_RESTRICT.patch
Patch19: 0001-fs-export-__block_write_full_page.patch
Patch20: 0001-Fix-memory-leaks-in-cifs_do_mount.patch
Patch21: 0002-Compare-prepaths-when-comparing-superblocks.patch
Patch22: 0003-Move-check-for-prefix-path-to-within-cifs_get_root.patch
Patch23: 0001-cifs-don-t-use-memcpy-to-copy-struct-iov_iter.patch
Patch24: 0011-fs-cifs-reopen-persistent-handles-on-reconnect.patch
Patch25: 0012-SMB3-Add-mount-parameter-to-allow-user-to-override-m.patch
Patch26: 0013-Expose-cifs-module-parameters-in-sysfs.patch
Patch27: 0014-CIFS-Fix-persistent-handles-re-opening-on-reconnect.patch
Patch28: 0015-CIFS-Reset-read-oplock-to-NONE-if-we-have-mandatory-.patch
Patch29: 0001-smartpqi-initial-commit-of-Microsemi-smartpqi-driver.patch
Patch30: 0002-scsi-smartpqi-change-aio-sg-processing.patch
Patch31: 0003-scsi-smartpqi-change-tmf-macro-names.patch
Patch32: 0004-scsi-smartpqi-simplify-spanning.patch
Patch33: 0005-scsi-smartpqi-enhance-drive-offline-informational-me.patch
Patch34: 0006-scsi-smartpqi-enhance-reset-logic.patch
Patch35: 0007-scsi-smartpqi-add-kdump-support.patch
Patch36: 0008-scsi-smartpqi-correct-controller-offline-issue.patch
Patch37: 0009-scsi-smartpqi-correct-event-acknowledgment-timeout-i.patch
Patch38: 0010-scsi-smartpqi-minor-function-reformating.patch
Patch39: 0011-scsi-smartpqi-minor-tweaks-to-update-time-support.patch
Patch40: 0012-scsi-smartpqi-scsi-queuecommand-cleanup.patch
Patch41: 0013-scsi-smartpqi-remove-timeout-for-cache-flush-operati.patch
Patch42: 0014-scsi-smartpqi-update-Kconfig.patch
Patch43: 0015-scsi-smartpqi-bump-driver-version.patch
Patch44: 0016-scsi-smartpqi-raid-bypass-lba-calculation-fix.patch
Patch45: 0001-SMB2-Separate-Kerberos-authentication-from-SMB2_sess.patch
Patch46: 0001-SMB2-Separate-RawNTLMSSP-authentication-from-SMB2_se.patch
Patch47: 0001-scsi-libiscsi-Fix-locking-in-__iscsi_conn_send_pdu.patch
Patch48: 0001-libfc-Update-rport-reference-counting.patch
Patch49: 0001-libfc-sanity-check-cpu-number-extracted-from-xid.patch
Patch50: 0001-scsi-libfc-Issue-PRLI-after-a-PRLO-has-been-received.patch
Patch51: 0001-scsi-libfc-send-LOGO-for-PLOGI-failure.patch
Patch52: 0001-scsi-libfc-reset-exchange-manager-during-LOGO-handli.patch
Patch53: 0001-scsi-libfc-do-not-send-ABTS-when-resetting-exchanges.patch
Patch54: 0001-Call-echo-service-immediately-after-socket-reconnect.patch
Patch55: 0001-libfc-Revisit-kref-handling.patch
Patch56: 0001-scsi-libfc-Fixup-disc_mutex-handling.patch
Patch57: 0001-scsi-libfc-Do-not-take-rdata-rp_mutex-when-processin.patch
Patch58: 0001-scsi-libfc-Do-not-drop-down-to-FLOGI-for-fc_rport_lo.patch
Patch59: 0001-scsi-libfc-Do-not-login-if-the-port-is-already-start.patch
Patch60: 0001-scsi-libfc-don-t-advance-state-machine-for-incoming-.patch
Patch61: 0001-scsi-fcoe-Harden-CVL-handling-when-we-have-not-logge.patch
Patch62: 0001-CIFS-Fix-a-possible-double-locking-of-mutex-during-r.patch
Patch63: 0001-scsi-bfa-Increase-requested-firmware-version.patch
Patch64: 0001-xen-privcmd-return-ENOTTY-for-unimplemented-IOCTLs.patch
Patch65: 0001-xen-privcmd-Add-IOCTL_PRIVCMD_DM_OP.patch
Patch66: 0001-xen-privcmd-add-IOCTL_PRIVCMD_RESTRICT.patch
Patch67: 0001-cifs-Do-not-send-echoes-before-Negotiate-is-complete.patch
Patch68: 0001-xen-fix-bio-vec-merging.patch
Patch69: 0001-netfilter-ipset-Null-pointer-exception-in-ipset-list.patch
Patch70: 0001-net-reduce-skb_warn_bad_offload-noise.patch
Patch71: 0001-net-skb_needs_check-accepts-CHECKSUM_NONE-for-tx.patch
Patch72: 0001-net-avoid-skb_warn_bad_offload-false-positives-on-UF.patch
Patch73: 0001-scsi-libfc-fix-a-deadlock-in-fc_rport_work.patch
Patch74: 0001-xen-gntdev-avoid-out-of-bounds-access-in-case-of-par.patch
Patch75: 0007-component-remove-old-add_components-method.patch
Patch76: 0008-component-move-check-for-unbound-master-into-try_to_.patch
Patch77: 0009-component-track-components-via-array-rather-than-lis.patch
Patch78: 0010-component-add-support-for-releasing-match-data.patch
Patch79: 0001-xen-netback-use-skb-to-determine-number-of-required-.patch
Patch80: 0002-xen-netback-delete-NAPI-instance-when-queue-fails-to.patch
Patch81: 0003-xen-netback-free-queues-after-freeing-the-net-device.patch
Patch82: 0004-xen-netback-implement-dynamic-multicast-control.patch
Patch83: 0001-xen-netback-re-import-canonical-netif-header.patch
Patch84: 0005-xen-netback-support-multiple-extra-info-fragments-pa.patch
Patch85: 0006-xen-netback-reduce-log-spam.patch
Patch86: 0007-xen-netback-fix-extra_info-handling-in-xenvif_tx_err.patch
Patch87: 0008-xen-netback-add-control-ring-boilerplate.patch
Patch88: 0009-xen-netback-add-control-protocol-implementation.patch
Patch89: 0010-xen-netback-pass-hash-value-to-the-frontend.patch
Patch90: 0011-xen-netback-use-hash-value-from-the-frontend.patch
Patch91: 0012-xen-netback-correct-length-checks-on-hash-copy_ops.patch
Patch92: 0013-xen-netback-only-deinitialized-hash-if-it-was-initia.patch
Patch93: 0014-xen-netback-create-a-debugfs-node-for-hash-informati.patch
Patch94: 0015-xen-netback-using-kfree_rcu-to-simplify-the-code.patch
Patch95: 0001-xen-netback-separate-guest-side-rx-code-into-separat.patch
Patch96: 0002-xen-netback-retire-guest-rx-side-prefix-GSO-feature.patch
Patch97: 0003-xen-netback-refactor-guest-rx.patch
Patch98: 0004-xen-netback-immediately-wake-tx-queue-when-guest-rx-.patch
Patch99: 0005-xen-netback-process-guest-rx-packets-in-batches.patch
Patch100: 0006-xen-netback-batch-copies-for-multiple-to-guest-rx-pa.patch
Patch101: 0007-xen-netback-add-fraglist-support-for-to-guest-rx.patch
Patch102: 0001-xen-netback-make-sure-that-hashes-are-not-send-to-un.patch
Patch103: 0001-xen-netback-fix-memory-leaks-on-XenBus-disconnect.patch
Patch104: 0002-xen-netback-protect-resource-cleaning-on-XenBus-disc.patch
Patch105: 0001-xen-netback-Use-GFP_ATOMIC-to-allocate-hash.patch
Patch106: 0001-xen-netback-fix-race-condition-on-XenBus-disconnect.patch
Patch107: 0001-scsi-libiscsi-add-lock-around-task-lists-to-fix-list.patch
Patch108: 0001-lib-bitmap.c-conversion-routines-to-from-u32-array.patch
Patch109: 0001-net-usnic-remove-unused-call-to-ethtool_ops-get_sett.patch
Patch110: 0002-net-usnic-use-__ethtool_get_settings.patch
Patch111: 0001-net-ethtool-add-new-ETHTOOL_xLINKSETTINGS-API.patch
Patch112: 0003-tx4939-use-__ethtool_get_ksettings.patch
Patch113: 0004-net-usnic-use-__ethtool_get_ksettings.patch
Patch114: 0005-net-bonding-use-__ethtool_get_ksettings.patch
Patch115: 0006-net-ipvlan-use-__ethtool_get_ksettings.patch
Patch116: 0007-net-macvlan-use-__ethtool_get_ksettings.patch
Patch117: 0008-net-team-use-__ethtool_get_ksettings.patch
Patch118: 0009-net-fcoe-use-__ethtool_get_ksettings.patch
Patch119: 0010-net-rdma-use-__ethtool_get_ksettings.patch
Patch120: 0011-net-8021q-use-__ethtool_get_ksettings.patch
Patch121: 0012-net-bridge-use-__ethtool_get_ksettings.patch
Patch122: 0013-net-core-use-__ethtool_get_ksettings.patch
Patch123: 0001-net-mlx4-use-new-ETHTOOL_G-SSETTINGS-API.patch
Patch124: 0002-ethtool-Set-cmd-field-in-ETHTOOL_GLINKSETTINGS-respo.patch
Patch125: 0003-ethtool-minor-doc-update.patch
Patch126: 0001-net-mlx5e-Fix-MLX5E_100BASE_T-define.patch
Patch127: 0003-net-ethtool-export-conversion-function-between-u32-a.patch
Patch128: 0004-ethtool-add-support-for-25G-50G-100G-speed-modes.patch
Patch129: 0005-ethtool-Add-50G-baseSR2-link-mode.patch
Patch130: 0001-net-mlx5e-Add-missing-50G-baseSR2-link-mode.patch
Patch131: 0001-net-mlx5e-Use-new-ethtool-get-set-link-ksettings-API.patch
Patch132: 0006-net-ethtool-add-support-for-1000BaseX-and-missing-10.patch
Patch133: 0004-net-ethtool-don-t-require-CAP_NET_ADMIN-for-ETHTOOL_.patch
Patch134: 0007-net-ethtool-add-support-for-2500BaseT-and-5000BaseT-.patch
Patch135: 0001-gfs2-Automatically-set-GFS2_DIF_SYSTEM-flag-on-syste.patch
Patch136: 0002-GFS2-Delete-an-unnecessary-check-before-the-function.patch
Patch137: 0003-GFS2-Use-rht_for_each_entry_rcu-in-glock_hash_walk.patch
Patch138: 0004-gfs2-Extended-attribute-readahead.patch
Patch139: 0005-gfs2-Extended-attribute-readahead-optimization.patch
Patch140: 0006-GFS2-Extract-quota-data-from-reservations-structure-.patch
Patch141: 0007-gfs2-Remove-gfs2_xattr_acl_chmod.patch
Patch142: 0008-posix-acls-Remove-duplicate-xattr-name-definitions.patch
Patch143: 0010-GFS2-Make-rgrp-reservations-part-of-the-gfs2_inode-s.patch
Patch144: 0011-GFS2-Reduce-size-of-incore-inode.patch
Patch145: 0012-GFS2-Update-master-statfs-buffer-with-sd_statfs_spin.patch
Patch146: 0013-GFS2-Reintroduce-a-timeout-in-function-gfs2_gl_hash_.patch
Patch147: 0014-gfs2-keep-offset-when-splitting-dir-leaf-blocks.patch
Patch148: 0015-gfs2-change-gfs2-readdir-cookie.patch
Patch149: 0016-gfs2-clear-journal-live-bit-in-gfs2_log_flush.patch
Patch150: 0017-GFS2-Wait-for-iopen-glock-dequeues.patch
Patch151: 0018-GFS2-Truncate-address-space-mapping-when-deleting-an.patch
Patch152: 0019-GFS2-Release-iopen-glock-in-gfs2_create_inode-error-.patch
Patch153: 0020-GFS2-Always-use-iopen-glock-for-gl_deletes.patch
Patch154: 0021-GFS2-Don-t-do-glock-put-on-when-inode-creation-fails.patch
Patch155: 0022-gfs2-fix-flock-panic-issue.patch
Patch156: 0023-gfs2-Invalid-security-labels-of-inodes-when-they-go-.patch
Patch157: 0025-fs-use-block_device-name-vsprintf-helper.patch
Patch158: 0026-GFS2-Check-if-iopen-is-held-when-deleting-inode.patch
Patch159: 0028-wrappers-for-i_mutex-access.patch
Patch160: 0029-gfs2-avoid-uninitialized-variable-warning.patch
Patch161: 0030-GFS2-Fix-direct-IO-write-rounding-error.patch
Patch162: 0031-GFS2-Prevent-delete-work-from-occurring-on-glocks-us.patch
Patch163: 0032-GFS2-Don-t-filter-out-I_FREEING-inodes-anymore.patch
Patch164: 0033-GFS2-Eliminate-parameter-non_block-on-gfs2_inode_loo.patch
Patch165: 0034-GFS2-ignore-unlock-failures-after-withdraw.patch
Patch166: 0035-mm-fs-get-rid-of-PAGE_CACHE_-and-page_cache_-get-rel.patch
Patch167: 0036-rhashtable-accept-GFP-flags-in-rhashtable_walk_init.patch
Patch168: 0037-GFS2-Get-rid-of-dead-code-in-inode_go_demote_ok.patch
Patch169: 0038-gfs2-Use-gfs2-wrapper-to-sync-inode-before-calling-g.patch
Patch170: 0039-don-t-bother-with-d_inode-i_sb-it-s-always-equal-to-.patch
Patch171: 0042-GFS2-fs-gfs2-glock.c-Deinline-do_error-save-1856-byt.patch
Patch172: 0043-GFS2-Don-t-dereference-inode-in-gfs2_inode_lookup-un.patch
Patch173: 0044-GFS2-Add-calls-to-gfs2_holder_uninit-in-two-error-ha.patch
Patch174: 0047-gfs2-use-inode_lock-unlock-instead-of-accessing-i_mu.patch
Patch175: 0048-GFS2-Remove-allocation-parms-from-gfs2_rbm_find.patch
Patch176: 0050-GFS2-Refactor-gfs2_remove_from_journal.patch
Patch177: 0052-gfs2-Switch-to-generic-xattr-handlers.patch
Patch178: 0054-remove-lots-of-IS_ERR_VALUE-abuses.patch
Patch179: 0059-GFS2-don-t-set-rgrp-gl_object-until-it-s-inserted-in.patch
Patch180: 0060-gfs2-Initialize-iopen-glock-holder-for-new-inodes.patch
Patch181: 0061-gfs2-Fix-gfs2_lookup_by_inum-lock-inversion.patch
Patch182: 0062-gfs2-Get-rid-of-gfs2_ilookup.patch
Patch183: 0063-gfs2-Large-filesystem-fix-for-32-bit-systems.patch
Patch184: 0064-gfs2-Lock-holder-cleanup.patch
Patch185: 0065-gfs2-writeout-truncated-pages.patch
Patch186: 0067-GFS2-Check-rs_free-with-rd_rsspin-protection.patch
Patch187: 0069-GFS2-Fix-gfs2_replay_incr_blk-for-multiple-journal-s.patch
Patch188: 0070-GFS2-use-BIT-macro.patch
Patch189: 0071-fs-return-EPERM-on-immutable-inode.patch
Patch190: 0072-gfs2-Remove-dirty-buffer-warning-from-gfs2_releasepa.patch
Patch191: 0073-gfs2-Fix-extended-attribute-readahead-optimization.patch
Patch192: 0074-gfs2-fix-to-detect-failure-of-register_shrinker.patch
Patch193: 0077-gfs2-Update-file-times-after-grabbing-glock.patch
Patch194: 0078-gfs2-Initialize-atime-of-I_NEW-inodes.patch
Patch195: 0085-block-fs-untangle-fs.h-and-blk_types.h.patch
Patch196: 0088-fix-gfs2_stuffed_write_end-on-short-copies.patch
Patch197: 0089-GFS2-Fix-reference-to-ERR_PTR-in-gfs2_glock_iter_nex.patch
Patch198: 0090-Replace-asm-uaccess.h-with-linux-uaccess.h-globally.patch
Patch199: 0092-GFS2-Limit-number-of-transaction-blocks-requested-fo.patch
Patch200: 0093-GFS2-Made-logd-daemon-take-into-account-log-demand.patch
Patch201: 0094-GFS2-Wake-up-io-waiters-whenever-a-flush-is-done.patch
Patch202: 0095-GFS2-Switch-tr_touched-to-flag-in-transaction.patch
Patch203: 0096-GFS2-Inline-function-meta_lo_add.patch
Patch204: 0097-GFS2-Reduce-contention-on-gfs2_log_lock.patch
Patch205: 0099-gfs2-Make-gfs2_write_full_page-static.patch
Patch206: 0100-gfs2-Use-rhashtable-walk-interface-in-glock_hash_wal.patch
Patch207: 0101-gfs2-Add-missing-rcu-locking-for-glock-lookup.patch
Patch208: 0103-sched-headers-Prepare-to-remove-linux-cred.h-inclusi.patch
Patch209: 0106-gfs2-Avoid-alignment-hole-in-struct-lm_lockname.patch
Patch210: 0107-GFS2-Prevent-BUG-from-occurring-when-normal-Withdraw.patch
Patch211: 0108-gfs2-Replace-rhashtable_walk_init-with-rhashtable_wa.patch
Patch212: 0109-gfs2-Deduplicate-gfs2_-glocks-glstats-_open.patch
Patch213: 0110-gfs2-Don-t-pack-struct-lm_lockname.patch
Patch214: 0111-GFS2-Temporarily-zero-i_no_addr-when-creating-a-dino.patch
Patch215: 0112-gfs2-Switch-to-rhashtable_lookup_get_insert_fast.patch
Patch216: 0113-Revert-GFS2-Wait-for-iopen-glock-dequeues.patch
Patch217: 0114-gfs2-Re-enable-fallocate-for-the-rindex.patch
Patch218: 0115-GFS2-Non-recursive-delete.patch
Patch219: 0118-GFS2-Allow-glocks-to-be-unlocked-after-withdraw.patch
Patch220: 0122-gfs2-remove-the-unused-sd_log_error-field.patch
Patch221: 0124-GFS2-Withdraw-when-directory-entry-inconsistencies-a.patch
Patch222: 0125-GFS2-Remove-gl_list-from-glock-structure.patch
Patch223: 0126-GFS2-Eliminate-vestigial-sd_log_flush_wrapped.patch
Patch224: 0127-gfs2-Get-rid-of-flush_delayed_work-in-gfs2_evict_ino.patch
Patch225: 0128-gfs2-Protect-gl-gl_object-by-spin-lock.patch
Patch226: 0129-gfs2-Clean-up-glock-work-enqueuing.patch
Patch227: 0130-gfs2-gfs2_create_inode-Keep-glock-across-iput.patch
Patch228: 0131-GFS2-constify-attribute_group-structures.patch
Patch229: 0132-VFS-Provide-empty-name-qstr.patch
Patch230: 0134-gfs2-Fix-glock-rhashtable-rcu-bug.patch
Patch231: 0136-GFS2-Prevent-double-brelse-in-gfs2_meta_indirect_buf.patch
Patch232: 0137-gfs2-Lock-holder-cleanup-fixup.patch
Patch233: 0138-gfs2-Don-t-clear-SGID-when-inheriting-ACLs.patch
Patch234: 0139-gfs2-Fixup-to-Get-rid-of-flush_delayed_work-in-gfs2_.patch
Patch235: 0140-GFS2-fix-code-parameter-error-in-inode_go_lock.patch
Patch236: 0141-gfs2-add-flag-REQ_PRIO-for-metadata-I-O.patch
Patch237: 0142-GFS2-Introduce-helper-for-clearing-gl_object.patch
Patch238: 0143-GFS2-Set-gl_object-in-inode-lookup-only-after-block-.patch
Patch239: 0144-gfs2-convert-to-errseq_t-based-writeback-error-repor.patch
Patch240: 0145-GFS2-Clear-gl_object-if-gfs2_create_inode-fails.patch
Patch241: 0146-GFS2-Clear-gl_object-when-deleting-an-inode-in-gfs2_.patch
Patch242: 0147-GFS2-Don-t-bother-trying-to-add-rgrps-to-the-lru-lis.patch
Patch243: 0148-GFS2-Don-t-waste-time-locking-lru_lock-for-non-lru-g.patch
Patch244: 0149-GFS2-Delete-debugfs-files-only-after-we-evict-the-gl.patch
Patch245: 0150-gfs2-Fix-trivial-typos.patch
Patch246: 0151-gfs2-gfs2_glock_get-Wait-on-freeing-glocks.patch
Patch247: 0152-gfs2-Get-rid-of-gfs2_set_nlink.patch
Patch248: 0153-gfs2-gfs2_evict_inode-Put-glocks-asynchronously.patch
Patch249: 0154-gfs2-Defer-deleting-inodes-under-memory-pressure.patch
Patch250: 0155-gfs2-Clean-up-waiting-on-glocks.patch
Patch251: 0156-gfs2-forcibly-flush-ail-to-relieve-memory-pressure.patch
Patch252: 0157-gfs2-fix-slab-corruption-during-mounting-and-umounti.patch
Patch253: 0159-GFS2-Withdraw-for-IO-errors-writing-to-the-journal-o.patch
Patch254: 0160-gfs2-Silence-gcc-format-truncation-warning.patch
Patch255: 0161-GFS2-Fix-up-some-sparse-warnings.patch
Patch256: 0162-GFS2-Fix-gl_object-warnings.patch
Patch257: 0163-gfs2-constify-rhashtable_params.patch
Patch258: 0164-GFS2-Fix-non-recursive-truncate-bug.patch
Patch259: 0165-gfs2-don-t-return-ENODATA-in-__gfs2_xattr_set-unless.patch
Patch260: 0166-gfs2-preserve-i_mode-if-__gfs2_set_acl-fails.patch
Patch261: 0167-gfs2-Fix-debugfs-glocks-dump.patch
Patch262: 0168-License-cleanup-add-SPDX-GPL-2.0-license-identifier-.patch
Patch263: 0169-License-cleanup-add-SPDX-license-identifier-to-uapi-.patch
Patch264: 0170-GFS2-Take-inode-off-order_write-list-when-setting-jd.patch
Patch265: gfs2-backport-rhashtable.patch
Patch266: 0001-convert-a-bunch-of-open-coded-instances-of-memdup_us.patch
Patch267: 0002-regression-fix-braino-in-fs-dlm-user.c.patch
Patch268: 0003-DLM-Replace-nodeid_to_addr-with-kernel_getpeername.patch
Patch269: 0004-DLM-Save-and-restore-socket-callbacks-properly.patch
Patch270: 0007-mm-fs-get-rid-of-PAGE_CACHE_-and-page_cache_-get-rel.patch
Patch271: 0008-dlm-add-log_info-config-option.patch
Patch272: 0009-dlm-Use-kmemdup-instead-of-kmalloc-and-memcpy.patch
Patch273: 0010-dlm-fix-malfunction-of-dlm_tool-caused-by-debugfs-ch.patch
Patch274: 0012-dlm-make-genl_ops-const.patch
Patch275: 0014-dlm-don-t-save-callbacks-after-accept.patch
Patch276: 0015-dlm-remove-lock_sock-to-avoid-scheduling-while-atomi.patch
Patch277: 0016-dlm-don-t-specify-WQ_UNBOUND-for-the-ast-callback-wo.patch
Patch278: 0017-dlm-fix-error-return-code-in-sctp_accept_from_sock.patch
Patch279: 0018-genetlink-no-longer-support-using-static-family-IDs.patch
Patch280: 0019-genetlink-statically-initialize-families.patch
Patch281: 0021-Replace-asm-uaccess.h-with-linux-uaccess.h-globally.patch
Patch282: 0001-x86-cpu-Merge-bugs.c-and-bugs_64.c.patch
Patch283: 0027-dlm-Fix-kernel-memory-disclosure.patch
Patch284: 0028-dlm-Make-dismatch-error-message-more-clear.patch
Patch285: 0029-dlm-Replace-six-seq_puts-calls-by-seq_putc.patch
Patch286: 0030-dlm-Add-spaces-for-better-code-readability.patch
Patch287: 0031-dlm-Improve-a-size-determination-in-table_seq_start.patch
Patch288: 0032-dlm-Use-kcalloc-in-dlm_scan_waiters.patch
Patch289: 0033-dlm-Improve-a-size-determination-in-dlm_recover_wait.patch
Patch290: 0034-dlm-Delete-an-error-message-for-a-failed-memory-allo.patch
Patch291: 0035-dlm-Use-kmalloc_array-in-make_member_array.patch
Patch292: 0036-dlm-Use-kcalloc-in-two-functions.patch
Patch293: 0037-dlm-Improve-a-size-determination-in-two-functions.patch
Patch294: 0038-dlm-Delete-an-unnecessary-variable-initialisation-in.patch
Patch295: 0039-dlm-print-log-message-when-cluster-name-is-not-set.patch
Patch296: 0040-dlm-constify-kset_uevent_ops-structure.patch
Patch297: 0041-dlm-avoid-double-free-on-error-path-in-dlm_device_-r.patch
Patch298: 0042-uapi-linux-dlm_netlink.h-include-linux-dlmconstants.patch
Patch299: 0043-dlm-use-sock_create_lite-inside-tcp_accept_from_sock.patch
Patch300: 0044-License-cleanup-add-SPDX-GPL-2.0-license-identifier-.patch
Patch301: 0045-License-cleanup-add-SPDX-license-identifier-to-uapi-.patch
Patch302: 0002-x86-cpufeatures-Make-CPU-bugs-sticky.patch
Patch303: kbuild-AFTER_LINK.patch
Patch304: commit-info.patch
Patch305: blktap2.patch
Patch306: 0001-dma-add-dma_get_required_mask_from_max_pfn.patch
Patch307: 0002-x86-xen-correct-dma_get_required_mask-for-Xen-PV-gue.patch
Patch308: 0001-xen-setup-Don-t-relocate-p2m-initrd-over-existing-on.patch
Patch309: xen-balloon-hotplug-select-HOLES_IN_ZONE.patch
Patch310: xen-balloon-Only-mark-a-page-as-managed-when-it-is-r.patch
Patch311: blkback-debug-ring.diff
Patch312: 0001-pci-export-pci_probe_reset_function.patch
Patch313: 0002-xen-pciback-provide-a-reset-sysfs-file-to-try-harder.patch
Patch314: pciback-disable-root-port-aer.patch
Patch315: pciback-mask-root-port-comp-timeout.patch
Patch316: xen-gntdev-grant-copy.patch
Patch317: 0001-xen-netback-fix-guest-Rx-stall-detection-after-guest.patch
Patch318: xen-netback-record-rx-queue-for-skb.patch
Patch319: 0001-xen-netback-don-t-populate-the-hash-cache-on-XenBus-.patch
Patch320: no-flr-quirk.patch
Patch321: block-loop-only-flush-on-close-if-attached.patch
Patch322: CA-135938-nfs-disconnect-on-rpc-retry.patch
Patch323: sunrpc-force-disconnect-on-connection-timeout.patch
Patch324: fix_default_behaviour_for_empty_domains_and_add_domainauto_option
Patch325: cifs__queue_reconnect_thread_with_a_delay.patch
Patch326: cifs__reconnect_thread_reschedule_itself.patch
Patch327: cifs__remove_bad_network_name_flag.patch
Patch328: cifs__store_results_of_cifs_reopen_file_to_avoid_infinite_wait.patch
Patch329: cifs__handle_guest_access_errors_to_windows_shares
Patch330: netlink-alloc-allow-direct-reclaim.patch
Patch331: blkback-xsa216.patch
Patch332: tg3-alloc-repeat.patch
Patch333: 0001-netfilter-ipset-Fix-race-between-dump-and-swap.patch
Patch334: gntdev-mmap-cleanup.patch
Patch335: 0001-scsi-devinfo-Add-Microsoft-iSCSI-target-to-1024-sect.patch
Patch336: dlm__increase_socket_backlog_to_avoid_hangs_with_16_nodes.patch
Patch337: net-core__order-3_frag_allocator_causes_swiotlb_bouncing_under_xen.patch
Patch338: idle_cpu-return-0-during-softirq.patch
Patch339: call-kexec-before-offlining-noncrashing-cpus.patch
Patch340: fnic-disable-tracing-by-default.patch
Patch341: bnx2-disable-gro.patch
Patch342: x86-apic-disable-physflat-under-xen.patch
Patch343: xen-no-pmu.patch
Patch344: map-1MiB-1-1.patch
Patch345: default-xen-swiotlb-size-128MiB.patch
Patch346: restricted-privcmd.patch
Patch347: CP-9457-blkback-kthread-pid.patch
Patch348: x86-xen-add-cpuid-est-flag-if-present-on-host-hw.patch
Patch349: make-dev_load-noop.patch
Patch350: mm-Ignore-zones-with-no-managed-pages.patch
Patch351: xen-blkback-Don-t-use-persistent-grants.patch
Patch352: openvswitch-clear-sender-cpu-before-forwarding-packe.patch
Patch353: 0001-Revert-efi-Introduce-EFI_NX_PE_DATA-bit-and-set-it-f.patch
Patch354: hide-nr_cpus-warning.patch
Patch355: disable-pm-timer.patch
Patch356: xen-evtchn-Bind-dyn-evtchn-qemu-dm-interrupt-to-next-online-VCPU.patch
Patch357: net-Do-not-scrub-ignore_df-within-the-same-name-spac.patch
Patch358: enable-fragmention-gre-packets.patch
Patch359: ipset-restore-kabi.patch
Patch360: xsa270.patch
Patch361: 0001-x86-entry-64-Remove-ebx-handling-from-error_entry-ex.patch
Patch362: 0003-x86-speculation-l1tf-Change-order-of-offset-type-in-.patch
Patch363: 0004-x86-speculation-l1tf-Protect-swap-entries-against-L1.patch
Patch364: 0005-x86-speculation-l1tf-Protect-PROT_NONE-PTEs-against-.patch
Patch365: 0006-x86-speculation-l1tf-Make-sure-the-first-page-is-alw.patch
Patch366: 0007-x86-speculation-l1tf-Add-sysfs-reporting-for-l1tf.patch
Patch367: 0008-x86-speculation-l1tf-Disallow-non-privileged-high-MM.patch
Patch368: 0009-x86-speculation-l1tf-Limit-swap-file-size-to-MAX_PA-.patch
Patch369: 0010-x86-speculation-l1tf-Extend-64bit-swap-file-size-lim.patch
Patch370: bonding-balance-slb.patch
Patch371: bridge-lock-fdb-after-garp.patch
Patch372: CP-13181-net-openvswitch-add-dropping-of-fip-and-lldp.patch
Patch373: xen-ioemu-inject-msi.patch
Patch374: build-mipi-dsi-as-a-module.patch
Patch375: intel-gvt-g-kernel-support.patch
Patch376: intel-gvt-g-enable-out-of-tree-compile.patch
Patch377: pv-iommu-support.patch
Patch378: kexec-reserve-crashkernel-region.patch
Patch379: amd-mxgpu.patch
Patch380: debug-pwq-null-point-deref.patch
Patch381: abi-version
Source1: kernel-%{_arch}.config
Source2: macros.kernel
%if %{do_kabichk}
Source3: check-kabi
Source4: Module.kabi
Source5: https://repo.citrite.net/list/ctx-local-contrib/citrix/branding/Citrix_Logo_Black.png
%endif

%description
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system, with selected patches provided by Citrix.  The
kernel handles the basic functions of the operating system: memory
allocation, process allocation, device input and output, etc.

Citrix, the Citrix logo, Xen, XenServer, and certain other marks appearing
herein are proprietary trademarks of Citrix Systems, Inc., and are
registered in the U.S. and other countries. You may not redistribute this
package, nor display or otherwise use any Citrix trademarks or any marks
that incorporate Citrix trademarks without the express prior written
authorization of Citrix. Nothing herein shall restrict your rights, if
any, in the software contained within this package under an applicable
open source license.

Portions of this package are © 2017 Citrix Systems, Inc. For other
copyright and licensing information see the relevant source RPM.


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

%prep

%autosetup -p1

make mrproper
cp -f %{SOURCE1} .config
cp -f %{SOURCE5} .

%build

# This override tweaks the kernel makefiles so that we run debugedit on an
# object before embedding it.  When we later run find-debuginfo.sh, it will
# run debugedit again.  The edits it does change the build ID bits embedded
# in the stripped object, but repeating debugedit is a no-op.  We do it
# beforehand to get the proper final build ID bits into the embedded image.
# This affects the vDSO images in vmlinux, and the vmlinux image in bzImage.
export AFTER_LINK='sh -xc "/usr/lib/rpm/debugedit -b %{buildroot} -d /usr/src/debug -i $@ > $@.id"'

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
cp -a --parents arch/x86/purgatory/sha256.h %{buildroot}%{srcpath}
cp -a --parents arch/x86/purgatory/sha256.c %{buildroot}%{srcpath}
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
%doc Citrix_Logo_Black.png

%files headers
/usr/include/*

%files devel
/lib/modules/%{uname}/build
/lib/modules/%{uname}/source
%verify(not mtime) /usr/src/kernels/%{uname}-%{_arch}
%{_rpmconfigdir}/macros.d/macros.kernel

%changelog
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
