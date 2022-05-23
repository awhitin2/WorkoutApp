import functools

from kivymd.app import MDApp
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
from kivy.uix.recycleview import RecycleView

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
            self, key: str, rv: RecycleView, date_str: str, date_obj, 
            workout: str,  lifts: dict = {}, new = False, index: int = 0,**kw):
        super().__init__(**kw)
        self.name: str = key 
        self.key: str = key
        self.rv = rv 
        self.workout: str = workout
        self.date_str: str = date_str
        self.date_obj = date_obj
        self.lifts: dict[str:bool] = lifts
        self.new = new
        self.index:int = index
        self.dialogs = {}
        self.stored_date = date_obj
        self.stored_lift_data = {}
        self.cards = [] #Do I want to constantly track these?
        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        self.toolbar.title = self.workout
        for lift in self.lifts:
            card = EditableSessionCard(lift, self.key)
            self.scroll_layout.add_widget(card)
            self.stored_lift_data[lift] = card.get_row_dicts()


    def on_date_obj(self, *args):
        if self.date_obj:
            self.date_str = utils.parse_date(self.date_obj, 'Day, Mon DD, YYYY')


    def show_add_lift_dialog(self):
        key = 'new_lift'
        
        self.dialogs[key] = MDDialog(
        title="Add Lift to Session",
        type="custom",
        content_cls = EditAddLiftDialog(self.lifts),
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

        if not self._info_has_changed():
            return
        
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

    def _info_has_changed(self):
        '''Checks if any info has been changed by the user relative 
        to what is in the database'''

        if self.date_obj != self.stored_date:
            return True
        
        if not self.cards:
            self.cards = [child for child in self.scroll_layout.children]

        # lift_data = {} #This is faster but less readable?
        # for card in self.cards:
        #     d = card.get_row_dicts()
        #     if d:
        #         lift_data[card.lift] = d

        lift_data = {card.lift: card.get_row_dicts() for card in self.cards 
                    if card.get_row_dicts() != []}

        if lift_data != self.stored_lift_data:
            return True

        return False

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

    def _proceed(self, key, instance):
        self._close_dialog(key)
        self._log_lifts()

    def _log_lifts(self, instance = None):
        
        db.update_session_date_workout(self.key, self.date_obj.isoformat(), self.workout)
        self.stored_date = self.date_obj

        if not self.new:
            del self.rv.data[self.index]

        data = {
            'key': self.key, 
            'date_str': self.date_str,
            'date_obj': self.date_obj,
            'workout': self.workout,
            'lifts': self.lifts
            } 

        self.rv.data.insert(self.index, data)

        for card in self.cards:
            if not card.is_empty():
                card.log_lift()
        
        self._success_dialog()

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

    def return_to_view_sessions_screen(self):
        if self._info_has_changed():
            self._leave_screen_dialog()
        else: 
            self._proceed_leave_screen()
        

    def _leave_screen_dialog(self):
        key = 'leave'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text="There are unsaved changes which will be lost. Proceed anyway?",
                buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    on_release = functools.partial(self._close_dialog, key)
                ),
                MDFlatButton(
                    text="PROCEED",
                    theme_text_color="Custom",
                    on_release = functools.partial(self._proceed_leave_screen, key)
                )
                ]
            )
        self.dialogs[key].open()

    def _proceed_leave_screen(self, key = 'leave', instance=None):
        if key in self.dialogs:
            self._close_dialog('leave')
        app = MDApp.get_running_app()
        manager = app.root.ids.data_sm
        app.change_screen(manager, screen_name='view_sessions_screen', direction='right')
        manager.remove_widget(self)
        db.delete_session(self.key)
        print('here now')


class EditableDateButton(Button):
    date_obj = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._post_init)

    def _post_init(self, *args):
        self.bind(date_obj = self.parent.parent.parent.setter('date_obj'))

    def show_date_picker(self):
            self.date_dialog = MDDatePicker(
                year=self.date_obj.year,
                month=self.date_obj.month,
                day=self.date_obj.day,
                min_year = 2020,
            )
            self.date_dialog.bind(on_save=self._on_save)
            self.date_dialog.open()

        
    def _on_save(self, instance, value, range):
        if not self.date_obj == value:
            self.date_obj = value
        self.date_dialog.dismiss()
    
           
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
        self.edit_screen = None
        
        if not sets:
            data = db.get_lift_session(key, lift)
            if not data: 
                data = []
            self.num_rows = len(data)
            for d in data:
                row = EditRow(d)
                self.rows.append(row)
                self.box.add_widget(row, 1) #Using ** to expand row here doesn't work?
        else:
            self.num_rows = sets
            for row in range(sets):
                row = EditRow()
                self.rows.append(row)
                self.box.add_widget(EditRow(),1)

        Clock.schedule_once(self._post_init)

    def _post_init(self, dt): #Recursive parent finder here
        self.edit_screen = self.parent.parent.parent.parent

    def _add_set(self):
        row = EditRow()
        self.rows.append(row)
        self.box.add_widget(row, 1)
        print("add set")
    
    def _set_num_rows(self, instance, children):
        self.num_rows = len(children)-1

    def remove(self):
        del self.edit_screen.lifts[self.lift]
        self.parent.remove_widget(self)

    def is_empty(self):
        self.rows = [child for child in self.box.children if isinstance(child, EditRow)]
        return True if all([row.is_empty() for row in self.rows]) else False
    
    def is_incomplete(self):
        return True if any([row.is_empty() for row in self.rows]) else False

    def get_row_dicts(self):
        return [row.get_dict() for row in self.rows]

    def log_lift(self):

        sets = []
        max = 0
        for row in self.rows:
            d = row.get_dict()
            if d:
                sets.append(d)
                #Update for comparison when navigating away from page.
                #More efficient here, but maybe more readable as it's own
                #dict comprension in the EditScreen log_lift as
                #self.stored_lift_data = {card.lift: card.get_row_dicts() for card in self.cards}
                self.edit_screen.stored_lift_data[self.lift] = d 

            if row.weight:
                weight = row.weight
                if weight > max:
                    max = weight
        
        sets.reverse()
        date = self.edit_screen.date_obj.isoformat()
        db.update_session(self.key, self.lift)
        db.register_completed_lift(self.key, self.lift, sets, date)
        db.register_graph_data(self.key, self.lift, max, date)

        #Delete the screen so reclicking generates a new one?    
        

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
            d =  {
                'reps': int(self.reps), 
                'weight': int(self.weight) if self.weight else 0}
            return d if d['reps'] != 0 else None

        except ValueError:
            return None
    

    def remove(self):
        session_card = self.parent.parent.parent
        if session_card.num_rows == 1:
            session_card = self.parent.parent.parent
            session_card.remove() #Rename remove here to not confuse with the list method?
        else:
            session_card.rows.remove(self)
            self.parent.remove_widget(self)
            
        print('remove row')


class EditAddLiftDialog(MDBoxLayout):
    scroll_box = ObjectProperty()

    def __init__(self, lifts: dict = {}, **kwargs):
        super().__init__(**kwargs)
        self.rows: list[EditAddLiftDialogRow] = []
        for lift in db.get_lifts(): 
            if lift not in lifts:
                self.scroll_box.add_widget(EditAddLiftDialogRow(lift))
    
    def get_input_data(self)-> dict[str:int]:
        
        return {(row.lift if row.lift else None) : 
                (int(row.input.text) if row.input.text else 1) 
                for row in self.scroll_box.children if row.check.active}
        
        
class EditAddLiftDialogRow(MDBoxLayout):
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


