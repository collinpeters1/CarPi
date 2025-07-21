# Purpos of this file is to handle the user interface (command terminal for now).
# This file will do everything from displaying messages on the terminal to
# handling keyboard input from the user. In the future this will turn into
# a GUI interface.

import RPi.GPIO as GPIO
import threading
import sys
import termios
import tty
import select
import spidev
import os
import time
import ADC_Chip
import queue

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

# This funciton is meant to keep the user from button mashing and bricking the program
# The function performs an action if a valid key is pressed and returns command line time
# which is meant to enforce the cooldown
#
# Limited-size queue to store a single unprocessed key at a time
key_queue = queue.Queue(maxsize=1)
def process_key_queue(last_command_time, cooldown):
    try:
        key = key_queue.get_nowait()
        current_time = time.time()

        if current_time - last_command_time > cooldown:
            last_command_time = current_time
            if key == 'g':
                print("'g' command processed", flush=True)
            elif key == 'l':
                print("'l' command processed", flush=True)
        else:
            print("\nKey received too soon — ignoring (cooldown active)", flush=True)

    except queue.Empty:
        pass

    return last_command_time

# Function to clear the terminal window
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

########################################################
#    This is the function that is called to main.py    #
########################################################
def terminal_interface(V_REF, MAX_ADC_VALUE):
    try:
        # Initialize the ADC on SPI bus 0, chip select 0 (CE:0)
        adc = ADC_Chip.MCP3208(0, 0)
        
        # Setup threading to see if a user presses a valid key
        key_listener = threading.Thread(target=listen_for_keys, daemon=True)
        key_listener.start()

        # Queue Control Variables to enforce cooldown
        last_command_time = 0
        cooldown = 0.5  # seconds between allowed command executions

        # Loop forever, reading from channel 0
        while True:
            # Select the channel you want to read (0-7)
            channel_to_read = 0
            raw_value = adc.read_adc(channel_to_read)
            
            print("Reading ADC values. Press Ctrl+C to exit.", flush=True)
            print("Press 'l' to move CW, Press 'g' to move CCW\n", flush=True)
            if raw_value != -1:
                # Convert the raw ADC value to a voltage
                voltage = (raw_value * V_REF) / MAX_ADC_VALUE
                s_voltage = adc.get_stable_voltage(channel_to_read, V_REF)
                print(f"Channel {channel_to_read}: Raw Value = {raw_value:<4}, Voltage = {voltage:.2f}V, Smooth Voltage = {s_voltage:.2f}V", flush=True)
            
            # Now Process key in queue if available
            last_command_time = process_key_queue(last_command_time, cooldown)    
            
            # Wait for a second before the next reading
            time.sleep(1)
            clear_screen()

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if adc:
            adc.close()
            print("SPI connection closed.")
            GPIO.cleanup()
            print("GPIOs cleaned up.")
