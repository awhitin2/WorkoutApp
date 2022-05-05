from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window

from screens import viewsessions



class MainApp(MDApp): 
    
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = "Cyan"
        Window.size = (375, 740)
        
        return Builder.load_file("kv/viewsessionsscreen.kv")

    def on_start(self):
        self.manager = self.root.ids.manager

    def change_screen(self, manager, screen_name: str, direction:str = 'left'): ## use a setter here?
        if not manager:
            manager = self.manager
        manager.transition.direction = direction
        manager.current = screen_name


if __name__ == '__main__':
    MainApp().run()