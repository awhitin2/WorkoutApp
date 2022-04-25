
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager
from screens.sessionscreen import SessionScreen
from screens.schedulescreen import ScheduleScreen, ScheduleCard
from screens.selectionscreen import SelectionScreen
from backend.mapping import WorkoutOptionInfo

import backend.database as db

def write_sessions()-> None:
    from datetime import datetime

    sessions = db.get_sessions()
    with open('backend/session_log.txt', 'w') as file:
        for _, v in sessions.items():
            date = datetime.fromisoformat(v['date'])
            date_str = datetime.strftime(date, '%b %d, %Y')
            file.write(date_str + '\n')

class MainApp(MDApp): 

    screens = {}
    scheduled: ScheduleCard = ObjectProperty()
    scheduled_text = StringProperty()
    scheduled_string = StringProperty()

    def on_scheduled(self, *args):
        self.scheduled_text = self.scheduled.text

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = "Cyan"
        Window.size = (375, 740)
        return Builder.load_file("kv/main.kv")

    def on_start(self):
        write_sessions()

    def change_screen(self, manager: ScreenManager, screen_name: str, direction:str = 'left'): ## use a setter here?
        manager.transition.direction = direction
        manager.current = screen_name


MainApp().run()