#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/lib/pr-ship/install-paths.sh"

INSTALL_PREFIX="${PREFIX:-$(prship_default_prefix)}"
BIN_DIR="${INSTALL_PREFIX}/bin"
SHARE_DIR="${INSTALL_PREFIX}/share/pr-ship"
LANG_DIR="${SHARE_DIR}/lang"
TARGET_HOME="$(prship_target_home)"
USER_CONFIG_DIR="${TARGET_HOME}/.config/pr-ship"

UI_FILE="${SCRIPT_DIR}/lib/pr-ship/ui.sh"
source "$UI_FILE"
ui_init_colors

if [[ "$INSTALL_PREFIX" != /* ]]; then
  ui_err "PREFIX must be an absolute path."
  exit 1
fi

if [[ -f "${BIN_DIR}/pr-ship" ]] || [[ -d "${SHARE_DIR}" ]]; then
  ui_header "pr-ship install"
  ui_warn "pr-ship already seems to be installed"
  ui_kv "Binary" "${BIN_DIR}/pr-ship"
  ui_kv "Share dir" "${SHARE_DIR}"
  echo ""
  read -rp "Reinstall now? [y/N] " reinstall
  if [[ ! "$reinstall" =~ ^[yY]$ ]]; then
    ui_info "Installation aborted"
    exit 0
  fi

  if [[ -d "$USER_CONFIG_DIR" ]]; then
    echo ""
    ui_warn "User config exists"
    ui_kv "Config" "${USER_CONFIG_DIR}"
    read -rp "Clean user config before reinstall? [y/N] " clean_config
    if [[ "$clean_config" =~ ^[yY]$ ]]; then
      rm -rf "$USER_CONFIG_DIR"
      ui_ok "User config removed"
    else
      ui_info "User config was kept"
    fi
  fi
fi
ui_header "pr-ship install"

ui_info "Installing files..."
if ! mkdir -p "$BIN_DIR" "$LANG_DIR"; then
  ui_err "Cannot create installation directories. Set PREFIX to a writable directory or run with sudo."
  exit 1
fi

install -m 755 "${SCRIPT_DIR}/bin/pr-ship" "${BIN_DIR}/pr-ship"
install -m 644 "${SCRIPT_DIR}/lib/pr-ship/ui.sh" "${SHARE_DIR}/ui.sh"

for lang_file in "${SCRIPT_DIR}/lib/pr-ship/lang/"*.sh; do
  [[ -f "$lang_file" ]] || continue
  install -m 644 "$lang_file" "${LANG_DIR}/$(basename "$lang_file")"
done

echo ""
ui_ok "Installation complete"
ui_kv "Binary" "${BIN_DIR}/pr-ship"
ui_kv "UI helper" "${SHARE_DIR}/ui.sh"
ui_kv "Languages" "${LANG_DIR}/"
echo ""
case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *) ui_info "Add ${BIN_DIR} to your shell's PATH." ;;
esac
ui_info "Next: run 'pr-ship --setup'"
