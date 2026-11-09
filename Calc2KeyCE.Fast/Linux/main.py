'''Cross-platform protocol for communicating with dnmalenke's Calc2KeyCE.
This implementation is written in python in order to improve cross-platform
portability. This implementation targets Linux and Mac devices running X11,
not Wayland.'''

import threading

import usb_utils
import settings

from screen import screen_thread

# USB configuration
vid = 0x0451
pid = 0xE009
fallback = 0xE008
bulk_out = 0x02

def main():
    # Load settings
    config = settings.load_config()
    
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
