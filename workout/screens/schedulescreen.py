import functools

from kivy.clock import Clock
from kivy_garden.drag_n_drop import (DraggableLayoutBehavior, 
                                    DraggableObjectBehavior)
from kivy.properties import StringProperty, ObjectProperty
from kivymd.uix.behaviors.toggle_behavior import ToggleButtonBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDTextButton
from kivymd.uix.card import MDCardSwipe
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivy.uix.widget import Widget

from backend.schedulemanager import schedule_manager
import backend.database as db



class ScheduleScreen(MDScreen):
    drag_box = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.dialogs = {}
    
    def show_schedule_dialog(self):
        key = 'add'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                title="Add to Schedule",
                type="custom",
                content_cls = ScheduleDialog(),
                buttons=[
                    MDFlatButton(
                        text="DISCARD",
                        on_release=functools.partial(self._close_dialog, key)
                    ),
                    MDFlatButton(
                        text="SCHEDULE", 
                        on_release=self._add_workouts
                    ),
                ],
            )
        self.dialogs[key].open()

    def _close_dialog(self, key, *args):
        self.dialogs[key].dismiss()

    def _add_workouts(self, *args):
        key = 'add'
        selected = [child.workout for child in 
                    self.dialogs[key].content_cls.box.children 
                    if child.check.active]

        self.drag_box.set_cards(selected)
        self._close_dialog(key)

    def _show_save_dialog(self):
        key = 'save'
        if not key in self.dialogs:
            self.dialogs[key] = MDDialog(
                text="Saved",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release = functools.partial(self._close_dialog, key)
                    )
                ]
            )
        self.dialogs[key].open()

    def save(self, *args):
        success = schedule_manager.save()
        if success:
            self._show_save_dialog()


class DragBox(DraggableLayoutBehavior, MDBoxLayout):

    def __init__(self, **kwargs):
        super().__init__(
            spacer_widget = MySpacer(),
            spacer_props = {'size_hint_y': None, 'height' : 150},
             **kwargs)
        schedule_manager.cards = self.children
        Clock.schedule_once(self._post_init)

    def _post_init(self, *args): 
        if schedule_manager.schedule:
            self.set_cards(schedule_manager.schedule)
            schedule_manager.set_next()

    def set_cards(self, workouts: list): 
        '''
        Called post_init, when new cards are added from the schedule dialog,
        and when new cards are added from the selection screen
        '''
        for i, w in enumerate(workouts):
            card = ScheduleCard(w)
            self.add_widget(card, i)

    def compare_pos_to_widget(self, widget, pos):
        if self.orientation == 'vertical':
            return 'before' if pos[1] >= widget.center_y else 'after'
        return 'before' if pos[0] < widget.center_x else 'after'

    def handle_drag_release(self, index, drag_widget):
        self.add_widget(drag_widget, index)
    

class ScheduleCard(DraggableObjectBehavior, MDCardSwipe):
    text = StringProperty()
    next_button = ObjectProperty()
  
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def remove(self, *args):
        if schedule_manager.next_card == self:
            schedule_manager.next_card = None
        self.parent.remove_widget(self)

    def initiate_drag(self):
        # during a drag, remove the widget from the original location
        self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.x > self.width*.1:
                return DraggableObjectBehavior.on_touch_down(self, touch)
            else:
                return MDCardSwipe.on_touch_down(self, touch)


class MySpacer(Widget):
    """Widget inserted at the location where the dragged widget may be
    dropped to show where it'll be dropped.
    """
    pass

    
class NextButton(MDTextButton, ToggleButtonBehavior):
    card = ObjectProperty()

    def on_press(self, *args):
        schedule_manager.update_next(self.card, self)


class ScheduleDialog(MDBoxLayout):
    """Content class for Schedule Add Workout dialog"""
    box = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        workouts = db.get_workout_names()
        for workout in workouts:
            self.box.add_widget(ScheduleDialogRow(workout = workout)) 


class ScheduleDialogRow(MDBoxLayout):
    workout = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def set_icon(self, instance_check):
        instance_check.active = not instance_check.active
