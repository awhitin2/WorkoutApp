import functools

from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivy.uix.button import Button
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.card import MDCardSwipe
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.screen import MDScreen

from kivymd.uix.textfield import MDTextField

from backend import utils
import backend.database as db


class EditScreen(MDScreen):
    toolbar = ObjectProperty()
    date_label = ObjectProperty()
    date_obj = ObjectProperty()
    date_str = StringProperty()
    scroll_layout = ObjectProperty()
    workout = StringProperty()
    lifts = ObjectProperty()
    
    def __init__(
            self, key: str, date_str: str, date_obj, 
            workout: str, lifts: dict, **kw):
        super().__init__(**kw)
        self.dialogs = {}
        self.name: str = key
        self.key: str = key
        self.workout: str = workout
        self.date_str: str = date_str
        self.date_obj = date_obj

        self.lifts: dict[str:bool] = lifts
        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        self.toolbar.title = self.workout
        for lift in self.lifts:
            self.scroll_layout.add_widget(EditableSessionCard(lift, self.key))

    def on_date_obj(self, *args):
        if self.date_obj:
            self.date_str = utils.parse_date(self.date_obj, 'Day, Mon DD, YYYY')


    def add_lift(self):
        print('Add lift')

    def show_add_lift_dialog(self):
        key = 'new_lift'
        
        self.dialogs[key] = MDDialog(
        title="Add Lift to Session",
        type="custom",
        content_cls = AddLiftDialog(self.lifts),
        buttons=[
            MDFlatButton(
                text="DISCARD",
                on_release=functools.partial(self._close_dialog, key)
            ),
            MDFlatButton(
                text="ADD", 
                # on_release=self.register_workout_template
                on_release=self._process_new_lift_dialog
            ),
        ],
    )
        self.dialogs[key].open()

    def _close_dialog(self, key, instance=None):
        self.dialogs[key].dismiss()

    def _process_new_lift_dialog(self, instance, *args):
        data = self.dialogs['new_lift'].content_cls.get_input_data()
        for k, v in data.items():
            self.scroll_layout.add_widget(EditableSessionCard(k, self.key, sets = v))
            self.lifts[k] = True

        self._close_dialog('new_lift')

    def validate_record(self, *args):
        self.cards = [child for child in self.scroll_layout.children]
        
        if all([card.is_empty() for card in self.cards]): #Count the trues here to avoid another is_empty check?
            self._empty_dialog()
            return
        
        incomplete_found = False
        empty_found = False

        for card in self.cards:
            if not incomplete_found: 
                if card.is_incomplete():
                    incomplete_found = True
            if not empty_found:
                if card.is_empty():
                    empty_found = True

        if incomplete_found or empty_found:
            self._incomplete_dialog(incomplete_found, empty_found)
            return

        self._log_lifts()

    def _empty_dialog(self):
        key = 'all empty'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text="No info to log",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    )
                ]
            )
        self.dialogs[key].open()

    def _incomplete_dialog(self, incomplete, empty):
        key = 'incomplete'
        text = ''
        if empty:
            text = 'Some records are empty and will not be logged.'
        if incomplete:
            text += '\nSome records are incomplete.'

        self.dialogs[key] = MDDialog(
            text=text,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    on_release = functools.partial(self._close_dialog, key)
                ),
                MDFlatButton(
                    text="PROCEED",
                    theme_text_color="Custom",
                    on_release = functools.partial(self._proceed, key)
                )
            ]
        )
        self.dialogs[key].open()
        
    def _success_dialog(self):
        key = 'success'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text="Logged successfully",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    ),
                ]
            )
        self.dialogs[key].open()

    def _proceed(self, key, instance):
        self._close_dialog(key)
        self._log_lifts()

    def _log_lifts(self, instance = None):
        db.update_session_date(self.key, self.date_obj.isoformat())
        for card in self.cards:
            if not card.is_empty():
                card.log_lift()

        # if validate:
        #     if not self.validate_template(data):
        #         return
        # db.register_workout_template(data)
        # new_template = db.get_latest_workout_template()
        # self.options_layout.add_widget(
        #     WorkoutOptionCard(new_template), len(self.options_layout.children))
        # self.dialogs['new_template'].dismiss()

class EditableDateButton(Button):
    date_obj = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._post_init)

    def _post_init(self, *args):
        self.bind(date_obj = self.parent.parent.setter('date_obj'))

    def show_date_picker(self):
            date_dialog = MDDatePicker(
                year=self.date_obj.year,
                month=self.date_obj.month,
                day=self.date_obj.day,
                min_year = 2020,
            )
            date_dialog.bind(on_save=self._on_save)
            date_dialog.open()

        
    def _on_save(self, instance, value, range):
        if not self.date_obj == value:
            self.date_obj = value
    
           
class EditableSessionCard(MDCardSwipe):
    lift = StringProperty()
    num_rows = NumericProperty()
    box = ObjectProperty()

    def __init__(self, lift, key, sets = None, **kwargs):
        super().__init__(**kwargs)
        self.lift = lift
        self.key = key
        self.rows = []
        self.dialogs = {}
        self.box.bind(children= self._set_num_rows) 
        self.session_screen = None
        
        if not sets:
            data = db.get_lift_session(key, lift)
            self.num_rows = len(data)
            for row in data:
                self.box.add_widget(EditRow(row), 1) #Using ** to expand row here doesn't work?
        else:
            self.num_rows = sets
            for row in range(sets):
                self.box.add_widget(EditRow(),1)

        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        self.session_screen = self.parent.parent.parent.parent

    def _add_rep(self):
        self.box.add_widget(EditRow(), 1)
        print("add rep")
    
    def _set_num_rows(self, instance, children):
        self.num_rows = len(children)-1

    def remove(self):
        del self.session_screen.lifts[self.lift]
        self.parent.remove_widget(self)

    def is_empty(self):
        self.rows = [child for child in self.box.children if isinstance(child, EditRow)]
        return True if all([row.is_empty() for row in self.rows]) else False
    
    def is_incomplete(self):
        return True if any([row.is_empty() for row in self.rows]) else False

    def log_lift(self):

        sets = [] #are these registered in reverse order? I think so
        max = 0
        for row in self.rows:
            sets.append(row.get_dict())
            if row.weight:
                weight = row.weight
                if weight > max:
                    max = weight
        
        date = self.session_screen.date_obj.isoformat()
        db.update_session(self.key, self.lift)
        db.register_completed_lift(self.key, self.lift, sets, date)
        db.register_graph_data(self.key, self.lift, max, date)

        self._success_dialog()
        #Delete the screen so reclicking generates a new one

    def _success_dialog(self):
        key = 'success'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text="Record updated succesfully",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    ),
                ]
            )
        self.dialogs[key].open()

    def _close_dialog(self, key, instance):
        self.dialogs[key].dismiss()

class EditRow(MDRelativeLayout):
    reps = NumericProperty()
    weight = NumericProperty()
    
    def __init__(self, row = None) -> None: 
        super().__init__()
        if row: 
            self.reps = row['reps']
            self.weight = row['weight']

    def is_empty(self):
        return False if self.reps else True

    def get_dict(self):
        try:
            return {
                'reps': int(self.reps), 
                'weight': int(self.weight) if self.weight else 0}
        except ValueError:
            return None
    

    def remove(self):
        if self.parent.parent.parent.num_rows == 1:
            session_card = self.parent.parent.parent
            session_card.remove()
        else:
            self.parent.remove_widget(self)
        
        print('remove row')


class AddLiftDialog(MDBoxLayout):
    scroll_box = ObjectProperty()

    def __init__(self, lifts: dict, **kwargs):
        super().__init__(**kwargs)
        self.rows: list[AddLiftdialogRow] = []
        for lift in db.get_lifts():
            if lift not in lifts:
                self.scroll_box.add_widget(AddLiftdialogRow(lift))

    def get_input_data(self)-> dict[str:int]:
        
        return {(row.lift if row.lift else None) : 
                (int(row.input.text) if row.input.text else 1) 
                for row in self.scroll_box.children if row.check.active}
        
        
class AddLiftdialogRow(MDBoxLayout):
    lift = StringProperty()
    check = ObjectProperty()
    input = ObjectProperty()

    def __init__(self, lift, **kwargs):
        super().__init__(**kwargs)
        self.lift = lift
    
    def set_icon(self, instance_check, instance_input):
        instance_check.active = not instance_check.active
        instance_input.disabled = not instance_input.disabled
        
        if instance_input.disabled == True: instance_input.text = "" 
        
        if instance_input.size_hint_x == 0:
            instance_input.size_hint_x = .2
        else:
            instance_input.size_hint_x = 0


