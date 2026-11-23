#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIRMWARE="${FIRMWARE:-${SCRIPT_DIR}/nanovault-ledger-v3.4.1.bin}"
FLAG_VALUE="${FLAG:-CTFAC{local_nanovault_flag}}"
TMPDIR="$(mktemp -d)"
ROOTFS_DIR="${TMPDIR}/loader-rootfs"
KERNEL_OUT="${TMPDIR}/bzImage"
LOADER_OUT="${TMPDIR}/loader.cpio.gz"

cleanup() {
    rm -rf "${TMPDIR}"
}
trap cleanup EXIT

python3 - "${FIRMWARE}" "${TMPDIR}" <<'PY'
import pathlib
import struct
import sys
import zlib

magic = b"NVFWIMG\x00"
header = struct.Struct("<8sII")
entry = struct.Struct("<16sQQII")

image = pathlib.Path(sys.argv[1]).read_bytes()
outdir = pathlib.Path(sys.argv[2])

file_magic, version, count = header.unpack_from(image, 0)
if file_magic != magic:
    raise SystemExit(f"bad firmware magic in {sys.argv[1]}")
if version != 1:
    raise SystemExit(f"unsupported firmware version {version}")

offset = header.size
for _ in range(count):
    raw_name, section_offset, size, crc, _flags = entry.unpack_from(image, offset)
    offset += entry.size
    name = raw_name.split(b"\x00", 1)[0].decode("ascii")
    blob = image[section_offset:section_offset + size]
    if zlib.crc32(blob) & 0xFFFFFFFF != crc:
        raise SystemExit(f"crc mismatch for section {name}")
    (outdir / name).write_bytes(blob)
PY

cp "${TMPDIR}/kernel" "${KERNEL_OUT}"
mkdir -p "${ROOTFS_DIR}"
(
    cd "${ROOTFS_DIR}"
    gzip -dc "${TMPDIR}/loader" | cpio -id --quiet
)
printf '%s\n' "${FLAG_VALUE}" > "${ROOTFS_DIR}/flag.txt"
chmod 0444 "${ROOTFS_DIR}/flag.txt"
(
    cd "${ROOTFS_DIR}"
    find . -print0 | cpio --null -o -H newc --quiet | gzip -9 > "${LOADER_OUT}"
)

echo "[nanovault_ledger] APDU transport will be exposed on the VM serial stream after NVREADY" >&2

exec qemu-system-x86_64 \
    -nographic \
    -monitor none \
    -no-reboot \
    -m 128M \
    -smp 1 \
    -cpu qemu64 \
    -kernel "${KERNEL_OUT}" \
    -initrd "${LOADER_OUT}" \
    -append "console=ttyS0 quiet loglevel=1 panic=1 oops=panic"
