from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window

from screens import _sessionscreen


 
class MainApp(MDApp): 
    
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = "Cyan"
        Window.size = (375, 740)
        

        return Builder.load_file("kv/scratch.kv")

    def on_start(self):
        pass

if __name__ == '__main__':
    MainApp().run()