import pyinputplus as pyip #verify that the input value entered is a number
import RPi.GPIO as GPIO #Raspberry pi pin enabled"
from time import sleep


while True:
    response = pyip.inputNum('Enter number: ')
        
    if response == 5:
        print ("up")
    elif response == 6:
        print("down")
            
    elif response == 7:
        print("right")
        
    elif response == 8:
        print("left")

#     elif response == 9:
#         response2 = pyip.inputNum('Enter number: ')
#         if response2 == 90:
#             print("right angle")
#             continue
    else:
        print("no option")