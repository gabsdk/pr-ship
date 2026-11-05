#!/usr/bin/env bash

prship_target_home() {
  local target_home="$HOME"
  if [[ -n "${SUDO_USER:-}" ]]; then
    if command -v getent &>/dev/null; then
      target_home="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
    elif command -v dscl &>/dev/null; then
      target_home="$(dscl . -read "/Users/${SUDO_USER}" NFSHomeDirectory | sed 's/^NFSHomeDirectory: //')"
    fi
  fi
  if [[ "$target_home" != /* ]]; then
    printf '%s\n' 'Cannot determine the target user home directory.' >&2
    return 1
  fi
  printf '%s\n' "$target_home"
}

prship_default_prefix() {
  case "$(uname -s)" in
    Darwin)
      local target_home
      target_home="$(prship_target_home)" || return 1
      printf '%s/.local\n' "$target_home"
      ;;
    *) printf '%s\n' /usr ;;
  esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  prship_default_prefix
fi
