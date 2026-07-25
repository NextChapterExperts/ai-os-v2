#!/usr/bin/env bash
# Antigravity in der DEV-VM — chrome-sandbox braucht root+4755, daher --no-sandbox.
AG_ROOT="${ANTIGRAVITY_ROOT:-$HOME/Antigravity-x64}"
exec "$AG_ROOT/antigravity" --no-sandbox "$@"
