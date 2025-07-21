# Purpos of this file is to handle the user interface (command terminal for now).
# This file will do everything from displaying messages on the terminal to
# handling keyboard input from the user. In the future this will turn into
# a GUI interface.

# import RPi.GPIO as GPIO
import sys
import termios
import tty
import select
import os
import time
import queue
import motor_lib as motor

# Limited-size queue to store a single unprocessed key at a time
key_queue = queue.Queue(maxsize=1)


#####################################
#           Functions               #
#####################################

# Non-Blocking Key Press Function
def get_keypress(timeout=0.1):
    fd = sys.stdin.fileno()  # Get the file descriptor for standard input (keyboard)
    old_settings = termios.tcgetattr(fd)  # Save the current terminal settings
    
    try:
        tty.setcbreak(fd)  # Set terminal to 'cbreak' mode (faster response than canonical mode but still handles Ctrl+C)
        
        # select() checks if input is ready (keyboard in this case)
        # Behind the scenes, select is polling for activity on file descriptors.
        rlist, _, _ = select.select([fd], [], [], timeout)
        
        if rlist:  # If there's input ready on stdin
            return sys.stdin.read(1)  # Read a single character (non-blocking)
    
    finally:
        # Restore the original terminal settings to avoid leaving the terminal in cbreak mode
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return None  # No key was pressed within the timeout

# Function to listen in the background for keyboard inputs
def listen_for_keys():
    while True:
        key = get_keypress()
        if key in ('g', 'l'):
            try:
                key_queue.put_nowait(key)
            except queue.Full:
                pass

# This funciton is meant to keep the user from button mashing and bricking the program.
# The function performs an action (GPIO for motor control) if a valid key is pressed 
# and returns command line time which is meant to enforce the cooldown.
def process_key_queue(last_command_time, cooldown):
    try:
        key = key_queue.get_nowait()
        current_time = time.time()

        if current_time - last_command_time > cooldown:
            last_command_time = current_time

            if key == 'g':
                print("'g' command processed", flush=True)
                motor.motor_forward()
                sleep(1)
                motor.motor_brake()

                # We need to drive the motor to the grow position
                # Then stop the motor
                

            elif key == 'l':
                print("'l' command processed", flush=True)
<<<<<<< HEAD
                motor.motor_backward()
                sleep(1)
                motor.motor_brake()

=======

                # We need to drive the motor to the load postion
                # Then stop the motor
>>>>>>> 694012ba8ba51cdafc1427d2d385adb1e1fd1d89
        else:
            print("\nKey received too soon — ignoring (cooldown active)", flush=True)

    except queue.Empty:
        pass

    return last_command_time

# Function to clear the terminal window
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')