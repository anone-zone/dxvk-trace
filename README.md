# dxvk-trace

Steam/Proton utility for sandwiching dxvk with apitrace and gfxreconstruct to capture both D3D and Vulkan API calls at the same time.

## Dependencies

- Steam + some game set up for Proton/dxvk
- apitrace
- [gfxreconstruct/BUILD.md#required-package-list](gfxreconstruct/BUILD.md#required-package-list)

## Usage

```
./get-apitrace.sh
./build-gfxreconstruct.sh
./trace.py --help
```

