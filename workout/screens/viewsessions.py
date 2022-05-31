from __future__ import annotations
import datetime
import functools

from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card import MDCardSwipe
from kivymd.uix.dialog import MDDialog
from kivy.uix.label import Label
from kivymd.uix.picker import MDDatePicker
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivymd.uix.screen import MDScreen

import backend.database as db
from backend import utils
from screens.sessionedit import EditScreen



class SessionInfo:

    def __init__(self, key, value) -> None:
        self.key = key
        self.date = utils.parse_date(value['date'], 'Day, Mon DD, YYYY')
    

class ViewSessionsScreen(MDScreen):
    recycle_view = ObjectProperty()
    box = ObjectProperty()
    rv = ObjectProperty()
    needs_recalculating = BooleanProperty()

    def __init__(self,  **kw):
        super().__init__(**kw)
        self.dialogs = {}
        Clock.schedule_once(self._post_init)


    def _post_init(self, dt):
        
        sessions = db.get_sessions()
        if sessions:
            sessions = [
            {
            'key': k, 
            'date_str': utils.parse_date(v['date'], 'Day, Mon DD, YYYY'),
            'date_obj': datetime.date.fromisoformat(v['date']),
            'workout': 'Custom' if not 'workout' in v else v['workout'],
            'lifts': {} if not 'lifts' in v else v['lifts']
            } 
            for k,v in sessions.items()]
            sessions.reverse()
            self.rv.data = sessions        

        else: 
            self.box.add_widget(Label(text='No data to display'),1)
        

    def add_session(self, app):
        key = db.register_session()
        date_obj = datetime.date.today()
        date_str = utils.parse_date(date_obj, 'Day, Mon DD, YYYY')
        manager = app.root.ids.data_sm
        manager.add_widget(
            EditScreen(
                key, 
                self.rv,
                date_str, 
                date_obj,
                'Custom',
                new = True
                ))
        
        app.change_screen(manager, screen_name = key)
        data_screen = MDApp.get_running_app().root.ids.data_screen
        data_screen.needs_recalculating = True

    def confirm_delete_dialog(self):
        key = 'confirm'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text='Are you sure you want to delete ALL sessions? This action cannot be undone.',
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    ),
                    MDFlatButton(
                        text="PROCEED",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._delete_all, key)
                    )
                ]
            )
        self.dialogs[key].open()

    def _close_dialog(self, key, instance=None):
        self.dialogs[key].dismiss()

    def _delete_all(self, key, instance):
        self.box.remove_widget(self.rv)
        self.box.add_widget(Label(text='No data to display'))
        db.delete_all_sessions()
        db.delete_all_completed_lifts()
        db.delete_all_graph_data()
        data_screen = MDApp.get_running_app().root.ids.data_screen
        data_screen.clear_data()
        self._close_dialog(key)
        


class SessionCard(RecycleDataViewBehavior, MDCardSwipe):

    index = None
    date_str = StringProperty()
    date_obj = ObjectProperty()
    key = StringProperty()
    workout = StringProperty()
    lifts = ObjectProperty()

    def __init__(self) -> None:
        super().__init__()
        self.dialogs = {}

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SessionCard, self).refresh_view_attrs(
            rv, index, data)

    
    def launch_edit_screen(self, app): # Check out "switch_to" a new ScreenManager method
        manager = app.root.ids.data_sm
        rv = self.parent.parent
        if not manager.has_screen(self.key):
            manager.add_widget(
                EditScreen(
                    self.key, 
                    rv,
                    self.date_str, 
                    self.date_obj,
                    self.workout,
                    self.lifts,
                    index = self.index,
                    ))
            
        app.change_screen(manager, screen_name = self.key)

    def confirm_delete_dialog(self):
        key = 'confirm'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text='Are you sure you want to delete this session? This action cannot be undone.',
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    ),
                    MDFlatButton(
                        text="PROCEED",
                        theme_text_color="Custom",
                        on_release = self._delete_session_info
                    )
                ]
            )
        self.dialogs[key].open()


    def _close_dialog(self, key, instance=None):
        self.dialogs[key].dismiss()

    def _delete_session_info(self, *args):

        del self.parent.parent.data[self.index]
        self._close_dialog('confirm')
        db.delete_session(self.key)

        for lift in self.lifts:
            db.delete_completed_lift(self.key, lift)
            db.delete_graph_data(self.key, lift)

        data_screen = MDApp.get_running_app().root.ids.data_screen
        data_screen.needs_recalculating = True

