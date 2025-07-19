import threading
import sys
import termios
import tty

# Non-Blocking Key Press Function
def get_keypress():
    # Makes terminal get char without Enter needing to be pressed
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)  # read 1 character
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# Background Threading for keyboard input (listening)
def listen_for_keys(stop_event):
    print("Press 's' to save, 'q' to quit.")
    while not stop_event.is_set():
        key = get_keypress()
        if key == 's':
            print("✅ SAVE action triggered!")
        elif key == 'q':
            print("🛑 Quit requested.")
            stop_event.set()  # signal to exit main loop
