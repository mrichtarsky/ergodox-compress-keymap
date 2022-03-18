import re

KEYMAP_FILE = r'c:\Users\Martin\qmk_firmware\keyboards\ergodox_ez\keymaps\martin_colemak\keymap.c'

LEDMAP_INDICATOR = 'const uint8_t PROGMEM ledmap[][DRIVER_LED_TOTAL][3]'

def process_ledmap(f, outlines):
    distinct_colors = set()
    layer_ids = []
    layers = []

    # Read existing keymap
    while 1:
        line = f.readline()
        if line.startswith('};'):
            break
        if len(line.strip()) == 0:
            continue
        mo = re.match(r'^\s*\[(\d+)\] = \{(.*?)\},\s*$', line)
        layer_id = int(mo.group(1))
        layer_ids.append(layer_id)
        colors = re.findall(r'\{(\d+),(\d+),(\d+)\}', mo.group(2))
        colors = [ tuple(map(int, color)) for color in colors ]
        layers.append(colors)
        distinct_colors.update(colors)

    print(len(distinct_colors), 'distinct colors')

    # Map layer id as passed to set_layer_color() to index in ledmap_indirect
    led_layer_map_size = max(layer_ids) + 1
    led_layer_map = [ 0 ] * (led_layer_map_size)
    for i, layer_id in enumerate(layer_ids):
        led_layer_map[layer_id] = i

    outlines.append(f"const uint8_t PROGMEM led_layer_map[{led_layer_map_size}] = {{ {', '.join(map(str, led_layer_map))} }};")

    outlines.append(f"const uint8_t PROGMEM ledmap_distinct_colors[{len(distinct_colors)}][3] = {{")

    distinct_colors = list(distinct_colors)
    for color in distinct_colors:
        outlines.append(f"    {{{color[0]}, {color[1]}, {color[2]}}},")
    outlines.append('};\n')

    # For each layer, store a list of keys that have a color
    outlines.append('typedef struct { uint8_t index; uint8_t distinct_color; } index_color_tuple;\n')

    for layer_index, layer in enumerate(layers):
        indirect = [ "{ %s, %s }" % (index, distinct_colors.index(k)) for index, k in enumerate(layer) if k != (0, 0, 0) ]
        indirect.append('{ 255, 255 }') # End marker
        outlines.append(f"const index_color_tuple PROGMEM ledmap_indirect_{layer_index}[] = {{ {', '.join(indirect)} }};\n")

    outlines.append('const index_color_tuple *const PROGMEM ledmap_indirect_sparse[] = {')
    for layer_index, _ in enumerate(layers):
        outlines.append(f"    &ledmap_indirect_{layer_index}[0],")
    outlines.append('};\n')

    # Replace set_layer_color() function
    assert f.readline().strip() == ''
    sig = f.readline()
    assert sig.startswith('void set_layer_color(int layer)')

    while not f.readline().startswith('}'):
        pass

    func = '''
void set_layer_color(int layer) {
  uint8_t layer_index = pgm_read_byte(&led_layer_map[layer]);
  const index_color_tuple *ledmap = pgm_read_ptr(&ledmap_indirect_sparse[layer_index]);

  int i = 0;
  int next_i = 0;
  do {
    next_i = pgm_read_byte(&ledmap->index);
    if (next_i == 255) {
      next_i = DRIVER_LED_TOTAL;
    } else {
      uint8_t distinct_color_index = pgm_read_byte(&ledmap->distinct_color);
      HSV hsv = {
        .h = pgm_read_byte(&ledmap_distinct_colors[distinct_color_index][0]),
        .s = pgm_read_byte(&ledmap_distinct_colors[distinct_color_index][1]),
        .v = pgm_read_byte(&ledmap_distinct_colors[distinct_color_index][2]),
      };
      RGB rgb = hsv_to_rgb( hsv );
      float f = (float)rgb_matrix_config.hsv.v / UINT8_MAX;
      rgb_matrix_set_color( next_i, f * rgb.r, f * rgb.g, f * rgb.b );
    }
    for (int j = i; j < next_i; ++j) {
      rgb_matrix_set_color( j, 0, 0, 0 );
    }
    i = next_i + 1;
    ++ledmap;
  } while (next_i != DRIVER_LED_TOTAL);
}
'''
    outlines.extend(func.split('\n'))

outlines =  []
with open(KEYMAP_FILE, 'rt') as f:
    while 1:
        line = f.readline()
        if len(line) == 0:
            break

        if line.startswith(LEDMAP_INDICATOR):
            process_ledmap(f, outlines)
        else:
            outlines.append(line.rstrip())

with open(KEYMAP_FILE, 'wt') as f:
    f.write('\n'.join(outlines))



#622 gains for 7 layers colored
#508+150