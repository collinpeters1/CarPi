from pynput import keyboard
from time import sleep
import pyinputplus as pyip #verify that the input value entered is a number
import board
import spidev
from numpy import interp
import RPi.GPIO as GPIO
from pynput import keyboard
import sys
# from threading import Thread
import time
import threading
import queue
import termios


class NonBlockingConsole(object):

    def __enter__(self):
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)


    def get_data(self):
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return False


spi = spidev.SpiDev()
spi.open(0,0)

GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.OUT)  #IN1
GPIO.setup(6, GPIO.OUT)  #IN2
GPIO.setup(12, GPIO.OUT) #enable

p = GPIO.PWM(12, 200)

def analogInput(channel):
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel) << 4,0])
    data = ((adc[1]&3) <<8) + adc[2]
    return data


def readPot():
    potvalue = analogInput(0)
#     print(potvalue)
    return potvalue
   
# Nonblocking input code from https://nam04.safelinks.protection.outlook.com/?url=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F2408560%2Fnon-blocking-console-input&data=05%7C02%7Ce_v288%40txstate.edu%7C276a633aaa1643235f2d08dcab45a47f%7Cb19c134a14c94d4caf65c420f94c8cbb%7C0%7C0%7C638573562800956498%7CUnknown%7CTWFpbGZsb3d8eyJWIjoiMC4wLjAwMDAiLCJQIjoiV2luMzIiLCJBTiI6Ik1haWwiLCJXVCI6Mn0%3D%7C0%7C%7C%7C&sdata=i7Uk%2Bj0CFzATI%2FAwYbKcxll51DSVfJst%2FzXBIEzmoZw%3D&reserved=0
def add_input(input_queue):
    
    while True:
        input_queue.put(sys.stdin.read(1))

def store_angles(grow_angle,load_angle,up_angle,down_angle):
    print('Need to save angles (voltages) to file here!')

def read_angles():
#     print('Need to read angles (voltages) from file here!')
#     print('Remember to add sanity checking and validation too!!!')
#     print('Angles out of range, bad file formatting, etc.')
    # For now, set default pot "voltage" (ADC reading) for each CAR position
    grow_angle = 15
    load_angle = 330
    up_angle = 165
    down_angle = 500
    return [grow_angle,load_angle,up_angle,down_angle]


print("""g = grow, G = set grow angle, l = load, L = set load, u = up,
U = set up angle, d = down, D = set down angle, m = enable motor,
n = disable motor, c = clockwise, cw = counterclockwise, x = Quit""")

# Nonblocking code from https://nam04.safelinks.protection.outlook.com/?url=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F2408560%2Fnon-blocking-console-input&data=05%7C02%7Ce_v288%40txstate.edu%7C276a633aaa1643235f2d08dcab45a47f%7Cb19c134a14c94d4caf65c420f94c8cbb%7C0%7C0%7C638573562800974428%7CUnknown%7CTWFpbGZsb3d8eyJWIjoiMC4wLjAwMDAiLCJQIjoiV2luMzIiLCJBTiI6Ik1haWwiLCJXVCI6Mn0%3D%7C0%7C%7C%7C&sdata=QZwKup684PhrKu8ndNq46V219P3axVER7PEwFXaY5gk%3D&reserved=0
# Get input in a separate thread, since threads don't block each other by default
input_queue = queue.Queue()
input_thread = threading.Thread(target=add_input, args=(input_queue,))
input_thread.daemon = True
input_thread.start()
last_update = time.time()

motor_on = True
target_angle = readPot()

[grow_angle,load_angle,up_angle,down_angle] = read_angles()   # read angles from file
v = ' '
p.stop()
while True:
    # Plan:
    # Check (using nonblocking read) if user has pressed a key.
    # If user presses a key, remember that (v) and use it as our new target
    # Don't change v unless user presses another key.
    # If capital letter G/L/U/D, store the current voltage for corresponding
    # position, both in the variable (grow_angle, etc.) and on disk.
   
    if not input_queue.empty():
        v = input_queue.get()
            
#             v = NonBlockingConsole().get_data()

    if v == 'G':
        grow_angle = readPot()
        print('Setting grow angle to ',grow_angle)
        store_angles(grow_angle,load_angle,up_angle,down_angle)
        v = 'g'   # Stay at this angle until next keypress
#         break
    
    if v == 'g':
        target_angle = grow_angle
   
   
    
    elif v == 'L':
        load_angle = readPot()
        print('Setting grow angle to ',load_angle)
        store_angles(grow_angle,load_angle,up_angle,down_angle)
        v = 'l'   # Stay at this angle until next keypress
        
        # copy code here from 'G' above
    if v == 'l':
        
        target_angle = load_angle
        
        # copy code here from 'g' above
    
        
    elif v == 'U':
        # copy code here from 'G' above
        up_angle = readPot()
        print('Setting grow angle to ',up_angle)
        store_angles(grow_angle,load_angle,up_angle,down_angle)
        v = 'u'   # Stay at this angle until next keypress
        
    if v == 'u':
        # copy code here from 'g' above
        target_angle = up_angle
        
    
    elif v == 'D':
        
        down_angle = readPot()
        print('Setting grow angle to ',down_angle)
        store_angles(grow_angle,load_angle,up_angle,down_angle)
        v = 'd'   # Stay at this angle until next keypress
        
    if v == 'd':
    # copy code here from 'g' above
        target_angle = down_angle
    # copy code here from 'G' above

#     elif v == 'r':
#         # copy code here from 'g' above
# 
#     elif v == 'R':
#         # copy code here from 'G' above
#        
#  
    elif v == 'n':
        print('motor disabled')
        p.stop()
        GPIO.setup(5, GPIO.LOW) #IN1
        GPIO.setup(6, GPIO.LOW)#IN2
#         break
    elif v == 'o':
        print('motor stopped')
        GPIO.setup(5, GPIO.LOW) #IN1
        GPIO.setup(6, GPIO.LOW)#IN2
        
    elif v == 'm':
       
        print('motor enabled')
        p.start(10)
        GPIO.setup(5, GPIO.LOW) #IN1
        GPIO.setup(6, GPIO.LOW)#IN2
#         break
   
    elif v == 'c':
       
        print('moving forward at 1 angle')
        p.start(10)
        GPIO.setup(5, GPIO.HIGH) #IN1
        GPIO.setup(6, GPIO.LOW)#IN2
        sleep(0.1)
        GPIO.setup(5, GPIO.LOW) #IN1
        GPIO.setup(6, GPIO.LOW)#IN2
#         break
   
    elif v == 'cw':
       
        print('moving backward at 1 angle')
        p.start(10)
        GPIO.setup(5, GPIO.LOW) #IN1
        GPIO.setup(6, GPIO.HIGH)#IN2
        sleep(0.1)
        GPIO.setup(5, GPIO.LOW) #IN1
        GPIO.setup(6, GPIO.LOW)#IN2
#         break
   
    elif v == 'x':
        exit()  #stop the whole program
     
    elif v == 'P':
        print('pot and motor on')
        p.start(15)
        
    elif v == '?':
        
        print("""g = grow, G = set grow angle, l = load, L = set load, u = up,
U = set up angle, d = down, D = set down angle, m = enable motor,
n = disable motor, c = clockwise, cw = counterclockwise, x = Quit""")
        v = ''

    elif v == 'P':
    
        v = input("press options to start: ")          
        sleep(1)
        
    else:
        print("Unknown keypress (",v,"), ignoring...")
        v = ''

    # Now move motor toward target angle
    if readPot() < target_angle:
        print('pot ',readPot(),'< target_angle ',target_angle,', turning CW(?)')
        GPIO.output(5, GPIO.LOW) #has to go backward to 0 angle
        GPIO.output(6, GPIO.HIGH)
#         break
    elif readPot() > target_angle:
        print('pot ',readPot(),'> target_angle ',target_angle,', turning CCW(?)')
#         print('Edna, please check if this is correct code to reverse the motor...')
        GPIO.output(5, GPIO.HIGH) #has to go backward to 0 angle
        GPIO.output(6, GPIO.LOW)
    else:
        print('pot at target_angle = ',grow_angle)
#         print('Edna, please check if this is correct code to stop the motor...')
#         print('...or should we set motor speed to 0 instead?')
        GPIO.output(5, GPIO.LOW) #has to go backward to 0 angle
        GPIO.output(6, GPIO.LOW)
        
        
    # For testing: print dots to show we're running
    if time.time()-last_update > 1.0:
        sys.stdout.write(".") 
        last_update = time.time()
    time.sleep(0.5)
    # end of while True
    
    
    
    