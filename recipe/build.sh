#!/usr/bin/env bash
export VALE_STYLES_PATH=${PREFIX}/share/vale/styles
mkdir -p "${VALE_STYLES_PATH}"

cp "${RECIPE_DIR}/.vale.ini" .vale.ini

vale sync
vale ls-config
vale ls-dirs

cp "LICENSE-vale-Microsoft-0.14.0" LICENSE
