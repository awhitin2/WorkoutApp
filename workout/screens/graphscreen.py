
from __future__ import annotations

from datetime import datetime
import matplotlib.pyplot as plt

from kivy.properties import ObjectProperty
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.clock import Clock
from kivymd.uix.chip import MDChip
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivy.uix.widget import Widget

import backend.database as db
from backend import figmanager


class GraphScreen(MDScreen):
    figdisplay = ObjectProperty()
    lift_stack = ObjectProperty()
    period_stack = ObjectProperty()
    periods = ['Week', 'Month', '3 Months', '6 Months', 'Year', 'All Time']


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.post_init)

    def post_init(self, *args):
        self.mngr = figmanager.manager
        self.mngr.register_display(self.figdisplay)
        self._add_lift_chips()
        self._add_period_chips()
        self._select_initial_chips()

    def _add_lift_chips(self):
        
        for lift in db.get_lifts(): ### Code smellllll
            chip = GraphChip(
                        text = lift, 
                        stack = self.lift_stack,
                        on_press = self.on_press_lift)

            if lift == self.mngr.lift: chip.dispatch('on_press')
            self.lift_stack.add_widget(chip)

    def _add_period_chips(self):

        for period in GraphScreen.periods:
            chip = GraphChip(
                        text = period, 
                        stack = self.period_stack,
                        on_press = self.on_press_period)

            if period == self.mngr.period: chip.dispatch('on_press')
            self.period_stack.add_widget(chip)

    def _select_initial_chips(self):
        for chip in self.lift_stack.children:
            if chip.text == self.mngr.lift:
                chip.dispatch('on_press')
        
        for chip in self.period_stack.children:
            if chip.text == self.mngr.period:
                chip.dispatch('on_press')

    def on_press_lift(self, instance):
        self.mngr.lift = instance.text 
        self._on_press_chip(instance)
        
    def on_press_period(self, instance):
        self.mngr.period = instance.text
        self._on_press_chip(instance)
    
    def _on_press_chip(self, instance):
        instance._change_color()
        instance._deselect_other_chips()


class GraphChip(MDChip):
    stack = ObjectProperty()

    def __init__(self, stack, **kwargs):
        super().__init__(**kwargs)
        self.stack = stack

    def _change_color(self):
        self.color=self.selected_chip_color

    def _deselect_other_chips(self, *args):
        for instance_chip in self.stack.children:
            if instance_chip != self:                   
                    instance_chip.color = self.theme_cls.primary_color