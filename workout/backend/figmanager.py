
from __future__ import annotations

import matplotlib.pyplot as plt

from kivy.properties import ObjectProperty
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.widget import Widget

import backend.database as db



class FigManager(Widget):
    period = StringProperty()
    lift = StringProperty()
    plot = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.displays: list[FigDisplay] = []
        self.figs = {}
        self.lift, self.period = db.get_plot_initialization_info()
        self.plot = ()
        # self.bind(period = self.on_period)
        # self.bind(lift = self.on_lift)
        self.bind(plot = self.on_plot)
        self.set_fig(self.lift, self.period)

    def on_period(self, *args):
        if self.lift and self.period:
            self.set_fig(self.lift, self.period)
        
    def on_lift(self, *args):
        if self.lift and self.period:
            self.set_fig(self.lift, self.period)

    def register_display(self, display: FigDisplay):
        self.displays.append(display)
        display.set_display()

    def set_fig(self, lift, period):
        if not (lift, period) in self.figs:
            self.figs[(lift, period)] = int(Figure(lift, period))
        plt.figure(self.figs[(lift, period)])
        self.plot = (lift, period)

    def on_plot(self, *args):
        for disp in self.displays:
                disp.set_display()

class FigDisplay(ButtonBehavior, MDBoxLayout):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plot = None
        
    def set_display(self):
        if self.plot:
            self.remove_widget(self.plot)
        self.plot = FigureCanvasKivyAgg(plt.gcf())
        self.add_widget(self.plot)

class Figure:
    next = 0

    def __init__(self, lift, period) -> int:
        self.lift = lift
        self.period = period
        Figure.next += 1
        self.index = Figure.next
        self.config_fig(self.index)
        self.config_ax()
        self.plot()

    def __int__(self):
        return self.index

    def config_fig(self, next: int) -> None:
        fig = plt.figure(next, figsize=(5,3))
        fig.patch.set_facecolor('black')
        plt.title(self.lift,fontweight="bold")
        font = {
            'family' : 'normal',
            'weight' : 'bold',
            'size'   : 22
            }
        plt.rc('font', **font)
        plt.rcParams['legend.frameon'] = 'False'
        plt.subplots_adjust(left=0.05, top=0.95, right = 0.88)
        self.fig = fig
        

    def config_ax(self):
        ax = plt.axes()
        ax.set_facecolor([0.06,0.06,0.06])
        for direction in ['bottom', 'top', 'left', 'right']:
            ax.spines[direction].set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.tick_right()
        ax.grid(alpha=0.1)
        ax.title.set_color('white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        self.ax = ax

    def plot(self):
        data = db.get_plot_data(self.lift, self.period)
        if data: 
            self.ax.plot_date(
                data.time_values, 
                data.lift_values, 
                color = 'orange',
                label = self.lift, 
                linestyle = '--',
                marker = 'o',
                markersize = 10,
                linewidth = 4
                )
            self.ax.xaxis.set_major_formatter(data.date_format)
            self.fig.autofmt_xdate(rotation=45, ha='center')
        else:
            plt.text(0.5, 0.65, 'No Data to Display', 
                color = 'white', 
                horizontalalignment='center',
                verticalalignment='center')


manager = FigManager()