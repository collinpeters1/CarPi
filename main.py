# Created by Collin Peters and Stuart Plaugher
# Dr. Wistey's Lab Group (EPEE), Summer 2025


import RPi.GPIO as GPIO
import time
import threading
import ADC_Chip
import terminal
import motor_lib as motor


# Start your debug here
def main():
   
    # Voltage reference for the ADC (3.3V for the ADC Chip).
    V_REF = 3.3 
    
    # The ADC has 12-bit resolution, so the maximum value is 2^12 - 1 = 4095
    MAX_ADC_VALUE = 4095
    
    # Begin The main working code
    try:
        # Initialize the ADC on SPI bus 0, chip select 0 (CE:0)
        adc = ADC_Chip.MCP3208(0, 0)
        
        # Setup threading to see if a user presses a key that does something!
        key_listener = threading.Thread(target=terminal.listen_for_keys, daemon=True)
        key_listener.start()

        # Queue Control Variables to enforce cooldown
        last_command_time = 0
        cooldown = 0.5  # seconds between allowed command executions

        # Setup GPIO for motor control
        motor.setup_pins()

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
                #print(f"-> ADC: {s_voltage:.2f}V | Key Command: {last_key_pressed} ", end='\r', flush=True)
                print(f"Channel {channel_to_read}: Raw Value = {raw_value:<4}, Voltage = {voltage:.2f}V, Smooth Voltage = {s_voltage:.2f}V", flush=True)
            
            # Now Process a key command in queue if available
            # The GPIO stuff happens in the process_key_queue function
            last_command_time = terminal.process_key_queue(last_command_time, cooldown)    

            # Wait for a second before the next reading
            time.sleep(1)
            terminal.clear_screen()

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if adc:
            adc.close()
            print("SPI connection closed.")
            motor.cleanup_pins()
            print("GPIOs cleaned up.")



# I am called down here!!
###################################################

if __name__ == '__main__':
    main()

###################################################