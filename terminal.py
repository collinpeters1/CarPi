# Purpos of this file is to handle the user interface (command terminal for now).
# This file will do everything from displaying messages on the terminal
# to handling keyboard input from the user. In the future this will turn into
# a GUI interface.

import RPi.GPIO as GPIO
import threading
import sys
import termios
import tty
import spidev
import os
import time
import ADC_Chip
import functions


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

# Function for Background Threading and keyboard input (listening)
def listen_for_keys(stop_event):
    while not stop_event.is_set():
        key = get_keypress()
        if key == 'g':
            print("g pressed")
        elif key == 'l':
            print("l pressed")
            stop_event.set()  # signal to exit main loop

# Function to clear the terminal window
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

########################################################
#    This is the function that is called to main.py    #
########################################################
def terminal_interface(V_REF, MAX_ADC_VALUE, adc):
    try:
        # Initialize the ADC on SPI bus 0, chip select 0 (CE:0)
        adc = ADC_Chip.MCP3208(0, 0)
        
        # Loop forever, reading from channel 0
        while True:
            # Select the channel you want to read (0-7)
            channel_to_read = 0
            
            raw_value = adc.read_adc(channel_to_read)
            
            # Setup threading to see if a user presses a valid key
            """threading.Thread(target=listen_for_keys, args=(stop_event,), daemon=True).start()"""
            # This should work ^^^

            print("Reading ADC values. Press Ctrl+C to exit.")
            print("Press 'l' to move CW, Press 'g' to move CCW\n")
            if raw_value != -1:
                # Convert the raw ADC value to a voltage
                voltage = (raw_value * V_REF) / MAX_ADC_VALUE
                s_voltage = adc.get_stable_voltage(channel_to_read, V_REF)
                print(f"Channel {channel_to_read}: Raw Value = {raw_value:<4}, Voltage = {voltage:.2f}V, Smooth Voltage = {s_voltage:.2f}V")
            
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
