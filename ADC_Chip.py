# This file is meant to house everything related to the ADC chip.
# The file creates a class for the ADC Chip to read the data from
# and the file contains functions for reading voltage and angles
# from the SPI data.

import spidev
import time

# This Class is meant for the MCP3204-C from Micron (ADC)
class MCP3208:
    def __init__(self, spi_bus=0, spi_device=0):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        
        # Set SPI speed and mode. 1MHz is a safe speed.
        # The MCP3208 supports SPI modes 0,0 and 1,1.
        self.spi.max_speed_hz = 1000000
        self.spi.mode = 0

    # Function to read data from the ADC chip
    def read_adc(self, channel):
        if not 0 <= channel <= 7:
            print("Invalid channel. Must be between 0 and 7.")
            return -1

        # The command to send to the MCP3208 consists of 3 bytes.
        # It's constructed based on the datasheet to select single-ended mode
        # and the desired channel.
        # Byte 1: Start bit
        # Byte 2: Config bits (Single-ended mode, channel selection)
        # Byte 3: Dummy byte to clock out the rest of the data
        command = [0x06 | (channel >> 2),          # 0x06 = 0b00000110  →  Start=1, SGL=1, D2
        (channel & 0x03) << 6,          # D1-D0 shifted into the top of byte 2
       0x00]
        
        # The spi.xfer2 function sends the command and returns the received data.
        adc_data = self.spi.xfer2(command)
        
        # The 12-bit result is spread across the last two bytes of the received data.
        # We need to combine them to get the final value.
        # adc_data[1] contains the 4 most significant bits.
        # adc_data[2] contains the 8 least significant bits.
        value = ((adc_data[1] & 0x0F) << 8) | adc_data[2]
        return value

    # Reads an ADC channel multiple times and return an average voltage.
    # Helps to smooth out noisy readings.
    def get_stable_voltage(self, channel, V_REF, num_readings=5, delay=0.01):
        readings = []
        for _ in range(num_readings):
            # Convert 12-bit raw value (0-4095) to voltage
            raw_value = self.read_adc(channel)
            voltage = raw_value * (V_REF / 4095.0)
            readings.append(voltage)
            time.sleep(delay)
        return sum(readings) / len(readings)

    # Function to close the instance
    def close(self):
        self.spi.close()


# Converts a voltage reading to a 0-180 degree angle.
def voltage_to_angle(voltage, v_load, v_grow):
    if (v_load - v_grow) == 0:
        return 0 # Avoid division by zero
    angle = 180 * (voltage - v_grow) / (v_load - v_grow)
    return max(0, min(180, angle)) # Clamp angle between 0 and 180