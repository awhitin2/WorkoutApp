import functools
from types import SimpleNamespace

from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, BooleanProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, ButtonBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivy.uix.label import Label
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.screen import MDScreen
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout

from backend import mapping 
from backend.schedulemanager import schedule_manager
import backend.mapping as mapping
import backend.database as db

option = db.get_latest_workout_template()

class SessionScreen(MDScreen):
    workout_info = ObjectProperty()
    toolbar = ObjectProperty()
    layout = ObjectProperty()

    def __init__(self, workout_info: mapping.WorkoutOptionInfo = None, **kwargs):
        super().__init__(**kwargs)
        if not workout_info:
            workout_info = option
        self.workout_info = workout_info
        self.title = workout_info.title
        self.name: str = self.workout_info.id #For registration with ScreenManager
        self.dialogs: dict[str:MDDialog] = {}
        self.lift_cards: list = [] #Keep this or iterate through layout.children
        self.input_layouts: list = None
        self.session_key: str = None
        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        self.toolbar.title = self.title
        for lift, sets in self.workout_info.lift_info_dict.items():
            self.layout.add_widget(LiftCard(lift, sets))
        self.input_layouts = [card.input_layout for card in self.layout.children]

    def validate_record(self, *args):       

        if all([layout.is_empty() for layout in self.input_layouts]):
            self._empty_dialog()
            return
        
        incomplete_found = False
        empty_found = False

        for layout in self.input_layouts:
            if not incomplete_found: 
                if layout.is_incomplete():
                    incomplete_found = True
            if not empty_found:
                if layout.is_empty():
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

        if not key in self.dialogs:
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
        for layout in self.input_layouts:
            if not layout.is_empty():
                layout.log_lift()

    def show_add_lift_dialog(self):
        key = 'lift'
        if not key in self.dialogs:
            self.dialogs[key] =  MDDialog(
                title="Select Lift",
                type="custom",
                content_cls = AddLiftDialog(self.workout_info.lift_info_dict),
                buttons=[
                    MDFlatButton(
                        text="DISCARD",
                        on_release=functools.partial(self._close_dialog, key)
                    ),
                    MDFlatButton(
                        text="ADD", 
                        on_release=self._validate_lift_dialog
                    ),
                ],
            )
        self.dialogs[key].open()

    def _validate_lift_dialog(self, *args):
        dialog: AddLiftDialog = self.dialogs['lift'].content_cls
        if not dialog.is_valid():
            return
            
        self._register_from_lift_dialog()

    def _close_dialog(self, key, instance = None):
        self.dialogs[key].dismiss()
        
    def _register_from_lift_dialog(self, *args):
        dialog = self.dialogs['lift'].content_cls
        selected = dialog.get_selected()

        for select in selected:
            self.layout.add_widget(LiftCard(select.lift, select.sets))

        self._close_dialog('lift')


class LiftCard(MDCard):

    lift = StringProperty()
    sets = NumericProperty()
    box = ObjectProperty()

    def __init__(self, lift, sets, **kwargs):
        super().__init__(**kwargs)
        self.lift = lift
        self.sets = sets
        self.record_layout = RecordLayout(lift, sets)
        self.box.add_widget(self.record_layout)
        self.input_layout = InputLayout(lift, sets)
        self.box.add_widget(self.input_layout)



class RecordLayout(ScrollView):
    stack = ObjectProperty()

    def __init__(self, lift, sets, **kwargs):
        super().__init__(**kwargs)
        self.lift = lift
        self.set_records()

    def set_records(self):
        more, previous_sessions = db.get_last_completed_lifts(self.lift, 4)
        if previous_sessions:
            for session in previous_sessions:
                self.stack.add_widget(RecordColumn(session))

            if more:
                self.start_id = previous_sessions[-1].id
                self.stack.add_widget(
                    LoadMore(on_press = self.load_more_records))
            if len(previous_sessions) == 2:
                self.stack.add_widget(ColumnSpacer())
            if len(previous_sessions) == 1:
                self.stack.add_widget(NoData(width = 197*2))
        else: 
            self.stack.add_widget(NoData(width = 197*3))

    def load_more_records(self, instance):
        self.stack.remove_widget(instance)
        more, previous_sessions = db.get_additional_completed_lifts(
                                        self.lift, self.start_id, 3)
        for session in previous_sessions:
            self.stack.add_widget(RecordColumn(session))
        if more:
            self.start_id = previous_sessions[-1].id
            self.stack.add_widget(LoadMore(on_press = self.load_more_records))
    

class RecordColumn(StackLayout):
    date = StringProperty()

    def  __init__(self, session_info: mapping.LiftSessionRecord, **kwargs) -> None:
        super().__init__(**kwargs)
        self.date = session_info.date
        for set in session_info.sets:
            self.add_widget(RecordLabel(set))

class RecordLabel(Label):
    set = ObjectProperty()

    def __init__(self, set: dict, **kwargs):
        super().__init__(**kwargs)
        self.text = self._format_set(set)

    def _format_set(self, set:dict)->str:
        if set['weight'] == 0: 
            return str(set['reps'])
        return f"{str(set['reps'])}x{str(set['weight'])}"

class ColumnSpacer(MDBoxLayout):
    pass

class NoData(MDRelativeLayout):
    pass

class LoadMore(ButtonBehavior, MDRelativeLayout):
    pass

class InputLayout(StackLayout):

    def __init__(self, lift, sets, **kwargs):
        super().__init__(**kwargs)
        self.lift = lift
        self.input_rows = []
        self.dialogs = {}
        for i in range(sets):
            row = InputRow()
            self.add_widget(row)
            self.input_rows.append(row)
        self.empty_rows = len(self.input_rows)

    def validate(self, *args):
        if self.is_empty():
            self._empty_dialog()
            
        elif self.is_incomplete():
            self._incomplete_dialog()

        else:
            self.log_lift()

    def is_empty(self)-> bool:
        if self.empty_rows == len(self.input_rows):
            return True
        return False

    def is_incomplete(self)-> bool:
        if 0 < self.empty_rows < len(self.input_rows):
            return True
        return False

    def _empty_dialog(self):
        key = 'empty'
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

    def _incomplete_dialog(self):
        key = 'incomplete'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text="Record is incomplete. Proceed anyway?",
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
        self.log_lift()

    def _close_dialog(self, key, instance = None):
        self.dialogs[key].dismiss()

    def log_lift(self):

        sets = []
        max = 0
        for row in self.input_rows:
            sets.append(row.get_dict())
            if row.weight:
                weight = row.weight
                if weight > max:
                    max = weight
            for field in [row.rep_field, row.weight_field]:
                field.text = ''
        
        #This is hideous
        session_screen = self.parent.parent.parent.parent.parent.parent
        
        if not session_screen.session_key:
            session_screen.session_key = db.register_session(session_screen.title)
            db.update_last_completed(session_screen.name)

            if session_screen.workout_info.title == schedule_manager.next_name:
                schedule_manager.cycle_next_scheduled()
        
        db.update_session(session_screen.session_key, self.lift)
        db.register_completed_lift(session_screen.session_key, self.lift, sets)
        db.register_graph_data(session_screen.session_key, self.lift, max)
            

        record_layout = self.parent.parent.record_layout
        record_layout.stack.clear_widgets()
        record_layout.set_records()

        self._success_dialog()

    def _success_dialog(self):
        key = 'success'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text="Logged succesfully",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    ),
                ]
            )
        self.dialogs[key].open()


class InputRow(MDBoxLayout):
    reps = NumericProperty()
    weight = NumericProperty()
    empty = BooleanProperty(True)
    rep_field = ObjectProperty()
    set_field = ObjectProperty()

    def on_reps(self, *args):
        self.empty = self._is_empty()
 
    # def on_reps(self, *args):  -- Test and maybe use this now that not requiring wieght
    #     self.empty = False if self.reps else True

    def on_weight(self, *args):
        self.empty = self._is_empty()

    def _is_empty(self):
        if self.reps:
            return False
        else:
            return True
    
    def on_empty(self, *args):
        if self.empty:
            self.parent.empty_rows += 1
        else:
            self.parent.empty_rows -= 1

    def get_dict(self):
        try:
            return {
                'reps': self.reps,
                'weight': self.weight if self.weight else 0}
        except ValueError:
            return None

class AddLiftDialog(MDBoxLayout):
    """Content class for SessionScreen Add Lift dialog"""
    lift_dict = ObjectProperty()
    box = ObjectProperty()

    def __init__(self, lift_dict: dict, **kwargs):
        super().__init__(**kwargs)
        self.rows = []
        self.dialogs = {}
        lifts = db.get_lifts()
        for lift in lifts:
            #Only display lifts not already included in current workout sessions
            if lift not in lift_dict:
                row = AddLiftDialogRow(lift = lift)
                self.box.add_widget(row) 
                self.rows.append(row)
    
    def is_valid(self):
        if all([row.is_empty() for row in self.rows]):
            self._empty_dialog()
            return
        if any([row.missing_sets() for row in self.rows]):
            self._incomplete_dialog()
            return
        if any([row.is_invalid() for row in self.rows]):
            self._invalid_dialog()
        return True
    
    def _empty_dialog(self):
        key = 'empty'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text="No lifts selected",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    )
                ]
            )
        self.dialogs[key].open()

    def _incomplete_dialog(self):
        key = 'incomplete'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text='Missing set info',
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    )
                ]
            )
        self.dialogs[key].open()

    def _invalid_dialog(self):
        key = 'invalid'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text='Invalid selection',
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    )
                ]
            )
        self.dialogs[key].open()

    def _close_dialog(self, key, instance):
        self.dialogs[key].dismiss()


    def get_selected(self):
        return [SimpleNamespace(lift = row.lift, sets = int(row.sets)) 
                for row in self.rows
                if row.check.active == True]
        

class AddLiftDialogRow(MDBoxLayout):
    lift = StringProperty()
    sets = StringProperty('')

    def __init__(self, lift: str, **kwargs):
        super().__init__(**kwargs)
        self.lift = lift

    def is_empty(self):
        if self.check.active == False and not self.sets:
            return True
        return False

    def missing_sets(self):
        if self.check.active == True and not self.sets:
            return True
        return False
    
    def is_invalid(self):
        if self.check.active == True and self.sets:
            return False
        if self.check.active == False and not self.sets:
            return False
        return True

    def set_icon(self, instance_check, instance_input):
        instance_check.active = True if instance_check.active == False else instance_check.active == False
        instance_input.disabled = True if instance_input.disabled == False else instance_input.disabled == False
        if instance_input.disabled == True: instance_input.text = "" 

        if instance_input.size_hint_x == 0:
            instance_input.size_hint_x = .2
        else:
            instance_input.size_hint_x = 0