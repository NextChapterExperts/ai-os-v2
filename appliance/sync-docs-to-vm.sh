#!/usr/bin/env bash
# Sync AI-OS v2 docs/repo + optional installers to DEV-VM.
# Usage:
#   ./appliance/sync-docs-to-vm.sh peter@192.168.122.42
#   ./appliance/sync-docs-to-vm.sh peter@192.168.122.42 --with-installers

set -euo pipefail

TARGET="${1:-}"
WITH_INSTALLERS=0
if [[ "${2:-}" == "--with-installers" ]] || [[ "${1:-}" == "--with-installers" ]]; then
  WITH_INSTALLERS=1
  [[ "${1:-}" == "--with-installers" ]] && TARGET="${2:-}"
fi

if [[ -z "${TARGET}" ]]; then
  echo "Usage: $0 USER@VM_IP [--with-installers]" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST_DOWNLOADS="${HOME}/Downloads"

echo "==> Sync docs/repo → ${TARGET}:~/Projekte/1100-AI-OS-V2/"
ssh "${TARGET}" 'mkdir -p ~/Projekte/1100-AI-OS-V2 ~/Transfers /opt/ai-os/ingest/inbox 2>/dev/null || mkdir -p ~/Projekte/1100-AI-OS-V2 ~/Transfers'

rsync -av --progress \
  --exclude '.git/' \
  "${ROOT}/" \
  "${TARGET}:~/Projekte/1100-AI-OS-V2/"

if [[ "${WITH_INSTALLERS}" -eq 1 ]]; then
  echo "==> Copy installers → ${TARGET}:~/Transfers/"
  CURSOR_DEB="$(ls -1t "${HOST_DOWNLOADS}"/cursor_*_amd64.deb 2>/dev/null | head -1 || true)"
  AG_TAR="$(ls -1t "${HOST_DOWNLOADS}"/Antigravity*.tar.gz 2>/dev/null | head -1 || true)"
  [[ -n "${CURSOR_DEB}" ]] && rsync -av --progress "${CURSOR_DEB}" "${TARGET}:~/Transfers/"
  [[ -n "${AG_TAR}" ]] && rsync -av --progress "${AG_TAR}" "${TARGET}:~/Transfers/"
  [[ -z "${CURSOR_DEB}" && -z "${AG_TAR}" ]] && echo "Warnung: keine Cursor/Antigravity-Pakete in ${HOST_DOWNLOADS}" >&2
fi

echo "==> Fertig. In der VM:"
echo "    Obsidian-Vault / Cursor-Workspace: ~/Projekte/1100-AI-OS-V2"
echo "    Bootstrap: ~/Projekte/1100-AI-OS-V2/appliance/BOOTSTRAP-DEV-VM.md"
