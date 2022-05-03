from __future__ import annotations
from datetime import datetime

import functools
from kivy.clock import Clock
from kivymd.uix.card import MDCardSwipe
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton

from kivymd.uix.dialog import MDDialog
from kivymd.uix.picker import MDDatePicker
from kivy.properties import StringProperty, ObjectProperty


import backend.database as db
from backend import utils
from screens.sessionedit import EditScreen

sessions = db.get_sessions()


class SessionInfo:

    def __init__(self, key, value) -> None:
        self.key = key
        self.date = utils.parse_date(value['date'], 'Day, Mon DD, YYYY')
    

# sessions = [
#     {
#     'key': k, 
#     'date_str': utils.parse_date(v['date'], 'Day, Mon DD, YYYY'),
#     'date_obj': datetime.fromisoformat(v['date']),
#     'workout': 'lower' if not 'workout' in v else v['workout'],
#     'lifts': 'Bench Press' if not 'lifts' in v else v['lifts']
#     } 
#     for k,v in sessions.items()]

# sessions.reverse()
# sessions = sessions[:5]

class ViewSessionsScreen(MDScreen):
    recycle_view = ObjectProperty()
    box = ObjectProperty()

    def __init__(self,  **kw):
        super().__init__(**kw)
        Clock.schedule_once(self._post_init)


    def _post_init(self, dt):
        sessions = db.get_sessions()
        if sessions:
            self.box.add_widget(RV(sessions))
        else:
            self.box.add_widget(Label(text='No data to display'))


    def delete_all(self):
        self.recycle_view.data.clear()
        #Delete all sessions and their corresponding graph/lift data


class MyButton(RecycleDataViewBehavior, MDCardSwipe):

    index = None
    date_str = StringProperty()
    date_obj = ObjectProperty()
    key = StringProperty()
    workout = StringProperty() #Do I need these properties?

    def __init__(self) -> None:
        super().__init__()
        self.dialogs = {}

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(MyButton, self).refresh_view_attrs(
            rv, index, data)

    
    def launch_edit_screen(self,app):
        manager = app.root.ids.data_sm
        if not manager.has_screen(self.key):
            manager.add_widget(
                EditScreen(
                    self.key, 
                    self.date_str, 
                    self.date_obj,
                    self.workout,
                    self.lifts,
                    ))
            
        app.change_screen(
            manager = manager, 
            screen_name = self.key)


    def show_confirm_dialog(self):
        key = 'confirm'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text='Are you sure you want to delete this session?',
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

        # self.parent.remove_widget(self)
        del self.parent.parent.data[self.index]
        self._close_dialog('confirm')
        db.delete_session(self.key)

        for lift in self.lifts:
            db.delete_completed_lift(self.key, lift)
            db.delete_graph_data(self.key, lift)
        
    
class RV(RecycleView):
    def __init__(self, data, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = data