import functools
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCardSwipe
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from screens.sessionscreen import SessionScreen

from backend import mapping
from backend.schedulemanager import schedule_manager

import backend.database as db


class SelectionScreen(MDScreen):
    options_layout = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.dialogs = {}
        self.option_info = [] #to compare new templates against to prevent creating identical workouts
        Clock.schedule_once(self._post_init)
     
    def _post_init(self, dt):       
        options: list[mapping.WorkoutOptionInfo] = db.get_workout_templates()
        for option in options:
            self.option_info.append(option)
            if not option.title == schedule_manager.next_name:
                self.options_layout.add_widget(WorkoutOptionCard(option))
            else:
                next_option = option
        #Wrap in try except
        self.options_layout.add_widget(WorkoutOptionCard(next_option), len(self.options_layout.children))
        

    def show_new_workout_dialog(self):
        self.dialogs['new_template'] = MDDialog(
            title="Create New Workout",
            type="custom",
            content_cls = WorkoutDialog(),
            buttons=[
                MDFlatButton(
                    text="DISCARD",
                    on_release=functools.partial(self.close_dialog, 'new_template')
                ),
                MDFlatButton(
                    text="CREATE", 
                    # on_release=self.register_workout_template
                    on_release=self.process_dialog_input
                ),
            ],
        )
        self.dialogs['new_template'].open()

    def close_dialog(self, key, *args): #consider dialog name
        self.dialogs[key].dismiss()

    def process_dialog_input(self, instance, validate: bool = True, *args):
        data = self.dialogs['new_template'].content_cls.get_input_data()
        if validate:
            if not self.validate_template(data):
                return
        db.register_workout_template(data)
        new_template = db.get_latest_workout_template()
        self.options_layout.add_widget(
            WorkoutOptionCard(new_template), len(self.options_layout.children))
        self.dialogs['new_template'].dismiss()
             

    def validate_template(self, data, *args):
        if data['title'] == '':
            self.trigger_error_dialog('Must include workout title')
            return
        if data['title'] in [option.title for option in self.option_info]:
            self.trigger_error_dialog('A template with this title already exits')
            return
        if not data['lifts']:
            self.trigger_error_dialog('Please select one or more lifts')
            return
        missing_sets = [key for (key, value) in data['lifts'].items() if value == None]
        if missing_sets:
            missing_sets = '\n'.join(missing_sets)
            self.trigger_error_dialog(f'Please include number of sets for:\n\n{missing_sets}')
            return
        for existing in self.option_info:
            if data['lifts'] == existing.lift_info_dict:
                self.trigger_confirm_dialog(f'The existing template {existing.title} has identical lifts and sets. Do you wish to proceed?')
                return
        return True

    def trigger_confirm_dialog(self, error_text):
        self.dialogs['confirm'] = MDDialog(
            title = 'Caution',
            text = error_text,
            buttons = [
                MDFlatButton(
                    text="Discard",
                    on_release = functools.partial(self.close_dialog, 'confirm')),
                MDFlatButton(
                    text="Confirm",
                    on_press = functools.partial(
                        self.process_dialog_input, 
                        validate = False),
                    on_release = functools.partial(self.close_dialog, 'confirm')
                    )])
        self.dialogs['confirm'].open()


    def trigger_error_dialog(self, error_text):
        self.dialogs['error'] = MDDialog(
            title = 'Error',
            text = error_text,
            buttons = [MDFlatButton(
                text="OK",
                on_release = functools.partial(self.close_dialog, 'error'))])
        self.dialogs['error'].open()


class WorkoutOptionCard(MDCardSwipe):
    option_info = ObjectProperty()
    
    def __init__(self, option_info: mapping.WorkoutOptionInfo, **kwargs):
        self.option_info = option_info #Check this
        super().__init__(**kwargs)
    
        
    def launch_session_screen(self, app):
        manager = app.root.ids.workout_sm
        if not manager.has_screen(self.option_info.id):
            manager.add_widget(SessionScreen(self.option_info))
            
        app.change_screen(
            manager = manager, 
            screen_name = self.option_info.id)
        
    def delete_template(self): ## move this to database
        self.parent.remove_widget(self)
        db.delete_template(self.option_info.id)



class WorkoutDialog(MDBoxLayout):
    title_field = ObjectProperty()
    scroll_box = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows: list[WorkoutDialogLiftRow] = []
        for lift in db.get_lifts():
            self.add_lift_row(lift)
            
    def add_lift_row(self,lift):
        row = (WorkoutDialogLiftRow(lift))
        self.rows.append(row)
        self.scroll_box.add_widget(row)

    def get_input_data(self)-> dict:
        data = {
            'title': self.title_field.text,
            'lifts': {(row.lift if row.lift else None) : 
                (int(row.input.text) if row.input.text else None) 
                for row in self.rows if row.check.active}
        }
        return data

    @staticmethod
    def register_new_lift(*args):
        print('register new lift')
        pass
        
class WorkoutDialogLiftRow(MDBoxLayout):
    lift = StringProperty()
    check = ObjectProperty() #is_selected_checkbox
    input = ObjectProperty() #num_sets_text_field

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


