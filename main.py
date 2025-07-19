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

    terminal_input.terminal_interface(V_REF, MAX_ADC_VALUE, adc)

"""
    try:
        # Initialize the ADC on SPI bus 0, chip select 0 (CE:0)
        adc = ADC_Chip.MCP3208(0, 0)
        
        print("Reading ADC values. Press Ctrl+C to exit.")
        
        # Loop forever, reading from channel 0
        while True:
            # Select the channel you want to read (0-7)
            channel_to_read = 0
            
            raw_value = adc.read_adc(channel_to_read)
            
            if raw_value != -1:
                # Convert the raw ADC value to a voltage
                voltage = (raw_value * V_REF) / MAX_ADC_VALUE
                
                print(f"Channel {channel_to_read}: Raw Value = {raw_value:<4}, Voltage = {voltage:.2f}V")
            
            # Wait for a second before the next reading
            time.sleep(1)
            functions.clear_screen()

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

"""