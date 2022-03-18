# ergodox-compress-keymap

The memory on the [ErgoDox EZ](https://ergodox-ez.com/) is limited, especially if you enable animations or the debugging console. Looking at a keymap generated by [Oryx](https://configure.zsa.io/) shows quite some waste:

- The `ledmap` is stored wastefully with gaps between layers. So if you have 10 layers and lighting defined for the last only, you still pay the storage for all layers.
```
const uint8_t PROGMEM ledmap[][DRIVER_LED_TOTAL][3] = {
    [1] = { ...
```
You can alleviate it a bit by moving all lit layers to the beginning, the ones at the end will not allocate storage.
- Most of the time only a few keys are lit, yet colors for all keys are stored, most of them black.
```
    [1] = { {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0},
```
- Most people use only a few distinct colors, yet the coding assumes all 16581375 colors are used, storing 8-bit RGB.

This script rewrites a `keymap.c` file as downloaded from Oryx in the following ways:

- Add a table with all distinct color definitions used by the map.
- For each lit layer, generate an array of `(index, color) [2 byte]` tuples coding lit keys only (`color` is an index into the table above)
- Therefore, each lit key will only use 2b (plus some small overhead for the global tables)

- I managed to save `622 bytes` on a map with 7 lit layers

The same can probably been done for the `keymaps` itself.

Bit coding could improve compression further ;)