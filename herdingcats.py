from __future__ import print_function

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty

import dateparser
import dateutil.parser
import re
import string

import cProfile


from googleservices import GoogleServices

MESSAGE_REGEXP =  r"Lieu : (.*)\s*Date : (.*)\s*Tel : (.*)"
MESSAGE_REGEXP += r"Google Analytics information:\s*--------------------------------------------\s*"
MESSAGE_REGEXP += r"Campaign Source: (.*)\s*Campaign Name: (.*)\s*Campaign Medium: (.*)\s*Campaign Term:(.*)\s*"
MESSAGE_REGEXP += r"Campaign Content:(.*)\s*First visit: (.*)\s*Previous visit: (.*)\s*Current visit: (.*)\s*Times visited: (.*)\s*"


global_messages = None
google_services = None


class UnexpectedMessageBodyFormatError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class HerdingCatsCustomerMessage():
    """Attributes:

Objects:

    message
    date
    location_distance_text
    location_distance_value

Strings:

    event_location_str
    date_str,
    customer_msg,
    campaign_source,
    campaign_name,
    campaign_medium,
    campaign_term,
    campaign_content,
    campaign_first_visit,
    campaign_previous_visit,
    campaign_current_visit,
    campaign_times_visited

"""

    msg_regexp = re.compile(MESSAGE_REGEXP, flags=re.DOTALL)
    numeric_date_regexp = re.compile('^\d\d/\d\d(/\d\d(\d\d)?)?$')

    def short_description(self):
        if self.date:
            return "{1:%Y-%m-%d (%a)}, {0.event_location_str} ({0.location_distance_text})".format(self, self.date)
        else:
            return "{0.date_str}, {0.event_location_str} ({0.location_distance_text})".format(self)
    
    def __init__(self, msg, language='fr'):
        self.message = msg
        self.parse_message(language)
        self.parse_date(language)
        self.compute_distance()

        self.customer_msg = self.customer_msg.replace('\r\n', '\n')
        if self.customer_msg and self.customer_msg[-1] != '\n':
            self.customer_msg += '\n'

    def parse_message(self, language):
        # extract message body from msg
        maintype = self.message.get_content_maintype()
        message_body = None
        if maintype == 'multipart':
            for part in self.message.get_payload():
                if part.get_content_maintype() == 'text':
                    message_body = part.get_payload()
        elif maintype == 'text':
            message_body = self.message.get_payload()
        else:
            raise UnexpectedMessageBodyFormatError('MIME type neither multipart nor text')
        if not message_body:
            raise UnexpectedMessageBodyFormatError('Empty message')
        
        matchgroups = self.msg_regexp.match(message_body)

        if matchgroups is None:
            raise UnexpectedMessageBodyFormatError('Message does not parse: ' + message_body)

        matchgroups = matchgroups.groups()
        matchgroups = [s.strip() for s in matchgroups]

        attributes = ("event_location_str",
                      "date_str",
                      "customer_msg",
                      "campaign_source",
                      "campaign_name",
                      "campaign_medium",
                      "campaign_term",
                      "campaign_content",
                      "campaign_first_visit",
                      "campaign_previous_visit",
                      "campaign_current_visit",
                      "campaign_times_visited")
        for index, attribute_name in enumerate(attributes):
            setattr(self, attribute_name, matchgroups[index])

    def parse_date(self, language):
        self.date_str = ''.join(s for s in self.date_str if s in string.printable)
        print("Parsing date: {0}".format(self.date_str))

        # dateparser gets european dd/mm/yy dates wrong, use dateutil instead
        
        if self.numeric_date_regexp.match(self.date_str):
            self.date = dateutil.parser.parse(self.date_str, dayfirst=(language=='fr'))
        else:
            self.date = dateparser.parse(self.date_str, settings={'PREFER_DATES_FROM': 'future'})

        
    def compute_distance(self):
        (self.location_distance_text,
         self.location_distance_value) = google_services.get_distance(self.event_location_str)
        

class HerdingCatsButton(Button):

    def __init__(self, **kwargs):
        super(HerdingCatsButton, self).__init__(**kwargs)
        self.message_id = kwargs['message_id']
        
class HerdingCatsHome(BoxLayout):
    
    def __init__(self, **kwargs):
        super(HerdingCatsHome, self).__init__(**kwargs)
        self.orientation = 'vertical'
        
        global global_messages
        if global_messages is None:
            HerdingCatsHome.populate_global_messages()
        for i in global_messages.keys():
            button = HerdingCatsButton(text=global_messages[i].short_description(),
                                       message_id=i)
            button.bind(on_press=self.update_message_screen)
            self.add_widget(button)

    @classmethod        
    def populate_global_messages(self):
        global global_messages
        global google_services
        global_messages = {}
        messages = ((i, HerdingCatsCustomerMessage(m))
                    for (i, m) in google_services.get_relevant_messages_from_gmail())

        try:
            for _ in range(5):
                (i, m) = next(messages)
                global_messages[i] = m
                
        except StopIteration:
            pass

    def update_message_screen(self, pressed_button):
        print('The button <%s> is being pressed' % pressed_button.message_id)
        global screen_manager
        global message_screen
        message = global_messages[pressed_button.message_id]
        
        message_screen.current_message_id = pressed_button.message_id
        message_screen.button.text = pressed_button.message_id
        message_screen.date_input.text = message.date_str
        print ('Customer message text: {t}'.format(t=message.customer_msg))
        message_screen.client_message_text.text = message.customer_msg


        
        screen_manager.current = 'Message'


kv_string = """
<TextInputWithLabel@BoxLayout>:
    orientation: 'horizontal'      
    label_text: 'default'
    label: iAmLabel
    text_input: iAmTxt
    text_input_text: ''
    update_button: iAmBtn
    size_hint: 1, None
    size: self.label.texture_size

    Label:
        id: iAmLabel
        text: root.label_text
        padding: 0, 4
        size_hint_x: 0.15
        
    TextInput:
        id: iAmTxt
        text: root.text_input_text
        size_hint_x: 0.7

    Button:
        id: iAmBtn
        text: 'Update'
        size_hint_x: 0.15


<MessageScreen>:
    button: button1
    back_button: button2
    date_input: date_field.text_input
    client_message_text: client_message
    
    BoxLayout:
        orientation: 'vertical'

        TextInputWithLabel:
            id: date_field
            label_text: 'Date: '

        RstDocument:
            id: client_message
            text: 'Test'
            size_hint: 1, 0.9

        Button:
            id: button1
            text: 'My settings button'
            size_hint: 1, 0.1
        Button:
            id: button2
            text: 'Back to menu'
            on_press: root.manager.current = 'List'
            size_hint: 1, 0.1
"""

class TextInputWithLabel(BoxLayout):
    label = ObjectProperty(None)
    text_input = ObjectProperty(None)
    update_button = ObjectProperty(None)
    label_text = StringProperty('default')

class ListScreen(Screen):
    pass

class MessageScreen(Screen):
    current_message_id = StringProperty('')
    button = ObjectProperty(None)
    back_button = ObjectProperty(None)
    date_input = ObjectProperty(None)
    client_message_text = ObjectProperty(None)

    def update(self, dt):
        pass

class HerdingCatsApp(App):
    def build(self):
        global screen_manager
        return screen_manager

def main():
    global google_services, screen_manager
    google_services = GoogleServices()
    Builder.load_string(kv_string)
    screen_manager = ScreenManager()
    list_screen = ListScreen(name='List')
    message_screen = MessageScreen(name='Message')
    screen_manager.add_widget(list_screen)
    screen_manager.add_widget(message_screen)
    list_screen.add_widget(HerdingCatsHome())
    HerdingCatsApp().run()


if __name__ == '__main__':
    main()



    
