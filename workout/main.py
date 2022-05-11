
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from screens.selectionscreen import SelectionScreen
from screens.sessionscreen import SessionScreen
from screens.datascreen import DataScreen
from screens.schedulescreen import ScheduleScreen

import backend.database as db

# db.generate_sample_db_session_data()
# db.initialize_sample_database_info()

def write_sessions()-> None:
    from datetime import datetime

    sessions = db.get_sessions()
    if sessions:
        with open('backend/session_log.txt', 'w') as file:
            for _, v in sessions.items():
                date = datetime.fromisoformat(v['date'])
                date_str = datetime.strftime(date, '%b %d, %Y')
                file.write(date_str + '\n')

class MainApp(MDApp): 

    def on_scheduled(self, *args): #Still in use?
        self.scheduled_text = self.scheduled.text

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = "Cyan"
        Window.size = (375, 740)
        return Builder.load_file("kv/main.kv")

    def on_start(self):
        write_sessions()

    #Set screen managers as objects directly rather than referencing via id
    def change_screen(self, manager: ScreenManager, screen_name: str, direction:str = 'left'):
        manager.transition.direction = direction
        manager.current = screen_name


MainApp().run()