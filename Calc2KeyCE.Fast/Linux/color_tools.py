import numpy

def generate_palette():
    """The 240 colours of the fixed palette (a 240 x 3 array of 0-255 values)."""
    cube = [(r * 51, g * 51, b * 51)                  # 216: even 6x6x6 grid
            for r in range(6) for g in range(6) for b in range(6)]
    have = set(cube)
    # Extra levels at 26 between 0 and 51: a finer 3x3x3 grid in the dark corner.
    # 27 combinations, 8 of which are already in the cube -> 19 new colours.
    dark = [(r, g, b) for r in (0, 26, 51) for g in (0, 26, 51) for b in (0, 26, 51)]
    dark = [c for c in dark if c not in have]
    # 5 more grays, giving a fine gray ramp up to 102: 0,13,26,38,51,64,77,89,102
    grays = [(v, v, v) for v in (13, 38, 64, 77, 89)]
    # 3 more browns?

    return numpy.array(cube + dark + grays, dtype=numpy.int32)       # 216 + 19 + 5 = 240
    # Palettes except up to 256 colours, this only has 240. Might add some more brown colour depth.


def read_palette(file):
    palette = []
    try:
        with open(f'palettes/{file}', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

            if lines[0] != 'JASC-PAL':
                return [(0, 0, 0)]

            version = lines[1]
            num_colors = int(lines[2])
            color_lines = lines[3:]

            for line in color_lines:
                channels = tuple(map(int, line.split()))
                
                if len(channels) == 3:
                    palette.append(channels)
    except FileNotFoundError:
        print('Error: Palette not found.')
        return None
    
    return palette

def build_lut(colors):
    """For every colour the calculator can show (5 bits per channel = 32768 of them),
    find the nearest palette entry. Built once at start-up."""
    g = numpy.arange(32, dtype=numpy.int32)
    r5, g5, b5 = numpy.meshgrid(g, g, g, indexing="ij")
    pts = numpy.stack([r5, g5, b5], -1).reshape(-1, 3) * 255 // 31   # 5-bit -> 8-bit
    weights = (3, 4, 2)                    # the eye is most sensitive to green, least to blue
    dist = sum(w * (pts[:, c, None] - colors[None, :, c]) ** 2 for c, w in enumerate(weights))
    return dist.argmin(1).astype(numpy.uint8)       # LUT[(r5 << 10) | (g5 << 5) | b5]

