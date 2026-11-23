#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec qemu-system-x86_64 \
    -nographic \
    -monitor none \
    -no-reboot \
    -m 128M \
    -smp 1 \
    -cpu qemu64 \
    -kernel "${SCRIPT_DIR}/bzImage" \
    -initrd "${SCRIPT_DIR}/initramfs.cpio.gz" \
    -append "console=ttyS0 quiet loglevel=1 panic=1 oops=panic nokaslr"
