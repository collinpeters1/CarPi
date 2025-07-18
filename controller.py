#!/usr/bin/python3
# Touchscreen controller for Edwards turbo pump for gas cabinet.
# Original code by Edna Vasquez & Ahmed Ogunjobi, 2022-2023.
#  Molly internet output added 9/2023 MAW.
#  More robust to errors in data stream: less likely to crash. 12/2023 MAW
#  Fixed Start/Stop so it's active immediately, not after spindown. 12/2023 MAW.
# Wish/bug list:
#  Protect against 2 copies running simultaneously. Good test for robustness too
#  Archive a copy of current program if not already done.
#  Bigger fonts.
#  Status region
#  Menu to change vent options, etc. 
#  More data integrity testing: wrap stuff in try's.
#  Return -999 or similar if pump has timed out: data is stale. 
#  Show pump warnings prominently, like oil due. See manual 5.5.1. 
#  Have start/stop button show fill based on pump state.
#  Must hold buttons for 2 seconds to turn pump on/off, or exit.
#  Maybe Molly control, not just Molly reading.
# Notes: Running, status=000502BC. after clicking Stop, status is 028700AC. 
#
import time
import serial
import kivy
import os
import sys
import socket
import select
import signal
import datetime
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import (NumericProperty, StringProperty, ReferenceListProperty, ObjectProperty, ListProperty)
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from functools import partial
from kivy.vector import Vector
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import mainthread
import threading
from kivy.uix.pagelayout import PageLayout
from kivy.uix.button import Button
import numpy
from kivy.uix.label import Label
from kivy.core.text.markup import MarkupLabel


LOGNAME="/dev/null"  # to prevent excess log growth
#LOGNAME="/var/log/turbo_ctlr.log"
#WINDOW_MIN_WIDTH = 320
#WINDOW_MIN_HEIGHT = 240

Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'top', '0')
Config.set('graphics', 'left', '0')
Config.set('graphics', 'position','custom')
# Window.fullscreen = 'auto'
#Window.fullscreen = False

Window.clearcolor = (0, 0, 0, 0)

verbose = 1   # increase it to be more verbose in output
Clock.max_iteration = 20

# The USB-RS485 serial port adapter connected to the turbo:
ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 9600
ser.bytesize = serial.EIGHTBITS #number of bits per bytes
ser.parity = serial.PARITY_NONE #set parity check: no parity
ser.stopbits = serial.STOPBITS_ONE #number of stop bits
ser.timeout = .5            #non-block read
ser.xonxoff = False     #disable software flow control
ser.rtscts = False     #disable hardware (RTS/CTS) flow control
ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
ser.writeTimeout = .5     #timeout for write

#TCP_IP = '127.0.0.1'
TCP_IP = '192.168.8.201'
TCP_PORT = 1200
BUFFER_SIZE = 1024
param = []

def cleanread(ser):
    try:
        return(strclean(ser.readline()))
    except serial.serialutil.SerialException as msg:
        return(b'')

def strclean(mystr):  # Strip \r & \r & any junk after them
    mystr = mystr.replace(b'\n', b'\r')
    mystr = mystr.split(b'\r',1)[0]
    return(mystr)

global statmsg   # Multiline string to display with recent debug/status msgs
global statlist  # Recent status messages
statlist=['1','2','3','4','5','6','7','8','9','10','11','12','13','14']   # list length=how many recent lines to keep
statmsg = ' '.join(statlist)  # join them with a space between

def addlog(mymsg, verblevel=2):  # add string to current status log, on screen or stdout
    global logfile
    if verblevel <= verbose+1:   # be extra verbose to terminal
        print(mymsg)   # only visible if running from terminal window
    if verblevel <= verbose:    # log is somewhat less verbose
        statlist.pop(0)
        statlist.append(mymsg)
        statmsg = '\n'.join(statlist)
        try:
            with open(LOGNAME,"a") as logfile:
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+mymsg, file=logfile)
        except IOError:
            print("Unable to write log file "+LOGNAME)
            statlist.pop(0)
            statlist.append("Unable to write log file "+LOGNAME)
    

# Be prepared to gracefully quit. Based on
# https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        addlog("exiting gracefully as requested...\n",verblevel=1)
        self.kill_now = True

addlog ('Listening for Molly client...')
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.settimeout(2)
#server.bind((TCP_IP,TCP_PORT))
try:
    server.bind(('',TCP_PORT))
    server.listen(1)
except socket.error as msg:
    addlog("Caught port open exception socket.error, %s " % msg, verblevel=1)
rxset = [server]
txset = []
#if verbose>1: print("rxset=",rxset,", server=",server)
addlog("rxset="+repr(rxset),verblevel=1)
addlog(", server="+repr(server),verblevel=1)

Builder.load_string(
"""
    
<TextInput>
    size_hint: (0.5, 0.2)

<MainLayout>

    FloatLayout:
        orientation: "horizontal"
        size: root.width, root.height
        
        ResizableLabel:
            id: RPM
            text: "RPM"
            pos_hint: {"x":.08, "top": 0.97}
            size_hint: .1, .1
            font_size: 50
            canvas.before:
                Color:
                    rgba: 0,0,0,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            color: (1, 1, 1, 1)
            background_color: (0, 0, 0, 1)
        
        ResizableButton:
            id: RPM_btn
            text: "START/STOP"
            pos_hint: {"x":.02, "top": 0.98}
            size_hint: .3, .3
            font_size: 35
            #color: (1, 1, 1, 1)
            # Draw grey border around button:
            canvas.before:
                Color:
                    rgba: 0.5,0.5,0.5,1
                Line:
                    width: 2
                    rectangle: self.x, self.y, self.width, self.height
            on_press: root.startstop_press()
            background_color: (0, 1, 0, 0)
        
        ResizableLabel:
            id: Watts
            text: "Watts"
            font_size: 50
            size_hint: .15, .15
            pos_hint: {"x":0.35, "top": 1}
            canvas.before:
                Color:
                    rgba: 0,0,0,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            color: (1, 1, 1, 1)
            background_color: (0, 0, 0, 0)

        ResizableLabel:
            id: MTemp
            text: "MTemp"
            font_size: 50
            size_hint: .15, .15
            pos_hint: {"x":0.55, "top": 1}
            canvas.before:
                Color:
                    rgba: 0,0,0,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            color: (1, 1, 1, 1)
            background_color: (0, 0, 0, 0)

        ResizableLabel:
            id: Oil
            text: "Oil Life"
            pos_hint: {"x":0.75, "y": .85}
            font_size: 50
            size_hint: .15, .15
            canvas.before:
                Color:
                    rgba: 0,0,0,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            color: (1, 1, 1, 1)
            background_color: (0, 0, 0, 0)

        ResizableButton:
            id: Back
            text: "Back"
            #Possible hints: "x", "y", "top", "bottom", "left", "right"
            pos_hint: {"x":0, "y":.3}
            size_hint: .25, .25
            font_size: 35
            #on_press: self.background_color = (1.0, 1.0, 0.0, 1.0)
            #on_release: self.background_color = (1.0, 1.0, 1.0, 1.0)
            canvas.before:
                Color:
                    rgba: 0.5,0.5,0.5,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            on_press: root.back()

        ResizableButton:
            id: Up
            text: "Up"
            pos_hint: {"x":.25, "y":.3}
            size_hint: .23, .25
            font_size: 35
            canvas.before:
                Color:
                    rgba: 0.5,0.5,0.5,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            on_press: root.up()
            on_release: root.enter()


        ResizableButton:
            id: Enter
            text: "Enter"
            pos_hint: {"x":0}
            size_hint: .25, .25
            font_size: 35
            canvas.before:
                Color:
                    rgba: 0.5,0.5,0.5,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            on_press: root.enter()

        ResizableButton:
            id: Down
            text: "Down"
            font_size: 35
            pos_hint: {"x":.25}
            size_hint: .23, .25
            canvas.before:
                Color:
                    rgba: 0.5,0.5,0.5,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            on_press: root.down()
            on_release: root.enter()

        ResizableLabel:
            id: Status
            text: "Status Bits:"
            pos_hint: {"x":0.51, "y": 0.60}
            size_hint: .2,.2
            font_size: 40
            canvas.before:
                Color:
                    rgba: 0,0,0,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            #color: (0, 1, 1, 1)
            #background_color: (0, 0, 0, 0)

        ResizableLabel:
            id: Sent
            text: "Sent:"
            pos_hint: {"x":0.5, "y": .45}
            size_hint: .05, .05
            font_size: 50
            canvas.before:
                Color:
                    rgba: 0,0,0,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            color: (1, 1, 1, 1)
            background_color: (0, 0, 0, 0)

        ResizableLabel:
            id: Received
            text: "Received:"
            pos_hint: {"x":0.51, "y": .30}
            size_hint: 0.15, 0.15
            font_size: 35
            canvas.before:
                Color:
                    rgba: 0,0,0,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            color: (1, 1, 1, 1)
            background_color: (0, 0, 0, 0)

#         ResizableLabel:
#             id: Fan
#             text: "Fan:"
#             font_size: '35sp'
#             size_hint: 0.1, 0.1
#             pos_hint: {"x":0.52}
#             canvas.before:
#                 Color:
#                     rgba: 0.5,0.5,0.5,1
#                 Line:
#                     width: 2
#                 Rectangle:
#                     pos:self.pos
#                     size:self.size
#             color: (1, 1, 1, 1)
#             background_color: (0, 0, 0, 0)
# 
#         Label:
#             text: str(root.value)
#             pos_hint: {'x': .73, 'y': 0.53}
#             size_hint: 0.30, 0.1
#             color: (1, 1, 1, 1)

        ResizableButton:
            id: Fan_btn
            text: "Fan"
            font_size: 50
            size_hint: 0.2, 0.25
            pos_hint: {"x":.52, "bottom": .5}
            canvas.before:
                Color:
                    rgba: 0,0,0,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
           
            on_press: root.fan_press()
            #background_color: (0, 0.5, 0, 0)

        ResizableButton:
            text: "Exit"
            pos_hint: {'x': .75, 'y': 0}
            size_hint: .25, .25
            font_size: 50
            canvas.before:
                Color:
                    rgba: 0.5,0.5,0.5,1
                Line:
                    width: 2
                Rectangle:
                    pos:self.pos
                    size:self.size
            on_press: root.exit_request()


""")


global request
global response

class MainLayout(Widget):
    font_scaling = NumericProperty()
    value = NumericProperty(0)

    # This doesn't seem to do anything, 12/15/2023 MAW:
    #def on_size(self,*args):
    #    self.font_scaling = min(Window.width/WINDOW_MIN_WIDTH, Window.height/WINDOW_MIN_HEIGHT)
    
    def up(self):
        self.event = Clock.schedule_once(lambda dt: setattr(self, 'value', self.value+1), .5)
        self.value += 1
        if self.value > 1:
            addlog("up button still undefined",verblevel=3)
            self.event.cancel()

    def down(self):
        self.event = Clock.schedule_once(lambda dt: setattr(self, 'value', self.value-1), .5)
        self.value -= 1
        if self.value < 0:
            addlog("down button still undefined",verblevel=3)
            self.event.cancel()

    def enter(self):
        self.event.cancel()

    def exit_request(self):
        exit()

    def startstop_press(self):
        global RPM1
        global stat1
        addlog("Requesting ?V852 for Start/Stop press...", verblevel=3)
        ser.write(b"?V852\r")
        time.sleep(.03)
        RPM1 = cleanread(ser)
        if not RPM1.startswith(b"=V852 "):
            ser.write(b"?V852\r")   # try one more time
            time.sleep(.03)
            RPM1 = cleanread(ser)
            if not RPM1.startswith(b"=V852 "):   # still not responding
                addlog("Start/Stop pressed but pump didn't respond to status query")
                return(-1)
        RPM1,stat1 = RPM1.decode().strip().split(';')
        stat1 = int(stat1, 16)
        addlog("Requested ?V852 for RPM... RPM:stat1="+repr(stat1),verblevel=2)
        if stat1 & (1 << 4):
            if stat1 & (1 << 2):
                if verbose > 0: addlog("Pump thinks it's at normal speed.")
            addlog('Pump currently running. Stopping it...',verblevel=1)
            #RPM_btn.background_color = (1,0,0,1)
            #addlog("RPM_btn.x="+repr(root.ids.RPM_btn.x),verblevel=3)
            ser.write(b"!C852 0\r")
            time.sleep(.03)
            s = cleanread(ser)
            addlog("Write Data: !C852 0, response:"+repr(s),verblevel=2)
        else:
            addlog("Pump decelerating or not running. Starting it...",verblevel=1)
            ser.write(b"!C852 1\r")
            time.sleep(.03)
            s = cleanread(ser)
            addlog("Write Data: !C852 1, response: "+repr(s),verblevel=2)

    def fan_press(self):
        #global RPM1
        #global stat1
        ser.write(b"?S853\r")
        time.sleep(.03)
        fanvent1 = cleanread(ser)
        addlog("Requested ?S853 for fan/vent...resp="+repr(fanvent1),verblevel=2)
        if not fanvent1.startswith(b"=S853 "):   # Pump unreadable
            fanvent1 = "Unknown"
        else:   # Got a good (?) response from pump
            fanvent1 = fanvent1.split(b' ')[1]   # get 2nd word
            if fanvent1 == '8':
                addlog('Fan currently on. Shutting it off.',verblevel=1)
                #Fan_btn.background_color = (1,0,0,1)
                ser.write(b"!S853 0\r")
                time.sleep(.03)
                s = cleanread(ser)
                addlog("Write Data: !S853 0, response:"+repr(s),verblevel=3)
            else:
                addlog("Fan currently off....starting it.",verblevel=1)
                ser.write(b"!S853 8\r")
                time.sleep(.03)
                s = cleanread(ser)
                addlog("Write Data: !S853 8, response: "+repr(s),verblevel=3)


    # def updateStatus(self, *args):
    #     ser.write(b"?V881\r")
    #     time.sleep(.05)
    #     global status
    #     status = strclean(ser.readline())
    #     print("status Write Data: ?V881; Response: ",status)
    #     #Clock.schedule_once(self.updateOilLife, 1)

    # def updateOilLife(self, *args):
    #     ser.write(b"?V886\r")
    #     print("Write Data: ?V886\n")
    #     time.sleep(.05)
    #     global oilLife
    #     oilLife = strclean(ser.readline())
    #     #Clock.schedule_once(self.updateLabels, 1)


class controllerApp(App):
    global button_pressed
    button_pressed = False
    status  = None

    def build(self):
        return MainLayout()

    def on_start(self, *args):
        Clock.schedule_once(self.updateLabels)

    def updateLabels(self, *args):
        # Print by binary nibbles, from stackoverflow.com/questions/50736143...
        def split_nibbles(x):
            while x:
                yield bin(x % 16)[2:].zfill(4)   # split into groups of 4 bits
                x >>= 4
        def by_nibbles(x):
            return "  ".join(split_nibbles(x))    # join with space between
    
        ser.write(b"?V852\r")
        #if verbose > 1: print("RPM request: ?V852\\r ...      ", end="")
        time.sleep(.03)
        RPM = cleanread(ser)
        addlog("RPM request: ?V852\\r ...      Response: "+repr(RPM))
        if RPM.startswith(b"=V852 "):
            RPM,stat1 = RPM.decode().strip().split(';')
            # Should really do more data validation here.
            RPM = RPM.split(' ')[1]   # get 2nd word
            stat1 = int(stat1, 16)    # convert hexadecimal string to integer
            if stat1 & (1 << 2):
                self.root.ids.RPM_btn.background_color = (0,1,0,1)
            elif stat1 & (1 << 4):
                self.root.ids.RPM_btn.background_color = (1,1,0,1)
            else:
                self.root.ids.RPM_btn.background_color = (0.5,0,0,1)
            if stat1 & (1 << 3):
                self.root.ids.Fan_btn.text = "Fan/Vent On (?)"
            else:
                self.root.ids.Fan_btn.text = "Fan/Vent Off (?)"
        else:
            #RPM = numpy.nan
            RPM = "NaN"
            stat1 = "NaN"
            self.root.ids.Fan_btn.text = "Fan \nUnknown"
        
        #if verbose > 1:  print("V/A/P Request: ?V860\\r ...    ", end="")
        ser.write(b"?V860\r")
        time.sleep(.03)
        s = cleanread(ser)
        if s.startswith(b"=V860 "):
            addlog("V/A/P Request: ?V860\\r ...    Response: " + str(s))
            t = s.decode().strip().split(';')
            Volts,Amps,Watts = s.decode().strip().split(';')
            s1,Volts = Volts.split(' ')
            Volts = float(Volts) * 0.1
            Volts = round(Volts, 1)
            Amps = float(Amps) * 0.1
            Amps = round(Amps, 1)
            Watts = float(Watts) * 0.1
            Watts = round(Watts, 1)
            #if verbose > 1:  print(Volts,Amps,Watts)
        else:
            #if verbose > 0: print("V/A/P response error.")
            addlog("V/A/P response error.",verblevel=1)
            Volts = -998
            Amps = -998
            Watts = -998


        #global Temp
        #if verbose > 1: print("T request: ?V859\\r ...        ", end="")
        ser.write(b"?V859\r")
        time.sleep(.03)
        s1 = cleanread(ser)
        if s1.startswith(b"=V859 "):
            sMTemp,sCTemp = s1.decode().strip().split(';')
            s2,sMTemp = sMTemp.split(' ')
            MTemp = round(float(sMTemp) ,1)
            CTemp = round(float(sCTemp) ,1)
            addlog(f"T request: ?V859\\r ...        Response: {s1} (Mot={MTemp}C,Ctlr={CTemp}C)")
        else:
            #if verbose>1: print("Temperature response error.")
            addlog("Temperature response error.",verblevel=1)
            MTemp = -998
            CTemp = -998

        #global oilLife, runOil, service_due
        ser.write(b"?V886\r")
        #if verbose>1: print("Oil life request: ?V886\\r ... ", end="")
        time.sleep(.03)
        oilLife = cleanread(ser)
        if oilLife.startswith(b"=V886 "):
            addlog("Oil life request: ?V886\\r ... Response: "+repr(oilLife))
            f = oilLife.decode().strip().split(':')
            runOil,service_due = oilLife.decode().strip().split(';')
            s1,runOil = runOil.split(' ')
            try:
                runOil = round(float(runOil), 1)
                service_due = round(float(service_due), 1)
            except ValueError:
                runOil=-997
                service_due=-997
            addlog(f"runOil={runOil}, service_due={service_due}",verblevel=2)
        else:
            #if verbose>1: print("Oil Life response error.")
            addlog("Oil Life response error.",verblevel=2)
            runOil = -998
            service_due = -998

        #if verbose>1: print("type of RPM is...",type(RPM))
        #if verbose>1: print("RPM="+repr(RPM)+"....\n")
        #if verbose>1: print("float(RPM)="+repr(float(RPM)))
        #if verbose>1: print("numpy.isnan(float(RPM))=",numpy.isnan(float(RPM)))
        #addlog("type of RPM is..."+repr(type(RPM)),verblevel=3)
        addlog("RPM="+repr(RPM)+"....",verblevel=2)
        #addlog("float(RPM)="+repr(float(RPM)),verblevel=3)
        addlog("numpy.isnan(float(RPM))="+repr(numpy.isnan(float(RPM))),verblevel=3)
        if numpy.isnan(float(RPM)):
            #if verbose>2: print("at 1...\n")
            addlog("at 1...",verblevel=3)
            self.root.ids.RPM.text = "RPM"+ "\n" + "error"
            self.root.ids.Watts.text = "Watts"+ "\n" + "error"
            self.root.ids.MTemp.text = "MotorTemp"+ "\n" + "error"
            self.root.ids.Oil.text = "\n"+"Oil Life"+ "\n" + "error"
            self.root.ids.Status.text = "Status Bits: \n        IMWT UVCP HBRG VNSF\n(unknown)"
        else:
            #if verbose>2: print("at 2...\n")
            addlog("at 2...",verblevel=3)
            self.root.ids.RPM.text = str(int(float(RPM)/9.99)) + "% speed" + "\n"
            self.root.ids.Watts.text = "Watts" + "\n" + str(Watts)
            self.root.ids.MTemp.text = "MotorTemp" + "\n" + str(MTemp)
            #self.root.ids.Status.text = "Status: " + f"{int(stat1):b}"
            self.root.ids.Status.text = "Status Bits: \n     IMWT UVCP HBRG VNSF\n" + by_nibbles(stat1)
            self.root.ids.Oil.text = "Oil Life" + "\n" + str(runOil) + " hr" + "\nDue:" + str(service_due) + " hr"
            self.root.ids.Received.text = "\n".join(statlist)
            #print("statmsg="+statmsg)
            print("statlist[0]="+statlist[0]+"\n")
            
            fakepow = 0
            fakerpm = 1000
            #if verbose>2: print("at 3...\n")
            addlog("at 3...",verblevel=3)

            killer = GracefulKiller()  # to watch for QUIT/control-C signals
            #if verbose>2: print("at 3b, killer=",killer,"\n")
            #addlog("at 3b, killer="+repr(killer)+"...\n",verblevel=3)
            #while not killer.kill_now: # True if user pressed control-C or Stop
            rxfds, txfds, exfds = select.select(rxset, txset, rxset, 0)
            #if verbose>2: print("at 4, rxfds=",rxfds,"...\n")
            addlog("at 4, rxfds="+repr(rxfds)+"...",verblevel=4)

            for sock in rxfds:
                if sock is server:
                    addlog("Trying server.accept...",verblevel=2)
                    try:
                        conn, addr = server.accept()
                    except socket.error as msg:
                        addlog("Caught exception socket.error, %s " % msg, verblevel=1)
                        addlog("Error opening TCP socket. Is port in use? Try again in a minute.", verblevel=0)
                        continue
                        #exit(1)
                    conn.setblocking(0)
                    rxset.append(conn)
                    addlog('Connection from address:'+repr(addr),verblevel=1)
                else:
                    try:
                        data = sock.recv(BUFFER_SIZE)  # get Molly's request
                        if data.count(b'\r') > 1:       # Multiple requests?
                            data = data.split(b'\r')[-2]+'\r'  # Ignore earlier stale requests 
                        if data == b"QUIT" :   # not used as of 12/2023
                            addlog("Received ether request to quit controller (QUIT).",verblevel=1)
                            addlog("param=" + str('\n'.join(param)))
                            param = []
                            rxset.remove(sock)
                            sock.close()
                        elif data == b'?V852\r':
                            #fakerpm = fakerpm + 1
                            #fakersp = "{}\r".format(fakerpm)
                            #if verbose>1: print(f"Sending response: {fakersp}\n")
                            rsp = f"=V852 {int(RPM):d};{stat1:-.8x}\r"
                            #if verbose>1: print(f"Sending response: {rsp}\n")
                            addlog(f"...eth: Molly sent ?V852\\r for RPM... replying {rsp}\n",verblevel=2)
                            sock.send(rsp.encode())
                            #print(f"Sending fake response...")
                            #sock.send(b"123\r")
                        elif data == b'?V859\r':
                            #if verbose>1: print("...eth: received ?V859 for temps\\r...")
                            #fakepow = fakepow + 1
                            #fakersp = "{}\r".format(fakepow)
                            rsp = f"=V859 {MTemp*10:d};{CTemp*10:d}\r"
                            #if verbose>1: print(f"Sending response: {rsp}\n")
                            addlog(f"...eth: Molly sent ?V859 for temps\\r, replying: {rsp}",verblevel=2)
                            sock.send(rsp.encode())
                        elif data == b'?V860\r':
                            #if verbose>1: print("...eth: received ?V860\\r for V/A/W...")
                            #fakepow = fakepow + 1
                            #fakersp = "{}\r".format(fakepow)
                            rsp = "=V860 {};{};{}\r".format(Volts*10,Amps*10,Watts*10)
                            addlog(f"...eth: Molly sent ?V860\\r for V/A/W, replying {rsp}\n",verblevel=2)
                            sock.send(rsp.encode())
                        else:
                            #if verbose>1: print(f"eth: Unknown request '{data}'\n...Sending fake response 9876...\n")
                            addlog(f"eth: Unknown Molly request '{data}'\n...Sending fake response 9876...\n",verblevel=2)
                            sock.send(b"9876\r")
                    except:
                        addlog("Connection closed by remote end",verblevel=1)
                        param = []
                        rxset.remove(sock)
                        sock.close()
            
        Clock.schedule_once(self.updateLabels, 0.05)
        
 
class ResizableLabel(Label):
    markup = True
    def on_text(self, *args, **kwargs):
        self.adjust_font_size()
        
    def on_size(self, *args, **kwargs):
        self.adjust_font_size()
        
    def adjust_font_size(self):
        font_size = self.font_size
        while True:
            lbl = MarkupLabel(font_name = self.font_name, font_size = font_size, text = self.text)
            lbl.refresh()
            lbl_available_height = self.height - self.padding_y * 2
            lbl_available_width = self.width - self.padding_x * 2
            if font_size > lbl_available_height:
                font_size = lbl_available_height
            elif lbl.content_width > lbl_available_width or \
                 lbl.content_height > lbl_available_height:
                 font_size *= 0.95
            else:
                break
        
        while True:
            lbl = MarkupLabel(font_name = self.font_name, font_size = font_size, text = self.text)
            lbl.refresh()
            if lbl.content_width * 1.1 < lbl_available_height and \
                lbl.content_height * 1.1 < lbl_available_height:
                font_size *= 1.05
                
            else:
                break
      
                
        self.font_size = font_size
        
class ResizableButton(Button):
    markup = True
    def on_text(self, *args, **kwargs):
        self.adjust_font_size()
        
    def on_size(self, *args, **kwargs):
        self.adjust_font_size()
        
    def adjust_font_size(self):
        font_size = self.font_size
        while True:
            lbl = MarkupLabel(font_name = self.font_name, font_size = font_size, text = self.text)
            lbl.refresh()
            lbl_available_height = self.height - self.padding_y * 2
            lbl_available_width = self.width - self.padding_x * 2
            if font_size > lbl_available_height:
                font_size = lbl_available_height
            elif lbl.content_width > lbl_available_width or \
                 lbl.content_height > lbl_available_height:
                 font_size *= 0.95
            else:
                break
        
        while True:
            lbl = MarkupLabel(font_name = self.font_name, font_size = font_size, text = self.text)
            lbl.refresh()
            if lbl.content_width * 1.1 < lbl_available_height and \
                lbl.content_height * 1.1 < lbl_available_height:
                font_size *= 1.05
                
            else:
                break

                
                
        self.font_size = font_size         



if __name__ == "__main__":
    try:
        ser.open()
    except Exception as e:
        addlog("Error opening serial port "+repr(ser.port)+"! Exiting... ",verblevel=1)
        exit()

    if ser.isOpen():
        try:
            ser.flushInput()
            ser.flushOutput()
        except Exception as e:
            addlog("Serial port error: " + str(e),verblevel=1)
    else:
        addlog("Error in serial comms to pump",verblevel=2)
    
    controllerApp().run()   # Run the GUI



