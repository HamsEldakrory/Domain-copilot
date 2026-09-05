#!/bin/sh
# Git does not use a committed .githooks/ folder automatically - this
# one-time setup step points git at it. Run once after cloning:
#
#   sh scripts/install-hooks.sh

set -e
cd "$(git rev-parse --show-toplevel)" || exit 1
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
echo "Git hooks installed. core.hooksPath -> .githooks"
