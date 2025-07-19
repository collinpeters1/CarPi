# Original code modified and taken from Collin Peters ADCread.py file

import spidev
import time
import threading
import Keyboad_Input


class MCP3208:
    def __init__(self, spi_bus=0, spi_device=0):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        
        # Set SPI speed and mode. 1MHz is a safe speed.
        # The MCP3208 supports SPI modes 0,0 and 1,1.
        self.spi.max_speed_hz = 1000000
        self.spi.mode = 0

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
        command = [0x01, (8 + channel) << 4, 0x00]
        
        # The spi.xfer2 function sends the command and returns the received data.
        adc_data = self.spi.xfer2(command)
        
        # The 12-bit result is spread across the last two bytes of the received data.
        # We need to combine them to get the final value.
        # adc_data[1] contains the 4 most significant bits.
        # adc_data[2] contains the 8 least significant bits.
        value = ((adc_data[1] & 0x0F) << 8) | adc_data[2]
        return value

    def close(self):
        self.spi.close()



# The Program Begins Here!!!!!!!!!!!!!!!!!!!!!!!!!
if __name__ == '__main__':
   
    # Voltage reference for the ADC (3.3V for the ADC Chip).
    V_REF = 3.3 
    
    # The ADC has 12-bit resolution, so the maximum value is 2^12 - 1 = 4095
    MAX_ADC_VALUE = 4095
    
    adc = None
    try:
        # Initialize the ADC on SPI bus 0, chip select 0 (CE:0)
        adc = MCP3208(0, 0)
        
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
