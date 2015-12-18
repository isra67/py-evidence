#!/bin/python

'''
Evicence 2.0
(C) IS 2015

Sources:
  https://github.com/kivy/kivy/wiki/Working-with-Python-threads-inside-a-Kivy-application
'''

from glob import glob
from math import cos, sin, pi

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.config import ConfigParser
from kivy.graphics import Color, Line, Rectangle, Ellipse
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import ListProperty 
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as mImage
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
#from kivy.utils import get_color_from_hex

from os.path import join, dirname

try:
    import urlparse
except ImportError:
    from urllib.parse import *

import datetime
import feedparser
import hashlib
import json
import locale
import random
##import os.path
import socket
import sys
import urllib
import threading


# IS packages:
##sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import mlib


Builder.load_file("main1.kv")

IMG_TIME = 10

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
    galleryIndex = 0
    gallery = []
    img = mImage()
    ln = Label()

    def __init__(self, **kwargs):
        super(Ticks, self).__init__(**kwargs)
        self.bind(pos = self.update_clock)
        self.bind(size = self.update_clock)

        self.ln.text = '[color=ff3333] Evidence 2.0 [/color]'
        self.ln.pos = self.pos
        self.ln.size = self.size
        self.ln.font_size = '32sp'
        self.ln.text_size = self.size
        self.ln.halign = 'right'
        self.ln.valign = 'bottom'
        self.ln.markup = True

        self.load_img_list()
        Clock.schedule_interval(self.update_clock, 1)

    def load_img_list(self, *args):
        # get any files into images directory
        curdir = dirname(__file__)

        for filename in glob(join(curdir, 'gallery', '*')):
            self.gallery.append( filename )

    def update_clock(self, *args):
        time = datetime.datetime.now()
        self.canvas.clear()

        if time.second % IMG_TIME == 0:
            ni = self.galleryIndex
            while ni == self.galleryIndex:
                ni = random.randint(0,len(self.gallery) - 1)
            self.galleryIndex = ni
        
        self.remove_widget(self.ln)
        self.remove_widget(self.img)
        self.img.source = self.gallery[self.galleryIndex]
        self.img.pos = self.pos
        self.img.size = self.size
        self.ln.pos = self.pos
        self.ln.size = self.size
        self.ln.text_size = self.size
        self.add_widget(self.img)
        self.add_widget(self.ln)

        with self.canvas:
            Color(.1, .1, .6, .15)
            Ellipse(pos={self.y + 19,self.width / 4}, size={self.width / 2, self.height - 38})

            Color(0.6, 0.6, 0.9)
            Line(points = [self.center_x, self.center_y, self.center_x+0.7*self.r*sin(pi/30*time.second), self.center_y+0.7*self.r*cos(pi/30*time.second)], width=1, cap="round")
            Color(0.5, 0.5, 0.8)
            Line(points = [self.center_x, self.center_y, self.center_x+0.6*self.r*sin(pi/30*time.minute), self.center_y+0.6*self.r*cos(pi/30*time.minute)], width=2, cap="round")
            Color(0.4, 0.4, 0.7)
            th = time.hour*60 + time.minute
            Line(points = [self.center_x, self.center_y, self.center_x+0.5*self.r*sin(pi/360*th), self.center_y+0.5*self.r*cos(pi/360*th)], width=3, cap="round")


#App
class Evidence(FloatLayout):
    stop = threading.Event()
    rfidKeyCode = ''
    config = ConfigParser()
    config.read('./myconfig.ini') # konfiguracny subor
    my_data = ListProperty([])

    def __init__(self, **kwargs):
        print('Ini')
        super(Evidence, self).__init__(**kwargs)
        self.scrmngr = self.ids._screen_manager
        
        loc = locale.getlocale()
        defloc = locale.getdefaultlocale()

        try:
            if loc[0] == None and loc[1] == None:
                if defloc[1] != 'cp1250':
                    locale.setlocale(locale.LC_ALL, 'sk_SK.UTF-8')
                else:
                    if defloc[0] != None and defloc[1] != None:
                        locale.setlocale(locale.LC_ALL, defloc[0]+'.'+defloc[1])
                    else:
                        locale.setlocale(locale.LC_ALL, '')
        except:
            print("Error: ", sys.exc_info()[0])
            try:
                locale.setlocale(locale.LC_ALL, '')
            except:
                print("Error 2: ", sys.exc_info()[0])
            #sys.exit()
            
        print('Locales: c:{} - d:{}'.format(locale.getlocale(),locale.getdefaultlocale()))
        
        try:
            self.config.read(dirname(__file__) + '/' + 'myconfig.ini') # konfiguracny subor
        except:
            pass

        # nacitanie konfiguracie
        self.DEVICE = self.config.get('evidence', 'device')
        self.EVIDENCE_TYPE = self.config.get('evidence', 'evidence_type')
        self.ACCESS_TYPE = self.config.get('evidence', 'access_type')
        self.EVIDENCE_SERVER = self.config.get('evidence', 'evidence_server')
        self.EVIDENCE_PATH = self.config.get('evidence', 'evidence_path')
        self.EVIDENCE_GET_PATH = self.config.get('evidence', 'evidence_get_path')

        self.HOST = self.config.get('server', 'host')
        self.PORT = self.config.getint('server', 'port')

#        print('test quote: ' + self.myQuote(u'123 +-*'))

#        mlib.lrss()

        # Start a new thread with an infinite loop and stop the current one
        d = threading.Thread(target = self.infinite_loop)
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
#            print('Connected with ' + addr[0] + ':' + str(addr[1]))

            #start new thread takes 1st argument as a function name to be run,
            # second is the tuple of arguments to the function
            threading.Thread(target=self.clientthread, args=(conn,)).start()

        self.s.close()

    def sockserv_init(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #Bind socket to local host and port
        try:
            self.s.bind((self.HOST, self.PORT))
        except socket.error as msg:
            print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            sys.exit()

        #Start listening on socket
        self.s.listen(10)

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
#            print('MSG: ' + msg)
            if '"RFID":' in msg:
                if self.scrmngr.current == 'events':
                    conn.sendall(b'RFID busy')
                else:
                    conn.sendall(b'RFID OK')

                    #spracovanie RFID kodu:
                    d = json.loads(msg)
                    for key, value in d.items():
                        if key == 'RFID':
                            self.rfidKeyCode = value.replace("UNDEFINED", "")

                    self.swap_screen('events')
                msg = ''
#                break

#        print('Out of client loop! ' + msg)
        #came out of loop
        conn.close()

    @mainthread
    def swap_screen(self, scr):
        self.scrmngr.current = scr

    def startScreenTiming(self):
        #print('Enter')
        Clock.schedule_once(self.return2clock, 5)

    def return2clock(self, *args):
#        print('ret2clock')
        self.swap_screen('clock')

    def finishScreenTiming(self):
        #print('Leave')
        Clock.unschedule(self.return2clock)

    def myQuote(self, par):
        try:
            a = quote(par, safe = '')
        except NameError:
            a = urllib.quote(par, safe = '')
        return a

    def saveEvidenceEvent(self, event, rfid):
        xdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        a = self.rfidKeyCode + xdate
        b = hashlib.md5(b'inoteska').hexdigest()
        c = b + a

        xhash = hashlib.md5(c.encode("utf-8")).hexdigest()

        par = 't=boarddata'
        par += '&x=' + self.myQuote(xhash)
        par += '&d=' + self.myQuote(xdate)
        par += '&ac=' + self.ACCESS_TYPE
        par += '&dev=' + self.DEVICE
        par += '&c=' + rfid + '&ty=' + event

        url = 'http://{0}{1}{2}'.format(self.EVIDENCE_SERVER, self.EVIDENCE_PATH, par)
        req = UrlRequest(url, self.decode_server_response)

    def processEvent(self, event):
        if self.rfidKeyCode == '':
            print('Lost event - no RFID key')
            self.return2clock()
        else:
            #print('Event: ' + event + ' Code: ' + self.rfidKeyCode)
            self.swap_screen('waitscr')
            self.saveEvidenceEvent(event, self.rfidKeyCode)
            self.rfidKeyCode = ''

    def decode_server_response(self, req, results):
        Clock.schedule_once(self.return2clock, 3)
        rqresult = self.ids.lblresult

        if 'ERROR' in results:
            rqresult.text = 'CHYBA!'
            print('RESP: ' + results)
        else:
            rqresult.text = 'OK'

    def read_server_status(self):
        url = 'http://{0}{1}t=4'.format(self.EVIDENCE_SERVER, self.EVIDENCE_PATH)
        req = UrlRequest(url, self.decode_server_status)
        
    def decode_server_status(self, req, results):
        d = json.loads(results)
        for key, value in d.items():
            if key == 'prit': self.ids.peopleya.text = value
            if key == 'neprit': self.ids.peopleno.text = value
 
    def read_detail_status(self):
        url = 'http://{0}{1}task=prit&json='.format(self.EVIDENCE_SERVER, self.EVIDENCE_GET_PATH)
        req = UrlRequest(url, self.decode_detail_status)
        while len(self.my_data):
            self.my_data.pop()

    def decode_detail_status(self, req, results):
        self.ids.idscrollperson.clear_widgets()
        
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        #Make sure the height is such that there is something to scroll.
        layout.bind(minimum_height=layout.setter('height'))

        try:
            d = json.loads(results)
            for value in d:
                m = ''
                p = ''
                descr = ''
                s = ''
                c = '#000'
                for k,v in value.items():
                    if k == 'priezvisko': p = v
                    if k == 'meno': m = v
                    if k == 'color': c = v
                    if k == 'descr' and v != '': descr = ' - ' + v
                
                s = u'[color={0}]{1} {2} {3}[/color]'.format(c, p, m, descr)
                
                self.my_data.append(s)
                try:
                    btn = Label(text=s, height='38sp', markup=True,\
                        font_size='32sp', pos=self.pos, size_hint_y=None )
                except:
                    print("Error: ", sys.exc_info()[0])
                layout.add_widget(btn)
        except:
            print('Chyba: ', sys.exc_info()[0])
            
        self.ids.idscrollperson.add_widget(layout)
                        

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
