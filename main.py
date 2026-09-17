import os
import json
from datetime import datetime
import uuid

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty

from kivymd.app import MDApp
from kivymd.uix.list import MDListItem
from kivymd.uix.pickers import MDTimePicker
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

# Plyer का उपयोग वाइब्रेशन के लिए
try:
    from plyer import vibrator
except ImportError:
    vibrator = None

# UI के लिए KV भाषा स्ट्रिंग
KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

<AlarmListItem>:
    id: list_item
    
    MDListItemLeadingIcon:
        icon: "alarm"

    MDListItemContent:
        MDListItemHeadlineText:
            text: root.alarm_time_formatted
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color if root.active else app.theme_cls.disabled_hint_text_color

        MDListItemSupportingText:
            text: "सक्रिय" if root.active else "निष्क्रिय"
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color if root.active else app.theme_cls.disabled_hint_text_color

    MDListItemTrailingContainer:
        MDSwitch:
            active: root.active
            on_active: app.toggle_alarm(root, self.active)

        MDIconButton:
            icon: "delete"
            on_release: app.delete_alarm(root)

MDScreen:
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "अलार्म घड़ी"
            elevation: 4

        MDLabel:
            id: clock_label
            text: "00:00:00"
            halign: 'center'
            font_style: 'H3'
            size_hint_y: None
            height: self.texture_size[1]
            padding_y: "20dp"

        MDScrollView:
            MDList:
                id: alarm_list

    MDFloatingActionButton:
        icon: "plus"
        pos_hint: {"center_x": .5, "center_y": .15}
        on_release: app.show_time_picker()
        md_bg_color: app.theme_cls.primary_color
"""

class AlarmListItem(MDListItem):
    """अलार्म सूची में एक आइटम का प्रतिनिधित्व करने वाला विजेट।"""
    alarm_id = StringProperty()
    alarm_time = StringProperty()  # 24-घंटे के प्रारूप में HH:MM
    active = BooleanProperty()
    alarm_time_formatted = StringProperty() # प्रदर्शन के लिए 12-घंटे के प्रारूप में

class AlarmGhadiApp(MDApp):
    """मुख्य अलार्म घड़ी एप्लीकेशन क्लास।"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alarms_data = []
        self.json_path = os.path.join(self.user_data_dir, 'alarms.json')
        self.dialog = None

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_string(KV)

    def on_start(self):
        """एप्लिकेशन शुरू होने पर अलार्म लोड करें और घड़ी शुरू करें।"""
        self.load_alarms()
        Clock.schedule_interval(self.update_clock, 1)

    def on_stop(self):
        """एप्लिकेशन बंद होने पर अलार्म सहेजें।"""
        self.save_alarms()

    def load_alarms(self):
        """JSON फ़ाइल से अलार्म लोड करता है।"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r') as f:
                    self.alarms_data = json.load(f)
                for alarm_data in self.alarms_data:
                    self.add_alarm_widget(alarm_data)
        except Exception as e:
            print(f"अलार्म लोड करने में विफल: {e}")
            self.alarms_data = []

    def save_alarms(self):
        """वर्तमान अलार्म को JSON फ़ाइल में सहेजता है।"""
        try:
            with open(self.json_path, 'w') as f:
                json.dump(self.alarms_data, f, indent=4)
        except Exception as e:
            print(f"अलार्म सहेजने में विफल: {e}")

    def update_clock(self, dt):
        """हर सेकंड घड़ी लेबल को अपडेट करता है और अलार्म की जांच करता है।"""
        now = datetime.now()
        self.root.ids.clock_label.text = now.strftime("%H:%M:%S")
        # हर मिनट की शुरुआत में अलार्म की जांच करें
        if now.second == 0:
            self.check_alarms(now)

    def check_alarms(self, now):
        """यह जांचने के लिए कि क्या कोई अलार्म बंद होना चाहिए।"""
        current_time_str = now.strftime("%H:%M")
        for alarm_data in self.alarms_data:
            if alarm_data['active'] and alarm_data['time'] == current_time_str:
                self.trigger_alarm(alarm_data)

    def trigger_alarm(self, alarm_data):
        """एक अलार्म को ट्रिगर करता है (वाइब्रेट और एक संवाद दिखाएं)।"""
        print(f"अलार्म ट्रिगर हो रहा है: {alarm_data['time']}")
        if vibrator:
            try:
                vibrator.vibrate(time=2)  # 2 सेकंड के लिए वाइब्रेट करें
            except Exception as e:
                print(f"वाइब्रेट करने में विफल: {e}")

        # संबंधित विजेट खोजें
        for widget in self.root.ids.alarm_list.children:
            if widget.alarm_id == alarm_data['id']:
                alarm_data['active'] = False
                widget.active = False
                break
        
        # संवाद दिखाएं
        if not self.dialog:
            alarm_time_obj = datetime.strptime(alarm_data['time'], '%H:%M')
            formatted_time = alarm_time_obj.strftime("%I:%M %p")
            self.dialog = MDDialog(
                title="[b]अलार्म![/b]",
                text=f"यह {formatted_time} के लिए आपका अलार्म है।",
                buttons=[
                    MDFlatButton(
                        text="ठीक", 
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                ],
            )
            self.dialog.on_dismiss = lambda: setattr(self, 'dialog', None)
            self.dialog.open()

    def show_time_picker(self):
        """एक नया अलार्म सेट करने के लिए टाइम पिकर संवाद दिखाता है।"""
        time_picker = MDTimePicker()
        time_picker.bind(on_save=self.on_time_save)
        time_picker.open()

    def on_time_save(self, instance, time):
        """जब टाइम पिकर से समय बचाया जाता है तो एक नया अलार्म जोड़ता है।"""
        alarm_time_str = time.strftime("%H:%M")
        new_alarm_data = {
            'id': str(uuid.uuid4()),
            'time': alarm_time_str,
            'active': True
        }
        self.alarms_data.append(new_alarm_data)
        self.add_alarm_widget(new_alarm_data)
        self.save_alarms()

    def add_alarm_widget(self, alarm_data):
        """सूची में एक नया अलार्म विजेट जोड़ता है।"""
        alarm_time_obj = datetime.strptime(alarm_data['time'], '%H:%M')
        formatted_time = alarm_time_obj.strftime("%I:%M %p")
        
        list_item = AlarmListItem(
            alarm_id=alarm_data['id'],
            alarm_time=alarm_data['time'],
            active=alarm_data['active'],
            alarm_time_formatted=formatted_time
        )
        self.root.ids.alarm_list.add_widget(list_item)

    def delete_alarm(self, list_item):
        """डेटा और UI से अलार्म हटाता है।"""
        self.alarms_data = [d for d in self.alarms_data if d['id'] != list_item.alarm_id]
        self.root.ids.alarm_list.remove_widget(list_item)
        self.save_alarms()

    def toggle_alarm(self, list_item, active):
        """अलार्म की सक्रिय स्थिति को टॉगल करता है।"""
        for alarm_data in self.alarms_data:
            if alarm_data['id'] == list_item.alarm_id:
                alarm_data['active'] = active
                list_item.active = active
                break
        self.save_alarms()

if __name__ == '__main__':
    AlarmGhadiApp().run()
