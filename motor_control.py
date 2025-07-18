import RPi.GPIO as GPIO
from time import sleep
import pyinputplus as pyip #verify that the input value entered is a number


GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.OUT) #IN1 
GPIO.setup(6, GPIO.OUT) #IN2
GPIO.setup(12, GPIO.OUT) #enable

p = GPIO.PWM(12, 300)
while True:
    response = pyip.inputNum('Enter number: ')
    
    if response == 5:
#         print ("up")
        print('forward')
        GPIO.output(5, GPIO.LOW)
        GPIO.output(6, GPIO.HIGH)
        p.start(20)
    
        
    elif response == 6:
#         print("down")
        print('backward')
        GPIO.output(5, GPIO.LOW)
        GPIO.output(6, GPIO.HIGH)
        p.start(100)
        
        
    elif response == 7:
#         print("right")
        print('clockwise')
#         right pin to right pin
        GPIO.output(12, GPIO.HIGH)
        GPIO.output(6, GPIO.LOW)
        GPIO.output(5, GPIO.HIGH)
        
    elif response == 8:
#         print("right")
        print('stop')
#         right pin to right pin
        GPIO.output(12, GPIO.LOW)
        GPIO.output(6, GPIO.LOW)
#         GPIO.output(5, GPIO.HIGH)