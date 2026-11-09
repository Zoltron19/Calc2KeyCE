'''Grab the user's screen and cast it to the calculator over usb.'''

import mss
import struct
import numpy
import pyautogui

from pathlib import Path
from PIL import Image

import usb_utils
import color_tools

def init(settings):
    # Load config values.
    if 'x' in settings:
        x = settings['x']
    else:
        x = 0
    if 'y' in settings:
        y = settings['y']
    else:
        y = 0
    if 'width' in settings:
        width = settings['width']
    else:
        width = 'auto'
    if 'height' in settings:
        height = settings['height']
    else:
        height = 'auto'
    if 'type' in settings:
        palette_type = settings['type']
    else:
        palette_type = 'auto'
    if 'palette' in settings:
        file = settings['palette']
    else:
        file = None
    if 'scaling' in settings:
        scaling = settings['scaling']
    else:
        scaling = 'nearest'

    if file:
        path = Path('palettes/') / file
    else:
        path = None

    if width == 'auto':
        w, h = pyautogui.size()
        width = w - x
    if height == 'auto':
        w, h = pyautogui.size()
        height = h - y
    
    if palette_type == 'generic':
        colors = color_tools.generate_palette()
        entries = [rgb_to_bgr1555(*map(int, c)) for c in colors] + [0] * (256 - len(colors))
        palette = struct.pack('<256H', *entries)
        lut = color_tools.build_lut(colors)
        palette_type = 'custom' # Set for internal handling
    elif palette_type == 'custom' and file and path.is_file():
        colors = numpy.array(color_tools.read_palette(file), dtype=numpy.int32)
        entries = [rgb_to_bgr1555(*map(int, c)) for c in colors] + [0] * (256 - len(colors))
        palette = struct.pack('<256H', *entries)
        lut = color_tools.build_lut(colors)
    else:
        if palette_type == 'custom':
            print('Error: Palette not found. Defaulting to auto palette.')
        palette_type = 'auto'
        palette = None
        lut = None
        
    return x, y, width, height, palette_type, palette, lut, scaling

def screen_thread(device, bulk_out, settings, stop):
    # Turn the user-defined settings into parameters
    x, y, width, height, palette_type, palette, lut, scaling = init(settings)
    capture_area = {'left': x, 'top': y, 'width': width, 'height': height}
    # initialize the camera object
    camera = mss.MSS()
    try:
        while not stop.is_set(): # Exit when stop is set
            # Capture screen and convert it to a format the calculator can read
            screen = camera.grab(capture_area)
            image = Image.frombytes('RGB', screen.size, screen.bgra, 'raw', 'BGRX')
            header, frame = build_frame(image, palette_type, palette, lut, scaling)
            usb_utils.send(device, bulk_out, header)
            usb_utils.send(device, bulk_out, frame)
    except Exception as e:
        print(e)
    finally:
        try:
            header = struct.pack('<i', -1).ljust(64, b'\0')
            usb_utils.send(device, bulk_out, header)
        except Exception as e:
            print('Could not terminate connection. (Already terminated)')
        stop.set()
            
def build_frame(image, palette_type, palette, lut, scaling):
    '''Convert the PIL image to the calculator's header and frame data'''
    # Resize the screen
    if scaling == 'lanczos':
        image = image.convert('RGB').resize((320, 240), Image.Resampling.LANCZOS)
    elif scaling == 'bicubic':
        image = image.convert('RGB').resize((320, 240), Image.Resampling.BICUBIC)
    elif scaling == 'hamming':
        image = image.convert('RGB').resize((320, 240), Image.Resampling.HAMMING)
    elif scaling == 'bilinear':
        image = image.convert('RGB').resize((320, 240), Image.Resampling.BILINEAR)
    elif scaling == 'box':
        image = image.convert('RGB').resize((320, 240), Image.Resampling.BOX)
    else:
        image = image.convert('RGB').resize((320, 240), Image.Resampling.NEAREST)
        
        
    # Apply palette based on user-defined settings
    if palette_type == 'custom':
        pixels = to_indices(image, lut)
        frame = palette + pixels
    else:
        # Reduce colors and generate palette
        image = image.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        image = image.transpose(Image.Transpose.ROTATE_270) # The calculator's screen is just messed up.
        rgb = image.getpalette()[:768]
        entries = [rgb_to_bgr1555(*rgb[i:i + 3]) for i in range(0, len(rgb), 3)]
        palette = struct.pack('<256H', *entries)

        # Create byte objects
        pixels = image.tobytes()
        frame = palette + pixels

    header = struct.pack('<i', len(frame)).ljust(64, b'\0')

    return header, frame

def rgb_to_bgr1555(r, g, b):
    '''Calculator palette entry: 0BBBBBGGGGGRRRRR (5 bits per channel).'''
    # Convert the color space to the calculator's.
    c5 = lambda c: (c * 31 * 2 + 255) // 510      # == round(c * 31 / 255)
    return (c5(b) << 10) | (c5(g) << 5) | c5(r)

def to_indices(image, lut):
    '''320x240 RGB PIL image -> 76800 palette indices in wire order.'''
    a = numpy.asarray(image, dtype=numpy.uint16)
    q = (a * 31 + 127) // 255 # each channel: 0-255 -> 0-31
    idx = lut[(q[..., 0] << 10) | (q[..., 1] << 5) | q[..., 2]]
    return numpy.rot90(idx, k=-1).astype(numpy.uint8).tobytes() # Rotate clockwise
