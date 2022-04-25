from kivy.app import App 
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty


class HomeScreen(MDScreen):
    box = ObjectProperty()
    
    def __init__(self, **kw):
        super().__init__(**kw)
        App.get_running_app().screens['home'] = self
        # Clock.schedule_once(self._post_init)

    # def _post_init(self, dt):
    #     self.box.add_widget(WorkoutOptionCard.next_card)