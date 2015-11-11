#!/bin/python

from math import cos, sin, pi
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition
from kivy.uix.widget import Widget

import datetime
import json


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
    def __init__(self, **kwargs):
        print('Ini')
        super(Evidence, self).__init__(**kwargs)
        self.scrmngr = self.ids._screen_manager        
        self.read_server_status('192.168.1.47')

    def startScreenTiming(self):
        print('Enter')
        Clock.schedule_once(self.return2clock, 5)

    def return2clock(self, *args):
        print('ret2clock')
        self.scrmngr.current = 'clock'

    def finishScreenTiming(self):
        print('Leave')
        Clock.unschedule(self.return2clock)

    def processEvent(self, event):
        print('Event: ' + event)
        self.finishScreenTiming()
        self.return2clock()
        self.read_server_status('192.168.1.47')
        
    def read_server_status(self, addr):
        url = 'http://%s/inoteska/setdata.php?t=4' % addr 
        req = UrlRequest( url, self.decode_server_status)

    def decode_server_status(self, req, results):
        d = json.loads(results)
        for key, value in d.items():
            print(key, ': ', value)


class MainApp(App):
    def build(self):
        return Evidence()


if __name__ == "__main__":
    MainApp().run()
