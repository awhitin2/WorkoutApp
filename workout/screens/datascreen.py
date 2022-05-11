#Data cards are not taking newwly logged sessions into consideration

from __future__ import annotations

from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior

from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.screen import MDScreen
from kivy.uix.togglebutton import ToggleButtonBehavior
from kivy.uix.widget import Widget

from backend import colors
import backend.database as db
from backend import datacarddata
from screens import graphscreen
from screens import viewsessions
from backend import figmanager


class DataScreen(MDScreen):
    fig_display = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        mngr = figmanager.manager
        mngr.register_display(self.fig_display)


class DataCard(MDCard):
    """Base card used on datascreen when no calculation to display"""
    pass

class DataCardButton(DataCard): 
    """Data display card with button instead of calculation"""
    title = StringProperty()
    screen = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        self.left_container.add_widget(DataLabel(text = self.title))
        self.right_container.add_widget(DataButton(screen=self.screen))

class DataCardCalc(DataCard):  #Composition over inheritance here?
    """Data display card with calculation"""

    target = NumericProperty()
    title = StringProperty()
    calculation = NumericProperty()
    circle = BooleanProperty(False)
    unit = StringProperty()
    name = StringProperty()
    start_date_str = StringProperty() #What happens when there's no start date in the database?
    #Probably need to add a has_start_date boolean and use that determine inclusion of a start button. 
    #If has_start_date but start_date_str = '', then use today.
    left_container = ObjectProperty()
    right_container = ObjectProperty()
   
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._finish_init)
        
    def _finish_init(self, dt):
        data = db.get_data_card_data(self.name)

        if data.start_date_str:
            data.start_date = datetime.strptime(data.start_date_str, 
                                                "%Y-%m-%d").date()
        for key, value in vars(data).items():
            if value:
                setattr(self, key, value)

        self.calculate()
        self.default_view = DataLabel(text = self.title)
        self.edit_view = EditView(base_card = self)
        self.left_container.add_widget(self.default_view, index=1)

        if self.circle: 
            self.calc_widget = CircleCalculation(base_card = self)
        else: 
            self.calc_widget = Calculation(base_card = self)
        self.right_container.add_widget(self.calc_widget)

    def calculate(self):
        if self.unit:
            self.calculation = datacarddata.calc_functions[self.name][self.unit](self)
        else:
            self.calculation = datacarddata.calc_functions[self.name](self)

    def on_calculation(self, *args):
        print('calculated')

    def __repr__(self):
        return "{}(name={}, title={})".format(self.__class__.__name__, self.name, self.title)


class DataLabel(Label):
    """DataCard default view showing only the title"""
    
class DataButton(FloatLayout):
    screen = StringProperty()
    pass


class EditView(MDBoxLayout):
    """DataCard alternate view showing widgets to edit parameters"""
    base_card = ObjectProperty()
    text = StringProperty()
    orientation = 'horizontal'

    def __init__(self, base_card, **kwargs):
        super().__init__(**kwargs)
        self.base_card = base_card
        Clock.schedule_once(self._post_init, 0)

    def _post_init(self, dt):
        if self.base_card.start_date_str:
            self.add_starting_widget()
        if self.base_card.unit:
            self.add_unit_widget()
        self.add_target_widget()

    def add_starting_widget(self):
        self.add_widget(Starting(base_card = self.base_card))

    def add_target_widget(self):
        self.add_widget(Target(base_card = self.base_card))

    def add_unit_widget(self):
        self.add_widget(Unit(base_card = self.base_card))

    

class Starting(MDBoxLayout):
    """Allows user to modify DataCard start date"""

    start = StringProperty()
    base_card = ObjectProperty()
    # start_date = ObjectProperty()


    def __init__(self, base_card, **kwargs):
        super().__init__(**kwargs)
        self.base_card = base_card
        self.start_date = base_card.start_date
        # self.bind(start_date= self.base_card.setter('start_date'))
        self._set_start_date(self.start_date)

    def _set_start_date(self, date):
        self.start = \
            str(date.month) + '/' +\
            str(date.day) + '/' +\
            str(date.year)

    def _show_date_picker(self):
            date_dialog = MDDatePicker(
                year=self.start_date.year,
                month=self.start_date.month,
                day=self.start_date.day,
                min_year = 2020,
            )
            date_dialog.bind(on_save=self._on_save)
            date_dialog.open()
        
    def _on_save(self, instance, value, range):
        if not self.start_date == value:
            self.start_date = value # Can I bind starting.text to self.date? Maybe by binding a parse_date func?
            self.base_card.start_date = value
            self.base_card.start_date_str = value.isoformat()
            self._set_start_date(value)
            self.base_card.calculate()
            db.update_data_card(self.base_card.name, 'start_date_str', value.isoformat())
    


class Target(MDBoxLayout):
    """Allows user to modify DataCard target"""

    target = NumericProperty()
    base_card = ObjectProperty()
    target_button = ObjectProperty()

    def __init__(self, base_card, **kwargs):
        super().__init__(**kwargs)
        self.base_card = base_card
        self.target = base_card.target
        self.bind(target = base_card.setter('target'))
        self._create_dropdown()

    def _create_dropdown(self):
        menu_items = [
                {
                    "viewclass": "MenuLabel",
                    "text": f'{str(i)} sessions per week',
                    "height": dp(56),
                    "on_release": lambda x=i: self._target_update(x)
                    # "on_release": lambda x=i: self._load_data(str(x))

                } for i in range(1, 8)
            ]
        self.menu = MDDropdownMenu(
            caller=self.target_button,
            items=menu_items,
            position="center",
            width_mult=2.5,
            ver_growth="up"
        )

    def _target_update(self, target):
        if self.target != target:
            self.target = target #create update function? or just bind more smoothly
            self.base_card.calculate()
            db.update_data_card(self.base_card.name, 'target', self.target)
            self.menu.dismiss()

    def _show_menu(self):
        self.menu.open()


class Unit(MDBoxLayout):
    """Allows user to modify DataCard unit"""

    unit = StringProperty()
    base_card = ObjectProperty()
    unit_button = ObjectProperty()

    def __init__(self, base_card, **kwargs):
        super().__init__(**kwargs)
        self.base_card = base_card
        self.unit = self.base_card.unit
        self.bind(unit = base_card.setter('unit'))
        self._create_dropdown()

    def _create_dropdown(self):
        menu_items = [
                {
                    "viewclass": "MenuLabel",
                    "text": item,
                    "height": dp(56),
                    "on_release": lambda x=item: self._unit_update(x)
                    # "on_release": lambda x=i: self._load_data(str(x))

                } for item in ['Sessions', 'Weeks']
            ]
        self.menu = MDDropdownMenu(
            caller=self.unit_button,
            items=menu_items,
            position="center",
            width_mult=1.5,
        )

    def _unit_update(self, unit):
        if self.unit != unit:
            self.unit = unit 
            self.base_card.calculate()
            db.update_data_card(self.base_card.name, 'unit', unit)
            self.menu.dismiss()

    def _show_menu(self):
        self.menu.open()


class MenuLabel(ButtonBehavior, Label):
    pass

class RightContainer(Widget):
    """Defines size/position for the rightmost portion of a DataCard"""
    pass

class Calculation(ToggleButtonBehavior, RightContainer):
    """Displays calculation result"""

    # calculation = NumericProperty()
    # target = NumericProperty()
    base_card = ObjectProperty()
    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_card = kwargs['base_card']
        # self.base_card.bind(calculation = self._set_size)

    def on_state(self, widget, value):
        if value == 'down':
            self.base_card.left_container.remove_widget(self.base_card.default_view)
            self.base_card.left_container.add_widget(self.base_card.edit_view, index=1)
        else:
            self.base_card.left_container.remove_widget(self.base_card.edit_view)
            self.base_card.left_container.add_widget(self.base_card.default_view, index=1)


class CircleCalculation(Calculation):
    """Displays calculation result with progress circle"""
    
    angle_end = NumericProperty()
    target = NumericProperty()
    line_color = ListProperty(colors.chart_colors['transparent'])
    colors = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._finish_init)
        self.base_card = kwargs['base_card']
        
    def _finish_init(self, dt):
        self.set_color()
        self.base_card.bind(calculation = self.set_color)
        self.base_card.bind(target = self.set_color)

    def set_color(self, *args):
        if self.base_card.calculation >= self.base_card.target:
            self.line_color = colors.chart_colors['teal']
        elif self.base_card.calculation >= self.base_card.target*2/3:
            self.line_color = colors.chart_colors['green']
        elif self.base_card.calculation >= self.base_card.target/3:
            self.line_color = colors.chart_colors['orange']
        else:
            self.line_color = colors.chart_colors['red']


