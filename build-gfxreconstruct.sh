#!/bin/bash -x
#
# Build x86 and x86_64 gfxreconstruct for Vulkan captures.
#

set -euo pipefail

cd gfxreconstruct

BUILD_DIR_32="build-32"
BUILD_DIR_64="build-64"

rm -rf "$BUILD_DIR_32"
rm -rf "$BUILD_DIR_64"

mkdir "$BUILD_DIR_32"
mkdir "$BUILD_DIR_64"

OPTIONS=(
    "-DCMAKE_BUILD_TYPE=Debug"
    "-DGFXRECON_ENABLE_OPENXR=OFF"
)

cmake . \
    "-B$BUILD_DIR_32" \
    "${OPTIONS[@]}" \
    -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain/linux_x86_32.cmake
cd "$BUILD_DIR_32"
make "-j$(nproc)"

cd ..

cmake . \
    "-B$BUILD_DIR_64" \
    "${OPTIONS[@]}"
cd "$BUILD_DIR_64"
make "-j$(nproc)"

