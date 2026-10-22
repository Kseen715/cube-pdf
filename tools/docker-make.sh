#!/bin/sh
# Run the Makefile inside a toolchain container (docker/<target>.Dockerfile):
#
#   tools/docker-make.sh linux|windows|wasm [make goals and variables]
#
# The build directory is $OCR_BUILD, by default ./out. A named Docker volume
# (OCR_BUILD=ocr-build) is much faster than a bind mount under WSL.
set -e
target=$1
shift
cd "$(dirname "$0")/.."

# CI builds the image in a step of its own, which caches its layers
[ -n "$OCR_IMAGE_BUILT" ] || docker build -q -t "ocr-$target" \
    -f "docker/$target.Dockerfile" docker > /dev/null
exec docker run --rm -v "$PWD:/src" -v "${OCR_BUILD:-$PWD/out}:/build" \
    -w /src "ocr-$target" make TARGET="$target" B=/build "$@"
