from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager


from kivy.lang import Builder

from screens.sessionscreen import SessionScreen


class MainApp(MDApp): 
    
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = "Cyan"
        Window.size = (375, 740)
        return Builder.load_file("kv/sessionscreen.kv")

    def on_start(self):
        pass

    def change_screen(self, manager: ScreenManager, screen_name: str, direction:str = 'left'): ## use a setter here?
        manager.transition.direction = direction
        manager.current = screen_name


if __name__ == '__main__':
    MainApp().run()


