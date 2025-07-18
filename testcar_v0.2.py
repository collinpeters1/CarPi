# CAR position controller for Green MBE.
# Original code: summer 2024 by Edna Vasquez & Mark Wistey.
#from time import sleep
import pyinputplus asf pyip #verify that the input value entered is a number
import board
import spidev
from numpy import interp
import RPi.GPIO as GPIO
import sys
import os
import time
# from threading import Thread
#import threading
#import queue
import termios

# Nonblocking input code from user Luca Invernizzi at
# https://stackoverflow.com/questions/2408560/non-blocking-console-input
# If run under Windows, see that page for modifications using msvcrt.
class NonBlockingConsole(object):

    def __enter__(self):
        # preserve settings of tty before we change it
        self.old_settings = termios.tcgetattr(sys.stdin)   
        tty.setcbreak(sys.stdin.fileno())   # remove line buffering (requires Enter key)
        return self

    def __exit__(self, type, value, traceback):
        # restore settings of tty before we quit
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)


    def get_data(self):   # if a key is pressed, return it, otherwise return False
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return False


def analogInput(channel):
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel) << 4,0])
    data = ((adc[1]&3) <<8) + adc[2]
    return data


def readPot():
    potvalue = analogInput(0)
#     print(potvalue)
    return potvalue
   
# Nonblocking input code from https://stackoverflow.com/questions/2408560/non-blocking-console-input
# def add_input(input_queue):
#     
#     while True:
#         input_queue.put(sys.stdin.read(1))

def save_angles(grow_angle,load_angle,up_angle,down_angle):
    print('Saving angle settings (pot readings) to CARPOS.txt...')
    with open("CARPOS.txt", "w") as fp:
        fp.write("#CARPOS settings version 1.0\n")
        fp.write("#rheed grow load up down (pot readings)\n")
        fp.write(f"{rheed_angle} {grow_angle} {load_angle} {up_angle} {down_angle} {rheed_angle+grow_angle+load_angle+up_angle+down_angle}\n") #crude checksum


# Read the 4 (or more?) angles for CAR positions from file. 
def read_angles():
    try:  # handle some error checking exceptions below
        with open("CARPOS.txt") as fp:
            line = fp.readline()   # read header line
            if not line:
                print("CARPOS.txt is empty, quitting.")
                exit(1)
            if line != "#CARPOS settings version 0.1":
                print("CARPOS.txt has wrong header, quitting.")
                exit(1)
            while line[0] == "#":
                line = fp.readline()   # skip comment lines including header
                if not line:   # Oops, ran out of lines in file
                    print("CARPOS.txt has bad format, quitting.")
                    exit(1)
            try:
                [rheed_angle,grow_angle,load_angle,up_angle,down_angle,chk] = line.split()
                if chk != rheed_angle+grow_angle+load_angle+up_angle+down_angle:
                    print("CARPOS.txt has bad checksum, quitting.")
                    exit(1)
            except ValueError:
                print("CARPOS.txt has bad format, quitting.")
                exit(1)
                
    except IOError as error: 
        print("Unable to read settings from CARPOS.txt, creating...")
            rheed_angle = 15
            grow_angle = 15
            load_angle = 330
            up_angle = 165
            down_angle = 500
            save_angles(rheed_angle,grow_angle,load_angle,up_angle,down_angle)
            
    return check_angles(HARDMIN,HARDMAX,[rheed_angle,grow_angle,load_angle,up_angle,down_angle])


# check_angles(): given a list of angles, reurn 
# Parameters: hardmin = pot reading just before minimum angle hard stop.
# hardmax=max angle hard stop. angles = list of angles to check.
# Returns "angles" list cropped at max/min so none are out of range. 
def check_angles(hardmin,hardmax,angles):
    # Check whether any of our angles are out of range
    for i in range(len(angles)):
        if angles[i] < hardmin:  # below minimum allowed angle
            angles[i] = hardmin
        if angles[i] > hardmax:  # above maximum allowed angle
            angles[i] = hardmax
    return angles


def enable_motor(p):
    global motor_on = True
    GPIO.output(PIN_IN1, GPIO.LOW)  #IN1
    GPIO.output(PIN_IN2, GPIO.LOW)  #IN2
    GPIO.output(PIN_ENABLE, GPIO.HIGH)  #IN2
    p.start(10)



############### Start of main code ##################

# HARDMIN and HARDMAX might be software configurable someday, but for now, hard code them:
HARDMAX = 500  # pot reading just before the max angle hard stop
HARDMIN = 25  # pot reading just before the min angle hard stop

spi = spidev.SpiDev()
spi.open(0,0)

PIN_IN1 = 5
PIN_IN2 = 6
PIN_ENABLE = 12
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_IN1, GPIO.OUT)  #IN1
GPIO.setup(PIN_IN2, GPIO.OUT)  #IN2
GPIO.setup(PIN_ENABLE, GPIO.OUT) #enable
p = GPIO.PWM(PIN_ENABLE, 200)

print("""g = grow, G = set grow angle, l = load, L = set load, u = up,
U = set up angle, d = down, D = set down angle, m = enable motor,
n = disable motor, c = clockwise, cw = counterclockwise, x = Quit""")

# Nonblocking code from https://stackoverflow.com/questions/2408560/non-blocking-console-input
# Get input in a separate thread, since threads don't block each other by default
# input_queue = queue.Queue()
# input_thread = threading.Thread(target=add_input, args=(input_queue,))
# input_thread.daemon = True
# input_thread.start()
# last_update = time.time()

[rheed_angle,grow_angle,load_angle,up_angle,down_angle] = read_angles()   # read angles from file

target_angle = readPot()
global motor_on = True
v = False

print("NOTE: This program does not yet check motor torque (locked rotor)!")
print("NOTE: Also does not yet check if taking too long! (slip/broken shaft)")

with NonBlockingConsole() as nbc:
    while True:
        # Plan:
        # Check (using nonblocking read) if user has pressed a key.
        # If lowercase g/l/u/d, set targe_angle to the corresponding position. 
        # If capital letter G/L/U/D, store the current voltage for corresponding
        # position, both in the variable (grow_angle, etc.) and on disk.
        # At the end of each loop, start motor moving in the correct direction toward target_angle.
        
        # Old way to check for keystrokes: if not input_queue.empty(): v = input_queue.get()

        prevv = v
        v = nbc.get_data()  # nonblocking check for keystroke, or False if none
        
        # Testing whether we can detect a key is being held down. Might need to check
        # for n occurrences within 2 seconds or something like that. 
        if v != False:
            if v == prevv:
                vhold += 1
            else:
                vhold = 0
        if vhold > 50:
            print(f"I see you've been holding {v} for {vhold} counts.")
    
        if v == 'G':
            grow_angle = readPot()
            if grow_angle < HARDMIN or grow_angle > HARDMAX:
                print(f"Current position {grow_angle} out of range {HARDMIN}-{HARDMAX}. Ignoring.")
                v = False
            else:
                print('Setting Grow angle to ',grow_angle)
                save_angles(rheed_angle,grow_angle,load_angle,up_angle,down_angle)
                v = 'g'   # Stay at this angle until next keypress
                # fall through to 'g' section
            
        if v == 'g':
            target_angle = grow_angle
            enable_motor(p)
        
        if v == 'L':
            load_angle = readPot()
            if load_angle < HARDMIN or load_angle > HARDMAX:
                print(f"Current position {load_angle} out of range {HARDMIN}-{HARDMAX}. Ignoring.")
                v = False
            else:
                print('Setting Load angle to ',load_angle)
                save_angles(rheed_angle,grow_angle,load_angle,up_angle,down_angle)
                v = 'l'   # Stay at this angle until next keypress
                # fall through to 'l' section
            
        if v == 'l':
            target_angle = load_angle
            enable_motor(p)
            
        if v == 'U':
            # copy code here from 'G' above
            up_angle = readPot()
            if up_angle < HARDMIN or up_angle > HARDMAX:
                print(f"Current position {up_angle} out of range {HARDMIN}-{HARDMAX}. Ignoring.")
                v = False
            else:
                print('Setting Up angle to ',up_angle)
                save_angles(rheed_angle,grow_angle,load_angle,up_angle,down_angle)
                v = 'u'   # Stay at this angle until next keypress
                # fall through to 'u' section    

        if v == 'u':
            target_angle = up_angle
            enable_motor(p)
            
        if v == 'D':            
            down_angle = readPot()
            if down_angle < HARDMIN or down_angle > HARDMAX:
                print(f"Current position {down_angle} out of range {HARDMIN}-{HARDMAX}. Ignoring.")
                v = False
            else:
                print('Setting Down angle to ',down_angle)
                save_angles(rheed_angle,grow_angle,load_angle,up_angle,down_angle)
                v = 'd'   # Stay at this angle until next keypress
                # fall through to 'd' section    

        if v == 'd':
            target_angle = down_angle
            enable_motor(p)
    
        if v == 'R':            
            rheed_angle = readPot()
            if rheed_angle < HARDMIN or rheed_angle > HARDMAX:
                print(f"Current position {rheed_angle} out of range {HARDMIN}-{HARDMAX}. Ignoring.")
                v = False
            else:
                print('Setting RHEED angle to ',rheed_angle)
                save_angles(rheed_angle,grow_angle,load_angle,up_angle,down_angle)
                v = 'f'   # Stay at this angle until next keypress
                # fall through to 'r' section    

        if v == 'r':
            target_angle = rheed_angle
            enable_motor(p)
            
        if v == 'n':
            print('Disabling motor controller...')
            motor_on = False   # just for keeping track of if we think motor's enabled
            GPIO.output(PIN_ENABLE, GPIO.LOW)  # disable motor controller
            # These alone don't work because they get set again at end of loop:
            GPIO.output(PIN_IN1, GPIO.LOW) #IN1
            GPIO.output(PIN_IN2, GPIO.LOW)#IN2
            p.stop()
            v = False

        elif v == 'o':
            motor_on = False   # just for keeping track if we think motor's enabled
            print('Should stop motor here...')
            GPIO.output(PIN_IN1, GPIO.LOW) #IN1
            GPIO.output(PIN_IN2, GPIO.LOW)#IN2
            v = False
            
        elif v == 'm':
           
            print('Should enable motor board here...')
            motor_on = True   # for keeping track if we think motor's enabled
            enable_motor(p)
            v = False
       
        elif v == 'c':
            target_angle += 1  # move 1 step ahead
            v = False   # do nothing more than this
        elif v == 'C':
            target_angle += 10  # move 10 steps ahead
            v = False
        elif v == 'v':
            target_angle -= 1  # move 1 step back
            v = False
        elif v == 'V':
            target_angle -= 10  # move 10 steps back
            v = False
     
        elif v == 'x' or v == '\x1b':  # x1b is ESC
            print("Quitting...")
            break  # Gracefully exit the loop & program
         
        elif v == 'P':
            print('pot and motor on')
            p.start(15)
            
        elif v == '?':
            
            print("""g = grow, G = set grow angle, l = load, L = set load, u = up,
    U = set up angle, d = down, D = set down angle, m = enable motor,
    n = disable motor, c = clockwise, cw = counterclockwise, x = Quit""")
            v = False
    
        elif v == 'P':
        
            v = input("Type options followed by Enter: ")          
            #time.sleep(1)
            
        else:
            print("Unknown keypress (",v,"), ignoring...")
            v = False
    
        # Make sure our target angle is within allowed range
        target_angle = check_angles(HARDMIN,HARDMAX,[target_angle])[0]
        # If current position is out of range, disable motor
        pos = readPot()
        if pos < HARDMIN or pos > HARDMAX:
            motor_on = False
            print("Position {pos} out of range {HARDMIN}-{HARDMAX}! Disabling motor.")
            GPIO.output(PIN_ENABLE, GPIO.LOW)  # disable motor controller
            # These alone don't work because they get set again at end of loop, below:
            GPIO.output(PIN_IN1, GPIO.LOW) 
            GPIO.output(PIN_IN2, GPIO.LOW) 
            p.stop()
            
        elif motor_on == False:
            print(f'pot ={pos:4}, target_angle ={target_angle:4}. MOTOR DISABLED\r',end="", flush=True)
        # Motor is enabled, so move it toward target angle 
        elif pos < target_angle:
            print(f'pot ={pos:4}, target_angle ={target_angle:4}, turning CW(?) \r',end="", flush=True)
            GPIO.output(PIN_IN1, GPIO.LOW) #has to go forward(?) toward target angle
            GPIO.output(PIN_IN2, GPIO.HIGH)
    
        elif pos > target_angle:
            print(f'pot ={pos:4}, target_angle ={target_angle:4}, turning CCW(?)\r',end="", flush=True)
            # print('Edna, please check if this is correct code to reverse the motor...')
            GPIO.output(PIN_IN1, GPIO.HIGH) #has to go backward(?) toward 0 angle
            GPIO.output(PIN_IN2, GPIO.LOW)
        else:
            print(f'pot ={pos:4}, target_angle ={target_angle:4}                \r',end="", flush=True)
            # print('Edna, please check if this is correct code to stop the motor...')
            # print('...or should we set motor speed to 0 instead?')
            GPIO.output(PIN_IN1, GPIO.LOW)  # Freeze motor: set IN1=IN2.
            GPIO.output(PIN_IN2, GPIO.LOW)
            p.stop()
            
            
        # For testing: print dots to show we're running
        if time.time()-last_update > 1.0:
            sys.stdout.write(".")
            sys.stdout.flush() 
            last_update = time.time()
        time.sleep(0.1)
        
        # end of while True
    #end of with NonBlockingConsole() as nbc

print("Have a nice day!")
print("To restart: ", os.path.abspath(__file__))
print(" or ",os.path.dirname(sys.argv[0]))
