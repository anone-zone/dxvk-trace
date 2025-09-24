#!/bin/bash
#
# Get apitrace Windows binaries from GitHub.
#

set -euo pipefail

VERSION=13.0
URL_WIN32="https://github.com/apitrace/apitrace/releases/download/$VERSION/apitrace-$VERSION-win32.7z"
URL_WIN64="https://github.com/apitrace/apitrace/releases/download/$VERSION/apitrace-$VERSION-win64.7z"
CHECKSUM="checksum.txt"

curl -L "$URL_WIN32" -o "apitrace-$VERSION-win32.7z"
curl -L "$URL_WIN64" -o "apitrace-$VERSION-win64.7z"

sha256sum -c "$CHECKSUM"
retCode=$?
if [[ $retCode -ne 0 ]]; then
  echo "Checksum failed"
  exit $retCode
fi

7z x "apitrace-$VERSION-win32.7z"
7z x "apitrace-$VERSION-win64.7z"

