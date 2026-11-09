'''Method to connect to the calculator running Calc2KeyCE'''

import usb.core
import usb.util

def connect(vid, pid, fallback):

    # Search for calculators with Calc2KeyCE open
    device = usb.core.find(idVendor=vid, idProduct=pid)
    if device is None:
        # Check to see if the user hasn't launched the application on the calculator
        if usb.core.find(idVendor=vid, idProduct=fallback):
            raise SystemExit('Calculator found, but is not running Calc2KeyCE. Launch the program first and try again.')
        else: # Calculator not found
            raise SystemExit('Calculator not found. Check cable connection, application permissions, and make sure the calculator is ON.')

    # Make sure the OS has not taken control of the device
    try:
        if device.is_kernel_driver_active(0):
            device.detach_kernel_driver(0)
    except (NotImplementedError, usb.core.USBError) as e: # Handle OS-specific errors
        print('Error disconnecting device from operating system')

    # Initialize the USB device
    device.set_configuration()

    # Connect to the calculator
    usb.util.claim_interface(device, 0)

    return device

def send(device, endpoint, data):
    # I think this one is pretty obvious
    device.write(endpoint, data)
