#motor functions for PWM control
import RPi.GPIO as GPIO
# GLOBAL PIN DEFINITIONS 
# PINS ARE BCM!!!!!!!!!!!!!
MOTOR_IN1_PIN = 5
MOTOR_IN2_PIN = 6
ENABLE_PIN = 12
PWM_FREQUENCY = 300



# Global PWM object
p = None


##### FUNCTION LIB ###########

    def setup_pins():
        """initialize GPIO"""
        global p
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MOTOR_IN1_PIN, GPIO.OUT)
        GPIO.setup(MOTOR_IN2_PIN, GPIO.OUT)
        GPIO.setup(ENABLE_PIN, GPIO.OUT)
        
        p = GPIO.PWM(ENABLE_PIN, GPIO.OUT)
        print("GPIO enabled --- you are clear for launch")
        
    
    def motor_forward(speed):
        GPIO.output(MOTOR_IN1_PIN, GPIO.HIGH)
        GPIO.output(MOTOR_IN2_PIN, GPIO.LOW)
        # https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/
        p.start(speed)
        print(f"Motor moving forward at {speed}% speed.")
 
    def motor_backward(speed):
        GPIO.output(MOTOR_IN1_PIN, GPIO.LOW)
        GPIO.output(MOTOR_IN2_PIN, GPIO.HIGH)
        # https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/
        p.start(speed)
        print(f"Motor moving backward at {speed}% speed.") 

    
    def motor_drive(direction, speed):
        """
        Drives the motor in a specific direction at a given speed.
        :param direction: grow position - g, load position - l
        :param speed: int (0-100), the duty cycle for motor speed.
        """
        if direction == 'g':
            GPIO.output(MOTOR_IN1_PIN, GPIO.HIGH)
            GPIO.output(MOTOR_IN2_PIN, GPIO.LOW)
            p.start(speed)
        elif direction == 'l':
            GPIO.output(MOTOR_IN1_PIN, GPIO.LOW)
            GPIO.output(MOTOR_IN2_PIN, GPIO.HIGH)
            p.start(speed)