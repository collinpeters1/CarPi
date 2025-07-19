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