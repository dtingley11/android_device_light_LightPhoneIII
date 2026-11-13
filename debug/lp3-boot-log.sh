#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
umask 077
lp3_log_dir=/metadata/lp3-boot-logs

# Metadata also holds encryption and OTA state. Leave at least 4 MiB free
# before starting the bounded logger; do not rotate snapshots on low space.
set -- $(stat -f -c '%a %S' /metadata)
lp3_free_blocks=${1:-0}
lp3_block_bytes=${2:-0}
case "$lp3_free_blocks:$lp3_block_bytes" in
    *[!0-9:]*|:*|*:) exit 0 ;;
esac
[ "$((lp3_free_blocks * lp3_block_bytes))" -ge 4194304 ] || exit 0

for lp3_name in kernel.txt bootconfig.txt cmdline.txt; do
    if [ -f "$lp3_log_dir/$lp3_name" ]; then
        mv -f "$lp3_log_dir/$lp3_name" "$lp3_log_dir/$lp3_name.previous"
    fi
done

cat /proc/bootconfig > "$lp3_log_dir/bootconfig.txt"
cat /proc/cmdline > "$lp3_log_dir/cmdline.txt"
dmesg -S -s 262144 > "$lp3_log_dir/kernel.txt"

# Includes the kernel buffer with ro.logd.kernel enabled. Rotation bounds
# persistent logcat storage to four files of approximately 128 KiB each.
exec /system/bin/logcat -b main -b system -b crash -b kernel -b radio \
    -v threadtime -f "$lp3_log_dir/logcat.txt" -r 128 -n 3
