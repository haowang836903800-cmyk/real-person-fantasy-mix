#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "usage: sh scripts/macos_person_mask.sh INPUT_IMAGE OUTPUT_MASK.png" >&2
  exit 1
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mask_binary="/tmp/real-person-fantasy-mix-person-mask"

clang -fobjc-arc -Wno-deprecated-declarations \
  -framework Foundation \
  -framework Vision \
  -framework CoreImage \
  -framework CoreGraphics \
  -framework CoreVideo \
  -framework ImageIO \
  "$script_dir/macos_person_mask.m" \
  -o "$mask_binary"

exec "$mask_binary" "$1" "$2"
