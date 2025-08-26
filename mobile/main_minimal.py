#!/usr/bin/env python3

from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text='Hello World')

TestApp().run()