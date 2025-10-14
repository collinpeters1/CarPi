# Motor functions for PWM control

import RPi.GPIO as GPIO
import time
import ADC_Chip

# Global Values for CAR pot
MAX_LOAD_POS = 0.66
LOAD_POS = 0.9
GROW_POS = 2.35
MAX_GROW_POS = 2.37


# GLOBAL PIN DEFINITIONS 
# PINS ARE BCM!!!!!!!!!!!!!
MOTOR_IN1_PIN = 5
MOTOR_IN2_PIN = 6
ENABLE_PIN = 12
PWM_FREQUENCY = 300
# Global PWM object
p = None

##############################
######## FUNCTION LIB ########
##############################

# Sets up GPIO to drive the CAR motor
def setup_pins():
    global p
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MOTOR_IN1_PIN, GPIO.OUT)
    GPIO.setup(MOTOR_IN2_PIN, GPIO.OUT)
    GPIO.setup(ENABLE_PIN, GPIO.OUT)
    
    p = GPIO.PWM(ENABLE_PIN, PWM_FREQUENCY)
    print("GPIO enabled --- you are clear for launch\n")

# This function moves the CAR to the grow position
# The grow position needs to be set in the ADC_Chip.py file
def move_to_grow(adc, channel=0, tolerance=0.01, speed=25):
    print("[TEST] Stepping motor to Grow Position...")

    while True:
        # Sample the voltage after each step
        s_voltage = adc.get_stable_voltage(channel, ADC_Chip.V_REF)
        print(f"[DEBUG] Pot voltage: {s_voltage:.2f} V, Target: {GROW_POS:.2f} V")

        # Exit loop if within range or safety overtravel
        if abs(s_voltage - GROW_POS) <= tolerance or s_voltage > MAX_GROW_POS:
            break

        # Step the motor for a brief moment
        motor_forward(speed)
        time.sleep(0.05)
        motor_brake()
        time.sleep(0.01)

    print("Grow position reached.")

# This function moves the CAR to the load position
# The load position needs to be set in the ADC_Chip.py file
def move_to_grow(adc, channel=0, tolerance=0.01, speed=25):
    print("Stepping motor to Load Position...")

    while True:
        # Sample the voltage
        s_voltage = adc.get_stable_voltage(channel, ADC_Chip.V_REF)
        print(f"Pot voltage: {s_voltage:.2f} V, Target: {LOAD_POS:.2f} V")
        
        # Exit loop if within range or safety overtravel
        if abs(s_voltage - LOAD_POS) <= tolerance or s_voltage > MAX_LOAD_POS:
            break

        # Step the motor for a brief moment
        motor_forward(speed)
        time.sleep(0.05)
        motor_brake()
        time.sleep(0.01)
        
    print("Load position reached.")


# Function to drive the motor in a specified direction at a given speed.
# :param direction: grow position 'g', load position 'l'
# :param speed: int (0-100), is the dutry cycle for the motor speed
def motor_drive(direction, speed):
    if direction == 'g':
        GPIO.output(MOTOR_IN1_PIN, GPIO.HIGH)
        GPIO.output(MOTOR_IN2_PIN, GPIO.LOW)
    elif direction == 'l':
        GPIO.output(MOTOR_IN1_PIN, GPIO.LOW)
        GPIO.output(MOTOR_IN2_PIN, GPIO.HIGH)
    if p:
        p.ChangeDutyCycle(speed)
    print(f"[DEBUG] Motor direction: {direction}, speed: {speed}")

# Function to be used to stop the motor
def motor_brake():
    p.stop()
    GPIO.output(MOTOR_IN1_PIN, GPIO.LOW)
    GPIO.output(MOTOR_IN2_PIN, GPIO.LOW)

# Testing function to move the motor "forward"
def motor_forward(speed):
    GPIO.output(MOTOR_IN1_PIN, GPIO.HIGH)
    GPIO.output(MOTOR_IN2_PIN, GPIO.LOW)
    # https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/
    p.start(speed)
    print(f"Motor moving forward at {speed}% speed.")

# Testing function to move the motor "backward"
def motor_backward(speed):
    GPIO.output(MOTOR_IN1_PIN, GPIO.LOW)
    GPIO.output(MOTOR_IN2_PIN, GPIO.HIGH)
    # https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/
    p.start(speed)
    print(f"Motor moving backward at {speed}% speed.") 
    
def cleanup_pins():
    motor_brake()
    GPIO.cleanup()