from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from screens.selectionscreen import SelectionScreen
from screens.sessionscreen import SessionScreen
from screens.datascreen import DataScreen
from screens.schedulescreen import ScheduleScreen

import backend.database as db


class MainApp(MDApp): 

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = "Cyan"
        Window.size = (375, 740)
        return Builder.load_file("kv/main.kv")

    def change_screen(self, manager: ScreenManager, screen_name: str, direction:str = 'left'):
        manager.transition.direction = direction
        manager.current = screen_name


MainApp().run()