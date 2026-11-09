'''Cross-platform protocol for communicating with dnmalenke's Calc2KeyCE.
This implementation is written in python in order to improve cross-platform
portability. This implementation targets Linux and Mac devices running X11,
not Wayland.'''

import threading
import argparse

import usb_utils
import settings

from screen import screen_thread

# USB configuration
vid = 0x0451
pid = 0xE009
fallback = 0xE008
bulk_out = 0x02

def init():
    parser = argparse.ArgumentParser(description='Python-based connectivity tool for Calc2KeyCE')

    parser.add_argument('-x', type=int, help='X offset of the camera, in pixels.')
    parser.add_argument('-y', type=int, help='Y offset of the camera, in pixels.')
    parser.add_argument('--width', type=int, help='Width of the camera, in pixels.')
    parser.add_argument('--height', type=int, help='Width of the camera, in pixels.')
    parser.add_argument('-t', '--type', type=str, choices=['auto', 'generic', 'custom'], help='Type of palette to use.')
    parser.add_argument('-p', '--palette', type=str, help='Name of the palette file. Palette must be .pal and be located in /palettes.')
    parser.add_argument('-s', '--scaling', type=str, choices=['nearest', 'box', 'bilinear', 'hamming', 'bicubic', 'lanczos'], help='Scaling method to use. (fastest to slowest)')

    args = parser.parse_args()

    return args
    
def main():
    args = init()
    # Load settings
    config = settings.load_config(args)
    
    # Connect to calculator
    device = usb_utils.connect(vid, pid, fallback)
    print('Connected to calculator.')

    # Create and run the first thread (the screen)
    stop = threading.Event()
    screen = threading.Thread(target=screen_thread, args=(device, bulk_out, config, stop))
    screen.start()

    print('Calculator cast started. Press Ctrl-C or [on] on the calculator to stop.')
    try:
        while not stop.is_set():
            stop.wait()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        screen.join()
    print('Connection terminated')

if __name__ == '__main__':
    main()
