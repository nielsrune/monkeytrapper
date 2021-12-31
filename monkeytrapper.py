#!/usr/bin/python3

# CC0, originally written by t184256.

# This is an example Python program for Linux that remaps a keyboard.
# The events (key presses releases and repeats), are captured with evdev,
# and then injected back with uinput.

# This approach should work in X, Wayland, anywhere!

# Also it is not limited to keyboards, may be adapted to any input devices.

# The program should be easily portable to other languages or extendable to
# run really any code in 'macros', e.g., fetching and typing current weather.

# The ones eager to do it in C can take a look at (overengineered) caps2esc:
# https://github.com/oblitum/caps2esc


# Import necessary libraries.
import atexit
# You need to install evdev with a package manager or pip3.
import evdev  # (sudo pip3 install evdev)

import signal
import sys


def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)


# /proc/bus/input/devices
PHYS: str = 'usb-0000:00:14.0-14.3/input1'
NAME: str = 'TRAPPER DATA Mousetrapper Advance 2.0'

VIRTUAL_NAME: str = 'MonkeyTrapper'

SCROLL_VALUE: int = 3
# Allow accelleration
# True: fast dragging the edge of the plate is passed through
# False: all scrolling is fixed at set value
ALLOW_ACCEL: bool = False

# Find all input devices.
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
# Limit the list to those containing MATCH and pick the first one.
# Try block to handle no device found
try:
    kbd = [d for d in devices if PHYS in d.phys and NAME in d.name][0]
except IndexError:
    sys.exit(1)

atexit.register(kbd.ungrab)  # Don't forget to ungrab the keyboard on exit!
kbd.grab()  # Grab, i.e. prevent the keyboard from emitting original events

soloing_caps = False  # A flag needed for CapsLock example later.

try:
    # Create a new keyboard mimicking the original one.
    with evdev.UInput.from_device(kbd, name=VIRTUAL_NAME) as ui:
        for ev in kbd.read_loop():  # Read events from original keyboard.
            if ALLOW_ACCEL:
                if (ev.type == evdev.ecodes.EV_REL
                        and ev.code in (evdev.ecodes.REL_WHEEL,
                                        evdev.ecodes.REL_WHEEL_HI_RES)
                        and ev.value in (75, -75, 9000, -9000)):
                    if ev.code == evdev.ecodes.REL_WHEEL and ev.value == 75:
                        ui.write(evdev.ecodes.EV_REL,
                                 evdev.ecodes.REL_WHEEL,
                                 SCROLL_VALUE)
                        ui.write(evdev.ecodes.EV_REL,
                                 evdev.ecodes.REL_WHEEL_HI_RES,
                                 120 * SCROLL_VALUE)
                        ui.syn()
                    elif ev.code == evdev.ecodes.REL_WHEEL and ev.value == -75:
                        ui.write(evdev.ecodes.EV_REL,
                                 evdev.ecodes.REL_WHEEL,
                                 -SCROLL_VALUE)
                        ui.write(evdev.ecodes.EV_REL,
                                 evdev.ecodes.REL_WHEEL_HI_RES,
                                 120 * -SCROLL_VALUE)
                        ui.syn()
                else:
                    # Passthrough other events unmodified (e.g. SYNs).
                    ui.write(ev.type, ev.code, ev.value)

            elif not ALLOW_ACCEL:
                if (ev.type == evdev.ecodes.EV_REL
                        and ev.code in (evdev.ecodes.REL_WHEEL,
                                        evdev.ecodes.REL_WHEEL_HI_RES)):
                    if ev.code == evdev.ecodes.REL_WHEEL and ev.value > 0:
                        ui.write(evdev.ecodes.EV_REL,
                                 evdev.ecodes.REL_WHEEL,
                                 SCROLL_VALUE)
                        ui.write(evdev.ecodes.EV_REL,
                                 evdev.ecodes.REL_WHEEL_HI_RES,
                                 120 * SCROLL_VALUE)
                        ui.syn()
                    elif ev.code == evdev.ecodes.REL_WHEEL and ev.value < 0:
                        ui.write(evdev.ecodes.EV_REL,
                                 evdev.ecodes.REL_WHEEL,
                                 -SCROLL_VALUE)
                        ui.write(evdev.ecodes.EV_REL,
                                 evdev.ecodes.REL_WHEEL_HI_RES,
                                 120 * -SCROLL_VALUE)
                        ui.syn()
                else:
                    # Passthrough other events unmodified (e.g. SYNs).
                    ui.write(ev.type, ev.code, ev.value)

finally:
    print("Exited")
