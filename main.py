# Original code modified and taken from Collin Peters ADCread.py file
import RPi.GPIO as GPIO
import os
import spidev
import time
import sys
import termios
import tty
import threading
import ADC_Chip
import terminal_input
import functions




# The Program Begins Here!!!!!!!!!!!!!!!!!!!!!!!!!
if __name__ == '__main__':
   
    # Voltage reference for the ADC (3.3V for the ADC Chip).
    V_REF = 3.3 
    
    # The ADC has 12-bit resolution, so the maximum value is 2^12 - 1 = 4095
    MAX_ADC_VALUE = 4095
    
    adc = None

    # Create a stop_event to share between threads
    stop_event = threading.Event()
    try:
        # Initialize the ADC on SPI bus 0, chip select 0 (CE:0)
        adc = ADC_Chip.MCP3208(0, 0)
        

        # Start the keyboard listener in a background thread
        key_thread = threading.Thread(target=terminal_input.listen_for_keys, args=(stop_event,))
        key_thread.daemon = True
        key_thread.start()

        print("Reading ADC values. Ctrl+C to exit.\n")

        while not stop_event.is_set():
            channel_to_read = 0
            raw_value = adc.read_adc(channel_to_read)

            if raw_value != -1:
                voltage = (raw_value * V_REF) / MAX_ADC_VALUE
                print("Key Menu: Press 'g' for CCW, 'l' for CW\n")
                print(f"Channel {channel_to_read}: Raw Value = {raw_value:<4}, Voltage = {voltage:.2f}V\n")

            time.sleep(1)
            functions.clear_screen()

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        stop_event.set()
        if adc:
            adc.close()
            print("SPI connection closed.")
        GPIO.cleanup()
        print("GPIOs cleaned up.")