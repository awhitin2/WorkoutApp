from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivy_garden.drag_n_drop import DraggableObjectBehavior
from kivymd.uix.card import MDCardSwipe

import backend.database as db


class ScheduleManager(Widget):
    next_name = StringProperty()
    next_card = ObjectProperty(allownone=True)
    

    def __init__(self) -> None:
        self.cards = []
        data = db.get_schedule_data()
        if data:
            try:
                self.next_index = data['next']
            except:
                self.next_index = 0
            self.schedule = data['order']
            self.next_name = self.schedule[self.next_index]
        else:
            self.schedule = []

    def set_next(self): 

        for i, card in enumerate(self.cards):
            if i == self.next_index:
                self.next_card = card
                card.next_button.state = 'down'

    def cycle_next_scheduled(self):
        self.next_card.next_button.state = 'normal'
        next_index = self.cards.index(self.next_card)-1
        if next_index < 0:
            next_index = len(self.cards)-1
        self.next_card = self.cards[next_index]
        self.next_name = self.next_card.text
        self.next_card.next_button.state = 'down'
        db.update_next_index(next_index)

    def update_next(self, card, button):
        if button.state == 'down':
            self.next_card = card
            self.next_name = card.text
        else:
            self.next_card = None
            self.next_name = ''

    def on_next_card(self): ###This is not being triggered?
        self.next_name = '' if self.next_card == None else self.next_card.text
        print('next card changed')
        

    def save(self, *args):
        if self.cards:
            workouts = []
            next = None
            for index, card in enumerate(self.cards):
                if card == schedule_manager.next_card:
                    next = index
                workouts.append(card.text)
            if not next:
                next = len(workouts)-1
            d = {
                'next': next,
                'order' : workouts
            }
            db.set_schedule(d)
            return True
        return False


schedule_manager = ScheduleManager()