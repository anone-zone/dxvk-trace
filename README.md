# dxvk-trace

Steam/Proton utility for sandwiching dxvk with apitrace and gfxreconstruct to capture both D3D and Vulkan API calls at the same time.

## Dependencies

- Steam + a Windows game set up for Proton + dxvk
- apitrace, curl, python, 7z
- [gfxreconstruct/BUILD.md#required-package-list](https://github.com/LunarG/gfxreconstruct/blob/vulkan-sdk-1.4.321.0/BUILD.md#required-package-list)

## Usage

```
./get-apitrace.sh
./build-gfxreconstruct.sh
./trace.py --help
```

