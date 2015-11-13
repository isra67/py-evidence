#!/bin/python

'''
Sources:
  https://github.com/kivy/kivy/wiki/Working-with-Python-threads-inside-a-Kivy-application
'''

from math import cos, sin, pi
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition
from kivy.uix.widget import Widget

import datetime
import hashlib
import json
import socket
import sys
import urllib
import threading


Builder.load_file("main1.kv")


# Clock class - digital
class DigiClockWidget(FloatLayout):
    pass

class DigiClock(Label):
    def __init__(self, **kwargs):
        super(DigiClock, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1)
        
    def update(self, *args):
        self.text = datetime.datetime.now().strftime("%d.%m.%Y     %H:%M:%S")


# Clock class - analog
class MyClockWidget(FloatLayout):
    pass

class Ticks(Widget):
    def __init__(self, **kwargs):
        super(Ticks, self).__init__(**kwargs)
        self.bind(pos=self.update_clock)
        self.bind(size=self.update_clock)
        Clock.schedule_interval(self.update_clock, 1)

    def update_clock(self, *args):
        self.canvas.clear()
        with self.canvas:
            time = datetime.datetime.now()
            Color(0.6, 0.6, 0.9)
            Line(points=[self.center_x, self.center_y, self.center_x+0.7*self.r*sin(pi/30*time.second), self.center_y+0.7*self.r*cos(pi/30*time.second)], width=1, cap="round")
            Color(0.5, 0.5, 0.8)
            Line(points=[self.center_x, self.center_y, self.center_x+0.6*self.r*sin(pi/30*time.minute), self.center_y+0.6*self.r*cos(pi/30*time.minute)], width=2, cap="round")
            Color(0.4, 0.4, 0.7)
            th = time.hour*60 + time.minute
            Line(points=[self.center_x, self.center_y, self.center_x+0.5*self.r*sin(pi/360*th), self.center_y+0.5*self.r*cos(pi/360*th)], width=3, cap="round")


#App
class Evidence(FloatLayout):
    DEVICE = '6'          # cislo zariadenia
    EVIDENCE_TYPE = '15'  # typ udalosti dochadzky
    ACCESS_TYPE = '2'     # typ vzniku udalosti
    EVIDENCE_SERVER = '192.168.1.47:8080'
    EVIDENCE_PATH = '/inoteska/setdata.php?'

    stop = threading.Event()
    rfidKeyCode = ''
    
    def __init__(self, **kwargs):
        print('Ini')
        super(Evidence, self).__init__(**kwargs)
        self.scrmngr = self.ids._screen_manager        
        #self.read_server_status(self.EVIDENCE_SERVER)
        
        # Start a new thread with an infinite loop and stop the current one
        d = threading.Thread(target=self.infinite_loop)
        d.setDaemon(True)
        d.start()

    def infinite_loop(self):
        self.sockserv_init()
        while True:
            if self.stop.is_set():
                # Stop running this thread so the main Python process can exit
                return
                
            #wait to accept a connection - blocking call
            conn, addr = self.s.accept()
            print('Connected with ' + addr[0] + ':' + str(addr[1]))
             
            #start new thread takes 1st argument as a function name to be run, 
            # second is the tuple of arguments to the function
            threading.Thread(target=self.clientthread, args=(conn,)).start()
         
        self.s.close()

    def sockserv_init(self):    
        HOST = ''   # Symbolic name meaning all available interfaces
        PORT = 8888 # Arbitrary non-privileged port
         
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #print('Socket created')
         
        #Bind socket to local host and port
        try:
            self.s.bind((HOST, PORT))
        except socket.error as msg:
            print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            sys.exit()
             
        #print('Socket bind complete')
         
        #Start listening on socket
        self.s.listen(10)
        print('Socket now listening')
            
    #Function for handling connections. This will be used to create threads
    def clientthread(self, conn):
        msg = '' 
        #infinite loop so that function do not terminate and thread do not end
        while not self.stop.is_set():             
            #Receiving from client
            data = conn.recv(512)

            if not data:
                print('NO DATA!!!')
                break
         
            msg += data.decode("utf-8")
            print('MSG: ' + msg)
            if '"RFID":' in msg:
                if self.scrmngr.current == 'events':
                    conn.sendall(b'RFID busy')
                else:
                    conn.sendall(b'RFID OK')
                    self.swap_screen('events')
                    #spracovanie RFID kodu:
                    d = json.loads(msg)
                    for key, value in d.items():
                        print(key, ': ', value)
                        if key=='RFID': self.rfidKeyCode = value                 
                break
         
        print('Out of client loop! ' + msg)
        #came out of loop
        conn.close()
        
    @mainthread
    def swap_screen(self, scr):
        self.scrmngr.current = scr
        
    def startScreenTiming(self):
        #print('Enter')
        Clock.schedule_once(self.return2clock, 5)

    def return2clock(self, *args):
        print('ret2clock')
        self.scrmngr.current = 'clock'

    def finishScreenTiming(self):
        #print('Leave')
        Clock.unschedule(self.return2clock)

    def saveEvidenceEvent(self, event, rfid):
        xdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        a = self.rfidKeyCode + xdate 
        b = hashlib.md5(b'inoteska').hexdigest() 
        c = b + a

        xhash = hashlib.md5(c.encode("utf-8")).hexdigest()

        par = 't=boarddata'
        par += '&c='+rfid
        par += '&d='+urllib.parse.quote(xdate, safe='')
        par += '&ty='+event #self.EVIDENCE_TYPE
        par += '&ac='+self.ACCESS_TYPE
        par += '&dev='+self.DEVICE
        par += '&x='+urllib.parse.quote(xhash, safe='')

        print('UrlParam: ' + par)
        url = 'http://{0}{1}{2}'.format(self.EVIDENCE_SERVER, self.EVIDENCE_PATH, par) 
        req = UrlRequest(url, self.decode_server_response)        
        
    def processEvent(self, event):
        if self.rfidKeyCode == '':
            print('Lost event - no RFID key')
        else:
            print('Event: ' + event + ' Code: ' + self.rfidKeyCode)
            self.saveEvidenceEvent(event, self.rfidKeyCode)
            self.rfidKeyCode = ''
            
        self.finishScreenTiming()
        self.return2clock()

    def decode_server_response(self, req, results):
        print('RESP: ' + results)
        self.read_server_status(self.EVIDENCE_SERVER)        
                
    def read_server_status(self, addr=EVIDENCE_SERVER):
        url = 'http://{0}{1}t=4'.format(addr, self.EVIDENCE_PATH) 
        req = UrlRequest(url, self.decode_server_status)

    def decode_server_status(self, req, results):
        peopleno = self.ids.peopleno
        peopleya = self.ids.peopleya

        d = json.loads(results)
        for key, value in d.items():
            print(key, ': ', value)
            if key=='prit': peopleya.text = value 
            if key=='neprit': peopleno.text = value 


class MainApp(App):
    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.stop.set()
        
    def build(self):
        return Evidence()


if __name__ == "__main__":
    MainApp().run()
